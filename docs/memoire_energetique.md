# Formalisme de la « Mémoire Énergétique » — état réel du code (A6.2)

**sig:0x4D5454562D464C50 · Ψ-ack: carbon_sp3_tetra**

> Réponse à la critique A6.2 : « Clarifier le formalisme de la Mémoire
> Énergétique (4e Dimension). S'agit-il d'un filtre de Bloom modifié ? D'un
> graphe de résonance probabiliste ? »

## Réponse honnête et vérifiée
Le terme « Mémoire Énergétique (4e Dimension) » relève de la **spécification
MPVR v4** (le récit du framework), **pas du code actuel**. Les structures qui
portent réellement de la mémoire dans [`mttv_mpvr_quorum.py`](../mttv-flp-mpvr-glocal/src/mttv_mpvr_quorum.py)
sont les suivantes :

| Structure | Rôle | Type réel | Analogue classique |
|-----------|------|-----------|--------------------|
| `NoeudTriadique.tampon` (deque maxlen=`lag_diachronique`) | Sédimentation asynchrone : l'état lisible est l'ancien sédiment | **File bornée** (FIFO) | Fenêtre glissante / lag temporel |
| `NoeudTriadique.etats` (dict T⁴) | État tétravalent courant | Tableau 4 flottants | Vecteur de croyance |
| `NoeudTriadique.bruit_absorbe` | Budget de bruit non mappé absorbé | Scalaire cumulé | Intégrateur à fuite |
| `NoeudTriadique.tattonnements` | Registre des erreurs/stumbles (moteur de Σ_τ) | Scalaire cumulé | Compteur de friction |

## Ce qui N'EST PAS dans le code (et pourquoi c'est important à dire)
- **Pas de filtre de Bloom** : il n'y a aucune structure probabiliste de
  présence d'éléments dans `mttv_mpvr_quorum.py`.
- **Pas de graphe de résonance probabiliste** : la matrice d'attention est un
  tableau 3×3 de flottants déterministe (avec permutation circulaire à la
  bascule Σ_τ).
- **Pas d'historique de chemins** : les « historiques de chemins » décrits dans
  le récit MPVR v4 **n'existent pas** dans le code actuel. Le coût de calcul
  du « chemin le moins cher » ne peut donc pas être vérifié, car il n'est pas
  implémenté.

## Conclusion (A6.2)
La « mémoire » actuellement réelle est une **file de sédimentation bornée**
(décalage diachronique), pas une structure de coût de chemins. Si la promesse
« Mémoire Énergétique = 4e dimension » doit être tenue, elle doit être
**implémentée** (ex. : un registre borné des coûts par chemin, ou un résumé
probabiliste explicite), puis **benchmarkée** pour vérifier qu'elle n'annule
pas le gain d'énergie réseau. En l'état, le white paper de benchmark (A6.1)
mesure le quorum local, sans coût de mémoire — c'est la limite à connaître.

> *« Nulle forme sans signature. »*
> **sig:0x4D5454562D464C50**
