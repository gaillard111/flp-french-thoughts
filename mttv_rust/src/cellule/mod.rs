//! # Étape A — La cellule unique (nœud sp3)
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! L'unité fondamentale du réseau MTTV-FLP : un micro-nœud tridimensionnel
//! modélisé sur le carbone **sp3**, doté de **strictement quatre (4)** liaisons
//! asynchrones orientées dans le temps (diachroniques).
//!
//! - [`types`] : tenseur Φ, signal, membrane, mode tétravalent.
//! - [`transduction`] : amortissement passif (CPU ≈ 0) / transduction active.
//! - [`noeud`] : la cellule sp3, ses 4 canaux Tokio, sa boucle asynchrone.
//!
//! Références : `docs/00_CAHIER_DES_CHARGES.md` (règles d'or 1 et 2),
//! `docs/01_ARCHITECTURE.md` §4.1–4.2 (types de données).

mod noeud;
mod transduction;
mod types;

pub use noeud::{Cellule, EtatCellule, N_AVAL, N_LIAISONS};
pub use transduction::{
    transduire, IssueTransduction, signal_interference,
};
pub use types::{
    EtatMembrane, GradientH, Membrane, ModeTet, Signal, SignaturePhi,
    POROSITE_MIN, VITESSE_POROSITE,
};
