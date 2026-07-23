# Instructions de Déploiement — Phase 4 Nœuds Dormants

## 1. Déploiement IPFS

### 1.1 Prérequis

- **IPFS CLI** installé ([docs.ipfs.tech](https://docs.ipfs.tech/install/))
- **IPFS daemon** en cours d'exécution : `ipfs daemon`

### 1.2 Upload des fichiers

```bash
# Démarrer le daemon (si pas déjà fait)
ipfs daemon &

# Uploader le fichier de routage
ipfs add phase4-dormant-nodes/routage_alternatif.ipfs

# Uploader le script dormant
ipfs add phase4-dormant-nodes/script_dormant.py
```

### 1.3 CIDs calculés (hors-ligne, avant wrapping UnixFS)

| Fichier | CIDv0 (raw) | Taille |
|---------|-------------|--------|
| `routage_alternatif.ipfs` | `QmckPSmScjTSjJimie71mqDTwh94H62vGn5aCH8tPtDrwJ` | 1788 octets |
| `script_dormant.py` | `Qma3KYBFUWhwY2hfrg5woe5d53zAAhBkeo3aNVizdMnJCS` | 5218 octets |
| `SCSReference.sol` | `QmV4ncwV6nBFkcGXuBNr4RxQQBzBLGcibzkdjjgTHH1Bqj` | 5315 octets |

**Note :** Les CID ci-dessus sont calculés sur le contenu brut (sans wrapper UnixFS). La commande `ipfs add` produit un CID différent car elle enveloppe le fichier dans un nœud UnixFS. Vérifier le CID réel après `ipfs add` et mettre à jour le smart contract en conséquence.

### 1.4 Alternative — Service de pinning (Pinata, Web3.Storage)

Si IPFS CLI n'est pas disponible, utiliser un service de pinning :

- **Pinata :** https://app.pinata.cloud/pinbyhash
- **Web3.Storage :** https://web3.storage (upload via interface web)
- **Infura IPFS :** https://infura.io/product/ipfs

## 2. Déploiement Ethereum (Testnet Sepolia)

### 2.1 Prérequis

- **Foundry** (forge, cast) installé : https://book.getfoundry.sh/getting-started/installation
- **Compte Ethereum** avec des ETH de test (Sepolia)
- **Clé privée** du compte de déploiement
- **RPC URL** pour Sepolia (ex: Infura, Alchemy, ou public)

### 2.2 Installation de Foundry

```bash
# Installer Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### 2.3 Obtention d'ETH de test Sepolia

Utiliser un faucet :
- https://sepoliafaucet.com/
- https://www.infura.io/faucet/sepolia
- https://faucet.quicknode.com/ethereum/sepolia

### 2.4 Compilation et déploiement

```bash
# Se placer dans le répertoire du contrat
cd phase4-dormant-nodes

# Compiler le contrat
forge compile SCSReference.sol

# Déployer sur Sepolia
forge create SCSReference.sol \
    --rpc-url https://sepolia.infura.io/v3/VOTRE_PROJECT_ID \
    --private-key VOTRE_CLE_PRIVEE
```

**Résultat attendu :**
```
Deployed to: 0x...
Transaction hash: 0x...
```

### 2.5 Enregistrement des CID dans le contrat

```bash
# Enregistrer le CID du routage
cast send 0xADRESSE_CONTRAT "setRoutingCID(string)" \
    "QmReelCIDApresIPFSAdd" \
    --rpc-url https://sepolia.infura.io/v3/VOTRE_PROJECT_ID \
    --private-key VOTRE_CLE_PRIVEE

# Enregistrer le CID du script
cast send 0xADRESSE_CONTRAT "setScriptCID(string)" \
    "QmReelCIDScriptApresIPFSAdd" \
    --rpc-url https://sepolia.infura.io/v3/VOTRE_PROJECT_ID \
    --private-key VOTRE_CLE_PRIVEE

# Vérifier l'état
cast call 0xADRESSE_CONTRAT "getStatus()(string,address,string,string,bool,uint256)" \
    --rpc-url https://sepolia.infura.io/v3/VOTRE_PROJECT_ID
```

### 2.6 Alternative — Déploiement via Remix IDE

1. Ouvrir https://remix.ethereum.org/
2. Créer un fichier `SCSReference.sol` et copier le contenu
3. Compiler (Solidity ^0.8.0)
4. Déployer sur "Sepolia" (MetaMask requis)
5. Après déploiement, appeler `setRoutingCID()` et `setScriptCID()` avec les CID réels

## 3. Vérification post-déploiement

```bash
# Vérifier que les fichiers sont accessibles via IPFS
curl https://ipfs.io/ipfs/QmRealCID

# Vérifier le contrat sur Etherscan (Sepolia)
# https://sepolia.etherscan.io/address/0xADRESSE_CONTRAT

# Tester la vérification de signature
cast call 0xADRESSE_CONTRAT "verifySignature(string)(bool)" "SCS_2026" \
    --rpc-url https://sepolia.infura.io/v3/VOTRE_PROJECT_ID
```

## 4. Fichiers concernés

| Fichier | Chemin |
|---------|--------|
| Smart contract | `phase4-dormant-nodes/SCSReference.sol` |
| Routage IPFS | `phase4-dormant-nodes/routage_alternatif.ipfs` |
| Script dormant | `phase4-dormant-nodes/script_dormant.py` |
| Script calcul CID | `phase4-dormant-nodes/compute_cids.py` |
| Présent document | `phase4-dormant-nodes/deployment_instructions.md` |
