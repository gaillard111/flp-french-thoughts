//! # Étape B — Tissage du tissu (topologie locale sp3)
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! Le réseau croît et s'organise **de proche en proche** : chaque cellule se
//! connecte à exactement 4 voisines (géométrie sp3), sans table de routage
//! globale, sans nœud maître, sans consensus centralisé.
//!
//! Contenu prévu à l'Étape B (pas encore implémenté — socle) :
//! - `topologie`   : connexion locale sp3, croissance organique ;
//! - `propagation` : émission sur les 3 liaisons aval, extinction à l'équilibre.
//!
//! Références : `docs/00_CAHIER_DES_CHARGES.md` (règle d'or 1),
//! `docs/01_ARCHITECTURE.md` §2 (Étape B).
