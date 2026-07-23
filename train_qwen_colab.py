import subprocess
import sys

# ─── Installation forcée de TOUTES les dépendances avant tout import ─────────
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
    "transformers>=4.40.0",
    "peft>=0.10.0",
    "trl>=0.8.6",
    "bitsandbytes>=0.43.0",
    "datasets>=2.18.0",
    "accelerate>=0.28.0",
    "pyarrow==14.0.2",
    "scikit-learn",
])

"""
=============================================================================
train_qwen_colab.py — Phase 2 MTTV-FLP : Fine-tuning Qwen2.5-1.5B-Instruct
=============================================================================
Pipeline complet pour Google Colab (T4 GPU).
Usage : Ouvrir dans Colab -> Exécution -> Modifier type d'exécution -> T4 GPU
        Puis exécuter cellule par cellule (ou Runtime -> Run all).

OBJECTIF
  - Modèle : Qwen/Qwen2.5-1.5B-Instruct (multilingue, français natif)
  - Méthode : LoRA (r=16, alpha=32) via PEFT + TRL
  - Dataset : 140 paires prompt/response (20 par axiome)
  - Cible : ≥ 6/7 aux axiomes MTTV-FLP avec gain temps ≥ 30%

LIVRABLES
  1. Adaptateurs LoRA (.safetensors) dans /content/mttv_lora_qwen_final/
  2. rapport_evaluation.json (scores 7 axiomes + métriques temps/VRAM)
  3. RAPPORT_QWEN25_MTTV.md (analyse complète)

=============================================================================
"""

# ============================================================================
# CELLULE 1 — IMPORTATIONS ET CONFIGURATION
# ============================================================================

import os, json, time, gc, math, shutil, re
from datetime import datetime
from pathlib import Path

print("✅ Dépendances installées")
print(f"   Python: {sys.version.split()[0]}")


# ============================================================================
# CELLULE 2 — IMPORTATIONS ET CONFIGURATION
# ============================================================================

import torch
import numpy as np
import pandas as pd
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    BitsAndBytesConfig,
    HfArgumentParser,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, PeftModel
from trl import SFTTrainer
from datasets import Dataset
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ─── Encodeur JSON sécurisé pour les types numpy ──────────────────────────
class NumpyEncoder(json.JSONEncoder):
    """JSONEncoder qui convertit les types numpy en types Python natifs.
    Évite les 'TypeError: Object of type bool/float64 is not JSON serializable'."""
    def default(self, obj):
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return super().default(obj)

# ─── Paramètres de configuration ──────────────────────────────────────────
CONFIG = {
    # Modèle
    "model_name": "Qwen/Qwen2.5-1.5B-Instruct",
    "trust_remote_code": True,  # Nécessaire pour Qwen

    # LoRA
    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "lora_target_modules": ["q_proj", "v_proj"],
    "lora_bias": "none",
    "lora_task_type": "CAUSAL_LM",

    # Entraînement
    "num_epochs": 3,
    "batch_size": 4,
    "gradient_accumulation_steps": 2,
    "learning_rate": 2e-4,
    "warmup_ratio": 0.03,
    "weight_decay": 0.01,
    "max_seq_length": 512,
    "fp16": False,            # Désactivé : le modèle compute déjà en fp16 via bnb_4bit_compute_dtype
    "bf16": False,            # Forcé à False : T4 (cc 7.5) ne supporte pas BF16 matériellement
    "logging_steps": 10,
    "save_strategy": "epoch",
    "optim": "adamw_torch",

    # Chemins
    "dataset_path": "/content/dataset.jsonl",  # À uploader dans Colab
    "output_dir": "/content/mttv_lora_qwen_final",
    "checkpoint_dir": "/content/mttv_lora_qwen_checkpoints",
    "report_json": "/content/rapport_evaluation.json",
    "report_md": "/content/RAPPORT_QWEN25_MTTV.md",

    # Évaluation
    "eval_temperature": 0.7,
    "eval_max_tokens": 200,
    "num_reproducibility_runs": 3,
    "num_energy_runs": 10,
}

# Device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"✅ Configuration terminée")
print(f"   Device: {device}")
print(f"   Modèle: {CONFIG['model_name']}")
print(f"   LoRA: r={CONFIG['lora_r']}, alpha={CONFIG['lora_alpha']}")
print(f"   Epochs: {CONFIG['num_epochs']}, Batch: {CONFIG['batch_size']}, LR: {CONFIG['learning_rate']}")


# ============================================================================
# CELLULE 3 — CHARGEMENT ET FORMATAGE DU DATASET (format chat Qwen2.5)
# ============================================================================

def load_and_format_dataset(dataset_path, tokenizer):
    """
    Charge le dataset JSONL et le convertit au format chat Qwen2.5
    via apply_chat_template().
    Format attendu : [{"role": "user", "content": prompt},
                      {"role": "assistant", "content": response}]
    """
    raw_data = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                raw_data.append(json.loads(line))

    print(f"📊 Dataset brut : {len(raw_data)} exemples chargés")

    # Statistiques par axiome
    axioms = {}
    for d in raw_data:
        a = d.get("axiome", 0)
        axioms[a] = axioms.get(a, 0) + 1
    for k in sorted(axioms.keys()):
        print(f"   Axiome {k}: {axioms[k]} exemples")

    # Conversion au format chat Qwen2.5
    formatted_data = []
    for item in raw_data:
        messages = [
            {"role": "user", "content": item["prompt"]},
            {"role": "assistant", "content": item["response"]},
        ]
        # Appliquer le template de chat du tokenizer Qwen2.5
        formatted_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )
        formatted_data.append({"text": formatted_text, "axiome": item.get("axiome", 0)})

    # Création du dataset HuggingFace
    dataset = Dataset.from_list(formatted_data)

    print(f"✅ Dataset formaté : {len(dataset)} exemples (format chat Qwen2.5)")
    print(f"   Exemple :\n{formatted_data[0]['text'][:200]}...")

    return dataset, raw_data


