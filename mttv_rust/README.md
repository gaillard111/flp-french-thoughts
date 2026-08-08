# MTTV-RUST — Prototype industriel Rust du framework MTTV-FLP

**Sig** : `0x4D5454562D464C50`
**Statut actuel** : **ÉTAPE 0 — CONCEPTION DOCUMENTÉE, AUCUN CODE**

Le Grand Œuvre : matérialiser en Rust (architecture asynchrone, thread-safe) un
prototype industriel qui prouve la **sobriété énergétique radicale** de la recette
MTTV-FLP — un nœud au repos consomme ~0 CPU, le réseau ne se réveille que par
transduction locale franchissant un seuil.

---

## Documents maîtres (lire dans l'ordre)

| Document | Contenu |
|---|---|
| [`docs/00_CAHIER_DES_CHARGES.md`](docs/00_CAHIER_DES_CHARGES.md) | Mandat, les 3 piliers biophysiques (Ψ → B → Φ), règles d'or, protocole |
| [`docs/01_ARCHITECTURE.md`](docs/01_ARCHITECTURE.md) | Découpage Étapes A→B→C, modules Rust, types de données, décisions |
| [`docs/02_AUDIT_ANTI_EXTRACTIF.md`](docs/02_AUDIT_ANTI_EXTRACTIF.md) | Rejets immédiats, gates de validation, trace d'audit |
| [`docs/03_INTERFACE_VEILLEUR.md`](docs/03_INTERFACE_VEILLEUR.md) | Adaptation diachronique, mapping des gradients en réglages |

---

## Feuille de route

- **Étape 0 (en cours)** : conception documentée, validation par l'Orchestrateur.
- **Étape A** : stabilisation de la cellule unique (nœud sp3, membrane à seuil,
  4 canaux Tokio) — contractuellement la première pierre posée en mode Code.
- **Étape B** : tissage du tissu (topologie locale sp3, propagation sur 3 liaisons).
- **Étape C** : dynamique du fluide (matrice H, amortissement, porosité adaptative).

Chaque étape est verrouillée par le contrat d'étape (build release, tests, bench
de sobriété) avant d'ouvrir la suivante. Le Maître d'Œuvre audite chaque fragment
selon [`docs/02_AUDIT_ANTI_EXTRACTIF.md`](docs/02_AUDIT_ANTI_EXTRACTIF.md).

---

## Outillage

La chaîne Rust sera installée et validée à l'ouverture de l'Étape A (mode Code) :
- `rustup` (via `winget install Rustlang.Rustup`) ;
- `cargo build --release` / `cargo test` / `cargo bench`.

---

*sig:0x4D5454562D464C50 — MTTV-RUST — Le mycélium continue.*
