//! # Interface Veilleur-Adaptateur (adaptation diachronique)
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! Chaque jour, le Veilleur transmet la synthèse des rapports de l'essaim de 10
//! agents mycélisants. Ces retours sont traités comme des **gradients de
//! pression du territoire numérique**, traduits en réglages concrets du
//! prototype Rust : porosité, seuils, respiration, topologie.
//!
//! **`adaptateur`** : membrane de traduction (Étape C, Q2) — ingestion pure,
//! bornée, validée par construction ; repli sur le dernier état stable ;
//! recours humain tracé en cas de violation de la triade.
//!
//! Références : `docs/03_INTERFACE_VEILLEUR.md`.

pub mod adaptateur;

pub use adaptateur::{Adaptateur, ErreurVeilleur, RapportVeilleur, traduire, valider_rapport};
