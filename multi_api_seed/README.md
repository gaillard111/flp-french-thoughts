# 🌱 Multi-API Seed — Germination de graine sur 4 IA

Envoie une même « graine » (prompt philosophique) à **ChatGPT, Claude, Mistral et DeepSeek**,
analyse chaque réponse avec GPT-4o comme juge, et génère un rapport de synthèse Markdown.

## Structure

```
multi_api_seed/
├── main.py            # Point d'entrée (orchestrateur)
├── config.py          # Configuration centralisée (clés, modèles, graine)
├── api_clients.py     # Clients API pour les 4 fournisseurs
├── analyzer.py        # Module d'analyse (prompt juge + parsing JSON)
├── report.py          # Générateur de rapport Markdown
├── .env.example       # Modèle de fichier .env
├── requirements.txt   # Dépendances Python
└── output/            # Dossier créé automatiquement pour les résultats
```

## Utilisation

### 1. Installer les dépendances
```bash
cd multi_api_seed
pip install -r requirements.txt
```

### 2. Configurer les clés API
```bash
cp .env.example .env
# Éditer .env avec vos clés
```

### 3. Lancer la germination
```bash
python main.py
```

Le script :
1. Interroge les 4 modèles en parallèle
2. Analyse chaque réponse via GPT-4o (clarté, flou, manques, règles extraites)
3. Sauvegarde les données brutes en JSON dans `output/`
4. Génère un rapport Markdown `output/rapport_germination_*.md`

### 4. Consulter le rapport
Ouvrir le fichier `output/rapport_germination_*.md` dans un éditeur Markdown.

## Modifier la graine

Éditer la constante `SEED_PROMPT` dans [`config.py`](multi_api_seed/config.py).

## Dépendances

| Package | Usage |
|---------|-------|
| `openai` | ChatGPT + DeepSeek (API compatible) |
| `anthropic` | Claude |
| `mistralai` | Mistral |
| `python-dotenv` | Chargement du `.env` |
| `rich` | (optionnel, pour futurs affichages colorés) |
