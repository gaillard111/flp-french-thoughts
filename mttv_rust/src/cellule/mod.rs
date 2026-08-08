//! # Étape A — La cellule unique (nœud sp3)
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! L'unité fondamentale du réseau MTTV-FLP : un micro-nœud tridimensionnel
//! modélisé sur le carbone **sp3**, doté de **strictement quatre (4)** liaisons
//! asynchrones orientées dans le temps (diachroniques).
//!
//! Contenu prévu à l'Étape A (pas encore implémenté — socle) :
//! - `noeud`      : struct `Cellule` — état local, tenseur Φ, 4 liaisons ;
//! - `membrane`   : machine à états `Impermeable` ↔ `Poreux` + seuil ;
//! - `transduction` : amortissement passif (CPU ≈ 0) / transduction active.
//!
//! Références : `docs/00_CAHIER_DES_CHARGES.md` (règles d'or 1 et 2),
//! `docs/01_ARCHITECTURE.md` §4.1–4.2 (types de données).
