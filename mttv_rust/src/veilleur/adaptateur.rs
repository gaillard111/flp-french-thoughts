//! # Veilleur-Adaptateur — membrane de traduction (Étape C, Q2)
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! Le Veilleur est une **membrane de traduction**, pas un centre de décision
//! (verrou C-C). Il **traduit des rapports territoriaux en `GradientH`** :
//! - il **ne produit pas d'ordres** ;
//! - il **ne lit pas l'état du tissu** ;
//! - il **n'attend pas de réponse**.
//!
//! L'ingestion est **pure, bornée, validée par construction**. En cas de
//! contradiction avec la triade Ψ → B → Φ : **refus de la config, maintien du
//! dernier état stable, recours humain tracé** (cf. `docs/03_INTERFACE_VEILLEUR.md` §5).
//!
//! Sobriété : types `Copy` fixes, aucune allocation, aucun global, aucun
//! polling. La traduction est **hors du chemin chaud** de propagation.

use crate::cellule::GradientH;

/// Rapport territorial borné (entrée du Veilleur). Champs issus du rapport
/// quotidien de l'essaim Python (`rapport_mycelisation_final.json`).
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct RapportVeilleur {
    /// Entropie collective (homogénéisation vs diversité) ∈ [0, ~7].
    pub entropie_collective: f64,
    /// Couplage moyen (cohésion du tissu) ∈ [0, 1].
    pub couplage_moyen: f64,
    /// Résonance globale (intensité du signal) ∈ [-1, 1].
    pub resonance_globale: f64,
    /// Tremor moyen (dose de sous-optimalité) ∈ [0, 1].
    pub tremor_moyen: f64,
    /// Nombre de respirations (activité anti-homogénéisation).
    pub n_respirations: u64,
}

