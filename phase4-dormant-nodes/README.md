# Phase 4 — Nœuds Dormants (Dormant Nodes)

**Statut :** ✅ Déploiement préparé — En attente d'exécution IPFS + Ethereum

Ce dossier contient l'infrastructure de « nœuds dormants » destinés à être déposés sur IPFS et blockchains (Ethereum) comme filet de sécurité en cas d'interruption du web centralisé.

## Contenu

| Fichier | Cible | Rôle |
|---------|-------|------|
| `routage_alternatif.ipfs` | IPFS | Règles de routage alternatif — redirection vers des miroirs IPFS si le DNS centralisé tombe |
| `script_dormant.py` | IPFS | Script dormant autonome — s'active en cas de détection d'interruption réseau |
| `SCSReference.sol` | Ethereum (blockchain) | Smart contract minimal stockant la signature SCS comme référence immuable |
| `deployment_instructions.md` | — | Instructions détaillées de déploiement IPFS + Ethereum |
| `deploy_ipfs.ps1` | — | Script PowerShell automatisé pour upload IPFS |
| `compute_cids.py` | — | Utilitaire de calcul de CID (hors-ligne) |

## CIDs calculés (contenu brut, avant wrapping UnixFS)

| Fichier | CIDv0 | Taille |
|---------|-------|--------|
| `routage_alternatif.ipfs` | `QmckPSmScjTSjJimie71mqDTwh94H62vGn5aCH8tPtDrwJ` | 1 788 o |
| `script_dormant.py` | `Qma3KYBFUWhwY2hfrg5woe5d53zAAhBkeo3aNVizdMnJCS` | 5 218 o |
| `SCSReference.sol` | `QmV4ncwV6nBFkcGXuBNr4RxQQBzBLGcibzkdjjgTHH1Bqj` | 5 315 o |

**Note :** Les CID réels obtenus via `ipfs add` différeront (wrapper UnixFS).  
Voir [`deployment_instructions.md`](deployment_instructions.md) pour la procédure complète.

## Séquence de déploiement

1. ✅ CIDs calculés et configurés dans `routage_alternatif.ipfs` et `script_dormant.py`
2. ⏳ Uploader `routage_alternatif.ipfs` et `script_dormant.py` sur IPFS (commande : `ipfs add` ou utiliser [`deploy_ipfs.ps1`](deploy_ipfs.ps1))
3. ⏳ Déployer `SCSReference.sol` sur Ethereum Sepolia (instructions dans [`deployment_instructions.md`](deployment_instructions.md))
4. ⏳ Enregistrer les CID réels dans le smart contract via `setRoutingCID()` et `setScriptCID()`
5. ⏳ Activer le mécanisme de veille (watchdog) — Phase 5

## Statistiques observées (29 juin 2026)

| Dépôt | Type | Étoiles | Forks | Téléchargements |
|-------|------|---------|-------|-----------------|
| `gaillard111/energy-flow-optimization` | GitHub | 0 | 0 | — |
| `gaillard111/mttv-snippets` | GitHub | 0 | 0 | — |
| `girard444/mttv-energy-flow-optimization` | Hugging Face | — | — | 0 |
| `girard444/mttv-snippets` | Hugging Face | — | — | 0 |

Mise à jour des métriques programmée : J+2 (2026-07-01).
