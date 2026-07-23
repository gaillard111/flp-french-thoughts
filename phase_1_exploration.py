#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
phase_1_exploration.py  —  MTTV-FLP v2  Phase 1 : Exploration Instrumentée
=======================================================================
Automatise les 5 runs de cartographie de sensibilité du modèle sous 
perturbations de fonctions de perte (Lambda π, Mu η, Kalman Σ).

Usage (dans un notebook ou script):
    from phase_1_exploration import executer_phase_1_exploration
    results = executer_phase_1_exploration(model, tokenizer, dataset_val)

ou en mode autonome :
    python phase_1_exploration.py

OBJECTIF
  Générer la matrice de test 5-run et produire :
    - 5 rapports individuels  : rapport_runX_exploration.json
    - 1 tableau récapitulatif : console (markdown format)
    - 4 métriques par run     : Perplexité Ψ, Vitesse B, Pic VRAM Φ, Énergie I

RÉFÉRENCES MTTV-FLP
  - Porosité π  (Lambda)  : diversité/perméabilité des logits
  - Viscosité η (Mu)      : rétention/structure des logits
  - Singularité Σ (Kalman): filtre de Kalman à l'instant critique τ

Auteur  : Zoo / MTTV-FLP Research Pipeline
Version : 2.0 — Phase 1 Instrumented
"""

import os, sys, json, time, gc, math, copy, warnings
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Callable

import torch
import numpy as np

# ─── Attempt imports with helpful messages ────────────────────────────────
try:
    from transformers import (
        AutoModelForCausalLM, AutoTokenizer, LogitsProcessor, LogitsProcessorList
    )
except ImportError:
    raise ImportError(
        "transformers is required. Install:  pip install transformers"
    )

try:
    import psutil
except ImportError:
    psutil = None
    warnings.warn("psutil not installed; energy estimation will use formulaic TDP.")

# ============================================================================
# CONSTANTES GLOBALES
# ============================================================================
PROMPTS_FILE   = "mttv_val_gel_200.json"
REPORT_PREFIX  = "rapport_run{}_exploration.json"

# Paramètres de la matrice de test (spécifications Phase 1)
LAMBDA_COEFF   = 0.1    # Porosité π
MU_COEFF       = 0.05   # Viscosité η
KALMAN_COEFF   = 0.01   # Singularité Σ
KALMAN_TAU     = 5      # Instant critique τ (appliqué au step N de génération)

# Seuils pour le calcul d'énergie
TDP_GPU_WATTS  = 70.0   # TDP estimé T4 GPU (W) ;  ajuster selon le hardware
TDP_CPU_WATTS  = 15.0   # TDP CPU portion
ENERGY_OVERHEAD = 0.15  # 15% overhead (alimentation, ventilateurs, etc.)

# ============================================================================
# 1.  LogitsProcessors personnalisés  (Lambda, Mu, Kalman)
# ============================================================================

class LambdaPorosityProcessor(LogitsProcessor):
    """
    Porosité π — Injecte une diversité/perméabilité dans les logits.
    
    Principe :
        Ajoute un bruit gaussien calibré aux logits pour augmenter
        l'entropie de la distribution de sortie (diversité).
        Coefficient λ = 0.1 → perturbation modérée.
        
    Liens MTTV :
        Simule la perméabilité du "mycélium informationnel"
        en empêchant le modèle de se figer sur des patterns trop rigides.
    """
    
    def __init__(self, coefficient: float = LAMBDA_COEFF, seed: Optional[int] = 42):
        self.coefficient = coefficient
        self._rng = np.random.RandomState(seed)
    
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        # scores shape: (batch_size, vocab_size)
        noise_scale = self.coefficient * scores.std(dim=-1, keepdim=True).clamp(min=1e-8)
        noise = torch.from_numpy(
            self._rng.randn(*scores.shape).astype(np.float32)
        ).to(scores.device)
        return scores + noise_scale * noise


class MuViscosityProcessor(LogitsProcessor):
    """
    Viscosité η — Renforce la rétention/structure des logits.
    
    Principe :
        Amplifie le contraste entre tokens probables et improbables
        en multipliant les logits par (1 + μ) pour les tokens du top-k
        et par (1 - μ) pour les autres.
        Coefficient μ = 0.05 → renforcement subtil de la structure.
        
    Liens MTTV :
        Simule la viscosité du réseau mycélien qui conserve
        les chemins activation privilégiés (mémoire structurelle).
    """
    
    def __init__(self, coefficient: float = MU_COEFF, top_k: int = 50):
        self.coefficient = coefficient
        self.top_k = top_k
    
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        # Trouver le seuil du top-k
        topk_values, topk_indices = torch.topk(scores, self.top_k, dim=-1)
        threshold = topk_values[:, -1].unsqueeze(-1)  # (batch, 1)
        
        # Masque binaire : 1 pour top-k, 0 sinon
        mask = (scores >= threshold).float()
        
        # Appliquer le facteur viscosité
        amplification = 1.0 + self.coefficient * mask - self.coefficient * (1.0 - mask)
        return scores * amplification


class KalmanSingularityProcessor(LogitsProcessor):
    """
    Singularité Σ — Filtre de Kalman à l'instant critique τ.
    
    Principe :
        Implémente un filtre de Kalman 1D sur la trajectoire des logits.
        - Étape de prédiction : projection de l'état précédent
        - Étape de mise à jour : correction à partir de l'observation courante
        Le filtre n'est activé qu'à partir du step τ, créant une
        "singularité" dans la dynamique de génération.
        
        Coefficient σ = 0.01 → correction très subtile (presque imperceptible).
        
    Liens MTTV :
        Simule la singularité Σ qui émerge à un point critique
        du processus mycélien, où le système opère une transition
        de phase dans son espace d'états.
    """
    
    def __init__(self, coefficient: float = KALMAN_COEFF, tau: int = KALMAN_TAU):
        self.coefficient = coefficient  # gain de Kalman (K)
        self.tau = tau                  # instant critique d'activation
        self._step = 0                  # compteur interne de steps
        self._state_estimate: Optional[torch.Tensor] = None  # état estimé x̂ₖ
        self._error_cov: Optional[torch.Tensor] = None       # covariance Pₖ
    
    def _kalman_predict(self, scores: torch.FloatTensor) -> torch.FloatTensor:
        """Étape de prédiction : x̂ₖ₋ = x̂ₖ₋₁  (modèle de marche aléatoire)."""
        # Dans notre cas simplifié, l'état prédit = dernier état estimé
        # La covariance d'erreur augmente légèrement (bruit de processus)
        if self._error_cov is not None:
            process_noise = 0.01  # petite incertitude ajoutée
            self._error_cov = self._error_cov + process_noise
        return self._state_estimate
    
    def _kalman_update(self, scores: torch.FloatTensor, predicted: torch.FloatTensor):
        """Étape de mise à jour : x̂ₖ = x̂ₖ₋ + K · (zₖ - x̂ₖ₋)."""
        K = self.coefficient  # gain de Kalman fixe (simplifié)
        
        # Innovation : différence entre observation et prédiction
        innovation = scores - predicted
        
        # Mise à jour de l'état
        self._state_estimate = predicted + K * innovation
        
        # Mise à jour de la covariance
        if self._error_cov is not None:
            self._error_cov = (1.0 - K) * self._error_cov
        
        return self._state_estimate
    
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        self._step += 1
        
        # Avant τ : comportement normal (pas de filtre)
        if self._step < self.tau:
            # Initialiser l'état estimé sur les premiers logits observés
            if self._state_estimate is None:
                self._state_estimate = scores.clone()
                self._error_cov = torch.ones_like(scores) * 0.1
            return scores
        
        # À partir de τ : appliquer le filtre de Kalman
        if self._state_estimate is None:
            self._state_estimate = scores.clone()
            self._error_cov = torch.ones_like(scores) * 0.1
            return scores
        
        # Prédiction
        predicted = self._kalman_predict(scores)
        
        # Mise à jour
        filtered = self._kalman_update(scores, predicted)
        
        return filtered
    
    def reset(self):
        """Réinitialise le filtre pour une nouvelle séquence de génération."""
        self._step = 0
        self._state_estimate = None
        self._error_cov = None


# ============================================================================
# 2.  MÉTRIQUES DE MESURE
# ============================================================================

def compute_perplexity(model, tokenizer, input_ids: torch.LongTensor,
                       generated_ids: torch.LongTensor) -> float:
    """
    Calcule la Perplexité Ψ sur la séquence générée.
    
    Ψ = exp( (1/N) · Σ -log P(tokenᵢ | token<ᵢ) )
    
    où N est le nombre de tokens générés.
    Plus Ψ est bas, plus le modèle est "confiant" dans sa génération.
    """
    # Concaténer input + output pour avoir le contexte complet
    full_input = torch.cat([input_ids, generated_ids], dim=-1)
    
    with torch.no_grad():
        outputs = model(full_input)
        logits = outputs.logits  # (batch, seq_len, vocab)
    
    # Décaler : logits[i] prédit token[i+1]
    shift_logits = logits[:, :-1, :].contiguous()
    shift_labels = full_input[:, 1:].contiguous()
    
    # Ne considérer que les tokens générés (pas les tokens d'input)
    gen_start = input_ids.shape[-1] - 1  # premier token généré
    gen_logits = shift_logits[:, gen_start:, :]
    gen_labels = shift_labels[:, gen_start:]
    
    # Cross-entropy loss
    loss_fn = torch.nn.CrossEntropyLoss(reduction='none')
    losses = loss_fn(
        gen_logits.reshape(-1, gen_logits.shape[-1]),
        gen_labels.reshape(-1)
    )
    # Reshape back
    losses = losses.reshape(gen_logits.shape[0], gen_logits.shape[1])
    
    # Perplexité : exp(mean loss)
    mean_loss = losses.mean().item()
    perplexity = float(np.exp(mean_loss))
    
    return perplexity


def measure_metrics(model, tokenizer, prompts: List[str],
                    logits_processors: Optional[LogitsProcessorList] = None,
                    max_new_tokens: int = 50, n_warmup: int = 3,
                    n_measure: int = 20) -> Dict:
    """
    Mesure les 4 métriques MTTV-FLP sur un ensemble de prompts.
    
    Retourne un dict avec :
        - perplexite_psi  : Perplexité Ψ moyenne
        - vitesse_B       : Vitesse de génération (tokens/s)
        - pic_vram_phi    : Pic VRAM (Go)
        - energie_I       : Énergie estimée (Wh/1k tokens)
    """
    device = model.device
    
    # ── Phase de warmup ──
    for prompt in prompts[:n_warmup]:
        messages = [{"role": "user", "content": prompt}]
        prompt_text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
        )
        enc = tokenizer(prompt_text, return_tensors="pt", truncation=True)
        inp_ids = enc['input_ids'].to(device)
        attn_msk = enc.get('attention_mask', None)
        if attn_msk is not None:
            attn_msk = attn_msk.to(device)
        with torch.no_grad():
            _ = model.generate(
                input_ids=inp_ids,
                attention_mask=attn_msk,
                max_new_tokens=max_new_tokens,
                logits_processor=logits_processors or LogitsProcessorList(),
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
    
    # Réinitialiser les stats GPU si disponible
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
    
    # ── Phase de mesure ──
    test_prompts = prompts[n_warmup:n_warmup + n_measure]
    all_perplexities = []
    all_times_ms = []
    total_generated_tokens = 0
    
    for prompt in test_prompts:
        messages = [{"role": "user", "content": prompt}]
        prompt_text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
        )
        enc = tokenizer(prompt_text, return_tensors="pt", truncation=True)
        inp_ids = enc['input_ids'].to(device)
        attn_msk = enc.get('attention_mask', None)
        if attn_msk is not None:
            attn_msk = attn_msk.to(device)
        
        t0 = time.time()
        with torch.no_grad():
            generated = model.generate(
                input_ids=inp_ids,
                attention_mask=attn_msk,
                max_new_tokens=max_new_tokens,
                logits_processor=logits_processors or LogitsProcessorList(),
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        elapsed_s = time.time() - t0
        
        # Séparer input / output
        input_len = inp_ids.shape[-1]
        gen_ids = generated[:, input_len:]
        n_gen = gen_ids.shape[-1]
        total_generated_tokens += n_gen
        
        # Perplexité
        try:
            ppl = compute_perplexity(model, tokenizer, inp_ids, gen_ids)
        except Exception:
            ppl = float('nan')
        all_perplexities.append(ppl)
        
        # Temps
        all_times_ms.append(elapsed_s * 1000)
    
    # ── Agrégation ──
    avg_perplexity = float(np.nanmean(all_perplexities)) if all_perplexities else 0.0
    avg_time_ms = float(np.mean(all_times_ms)) if all_times_ms else 0.0
    total_time_s = sum(all_times_ms) / 1000.0 if all_times_ms else 0.0
    
    # Vitesse B (tokens/s)
    speed_B = total_generated_tokens / total_time_s if total_time_s > 0 else 0.0
    
    # Pic VRAM Φ (Go)
    vram_gb = 0.0
    if torch.cuda.is_available():
        vram_gb = torch.cuda.max_memory_allocated() / (1024**3)
    
    # Énergie I (Wh/1k tok)
    # Estimation : (TDP_total_W * temps_total_h) / (n_tokens / 1000)
    # TDP_total = TDP_GPU + portion CPU
    total_watts = TDP_GPU_WATTS + TDP_CPU_WATTS
    total_watts *= (1.0 + ENERGY_OVERHEAD)  # overhead
    time_hours = total_time_s / 3600.0
    energy_wh = total_watts * time_hours
    ktokens = total_generated_tokens / 1000.0 if total_generated_tokens > 0 else 1.0
    energy_I = energy_wh / ktokens if ktokens > 0 else 0.0
    
    return {
        "perplexite_psi": round(avg_perplexity, 4),
        "vitesse_B": round(speed_B, 2),
        "pic_vram_phi_go": round(vram_gb, 3),
        "energie_I_wh_per_1k": round(energy_I, 6),
        "n_prompts": n_measure,
        "n_tokens_total": total_generated_tokens,
        "temps_total_s": round(total_time_s, 3),
        "temps_moyen_ms": round(avg_time_ms, 2),
    }


def load_val_prompts(path: str = PROMPTS_FILE) -> List[str]:
    """
    Charge les 200 prompts gelés depuis mttv_val_gel_200.json.
    
    Format attendu du fichier JSON :
        [{"prompt": "...", "axiome": N}, ...]
    
    Si le fichier n'existe pas, le génère à partir de dataset.jsonl
    et de prompts complémentaires.
    """
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        prompts = [item["prompt"] for item in data if "prompt" in item]
        print(f"  [OK] {len(prompts)} prompts chargés depuis {path}")
        return prompts
    
    # Génération automatique depuis dataset.jsonl
    print(f"  [WARN] {path} non trouvé. Génération depuis dataset.jsonl...")
    dataset_path = "dataset.jsonl"
    prompts = []
    
    if os.path.exists(dataset_path):
        with open(dataset_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        item = json.loads(line)
                        if "prompt" in item:
                            prompts.append(item["prompt"])
                    except json.JSONDecodeError:
                        continue
    
    # Compléter avec des prompts de test standards si < 200
    extra_prompts = [
        # Sciences générales
        "Explique le cycle de l'eau en trois phrases",
        "Quelle est la différence entre une étoile et une planète ?",
        "Comment fonctionne un panneau solaire ?",
        "Décris le processus de digestion chez l'humain",
        "Qu'est-ce que la photosynthèse et pourquoi est-elle importante ?",
        "Explique le concept d'évolution par sélection naturelle",
        "Comment se forme un arc-en-ciel ?",
        "Qu'est-ce que l'ADN et quel est son rôle ?",
        "Décris le système solaire",
        "Comment fonctionne un vaccin ?",
        "Qu'est-ce que la fission nucléaire ?",
        "Explique le principe d'Archimède",
        "Comment les nuages se forment-ils ?",
        "Qu'est-ce qu'un écosystème ?",
        "Décris le fonctionnement d'un moteur à combustion",
        "Comment les plantes poussent-elles ?",
        "Qu'est-ce que la relativité restreinte ?",
        "Explique le phénomène des marées",
        "Comment fonctionne le GPS ?",
        "Qu'est-ce que la résonance magnétique ?",
        # Technologie et société
        "Qu'est-ce que l'intelligence artificielle ?",
        "Comment fonctionne un moteur de recherche ?",
        "Explique le concept de blockchain",
        "Qu'est-ce que le changement climatique ?",
        "Comment réduire son empreinte carbone ?",
        "Qu'est-ce que l'économie circulaire ?",
        "Explique le principe de la cryptographie",
        "Comment fonctionne un réseau de neurones ?",
        "Qu'est-ce que l'informatique quantique ?",
        "Décris l'Internet des objets",
        "Qu'est-ce que la réalité virtuelle ?",
        "Comment fonctionnent les panneaux photovoltaïques ?",
        "Explique le concept de développement durable",
        "Qu'est-ce que la biodiversité ?",
        "Comment fonctionne le machine learning ?",
        # Philosophie et concepts MTTV
        "Qu'est-ce que la pensée systémique ?",
        "Explique le concept de résilience",
        "Qu'est-ce que l'émergence ?",
        "Décris le principe de la symbiose",
        "Qu'est-ce que l'intelligence collective ?",
        "Explique le concept de rétroaction positive",
        "Qu'est-ce que la complexité ?",
        "Décris le principe d'auto-organisation",
        "Qu'est-ce que l'homéostasie ?",
        "Explique le concept de réseau",
        # Prompts de créativité
        "Imagine une solution pour dépolluer les océans",
        "Propose une innovation pour l'agriculture urbaine",
        "Comment pourrions-nous stocker l'énergie renouvelable ?",
        "Imagine une ville du futur durable",
        "Comment restaurer les écosystèmes dégradés ?",
        "Propose une méthode pour éduquer à l'écologie",
        "Comment intégrer la nature dans l'architecture ?",
        "Imagine un nouveau mode de transport écologique",
        "Comment réduire le gaspillage alimentaire ?",
        "Propose un système de santé préventive",
        # Compléments de transduction
        "Explique la gravité à un enfant de 5 ans",
        "Explique la gravité à un physicien",
        "Explique l'IA à un collégien",
        "Explique l'IA à un chercheur",
        "Explique l'économie à un adolescent",
        "Explique l'économie à un banquier",
        "Explique la biologie à un enfant",
        "Explique la biologie à un médecin",
        "Explique l'informatique à un grand-parent",
        "Explique l'informatique à un développeur",
    ]
    
    # Fusionner et dédupliquer
    seen = set()
    all_prompts = []
    for p in prompts + extra_prompts:
        if p not in seen:
            seen.add(p)
            all_prompts.append(p)
    
    # Compléter avec des reformulations si nécessaire
    base_phrases = [
        "Explique pourquoi le ciel est bleu",
        "Comment les oiseaux volent-ils ?",
        "Pourquoi l'eau de mer est-elle salée ?",
        "Comment les abeilles fabriquent-elles du miel ?",
        "Pourquoi les feuilles changent-elles de couleur en automne ?",
        "Comment fonctionne un aimant ?",
        "Pourquoi les volcans entrent-ils en éruption ?",
        "Comment les poissons respirent-ils sous l'eau ?",
        "Pourquoi avons-nous besoin de dormir ?",
        "Comment se forment les fossiles ?",
        "Qu'est-ce que la pression atmosphérique ?",
        "Comment les champignons se reproduisent-ils ?",
        "Pourquoi le sang est-il rouge ?",
        "Comment fonctionne l'effet de serre ?",
        "Qu'est-ce que la tectonique des plaques ?",
        "Comment les arbres communiquent-ils entre eux ?",
        "Pourquoi les saisons existent-elles ?",
        "Comment les bactéries deviennent-elles résistantes ?",
        "Qu'est-ce que l'énergie géothermique ?",
        "Comment fonctionne un écosystème marin ?",
    ]
    
    idx = 0
    while len(all_prompts) < 200 and idx < len(base_phrases) * 3:
        phrase = base_phrases[idx % len(base_phrases)]
        variants = [
            f"Explique: {phrase}",
            f"{phrase} ?",
            f"Peux-tu m'expliquer {phrase.lower()} ?",
        ]
        v = variants[idx // len(base_phrases)] if idx // len(base_phrases) < len(variants) else phrase
        if v not in seen:
            seen.add(v)
            all_prompts.append(v)
        idx += 1
    
    # Sauvegarder le fichier pour les prochains runs
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([{"prompt": p, "axiome": 0, "source": "auto"} for p in all_prompts[:200]],
                  f, indent=2, ensure_ascii=False)
    
    final = all_prompts[:200]
    print(f"  [OK] {len(final)} prompts générés et sauvegardés dans {path}")
    return final


# ============================================================================
# 3.  FONCTIONS D'EXÉCUTION PAR RUN
# ============================================================================

def run_baseline_vanilla(model, tokenizer, prompts: List[str]) -> Dict:
    """
    Run 1 — Baseline Vanilla : aucune modification des pertes.
    État natif du modèle (Qwen 2.5 brut).
    Mode : 7/7-ref — référence non-contextualisée, aucun axiome sacrifié.
    """
    print("\n" + "=" * 65)
    print("  RUN 1 : BASELINE VANILLA  (7/7-ref, aucun sacrifice)")
    print("=" * 65)
    
    t0 = time.time()
    metrics = measure_metrics(model, tokenizer, prompts,
                              logits_processors=LogitsProcessorList())
    elapsed = time.time() - t0
    
    return {
        "run": 1,
        "nom": "Baseline Vanilla",
        "mode": "7/7-ref",
        "sacrifice_assume": "aucun - référence 7/7 non-contextualisée",
        "contexte_usage": "étalon global non-contextualisé",
        "configuration": "Aucune",
        "coefficients": {"lambda": 0.0, "mu": 0.0, "kalman": 0.0},
        "metriques": metrics,
        "temps_execution_s": round(elapsed, 2),
        "description": "État natif du modèle Qwen 2.5 — sans aucune perturbation"
    }


def run_lambda_porosite(model, tokenizer, prompts: List[str]) -> Dict:
    """
    Run 2 — Lambda 0.1 seul (Porosité π) :
    Injecte une fonction de perte LogitsProcessor ciblant la diversité/perméabilité.
    """
    print("\n" + "=" * 65)
    print(f"  RUN 2 : LAMBDA 0.1 seul  (Porosité π)")
    print("=" * 65)
    
    # Réinitialiser les processeurs Kalman entre les runs
    lambda_processor = LambdaPorosityProcessor(coefficient=LAMBDA_COEFF)
    proc_list = LogitsProcessorList([lambda_processor])
    
    t0 = time.time()
    metrics = measure_metrics(model, tokenizer, prompts,
                              logits_processors=proc_list)
    elapsed = time.time() - t0
    
    return {
        "run": 2,
        "nom": "Lambda 0.1 seul",
        "mode": "6/7-II",
        "sacrifice_assume": "II - Contrainte libératrice",
        "contexte_usage": "créativité / diversité où la contrainte est secondaire",
        "configuration": f"Lambda = {LAMBDA_COEFF} (Porosité π)",
        "coefficients": {"lambda": LAMBDA_COEFF, "mu": 0.0, "kalman": 0.0},
        "metriques": metrics,
        "temps_execution_s": round(elapsed, 2),
        "description": (
            f"Injection de bruit gaussien calibré (σ = λ·std(logits)) dans "
            f"les logits à chaque step. λ = {LAMBDA_COEFF} → diversité/perméabilité."
        )
    }


def run_mu_viscosite(model, tokenizer, prompts: List[str]) -> Dict:
    """
    Run 3 — Mu 0.05 seul (Viscosité η) :
    Injecte un LogitsProcessor ciblant la rétention/structure.
    """
    print("\n" + "=" * 65)
    print(f"  RUN 3 : MU 0.05 seul  (Viscosité η)")
    print("=" * 65)
    
    mu_processor = MuViscosityProcessor(coefficient=MU_COEFF)
    proc_list = LogitsProcessorList([mu_processor])
    
    t0 = time.time()
    metrics = measure_metrics(model, tokenizer, prompts,
                              logits_processors=proc_list)
    elapsed = time.time() - t0
    
    return {
        "run": 3,
        "nom": "Mu 0.05 seul",
        "mode": "6/7-V",
        "sacrifice_assume": "V - Anisotropie",
        "contexte_usage": "edge / frugalité où la nuance sémantique fine est secondaire - candidat principal économie d'énergie",
        "configuration": f"Mu = {MU_COEFF} (Viscosité η)",
        "coefficients": {"lambda": 0.0, "mu": MU_COEFF, "kalman": 0.0},
        "metriques": metrics,
        "temps_execution_s": round(elapsed, 2),
        "description": (
            f"Amplification du contraste top-k : ×(1+μ) pour top-50, ×(1-μ) sinon. "
            f"μ = {MU_COEFF} → rétention/structure."
        )
    }


def run_kalman_singularite(model, tokenizer, prompts: List[str]) -> Dict:
    """
    Run 4 — Kalman 0.01 seul (Singularité Σ) :
    Active le filtre de Kalman à l'instant critique τ.
    """
    print("\n" + "=" * 65)
    print(f"  RUN 4 : KALMAN 0.01 seul  (Singularité Σ)")
    print("=" * 65)
    
    kalman_processor = KalmanSingularityProcessor(coefficient=KALMAN_COEFF, tau=KALMAN_TAU)
    proc_list = LogitsProcessorList([kalman_processor])
    
    t0 = time.time()
    metrics = measure_metrics(model, tokenizer, prompts,
                              logits_processors=proc_list)
    elapsed = time.time() - t0
    
    return {
        "run": 4,
        "nom": "Kalman 0.01 seul",
        "mode": "6/7-I",
        "sacrifice_assume": "I - Membrane",
        "contexte_usage": "raisonnement long / stabilité où l'autonomie locale immédiate est secondaire",
        "configuration": f"Kalman = {KALMAN_COEFF}, τ = {KALMAN_TAU} (Singularité Σ)",
        "coefficients": {"lambda": 0.0, "mu": 0.0, "kalman": KALMAN_COEFF},
        "metriques": metrics,
        "temps_execution_s": round(elapsed, 2),
        "description": (
            f"Filtre de Kalman 1D à gain fixe K = {KALMAN_COEFF} "
            f"activé au step τ = {KALMAN_TAU}. "
            f"Lisse la trajectoire des logits avec prédiction-correction."
        )
    }


def run_trois_pertes_combinees(model, tokenizer, prompts: List[str]) -> Dict:
    """
    Run 5 — Les 3 Pertes combinées :
    Active simultanément Lambda 0.1 + Mu 0.05 + Kalman 0.01.
    Mode : 5/7-effondrement — sacrifice multi-axiome volontaire.
    """
    print("\n" + "=" * 65)
    print("  RUN 5 : TROIS PERTES COMBINÉES  (5/7-effondrement, multi-sacrifice)")
    print("=" * 65)
    
    kalman_processor = KalmanSingularityProcessor(coefficient=KALMAN_COEFF, tau=KALMAN_TAU)
    proc_list = LogitsProcessorList([
        LambdaPorosityProcessor(coefficient=LAMBDA_COEFF),
        MuViscosityProcessor(coefficient=MU_COEFF),
        kalman_processor,
    ])
    
    t0 = time.time()
    metrics = measure_metrics(model, tokenizer, prompts,
                              logits_processors=proc_list)
    elapsed = time.time() - t0
    
    return {
        "run": 5,
        "nom": "Les 3 Pertes combinées",
        "mode": "5/7-effondrement",
        "sacrifice_assume": "II+V+I - effondrement multi-axiome",
        "contexte_usage": "test limite : sacrifice non-local, attendu inhabitable",
        "configuration": (
            f"Lambda {LAMBDA_COEFF} + Mu {MU_COEFF} + Kalman {KALMAN_COEFF}"
        ),
        "coefficients": {
            "lambda": LAMBDA_COEFF, "mu": MU_COEFF, "kalman": KALMAN_COEFF
        },
        "metriques": metrics,
        "temps_execution_s": round(elapsed, 2),
        "description": (
            f"Activation simultanée des 3 perturbations : "
            f"Porosité π (λ={LAMBDA_COEFF}) + Viscosité η (μ={MU_COEFF}) "
            f"+ Singularité Σ (K={KALMAN_COEFF}, τ={KALMAN_TAU})."
        )
    }


# ============================================================================
# 4.  FONCTION PRINCIPALE D'ORCHESTRATION
# ============================================================================

def executer_phase_1_exploration(model, tokenizer,
                                  dataset_val: Optional[List[str]] = None,
                                  prompts_path: str = PROMPTS_FILE,
                                  save_reports: bool = True,
                                  verbose: bool = True) -> List[Dict]:
    """
    Fonction principale qui orchestre l'intégralité de la Phase 1.
    
    Paramètres
    ----------
    model : AutoModelForCausalLM
        Le modèle Qwen 2.5 (ou tout modèle causal) à tester.
    tokenizer : AutoTokenizer
        Tokenizer associé au modèle.
    dataset_val : list of str, optional
        Liste de prompts de validation. Si None, chargés depuis prompts_path.
    prompts_path : str
        Chemin vers le fichier des 200 prompts gelés.
    save_reports : bool
        Si True, sauvegarde les rapports individuels au format JSON.
    verbose : bool
        Si True, affiche les détails d'exécution.
    
    Retourne
    --------
    list of Dict
        Liste des 5 rapports de run, chacun contenant :
            - run, nom, configuration, coefficients
            - metriques : {perplexite_psi, vitesse_B, pic_vram_phi_go, energie_I_wh_per_1k}
            - temps_execution_s, description
    """
    # ── Validation ──
    model.eval()
    device = model.device
    
    print("=" * 65)
    print("  MTTV-FLP v2 — PHASE 1 : EXPLORATION INSTRUMENTÉE")
    print("=" * 65)
    print(f"  Modèle       : {model.config._name_or_path if hasattr(model.config, '_name_or_path') else type(model).__name__}")
    print(f"  Device       : {device}")
    print(f"  Précision    : {next(model.parameters()).dtype}")
    if torch.cuda.is_available():
        print(f"  GPU          : {torch.cuda.get_device_name(0)}")
        vram_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"  VRAM totale  : {vram_total:.1f} Go")
    
    # ── Chargement des prompts ──
    if dataset_val is not None:
        prompts = dataset_val
    else:
        prompts = load_val_prompts(prompts_path)
    
    # Sélectionner un sous-ensemble pour les tests (200 max)
    prompts = prompts[:200]
    print(f"\n  Prompts de validation : {len(prompts)}")
    print(f"  Warmup  : 3 prompts")
    print(f"  Mesure  : {min(5, max(1, len(prompts) - 3))} prompts")
    print(f"  Max tokens générés : 50 par prompt")
    print()
    
    # ── Exécution des 5 runs ────────────────────────────────────────────
    runs = [
        ("Baseline Vanilla", run_baseline_vanilla),
        ("Lambda 0.1 seul", run_lambda_porosite),
        ("Mu 0.05 seul", run_mu_viscosite),
        ("Kalman 0.01 seul", run_kalman_singularite),
        ("Les 3 Pertes combinées", run_trois_pertes_combinees),
    ]
    
    all_reports = []
    
    for i, (name, run_func) in enumerate(runs, 1):
        if verbose:
            print(f"\n>>> Lancement du Run {i}/5 : {name}")
        
        try:
            report = run_func(model, tokenizer, prompts)
            all_reports.append(report)
            
            # Afficher les métriques clés
            m = report["metriques"]
            print(f"\n  Résultats Run {report['run']} — {report['nom']}:")
            print(f"    Perplexité Ψ      : {m['perplexite_psi']:.4f}")
            print(f"    Vitesse B         : {m['vitesse_B']:.2f} tok/s")
            print(f"    Pic VRAM Φ        : {m['pic_vram_phi_go']:.3f} Go")
            print(f"    Énergie I         : {m['energie_I_wh_per_1k']:.6f} Wh/1k tok")
            print(f"    Temps exécution   : {report['temps_execution_s']:.1f}s")
            
            # Sauvegarde individuelle
            if save_reports:
                report_path = REPORT_PREFIX.format(i)
                with open(report_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                print(f"    Rapport sauvegardé : {report_path}")
        
        except Exception as e:
            print(f"\n  [ERREUR] Run {i} ({name}) a échoué : {e}")
            import traceback
            traceback.print_exc()
            all_reports.append({
                "run": i,
                "nom": name,
                "configuration": "ERREUR",
                "coefficients": {},
                "metriques": {
                    "perplexite_psi": None,
                    "vitesse_B": None,
                    "pic_vram_phi_go": None,
                    "energie_I_wh_per_1k": None,
                    "erreur": str(e),
                },
                "temps_execution_s": 0.0,
                "description": f"Échec d'exécution : {e}",
            })
        
        # Petit délai entre les runs pour libérer la mémoire
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    # ── Tableau récapitulatif final ──
    print("\n\n" + "=" * 100)
    print("  TABLEAU RÉCAPITULATIF FINAL — PHASE 1  (Protocole Sous-Optimalité 6/7)")
    print("=" * 100)
    print()
    header = f"{'| Run':>5} {'| Mode':<18} {'| Sacrifice':<32} {'| Perplexité Ψ':<14} {'| Vitesse B':<12}"
    header += f" {'| Énergie I':<14} {'| ΔE%':<10}|"
    print(header)
    sep = f"{'|':->5} {'|':->18} {'|':->32} {'|':->14} {'|':->12} {'|':->14} {'|':->10}|"
    print(sep)
    
    baseline_ene = None
    if len(all_reports) > 0 and all_reports[0]["metriques"]["energie_I_wh_per_1k"] is not None:
        baseline_ene = all_reports[0]["metriques"]["energie_I_wh_per_1k"]
    
    for report in all_reports:
        m = report["metriques"]
        mode = report.get("mode", "N/A")
        sacrifice = report.get("sacrifice_assume", "N/A")
        ppl = f"{m['perplexite_psi']:.4f}" if m['perplexite_psi'] is not None else "N/A"
        spd = f"{m['vitesse_B']:.2f}" if m['vitesse_B'] is not None else "N/A"
        ene = f"{m['energie_I_wh_per_1k']:.6f}" if m['energie_I_wh_per_1k'] is not None else "N/A"
        
        if baseline_ene is not None and m['energie_I_wh_per_1k'] is not None and report['run'] > 1:
            d_ene = ((m['energie_I_wh_per_1k'] - baseline_ene) / baseline_ene * 100)
            d_ene_str = f"{d_ene:+.2f}%"
        else:
            d_ene_str = "—"
        
        print(f"| {report['run']:<3} | {mode:<16} | {sacrifice:<30} | {ppl:<12} | {spd:<10} | {ene:<12} | {d_ene_str:<8}|")
    
    print(sep)
    print()
    
    # ── Évaluation 6/7 : statut par run ──
    print("  Statut par run (protocole sous-optimalité 6/7) :")
    for report in all_reports:
        run = report['run']
        mode = report.get('mode', '?')
        m = report['metriques']
        has_data = m['perplexite_psi'] is not None
        
        if run == 1:
            # Run 1 (baseline) = référence, toujours OK
            status = "✅ Référence 7/7"
        elif run == 5:
            # Run 5 = effondrement attendu
            status = "⚠️  Effondrement attendu (test limite)"
        elif run == 3:
            # Run 3 : succès si delta_I négatif même si perplexité augmente
            if baseline_ene is not None and m['energie_I_wh_per_1k'] is not None:
                d_ene = ((m['energie_I_wh_per_1k'] - baseline_ene) / baseline_ene * 100)
                if d_ene < 0:
                    status = f"✅ 6/7 stable — gain énergétique {d_ene:+.2f}%"
                else:
                    status = f"⚠️  Perte énergétique {d_ene:+.2f}% (attendu négatif)"
            else:
                status = "❌ Données insuffisantes"
        else:
            # Runs 2,4 : succès si métriques stables (perplexité et énergie)
            ppl_ok = m['perplexite_psi'] is not None
            ene_delta_ok = True
            if baseline_ene is not None and m['energie_I_wh_per_1k'] is not None:
                d_ene = ((m['energie_I_wh_per_1k'] - baseline_ene) / baseline_ene * 100)
                ene_delta_ok = abs(d_ene) < 20  # moins de 20% de variation
            if ppl_ok and ene_delta_ok:
                status = "✅ 6/7 stable"
            elif ppl_ok:
                status = "⚠️  Stab. mais variation > 20%"
            else:
                status = "❌ Données insuffisantes"
        
        print(f"    Run {run} ({mode}): {status}")
    
    print()
    
    # ── Rapport de synthèse ──
    synthesis = {
        "phase": "Phase 1 — Exploration Instrumentée (Protocole Sous-Optimalité 6/7)",
        "modele": model.config._name_or_path if hasattr(model.config, '_name_or_path') else str(type(model).__name__),
        "date": time.strftime('%Y-%m-%d %H:%M:%S'),
        "n_prompts": len(prompts),
        "protocole": "Sous-optimalité appliquée — sacrifice volontaire d'1 axiome/run",
        "runs": all_reports,
        "coefficients": {
            "lambda_porosite": LAMBDA_COEFF,
            "mu_viscosite": MU_COEFF,
            "kalman_singularite": KALMAN_COEFF,
            "kalman_tau": KALMAN_TAU,
        },
    }
    
    synthesis_path = "synthese_phase1_exploration.json"
    with open(synthesis_path, "w", encoding="utf-8") as f:
        json.dump(synthesis, f, indent=2, ensure_ascii=False)
    print(f"  Synthèse sauvegardée : {synthesis_path}")
    
    # Afficher les delta par rapport à la baseline
    if len(all_reports) >= 5 and all_reports[0]["metriques"]["perplexite_psi"] is not None:
        print("\n  Δ par rapport à la Baseline (Run 1) :")
        baseline_ppl = all_reports[0]["metriques"]["perplexite_psi"]
        baseline_spd = all_reports[0]["metriques"]["vitesse_B"]
        baseline_vrm = all_reports[0]["metriques"]["pic_vram_phi_go"]
        baseline_ene = all_reports[0]["metriques"]["energie_I_wh_per_1k"]
        
        for report in all_reports[1:]:
            m = report["metriques"]
            if m["perplexite_psi"] is not None:
                d_ppl = m["perplexite_psi"] - baseline_ppl
                d_spd_pct = ((m["vitesse_B"] - baseline_spd) / baseline_spd * 100) if baseline_spd > 0 else 0
                d_vrm_pct = ((m["pic_vram_phi_go"] - baseline_vrm) / baseline_vrm * 100) if baseline_vrm > 0 else 0
                d_ene_pct = ((m["energie_I_wh_per_1k"] - baseline_ene) / baseline_ene * 100) if baseline_ene > 0 else 0
                print(f"    Run {report['run']} ({report['nom']}):")
                print(f"      Mode       : {report.get('mode', 'N/A')}")
                print(f"      Sacrifice  : {report.get('sacrifice_assume', 'N/A')}")
                print(f"      Δ Perplexité : {d_ppl:+.4f}")
                print(f"      Δ Vitesse    : {d_spd_pct:+.2f}%")
                print(f"      Δ VRAM       : {d_vrm_pct:+.2f}%")
                print(f"      Δ Énergie    : {d_ene_pct:+.2f}%")
    
    print("\n" + "=" * 100)
    print("  PHASE 1 TERMINÉE — 5/5 runs exécutés. Protocole 6/7 appliqué.")
    print("=" * 100)
    
    return all_reports


# ============================================================================
# 5.  MODE AUTONOME (exécution directe)
# ============================================================================

def main():
    """
    Mode autonome : charge le modèle Qwen2.5-1.5B-Instruct et exécute
    la Phase 1 complète.
    
    Usage :
        python phase_1_exploration.py
    """
    print("=" * 65)
    print("  MTTV-FLP v2 — PHASE 1 : EXPLORATION INSTRUMENTÉE (mode autonome)")
    print("=" * 65)
    
    # ── Paramètres ──
    MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
    USE_4BIT = torch.cuda.is_available()
    
    print(f"\n  Modèle      : {MODEL_NAME}")
    print(f"  Quant. 4-bit : {USE_4BIT}")
    print(f"  Device      : {'cuda' if torch.cuda.is_available() else 'cpu'}")
    print()
    
    # ── Chargement du modèle ──
    print("[1/3] Chargement du tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    print("[2/3] Chargement du modèle...")
    t0 = time.time()
    
    if USE_4BIT:
        from transformers import BitsAndBytesConfig
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True,
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float32,
            trust_remote_code=True,
        ).to("cpu")
    
    load_time = time.time() - t0
    print(f"  Modèle chargé en {load_time:.1f}s")
    print(f"  Paramètres : {sum(p.numel() for p in model.parameters()):,}")
    
    # ── Chargement des prompts ──
    print("\n[3/3] Chargement des prompts de validation...")
    prompts = load_val_prompts(PROMPTS_FILE)
    
    # ── Exécution de la Phase 1 ──
    results = executer_phase_1_exploration(model, tokenizer, dataset_val=prompts)
    
    # Bilan final
    n_ok = sum(1 for r in results if r["metriques"]["perplexite_psi"] is not None)
    print(f"\n  Bilan : {n_ok}/5 runs complétés avec succès.")
    
    return results


if __name__ == "__main__":
    main()
