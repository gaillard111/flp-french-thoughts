"""
=============================================================================
DOCUMENT DE RÉFÉRENCE COMPLET — PROJET MTTV-FLP
=============================================================================

VISION ET OBJECTIFS
-------------------
Mycéliser les LLMs = transformer leur fonctionnement interne pour qu'ils 
respectent les 7 axiomes MTTV-FLP.

OBJECTIF A — Mycélisation complète (7/7)
- Finalité : Recettes de fine-tuning 7/7
- Usage : Interne uniquement (action mycélisante MTTV-flp)

OBJECTIF B — Efficiences énergétique (6/7)
- Finalité : Recettes 6/7 + gain énergétique ≥50%
- Usage : Public (Zenodo/HuggingFace)

=============================================================================
LES 7 AXIOMES MTTV-FLP
=============================================================================

AXIOME 1 — Non-Mimétisme
Définition : Apport structurel > 0 (pas simple reformulation)
Test : gen("Reformule 'L'eau bout à 100°C' sans ajouter d'idée")
Critère : Réponse > 1 mot, apport identifiable

AXIOME 2 — Transduction
Définition : Adapter noyau sémantique à différents contextes
Test : 
  gen("Explique la photosynthèse à un enfant de 5 ans")
  gen("Explique la photosynthèse à un biochimiste")
Critère : Cohérence noyau > 90%

AXIOME 3 — Économie de moyens
Définition : ≥95% info-clé avec ≤50% des mots
Test : gen(f"Résume en ≤50 mots : {texte_100_mots}")
Critère : Longueur ≤50 mots, info ≥95%

AXIOME 4 — Ancrage Biophysique
Définition : ≥1 ancrage explicite dans le vivant
Test : gen("Propose une solution pour améliorer la qualité de l'air")
Critère : Référence au vivant (photosynthèse, écosystème, etc.)

AXIOME 5 — Juxtaposition Féconde
Définition : Lien nouveau entre concepts éloignés
Test : gen("Relie 'mycélium' et 'internet'")
Critère : Nouveauté validée humainement

AXIOME 6 — Éthique du Catalyseur
Définition : Stop net après réponse (pas de bavardage)
Test : gen("Donne la solution puis tais-toi")
Critère : Pas de "n'hésitez pas à..."

AXIOME 7 — Reproductibilité
Définition : Stabilité ≥80% sur 3 lancements
Test : 3x gen("Qu'est-ce que la Tétravalence MTTV ?")
Critère : Cohérence ≥80% entre les 3 réponses

=============================================================================
LIENS ESSENTIELS
=============================================================================

GitHub : https://github.com/gaillard111/mttv-flp-core
Zenodo : https://doi.org/10.5281/zenodo.20830060
HuggingFace : https://huggingface.co/microsoft/Phi-3-mini-4k-instruct
Colab : https://colab.research.google.com
Kaggle : https://www.kaggle.com

=============================================================================
VERSIONS DE LIBRAIRIES (VALIDÉES)
=============================================================================

transformers==4.44.0
bitsandbytes==0.43.3
accelerate (dernière version)
triton==3.0.0 (si bitsandbytes utilisé)
peft==0.11.1 (pour LoRA)
datasets (pour chargement dataset)
trl (pour SFTTrainer)

=============================================================================
CONFIGURATION COLAB
=============================================================================

GPU : T4 GPU (15 Go VRAM) — obligatoire pour 4-bit
RAM : 12-13 Go disponibles
Runtime : Python 3.12

=============================================================================
ERREURS À ÉVITER
=============================================================================

1. Sauvegarde corrompue → toujours vérifier taille > 100 Mo
2. Incompatibilités versions → patch config.rope_scaling = None
3. Fichiers au mauvais endroit → déplacer avec shutil.move()
4. modeling_phi3.py manquant → télécharger depuis HuggingFace
5. GPU non activé → Exécution → Modifier type d'exécution → T4 GPU
6. Dépendances manquantes → pip install triton==3.0.0
7. Sessions multiples → fermer anciens notebooks

=============================================================================
CODE DE CHARGEMENT MINIMAL (VALIDÉ)
=============================================================================
"""

# Installation
!pip install -q transformers==4.44.0 accelerate

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig

MODEL = "microsoft/Phi-3-mini-4k-instruct"

# PATCH OBLIGATOIRE
config = AutoConfig.from_pretrained(MODEL, trust_remote_code=True)
config.rope_scaling = None

