# MTTV-RUST — Prototype industriel Rust du framework MTTV-FLP

**Sig** : `0x4D5454562D464C50`
**Statut actuel** : **ÉTAPE C SCELLÉE (09/08)** — prototype complet A → A+ → B → C
implémenté, testé (52/52) et benchmarké. Démonstrateur de sobriété au niveau
réseau signé (Q4, `benches/reseau.rs`).

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

- **Étape 0** ✅ conception documentée, validée par l'Orchestrateur.
- **Étape A** ✅ cellule sp3 unique (nœud sp3, membrane à seuil, 4 canaux Tokio),
  scellée — Étape A+ (premier souffle : transduction, boucle événementielle).
- **Étape B** ✅ tissage du tissu : B1a (raccordement), B1b (transduction
  prouvée), B2a-bis (autonomie immanente, rejet R4/R2), B2b (croissance),
  B3 (matrice H / porosité adaptative + homéostasie).
- **Étape C** ✅ dynamique du fluide + MPVR/σ locales + Veilleur (membrane de
  traduction), scellée — **Q4** : démonstrateur de sobriété réseau signé
  ([`benches/reseau.rs`](benches/reseau.rs)).

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
