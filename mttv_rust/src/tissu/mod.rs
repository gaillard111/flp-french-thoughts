//! # Étape B — Tissage du tissu (topologie locale sp3)
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! Le réseau croît et s'organise **de proche en proche** : chaque cellule se
//! connecte à exactement 4 voisines orientées (1 amont + 3 aval, géométrie sp3
//! diachronique), sans table de routage globale, sans nœud maître, sans
//! consensus centralisé.
//!
//! - [`lien`] : B1a — le squelette de raccordement des canaux Tokio
//!   (`brancher` relie une liaison aval d'une cellule à l'amont d'une autre).
//! - `topologie` : B2a — tissu statique minimal (géométrie 4-régulière) puis
//!   B2b — croissance organique (auto-suture) — **à venir**.
//! - `propagation` : B3 — dynamique immanente (anti-Larsen, extinction) — **à venir**.
//!
//! Références : `docs/00_CAHIER_DES_CHARGES.md` (règle d'or 1),
//! `docs/05_PLAN_ETAPE_B.md` (plan B1→B2→B3, clarifications Orchestrateur).

pub mod essai;
pub mod lien;
pub mod propagation;
pub mod topologie;

pub use essai::{
    essai_signal_aligne, essai_signal_orthogonal, essai_sequence_mixte,
    lancer_essais, ResultatEssai,
};
pub use lien::{brancher, ErreurBranchement, TAMPON_LIAISON};
pub use propagation::{
    diversite_tissu, propager, propager_avec_sauts, ResultatPropagation,
    SAUTS_INITIAUX, SEUIL_ALERTE_ENTROPIE,
};
pub use topologie::{CelluleRevenue, Tissu, PROFONDEUR_DEFAUT, TAMPON_TISSU};
