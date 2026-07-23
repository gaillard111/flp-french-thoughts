"""
Cellule Colab standalone : sauvegarde, recuperation et telechargement
du modele Phi-3-mini fine-tune avec MTTV-flp.

Usage : copier-coller dans une cellule Colab et executer.
"""

import os, zipfile, gc, subprocess, sys
from google.colab import files
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

CHECKPOINT_DIR = "/content/mttv_flp_checkpoints"
MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"

print("=" * 60)
print("ETAPE 1/5 - Verification des variables en memoire")
print("=" * 60)

model_in_memory = False
tokenizer_in_memory = False

try:
    if 'model' in dir() or 'model' in globals():
        _ = model.config
        model_in_memory = True
        print("  [OK] variable 'model' trouvee en memoire")
    else:
        print("  [INFO] variable 'model' absente")
except Exception as e:
    print(f"  [INFO] model inaccessible: {e}")

try:
    if 'tokenizer' in dir() or 'tokenizer' in globals():
        _ = tokenizer.vocab_size
        tokenizer_in_memory = True
        print("  [OK] variable 'tokenizer' trouvee en memoire")
    else:
        print("  [INFO] variable 'tokenizer' absente")
except Exception as e:
    print(f"  [INFO] tokenizer inaccessible: {e}")

print()

# ---------------------------------------------------------------------------
print("=" * 60)
print("ETAPE 2/5 - Sauvegarde du modele et du tokenizer")
print("=" * 60)

os.makedirs(CHECKPOINT_DIR, exist_ok=True)
sauvegarde_ok = False

if model_in_memory and tokenizer_in_memory:
    print("  Modele en memoire -> sauvegarde directe...")
    try:
        model.save_pretrained(CHECKPOINT_DIR, safe_serialization=True)
        print("  [OK] model.save_pretrained() reussi")
        tokenizer.save_pretrained(CHECKPOINT_DIR)
        print("  [OK] tokenizer.save_pretrained() reussi")
        sauvegarde_ok = True
    except Exception as e:
        print(f"  [ERREUR] sauvegarde directe echouee: {e}")
        print("  Tentative avec merge_and_unload...")
        try:
            if hasattr(model, "merge_and_unload"):
                m = model.merge_and_unload()
                m.save_pretrained(CHECKPOINT_DIR, safe_serialization=True)
                del m
                print("  [OK] merge_and_unload() + save_pretrained() reussi")
                tokenizer.save_pretrained(CHECKPOINT_DIR)
                print("  [OK] tokenizer sauvegarde")
                sauvegarde_ok = True
            else:
                print("  [ERREUR] merge_and_unload non disponible")
        except Exception as e2:
            print(f"  [ERREUR] sauvegarde avec merge echouee: {e2}")
else:
    print("  Modele NON disponible en memoire -> rechargement depuis HuggingFace")
    try:
        print("  Installation de bitsandbytes==0.46.1...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "bitsandbytes==0.46.1"])
        print("  [OK] bitsandbytes 0.46.1 installe")
    except Exception as e:
        print(f"  [WARN] installation bitsandbytes: {e}")

    try:
        print(f"  Rechargement de {MODEL_NAME} en 4-bit...")
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            quantization_config=quant_config,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True,
        )
        print("  [OK] modele recharge depuis HuggingFace")

        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        print("  [OK] tokenizer recharge")

        model.save_pretrained(CHECKPOINT_DIR, safe_serialization=True)
        print("  [OK] model.save_pretrained() reussi")
        tokenizer.save_pretrained(CHECKPOINT_DIR)
        print("  [OK] tokenizer.save_pretrained() reussi")
        sauvegarde_ok = True

    except Exception as e:
        print(f"  [ERREUR] rechargement et sauvegarde echoues: {e}")

print()

# ---------------------------------------------------------------------------
print("=" * 60)
print("ETAPE 3/5 - Verification du dossier de checkpoints")
print("=" * 60)

if os.path.exists(CHECKPOINT_DIR):
    fichiers = os.listdir(CHECKPOINT_DIR)
    print(f"  Dossier: {CHECKPOINT_DIR}")
    print(f"  Fichiers trouves: {len(fichiers)}")
    for f in sorted(fichiers)[:10]:
        path = os.path.join(CHECKPOINT_DIR, f)
        taille = os.path.getsize(path)
        if taille > 1024*1024:
            print(f"    - {f} ({taille/1024/1024:.1f} MB)")
        elif taille > 1024:
            print(f"    - {f} ({taille/1024:.1f} KB)")
        else:
            print(f"    - {f} ({taille} B)")
    if len(fichiers) > 10:
        print(f"    ... et {len(fichiers)-10} autres fichiers")
else:
    print(f"  [ERREUR] Le dossier {CHECKPOINT_DIR} n'existe pas")

print()

# ---------------------------------------------------------------------------
print("=" * 60)
print("ETAPE 4/5 - Compression du dossier en zip")
print("=" * 60)

zip_path = "/content/mttv_flp_checkpoints.zip"

try:
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files_list in os.walk(CHECKPOINT_DIR):
            for file in files_list:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(CHECKPOINT_DIR))
                zf.write(file_path, arcname=arcname)
    print(f"  [OK] Zip cree: {zip_path}")
    size_mb = os.path.getsize(zip_path) / (1024*1024)
    print(f"  Taille: {size_mb:.1f} MB")
except Exception as e:
    print(f"  [ERREUR] Compression echouee: {e}")

print()

# ---------------------------------------------------------------------------
print("=" * 60)
print("ETAPE 5/5 - Telechargement")
print("=" * 60)

try:
    if os.path.exists(zip_path):
        print(f"  Telechargement de {zip_path}...")
        files.download(zip_path)
        print("  [OK] Telechargement lance")
    else:
        print(f"  [ERREUR] Fichier zip introuvable: {zip_path}")
except Exception as e:
    print(f"  [ERREUR] Telechargement echoue: {e}")

print()
gc.collect()
print("=" * 60)
print("TERMINE")
print("=" * 60)
