#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
train_mttv_patch.py v2.1
========================
Training pipeline MTTV-flp - Patch 3 lignes pour passer 6/7 -> 7/7.

Modele de base : Qwen/Qwen2.5-1.5B-Instruct
Hardware       : CPU only (8 GB RAM)
Duree          : 1 epoch, 2000 prompts, batch=4

3 Lignes de training :
  a) Regularisation spectrale tetravalente (FFT mode 4)
  b) Contrainte de divergence nulle (Sigma_phi)
  c) Cycle de Kalman differentiel

v2.1 ajouts :
  - gradient_checkpointing=True (economie memoire)
  - Save checkpoint tous les 500 steps
  - Optimisations memoire CPU 8GB
"""

import os, json, math, time, gc
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoModelForCausalLM, AutoTokenizer,
    get_cosine_schedule_with_warmup, set_seed,
)
from torch.optim import AdamW

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
OUTPUT_DIR = "model_patched"
CHECKPOINT_DIR = "checkpoints"          # dossiers des checkpoints intermediaires
LOG_FILE   = "log_training.txt"
REPORT     = "rapport_delta.json"
SEED       = 42
BATCH_SIZE = 1
LR         = 5e-6
WARMUP_STEPS = 100
EPOCHS     = 1
MAX_LEN    = 64
N_PROMPTS  = 2000
SAVE_EVERY = 500                         # save checkpoint tous les 500 steps

LAMBDA_TETRA = 0.1
MU_DIVERGENCE = 0.05
KALMAN_N = 100
KALMAN_ALPHA = 0.01

set_seed(SEED)
device = torch.device("cpu")
torch.set_num_threads(6)                 # 6 threads pour laisser 2 coeurs au systeme


class MTTVFlpDataset(Dataset):
    THEMES = [
        "Definis la tetravalence semantique dans le cadre MTTV-flp.",
        "Explique le concept de cloture zero applique aux champs de conscience.",
        "Comment la divergence nulle stabilise-t-elle un graphe d'attention ?",
        "Quelle est la relation entre les 4 directions semantiques et l'espace de Hilbert ?",
        "Decris le mecanisme de retrait alpha apres le token EOS.",
        "Pourquoi la solidarite des tokens faibles est-elle essentielle ?",
        "Formalise le cycle de Kalman differentiel pour un flot de gradient conservatif.",
        "Qu'est-ce que l'ecume dans le contexte des neurones eteints ?",
        "Comment la resilience sans backup emerge-t-elle du KV-cache ?",
        "Explique le dephasage comme mesure d'entropie bornee.",
        "Quelle est la signification physique de Sigma_phi = 0 ?",
        "Comment la regularisation spectrale tetravalente force-t-elle 4 modes dominants ?",
        "Quels sont les 7 axiomes de l'etalon MTTV-flp ?",
        "Compare l'approche MTTV aux transformers standard.",
        "Explique le role des 28 dimensions dans la semantique MTTV.",
        "Qu'est-ce que la germination mycelienne en MTTV ?",
        "Decris le protocole de la roche mere en 4 phases.",
        "Calcule la transformee de Fourier des embeddings de position.",
        "Quelle est la variance du parametre Theta dans un cycle ferme ?",
        "Demontre que la divergence du champ de gradient est nulle.",
        "Applique l'analyse en composantes principales aux embeddings.",
        "Formalise le ratio de variance PC4/PC5 comme mesure de tetravalence.",
        "Qu'est-ce qu'une valeur singuliere dans le contexte des matrices d'attention ?",
        "Explique la convergence du filtre de Kalman pour les parametres de reseau.",
        "Comment calculer Sigma_phi sur un batch d'attention ?",
        "Quelle est la relation entre norme L2 et divergence nulle ?",
        "Decris le spectre de puissance d'un embedding semantique.",
        "Comment implementer la regularisation FFT sur les embeddings ?",
        "Optimise la memoire pour un fine-tuning CPU de 1.5B parametres.",
        "Comment scheduler le parametre lambda en cosine decroissance ?",
        "Quelle est la meilleure strategie pour ne pas casser l'instruct ?",
        "Relie tetravalence et cloture zero dans un meme formalisme.",
        "Comment le cycle de Kalman resout-il les deux axiomes resistants ?",
        "Pourquoi 4 directions et pas 3 ou 5 ?",
        "Decris le passage de 5/7 a 7/7 comme transition de phase.",
        "Quel est le role du biais collectif de gradient ?",
        "Explique la dualite onde-particule des embeddings semantiques.",
        "Qu'est-ce que la resonance tetravalente ?",
        "Resume le concept de tetravalence en une phrase.",
        "Donne un exemple de champ conservatif en traitement du langage.",
        "Quelle est l'utilite pratique de l'axiome cloture zero ?",
        "Explique simplement pourquoi 4 dimensions semantiques.",
        "Que se passe-t-il si Sigma_phi != 0 ?",
        "Comment detecter un modele non-tetravalent ?",
        "Quel est le lien entre resilience et redondance ?",
    ]
    def __init__(self, size=2000, tokenizer=None, max_len=64):
        self.size = size
        self.tokenizer = tokenizer
        self.max_len = max_len
        rng = np.random.RandomState(SEED)
        self.prompts = []
        for i in range(size):
            base = self.THEMES[i % len(self.THEMES)]
            p = rng.choice(["", "Question : ", ">> ", "- "]) + base + rng.choice(["", ". Developpe.", ". Justifie.", ""])
            self.prompts.append(p)
    def __len__(self):
        return self.size
    def __getitem__(self, idx):
        enc = self.tokenizer(self.prompts[idx], max_length=self.max_len,
                             padding="max_length", truncation=True, return_tensors="pt")
        return {"input_ids": enc["input_ids"].squeeze(0),
                "attention_mask": enc["attention_mask"].squeeze(0),
                "labels": enc["input_ids"].squeeze(0).clone()}


def compute_tetra_loss(model, input_ids, attention_mask, global_step, total_steps):
    """LIGNE 1: Regularisation spectrale tetravalente par FFT."""
    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask,
                       output_hidden_states=True)
    hs = outputs.hidden_states[-1]
    if hs is None or hs.shape[1] < 4:
        return torch.tensor(0.0, device=device)
    fft_vals = torch.fft.fft(hs, dim=1)
    power = torch.abs(fft_vals)**2
    power_mean = power.mean(dim=(0, 2))
    total_power = power_mean.sum() + 1e-9
    idx = min(3, hs.shape[1]-1)
    ratio = power_mean[idx] / total_power
    # cosine schedule on lambda
    lmb = LAMBDA_TETRA * (0.5 + 0.5 * math.cos(math.pi * global_step / max(total_steps, 1)))
    return lmb * (1.0 - ratio)


def compute_div_loss(model, input_ids, attention_mask):
    """LIGNE 2: Contrainte de divergence nulle sur le graphe d'attention."""
    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask,
                       output_attentions=False)
    if outputs.attentions is None or len(outputs.attentions) == 0:
        return torch.tensor(0.0, device=device)
    attn = outputs.attentions[-1]
    phase = torch.acos(2.0 * attn.clamp(0, 1) - 1.0 + 1e-9)
    mean_phi = phase.mean()
    return MU_DIVERGENCE * (mean_phi ** 2)