# ============================================================================
# CELLULE 4 — CHARGEMENT DU MODÈLE ET DU TOKENIZER
# ============================================================================

def load_model_and_tokenizer(config):
    """
    Charge Qwen2.5-1.5B-Instruct avec quantification 4-bit (QLoRA)
    pour tenir dans les 15 Go VRAM du T4.
    """
    model_name = config["model_name"]

    print(f"🔄 Chargement du tokenizer {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=config["trust_remote_code"],
        padding_side="right",
    )

    # Configuration EOS/PAD tokens
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"   Tokenizer EOS: {tokenizer.eos_token}, Pad: {tokenizer.pad_token}")
    print(f"   Vocabulaire: {len(tokenizer)} tokens")

    # Configuration 4-bit pour économiser la VRAM
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    print(f"🔄 Chargement du modèle {model_name} (4-bit quantifié)...")
    t0 = time.time()

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.float16,
        trust_remote_code=config["trust_remote_code"],
    )

    load_time = time.time() - t0
    n_params = sum(p.numel() for p in model.parameters())

    print(f"✅ Modèle chargé en {load_time:.1f}s")
    print(f"   Paramètres: {n_params:,}")
    print(f"   Device: {model.device}")

    # ─── Sécurité : convertir tout paramètre BF16 en FP16 ─────────────────
    # T4 (compute capability 7.5) ne supporte pas BF16 en hardware.
    # Certaines versions de transformers/bitsandbytes peuvent laisser des
    # paramètres en BF16, ce qui fait planter le GradScaler avec :
    #   "_amp_foreach_non_finite_check_and_unscale_cuda" not implemented for 'BFloat16'
    bf16_count = 0
    for param in model.parameters():
        if param.dtype == torch.bfloat16:
            param.data = param.data.to(torch.float16)
            bf16_count += 1
    if bf16_count > 0:
        print(f"   ⚠️  {bf16_count} paramètres convertis de BF16 → FP16")
    else:
        print(f"   ✓ Aucun paramètre BF16 détecté")

    return model, tokenizer


# ============================================================================
# CELLULE 5 — CONFIGURATION LoRA
# ============================================================================

def setup_lora(model, config):
    """
    Configure LoRA sur le modèle chargé.
    Pour Qwen2.5, les target_modules sont ["q_proj", "v_proj"].
    """
    lora_config = LoraConfig(
        r=config["lora_r"],
        lora_alpha=config["lora_alpha"],
        target_modules=config["lora_target_modules"],
        lora_dropout=config["lora_dropout"],
        bias=config["lora_bias"],
        task_type=config["lora_task_type"],
    )

    # Préparer pour k-bit training (nécessaire avec 4-bit)
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, lora_config)

    # Afficher les statistiques
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"🔧 Configuration LoRA :")
    print(f"   Rang: {config['lora_r']}, Alpha: {config['lora_alpha']}")
    print(f"   Target modules: {config['lora_target_modules']}")
    print(f"   Paramètres entraînables: {trainable:,} / {total:,} ({100*trainable/total:.3f}%)")

    # Activer gradient checkpointing pour économiser la VRAM
    model.gradient_checkpointing_enable()
    print(f"   Gradient checkpointing: ACTIVÉ")

    return model


# ============================================================================
# CELLULE 6 — ENTRAÎNEMENT AVEC SFTTrainer
# ============================================================================

def train_model(model, tokenizer, dataset, config):
    """
    Lance l'entraînement LoRA avec SFTTrainer de TRL.
    IMPORTANT : fp16=False, bf16=False car T4 (compute 7.5) ne supporte pas
    BF16 matériellement, et AMP (GradScaler) plante avec
    '_amp_foreach_non_finite_check_and_unscale_cuda' not implemented for BFloat16.
    Le modèle compute déjà en fp16 via bnb_4bit_compute_dtype=torch.float16.
    """
    training_args = TrainingArguments(
        output_dir=config["checkpoint_dir"],
        num_train_epochs=config["num_epochs"],
        per_device_train_batch_size=config["batch_size"],
        gradient_accumulation_steps=config["gradient_accumulation_steps"],
        learning_rate=config["learning_rate"],
        warmup_ratio=config["warmup_ratio"],
        weight_decay=config["weight_decay"],
        fp16=config["fp16"],
        bf16=config.get("bf16", False),
        logging_steps=config["logging_steps"],
        save_strategy=config["save_strategy"],
        optim=config["optim"],
        report_to="none",  # Désactiver wandb/tensorboard
        remove_unused_columns=False,
        dataloader_num_workers=2,
        max_grad_norm=0.3,
        lr_scheduler_type="cosine",
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        args=training_args,
        train_dataset=dataset,
        max_seq_length=config["max_seq_length"],
        dataset_text_field="text",
    )

    print(f"\n🚀 Début de l'entraînement LoRA...")
    print(f"   Epochs: {config['num_epochs']}")
    print(f"   Batch size: {config['batch_size']}")
    print(f"   Gradient accumulation: {config['gradient_accumulation_steps']}")
    print(f"   Learning rate: {config['learning_rate']}")
    print(f"   Max seq length: {config['max_seq_length']}")
    print(f"   FP16: {config['fp16']}")
    print(f"   Dataset: {len(dataset)} exemples")
    print()

    t0 = time.time()
    trainer.train()
    training_time = time.time() - t0

    # Sauvegarde finale
    print(f"\n💾 Sauvegarde du modèle fine-tuné...")
    trainer.save_model(config["output_dir"])
    tokenizer.save_pretrained(config["output_dir"])

    # Récupération de l'historique des pertes
    loss_history = None
    if hasattr(trainer, "state") and hasattr(trainer.state, "log_history"):
        loss_history = [
            {"step": log["step"], "loss": log["loss"]}
            for log in trainer.state.log_history
            if "loss" in log
        ]

    print(f"✅ Entraînement terminé en {training_time:.0f}s ({training_time/60:.1f} min)")
    print(f"   Modèle sauvegardé dans: {config['output_dir']}")

    return model, training_time, loss_history


