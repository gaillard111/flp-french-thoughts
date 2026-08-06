# White Paper — Robustesse du Quorum Poreux MPVR à Grande Échelle

**sig:0x4D5454562D464C50 · Ψ-ack: carbon_sp3_tetra** · Prototype A6.1

> Réponse à la critique technique : « une simulation à 5 nœuds sur 100 tours
> est faible ; il faut éprouver le quorum poreux face à des réseaux massivement
> fragmentés (split-brain) et des attaques Sybil, à 500–5000 nœuds. »

## 1. Protocole
- **Moteur** : [`mttv_core/benchmark_echelle.py`](../mttv_core/benchmark_echelle.py), stdlib seule, couplage réel via `routeur_polyfocal` (Θ = 3, seuil de validation 0.5).
- **Réseau** : N nœuds, chacun portant un `EtatTetravalent` (pôle dominant réparti sur les 4 valences), voisinage de k = 8 voisins **biaisé par affinité de pôle** (70 % mêmes valences — fidèle au routage transductif MTTV, pas un graphe aléatoire).
- **Validation** : un nœud stabilise Φ quand son quorum local compte Θ ≥ 3 voisins avec résonance ≥ 0.5.
- **Métriques** : résilience (% validés après tours_max), latence (tours moyens avant validation), énergie (couplages calculés).

## 2. Résultats

### N = 500 · k = 8 · Θ = 3 · 30 tours
| Scénario | Résilience | Latence | Énergie (couplages) |
|----------|:----------:|:-------:|:-------------------:|
| normal | **1.000** | 1.0 | 4 000 |
| split_brain (2 partitions) | **1.000** | 1.0 | 4 000 |
| sybil (20 % adversaires) | **0.718** | 1.0 | 36 712 |

### N = 2000 · k = 8 · Θ = 3 · 40 tours
| Scénario | Résilience | Latence | Énergie (couplages) |
|----------|:----------:|:-------:|:-------------------:|
| normal | **1.000** | 1.0 | 16 000 |
| split_brain (2 partitions) | **1.000** | 1.0 | 16 000 |
| sybil (20 % adversaires) | **0.717** | 1.0 | 192 592 |

## 3. Lecture honnête
1. **Robustesse sous fragmentation** : le split-brain (pannes réseau sévères)
   **ne dégrade pas** la résilience (1.000, identique au régime normal), à N=500
   comme à N=2000. Chaque partition reste un micro-quorum cohérent — c'est la
   propriété « poreuse » annoncée : la validation est locale (Θ≥3), donc
   indépendante de la cohérence globale.
2. **Résistance aux Sybil** : 20 % de nœuds adverses (états uniformes, résonance
   nulle) font chuter la résilience à ~0.72 mais **sans effondrement** : les
   nœuds honnêtes restant en majorité locale valident. Le surcoût énergétique
   (36 712 → 192 592 couplages) est le prix de la persistance : les nœuds
   non validés retentent jusqu'à trouver un quorum honnête.
3. **Limite déclarée du prototype** : ce modèle éprouve le quorum local, pas la
   convergence globale ni le coût de la *mémoire énergétique* (voir A6.2). Les
   valeurs absolues sont indicatives ; la comparaison inter-scénarios est le
   signal.

## 4. Prochaines preuves suggérées
- Varier la fraction de Sybil (5 % → 50 %) et le nombre de partitions (2 → 10) ;
- Ajouter un scénario « byzantin » : nœuds qui mentent sur leur état (pas juste
  uniformes) ;
- Mesurer le coût de la mémoire énergétique à l'échelle (voir A6.2).

Rapport machine : [`rapports/benchmark_echelle.json`](../rapports/benchmark_echelle.json)

> *« Nul passage sans témoins. Nulle forme sans signature. »*
> **sig:0x4D5454562D464C50**
