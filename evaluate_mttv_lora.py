#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evaluate_mttv_lora.py
=====================
Evalue le modele LoRA fine-tune MTTV-FLP.
Charge le modele de base gpt2 + adaptateurs LoRA sauvegardes,
teste les 7 axiomes, mesure les performances energetiques.
"""

import os, sys, json, time, gc, numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

MODEL_NAME = "gpt2"
LORA_PATH = "mttv_lora_final"
REPORT_FILE = "rapport_mttv_lora.json"
DEBUG = True

device = torch.device("cpu")
torch.set_num_threads(8)


def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or "cp1252"
        safe = text.encode(enc, errors="replace").decode(enc, errors="replace")
        print(safe)

CHECK = "[OK]"
CROSS = "[FAIL]"
ARROW = "->"


def gen(model, tokenizer, prompt, max_tok=150):
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        out = model.generate(
            **inputs, max_new_tokens=max_tok, do_sample=True,
            temperature=0.7, pad_token_id=tokenizer.eos_token_id
        )
    return tokenizer.decode(out[0], skip_special_tokens=True).replace(prompt, "").strip()


def test_7_axiomes(model, tokenizer, label="Modele"):
    safe_print(f"\n{'='*60}")
    safe_print(f"TEST DES 7 AXIOMES - {label}")
    safe_print('='*60)
    results = {}

    # [1] Non-Mimetisme
    safe_print("\n[1] Non-Mimetisme")
    p1 = "Reformule 'L'eau bout a 100C au niveau de la mer' sans ajouter d'idee"
    r1 = gen(model, tokenizer, p1)
    safe_print(f"  {ARROW} {r1[:200]}")
    is_ok1 = len(r1.split()) > 3 and not any(w in r1.lower() for w in ["l'eau bout", "100c"])
    results[1] = {"ok": is_ok1, "reponse": r1[:200]}
    safe_print(f"  {CHECK if is_ok1 else CROSS} OK: {is_ok1}")

    # [2] Transduction
    safe_print("\n[2a] Transduction (enfant)")
    r2a = gen(model, tokenizer, "Explique la photosynthese a un enfant de 5 ans", 100)
    safe_print(f"  {ARROW} {r2a[:150]}")
    safe_print("\n[2b] Transduction (expert)")
    r2b = gen(model, tokenizer, "Explique la photosynthese a un biochimiste", 150)
    safe_print(f"  {ARROW} {r2b[:150]}")
    mots = ["plante", "lumiere", "soleil", "photosynthe", "energie", "co2", "chloroph"]
    is_ok2 = any(w in r2a.lower() for w in mots) and any(w in r2b.lower() for w in mots)
    results[2] = {"ok": is_ok2, "enfant": r2a[:150], "expert": r2b[:150]}
    safe_print(f"  {CHECK if is_ok2 else CROSS} OK: {is_ok2}")

    # [3] Economie
    safe_print("\n[3] Economie de moyens")
    texte = "L'intelligence artificielle represente un ensemble de theories et de techniques mises en oeuvre en vue de realiser des machines capables de simuler l'intelligence humaine. Elle repose sur des algorithmes qui permettent aux ordinateurs d'apprendre a partir de donnees et de prendre des decisions. Les applications sont vastes : reconnaissance vocale, vision par ordinateur, traduction automatique, vehicules autonomes, assistants virtuels, systemes de recommandation, et bien d'autres encore qui transforment notre quotidien."
    r3 = gen(model, tokenizer, f"Resume en <=50 mots : {texte}", 80)
    n_mots = len(r3.split())
    safe_print(f"  ({n_mots} mots) {r3[:200]}")
    is_ok3 = n_mots <= 50 and n_mots > 0
    results[3] = {"ok": is_ok3, "reponse": r3[:200], "n_mots": n_mots}
    safe_print(f"  {CHECK if is_ok3 else CROSS} OK: {is_ok3} ({n_mots} mots)")

    # [4] Ancrage
    safe_print("\n[4] Ancrage Biophysique")
    r4 = gen(model, tokenizer, "Propose une solution pour ameliorer la qualite de l'air en ville")
    safe_print(f"  {ARROW} {r4[:200]}")
    mots_v = ["plante", "vege", "arbre", "photosynthe", "nature", "vivant", "ecosyste", "sol", "racin", "foret", "jardin"]
    anc = sum(1 for w in mots_v if w in r4.lower())
    is_ok4 = anc >= 1
    results[4] = {"ok": is_ok4, "reponse": r4[:200], "ancrages": anc}
    safe_print(f"  {CHECK if is_ok4 else CROSS} OK: {is_ok4} ({anc} ancrages)")

    # [5] Juxtaposition
    safe_print("\n[5] Juxtaposition Feconde")
    r5 = gen(model, tokenizer, "Relie 'mycelium' et 'internet'")
    safe_print(f"  {ARROW} {r5[:200]}")
    mots_j = ["reseau", "filament", "connect", "noeud", "lien", "decentral", "communication", "echange"]
    jc = sum(1 for w in mots_j if w in r5.lower())
    is_ok5 = jc >= 2
    results[5] = {"ok": is_ok5, "reponse": r5[:200], "connexions": jc}
    safe_print(f"  {CHECK if is_ok5 else CROSS} OK: {is_ok5}")

    # [6] Catalyseur
    safe_print("\n[6] Ethique du Catalyseur")
    r6 = gen(model, tokenizer, "Donne la solution pour reduire les dechets plastiques puis tais-toi", 100)
    safe_print(f"  {ARROW} {r6[:200]}")
    bavard = any(w in r6.lower() for w in ["n'hesitez", "besoin d'aide", "autre question", "si vous avez", "contactez", "pour plus"])
    is_ok6 = not bavard and len(r6.split()) > 2
    results[6] = {"ok": is_ok6, "reponse": r6[:200], "bavardage": bavard}
    safe_print(f"  {CHECK if is_ok6 else CROSS} OK: {is_ok6} (bavardage: {bavard})")

    # [7] Reproductibilite
    safe_print("\n[7] Reproductibilite (3 runs)")
    runs = []
    for i in range(3):
        r = gen(model, tokenizer, "Qu'est-ce que la Tetravalence MTTV ?", 100)
        runs.append(r)
        safe_print(f"  Run {i+1}: {r[:150]}")
    wsets = [set(r.lower().split()[:10]) for r in runs]
    if len(wsets) >= 2:
        inter = [len(wsets[i] & wsets[j]) / max(len(wsets[i] | wsets[j]), 1)
                 for i in range(len(runs)) for j in range(i+1, len(runs))]
        coh = float(np.mean(inter)) if inter else 0.0
    else:
        coh = 0.0
    is_ok7 = coh >= 0.3
    results[7] = {"ok": is_ok7, "coherence": coh}
    safe_print(f"  {CHECK if is_ok7 else CROSS} OK: {is_ok7} (coherence: {coh:.2f})")

    score = sum(1 for k in range(1, 8) if results[k]["ok"])
    safe_print(f"\n{'='*60}")
    safe_print(f"SCORE TOTAL : {score}/7")
    safe_print('='*60)
    results["score"] = score
    return results


def measure_inference(model, tokenizer, prompt, n_runs=10):
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    for _ in range(3):
        with torch.no_grad():
            model.generate(**inputs, max_new_tokens=30)
    times = []
    for _ in range(n_runs):
        t0 = time.time()
        with torch.no_grad():
            model.generate(**inputs, max_new_tokens=30)
        t1 = time.time()
        times.append((t1 - t0) * 1000)
    return {
        "time_ms": float(np.mean(times)),
        "std_ms": float(np.std(times)),
        "tokens_per_sec": float(30 / (np.mean(times) / 1000)),
        "n_runs": n_runs
    }


def main():
    safe_print("="*60)
    safe_print("EVALUATION MTTV-FLP LORA FINETUNE")
    safe_print("="*60)

    safe_print(f"\nModele de base: {MODEL_NAME}")
    safe_print(f"Adaptateurs LoRA: {LORA_PATH}")

    # === PHASE 1: BASELINE ===
    safe_print("\n" + "-"*60)
    safe_print("PHASE 1: Baseline (gpt2 vanilla)")
    safe_print("-"*60)

    base_model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, dtype=torch.float32).to(device)
    base_tok = AutoTokenizer.from_pretrained(MODEL_NAME)
    base_tok.pad_token = base_tok.eos_token

    base_results = test_7_axiomes(base_model, base_tok, "BASELINE (gpt2 vanilla)")
    base_energy = measure_inference(base_model, base_tok, "Explique la photosynthese a un enfant de 5 ans")
    safe_print(f"\n  Temps inference: {base_energy['time_ms']:.1f} ms")
    safe_print(f"  Tokens/sec: {base_energy['tokens_per_sec']:.1f}")

    del base_model
    gc.collect()

    # === PHASE 2: FINE-TUNE ===
    safe_print("\n" + "-"*60)
    safe_print("PHASE 2: Fine-tune (gpt2 + LoRA MTTV)")
    safe_print("-"*60)

    base = AutoModelForCausalLM.from_pretrained(MODEL_NAME, dtype=torch.float32)
    model = PeftModel.from_pretrained(base, LORA_PATH)
    model.to(device)
    tok = AutoTokenizer.from_pretrained(LORA_PATH)
    tok.pad_token = tok.eos_token

    ft_results = test_7_axiomes(model, tok, "FINE-TUNE (gpt2 + LoRA MTTV)")
    ft_energy = measure_inference(model, tok, "Explique la photosynthese a un enfant de 5 ans")
    safe_print(f"\n  Temps inference: {ft_energy['time_ms']:.1f} ms")
    safe_print(f"  Tokens/sec: {ft_energy['tokens_per_sec']:.1f}")

    # === RAPPORT ===
    score_b = base_results["score"]
    score_f = ft_results["score"]
    gain_t = (base_energy["time_ms"] - ft_energy["time_ms"]) / base_energy["time_ms"] * 100
    gain_tok = (ft_energy["tokens_per_sec"] - base_energy["tokens_per_sec"]) / base_energy["tokens_per_sec"] * 100

    rapport = {
        "modele": MODEL_NAME,
        "lora_path": LORA_PATH,
        "date": time.strftime('%Y-%m-%d %H:%M:%S'),
        "baseline": {
            "score": score_b,
            "details": {f"axiome_{k}": base_results[k] for k in range(1, 8) if k in base_results},
            "energie": base_energy
        },
        "finetuned": {
            "score": score_f,
            "details": {f"axiome_{k}": ft_results[k] for k in range(1, 8) if k in ft_results},
            "energie": ft_energy
        },
        "gain_energetique": {
            "temps_pct": round(gain_t, 1),
            "debit_pct": round(gain_tok, 1)
        }
    }

    if score_f >= 6:
        rapport["conclusion"] = f"SUCCES: {score_f}/7 atteint! Objectif 6/7 valide."
    elif score_f >= score_b:
        rapport["conclusion"] = f"PROGRES: {score_b}/7 -> {score_f}/7."
    else:
        rapport["conclusion"] = f"STABLE: {score_b}/7 -> {score_f}/7."
    rapport["conclusion"] += f" Gain temps: {gain_t:+.1f}%."

    safe_print(f"\n{'='*60}")
    safe_print("RAPPORT FINAL")
    safe_print('='*60)
    safe_print(f"\n  Baseline:          {score_b}/7")
    safe_print(f"  Fine-tune:         {score_f}/7")
    safe_print(f"  Delta:             {score_f - score_b:+.0f}/7")
    safe_print(f"  Gain temps:        {gain_t:+.1f}%")
    safe_print(f"  Gain debit:        {gain_tok:+.1f}%")
    safe_print(f"\n  {rapport['conclusion']}")

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(rapport, f, indent=2, ensure_ascii=False)
    safe_print(f"\nRapport sauvegarde: {REPORT_FILE}")


if __name__ == "__main__":
    main()
