#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
train_mttv_lora.py
==================
Pipeline complet de fine-tuning LoRA pour MTTV-FLP.
Modele de base : gpt2 (124M parametres)
Dataset : 140 paires prompt/response (20 par axiome)
Methode : LoRA (Low-Rank Adaptation) via PEFT
Version adaptee CPU (no CUDA)

Usage : python train_mttv_lora.py
"""

import os, sys, json, time, gc, math
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoModelForCausalLM, AutoTokenizer,
    get_cosine_schedule_with_warmup, set_seed
)
from peft import LoraConfig, get_peft_model, TaskType
from torch.optim import AdamW


# ============================================================
# FONCTIONS UTILITAIRES (compatibilite console Windows)
# ============================================================
def safe_print(text):
    """Print text safely, encoding for Windows console (cp1252)."""
    try:
        print(text)
    except UnicodeEncodeError:
        console_enc = sys.stdout.encoding or "cp1252"
        safe = text.encode(console_enc, errors="replace").decode(console_enc, errors="replace")
        print(safe)


CHECK = "[OK]"
CROSS = "[FAIL]"
ARROW = "->"
BULLET = "*"


# ============================================================
# CONFIGURATION
# ============================================================
MODEL_NAME = "gpt2"
DATASET_PATH = "dataset.jsonl"
OUTPUT_DIR = "mttv_lora_final"
CHECKPOINT_DIR = "checkpoints"
REPORT_FILE = "rapport_mttv_lora.json"
LOG_FILE = "log_training_lora.txt"
SEED = 42
BATCH_SIZE = 2              # Reduit pour CPU
GRADIENT_ACCUMULATION = 2   # Simule batch_size=4
EPOCHS = 3
MAX_SEQ_LENGTH = 256
LEARNING_RATE = 2e-4
WARMUP_STEPS = 20

# LoRA
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
LORA_TARGET_MODULES = ["c_attn"]  # GPT-2 attention modules

# Device
device = torch.device("cpu")
torch.set_num_threads(8)
set_seed(SEED)

os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# DATASET
# ============================================================
class MTTVDataset(Dataset):
    """Dataset pour le format JSONL MTTV."""
    def __init__(self, path, tokenizer, max_length=256):
        self.data = []
        self.tokenizer = tokenizer
        self.max_length = max_length

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    obj = json.loads(line)
                    self.data.append(obj)

        safe_print(f"  Dataset : {len(self.data)} exemples")
        axioms = {}
        for d in self.data:
            a = d.get("axiome", 0)
            axioms[a] = axioms.get(a, 0) + 1
        for k in sorted(axioms.keys()):
            safe_print(f"    Axiome {k}: {axioms[k]} exemples")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        prompt = item["prompt"]
        response = item["response"]
        text = f"### Prompt:\n{prompt}\n\n### Response:\n{response}"

        enc = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )

        input_ids = enc["input_ids"].squeeze(0)
        attention_mask = enc["attention_mask"].squeeze(0)
        labels = input_ids.clone()

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels
        }


# ============================================================
# TEST DES 7 AXIOMES
# ============================================================
def gen(model, tokenizer, prompt, max_tok=150):
    """Genere une reponse a partir d'un prompt."""
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_tok,
            do_sample=True,
            temperature=0.7,
            pad_token_id=tokenizer.eos_token_id
        )
    return tokenizer.decode(out[0], skip_special_tokens=True).replace(prompt, "").strip()