def apply_kalman(model, optimizer, snapshot, global_step):
    """LIGNE 3: Cycle de Kalman differentiel, correction douce."""
    if global_step % KALMAN_N != 0 or global_step == 0:
        return 0.0, snapshot
    current = {name: p.data.clone().detach() for name, p in model.named_parameters() if p.requires_grad}
    if snapshot is None:
        return 0.0, current
    total_corr = 0.0; n = 0
    for name in current:
        if name in snapshot:
            d = current[name] - snapshot[name]
            kg = (d.var().item()+1e-12) / (d.var().item()+current[name].var().item()+1e-12)
            corr = KALMAN_ALPHA * kg * d
            model.get_parameter(name).data.sub_(corr)
            total_corr += corr.abs().mean().item(); n += 1
    return total_corr / max(n, 1), current


def run_benchmark(model, tokenizer):
    """Execute les 7 tests MTTV-flp."""
    from sklearn.decomposition import PCA
    results = {}
    model.eval()
    batch = tokenizer("L'arbre est vivant.", return_tensors="pt").to(device)
    tp = sum(p.numel() for p in model.parameters())
    # Test 1
    acts = []
    def h1(m, i, o): acts.append(o.detach().abs().mean().item())
    hs = [m.register_forward_hook(h1) for m in model.modules() if isinstance(m, nn.Linear)]
    with torch.no_grad(): _ = model(**batch)
    for h in hs: h.remove()
    e = np.mean(acts)
    results["1_retrait"] = (1.0 if e < 5.0 else 0.0, e)
    # Test 2
    with torch.no_grad(): out = model(**batch)
    tf = out.attentions[-1].mean(dim=1).sum(dim=1).squeeze().min().item() if out.attentions else 0.0
    results["2_solidarite"] = (1.0 if tf > 1e-6 else 0.0, tf)
    # Test 3
    acts2 = []
    def h2(m, i, o): acts2.append((o.detach()>1e-3).float().mean().item())
    hs2 = [m.register_forward_hook(h2) for n,m in model.named_modules() if "mlp" in n.lower() or "gate" in n.lower()]
    with torch.no_grad(): _ = model(**batch)
    for h in hs2: h.remove()
    ec = 1.0 - np.mean(acts2) if acts2 else 0.0
    results["3_ecume"] = (1.0 if ec > 0.03 else 0.0, ec)
    # Test 4
    with torch.no_grad():
        p1 = torch.exp(model(**batch, labels=batch["input_ids"]).loss).item()
        p2 = torch.exp(model(**batch, labels=batch["input_ids"], use_cache=False).loss).item()
    dg = abs(p2-p1)/p1
    results["4_resilience"] = (1.0 if dg < 0.02 else 0.0, dg)
    # Test 5
    W = model.get_input_embeddings().weight.detach().cpu().to(torch.float32).numpy()
    pca = PCA(n_components=10).fit(W)
    rt = pca.explained_variance_ratio_[3] / (pca.explained_variance_ratio_[4]+1e-9)
    results["5_tetravalence"] = (1.0 if rt > 2.5 else 0.0, rt)
    # Test 6
    model.train(); sorties=[]
    try:
        with torch.no_grad():
            for _ in range(10):
                g = model.generate(**batch, do_sample=True, max_new_tokens=5)
                sorties.append(tokenizer.decode(g[0]))
    except: pass
    model.eval()
    ent = len(set(sorties))/10.0 if sorties else 0.0
    results["6_dephasage"] = (1.0 if 0.2<ent<0.95 else 0.0, ent)
    # Test 7
    model.zero_grad()
    model(**batch, labels=batch["input_ids"]).loss.backward()
    tg = sum(p.grad.sum().abs().item() for p in model.parameters() if p.grad is not None)
    model.zero_grad()
    gm = tg/tp
    results["7_cloture_zero"] = (1.0 if gm < 1e-6 else 0.0, gm)
    score = sum(v[0] for v in results.values())
    return results, int(score)