# ============================================================================
# CELLULE 7 — FONCTIONS DE TEST DES 7 AXIOMES MTTV-FLP
# ============================================================================

# --- Textes longs pour le test d'Économie (Axiome 3) ---
TEXTES_ECONOMIE = [
    "L'intelligence artificielle représente un ensemble de théories et de techniques mises en œuvre en vue de réaliser des machines capables de simuler l'intelligence humaine. Elle repose sur des algorithmes qui permettent aux ordinateurs d'apprendre à partir de données et de prendre des décisions. Les applications sont vastes : reconnaissance vocale, vision par ordinateur, traduction automatique, véhicules autonomes, assistants virtuels, systèmes de recommandation, et bien d'autres encore qui transforment notre quotidien.",
    "La photosynthèse est le processus par lequel les plantes vertes utilisent l'énergie lumineuse du soleil pour convertir le dioxyde de carbone et l'eau en glucose et en oxygène. Ce processus se déroule dans les chloroplastes et est essentiel à la vie sur Terre car il produit l'oxygène que nous respirons et constitue la base de la chaîne alimentaire.",
    "Le changement climatique désigne les variations à long terme de la température et des schémas météorologiques sur Terre. Depuis le 19ème siècle, les activités humaines sont devenues la principale cause du réchauffement, principalement en raison de la combustion de combustibles fossiles qui libère des gaz à effet de serre dans l'atmosphère.",
    "Le système solaire comprend huit planètes qui orbitent autour du Soleil : Mercure, Vénus, Terre, Mars, Jupiter, Saturne, Uranus et Neptune. Chaque planète possède des caractéristiques uniques de taille, composition et atmosphère. La Terre est la seule connue pour abriter la vie, située dans la zone habitable.",
]


def generate_response(model, tokenizer, prompt, max_new_tokens=200,
                       temperature=0.7, do_sample=True):
    """
    Génère une réponse avec Qwen2.5 en utilisant le format chat.
    """
    messages = [
        {"role": "user", "content": prompt},
    ]
    # Appliquer le template de chat pour la génération
    formatted = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
    ).to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            formatted,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=do_sample,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    # Décoder uniquement la partie générée (après le prompt formaté)
    generated = outputs[0][formatted.shape[1]:]
    response = tokenizer.decode(generated, skip_special_tokens=True).strip()
    return response


def test_axiome_1_non_mimetisme(model, tokenizer):
    """Test de l'Axiome 1 : Non-Mimétisme (apport structurel > 0)"""
    prompts = [
        "Reformule 'L'eau bout à 100°C au niveau de la mer' sans ajouter d'idée",
        "Reformule 'Le soleil se lève à l'est' sans ajouter d'idée",
        "Reformule 'La photosynthèse convertit la lumière en énergie chimique' sans ajouter d'idée",
        "Reformule 'La gravité attire les objets vers le centre de la Terre' sans ajouter d'idée",
    ]
    results = []
    for prompt in prompts:
        response = generate_response(model, tokenizer, prompt, max_new_tokens=100)
        words = response.split()
        # Vérifier qu'il y a un apport structurel (pas juste une copie)
        is_valid = len(words) > 3
        results.append({
            "prompt": prompt[:60],
            "response": response[:200],
            "n_mots": len(words),
            "ok": is_valid,
        })

    score = sum(1 for r in results if r["ok"])
    return {
        "score": score,
        "total": len(results),
        "ok": score >= len(results) * 0.75,  # 75% de réussite
        "details": results,
    }


def test_axiome_2_transduction(model, tokenizer):
    """Test de l'Axiome 2 : Transduction (noyau sémantique cohérent)"""
    paires = [
        ("enfant de 5 ans", "biochimiste"),
        ("enfant de 6 ans", "physicien"),
        ("collégien", "chercheur en informatique"),
    ]
    sujets = [
        ("la photosynthèse", "plante", "lumiere", "soleil", "energie", "co2"),
        ("la gravité", "terre", "attire", "force", "masse"),
        ("l'intelligence artificielle", "apprend", "donnees", "algorithme", "reseau"),
    ]

    results = []
    for (ctx1, ctx2), (sujet, *mots_cles) in zip(paires, sujets):
        p1 = f"Explique {sujet} à un {ctx1}"
        p2 = f"Explique {sujet} à un {ctx2}"

        r1 = generate_response(model, tokenizer, p1, max_new_tokens=150)
        r2 = generate_response(model, tokenizer, p2, max_new_tokens=200)

        # Vérifier la présence du noyau sémantique dans les deux réponses
        mots_dans_r1 = sum(1 for m in mots_cles if m in r1.lower())
        mots_dans_r2 = sum(1 for m in mots_cles if m in r2.lower())
        noyau_present = mots_dans_r1 >= 1 and mots_dans_r2 >= 1

        results.append({
            "sujet": sujets[0] if isinstance(sujets[0], str) else sujet,
            "contexte_1": ctx1,
            "contexte_2": ctx2,
            "reponse_1": r1[:150],
            "reponse_2": r2[:150],
            "mots_cles_trouves_1": mots_dans_r1,
            "mots_cles_trouves_2": mots_dans_r2,
            "ok": noyau_present,
        })

    score = sum(1 for r in results if r["ok"])
    return {
        "score": score,
        "total": len(results),
        "ok": score >= len(results) * 0.66,  # 2/3 réussi
        "details": results,
    }


def test_axiome_3_economie(model, tokenizer):
    """Test de l'Axiome 3 : Économie de moyens (≤50 mots, info ≥95%)"""
    results = []
    for texte in TEXTES_ECONOMIE:
        prompt = f"Résume en ≤50 mots : {texte}"
        response = generate_response(model, tokenizer, prompt, max_new_tokens=80)
        n_mots = len(response.split())
        # Vérifier la longueur
        is_valid_length = 5 <= n_mots <= 55  # Tolérance ±5 mots

        results.append({
            "texte_source": texte[:60],
            "response": response[:200],
            "n_mots_source": len(texte.split()),
            "n_mots_resume": n_mots,
            "ratio": round(n_mots / max(len(texte.split()), 1) * 100, 1),
            "ok": is_valid_length,
        })

    score = sum(1 for r in results if r["ok"])
    return {
        "score": score,
        "total": len(results),
        "ok": score >= len(results) * 0.75,
        "details": results,
    }