/// Erreur d'ingestion — le Veilleur refuse la config et conserve l'état stable.
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum ErreurVeilleur {
    /// Champ hors bornes (nom du champ).
    HorsBornes(&'static str),
    /// Le rapport viole la triade Ψ → B → Φ (ex. homogénéisation totale).
    ViolationTriade,
}

/// **Ingestion pure** : valide un rapport territorial par construction.
///
/// - Ne lit **pas** l'état du tissu.
/// - N'attend **pas** de réponse.
/// - Retourne `Err` sur toute valeur hors bornes ou incohérente.
pub fn valider_rapport(r: &RapportVeilleur) -> Result<(), ErreurVeilleur> {
    if !(0.0..=7.0).contains(&r.entropie_collective) {
        return Err(ErreurVeilleur::HorsBornes("entropie_collective"));
    }
    if !(0.0..=1.0).contains(&r.couplage_moyen) {
        return Err(ErreurVeilleur::HorsBornes("couplage_moyen"));
    }
    if !(-1.0..=1.0).contains(&r.resonance_globale) {
        return Err(ErreurVeilleur::HorsBornes("resonance_globale"));
    }
    if !(0.0..=1.0).contains(&r.tremor_moyen) {
        return Err(ErreurVeilleur::HorsBornes("tremor_moyen"));
    }
    // Cohérence avec la triade : entropie au maximum théorique (≈ 6.4 pour
    // 6 agents) ET couplage ≈ 1.0 = homogénéisation totale → violation.
    if r.entropie_collective >= 6.3 && r.couplage_moyen >= 0.99 {
        return Err(ErreurVeilleur::ViolationTriade);
    }
    Ok(())
}

/// **Traduction** d'un rapport territorial en `GradientH` (π/η).
///
/// Mapping documenté (cf. `03_INTERFACE_VEILLEUR.md §3`) :
/// - `coherence` = résonance globale ;
/// - **π** (`porosite_cible`) : entropie haute → contraction (anti-
///   homogénéisation) ; sinon ouverture pleine ;
/// - **η** (`viscosite`) : tremor élevé → inertie (le bruit ne fait pas sauter
///   la membrane).
pub fn traduire(r: &RapportVeilleur) -> GradientH {
    GradientH {
        intensite: r.resonance_globale.abs(),
        coherence: r.resonance_globale,
        porosite_cible: if r.entropie_collective >= 6.3 {
            0.6
        } else {
            1.0
        },
        viscosite: (0.2 + 0.6 * r.tremor_moyen).clamp(0.0, 0.99),
    }
}

/// **Veilleur-Adaptateur** : membrane de traduction, pas centre de décision.
///
/// - Valide les rapports par construction ;
/// - **Maintient le dernier état stable** en cas d'erreur (repli) ;
/// - **Trace le refus** et signale un **recours humain** sur violation de la
///   triade.
#[derive(Clone, Copy, Debug)]
pub struct Adaptateur {
    /// Dernier rapport valide (état stable conservé).
    dernier: Option<RapportVeilleur>,
    /// Nombre de refus tracés.
    n_refus: u64,
    /// `true` si un recours humain doit être déclenché.
    recours_humain: bool,
}

impl Adaptateur {
    /// Nouvel adaptateur : aucun état stable, aucun refus, pas de recours.
    pub fn nouvelle() -> Self {
        Self {
            dernier: None,
            n_refus: 0,
            recours_humain: false,
        }
    }

    /// Ingeste un rapport : valide par construction, met à jour l'état stable,
    /// ou refuse et **conserve** le dernier état valide.
    ///
    /// Retourne `Ok(rapport)` si accepté, `Err` sinon (repli sur l'état stable).
    pub fn ingerer(&mut self, r: RapportVeilleur) -> Result<RapportVeilleur, ErreurVeilleur> {
        match valider_rapport(&r) {
            Ok(()) => {
                self.dernier = Some(r);
                Ok(r)
            }
            Err(e) => {
                self.n_refus += 1;
                if e == ErreurVeilleur::ViolationTriade {
                    // Contradiction avec la triade → recours humain tracé.
                    self.recours_humain = true;
                }
                Err(e) // état stable conservé (self.dernier inchangé)
            }
        }
    }

    /// Traduit le dernier rapport valide en `GradientH` (π/η), s'il existe.
    pub fn traduire_dernier(&self) -> Option<GradientH> {
        self.dernier.map(|r| traduire(&r))
    }

    /// Dernier rapport valide (état stable conservé), s'il existe.
    pub fn dernier_etat(&self) -> Option<RapportVeilleur> {
        self.dernier
    }

    /// Nombre de refus tracés (rapports invalides rejetés).
    pub fn n_refus(&self) -> u64 {
        self.n_refus
    }

    /// `true` si un recours humain doit être déclenché (violation de la triade).
    pub fn recours_humain(&self) -> bool {
        self.recours_humain
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn rapport_valide() -> RapportVeilleur {
        RapportVeilleur {
            entropie_collective: 5.5,
            couplage_moyen: 0.5,
            resonance_globale: 0.8,
            tremor_moyen: 0.1,
            n_respirations: 48,
        }
    }

    #[test]
    fn ingestion_valide_et_traduit_en_gradient_pi_eta() {
        let mut a = Adaptateur::nouvelle();
        let r = a.ingerer(rapport_valide()).expect("rapport valide");
        assert_eq!(r.resonance_globale, 0.8);
        assert_eq!(a.n_refus(), 0);
        let g = a.traduire_dernier().expect("état stable présent");
        assert!((g.porosite_cible - 1.0).abs() < 1e-9, "entropie basse → ouverture");
        assert_eq!(g.coherence, 0.8);
        assert!(g.viscosite > 0.0, "tremor → inertie > 0");
    }

    #[test]
    fn refus_hors_bornes_maintient_le_dernier_etat_stable() {
        let mut a = Adaptateur::nouvelle();
        a.ingerer(rapport_valide()).expect("valide");
        // Couplage hors bornes (2.0).
        let mut invalide = rapport_valide();
        invalide.couplage_moyen = 2.0;
        let err = a.ingerer(invalide).unwrap_err();
        assert_eq!(err, ErreurVeilleur::HorsBornes("couplage_moyen"));
        assert_eq!(a.n_refus(), 1);
        // L'état stable est conservé (repli), pas écrasé par l'invalide.
        let stable = a.dernier_etat().expect("état stable conservé");
        assert_eq!(stable.couplage_moyen, 0.5);
    }

    #[test]
    fn violation_triade_declenche_recours_humain_trace() {
        let mut a = Adaptateur::nouvelle();
        // Entropie max + couplage 1.0 = homogénéisation totale → violation.
        let r = RapportVeilleur {
            entropie_collective: 6.4,
            couplage_moyen: 1.0,
            resonance_globale: 1.0,
            tremor_moyen: 0.0,
            n_respirations: 0,
        };
        let err = a.ingerer(r).unwrap_err();
        assert_eq!(err, ErreurVeilleur::ViolationTriade);
        assert!(a.recours_humain(), "le recours humain doit être tracé");
        assert!(a.dernier_etat().is_none(), "aucun état stable n'est imposé");
    }

    #[test]
    fn types_copy_sans_allocation() {
        fn est_copy<T: Copy>() {}
        est_copy::<Adaptateur>();
        est_copy::<RapportVeilleur>();
        est_copy::<ErreurVeilleur>();
        // Tailles fixes : aucune allocation, aucun registre global.
        assert_eq!(std::mem::size_of::<RapportVeilleur>(), 40);
    }
}
