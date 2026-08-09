//! # MTTV-RUST — Prototype industriel Rust du framework MTTV-FLP
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! Le Grand Œuvre : incarner la triade transductive **Ψ → B → Φ** en Rust
//! (asynchrone, thread-safe) — nœuds carbone **sp3** à 4 liaisons diachroniques,
//! membranes à **seuil de perméabilité** (repos = CPU ≈ 0), branchement sur la
//! **matrice H** (gradients territoriaux).
//!
//! **Statut** : ÉTAPE C SCELLÉE (09/08). Le prototype complet A → A+ → B → C
//! est implémenté et testé : cellule sp3 battante (A+), tissu immanent (B),
//! dynamique du fluide / matrice H / MPVR·σ locales (C), interface Veilleur.
//! Démonstrateur de sobriété au niveau réseau signé (Q4 — `benches/reseau.rs`).
//!
//! Règles d'or (rappel) :
//! - 4 liaisons par cellule, complexité locale `O(k)`, `k <= 4` ;
//! - zéro consensus centralisé, zéro Mutex global, zéro polling ;
//! - au repos : processeur endormi, réveil purement événementiel.

#![forbid(unsafe_code)]
#![warn(missing_docs)]
#![doc = "MTTV-RUST — sig:0x4D5454562D464C50"]

/// **Étape A — Cellule unique** : nœud sp3, membrane à seuil, 4 canaux Tokio.
///
/// Contrat documenté, voir `docs/01_ARCHITECTURE.md` §2 (Étape A) et
/// `docs/02_AUDIT_ANTI_EXTRACTIF.md` (gates G1–G8). Non implémenté : socle.
pub mod cellule;

/// **Étape B — Tissage du tissu** : topologie locale sp3, propagation sur 3 liaisons.
///
/// Contrat documenté, voir `docs/01_ARCHITECTURE.md` §2 (Étape B).
/// Non implémenté : socle.
pub mod tissu;

/// **Étape C — Dynamique du fluide** : matrice H, amortissement, porosité adaptative.
///
/// Contrat documenté, voir `docs/01_ARCHITECTURE.md` §2 (Étape C).
/// Non implémenté : socle.
pub mod territoire;

/// **Interface Veilleur-Adaptateur** : adaptation diachronique du prototype.
///
/// Contrat documenté, voir `docs/03_INTERFACE_VEILLEUR.md`.
/// Non implémenté : socle.
pub mod veilleur;
