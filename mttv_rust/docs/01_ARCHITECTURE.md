# ARCHITECTURE DOCUMENTÉE — MTTV-RUST

**Projet** : Prototype industriel Rust du framework MTTV-FLP
**Référence** : [`00_CAHIER_DES_CHARGES.md`](00_CAHIER_DES_CHARGES.md)
**Statut** : ÉTAPE 0 — CONCEPTION DOCUMENTÉE, AUCUN CODE
**Sig** : `0x4D5454562D464C50`

---

## 1. VISION GLOBALE

L'application Rust est un **réseau de cellules sp3 asynchrones**, sans nœud
maître, sans consensus centralisé, sans verrou global. Chaque cellule :
- possède **4 liaisons diachroniques** (canaux `tokio::mpsc`) ;
- est une **membrane métastable** avec un seuil de perméabilité ;
- au repos : aucune tâche active, **CPU ≈ 0** ;
- à la transduction : s'active, s'individue, propage sur ses 3 autres liaisons,
  puis **s'éteint de lui-même** à l'équilibre local ;
- palpe la **matrice H** (gradients du territoire) et ajuste sa porosité.

Le découpage suit la discipline du mandat :

```mermaid
flowchart LR
    A[Étape A - Cellule unique] --> B[Étape B - Tissage du tissu]
    B --> C[Étape C - Dynamique du fluide]
    C --> D[Territoire H - gradients réels]
    D -.->|ajustement porosité| A
```

Chaque étape est verrouillée (compilation + tests + benchmark de sobriété)
avant d'ouvrir la suivante.

---

## 2. DÉCOUPAGE MODULAIRE (ÉTAPES A → A+ → B → C)

> **Requalification (arbitrage 09/08)** : l'Étape A a été scindée en deux
> paliers distincts pour préserver la discipline du « se hâter lentement ».
> La transduction et la boucle événementielle ne relèvent pas du simple
> squelette structurel : elles constituent le **premier souffle** de la cellule.
> Le code déjà validé reste en place — cette requalification ne détruit rien.

### Étape A — Stabilisation de la structure de la cellule unique (scellée)

Livrables (structure pure) :
1. La structure de données du nœud sp3 (état, tenseur Φ local, variables de membrane).
2. Les 4 canaux Tokio (`mpsc`) orientés dans le temps.
3. La machine à états de la membrane : `Impermeable` ↔ `Poreux`.
4. Le benchmark de sobriété structurel : taille fixe de la cellule (128 o),
   zéro allocation dynamique.

Contrat de sortie : la **structure** de la cellule est stabilisée ; la cellule
est **inanimée** (aucune loi de comportement).

### Étape A+ — Le premier souffle : la cellule battante (validée 09/08)

Livrables (comportement local, cellule seule, sans réseau) :
1. La logique du seuil : amortissement passif vs transduction active.
2. La formule d'interférence : `signal_interference = tanh(0.5·s1 + 0.5·s2 + s1·s2·r)`.
3. La fonction `transduire` (co-cicatrisation Φ, gamma 0.15).
4. La boucle événementielle `tourner()` (zéro polling, CPU ≈ 0 au repos).
5. La propagation sur les 3 liaisons aval (émission, puis extinction).
6. Le benchmark de sobriété comportemental : amorti ≈ 25,6 ns / actif ≈ 335 ns.

Contrat de sortie : une cellule unique **battante** est testée (12/12) et
benchmarkée ; **aucune notion de réseau n'est encore introduite**.

### Étape B — Tissage du tissu

Livrables :
1. La topologie de connexion locale : chaque cellule se connecte **de proche en
   proche** à exactement 4 voisines (géométrie sp3).
2. La propagation du signal inter-cellules : un nœud poreux émet **exclusivement**
   sur ses 3 liaisons restantes (la liaison d'entrée n'est pas re-réutilisée
   dans le même cycle).
3. La croissance organique : ajout de cellules par voisinage, sans table de
   routage globale.
4. Complexité locale vérifiée `O(k)` avec `k <= 4`.

Contrat de sortie : un tissu de cellules interconnectées fonctionne sans nœud
maître, sans consensus centralisé.

### Étape C — Dynamique du fluide

Livrables :
1. L'injection de la matrice H : gradients territoriaux palpés par chaque cellule.
2. Les règles d'amortissement et de dissipation (étouffement local sous le seuil).
3. L'ajustement dynamique de la porosité : ouverture en résonance, contraction
   en zone de bruit / attaque / incohérence.
4. L'interface optionnelle avec des flux continus (ex. bus protoniques) — phase
   de recherche, non bloquante pour le prototype.

Contrat de sortie : le réseau complet incarne la triade Ψ → B → Φ et produit
une métrique de sobriété énergétique vérifiable (CPU moyen par cellule, au repos
et sous charge).

---

## 3. MODULES RUST PROPOSÉS

