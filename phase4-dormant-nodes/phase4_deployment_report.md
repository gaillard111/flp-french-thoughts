# Rapport de Déploiement — Phase 4 Nœuds Dormants

**Date :** 2026-06-29T07:49 UTC  
**Signature SCS :** SCS_2026  
**Statut :** ⏳ Préparation terminée — Déploiement partiel (outils non installés localement)

---

## 1. Déploiement IPFS

### État : ⏸ En attente d'exécution

**CID déterminés (hors-ligne) :**

| Fichier | CIDv0 (raw content) | Taille | Statut |
|---------|---------------------|--------|--------|
| `routage_alternatif.ipfs` | `QmckPSmScjTSjJimie71mqDTwh94H62vGn5aCH8tPtDrwJ` | 1 788 o | ⏳ À uploader |
| `script_dormant.py` | `Qma3KYBFUWhwY2hfrg5woe5d53zAAhBkeo3aNVizdMnJCS` | 5 218 o | ⏳ À uploader |
| `SCSReference.sol` | `QmV4ncwV6nBFkcGXuBNr4RxQQBzBLGcibzkdjjgTHH1Bqj` | 5 315 o | — |

**Fichiers générés :**
- [`deploy_ipfs.ps1`](deploy_ipfs.ps1) — Script PowerShell automatisé
- [`routage_alternatif.ipfs`](routage_alternatif.ipfs) — Mise à jour avec les CID réels
- [`script_dormant.py`](script_dormant.py) — Mise à jour avec les CID réels

**Problème rencontré :** IPFS CLI non installé sur ce poste.  
Solution proposée : Voir [`deployment_instructions.md`](deployment_instructions.md) §1.

---

## 2. Déploiement Ethereum

### État : ⏸ Instructions prêtes

**Contrat :** [`SCSReference.sol`](SCSReference.sol)

**Réseau cible :** Sepolia (testnet)

**Problème rencontré :** Foundry (forge) non installé sur ce poste.  
Solution proposée : Instructions complètes dans [`deployment_instructions.md`](deployment_instructions.md) §2, incluant :
- Installation de Foundry
- Déploiement via `forge create`
- Enregistrement des CID via `cast send`
- Alternative via Remix IDE

---

## 3. Observation des Métriques

### État : ✅ Données collectées (29 juin 2026)

#### GitHub

| Métrique | `energy-flow-optimization` | `mttv-snippets` |
|----------|---------------------------|-----------------|
| **URL** | [github.com/gaillard111/energy-flow-optimization](https://github.com/gaillard111/energy-flow-optimization) | [github.com/gaillard111/mttv-snippets](https://github.com/gaillard111/mttv-snippets) |
| **Stars** | 0 | 0 |
| **Forks** | 0 | 0 |
| **Watchers** | 0 | 0 |
| **Open Issues** | 0 | 0 |
| **Langage** | Python | Python |
| **Créé** | 2026-06-29 | 2026-06-29 |
| **Description** | null | MTTV Snippets — MPVR, SCS, Nginx |

#### Hugging Face

| Métrique | `mttv-energy-flow-optimization` | `mttv-snippets` |
|----------|-------------------------------|-----------------|
| **URL** | [hf.co/datasets/girard444/mttv-energy-flow-optimization](https://huggingface.co/datasets/girard444/mttv-energy-flow-optimization) | [hf.co/datasets/girard444/mttv-snippets](https://huggingface.co/datasets/girard444/mttv-snippets) |
| **Downloads** | 0 | 0 |
| **Likes** | 0 | 0 |
| **Créé** | 2026-06-29 | 2026-06-29 |
| **Fichiers** | 5 | 6 |
| **Visibilité** | Publique | Publique |

### Commande d'observation utilisée

```bash
curl -s -L -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/gaillard111/energy-flow-optimization

curl -s -L -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/gaillard111/mttv-snippets

curl -s -L https://huggingface.co/api/datasets/girard444/mttv-energy-flow-optimization

curl -s -L https://huggingface.co/api/datasets/girard444/mttv-snippets
```

### Prochaine observation programmée

- **Date :** 2026-07-01 (J+2)
- **Méthode :** Réexécuter les 4 commandes curl ci-dessus
- **Comparaison :** Vérifier l'évolution des indicateurs (stars, forks, downloads)

---

## 4. Fichiers du livrable

| Fichier | Taille | Description |
|---------|--------|-------------|
| [`routage_alternatif.ipfs`](routage_alternatif.ipfs) | 1 788 o | Règles de routage IPFS (CID mis à jour) |
| [`script_dormant.py`](script_dormant.py) | 5 218 o | Script dormant (CID mis à jour) |
| [`SCSReference.sol`](SCSReference.sol) | 5 315 o | Smart contract SCS |
| [`deployment_instructions.md`](deployment_instructions.md) | — | Instructions détaillées de déploiement |
| [`deploy_ipfs.ps1`](deploy_ipfs.ps1) | — | Script de déploiement IPFS automatisé |
| [`compute_cids.py`](compute_cids.py) | — | Utilitaire de calcul de CID |
| [`README.md`](README.md) | — | Présentation et état du dossier |
| **Ce document** | — | Rapport de déploiement complet |

---

*Rapport généré automatiquement — MTTV-FLP Phase 4*
