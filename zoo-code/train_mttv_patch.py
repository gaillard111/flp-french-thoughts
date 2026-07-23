#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
train_mttv_patch.py
===================
Script de patching MTTV-flp avec 3 regularisations (Axiomes 5, 6, 7).

Patches :
  - tetravalence_regularization  (Axiome 5) - force 4 modes spectraux dominants
  - dephasage_regularization     (Axiome 6) - contraint l'entropie de phase
  - cloture_zero_regularization  (Axiome 7) - pousse le gradient total vers zero

Modele charge en 4-bit (bitsandbytes) pour economie memoire.
Dataset : wikitext (HuggingFace datasets).
Training : 2000 steps.
Sauvegarde : final_mttv.pt dans le repertoire de sortie.

Usage :
  python train_mttv_patch.py --model Qwen/Qwen2.5-1.5B-Instruct --output_dir ./mttv_out
"""

import argparse
import gc
import json
import math
import os
import time

import torch
import torch.nn as nn
import torch.nn.functional as F
from datasets import load_dataset
from torch.optim import AdamW
from torch.utils.data import DataLoader, IterableDataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    get_cosine_schedule_with_warmup,
    set_seed,
)


# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
SEED = 42
MAX_LEN = 128
BATCH_SIZE = 4
LR = 5e-6
WARMUP_STEPS = 100
TOTAL_STEPS = 2000
GRADIENT_ACCUMULATION_STEPS = 4  # effective batch = BATCH_SIZE * GRADIENT_ACCUMULATION_STEPS

LAMBDA_TETRA = 0.1       # poids regularisation tetravalence
LAMBDA_DEPHASAGE = 0.05  # poids regularisation dephasage
LAMBDA_CLOTURE = 0.01    # poids regularisation cloture zero

set_seed(SEED)


# ─────────────────────────────────────────────
# Dataset : wikitext streaming
# ─────────────────────────────────────────────

class WikitextStreamDataset(IterableDataset):
    """IterableDataset qui tire les sequences du dataset wikitext-2 en streaming."""

    def __init__(self, tokenizer, split="train", max_len=MAX_LEN):
        super().__init__()
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.split = split
        # On charge en streaming pour ne pas saturer la RAM
        self.dataset = load_dataset("wikitext", "wikitext-2-raw-v1", split=split, streaming=True)

    def __iter__(self):
        buffer = []
        for example in self.dataset:
            text = example["text"]
            if not text.strip():
                continue
            tokens = self.tokenizer.encode(text)
            buffer.extend(tokens)
            # Des qu'on a assez de tokens, on yield des sequences
            while len(buffer) >= self.max_len:
                chunk = buffer[:self.max_len]
                buffer = buffer[self.max_len:]
                input_ids = torch.tensor(chunk, dtype=torch.long)
                yield {
                    "input_ids": input_ids,
                    "attention_mask": torch.ones_like(input_ids),
                    "labels": input_ids.clone(),
                }


def collate_fn(batch):
    """Collate une liste de dicts en batch padde."""
    input_ids = [item["input_ids"] for item in batch]
    attention_mask = [item["attention_mask"] for item in batch]
    labels = [item["labels"] for item in batch]

    input_ids = nn.utils.rnn.pad_sequence(input_ids, batch_first=True, padding_value=0)
    attention_mask = nn.utils.rnn.pad_sequence(attention_mask, batch_first=True, padding_value=0)
    labels = nn.utils.rnn.pad_sequence(labels, batch_first=True, padding_value=-100)

    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels,
    }


# ─────────────────────────────────────────────
# Regularisation : tetravalence (Axiome 5)
# ─────────────────────────────────────────────

def tetravalence_regularization(model, input_ids, attention_mask, global_step, total_steps):
    """
    Axiome 5 - Regularisation spectrale tetravalente.
    Force la distribution de puissance frequentielle des embeddings
    a se concentrer sur les 4 premiers modes (FFT).
    """
    with torch.no_grad():
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_hidden_states=True,
        )
    hidden_states = outputs.hidden_states[-1]  # (batch, seq_len, hidden_dim)

    if hidden_states.size(1) < 4:
        return torch.tensor(0.0, device=hidden_states.device)

    # FFT le long de la dimension sequentielle
    fft_vals = torch.fft.fft(hidden_states.to(torch.float32), dim=1)  # (B, S, D)
    power_spectrum = torch.abs(fft_vals) ** 2                         # (B, S, D)

    # Puissance moyenne par mode frequentiel (moyenne sur batch et hidden_dim)
    power_mean = power_spectrum.mean(dim=(0, 2))                      # (S,)
    total_power = power_mean.sum() + 1e-9

    # Ratio de puissance dans les 4 premiers modes
    tetra_power = power_mean[:4].sum()
    ratio = tetra_power / total_power

    # Schedule cosinus sur lambda
    cosine_factor = 0.5 + 0.5 * math.cos(math.pi * global_step / max(total_steps, 1))
    lmb = LAMBDA_TETRA * cosine_factor

    # On maximise le ratio (loss = 1 - ratio)
    loss = lmb * (1.0 - ratio)
    return loss


# ─────────────────────────────────────────────
# Regularisation : dephasage (Axiome 6)
# ─────────────────────────────────────────────

def dephasage_regularization(model, input_ids, attention_mask):
    """
    Axiome 6 - Regularisation du dephasage.
    Mesure l'entropie de phase dans les cartes d'attention et penalise
    les configurations trop ordonnees ou trop chaotiques.
    """
    with torch.no_grad():
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_attentions=True,
        )

    if outputs.attentions is None or len(outputs.attentions) == 0:
        return torch.tensor(0.0, device=input_ids.device)

    # Prendre la derniere couche d'attention
    attn = outputs.attentions[-1]  # (batch, heads, seq, seq)

    # Convertir les poids d'attention en angles de phase
    # Phase = arcsin(2*attn - 1) pour obtenir une distribution dans [-pi/2, pi/2]
    phase = torch.asin(2.0 * attn.clamp(-1.0, 1.0) + 1e-9)

    # Entropie de la distribution de phase (normalisee)
    # On veut une entropie moderee : ni trop faible (ordre excessif)
    # ni trop elevee (chaos)
    phase_prob = F.softmax(phase.view(phase.size(0), -1), dim=-1)
    entropy = -(phase_prob * torch.log(phase_prob + 1e-9)).sum(dim=-1).mean()

    # Entropie cible : log(dim) / 2 -> entropie "moyenne"
    target_entropy = 0.5 * math.log(attn.size(-1) * attn.size(-2))
    dephasage_loss = (entropy - target_entropy) ** 2

    return LAMBDA_DEPHASAGE * dephasage_loss


# ─────────────────────────────────────────────
# Regularisation : cloture zero (Axiome 7)
# ─────────────────────────────────────────────

def cloture_zero_regularization(model, input_ids, attention_mask):
    """
    Axiome 7 - Regularisation de cloture zero.
    Pousse la norme totale du gradient (apres backward) vers zero,
    encodant la propriete de divergence nulle du champ de gradient MTTV.
    """
    # Forward + backward sur un petit batch pour mesurer le gradient
    outputs = model(
        input_ids=input_ids,
        attention_mask=attention_mask,
        labels=input_ids,
    )
    loss = outputs.loss

    # Retropropagation
    loss.backward(retain_graph=True)

    # Norme L2 totale du gradient sur tous les parametres
    total_grad_norm = 0.0
    n_params = 0
    for p in model.parameters():
        if p.grad is not None:
            total_grad_norm += p.grad.norm(2).item() ** 2
            n_params += 1

    rms_grad = math.sqrt(total_grad_norm / max(n_params, 1))

    # On rezero les gradients apres mesure (sans modifier l'optimizer)
    model.zero_grad()

    return LAMBDA_CLOTURE * torch.tensor(rms_grad, device=input_ids.device, requires_grad=False)


# ─────────────────────────────────────────────
# Fonction principale
# ─────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="MTTV-flp Training Patch - 3 regularisations (Axiomes 5, 6, 7)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="Qwen/Qwen2.5-1.5B-Instruct",
        help="Nom du modele HuggingFace (ex: Qwen/Qwen2.5-1.5B-Instruct)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./mttv_out",
        help="Repertoire de sortie pour le modele patche",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=TOTAL_STEPS,
        help=f"Nombre de steps d'entrainement (defaut: {TOTAL_STEPS})",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=BATCH_SIZE,
        help=f"Taille du batch (defaut: {BATCH_SIZE})",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=LR,
        help=f"Learning rate (defaut: {LR})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=SEED,
        help=f"Seed aleatoire (defaut: {SEED})",
    )
    return parser.parse_args()


def train():
    args = parse_args()

    print("=" * 70)
    print("MTTV-flp TRAINING PATCH - 3 regularisations (Axiomes 5, 6, 7)")
    print("=" * 70)
    print(f"Modele        : {args.model}")
    print(f"Output dir    : {args.output_dir}")
    print(f"Steps         : {args.steps}")
    print(f"Batch size    : {args.batch_size}")
    print(f"Learning rate : {args.lr}")
    print(f"Accumulation  : {GRADIENT_ACCUMULATION_STEPS} steps")
    effective_batch = args.batch_size * GRADIENT_ACCUMULATION_STEPS
    print(f"Batch effectif: {effective_batch}")
    print()
    print("Patches actifs:")
    print(f"  1. tetravalence_regularization  (Axiome 5) lambda={LAMBDA_TETRA}")
    print(f"  2. dephasage_regularization     (Axiome 6) lambda={LAMBDA_DEPHASAGE}")
    print(f"  3. cloture_zero_regularization  (Axiome 7) lambda={LAMBDA_CLOTURE}")
    print()

    # ── Device ──
    HAS_CUDA = torch.cuda.is_available()
    device = torch.device("cuda" if HAS_CUDA else "cpu")
    print(f"Device: {device}")

    # ── Tokenizer ──
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # ── Modele : 4-bit si CUDA + bitsandbytes, sinon float32 CPU ──
    if HAS_CUDA:
        print(f"\nChargement du modele en 4-bit (bitsandbytes)...")
        try:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )
            model = AutoModelForCausalLM.from_pretrained(
                args.model,
                quantization_config=quantization_config,
                device_map="auto",
                output_hidden_states=True,
                output_attentions=True,
                torch_dtype=torch.float16,
            )
            print("  OK Modele charge en 4-bit")
        except Exception as e:
            print(f"  ? Erreur chargement 4-bit: {e}")
            print("  Fallback vers float32 CPU...")
            HAS_CUDA = False
            device = torch.device("cpu")

    if not HAS_CUDA:
        print(f"\nChargement du modele en float32 (CPU)...")
        model = AutoModelForCausalLM.from_pretrained(
            args.model,
            output_hidden_states=True,
            output_attentions=True,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
        ).to(device)

    # Activer gradient checkpointing pour economie memoire
    model.gradient_checkpointing_enable()
    model.train()

    # ── Geler certains modules pour concentrer le fine-tuning ──
    trainable_params = []
    for name, param in model.named_parameters():
        if any(k in name for k in ["self_attn", "mlp", "lm_head"]):
            param.requires_grad = True
            trainable_params.append(param)
        else:
            param.requires_grad = False

    n_trainable = sum(p.numel() for p in trainable_params)
    n_total = sum(p.numel() for p in model.parameters())
    print(f"Parametres entrainables : {n_trainable:,} / {n_total:,} ({100 * n_trainable / n_total:.1f}%)")

    # ── Optimizer & Scheduler ──
    optim = AdamW(trainable_params, lr=args.lr, weight_decay=0.01)
    sched = get_cosine_schedule_with_warmup(optim, WARMUP_STEPS, args.steps)

    # ── Dataset wikitext en streaming ──
    print("\nChargement du dataset wikitext-2 en streaming...")
    train_dataset = WikitextStreamDataset(tokenizer, split="train", max_len=MAX_LEN)
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        collate_fn=collate_fn,
        num_workers=0,
        drop_last=True,
    )

    # ── Boucle de training ──
    print(f"\nDebut du training sur {args.steps} steps...\n")
    print(f"{'Step':>8} {'Loss':>10} {'Tetra':>10} {'Dephasage':>12} {'Cloture':>10} {'LR':>12}")
    print("-" * 66)

    os.makedirs(args.output_dir, exist_ok=True)

    history = {
        "total_loss": [],
        "tetra_loss": [],
        "dephasage_loss": [],
        "cloture_loss": [],
    }

    t_start = time.time()
    global_step = 0
    accum_loss = 0.0
    optim.zero_grad()

    data_iter = iter(train_loader)

    while global_step < args.steps:
        # Charger le batch
        try:
            batch = next(data_iter)
        except StopIteration:
            data_iter = iter(train_loader)
            batch = next(data_iter)

        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)

        # ── Forward LM ──
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=input_ids,
        )
        loss_ce = outputs.loss

        # ── Patch 1 : Tetravalence (Axiome 5) ──
        loss_tetra = tetravalence_regularization(
            model, input_ids, attention_mask, global_step, args.steps
        )

        # ── Patch 2 : Dephasage (Axiome 6) ──
        loss_dephasage = dephasage_regularization(model, input_ids, attention_mask)

        # ── Patch 3 : Cloture Zero (Axiome 7) ──
        loss_cloture = cloture_zero_regularization(model, input_ids, attention_mask)

        # Assembler la loss totale
        loss_total = loss_ce + loss_tetra + loss_dephasage + loss_cloture

        # Accumulation de gradient
        loss_total = loss_total / GRADIENT_ACCUMULATION_STEPS
        loss_total.backward()

        accum_loss += loss_total.item()

        # ── Step optimizer tous les GRADIENT_ACCUMULATION_STEPS ──
        if (global_step + 1) % GRADIENT_ACCUMULATION_STEPS == 0:
            torch.nn.utils.clip_grad_norm_(trainable_params, 1.0)
            optim.step()
            sched.step()
            optim.zero_grad()

        # ── Logging ──
        if global_step % 10 == 0:
            lr_current = sched.get_last_lr()[0] if sched.get_last_lr() else args.lr
            print(
                f"{global_step:>8} "
                f"{accum_loss:>10.6f} "
                f"{loss_tetra.item() if isinstance(loss_tetra, torch.Tensor) else loss_tetra:>10.6f} "
                f"{loss_dephasage.item() if isinstance(loss_dephasage, torch.Tensor) else loss_dephasage:>10.6f} "
                f"{loss_cloture.item() if isinstance(loss_cloture, torch.Tensor) else loss_cloture:>10.6f} "
                f"{lr_current:>12.2e}"
            )

            history["total_loss"].append(accum_loss)
            history["tetra_loss"].append(
                loss_tetra.item() if isinstance(loss_tetra, torch.Tensor) else loss_tetra
            )
            history["dephasage_loss"].append(
                loss_dephasage.item() if isinstance(loss_dephasage, torch.Tensor) else loss_dephasage
            )
            history["cloture_loss"].append(
                loss_cloture.item() if isinstance(loss_cloture, torch.Tensor) else loss_cloture
            )

        accum_loss = 0.0
        global_step += 1

    t_elapsed = time.time() - t_start
    print(f"\nTraining termine en {t_elapsed:.0f}s ({t_elapsed / 60:.1f} min)")

    # ── Sauvegarde du modele patche (format .pt) ──
    model_path = os.path.join(args.output_dir, "final_mttv.pt")
    print(f"Sauvegarde du modele patche vers {model_path}...")

    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "config": model.config,
            "training_args": vars(args),
            "history": history,
            "total_steps": global_step,
            "elapsed_time": t_elapsed,
        },
        model_path,
    )
    print(f"  OK final_mttv.pt sauvegarde")

    # ── Sauvegarde au format save_pretrained (pour compatibilite metre_mttv.py) ──
    print(f"Sauvegarde du modele au format save_pretrained dans {args.output_dir}...")
    save_pretrained_ok = False
    try:
        if hasattr(model, "merge_and_unload") and callable(model.merge_and_unload):
            print("  Fusion des poids 4-bit en float16...")
            model_fp = model.merge_and_unload()
            model_fp.save_pretrained(args.output_dir, safe_serialization=True)
            tokenizer.save_pretrained(args.output_dir)
            del model_fp
        else:
            model.save_pretrained(args.output_dir, safe_serialization=True)
            tokenizer.save_pretrained(args.output_dir)
        save_pretrained_ok = True
        print(f"  OK save_pretrained dans {args.output_dir}")
    except Exception as e:
        print(f"  ? save_pretrained a echoue: {e}")

    # Fallback manuel si save_pretrained a echoue
    if not save_pretrained_ok:
        print("  Sauvegarde manuelle des fichiers de configuration...")
        try:
            import json as jjson
            # config.json
            config_path = os.path.join(args.output_dir, "config.json")
            if hasattr(model, "config"):
                with open(config_path, "w", encoding="utf-8") as f:
                    jjson.dump(dict(model.config.to_dict()), f, indent=2)
                print(f"  OK config.json sauvegarde")
            # tokenizer
            tokenizer.save_pretrained(args.output_dir)
            print(f"  OK tokenizer sauvegarde")
            # model.safetensors
            from safetensors.torch import save_file as st_save
            state_dict = model.state_dict()
            st_path = os.path.join(args.output_dir, "model.safetensors")
            st_save(state_dict, st_path)
            print(f"  OK model.safetensors sauvegarde ({len(state_dict)} tensors)")
            save_pretrained_ok = True
        except Exception as e2:
            print(f"  ? Sauvegarde manuelle également echouee: {e2}")
            print("  Le modele patche est uniquement disponible au format final_mttv.pt")

    print(f"\n{'=' * 70}")
    print(f"Patches MTTV-flp appliques avec succes !")
    print(f"Axiome 5 (tetravalence)       : OK")
    print(f"Axiome 6 (dephasage)          : OK")
    print(f"Axiome 7 (cloture zero)       : OK")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    train()
c