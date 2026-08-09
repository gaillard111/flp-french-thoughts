//! # Étape C — Dynamique du fluide (matrice H, territoire)
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! Le réseau ne calcule pas de probabilités hors-sol : il palpe et réagit aux
//! **gradients de son environnement** (matrice H). La porosité des membranes
//! s'ouvre en résonance informationnelle et se contracte jusqu'à
//! l'imperméabilité dans les zones de bruit, d'attaque ou d'incohérence.
//!
//! Contenu prévu à l'Étape C (pas encore implémenté — socle) :
//! - `matrice_h` : gradients H, ajustement dynamique de la porosité ;
//! - règles d'amortissement et de dissipation locales.
//!
//! **`spike`** : SPIKE SACRIFIABLE du protocole « Double Filtre » (phase 2) —
//! épreuve par le réel des verrous Q1/Q2 (GradientH π/η, ingestion pure,
//! repli état stable). À jeter ou intégrer selon l'arbitrage.
//!
//! Références : `docs/00_CAHIER_DES_CHARGES.md` (règle d'or 3),
//! `docs/01_ARCHITECTURE.md` §2 (Étape C) et §4.3.

pub mod spike;
