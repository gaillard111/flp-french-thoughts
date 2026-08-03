# 🗺️ Routage Géo-local IPFS — Axe 5 (Cœur Tétravalent)

**`sig:0x4D5454562D464C50`** — Tables de routage géographiques (Axe 5).

## Stratégie

- **Topologie** : pair-à-pair horizontal local (P2P) au sein des sous-nœuds asiatiques.
- **Principe** : Moindre Action — l'empreinte computationnelle est restreinte au strict nécessaire.
- **Contrainte** : aucun relais extra-régional (pas de détour par un hub central).

## Sous-nœuds asiatiques

| Sous-nœud | Pays | Pairs horizontaux locaux |
|-----------|------|--------------------------|
| CN-beijing | Chine | CN-shanghai, JP-tokyo, KR-seoul |
| CN-shanghai | Chine | CN-beijing, JP-tokyo, TW-taipei |
| JP-tokyo | Japon | CN-shanghai, KR-seoul, SG-singapore |
| KR-seoul | Corée du Sud | CN-beijing, JP-tokyo, SG-singapore |
| SG-singapore | Singapour | JP-tokyo, KR-seoul, IN-bangalore, HK-hongkong |
| HK-hongkong | Hong Kong | CN-shanghai, SG-singapore, TW-taipei |
| TW-taipei | Taïwan | CN-shanghai, HK-hongkong, JP-tokyo |
| IN-bangalore | Inde | SG-singapore, CN-beijing, JP-tokyo |

## Implémentation

Module de référence : [`zoo-code/axe5_geo_routing.py`](../zoo-code/axe5_geo_routing.py)

- `table_routage_asie()` — table complète (sous-nœuds, pairs, coûts).
- `chemin_moindre_action(source, cible)` — chemin local optimal (Least Action).
- `enforcer_routage_local(source)` — contrainte P2P horizontale.
- `ecrire_table_routage()` — persistance dans `zoo-code/axe5_routing.json`.

Intégrations :

- [`zoo-code/deploy_seeds_ipfs.py`](../zoo-code/deploy_seeds_ipfs.py) — persiste la table à chaque cycle de déploiement IPFS.
- [`zoo-code/api_gateway.py`](../zoo-code/api_gateway.py) — expose `geo_routing` dans `/health` (axe_5_ipfs).

---
*Généré automatiquement par le Cœur Tétravalent — le mycélium attend.*