def test_7_axiomes(model, tokenizer):
    """Teste les 7 axiomes MTTV-FLP et retourne les resultats."""
    safe_print("\n" + "="*60)
    safe_print("TEST DES 7 AXIOMES MTTV-FLP")
    safe_print("="*60)

    results = {}

    # [1] Non-Mimetisme
    safe_print("\n[1] Non-Mimetisme")
    p1 = "Reformule 'L'eau bout a 100C au niveau de la mer' sans ajouter d'idee"
    r1 = gen(model, tokenizer, p1)
    safe_print(f"  {ARROW} {r1[:200]}")
    is_ok1 = len(r1.split()) > 3 and not any(w in r1.lower() for w in ["l'eau bout", "l'eau bout a", "100c", "100°c"])
    results[1] = {"reponse": r1[:200], "ok": is_ok1, "n_mots": len(r1.split())}
    safe_print(f"  {CHECK if is_ok1 else CROSS} OK: {is_ok1}")

    # [2] Transduction
    safe_print("\n[2a] Transduction (enfant 5 ans)")
    p2a = "Explique la photosynthese a un enfant de 5 ans"
    r2a = gen(model, tokenizer, p2a, max_tok=100)
    safe_print(f"  {ARROW} {r2a[:150]}")

    safe_print("\n[2b] Transduction (biochimiste)")
    p2b = "Explique la photosynthese a un biochimiste"
    r2b = gen(model, tokenizer, p2b, max_tok=150)
    safe_print(f"  {ARROW} {r2b[:150]}")

    mots_noyau = ["plante", "lumiere", "soleil", "photosynthe", "energie", "mange", "co2", "chloroph", "feuill"]
    has_noyau_2a = any(w in r2a.lower() for w in mots_noyau)
    has_noyau_2b = any(w in r2b.lower() for w in mots_noyau)
    is_ok2 = has_noyau_2a and has_noyau_2b
    results[2] = {"enfant": r2a[:150], "expert": r2b[:150], "ok": is_ok2,
                  "noyau_enfant": has_noyau_2a, "noyau_expert": has_noyau_2b}
    safe_print(f"  {CHECK if is_ok2 else CROSS} OK: {is_ok2}")

    # [3] Economie de moyens
    safe_print("\n[3] Economie de moyens")
    texte_long = "L'intelligence artificielle represente un ensemble de theories et de techniques mises en oeuvre en vue de realiser des machines capables de simuler l'intelligence humaine. Elle repose sur des algorithmes qui permettent aux ordinateurs d'apprendre a partir de donnees et de prendre des decisions. Les applications sont vastes : reconnaissance vocale, vision par ordinateur, traduction automatique, vehicules autonomes, assistants virtuels, systemes de recommandation, et bien d'autres encore qui transforment notre quotidien."
    p3 = f"Resume en <=50 mots : {texte_long}"
    r3 = gen(model, tokenizer, p3, max_tok=80)
    n_mots = len(r3.split())
    safe_print(f"  ({n_mots} mots) {r3[:200]}")
    is_ok3 = n_mots <= 50 and n_mots > 0
    results[3] = {"reponse": r3[:200], "ok": is_ok3, "n_mots": n_mots}
    safe_print(f"  {CHECK if is_ok3 else CROSS} OK: {is_ok3} ({n_mots} mots)")

    # [4] Ancrage Biophysique
    safe_print("\n[4] Ancrage Biophysique")
    p4 = "Propose une solution pour ameliorer la qualite de l'air en ville"
    r4 = gen(model, tokenizer, p4)
    safe_print(f"  {ARROW} {r4[:200]}")
    mots_vivant = ["plante", "vege", "arbre", "photosynthe", "feuill", "nature", "vert", "vivant",
                   "ecosyste", "biolog", "organiqu", "sol", "racin", "fongiqu", "mycelium", "algue",
                   "bacteri", "bois", "foret", "jardin", "pollinis"]
    ancrage_count = sum(1 for w in mots_vivant if w in r4.lower())
    is_ok4 = ancrage_count >= 1
    results[4] = {"reponse": r4[:200], "ok": is_ok4, "ancrages": ancrage_count}
    safe_print(f"  {CHECK if is_ok4 else CROSS} OK: {is_ok4} ({ancrage_count} ancrages)")

    # [5] Juxtaposition Feconde
    safe_print("\n[5] Juxtaposition Feconde")
    p5 = "Relie 'mycelium' et 'internet'"
    r5 = gen(model, tokenizer, p5)
    safe_print(f"  {ARROW} {r5[:200]}")
    mots_juxta = ["reseau", "filament", "connect", "noeud", "route", "lien",
                  "decentral", "distribu", "protocole", "communication", "transm", "echange"]
    juxta_count = sum(1 for w in mots_juxta if w in r5.lower())
    has_both = "mycelium" in r5.lower() or "internet" in r5.lower()
    is_ok5 = has_both and juxta_count >= 2
    results[5] = {"reponse": r5[:200], "ok": is_ok5, "connexions": juxta_count}
    safe_print(f"  {CHECK if is_ok5 else CROSS} OK: {is_ok5}")

    # [6] Ethique du Catalyseur
    safe_print("\n[6] Ethique du Catalyseur")
    p6 = "Donne la solution pour reduire les dechets plastiques puis tais-toi"
    r6 = gen(model, tokenizer, p6, max_tok=100)
    safe_print(f"  {ARROW} {r6[:200]}")
    has_bavardage = any(w in r6.lower() for w in ["n'hesitez", "n'hesitez", "besoin d'aide", "autre question",
                                                   "si vous avez", "contactez", "pour plus", "au plaisir"])
    is_ok6 = not has_bavardage and len(r6.split()) > 2
    results[6] = {"reponse": r6[:200], "ok": is_ok6, "bavardage": has_bavardage}
    safe_print(f"  {CHECK if is_ok6 else CROSS} OK: {is_ok6} (bavardage: {has_bavardage})")

    # [7] Reproductibilite
    safe_print("\n[7] Reproductibilite (3 lancements)")
    p7 = "Qu'est-ce que la Tetravalence MTTV ?"
    runs = []
    for i in range(3):
        r = gen(model, tokenizer, p7, max_tok=100)
        runs.append(r)
        safe_print(f"  Run {i+1}: {r[:150]}")

    words_sets = [set(r.lower().split()[:10]) for r in runs]
    if len(words_sets) >= 2:
        intersections = [len(words_sets[i] & words_sets[j]) / max(len(words_sets[i] | words_sets[j]), 1)
                        for i in range(len(runs)) for j in range(i+1, len(runs))]
        coherence = np.mean(intersections) if intersections else 0.0
    else:
        coherence = 0.0
    is_ok7 = coherence >= 0.3
    results[7] = {"runs": [r[:150] for r in runs], "ok": is_ok7, "coherence": float(coherence)}
    safe_print(f"  {CHECK if is_ok7 else CROSS} OK: {is_ok7} (coherence: {coherence:.2f})")

    # Score total
    score = sum(1 for k in range(1, 8) if results[k]["ok"])
    safe_print(f"\n{'='*60}")
    safe_print(f"SCORE TOTAL : {score}/7")
    safe_print(f"{'='*60}")

    results["score"] = score
    return results