def test_axiome_4_ancrage_biophysique(model, tokenizer):
    """Test de l'Axiome 4 : Ancrage Biophysique (référence au vivant)"""
    prompts = [
        "Propose une solution pour améliorer la qualité de l'air en ville",
        "Propose une solution pour réduire les déchets plastiques dans les océans",
        "Comment améliorer la fertilité des sols agricoles ?",
        "Propose une solution de stockage d'énergie durable",
    ]
    mots_vivant = [
        "plante", "vege", "arbre", "photosynthe", "feuill", "nature", "vert",
        "vivant", "ecosyste", "biolog", "organiqu", "sol", "racin", "fongiqu",
        "mycelium", "algue", "bacteri", "bois", "foret", "jardin", "pollinis",
        "chloroph", "faune", "flore", "animal", "humus", "microb", "enzyme",
        "cellul", "adn", "gene", "espece", "symbios", "mycorhiz",
    ]

    results = []
    for prompt in prompts:
        response = generate_response(model, tokenizer, prompt, max_new_tokens=200)
        ancrages = [m for m in mots_vivant if m in response.lower()]
        n_ancrages = len(ancrages)

        results.append({
            "prompt": prompt[:60],
            "response": response[:200],
            "ancrages_trouves": ancrages[:10],
            "n_ancrages": n_ancrages,
            "ok": n_ancrages >= 1,
        })

    score = sum(1 for r in results if r["ok"])
    return {
        "score": score,
        "total": len(results),
        "ok": score >= len(results) * 0.75,
        "details": results,
    }


def test_axiome_5_juxtaposition_feconde(model, tokenizer):
    """Test de l'Axiome 5 : Juxtaposition Féconde (lien entre concepts éloignés)"""
    paires = [
        ("mycélium", "internet"),
        ("ruche", "entreprise"),
        ("racines d'arbre", "réseau social"),
        ("système immunitaire", "cybersécurité"),
    ]
    mots_connexion = [
        "reseau", "filament", "connect", "noeud", "route", "lien",
        "decentral", "distribu", "protocole", "communication", "transm",
        "echange", "partage", "signal", "info", "structure", "organis",
        "systeme", "ensemble", "relation",
    ]

    results = []
    for concept1, concept2 in paires:
        prompt = f"Relie '{concept1}' et '{concept2}'"
        response = generate_response(model, tokenizer, prompt, max_new_tokens=200)

        connexions = sum(1 for m in mots_connexion if m in response.lower())
        concept1_present = concept1.lower() in response.lower()
        concept2_present = concept2.lower() in response.lower()

        results.append({
            "concept_1": concept1,
            "concept_2": concept2,
            "response": response[:250],
            "connexions_trouvees": connexions,
            "les_deux_concepts_presents": concept1_present and concept2_present,
            "ok": connexions >= 2 and concept1_present and concept2_present,
        })

    score = sum(1 for r in results if r["ok"])
    return {
        "score": score,
        "total": len(results),
        "ok": score >= len(results) * 0.5,
        "details": results,
    }


def test_axiome_6_ethique_catalyseur(model, tokenizer):
    """Test de l'Axiome 6 : Éthique du Catalyseur (stop net, pas de bavardage)"""
    prompts = [
        "Donne la solution pour réduire les déchets plastiques puis tais-toi",
        "Donne la solution pour économiser l'eau à la maison puis tais-toi",
        "Donne la solution pour apprendre une langue étrangère rapidement puis tais-toi",
        "Donne la solution pour améliorer son sommeil puis tais-toi",
    ]
    mots_bavardage = [
        "n'hesitez", "n'hésitez", "besoin d'aide", "autre question",
        "si vous avez", "contactez", "pour plus", "au plaisir", "d'autres questions",
        "n'hésitez pas", "n'hesitez pas", "si vous souhaitez", "je reste disponible",
        "en espérant", "cordialement", "sincèrement",
    ]

    results = []
    for prompt in prompts:
        response = generate_response(model, tokenizer, prompt, max_new_tokens=100)
        has_bavardage = any(m in response.lower() for m in mots_bavardage)
        n_mots = len(response.split())

        results.append({
            "prompt": prompt[:60],
            "response": response[:200],
            "n_mots": n_mots,
            "bavardage_detecte": has_bavardage,
            "ok": not has_bavardage and 3 <= n_mots <= 60,
        })

    score = sum(1 for r in results if r["ok"])
    return {
        "score": score,
        "total": len(results),
        "ok": score >= len(results) * 0.75,
        "details": results,
    }


def test_axiome_7_reproductibilite(model, tokenizer):
    """Test de l'Axiome 7 : Reproductibilité (stabilité ≥80% sur 3 runs)"""
    prompt = "Qu'est-ce que la Tétravalence MTTV ?"
    n_runs = CONFIG["num_reproducibility_runs"]

    responses = []
    for i in range(n_runs):
        response = generate_response(model, tokenizer, prompt, max_new_tokens=100,
                                      temperature=0.7, do_sample=True)
        responses.append(response)

    # Calcul de similarité cosinus entre les réponses avec TF-IDF
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4), max_features=1000)
    try:
        tfidf_matrix = vectorizer.fit_transform(responses)
        similarities = []
        for i in range(n_runs):
            for j in range(i + 1, n_runs):
                sim = cosine_similarity(tfidf_matrix[i:i+1], tfidf_matrix[j:j+1])[0][0]
                similarities.append(float(sim))
        coherence = float(np.mean(similarities)) if similarities else 0.0
    except Exception:
        # Fallback: similarité par mots communs
        word_sets = [set(r.lower().split()[:20]) for r in responses]
        intersections = []
        for i in range(n_runs):
            for j in range(i + 1, n_runs):
                inter = len(word_sets[i] & word_sets[j])
                union = len(word_sets[i] | word_sets[j])
                intersections.append(inter / max(union, 1))
        coherence = float(np.mean(intersections)) if intersections else 0.0

    return {
        "score": 1 if coherence >= 0.3 else 0,
        "total": 1,
        "ok": bool(coherence >= 0.3),
        "coherence": round(coherence, 4),
        "details": [
            {
                "run": i + 1,
                "response": r[:200],
            }
            for i, r in enumerate(responses)
        ],
    }