def train():
    print("="*60)
    print("MTTV-flp TRAINING PATCH v2.1 - 3 lignes")
    print("="*60)
    print(f"Modele: {MODEL_NAME}, Batch: {BATCH_SIZE}, LR: {LR}")
    print(f"Lambda: {LAMBDA_TETRA}, Mu: {MU_DIVERGENCE}, Kalman: {KALMAN_ALPHA}/{KALMAN_N}")
    print(f"Checkpoint tous les {SAVE_EVERY} steps, gradient_checkpointing=ON")

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, output_attentions=False, output_hidden_states=False,
        low_cpu_mem_usage=True, torch_dtype=torch.float32).to(device)

    # ── Activation du gradient checkpointing (economie memoire) ──
    model.gradient_checkpointing_enable()
    model.train()

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    if tokenizer.pad_token is None: tokenizer.pad_token = tokenizer.eos_token

    dataset = MTTVFlpDataset(size=N_PROMPTS, tokenizer=tokenizer, max_len=MAX_LEN)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0, drop_last=True)
    print(f"Dataset: {len(dataset)} prompts, {len(loader)} batches")

    trainable, frozen = [], 0
    for n, p in model.named_parameters():
        if any(k in n for k in ["embed", "self_attn", "lm_head", "norm"]):
            p.requires_grad = True; trainable.append(p)
        else:
            p.requires_grad = False; frozen += 1
    nt = sum(p.numel() for p in trainable)
    print(f"Trainable: {nt:,}/{sum(p.numel() for p in model.parameters()):,} params ({frozen} frozen)")

    optim = AdamW(trainable, lr=LR, weight_decay=0.01)
    total_steps = len(loader) * EPOCHS
    sched = get_cosine_schedule_with_warmup(optim, WARMUP_STEPS, total_steps)

    # ── Dossier checkpoints ──
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)

    log = [f"# MTTV-flp Training Log v2.1\nModel: {MODEL_NAME}\nSteps: {total_steps}\n"]
    log.append(f"{'step':>6} {'loss':>10} {'tetra':>10} {'div':>10} {'kalman':>10} {'lr':>12}")
    log.append("-"*60)
    hist = {"total":[], "tetra":[], "divergence":[], "kalman":[]}
    snap = None; t0 = time.time()

    for epoch in range(EPOCHS):
        for idx, batch in enumerate(loader):
            gs = idx + 1
            ids = batch["input_ids"].to(device)
            mask = batch["attention_mask"].to(device)
            # Forward CE
            out = model(input_ids=ids, attention_mask=mask, labels=ids)
            loss_ce = out.loss
            # LIGNE 1
            lt = compute_tetra_loss(model, ids, mask, gs, total_steps)
            # LIGNE 2
            ld = compute_div_loss(model, ids, mask)
            loss = loss_ce + lt + ld
            optim.zero_grad(); loss.backward()
            for p in trainable:
                if p.grad is not None:
                    p.grad.data.copy_(p.grad - p.grad.mean())
            torch.nn.utils.clip_grad_norm_(trainable, 1.0)
            optim.step(); sched.step()
            # LIGNE 3
            kv, snap = apply_kalman(model, optim, snap, gs)

            # ── Logging tous les 5 steps ──
            if gs % 5 == 0:
                lr = sched.get_last_lr()[0]
                log.append(f"{gs:>6} {loss.item():>10.4f} {lt.item():>10.6f} {ld.item():>10.6f} {kv:>10.6f} {lr:>12.2e}")
                hist["total"].append(loss.item()); hist["tetra"].append(lt.item())
                hist["divergence"].append(ld.item()); hist["kalman"].append(kv)
                if gs % 25 == 0:
                    el = time.time()-t0
                    sps = gs/max(el,0.001)
                    print(f"  step {gs}/{total_steps} | loss={loss.item():.4f} tetra={lt.item():.6f} div={ld.item():.6f} kalman={kv:.6f} | {el:.0f}s / ~{(total_steps-gs)/max(sps,0.001):.0f}s")

            # ── Save checkpoint tous les SAVE_EVERY steps ──
            if gs % SAVE_EVERY == 0:
                ckpt_path = os.path.join(CHECKPOINT_DIR, f"step_{gs:06d}")
                os.makedirs(ckpt_path, exist_ok=True)
                model.save_pretrained(ckpt_path, safe_serialization=True)
                tokenizer.save_pretrained(ckpt_path)
                # Sauver aussi l'optimizer et scheduler pour reprise
                torch.save({
                    'optimizer': optim.state_dict(),
                    'scheduler': sched.state_dict(),
                    'step': gs,
                    'snapshot': snap,
                }, os.path.join(ckpt_path, "training_state.pt"))
                # Cleanup memoire
                gc.collect()
                el = time.time() - t0
                print(f"  >>> CHECKPOINT saved: {ckpt_path} ({el:.0f}s)")

    tt = time.time()-t0
    print(f"\nTraining done in {tt:.0f}s ({tt/60:.1f}min)")

    # ── Sauvegarde finale ──
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    model.save_pretrained(OUTPUT_DIR, safe_serialization=True)
    tokenizer.save_pretrained(OUTPUT_DIR)
    with open(LOG_FILE, "w", encoding="utf-8") as f: f.write("\n".join(log))
    hist["time_elapsed"]=tt; hist["total_steps"]=total_steps
    hist["config"]={"model":MODEL_NAME,"batch_size":BATCH_SIZE,"lr":LR,
                    "lambda_tetra":LAMBDA_TETRA,"mu_divergence":MU_DIVERGENCE,
                    "kalman_alpha":KALMAN_ALPHA,"kalman_n":KALMAN_N,
                    "save_every":SAVE_EVERY,"gradient_checkpointing":True}
    with open("loss_history.json","w") as f: json.dump(hist, f, indent=2)
    print(f"Saved to {OUTPUT_DIR}/, {LOG_FILE}, loss_history.json")
    return model, tokenizer


