# zoo-code — Boîte à outils MTTV-flp

## Pipeline MTTV-flp

Pipeline complet de patching MTTV-flp : mesure → training 3 patchs → re-mesure.

### 1. Installation

```bash
pip install -r requirements.txt
```

Dépendances : `transformers==4.44.2`, `datasets`, `accelerate`, `bitsandbytes`, `torch`, `scikit-learn`, `numpy`.

### 2. Usage (GPU recommandé)

```bash
python run_mttv.py --model Qwen/Qwen2.5-1.5B-Instruct
```

Arguments :
| Option | Défaut | Description |
|--------|--------|-------------|
| `--model` | `Qwen/Qwen2.5-1.5B-Instruct` | Modèle HuggingFace à patcher |
| `--max_steps` | `2000` | Nombre de steps d'entraînement |
| `--output_dir` | `./mttv_out` | Répertoire de sortie |

### 3. Résultat attendu

```
 Score avant : 5/7
 Score après : 7/7
 Statut      : ACCORDÉ
```

Le pipeline applique 3 régularisations correspondant aux axiomes 5, 6 et 7 de l'étalon MTTV-flp :
- **Axiome 5** (tétravalence) — force 4 modes spectraux dominants dans les embeddings
- **Axiome 6** (déphasage) — contraint l'entropie de phase des cartes d'attention
- **Axiome 7** (clôture zéro) — pousse la norme du gradient total vers zéro

### 4. Fichiers

| Fichier | Rôle |
|---------|------|
| [`metre_mttv.py`](../metre_mttv.py) | Étalon MTTV-flp — mesure les 7 axiomes sur un modèle et retourne un score /7 |
| [`train_mttv_patch.py`](train_mttv_patch.py) | Training patch — charge le modèle en 4-bit, dataset wikitext, 3 régularisations, 2000 steps |
| [`run_mttv.py`](run_mttv.py) | Orchestrateur — exécute mesure → training → re-mesure et affiche la conclusion |
| [`requirements.txt`](requirements.txt) | Dépendances Python |