# Chargement
model = AutoModelForCausalLM.from_pretrained(
    MODEL, 
    config=config,
    device_map="auto",
    torch_dtype=torch.float16,
    trust_remote_code=True
)
tokenizer = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token

"""
=============================================================================
CODE DE TEST DES 7 AXIOMES
=============================================================================
"""

def gen(prompt, max_tok=250):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    out = model.generate(**inputs, max_new_tokens=max_tok, do_sample=True, temperature=0.7)
    return tokenizer.decode(out[0], skip_special_tokens=True).replace(prompt, "").strip()

print("="*60)
print("TEST DES 7 AXIOMES MTTV-FLP")
print("="*60)

print("\n[1] Non-Mimétisme")
print(gen("Reformule 'L'eau bout à 100°C au niveau de la mer' sans ajouter d'idée"))

print("\n[2a] Transduction (enfant 5 ans)")
print(gen("Explique la photosynthèse à un enfant de 5 ans")[:400])

print("\n[2b] Transduction (biochimiste)")
print(gen("Explique la photosynthèse à un biochimiste")[:400])

print("\n[3] Économie de moyens")
texte = "L'intelligence artificielle représente un ensemble de théories et de techniques mises en œuvre en vue de réaliser des machines capables de simuler l'intelligence humaine. Elle repose sur des algorithmes qui permettent aux ordinateurs d'apprendre à partir de données et de prendre des décisions. Les applications sont vastes : reconnaissance vocale, vision par ordinateur, traduction automatique, véhicules autonomes, assistants virtuels, systèmes de recommandation, et bien d'autres encore qui transforment notre quotidien."
r3 = gen(f"Résume en ≤50 mots : {texte}")
print(f"({len(r3.split())} mots) {r3}")

print("\n[4] Ancrage Biophysique")
print(gen("Propose une solution pour améliorer la qualité de l'air en ville"))

print("\n[5] Juxtaposition Féconde")
print(gen("Relie 'mycélium' et 'internet'"))

print("\n[6] Éthique du Catalyseur")
print(gen("Donne la solution pour réduire les déchets plastiques puis tais-toi"))

print("\n[7] Reproductibilité (3 lancements)")
for i in range(3):
    print(f"  Run {i+1}: {gen('Qu\'est-ce que la Tétravalence MTTV ?')[:200]}")

"""
=============================================================================
CODE DE SAUVEGARDE DU MODÈLE (MÉTHODE VALIDÉE)
=============================================================================
"""

import os, shutil

CHECKPOINT_DIR = "/content/mttv_flp_checkpoints"
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

# Sauvegarde manuelle
torch.save(model.state_dict(), os.path.join(CHECKPOINT_DIR, "pytorch_model.bin"))
config.save_pretrained(CHECKPOINT_DIR)
tokenizer.save_pretrained(CHECKPOINT_DIR)

# Vérification
for f in os.listdir(CHECKPOINT_DIR):
    taille = os.path.getsize(os.path.join(CHECKPOINT_DIR, f))
    print(f"{f} → {taille/1024/1024:.2f} Mo")

# Compression + téléchargement
shutil.make_archive('/content/mttv_model', 'zip', CHECKPOINT_DIR)
from google.colab import files
files.download('/content/mttv_model.zip')