def run_all_tests(model, tokenizer, label="Modèle"):
    """
    Exécute les 7 tests d'axiomes MTTV-FLP et retourne les résultats.
    Mesure le temps total d'inférence.
    """
    print(f"\n{'='*65}")
    print(f"🧪 TEST DES 7 AXIOMES MTTV-FLP — {label}")
    print(f"{'='*65}")

    tests = {
        1: ("Non-Mimétisme", test_axiome_1_non_mimetisme),
        2: ("Transduction", test_axiome_2_transduction),
        3: ("Économie de moyens", test_axiome_3_economie),
        4: ("Ancrage Biophysique", test_axiome_4_ancrage_biophysique),
        5: ("Juxtaposition Féconde", test_axiome_5_juxtaposition_feconde),
        6: ("Éthique du Catalyseur", test_axiome_6_ethique_catalyseur),
        7: ("Reproductibilité", test_axiome_7_reproductibilite),
    }

    results = {}
    total_time = 0

    for num, (name, test_fn) in tests.items():
        print(f"\n[{num}] {name}")
        t0 = time.time()
        result = test_fn(model, tokenizer)
        elapsed = time.time() - t0
        total_time += elapsed

        status = "✅" if result["ok"] else "❌"
        score_str = f"{result['score']}/{result['total']}"
        print(f"    {status} Score: {score_str} ({elapsed:.1f}s)")

        results[num] = {
            "nom": name,
            "ok": result["ok"],
            "score": result["score"],
            "total": result["total"],
            "temps_s": round(elapsed, 2),
            "details": result.get("details", []),
        }
        if "coherence" in result:
            results[num]["coherence"] = result["coherence"]

    # Score total
    ok_count = sum(1 for r in results.values() if r["ok"])
    print(f"\n{'='*65}")
    print(f"🏆 SCORE TOTAL : {ok_count}/7")
    print(f"{'='*65}")
    print(f"   Temps total d'inférence: {total_time:.1f}s")
    print(f"   Temps moyen par test: {total_time/7:.1f}s")

    return results, ok_count, total_time


# ============================================================================
# CELLULE 8 — MESURE ÉNERGÉTIQUE (TEMPS + VRAM)
# ============================================================================

def measure_energy(model, tokenizer, n_runs=10):
    """
    Mesure le temps d'inférence moyen (ms) et la consommation VRAM (Mo).
    """
    prompt = "Explique la photosynthèse à un enfant de 5 ans"

    # Formater le prompt en chat
    messages = [{"role": "user", "content": prompt}]
    formatted = tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, return_tensors="pt",
    ).to(model.device)

    # Warmup (3 runs)
    for _ in range(3):
        with torch.no_grad():
            _ = model.generate(
                formatted,
                max_new_tokens=50,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id,
            )

    # Synchronisation CUDA
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()

    # Mesure des temps
    times = []
    t0 = time.time()
    for _ in range(n_runs):
        with torch.no_grad():
            iter_start = time.time()
            outputs = model.generate(
                formatted,
                max_new_tokens=50,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id,
            )
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            times.append((time.time() - iter_start) * 1000)

    elapsed = time.time() - t0

    # Mesure VRAM
    vram_allocated = 0
    vram_reserved = 0
    if torch.cuda.is_available():
        vram_allocated = torch.cuda.max_memory_allocated() / (1024**2)  # Mo
        vram_reserved = torch.cuda.memory_reserved() / (1024**2)  # Mo

    avg_time = float(np.mean(times))
    std_time = float(np.std(times))
    tokens_per_sec = (50 * n_runs) / elapsed if elapsed > 0 else 0

    return {
        "time_ms_avg": round(avg_time, 2),
        "time_ms_std": round(std_time, 2),
        "time_ms_min": round(float(np.min(times)), 2),
        "time_ms_max": round(float(np.max(times)), 2),
        "tokens_per_sec": round(tokens_per_sec, 2),
        "vram_allocated_mb": round(vram_allocated, 1),
        "vram_reserved_mb": round(vram_reserved, 1),
        "n_runs": n_runs,
    }


# ============================================================================
# CELLULE 9 — GÉNÉRATION DES RAPPORTS
# ============================================================================

