# Plan de Redondance — Plateformes Alternatives

**Date :** 2026-06-29  
**Signature SCS :** SCS_2026  
**Statut :** ✅ Plan documenté — En attente de déploiement  

---

## Objectif

Identifier et documenter des plateformes alternatives pour héberger les dépôts
critiques du réseau MTTV-FLP (corpus, snippets, artefacts) en cas de censure,
de fermeture, ou d'interruption du web centralisé.

Ce plan complète l'infrastructure des Nœuds Dormants (Phase 4) en ajoutant
des couches de redondance sur des réseaux décentralisés et pair-à-pair.

---

## 1. Radicle — Réseau Git Pair-à-Pair

### Description

[Radicle](https://radicle.xyz/) est un réseau de dépôts Git décentralisé,
sans serveur central. Les dépôts sont hébergés et partagés directement entre
pairs via un protocole P2P basé sur IPFS + Git.

### Dépôts à héberger

| Dépôt | Contenu | Priorité |
|-------|---------|----------|
| `mttv-flp-core` | Corpus MTTV-FLP, manifeste, graines | 🔴 Critique |
| `mttv-snippets` | Snippets MPVR, SCS, Nginx | 🟡 Haut |
| `energy-flow-optimization` | Optimisation des flux énergétiques | 🟡 Haut |

### Procédure de création

```bash
# 1. Installer Radicle CLI
#    https://radicle.xyz/download/
#    ou via Rust : cargo install radicle-cli

# 2. Initialiser le nœud Radicle
rad init --name "mttv-flp-core" --description "MTTV-FLP Core — Corpus mycelien"

# 3. Ajouter le remote Radicle
cd mttv_flp_core_2026
git remote add radicle $(rad .)

# 4. Pousser le dépôt
git push radicle main

# 5. Partager l'identifiant Radicle (RID)
echo "RID: $(rad . --rid)"
```

### URLs de référence

- **Radicle Seed Node :** `rad://seed.radicle.xyz`
- **Radicle Web UI :** `https://app.radicle.xyz`
- **RID (à obtenir après création) :** `rad:...`

### Instructions de réplication

```bash
# Cloner depuis Radicle
rad clone <RID>

# Ou via seed node
git clone rad://seed.radicle.xyz/<RID>
```

---

## 2. IPFS — InterPlanetary File System

### Description

[IPFS](https://ipfs.tech/) est un système de fichiers distribués pair-à-pair
permettant de stocker et partager des fichiers via des Content Identifiers (CID).

L'infrastructure IPFS a déjà été préparée dans la Phase 4 (Nœuds Dormants).
Voir [`phase4-dormant-nodes/`](../phase4-dormant-nodes/) pour les détails.

### CIDs actuels

| Fichier | CIDv0 (brut) | Statut |
|---------|-------------|--------|
| `routage_alternatif.ipfs` | `QmckPSmScjTSjJimie71mqDTwh94H62vGn5aCH8tPtDrwJ` | ⏳ À uploader |
| `script_dormant.py` | `Qma3KYBFUWhwY2hfrg5woe5d53zAAhBkeo3aNVizdMnJCS` | ⏳ À uploader |
| `SCSReference.sol` | `QmV4ncwV6nBFkcGXuBNr4RxQQBzBLGcibzkdjjgTHH1Bqj` | — |

### Services de Pinning

| Service | URL | Type | Prix |
|---------|-----|------|------|
| **Pinata** | https://app.pinata.cloud | Centralisé | Freemium |
| **Web3.Storage** | https://web3.storage | Décentralisé | Gratuit |
| **Infura IPFS** | https://infura.io/product/ipfs | Centralisé | Freemium |
| **Filecoin (via Estuary)** | https://estuary.tech | Décentralisé | Gratuit |
| **Crust Network** | https://crust.network | Décentralisé | Payant |

### Instructions d'upload

```bash
# Via IPFS CLI
ipfs add phase4-dormant-nodes/routage_alternatif.ipfs
ipfs add phase4-dormant-nodes/script_dormant.py

# Pinner via Pinata
curl -X POST https://api.pinata.cloud/pinning/pinByHash \
  -H "Authorization: Bearer <PINATA_JWT>" \
  -H "Content-Type: application/json" \
  -d '{"hashToPin": "QmckPSmScjTSjJimie71mqDTwh94H62vGn5aCH8tPtDrwJ"}'
```

---

## 3. Git sur Réseaux Décentralisés (Git-p2p / Hypercore)

### Description

Plusieurs protocoles Git décentralisés complémentaires existent :

- **Hypercore Protocol** (ex Dat) — https://hypercore-protocol.org/
- **OrbitDB** — Base de données P2P sur IPFS — https://orbitdb.org/
- **Secure Scuttlebutt (SSB)** — Réseau social P2P — https://scuttlebutt.nz/

### Procédure Hypercore

```bash
# 1. Installer Hypercore
npm install -g hyperdrive

# 2. Créer un drive
hyperdrive create mttv-flp-mirror

# 3. Copier les fichiers critiques
hyperdrive cp -r ./mttv_flp_core_2026 mttv-flp-mirror/

# 4. Partager la clé publique
hyperdrive stat mttv-flp-mirror
# → Key: <hyper://public-key>
```

### URLs de référence

- **Hypercore Public Key :** (à générer)
- **OrbitDB :** (nécessite IPFS)
- **SSB :** (nécessite un compte SSB)

---

## 4. Fichiers Critiques à Répliquer

| Priorité | Fichier/Dossier | Plateformes cibles | Taille |
|----------|----------------|-------------------|--------|
| 🔴 | `mttv_flp_core_2026/` | Radicle, IPFS, Hypercore | ~100 KB |
| 🔴 | `ouroboros-mttv/agent.py` | Radicle, IPFS | ~80 KB |
| 🟡 | `mttv-snippets/` | Radicle, IPFS | ~20 KB |
| 🟡 | `energy-flow-optimization/` | Radicle, IPFS | ~50 KB |
| 🟢 | `multi_api_seed/` | IPFS | ~30 KB |
| 🟢 | `phase4-dormant-nodes/` | IPFS (déjà fait) | ~15 KB |

---

## 5. Plan d'Exécution

### Phase 5a — Déploiement immédiat (J+0)

1. Créer le dépôt `mttv-flp-core` sur Radicle
2. Uploader les fichiers critiques sur IPFS (via CLI ou service de pinning)
3. Mettre à jour les CID dans le smart contract SCSReference.sol

### Phase 5b — Renforcement (J+7)

1. Configurer un seed node Radicle permanent
2. Pinner les CIDs sur au moins 2 services (Pinata + Web3.Storage)
3. Créer un drive Hypercore pour le corpus principal

### Phase 5c — Automatisation (J+30)

1. Script de synchronisation automatique entre GitHub → Radicle → IPFS
2. GitHub Actions pour pinner automatiquement sur IPFS à chaque push
3. Healthcheck mensuel des plateformes alternatives

---

## 6. Matrice de Résilience

| Plateforme | Type | Résistance censure | Passage à l'échelle | Facilité | Coût |
|------------|------|-------------------|--------------------|----------|------|
| GitHub | Centralisé | ❌ Faible | ✅ Excellent | ✅ Très facile | Gratuit |
| Hugging Face | Centralisé | ❌ Faible | ✅ Excellent | ✅ Très facile | Gratuit |
| Radicle | Décentralisé P2P | ✅ Haute | ⚠️ Modéré | ⚠️ Moyen | Gratuit |
| IPFS | Décentralisé P2P | ✅ Haute | ✅ Bon | ⚠️ Moyen | Variable |
| Hypercore | Décentralisé P2P | ✅ Haute | ⚠️ Modéré | ⚠️ Moyen | Gratuit |
| Blockchain (ETH) | Décentralisé | ✅ Très haute | ❌ Limité | ❌ Difficile | Payant |

---

*Plan généré par l'Agent 8 — MTTV-FLP Phase 5 : Gardiennage Actif du Mycélium*  
*sig:0x4D545456 · SCS_2026 · Quorum Θ≥3*