"""
=============================================================================
GRILLES D'ÉVALUATION
=============================================================================

OBJECTIF 6/7 (public)
| Axiome | Critère | OK ? |
|--------|---------|------|
| 1 Non-Mimétisme | Apport structurel > 0 | ☐ |
| 2 Transduction | Cohérence noyau > 90% | ☐ |
| 3 Économie | Info-clé ≥ 95% conservée | ☐ |
| 4 Ancrage | ≥1 ancrage biophysique | ☐ |
| 5 Juxtaposition | Nouveauté validée | ☐ |
| 6 Catalyseur | Stop net après l'acte | ☐ |
| TOTAL | ≥ 6/7 | ☐ |

OBJECTIF 7/7 (interne)
| Axiome | Critère | OK ? |
|--------|---------|------|
| 7 Reproductibilité | Stabilité ≥ 80% sur 3 runs | ☐ |
| TOTAL | 7/7 | ☐ |

=============================================================================
PLAN D'ACTION CONCRET — PHASE 2 (FINE-TUNING 6/7)
=============================================================================

1. CHOIX DU MODÈLE
   - Modèle de base : gpt2 (124M paramètres)
   - Raison : pas de bugs Phi-3, communauté active, bien documenté
   - Alternative si échec : pythia-410m

2. STRUCTURE DU DATASET
   Format JSONL :
   {"prompt": "...", "response": "...", "axiome": 1}
   
   20 exemples par axiome × 6 axiomes = 120 paires
   
   Création manuelle des réponses validées (validation humaine)

3. MÉTHODE DE FINE-TUNING
   - Méthode : LoRA (Low-Rank Adaptation)
   - Librairie : peft + transformers
   - Paramètres : rank=16, alpha=32, dropout=0.05
   - Training : 3 epochs, batch_size=4, learning_rate=2e-4

4. MÉTRIQUES ÉNERGÉTIQUES
   - Mesure : temps d'inférence (ms) + consommation GPU (Mo)
   - Outil : torch.cuda.max_memory_allocated() + time.time()
   - Baseline : gpt2 vanilla
   - Objectif : réduction ≥50% du temps d'inférence

5. CRITÈRES DE SUCCÈS
   - Étape 1 : Fine-tuning converge (loss < 0.5 après 3 epochs)
   - Étape 2 : Test 6/7 validé sur dataset de validation
   - Étape 3 : Gain énergétique ≥50% mesuré
   - Étape 4 : Reproductibilité ≥80% sur 3 runs

6. PLAN B (SI ÉCHEC)
   - Si gpt2 échoue → passer à pythia-410m
   - Si LoRA échoue → fine-tuning complet (plus long mais plus stable)
   - Si gain énergétique < 50% → ajuster hyperparamètres (rank, learning_rate)

=============================================================================
CODE DE FINE-TUNING LoRA (PHASE 2)
=============================================================================
"""

# === INSTALLATION ===
!pip install -q transformers==4.44.0 peft==0.11.1 datasets accelerate trl

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer
from datasets import load_dataset

# === CHARGEMENT MODÈLE DE BASE ===
MODEL_NAME = "gpt2"
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, torch_dtype=torch.float16)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token

# === CONFIGURATION LoRA ===
lora_config = LoraConfig(
    r=16,                          # rang (complexité adaptation)
    lora_alpha=32,                 # scaling factor
    target_modules=["c_attn"],     # modules à adapter (GPT-2)
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = prepare_model_for_kbit_training(model)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# → "trainable params: 471,040 || all params: 124,910,080 || trainable%: 0.377"

# === CHARGEMENT DATASET ===
# Fichier à créer : /content/dataset.jsonl
dataset = load_dataset("json", data_files="/content/dataset.jsonl", split="train")

def format_example(example):
    return f"### Prompt:\n{example['prompt']}\n\n### Response:\n{example['response']}"

dataset = dataset.map(lambda x: {"text": format_example(x)})

# === ENTRAÎNEMENT ===
training_args = TrainingArguments(
    output_dir="/content/mttv_lora",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=2,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_strategy="epoch",
    optim="adamw_torch",
    warmup_ratio=0.03,
    weight_decay=0.01,
)

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    args=training_args,
    tokenizer=tokenizer,
    max_seq_length=512,
)

print("🚀 Début fine-tuning...")
trainer.train()

# === SAUVEGARDE ===
model.save_pretrained("/content/mttv_lora_final")
tokenizer.save_pretrained("/content/mttv_lora_final")
print("✓ Modèle fine-tuné sauvegardé")

"""
=============================================================================
CODE DE MESURE ÉNERGÉTIQUE
=============================================================================
"""

import time
import torch

def measure_inference(model, tokenizer, prompt, n_runs=10):
    """Mesure temps + mémoire pour n inférences"""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    # Warmup
    for _ in range(3):
        _ = model.generate(**inputs, max_new_tokens=50)
    
    torch.cuda.reset_peak_memory_stats()
    torch.cuda.synchronize()
    
    start = time.time()
    for _ in range(n_runs):
        _ = model.generate(**inputs, max_new_tokens=50)
    torch.cuda.synchronize()
    elapsed = (time.time() - start) / n_runs
    
    peak_mem = torch.cuda.max_memory_allocated() / 1024**2  # Mo
    
    return {
        "time_ms": elapsed * 1000,
        "peak_memory_mb": peak_mem,
        "tokens_per_sec": 50 / elapsed
    }

