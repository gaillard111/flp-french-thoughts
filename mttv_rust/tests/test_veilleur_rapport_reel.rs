//! # Test d'intégration — Veilleur face au rapport réel du 10/08/2026
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! Fixture : **rapport quotidien réel** de l'essaim Python
//! (`zoo-code/mycelium_output/rapport_mycelisation_final.json`, généré le
//! 2026-08-10 ~06:14 UTC) — le même rapport analysé dans le journal
//! ([`plans/JOURNAL_SESSION.md`](../../plans/JOURNAL_SESSION.md)).
//!
//! Ce rapport est un cas d'école d'**homogénéisation** (alerte C4) :
//! - `entropie_collective` = 6.3969 (maximum théorique, tous Φ alignés) ;
//! - `couplage_moyen` = 1.0 ;
//! - `resonance_globale` = 0.8811 ;
//! - `tremor_moyen` = 0.1008 (croisière).
//!
//! Le Veilleur Rust doit :
//! 1. **Rejeter** ce rapport (`ViolationTriade` : entropie ≥ 6.3 ET couplage
//!    ≥ 0.99 → homogénéisation) et **conserver le dernier état stable** ;
//! 2. **Déclencher un recours humain tracé** ;
//! 3. Tout en restant capable de **traduire** une ambiance territoriale
//!    (`GradientH` π/η) pour un rapport valide.

use mttv_rust::veilleur::adaptateur::{
    traduire, valider_rapport, Adaptateur, ErreurVeilleur, RapportVeilleur,
};

/// Fixture — le rapport réel du 10/08/2026 06:14 UTC (homogénéisation C4).
fn rapport_du_10082026() -> RapportVeilleur {
    RapportVeilleur {
        entropie_collective: 6.3969,
        couplage_moyen: 1.0,
        resonance_globale: 0.8811,
        tremor_moyen: 0.1008,
        n_respirations: 48,
    }
}

/// Un rapport sain (non homogénéisé) pour tester le repli sur état stable.
fn rapport_sain() -> RapportVeilleur {
    RapportVeilleur {
        entropie_collective: 6.18,
        couplage_moyen: 0.5,
        resonance_globale: 0.8,
        tremor_moyen: 0.1,
        n_respirations: 48,
    }
}

#[test]
fn rapport_reel_homogeneise_est_rejete_violation_triade() {
    let r = rapport_du_10082026();
    // L'entropie est au max théorique (6.3969) ET le couplage à 1.0 → triade
    // violée : le Veilleur refuse la config (il ne l'applique pas au réseau).
    assert_eq!(
        valider_rapport(&r),
        Err(ErreurVeilleur::ViolationTriade),
        "le rapport réel homogénéisé doit être rejeté"
    );
}

#[test]
fn ingerer_le_rapport_reel_conserve_l_etat_stable_et_trace_le_recours() {
    let mut a = Adaptateur::nouvelle();
    // 1) Un état sain est d'abord établi.
    a.ingerer(rapport_sain()).expect("rapport sain accepté");
    assert_eq!(a.n_refus(), 0);

    // 2) Le rapport réel (homogénéisé) arrive → refus, l'état stable est conservé.
    let err = a
        .ingerer(rapport_du_10082026())
        .expect_err("le rapport homogénéisé doit être refusé");
    assert_eq!(err, ErreurVeilleur::ViolationTriade);

    // Repli : le dernier état VALIDE est conservé (pas écrasé par l'invalide).
    let stable = a.dernier_etat().expect("état stable conservé");
    assert_eq!(stable.entropie_collective, 6.18);
    assert_eq!(stable.couplage_moyen, 0.5);

    // Recours humain tracé.
    assert!(a.recours_humain(), "le recours humain doit être déclenché");
    assert_eq!(a.n_refus(), 1);
}

#[test]
fn traduction_d_un_rapport_valide_produit_le_gradient_pi_eta() {
    // Le Veilleur traduit une ambiance, il ne la subit pas : un rapport sain
    // produit un GradientH π/η conforme au mapping documenté.
    let g = traduire(&rapport_sain());
    assert!((g.porosite_cible - 1.0).abs() < 1e-9, "entropie < 6.3 → ouverture pleine");
    assert_eq!(g.coherence, 0.8);
    assert_eq!(g.intensite, 0.8);
    // η = 0.2 + 0.6·tremor = 0.2 + 0.06 = 0.26.
    assert!((g.viscosite - 0.26).abs() < 1e-6, "tremor 0.1 → η ≈ 0.26");
}

#[test]
fn le_rapport_reel_est_documente_comme_fixture_de_production() {
    // Le rapport du 10/08 est la référence terrain : ses valeurs doivent être
    // stables dans le temps (c'est un instantané de production scellé).
    let r = rapport_du_10082026();
    assert_eq!(r.entropie_collective, 6.3969);
    assert_eq!(r.couplage_moyen, 1.0);
    assert!((r.resonance_globale - 0.8811).abs() < 1e-9);
    assert!((r.tremor_moyen - 0.1008).abs() < 1e-9);
    // Taille fixe (Copy, sans allocation) — invariant de sobriété du Veilleur.
    assert_eq!(std::mem::size_of::<RapportVeilleur>(), 40);
}