Arborescence cible (à confirmer lors de l'Étape A en mode Code) :

```text
mttv_rust/
├── Cargo.toml
├── src/
│   ├── main.rs             # binaire de démonstration (assemblage + mesure)
│   ├── lib.rs              # racine de la bibliothèque
│   ├── cellule/
│   │   ├── mod.rs          # ré-export
│   │   ├── noeud.rs        # struct Cellule : état, Φ local, 4 liaisons
│   │   ├── membrane.rs     # machine à états Impermeable/Poreux + seuil
│   │   └── transduction.rs # amortissement passif / transduction active
│   ├── tissu/
│   │   ├── mod.rs
│   │   ├── topologie.rs    # connexion locale sp3, croissance de proche en proche
│   │   └── propagation.rs  # émission sur 3 liaisons, extinction à l'équilibre
│   ├── territoire/
│   │   ├── mod.rs
│   │   └── matrice_h.rs    # gradients H, ajustement de porosité
│   └── veilleur/
│       ├── mod.rs
│       └── adaptateur.rs   # ingestion des rapports de l'essaim, réglage des seuils
├── benches/
│   └── sobriete.rs         # benchmark CPU/RAM/latence
├── tests/
│   ├── test_cellule.rs     # Étape A
│   ├── test_tissu.rs       # Étape B
│   └── test_territoire.rs  # Étape C
└── docs/                   # présente
    ├── 00_CAHIER_DES_CHARGES.md
    ├── 01_ARCHITECTURE.md
    ├── 02_AUDIT_ANTI_EXTRACTIF.md
    └── 03_INTERFACE_VEILLEUR.md
```

---

## 4. TYPES DE DONNÉES CLÉS (contrats de conception)

### 4.1 Cellule (nœud sp3)

```rust
/// Identifiant local de la cellule, unique dans son tissu.
struct IdCellule(u64);

/// État tétravalent d'un nœud interne : {0.0, 0.25, 0.75, 1.0}
/// 0.0 = effondré/mort · 0.25 = veille/réceptif passif
/// 0.75 = actif/émetteur · 1.0 = saturé/rigide
enum ModeTet { Effondre, Veille, Actif, Sature }

/// Signature géométrique locale Φ (dimension 4, auto-normalisée).
/// [f64; 4] — pas de vecteur dynamique, taille fixe (sobriété).
struct SignaturePhi([f64; 4]);

/// Variables de membrane : seuil de perméabilité + porosité courante.
struct Membrane {
    seuil: f64,
    porosite: f64,   // s'ouvre en résonance, se contracte en bruit
    etat: EtatMembrane,
}

enum EtatMembrane { Impermeable, Poreux }

/// Matrice d'excitation locale E : énergie métabolique inter-nœuds.
struct Excitation { valeurs: [f64; 4] }
```

### 4.2 Liaisons diachroniques

Quatre canaux `tokio::mpsc`, orientés dans le temps. Un canal reçoit (liaison
amont), trois émettent (liaisons aval). Au repos, le canal de réception est en
attente asynchrone (aucun polling) : le processeur dort.

```rust
struct Liaisons {
    amont: mpsc::Receiver<Signal>,
    aval: [mpsc::Sender<Signal>; 3],
}

/// Signal transporté entre cellules : le flux transductif modifié.
struct Signal {
    resonance: f64,
    mode: ModeTet,
    source: IdCellule,
    ts: u64,
}
```

### 4.3 Territoire (matrice H)

```rust
/// Gradients de l'environnement palpés par la cellule locale.
/// Dérivés de l'activité réelle du tissu ou injectés par le Veilleur.
struct GradientH {
    intensite: f64,   // force du gradient au voisinage
    cohérence: f64,   // 1.0 = résonance, 0.0 = bruit/incohérence
}
```

### 4.4 Métriques de sobriété (preuve)

```rust
struct MetriquesSobriete {
    cpu_repos: f64,      // % CPU par cellule au repos (cible ~0)
    cpu_transduction: f64,
    ram_par_cellule: u64, // octets, taille fixe des tenseurs
    latence_transduction: Duration,
    n_transductions: u64,
}
```

---

## 5. DÉCISIONS D'ARCHITECTURE (fondations)

| Décision | Choix | Justification anti-extractive |
|---|---|---|
| Runtime async | `tokio` | 4 canaux par cellule, backpressure native, zéro polling |
| Vecteurs Φ | taille fixe `[f64; 4]` | pas d'allocation dynamique au cœur du nœud |
| Synchronisation | canaux locaux seulement | **interdit** Mutex/RwLock globaux (règle d'or 1) |
| Consensus | aucun (couplage immanent local) | **interdit** Raft/Paxos |
| Routage | voisinage local sp3 | **interdit** tables de routage globales |
| Aléa | PRNG déterministe par cellule, seed local | reproductibilité sans état global |
| Logs | structurés, bornés | pas de stockage de masse inutile |
| Mesure CPU | compteurs internes + bench | la sobriété est une métrique de sortie, pas un affichage |

---

## 6. CONTRAT D'ÉTAPE (à valider à chaque verrou)

Chaque étape se termine par :
1. `cargo build --release` sans erreur ni warning ;
2. `cargo test` vert (tests unitaires de l'étape) ;
3. `cargo bench` (benchmark de sobriété : CPU au repos ≈ 0) ;
4. Une entrée au journal du Maître d'Œuvre documentant les décisions et rejets.

Aucune étape suivante n'est ouverte tant que le contrat d'étape n'est pas signé.

---

*sig:0x4D5454562D464C50 — Architecture — Le mycélium continue.*