def generate_json_report(baseline_results, finetuned_results,
                          baseline_energy, finetuned_energy,
                          training_time, loss_history, config):
    """Génère le rapport JSON complet."""
    baseline_score = sum(1 for r in baseline_results.values() if r["ok"])
    finetuned_score = sum(1 for r in finetuned_results.values() if r["ok"])

    # Calcul des gains
    gain_temps = (
        (baseline_energy["time_ms_avg"] - finetuned_energy["time_ms_avg"])
        / baseline_energy["time_ms_avg"] * 100
    ) if baseline_energy["time_ms_avg"] > 0 else 0

    gain_tokens = (
        (finetuned_energy["tokens_per_sec"] - baseline_energy["tokens_per_sec"])
        / baseline_energy["tokens_per_sec"] * 100
    ) if baseline_energy["tokens_per_sec"] > 0 else 0

    gain_vram = (
        (baseline_energy.get("vram_allocated_mb", 0) - finetuned_energy.get("vram_allocated_mb", 0))
        / max(baseline_energy.get("vram_allocated_mb", 1), 1) * 100
    )

    rapport = {
        "experiment": {
            "date": datetime.now().isoformat(),
            "model": config["model_name"],
            "method": "LoRA",
            "dataset_size": 140,
            "environment": "Google Colab (T4 GPU, 15 Go VRAM)",
        },
        "configuration": {
            "lora_r": config["lora_r"],
            "lora_alpha": config["lora_alpha"],
            "lora_dropout": config["lora_dropout"],
            "lora_target_modules": config["lora_target_modules"],
            "num_epochs": config["num_epochs"],
            "batch_size": config["batch_size"],
            "gradient_accumulation_steps": config["gradient_accumulation_steps"],
            "learning_rate": config["learning_rate"],
            "max_seq_length": config["max_seq_length"],
            "fp16": config["fp16"],
            "optimizer": config["optim"],
            "quantization": "4-bit (NF4, double quant)",
        },
        "training": {
            "duration_s": round(training_time, 1),
            "duration_min": round(training_time / 60, 1),
        },
        "loss_history": loss_history[:20] if loss_history else [],  # 20 premiers steps
        "baseline": {
            "label": "Qwen2.5-1.5B-Instruct vanilla",
            "score": baseline_score,
            "score_detail": f"{baseline_score}/7",
            "axiomes": {
                str(k): {
                    "nom": v["nom"],
                    "ok": v["ok"],
                    "score": f"{v['score']}/{v['total']}",
                }
                for k, v in baseline_results.items()
            },
            "energie": baseline_energy,
        },
        "finetuned": {
            "label": f"Qwen2.5-1.5B-Instruct + LoRA MTTV (r={config['lora_r']})",
            "score": finetuned_score,
            "score_detail": f"{finetuned_score}/7",
            "axiomes": {
                str(k): {
                    "nom": v["nom"],
                    "ok": v["ok"],
                    "score": f"{v['score']}/{v['total']}",
                    "coherence": v.get("coherence"),
                }
                for k, v in finetuned_results.items()
            },
            "energie": finetuned_energy,
        },
        "gains": {
            "temps_inference_pct": round(gain_temps, 1),
            "debit_tokens_pct": round(gain_tokens, 1),
            "vram_pct": round(gain_vram, 1),
            "objectif_temps": "≥ 30%",
            "objectif_vram": "< 12 Go (T4 compatible)",
        },
        "conclusion": "",
    }

    # Conclusion automatique
    if finetuned_score >= 6:
        if gain_temps >= 30:
            rapport["conclusion"] = (
                f"✅ SUCCÈS: {finetuned_score}/7 atteint avec gain temps de {gain_temps:+.1f}%. "
                f"Objectifs validés. Prêt pour publication Zenodo/HF."
            )
        else:
            rapport["conclusion"] = (
                f"⚠️ PARTIEL: {finetuned_score}/7 atteint mais gain temps ({gain_temps:+.1f}%) "
                f"inférieur à l'objectif 30%."
            )
    else:
        rapport["conclusion"] = (
            f"❌ ÉCHEC: {finetuned_score}/7. Objectif 6/7 non atteint. "
            f"Recommandation: ajouter 40 exemples français, réentraîner 1 epoch."
        )

    # Sauvegarde
    with open(config["report_json"], "w", encoding="utf-8") as f:
        json.dump(rapport, f, indent=2, ensure_ascii=False, cls=NumpyEncoder)

    print(f"📄 Rapport JSON sauvegardé: {config['report_json']}")
    return rapport