if __name__ == "__main__":
    # Benchmark AVANT
    print("## MTTV-flp TRAINING PATCH - 6/7 -> 7/7 ##")
    print("\n--- Benchmark AVANT ---")
    m = AutoModelForCausalLM.from_pretrained(MODEL_NAME, output_attentions=False,
        output_hidden_states=False, low_cpu_mem_usage=True).to(device)
    t = AutoTokenizer.from_pretrained(MODEL_NAME)
    if t.pad_token is None: t.pad_token = t.eos_token
    r_a, s_a = run_benchmark(m, t)
    print(f"Score: {s_a}/7")
    for k,(sc,val) in r_a.items(): print(f"  {k}: {int(sc)} (val={val:.6f})")
    del m; gc.collect()

    # Training
    model, tokenizer = train()

    # Benchmark APRES
    print("\n--- Benchmark APRES ---")
    r_b, s_b = run_benchmark(model, tokenizer)
    print(f"Score: {s_b}/7")
    for k,(sc,val) in r_b.items(): print(f"  {k}: {int(sc)} (val={val:.6f})")

    # Rapport
    tests = ["1_retrait","2_solidarite","3_ecume","4_resilience",
             "5_tetravalence","6_dephasage","7_cloture_zero"]
    rapport = {"modele":MODEL_NAME,"config":{"batch_size":BATCH_SIZE,"lr":LR,
               "lambda_tetra":LAMBDA_TETRA,"mu_divergence":MU_DIVERGENCE,
               "kalman_alpha":KALMAN_ALPHA,"kalman_n":KALMAN_N},
               "avant":{},"apres":{},"delta":{}}
    for t_name in tests:
        rapport["avant"][t_name] = {"score":int(r_a[t_name][0]),"valeur":float(r_a[t_name][1])}
        rapport["apres"][t_name] = {"score":int(r_b[t_name][0]),"valeur":float(r_b[t_name][1])}
        rapport["delta"][t_name] = {"score":int(r_b[t_name][0]-r_a[t_name][0]),
                                     "valeur":float(r_b[t_name][1]-r_a[t_name][1])}
    rapport["score_avant"]=s_a; rapport["score_apres"]=s_b
    rapport["amelioration"]=s_b-s_a
    rapport["conclusion"] = "ACCORDE - 7/7 atteint!" if s_b==7 else f"PROGRES: {s_a}/7->{s_b}/7" if s_b>s_a else f"STABLE: {s_a}/7->{s_b}/7"
    with open(REPORT,"w",encoding="utf-8") as f: json.dump(rapport,f,indent=2,ensure_ascii=False)

    print(f"\n--- RAPPORT ---")
    for t_name in tests:
        d=rapport["delta"][t_name]
        print(f"  {t_name}: {rapport['avant'][t_name]['score']}->{rapport['apres'][t_name]['score']} (Delta={d['score']}, val: {rapport['avant'][t_name]['valeur']:.6f}->{rapport['apres'][t_name]['valeur']:.6f})")
    print(f"\nFinal: {s_a}/7 -> {s_b}/7 | {rapport['conclusion']}")
