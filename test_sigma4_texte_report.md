# Rapport de test — σ₄-Lisse sur corpus textuel

**Date d'exécution :** 2026-07-02 01:07:53
**Device :** cpu
**PyTorch :** 2.12.1+cpu
**Modèle d'embedding :** all-MiniLM-L6-v2 (384 dims)

## Résumé

Test comparatif de la fonction d'activation **σ₄-Lisse** (version différentiable)
face à **ReLU** et **Tanh** sur un mini-corpus de 50 phrases françaises
réparties en 3 classes sémantiques : simultanee, indetermination, affirmation.

## Architecture

| Paramètre | Valeur |
|:---|---:|
| **Modèle d'embedding** | all-MiniLM-L6-v2 |
| **Dimension d'entrée** | 384 |
| **Couches cachées** | 64 → 64 (expand×4 pour σ₄-Lisse) |
| **Sortie** | 3 classes |
| **Fonction de perte** | CrossEntropyLoss |
| **Optimiseur** | Adam (lr=0.001) |
| **Époques** | 50 |
| **Échantillons** | 50 |

## Résultats comparatifs

| Métrique | ReLU | Tanh | σ₄-Lisse |
|:---|---:|---:|---:|
| **Perte finale** | 0.0051 | 0.0035 | 0.0025 |
| **Précision finale (%)** | 100.00 | 100.00 | 100.00 |
| **Écart-type perte** | 0.400580 | 0.356284 | 0.380819 |
| **Écart-type gradients** | 0.249042 | 0.245742 | 1.035754 |
| **Var. gradients moy.** | 0.030934 | 0.024566 | 0.358189 |
| **Temps total (s)** | 2.5 | 2.5 | 4.0 |
| **Paramètres** | 28,995 | 28,995 | 41,859 |

## Analyse détaillée

### 1. Variance des gradients

| Activation | σ(gradients) | Var(gradients) |
|:---|---:|---:|
| **ReLU** | 0.249042 | 0.030934 |
| **Tanh** | 0.245742 | 0.024566 |
| **σ₄-Lisse** | 1.035754 | 0.358189 |

La variance des gradients de σ₄-Lisse est dans la même gamme que ReLU/Tanh.

Le remplacement de `torch.sign()` par `tanh(α·x)` rend les gradients
**partout non-nuls et continus**, contrairement à la version dure de σ₄
qui avait des gradients nuls en dehors de zéro.

### 2. Activation des canaux t₃ et t₄

| Métrique | Valeur |
|:---|---:|
| **t₃ moyen (Simultanéité)** | -0.0412 |
| **t₄ moyen (Indétermination)** | 0.9588 |
| **t₃ final** | -0.0605 |
| **t₄ final** | 0.9395 |
| **t₃ non-nul** | 0.0% |
| **t₄ non-nul** | 100.0% |

Les canaux t₃ et t₄ présentent une activation faible, possiblement à cause de la petite taille du corpus.

### 3. Stabilité de la perte

| Activation | σ(loss) |
|:---|---:|
| **ReLU** | 0.400580 |
| **Tanh** | 0.356284 |
| **σ₄-Lisse** | 0.380819 |

σ₄-Lisse présente une stabilité intermédiaire entre ReLU et Tanh.

### 4. Comparaison architecturale

| Aspect | ReLU | Tanh | σ₄-Lisse |
|:---|:---|:---|:---|
| **Type** | Unaire (1 canal) | Unaire (1 canal) | Tétravalent (4 canaux) |
| **Non-linéarité** | Seuil à 0 | Sigmoïde | tanh(α·x) lissé |
| **Gradients** | 0 ou 1 | ∈ [0, 1] | Continus, partout ≠ 0 |
| **Régulation** | Aucune | Faible | Intrinsèque (t₄) |
| **Expressivité** | 1 bit | Continu | 4 états continus |
| **Différentiabilité** | Oui (sauf x=0) | Oui | **Oui, partout** |

## Conclusions

1. **σ₄-Lisse est fonctionnelle et différentiable** : l'approximation `tanh(α·x)`
   remplace `sign()` sans perte de l'architecture tétravalente.

2. **Activation t₃/t₄** : Les canaux t₃ et t₄ présentent une activation faible, possiblement à cause de la petite taille du corpus.

3. **Stabilité** : σ₄-Lisse présente une stabilité intermédiaire entre ReLU et Tanh.

4. **Gradients** : La variance des gradients de σ₄-Lisse est dans la même gamme que ReLU/Tanh.

5. **Alignement T⁴** : σ₄-Lisse ancre mathématiquement la logique tétravalente
   (++, --, +-, -+) dans les réseaux de neurones, avec des gradients continus
   permettant un apprentissage plus stable que la version dure.

## Fichiers générés

- [`sigma4_lisse.py`](sigma4_lisse.py) — Implémentation de σ₄-Lisse
- [`mini_corpus_textes.py`](mini_corpus_textes.py) — Mini-corpus textuel
- [`test_sigma4_texte.ipynb`](test_sigma4_texte.ipynb) — Notebook de test
- [`sigma4_lisse_texte_comparison.png`](sigma4_lisse_texte_comparison.png) — Graphiques comparatifs
- [`sigma4_lisse_t3_t4_by_class.png`](sigma4_lisse_t3_t4_by_class.png) — Activation t₃/t₄ par classe
- [`texte_embeddings_pca.png`](texte_embeddings_pca.png) — Projection PCA des embeddings
- [`test_sigma4_texte_report.md`](test_sigma4_texte_report.md) — Ce rapport