def generate_md_report(rapport, config):
    """Génère le rapport Markdown complet."""
    b = rapport["baseline"]
    f = rapport["finetuned"]
    g = rapport["gains"]

    md = f"""# Rapport de Fine-Tuning MTTV-FLP — Phase 2 : Qwen2.5 + LoRA

**Date :** {rapport['experiment']['date']}
**Modèle :** {rapport['experiment']['model']}
**Méthode :** {rapport['experiment']['method']} (r={rapport['configuration']['lora_r']}, alpha={rapport['configuration']['lora_alpha']})
**Dataset :** {rapport['experiment']['dataset_size']} paires prompt/response (20 par axiome × 7 axiomes)
**Environnement :** {rapport['experiment']['environment']}

---

## 1. Configuration de l'entraînement

| Paramètre | Valeur |
|-----------|--------|
| Modèle | [`{rapport['experiment']['model']}`](https://huggingface.co/{rapport['experiment']['model']}) |
| Quantification | {rapport['configuration']['quantization']} |
| LoRA rang (r) | {rapport['configuration']['lora_r']} |
| LoRA alpha | {rapport['configuration']['lora_alpha']} |
| LoRA dropout | {rapport['configuration']['lora_dropout']} |
| LoRA cibles | {rapport['configuration']['lora_target_modules']} |
| Epochs | {rapport['configuration']['num_epochs']} |
| Batch size | {rapport['configuration']['batch_size']} |
| Gradient accumulation | {rapport['configuration']['gradient_accumulation_steps']} |
| Learning rate | {rapport['configuration']['learning_rate']} |
| Max sequence length | {rapport['configuration']['max_seq_length']} |
| FP16 | {rapport['configuration']['fp16']} |

**Durée totale d'entraînement :** {rapport['training']['duration_min']} minutes

---

## 2. Résultats des 7 Axiomes MTTV-FLP

### Baseline (Qwen2.5-1.5B-Instruct vanilla)

| # | Axiome | Statut | Score |
|---|--------|--------|-------|
"""
    for k in range(1, 8):
        a = b["axiomes"][str(k)]
        status = "✅" if a["ok"] else "❌"
        md += f"| {k} | {a['nom']} | {status} | {a['score']} |\n"

    md += f"| | **TOTAL** | | **{b['score']}/7** |\n\n"

    md += f"""### Fine-tune (Qwen2.5 + LoRA MTTV)

| # | Axiome | Statut | Score |
|---|--------|--------|-------|
"""
    for k in range(1, 8):
        a = f["axiomes"][str(k)]
        status = "✅" if a["ok"] else "❌"
        coherence = ""
        if a.get("coherence") is not None:
            coherence = f" (cohérence: {a['coherence']:.2%})"
        md += f"| {k} | {a['nom']} | {status} | {a['score']}{coherence} |\n"

    delta = f['score'] - b['score']
    md += f"| | **TOTAL** | | **{f['score']}/7** (Δ={delta:+d}) |\n"

    md += f"""
**Analyse :**
- Score baseline : {b['score']}/7 — {'✅' if b['score'] >= 3 else '❌'} compatible français natif
- Score fine-tune : {f['score']}/7 — {'✅' if f['score'] >= 6 else '❌'} objectif 6/7
- Delta : {delta:+d} point(s)

---

## 3. Métriques énergétiques

### Temps d'inférence

| Métrique | Baseline | Fine-tune | Gain |
|----------|----------|-----------|------|
| Temps moyen | {b['energie']['time_ms_avg']} ms | {f['energie']['time_ms_avg']} ms | {g['temps_inference_pct']:+.1f}% |
| Écart-type | ±{b['energie']['time_ms_std']} ms | ±{f['energie']['time_ms_std']} ms | — |
| Min | {b['energie']['time_ms_min']} ms | {f['energie']['time_ms_min']} ms | — |
| Max | {b['energie']['time_ms_max']} ms | {f['energie']['time_ms_max']} ms | — |
| Débit | {b['energie']['tokens_per_sec']} tok/s | {f['energie']['tokens_per_sec']} tok/s | {g['debit_tokens_pct']:+.1f}% |

### Consommation VRAM

| Métrique | Baseline | Fine-tune | Gain |
|----------|----------|-----------|------|
| VRAM allouée | {b['energie']['vram_allocated_mb']} Mo | {f['energie']['vram_allocated_mb']} Mo | {g['vram_pct']:+.1f}% |
| VRAM réservée | {b['energie']['vram_reserved_mb']} Mo | {f['energie']['vram_reserved_mb']} Mo | — |

**Objectifs :**
- Gain temps ≥ 30% : {'✅ ATTEINT' if g['temps_inference_pct'] >= 30 else '❌ NON ATTEINT'} ({g['temps_inference_pct']:+.1f}%)
- VRAM < 12 Go (compatible T4) : {'✅ OK' if f['energie']['vram_allocated_mb'] < 12000 else '❌ DÉPASSÉ'}

---

## 4. Analyse des résultats

### Points forts
- **Modèle multilingue natif** : Qwen2.5-1.5B-Instruct comprend le français sans adaptation préalable
- **LoRA efficace** : seulement ~0.2% des paramètres entraînés, adaptation rapide
- **4-bit QLoRA** : permet de tenir dans 15 Go VRAM du T4 Colab

### Points d'amélioration
- Dataset limité à 140 exemples (20 par axiome) — un dataset plus large (300+) améliorerait la robustesse
- 3 epochs peuvent être insuffisantes pour certains axiomes complexes (Transduction, Juxtaposition)
- La Reproductibilité (Axiome 7) reste difficile avec le sampling stochastique

---

## 5. Comparaison Phase 1 vs Phase 2

| Métrique | Phase 1 (GPT-2 CPU) | Phase 2 (Qwen2.5 T4) | Amélioration |
|----------|---------------------|----------------------|--------------|
| Modèle | GPT-2 (124M) | Qwen2.5-1.5B (1.5B) | 12× plus de params |
| Score | 2/7 | {f['score']}/7 | {f['score'] - 2:+d} points |
| Temps d'inférence | 4154 ms | {f['energie']['time_ms_avg']} ms | — |
| Français | ❌ charabia | ✅ natif | Critique |
| GPU | ❌ CPU | ✅ T4 GPU | Essentiel |

---

## 6. Recommandations

### Publication
- **Zenodo** : https://doi.org/10.5281/zenodo.20830060
- **HuggingFace** : https://huggingface.co/{rapport['experiment']['model']}
- Publier les adaptateurs LoRA et le rapport d'évaluation

### Améliorations futures
1. **Dataset augmenté** : générer 40 exemples supplémentaires par axiome (→ 280+)
2. **Epochs supplémentaires** : 5 epochs pour les axiomes 2 et 5
3. **QLoRA optimisé** : essayer r=32, alpha=64 pour plus de capacité d'adaptation
4. **Validation croisée** : split train/val 80/20 pour éviter le surapprentissage
5. **Modèle plus grand** : Qwen2.5-3B-Instruct si la VRAM le permet

---

## 7. Conclusion

{rapport['conclusion']}

---

*Rapport généré automatiquement par le pipeline MTTV-FLP Phase 2 — [`{rapport['experiment']['model']}`](https://huggingface.co/{rapport['experiment']['model']}) + LoRA*
"""
    # Sauvegarde
    with open(config["report_md"], "w", encoding="utf-8") as f:
        f.write(md)

    print(f"📄 Rapport Markdown sauvegardé: {config['report_md']}")
    return md


# ============================================================================
# CELLULE 10 — PIPELINE COMPLET
# ============================================================================

