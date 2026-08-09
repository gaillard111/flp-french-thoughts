//! # B1a — Le lien inter-cellules (squelette de raccordement des canaux)
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! Palier B1a : poser le **squelette de raccordement des canaux Tokio** — la
//! primitive qui relie une liaison aval d'une cellule à la liaison amont d'une
//! autre — **sans encore lancer le premier signal d'essai** (qui est B1b).
//!
//! Règle : le branchement est **local et de proche en proche**. Aucune table
//! globale, aucun registre, aucun coordinateur : on câble une cellule à une
//! voisine via un canal `mpsc` borné (capacité 4, backpressure naturelle).
//!
//! Référence : [`05_PLAN_ETAPE_B.md`](../../docs/05_PLAN_ETAPE_B.md) §B1a,
//! clarifications de l'Orchestrateur (points 1, 2, 4).

use tokio::sync::mpsc;

use crate::cellule::{Cellule, N_AVAL};

/// Capacité des canaux de liaison (bornée — sobriété, abandon local au lieu
/// d'une attente bloquante).
pub const TAMPON_LIAISON: usize = 4;

/// Erreur de branchement local.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ErreurBranchement {
    /// L'emplacement aval demandé est hors bornes (doit être < 3).
    EmplacementAvalInvalide(usize),
    /// La cellule cible n'a pas pu recevoir la nouvelle liaison amont.
    CibleSansAmont,
}

/// Raccorde la liaison aval `slot` de `source` à la liaison amont de `cible`.
///
/// Opération **purement locale et structurelle** :
/// 1. crée un canal `mpsc` borné ;
/// 2. injecte l'émetteur dans l'emplacement aval `slot` de `source` ;
/// 3. injecte le récepteur dans l'amont de `cible`.
///
/// Aucun signal n'est envoyé ici (B1a) : on pose le raccordement. La
/// propagation sémantique viendra à B1b.
///
/// Retourne `Ok(())` si le raccordement est posé, sinon l'erreur locale.
pub fn brancher(
    source: &mut Cellule,
    cible: &mut Cellule,
    slot: usize,
) -> Result<(), ErreurBranchement> {
    if slot >= N_AVAL {
        return Err(ErreurBranchement::EmplacementAvalInvalide(slot));
    }

    let (tx, rx) = mpsc::channel(TAMPON_LIAISON);

    if !source.remplacer_aval(slot, tx) {
        return Err(ErreurBranchement::EmplacementAvalInvalide(slot));
    }
    if !cible.remplacer_amont(rx) {
        return Err(ErreurBranchement::CibleSansAmont);
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cellule::SignaturePhi;

    fn cellule(id: u64) -> Cellule {
        Cellule::nouvelle(id, SignaturePhi::new([1.0, 0.0, 0.0, 0.0]), 0.35).0
    }

    #[test]
    fn branchement_pose_le_lien_local() {
        let mut a = cellule(1);
        let mut b = cellule(2);

        let avant_aval_a = a.liaisons_aval().len();
        assert_eq!(avant_aval_a, N_AVAL);

        assert_eq!(brancher(&mut a, &mut b, 0), Ok(()));
        // La source conserve ses 3 liaisons aval (une a été re-câblée).
        assert_eq!(a.liaisons_aval().len(), N_AVAL);
    }

    #[test]
    fn branchement_rejette_slot_hors_bornes() {
        let mut a = cellule(1);
        let mut b = cellule(2);
        let erreur = brancher(&mut a, &mut b, 3).unwrap_err();
        assert_eq!(erreur, ErreurBranchement::EmplacementAvalInvalide(3));
    }

    #[test]
    fn deux_cellules_cablees_reste_structure_sp3() {
        let mut a = cellule(1);
        let mut b = cellule(2);
        assert_eq!(brancher(&mut a, &mut b, 1), Ok(()));

        // Chaque cellule garde 4 canaux : 1 amont + 3 aval (géométrie sp3).
        assert_eq!(a.liaisons_aval().len(), N_AVAL);
        assert_eq!(b.liaisons_aval().len(), N_AVAL);
    }

    #[test]
    fn la_cible_a_bien_un_amont_apres_branchement() {
        let mut a = cellule(1);
        let mut b = cellule(2);
        assert_eq!(brancher(&mut a, &mut b, 2), Ok(()));
        // L'amont de la cible a été remplacé par le récepteur injecté :
        // la cellule peut maintenant recevoir (B1b le testera sémantiquement).
        assert_eq!(a.liaisons_aval().len(), 3);
        assert_eq!(b.liaisons_aval().len(), 3);
    }
}