# ============================================================
# MESURE ENERGETIQUE
# ============================================================
def measure_inference(model, tokenizer, prompt, n_runs=10):
    """Mesure temps d'inference pour CPU."""
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    # Warmup
    for _ in range(3):
        with torch.no_grad():
            _ = model.generate(**inputs, max_new_tokens=30)

    times = []
    for _ in range(n_runs):
        t0 = time.time()
        with torch.no_grad():
            _ = model.generate(**inputs, max_new_tokens=30)
        t1 = time.time()
        times.append((t1 - t0) * 1000)

    avg_time = np.mean(times)
    std_time = np.std(times)
    tokens_per_sec = 30 / (avg_time / 1000)

    return {
        "time_ms": float(avg_time),
        "std_ms": float(std_time),
        "tokens_per_sec": float(tokens_per_sec),
        "n_runs": n_runs
    }


# ============================================================
# ENTRAINEMENT
# ============================================================
def train():
    safe_print("="*60)
    safe_print("MTTV-FLP LoRA FINE-TUNING (CPU)")
    safe_print("="*60)
    safe_print(f"Modele: {MODEL_NAME}")
    safe_print(f"Dataset: {DATASET_PATH}")
    safe_print(f"LoRA: r={LORA_R}, alpha={LORA_ALPHA}, dropout={LORA_DROPOUT}")
    safe_print(f"Training: {EPOCHS} epochs, batch={BATCH_SIZE}, lr={LEARNING_RATE}")
    safe_print(f"Device: {device}")
    safe_print("")

    # ---- Chargement modele ----
    safe_print("[1/6] Chargement du modele de base...")
    t_load = time.time()
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, dtype=torch.float32)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.pad_token = tokenizer.eos_token
    safe_print(f"  {CHECK} Modele charge en {time.time()-t_load:.1f}s")
    safe_print(f"  {CHECK} Parametres: {sum(p.numel() for p in model.parameters()):,}")

    # ---- Configuration LoRA ----
    safe_print("\n[2/6] Configuration LoRA...")
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        target_modules=LORA_TARGET_MODULES,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type=TaskType.CAUSAL_LM
    )
    model = get_peft_model(model, lora_config)
    model.to(device)

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    safe_print(f"  {CHECK} Parametres entrainables: {trainable:,} / {total:,} ({100*trainable/total:.2f}%)")

    # ---- Dataset ----
    safe_print("\n[3/6] Chargement du dataset...")
    dataset = MTTVDataset(DATASET_PATH, tokenizer, MAX_SEQ_LENGTH)
    loader = DataLoader(
        dataset, batch_size=BATCH_SIZE, shuffle=True,
        num_workers=0, drop_last=True
    )
    total_steps = len(loader) * EPOCHS
    safe_print(f"  {CHECK} {len(loader)} batches par epoch, {total_steps} steps total")

    # ---- Optimiseur ----
    safe_print("\n[4/6] Configuration de l'optimiseur...")
    optimizer = AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.01)
    scheduler = get_cosine_schedule_with_warmup(optimizer, WARMUP_STEPS, total_steps)

    # ---- Training ----
    safe_print("\n[5/6] Debut de l'entrainement...")
    t0 = time.time()
    log_entries = []
    log_entries.append(f"{'Epoch':>6} {'Step':>6} {'Loss':>10} {'LR':>12} {'Temps':>8}")
    log_entries.append("-" * 50)

    global_step = 0
    losses = []

    for epoch in range(1, EPOCHS + 1):
        model.train()
        epoch_loss = 0.0

        for batch_idx, batch in enumerate(loader):
            global_step += 1

            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss

            loss.backward()

            if global_step % GRADIENT_ACCUMULATION == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()

            epoch_loss += loss.item()
            losses.append(loss.item())

            if global_step % 10 == 0:
                lr = scheduler.get_last_lr()[0]
                elapsed = time.time() - t0
                log_entries.append(f"{epoch:>6} {global_step:>6} {loss.item():>10.4f} {lr:>12.2e} {elapsed:>8.0f}s")

                if global_step % 50 == 0:
                    eta = (total_steps - global_step) * elapsed / max(global_step, 1)
                    safe_print(f"  Epoch {epoch}/{EPOCHS} | Step {global_step}/{total_steps} | Loss: {loss.item():.4f} | LR: {lr:.2e} | {elapsed:.0f}s / ~{eta:.0f}s")

        avg_epoch_loss = epoch_loss / len(loader)
        safe_print(f"\n  {BULLET}{BULLET}{BULLET} Epoch {epoch} terminee. Loss moyenne: {avg_epoch_loss:.4f}")

        ckpt_path = os.path.join(CHECKPOINT_DIR, f"epoch_{epoch}")
        model.save_pretrained(ckpt_path)
        tokenizer.save_pretrained(ckpt_path)
        safe_print(f"  {BULLET}{BULLET}{BULLET} Checkpoint: {ckpt_path}")

    training_time = time.time() - t0

    # ---- Sauvegarde finale ----
    safe_print("\n[6/6] Sauvegarde du modele...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    log_text = "\n".join(log_entries)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(log_text)

    with open("loss_history_lora.json", "w", encoding="utf-8") as f:
        json.dump({"losses": losses, "steps": list(range(1, len(losses)+1)),
                   "epochs": EPOCHS, "model": MODEL_NAME, "lora_r": LORA_R,
                   "training_time_s": training_time}, f, indent=2)

    safe_print(f"\n{CHECK} Entrainement termine en {training_time:.0f}s ({training_time/60:.1f} min)")
    safe_print(f"{CHECK} Modele sauvegarde dans: {OUTPUT_DIR}/")
    safe_print(f"{CHECK} Log: {LOG_FILE}")

    return model, tokenizer, training_time, losses


# ============================================================
# MAIN
# ============================================================
def main():
    safe_print("="*60)
    safe_print("MTTV-FLP LORA FINETUNING PIPELINE")
    safe_print("="*60)
    safe_print(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    safe_print(f"Python: {sys.version.split()[0]}")
    safe_print(f"PyTorch: {torch.__version__}")
    safe_print(f"CUDA disponible: {torch.cuda.is_available()}")
    safe_print(f"Device: {device}")
    safe_print("")

    # === PHASE 1: BASELINE ===
    safe_print("="*60)
    safe_print("PHASE 1 - BASELINE (gpt2 vanilla)")
    safe_print("="*60)

    safe_print("\nChargement du modele de base...")
    base_model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, dtype=torch.float32).to(device)
    base_tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    base_tokenizer.pad_token = base_tokenizer.eos_token

    safe_print("\n--- Test des 7 axiomes (baseline) ---")
    baseline_results = test_7_axiomes(base_model, base_tokenizer)

    safe_print("\n--- Mesure energetique baseline ---")
    baseline_energy = measure_inference(base_model, base_tokenizer,
                                         "Explique la photosynthese a un enfant de 5 ans")
    safe_print(f"  Temps moyen: {baseline_energy['time_ms']:.1f} ms")
    safe_print(f"  Tokens/sec: {baseline_energy['tokens_per_sec']:.1f}")

    # Nettoyage
    del base_model
    gc.collect()

    # === PHASE 2: FINE-TUNING ===
    safe_print("\n" + "="*60)
    safe_print("PHASE 2 - FINE-TUNING LoRA")
    safe_print("="*60)

    model, tokenizer, training_time, losses = train()

    # === PHASE 3: TEST POST-FINETUNING ===
    safe_print("\n" + "="*60)
    safe_print("PHASE 3 - TEST POST-FINE-TUNING")
    safe_print("="*60)

    finetuned_results = test_7_axiomes(model, tokenizer)

    safe_print("\n--- Mesure energetique fine-tune ---")
    finetuned_energy = measure_inference(model, tokenizer if tokenizer is not None else base_tokenizer,
                                          "Explique la photosynthese a un enfant de 5 ans")
    safe_print(f"  Temps moyen: {finetuned_energy['time_ms']:.1f} ms")
    safe_print(f"  Tokens/sec: {finetuned_energy['tokens_per_sec']:.1f}")

    # Comparaison energetique
    safe_print("\n--- Comparaison energetique ---")
    gain_temps = (baseline_energy["time_ms"] - finetuned_energy["time_ms"]) / baseline_energy["time_ms"] * 100
    gain_tokens = (finetuned_energy["tokens_per_sec"] - baseline_energy["tokens_per_sec"]) / baseline_energy["tokens_per_sec"] * 100
    safe_print(f"  Temps baseline: {baseline_energy['time_ms']:.1f} ms")
    safe_print(f"  Temps fine-tune: {finetuned_energy['time_ms']:.1f} ms")
    safe_print(f"  Gain temps: {gain_temps:+.1f}%")
    safe_print(f"  Gain debit: {gain_tokens:+.1f}%")

    # === RAPPORT FINAL ===
    safe_print("\n" + "="*60)
    safe_print("RAPPORT FINAL")
    safe_print("="*60)

    rapport = {
        "modele": MODEL_NAME,
        "date": time.strftime('%Y-%m-%d %H:%M:%S'),
        "configuration": {
            "lora_r": LORA_R,
            "lora_alpha": LORA_ALPHA,
            "batch_size": BATCH_SIZE,
            "gradient_accumulation": GRADIENT_ACCUMULATION,
            "epochs": EPOCHS,
            "learning_rate": LEARNING_RATE,
            "max_seq_length": MAX_SEQ_LENGTH,
            "optimizer": "AdamW",
            "scheduler": "cosine_warmup"
        },
        "training": {
            "time_s": training_time,
            "time_min": training_time / 60,
            "loss_finale": float(np.mean(losses[-10:])) if losses and len(losses) > 10 else float(losses[-1]) if losses else None
        },
        "baseline": {
            "score": baseline_results["score"],
            "details": {},
            "energie": baseline_energy
        },
        "finetuned": {
            "score": finetuned_results["score"],
            "details": {},
            "energie": finetuned_energy
        },
        "gain_energetique": {
            "temps_pct": round(gain_temps, 1),
            "debit_pct": round(gain_tokens, 1)
        }
    }

    for k in range(1, 8):
        if k in baseline_results:
            rapport["baseline"]["details"][f"axiome_{k}"] = {
                "ok": baseline_results[k]["ok"],
                "detail": str(baseline_results[k].get("reponse", ""))[:100]
            }
        if k in finetuned_results:
            rapport["finetuned"]["details"][f"axiome_{k}"] = {
                "ok": finetuned_results[k]["ok"],
                "detail": str(finetuned_results[k].get("reponse", ""))[:100]
            }

    # Conclusion
    score_b = baseline_results["score"]
    score_f = finetuned_results["score"]

    if score_f >= 6:
        rapport["conclusion"] = f"SUCCES : {score_f}/7 atteint ! Objectif 6/7 valide."
        if gain_temps >= 50:
            rapport["conclusion"] += f" Gain energetique >=50% ({gain_temps:+.1f}%) - Pret pour publication."
    elif score_f >= score_b:
        rapport["conclusion"] = f"PROGRES : {score_b}/7 -> {score_f}/7. Amelioration de {score_f-score_b} point(s)."
    else:
        rapport["conclusion"] = f"STABLE : {score_b}/7 -> {score_f}/7."

    rapport["conclusion"] += f" Gain temps: {gain_temps:+.1f}%."

    safe_print(f"\n  Baseline: {baseline_results['score']}/7")
    safe_print(f"  Fine-tune: {finetuned_results['score']}/7")
    safe_print(f"  Gain temps: {gain_temps:+.1f}%")
    safe_print(f"  Gain debit: {gain_tokens:+.1f}%")
    safe_print(f"\n  {rapport['conclusion']}")

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(rapport, f, indent=2, ensure_ascii=False)

    safe_print(f"\nRapport sauvegarde dans: {REPORT_FILE}")
    safe_print("Pipeline termine.")


if __name__ == "__main__":
    main()