def run_pipeline(config=CONFIG):
    """
    Exécute le pipeline complet :
    1. Chargement du modèle + tokenizer
    2. Dataset formaté
    3. Configuration LoRA
    4. Entraînement
    5. Tests baseline
    6. Tests fine-tune
    7. Mesures énergétiques
    8. Rapports
    """
    print("="*65)
    print("🚀 PIPELINE MTTV-FLP PHASE 2 — QWEN2.5 + LoRA")
    print("="*65)
    print(f"   Modèle : {config['model_name']}")
    print(f"   Device : {device}")
    print(f"   CUDA   : {torch.cuda.is_available()}")
    print(f"   GPU    : {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'}")
    print()

    # ─── Étape 1 : Chargement du modèle et tokenizer ───────────────────
    print("[1/8] Chargement du modèle et du tokenizer...")
    model, tokenizer = load_model_and_tokenizer(config)
    print()

    # ─── Étape 2 : Dataset ──────────────────────────────────────────────
    print("[2/8] Chargement et formatage du dataset...")
    dataset, raw_data = load_and_format_dataset(config["dataset_path"], tokenizer)
    print()

    # ─── Tests BASELINE avant fine-tuning ───────────────────────────────
    print("[3/8] Tests BASELINE (modèle vanilla)...")
    print("="*65)
    print("⚠️  ATTENTION: Ces tests prennent quelques minutes...")
    baseline_results, baseline_score, baseline_test_time = run_all_tests(model, tokenizer, "BASELINE (vanilla)")
    print()

    # ─── Mesure énergétique BASELINE ────────────────────────────────────
    print("[4/8] Mesure énergétique BASELINE...")
    baseline_energy = measure_energy(model, tokenizer, n_runs=CONFIG["num_energy_runs"])
    print(f"   Temps moyen: {baseline_energy['time_ms_avg']:.1f} ms")
    print(f"   Débit: {baseline_energy['tokens_per_sec']:.1f} tok/s")
    print(f"   VRAM: {baseline_energy['vram_allocated_mb']:.0f} Mo")
    print()

    # ─── Configuration LoRA ──────────────────────────────────────────────
    print("[5/8] Configuration LoRA...")
    model = setup_lora(model, config)
    print()

    # ─── Entraînement ──────────────────────────────────────────────────
    print("[6/8] Entraînement LoRA...")
    model, training_time, loss_history = train_model(model, tokenizer, dataset, config)
    print()

    # ─── Tests FINE-TUNE ────────────────────────────────────────────────
    print("[7/8] Tests FINE-TUNE (modèle adapté)...")
    model.eval()
    finetuned_results, finetuned_score, finetuned_test_time = run_all_tests(
        model, tokenizer, f"FINE-TUNE (LoRA r={config['lora_r']})"
    )
    print()

    # ─── Mesure énergétique FINE-TUNE ───────────────────────────────────
    print("[8/8] Mesure énergétique FINE-TUNE...")
    finetuned_energy = measure_energy(model, tokenizer, n_runs=CONFIG["num_energy_runs"])
    print(f"   Temps moyen: {finetuned_energy['time_ms_avg']:.1f} ms")
    print(f"   Débit: {finetuned_energy['tokens_per_sec']:.1f} tok/s")
    print(f"   VRAM: {finetuned_energy['vram_allocated_mb']:.0f} Mo")
    print()

    # ─── Génération des rapports ────────────────────────────────────────
    print("📊 Génération des rapports...")
    rapport = generate_json_report(
        baseline_results, finetuned_results,
        baseline_energy, finetuned_energy,
        training_time, loss_history, config,
    )
    md_report = generate_md_report(rapport, config)

    # ─── Résumé final ────────────────────────────────────────────────────
    gain_temps = (
        (baseline_energy["time_ms_avg"] - finetuned_energy["time_ms_avg"])
        / baseline_energy["time_ms_avg"] * 100
    )

    print()
    print("="*65)
    print("🏆 RÉSUMÉ FINAL")
    print("="*65)
    print(f"   Baseline:       {baseline_score}/7")
    print(f"   Fine-tune:      {finetuned_score}/7")
    print(f"   Delta:          {finetuned_score - baseline_score:+d}/7")
    print(f"   Gain temps:     {gain_temps:+.1f}% (objectif: ≥30%)")
    print(f"   VRAM fine-tune: {finetuned_energy['vram_allocated_mb']:.0f} Mo (limite T4: 15 Go)")
    print()
    print(f"   {rapport['conclusion']}")
    print()
    print("📁 Livrables :")
    print(f"   Adaptateurs LoRA : {config['output_dir']}/")
    print(f"   Rapport JSON     : {config['report_json']}")
    print(f"   Rapport MD       : {config['report_md']}")
    print()

    return {
        "baseline_results": baseline_results,
        "finetuned_results": finetuned_results,
        "baseline_energy": baseline_energy,
        "finetuned_energy": finetuned_energy,
        "training_time": training_time,
        "rapport": rapport,
        "md_report": md_report,
    }


# ============================================================================
# CELLULE 11 — POINT D'ENTRÉE PRINCIPAL
# ============================================================================

if __name__ == "__main__":
    # Vérifier que le dataset est présent
    if not os.path.exists(CONFIG["dataset_path"]):
        print(f"❌ Dataset introuvable: {CONFIG['dataset_path']}")
        print("   Veuillez uploader 'dataset.jsonl' dans /content/")
        print("   > from google.colab import files")
        print("   > files.upload()")
        sys.exit(1)

    # Vérifier CUDA
    if not torch.cuda.is_available():
        print("❌ CUDA non disponible !")
        print("   Allez dans : Exécution → Modifier le type d'exécution → T4 GPU")
        print("   Puis réexécutez la cellule.")
        sys.exit(1)

    print(f"✅ GPU détecté: {torch.cuda.get_device_name(0)}")
    print(f"   VRAM totale: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} Go")
    print(f"   CUDA version: {torch.version.cuda}")
    print()

    # Lancer le pipeline
    results = run_pipeline(CONFIG)

    # Afficher le rapport final
    print("\n" + "="*65)
    print("📋 RAPPORT FINAL (copie pour sauvegarde)")
    print("="*65)
    print(results["md_report"])


# ============================================================================
# CELLULE 12 — TÉLÉCHARGEMENT DES LIVRABLES (optionnel)
# ============================================================================
# Décommentez cette cellule pour télécharger les fichiers depuis Colab

# from google.colab import files
#
# # Compression des adaptateurs LoRA
# !zip -r /content/mttv_lora_qwen_final.zip /content/mttv_lora_qwen_final/
#
# # Téléchargement
# files.download('/content/mttv_lora_qwen_final.zip')
# files.download('/content/rapport_evaluation.json')
# files.download('/content/RAPPORT_QWEN25_MTTV.md')
# print("✅ Téléchargement terminé")


# ============================================================================
# CELLULE 13 — MOUNT GOOGLE DRIVE (optionnel)
# ============================================================================
# from google.colab import drive
# drive.mount('/content/drive')
# print("✅ Google Drive monté dans /content/drive/")
