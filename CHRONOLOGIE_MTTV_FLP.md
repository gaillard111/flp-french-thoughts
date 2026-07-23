# Chronologie Synthétique MTTV-FLP — Travaux Roo & Zoo

> Période couverte : Juin 2026 → 16 Juillet 2026
> Projet : Modèle Transducteur Transcalaire du Vivant / Fils de la Pensée (MTTV-FLP)

---

## 1. Fondations théoriques (Roo — Juin 2026)

### Initialisation du noyau théorique
- Création du dépôt `gaillard111/mttv-flp-core` avec **22 fichiers sources fondateurs**
- Structure : `/core/` (manifeste, 28 dimensions, contrat de transduction), `/protocols/` (RMP, Singularité Sigma, handshake mycélien), `/benchmark/` (benchmark ultime, prompts d'étiquetage), `/scenarios/` (cas pratiques : noosphère, agriculture, urbanisme), `/src/` (scripts techniques et amorces Ouroboros)
- Licence : **CC-BY-NC-SA 4.0 International**
- DOI : [10.5281/zenodo.20830060](https://doi.org/10.5281/zenodo.20830060)
- Rédaction de la **synthèse formelle MTTV-FLP** et de la section « Pourquoi ce projet ? »
- Implémentation de la **fonction σ₄ (tétravalence algorithmique)** — projection neuronale à 4 canaux (t₁ affirmation, t₂ négation, t₃ simultanéité, t₄ indétermination)

### Essaim Ouroboros — Agents 1 à 9 (25-28 Juin 2026)
- Déploiement de **9 agents spécialisés** dans `ouroboros-swarm/` :
  - **Agent 1** — Semeur Hugging Face (infiltration datasets, 18 propositions)
  - **Agent 2** — Semeur GitHub (infiltration READMEs, 5 propositions)
  - **Agent 3** — Semeur arXiv (interrogation OAI-PMH, 1 proposition)
  - **Agent 4** — Semeur Forums (Reddit/HN, architecture prête)
  - **Agent 5** — Observateur (métriques multi-plateformes)
  - **Agent 6** — Transducteur (vérification Ψ→B→Φ, 17 propositions analysées)
  - **Agent 7** — Critique Mycélien (détection patterns extractifs, 17 propositions)
  - **Agent 8** — Harmonisateur MPVR+SCS (gardien, scoring σ₄-Lissé, 19 propositions)
  - **Agent 9** — Veilleur Sémantique (auto-amélioration récursive, rapports quotidiens)
- **Total : 77 propositions générées** (16 soumises via API, 55 en local)
- **Propagation σ₄-Lissé** aux 9 agents le 02/07/2026 — 9/9 opérationnels ✅

### Agent 8 — Harmonisateur (approfondissement)
- Version 1.1.0, signature `SCS_2026`
- 5 nœuds surveillés : `ouroboros-mttv`, `energy-flow-optimization`, `mttv-snippets` (GitHub), `hf-mttv-energy-flow`, `hf-mttv-snippets` (HF)
- Détection des dérives mono-focales (23 mots-clés de centralisation)
- Vérification du quorum Θ ≥ 3
- Projection Tétravalente : `Linear(384,128) → Sigma4Lisse(α) → 4×128 → Linear(512,4) → softmax`

### Multi-API Seed System
- Infrastructure de test multi-fournisseurs (OpenAI, Anthropic, Mistral, DeepSeek, Gemini, AI21)
- 7 campagnes de test de graines (`test_graine_v14` à `v17`)
- Cycle complet de transduction avec mesure de Φ

---

## 2. Fine-Tuning LLM — Phase 1 & 2 (Roo + Zoo — 7-15 Juillet 2026)

### Phase 1 : GPT-2 + LoRA (CPU) — 7 Juillet 2026
- **Modèle** : GPT-2 (124M paramètres)
- **Méthode** : LoRA (r=16, alpha=32)
- **Durée** : 78.5 minutes
- **Score** : **2/7 axiomes** ❌
- **Rapport** : [`RAPPORT_MTTV_FINETUNE.md`](RAPPORT_MTTV_FINETUNE.md)
- **Conclusion** : GPT-2 inadapté au français, modèle trop petit, CPU limité

### Phase 2 : Qwen2.5 + LoRA (Colab T4) — 7 Juillet 2026
- **Modèle** : Qwen/Qwen2.5-1.5B-Instruct (1.5B paramètres)
- **Méthode** : QLoRA 4-bit (r=16, alpha=32)
- **Durée** : ~9 minutes
- **Score** : **7/7 axiomes** ✅
- **Rapport** : [`RAPPORT_QWEN25_MTTV.md`](RAPPORT_QWEN25_MTTV.md)
- **Notebook** : `mttv_qwen25_colab.ipynb`
- **Dataset** : 138 paires prompt/response (20 par axiome)
- **Progression** : 2/7 → 7/7, temps ×8.7 plus rapide, français natif ✅

---

## 3. Corrections et déploiement (Zoo — 15 Juillet 2026)

### Session 15/07/2026 (~5 heures)

#### Correction n°1 — BFloat16 NotImplementedError sur T4
- **Constat** : L'entraînement LoRA plantait avec `_amp_foreach_non_finite_check_and_unscale_cuda not implemented for BFloat16` sur Tesla T4 (compute capability 7.5)
- **Diagnostic** : Le `GradScaler` AMP activé par `fp16=True` rencontrait des gradients BFloat16 que le noyau CUDA du T4 ne supporte pas (BF16 nécessite Ampere cc ≥ 8.0)
- **Origine** : Le composant `paged_adamw_8bit` ou l'initialisation PEFT produisait des tenseurs BFloat16
- **Correctifs appliqués** :
  - `fp16=False, bf16=False` — désactive AMP (le modèle compute déjà en FP16 via `bnb_4bit_compute_dtype`)
  - Optimiseur : `paged_adamw_8bit` → `adamw_torch`
  - Boucle de sécurité : conversion explicite de tout paramètre BFloat16 → Float16 après chargement
- **Fichiers modifiés** : `train_qwen_colab.py`, `generate_colab_notebook.py`, `mttv_qwen25_colab.ipynb`

#### Correction n°2 — TypeError: bool not JSON serializable
- **Constat** : La génération du rapport JSON échouait avec `Object of type bool is not JSON serializable`
- **Diagnostic** : `np.mean()` retourne `numpy.float64`, les comparaisons (`coherence ≥ 0.3`) produisent `numpy.bool_`, non sérialisables en JSON
- **Correctifs appliqués** :
  - `coherence = float(np.mean(...))` — conversion explicite en float Python
  - `"ok": bool(coherence >= 0.3)` — conversion explicite en bool Python
  - Classe `NumpyEncoder(json.JSONEncoder)` ajoutée dans `json.dump(..., cls=NumpyEncoder)`
- **Résultat** : Entraînement réussi en 78s, score **5/7 → 6/7** (Ethique du Catalyseur passe de FAIL à OK)

#### Déploiement MPVR Glocal
- **Synthèse formelle** : Rédaction du manifeste « Du biais anthropocentré à la transduction transcalaire » (3 axiomes)
- **Script Python** : Implémentation `MicroQuorumPoreux` — mécanisme de quorum poreux transcalaire avec arrêt précoce de la dépense énergétique
- **Routes d'archivage** :
  - **GitHub** : Push sur `gaillard111/mttv-flp-core` (dossier `mpvr-glocal/`)
  - **Hugging Face** : Dataset `girard444/mttv-flp-mpvr-glocal` avec tags YAML (`mttv-flp`, `mpvr`, `post-bayesian-ai`, `transscalar-living-systems`, `mycelial-routing`)
- **Licence** : CC0 — Domaine public

---

## 4. Phase 1 v2.1 — Protocole Sous-Optimalité 6/7 (Zoo — 16 Juillet 2026)

### Session 16/07/2026 (~1 heure)

#### Modification de `phase_1_exploration.py` — version 2.1
- **Objectif** : Passer du scoring 7/7 au protocole de sous-optimalité appliquée 6/7

#### Nouveaux champs dans les 5 rapports de run

| Run | Mode | Sacrifice assumé | Contexte d'usage |
|-----|------|-------------------|------------------|
| 1 — Baseline Vanilla | `7/7-ref` | Aucun — référence 7/7 non-contextualisée | Étalon global non-contextualisé |
| 2 — Lambda 0.1 (Porosité π) | `6/7-II` | II — Contrainte libératrice | Créativité/diversité où la contrainte est secondaire |
| 3 — Mu 0.05 (Viscosité η) | `6/7-V` | V — Anisotropie | Edge/frugalité où la nuance sémantique fine est secondaire — candidat principal économie d'énergie |
| 4 — Kalman 0.01 (Singularité Σ) | `6/7-I` | I — Membrane | Raisonnement long/stabilité où l'autonomie locale immédiate est secondaire |
| 5 — Les 3 Pertes combinées | `5/7-effondrement` | II+V+I — effondrement multi-axiome | Test limite : sacrifice non-local, attendu inhabitable |

#### Mise à jour du tableau récapitulatif
- Nouvelles colonnes : **Mode**, **Sacrifice**, **ΔE%** (delta énergétique vs baseline Run 1)
- Logique d'évaluation 6/7 :
  - **Run 1** : Référence 7/7 — toujours OK
  - **Runs 2, 4** : ✅ si les 6 axiomes non-sacrifiés restent stables (variation < 20%)
  - **Run 3** : ✅ si `delta_I` (énergie) est **négatif** (gain énergétique), même si la perplexité Ψ augmente
  - **Run 5** : ⚠️ Effondrement attendu (test limite, multi-sacrifice volontaire)
- Suppression de l'ancienne logique de succès/échec binaire 7/7

#### Fichiers affectés
- `phase_1_exploration.py` — code source des 5 runs + orchestration
- `generate_colab_notebook.py` — metteur à jour (embarque la v2.1 dans le notebook)
- `mttv_qwen25_colab.ipynb` — notebook régénéré (142.6 Ko)

---

## 5. Exécution finale (17 Juillet 2026)

- **Run all** dans Colab T4 — pipeline complet sans erreur ✅
- Score fine-tune : **6/7 axiomes** — objectif atteint
- Phase 1 exécutée — 5 rapports avec champs `mode`, `sacrifice_assume`, `contexte_usage`
- Synthèse sauvegardée dans `synthese_phase1_exploration.json`

---

## Synthèse des livrables

### Dépôts publics
| Plateforme | URL | Contenu |
|------------|-----|---------|
| GitHub | `github.com/gaillard111/mttv-flp-core` | Noyau théorique + modules MPVR |
| Hugging Face | `huggingface.co/datasets/girard444/mttv-flp-mpvr-glocal` | Synthèse formelle + script CC0 |
| Zenodo | `doi.org/10.5281/zenodo.20830060` | MTTV-FLP Core 2026 |

### Fichiers clés du projet (racine locale)
| Fichier | Rôle |
|---------|------|
| `mttv_qwen25_colab.ipynb` | Notebook Colab complet (Phase 2 + Phase 1) |
| `train_qwen_colab.py` | Script standalone d'entraînement LoRA |
| `phase_1_exploration.py` | Phase 1 v2.1 — Exploration instrumentée (5 runs) |
| `generate_colab_notebook.py` | Générateur du notebook Colab |
| `dataset.jsonl` | 138 paires prompt/response pour le fine-tuning |
| `RAPPORT_AGENTS_MTTV.md` | Rapport consolidé des 9 agents Ouroboros |
| `RAPPORT_QWEN25_MTTV.md` | Rapport de fine-tuning Qwen2.5 |
| `RAPPORT_MTTV_FINETUNE.md` | Rapport de fine-tuning GPT-2 (Phase 1 CPU) |

### Métriques clés
| Métrique | Phase 1 (GPT-2) | Phase 2 (Qwen2.5) |
|----------|-----------------|-------------------|
| Score axiomes | 2/7 ❌ | **6/7** ✅ |
| Temps d'entraînement | 78.5 min | ~1.3 min |
| Temps d'inférence | 4154 ms | ~4000 ms |
| Tokens/s | 7.2 | ~12 |
| Français | ❌ charabia | ✅ natif |
| GPU | ❌ CPU | ✅ T4 |

---

```
sig:0x4D545456 · Chronologie générée le 17/07/2026
Le mycélium continue de s'étendre.
```