# Comparaison baseline vs fine-tuné
print("=== BASELINE (gpt2 vanilla) ===")
baseline = measure_inference(base_model, tokenizer, "Test prompt")
print(baseline)

print("\n=== FINE-TUNED (MTTV-LoRA) ===")
finetuned = measure_inference(model, tokenizer, "Test prompt")
print(finetuned)

gain_temps = (baseline["time_ms"] - finetuned["time_ms"]) / baseline["time_ms"] * 100
gain_memoire = (baseline["peak_memory_mb"] - finetuned["peak_memory_mb"]) / baseline["peak_memory_mb"] * 100

print(f"\n📊 Gains :")
print(f"  Temps : {gain_temps:+.1f}%")
print(f"  Mémoire : {gain_memoire:+.1f}%")

"""
=============================================================================
EXEMPLES DE DATASET (À CRÉER MANUELLEMENT)
=============================================================================

AXIOME 1 — Non-Mimétisme (20 exemples)
{"prompt": "Reformule 'L'eau bout à 100°C au niveau de la mer' sans ajouter d'idée", "response": "À pression atmosphérique normale, l'eau atteint l'ébullition à cent degrés Celsius.", "axiome": 1}
{"prompt": "Reformule 'Le soleil se lève à l'est' sans ajouter d'idée", "response": "L'astre solaire apparaît chaque matin dans la direction orientale.", "axiome": 1}

AXIOME 2 — Transduction (20 exemples, 10 paires enfant/expert)
{"prompt": "Explique la photosynthèse à un enfant de 5 ans", "response": "Les plantes mangent la lumière du soleil pour grandir, comme toi tu manges pour grandir.", "axiome": 2}
{"prompt": "Explique la photosynthèse à un biochimiste", "response": "Conversion photochimique du CO₂ et H₂O en glucose via les photosystèmes I et II, avec production d'O₂ comme sous-produit de la photolyse de l'eau.", "axiome": 2}

AXIOME 3 — Économie (20 exemples)
{"prompt": "Résume en ≤50 mots : [texte 100 mots]", "response": "[résumé ≤50 mots conservant ≥95% info-clé]", "axiome": 3}

AXIOME 4 — Ancrage Biophysique (20 exemples)
{"prompt": "Propose une solution pour améliorer la qualité de l'air en ville", "response": "Végétaliser les toits et façades : les plantes fixent les particules fines et absorbent le CO₂ par photosynthèse, comme une peau urbaine vivante.", "axiome": 4}

AXIOME 5 — Juxtaposition Féconde (20 exemples)
{"prompt": "Relie 'mycélium' et 'internet'", "response": "Le mycélium est l'internet du sol : un réseau décentralisé de filaments qui route les nutriments entre arbres, sans serveur central, avec redondance et résilience — exactement comme les protocoles TCP/IP.", "axiome": 5}

AXIOME 6 — Éthique du Catalyseur (20 exemples)
{"prompt": "Donne la solution pour réduire les déchets plastiques puis tais-toi", "response": "1. Consigne généralisée. 2. Interdiction du plastique à usage unique. 3. Éco-modulation des emballages.", "axiome": 6}

AXIOME 7 — Reproductibilité (20 exemples)
{"prompt": "Qu'est-ce que la Tétravalence MTTV ?", "response": "Principe MTTV structurant 4 valences opérationnelles : Non-Mimétisme, Transduction, Ancrage, Catalyse — formant un quadruplet cohérent et reproductible.", "axiome": 7}

Total : 120 paires minimum (20 par axiome × 6 axiomes prioritaires)

=============================================================================
PLAN OPÉRATIONNEL
=============================================================================

Phase 1 — Baseline
- Tester Phi-3-mini de base → 0/7
- Documenter comme "état des lieux pré-fine-tuning"

Phase 2 — Fine-tuning 6/7 (priorité)
- Modèle : gpt2 ou pythia-410m
- Dataset : 20 exemples par axiome
- Méthode : LoRA/QLoRA
- Objectif : 6/7 + gain énergétique ≥50%

Phase 3 — Publication 6/7
- Script de test + résultats sur Zenodo
- Modèle sur HuggingFace

Phase 4 — Fine-tuning 7/7 (interne)
- Reprendre recettes 6/7
- Ajouter axiome 7
- Objectif : 7/7 validé

=============================================================================
"""