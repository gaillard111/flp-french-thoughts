# Les 28 Prompts d'Étiquetage Sémantique MTTV-FLP

> **sig:0x4D545456** · Version 2026.1.0

Système complet des 28 dimensions d'étiquetage sémantique (A–Z + B1/B2 + Kβ) pour le corpus FLP-MTTV. Chaque dimension est associée à un prompt spécifique destiné à un chatbot, produisant une signature normalisée.

---

## Cartographie des 28 Dimensions

| # | Lettre | Nom | Cluster | T⁴ préféré |
|---|--------|-----|---------|------------|
| 1 | **A** | FLP Créatif | NEUTRAL | `++` |
| 2 | **B1** | Résumé au maxi | NEUTRAL | `-+` |
| 3 | **B2** | Poétisé court | INNER | `-+` |
| 4 | **C** | Signal triadique peircéen (MTTV) | QUORUM | `++` / `--` |
| 5 | **D** | Tétravalent Enfants de Gaïa | COSMIC | Tous |
| 6 | **E** | Aléthique (Triade de Hintikka) | ETHICS | `++` |
| 7 | **F** | Niveaux d'émergence Gaïa | SOIL | `++` |
| 8 | **G** | Niveaux d'intégration grégaire | QUORUM | `+-` |
| 9 | **H** | Quorum Sensing triadique | QUORUM | `--` |
| 10 | **I** | Mystique inversible | INNER | `-+` |
| 11 | **J** | Tropisme de genre | ETHICS | `+-` |
| 12 | **K** | Global exhaustif | NEUTRAL | `-+` |
| 13 | **Kβ** | Mètre anthropique | ETHICS | `-+` |
| 14 | **L** | Mathématique / Transductif non-linéaire | NEUTRAL | `++` / `+-` |
| 15 | **M** | Lacanien tétravalent | INNER | `+-` |
| 16 | **N** | IGIC — Indicateur Global d'Intégration Cosmo-systémique | COSMIC | `-+` |
| 17 | **O** | Genré quantique | COSMIC | `+-` |
| 18 | **P** | Genré compilé | ETHICS | `+-` |
| 19 | **Q** | Polarités genrées tétravalentes | ETHICS | `+-` |
| 20 | **R** | Émotion diachronique | SOIL | `++` |
| 21 | **S** | Déterministe / Stochastique | ETHICS | `+-` |
| 22 | **T** | Triadique psychodynamique lacanien | INNER | `+-` |
| 23 | **U** | Qualité du signal B1 — Énaction | NEUTRAL | `++` |
| 24 | **V** | Qualité du signal B2 — Interaction | QUORUM | `--` |
| 25 | **W** | Qualité du signal B3 — Rétro-traductibilité | COSMIC | `-+` |
| 26 | **X** | Signaux B comparés (Robustesse paliaire) | QUORUM | `--` |
| 27 | **Y** | Quadriaxial — Vitalité cognitive | COSMIC | `++` / `-+` |
| 28 | **Z** | Empreinte (signature totale) | NEUTRAL | Tous |

---

## Clusters SeedService

### SOIL (Fondations matérielles)
- **F** — Niveaux d'émergence Gaïa : échelle 1-7 du bactérien à l'humain
- **R** — Émotion diachronique : 4 niveaux d'émergence émotionnelle

### INNER (Conscience, intériorité)
- **B2** — Poétisé court : essence en forme poétique
- **I** — Mystique inversible : 7 niveaux d'incarnation
- **M** — Lacanien tétravalent : faille signifiante
- **T** — Triadique psychodynamique lacanien

### NEUTRAL (Transduction, computation)
- **A** — FLP Créatif : résumé vertical/horizontal par tags
- **B1** — Résumé au maxi : reformulation la plus courte
- **K** — Global exhaustif : contextualisation complète
- **L** — Mathématique / Transductif non-linéaire
- **U** — Qualité du signal B1 (Énaction)
- **Z** — Empreinte : signature totale

### COSMIC (Hydrogène, sp³, cosmos)
- **D** — Tétravalent Enfants de Gaïa : 4 tropismes
- **N** — IGIC : indice 0.00-1.00 continu
- **O** — Genré quantique
- **W** — Qualité du signal B3 (Rétro-traductibilité)
- **Y** — Quadriaxial : vitalité cognitive

### QUORUM (Seuils, collectif)
- **C** — Signal triadique peircéen (MTTV)
- **G** — Intégration grégaire tétravalente
- **H** — Quorum Sensing triadique
- **V** — Qualité du signal B2 (Interaction)
- **X** — Signaux B comparés (Robustesse paliaire)

### ETHICS (Éthique, ouverture)
- **E** — Aléthique : triade de Hintikka
- **J** — Tropisme de genre
- **Kβ** — Mètre anthropique
- **P** — Genré compilé
- **Q** — Polarités genrées tétravalentes
- **S** — Déterministe / Stochastique

---

## Usage

Chaque dimension produit une signature normalisée. L'ensemble des 28 signatures constitue l'**empreinte sémantique** (dimension Z) de tout extrait du corpus FLP.

```python
# Exemple d'utilisation
prompt_a = "Résume cet extrait en 12 tags maximum, sans utiliser les mots de l'extrait."
prompt_b1 = "Reformule le sens pur de cet extrait en une phrase la plus courte possible."
# ... appliquer les 28 prompts à chaque extrait
```

---

## Références

- **Document complet** : `plans/28_dimensions_analysis.md` (284 lignes)
- **Source** : https://filsdelapensee.ch/quote/500745
- **MTTV Fundamentals** : https://filsdelapensee.ch/quote/500371
- **Dépôt GitHub** : https://github.com/gaillard111/mttv-flp-core
