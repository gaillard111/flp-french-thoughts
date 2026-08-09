//! # SPIKE (sacrifiable) — Épreuve de l'Étape C, verrous Q1/Q2
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! Ce fichier est une **épreuve**, pas l'implémentation de l'Étape C. Il est
//! jetable. Son but (protocole « Double Filtre », phase 2) : **prouver par le
//! réel** que la spécification Q1/Q2 tient debout sans violer les verrous
//! C-A→C-D ni R2/R4.
//!
//! Ce qui est prouvé ici :
//! - **Q1** : un `GradientH` local étendu au couple **π/η** (porosité π =
//!   ouverture au flux ; viscosité η = inertie/amortissement), une membrane
//!   locale qui **métabolise** le gradient — sans table globale, sans polling,
//!   sans allocation dans le chemin critique (types `Copy` fixes).
//! - **Q2** : une **ingestion pure** (parse + bornes), un **repli automatique
//!   sur le dernier état stable**, un **refus tracé** et un recours humain
//!   documenté — sans lecture de l'état du tissu, sans attente de réponse.
//!
//! Critères de preuve (tests) : bornes π/η sur 10 000 cycles sans divergence,
//! contraction locale en bruit, réouverture locale après résonance, pas de
//! panique, pas de dépendance à un état global, drop propre.

use crate::cellule::POROSITE_MIN;

/// GradientH étendu au couple π/η (Q1) — **local**, jamais un registre.
#[derive(Clone, Copy, Debug)]
pub struct GradientH {
    /// Intensité du flux territorial.
    pub intensite: f64,
    /// Cohérence ∈ [-1, 1] (résonance / bruit).
    pub coherence: f64,
    /// **π** — porosité cible (ouverture au flux, réceptivité).
    pub porosite_cible: f64,
    /// **η** — viscosité / inertie (volant d'amortissement, rétention).
    pub viscosite: f64,
}

impl GradientH {
    /// Gradient minimal à partir d'une cohérence observée (π=1, η par défaut).
    pub fn nouvelle(coherence: f64) -> Self {
        Self {
            intensite: coherence.abs(),
            coherence,
            porosite_cible: 1.0,
            viscosite: 0.2,
        }
    }
}

/// Membrane locale π/η (Q1) — réception événementielle, sans boucle active.
#[derive(Clone, Copy, Debug)]
pub struct MembranePiEta {
    /// Seuil de perméabilité (référence : 0.35).
    pub seuil: f64,
    /// Porosité courante ∈ [POROSITE_MIN, 1].
    pub porosite: f64,
}

impl MembranePiEta {
    /// Nouvelle membrane, porosité initiale 1.0 (ouverte).
    pub fn nouvelle(seuil: f64) -> Self {
        Self {
            seuil,
            porosite: 1.0,
        }
    }

    /// **Métabolise un gradient territorial** : la porosité converge vers la
    /// cible avec un pas amorti par la viscosité η.
    ///
    /// - **Résonance** (`coherence ≥ 0`) → cible = π (ouverture) ;
    /// - **Bruit** (`coherence < 0`) → contraction vers `POROSITE_MIN`
    ///   (imperméabilité défensive) ;
    /// - **η** borne le pas : une forte viscosité = forte inertie = la membrane
    ///   ne saute pas (anti-hyper-réactivité, anti-oscillations folles).
    ///
    /// Événementiel, `O(1)`, aucun état global, aucune allocation.
    pub fn recevoir(&mut self, g: &GradientH) {
        let cible: f64 = if g.coherence >= 0.0 {
            g.porosite_cible
        } else {
            POROSITE_MIN + (1.0 - POROSITE_MIN) * (1.0 + g.coherence)
        };
        // Pas d'évolution = 1 − η (borné) : η élevé → pas petit → inertie forte.
        let pas: f64 = (1.0 - g.viscosite.clamp(0.0, 0.99)).max(1e-6);
        self.porosite += pas * (cible - self.porosite);
        self.porosite = self.porosite.clamp(POROSITE_MIN, 1.0);
    }

    /// Seuil effectif = seuil / porosité (une membrane contractée exige une
    /// résonance plus forte).
    pub fn seuil_effectif(&self) -> f64 {
        self.seuil / self.porosite.max(1e-9)
    }
}

// ===========================================================================
// Q2 — veilleur::adaptateur : ingestion pure, bornée, repli état stable
// ===========================================================================

/// Rapport territorial borné (entrée du Veilleur). Struct `Copy`, bornes
/// validées par construction dans `ingere_rapport`.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Rapport {
    /// Entropie collective (bornée [0, ~7]).
    pub entropie: f64,
    /// Couplage moyen (borné [0, 1]).
    pub couplage: f64,
    /// Résonance globale (bornée [-1, 1]).
    pub resonance: f64,
    /// Tremor moyen (borné [0, 1]).
    pub tremor: f64,
    /// Nombre de respirations (activité anti-homogénéisation).
    pub n_respirations: u64,
}

/// Erreur d'ingestion — le Veilleur refuse la config et maintient l'état stable.
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum ErreurVeilleur {
    /// Champ hors bornes (nom du champ).
    HorsBornes(&'static str),
    /// Le rapport viole la triade Ψ → B → Φ (ex. homogénéisation totale).
    ViolationTriade,
}

/// **Ingestion pure** : parse une chaîne `clé=valeur;...` et valide les bornes.
///
/// - Ne lit **pas** l'état du tissu.
/// - N'attend **pas** de réponse.
/// - Retourne `Err` sur toute valeur hors bornes ou incohérente → le
///   `VeilleurStable` maintiendra le dernier état valide (repli).
pub fn ingere_rapport(entree: &str) -> Result<Rapport, ErreurVeilleur> {
    let mut r = Rapport {
        entropie: 0.0,
        couplage: 0.0,
        resonance: 0.0,
        tremor: 0.0,
        n_respirations: 0,
    };
    for champ in entree.split(';') {
        let champ = champ.trim();
        if champ.is_empty() {
            continue;
        }
        let mut it = champ.split('=');
        let (cle, valeur) = match (it.next(), it.next()) {
            (Some(c), Some(v)) => (c.trim(), v.trim()),
            _ => return Err(ErreurVeilleur::HorsBornes("format")),
        };
        match cle {
            "entropie" => {
                let v: f64 = valeur
                    .parse()
                    .map_err(|_| ErreurVeilleur::HorsBornes("entropie"))?;
                if !(0.0..=7.0).contains(&v) {
                    return Err(ErreurVeilleur::HorsBornes("entropie"));
                }
                r.entropie = v;
            }
            "couplage" => {
                let v: f64 = valeur
                    .parse()
                    .map_err(|_| ErreurVeilleur::HorsBornes("couplage"))?;
                if !(0.0..=1.0).contains(&v) {
                    return Err(ErreurVeilleur::HorsBornes("couplage"));
                }
                r.couplage = v;
            }
            "resonance" => {
                let v: f64 = valeur
                    .parse()
                    .map_err(|_| ErreurVeilleur::HorsBornes("resonance"))?;
                if !(-1.0..=1.0).contains(&v) {
                    return Err(ErreurVeilleur::HorsBornes("resonance"));
                }
                r.resonance = v;
            }
            "tremor" => {
                let v: f64 = valeur
                    .parse()
                    .map_err(|_| ErreurVeilleur::HorsBornes("tremor"))?;
                if !(0.0..=1.0).contains(&v) {
                    return Err(ErreurVeilleur::HorsBornes("tremor"));
                }
                r.tremor = v;
            }
            "n_respirations" => {
                let v: u64 = valeur
                    .parse()
                    .map_err(|_| ErreurVeilleur::HorsBornes("n_respirations"))?;
                r.n_respirations = v;
            }
            _ => return Err(ErreurVeilleur::HorsBornes("champ inconnu")),
        }
    }
    // Cohérence avec la triade : une entropie au maximum théorique (≈ 6.4 pour
    // 6 agents) ET un couplage ≈ 1.0 = homogénéisation totale → violation.
    if r.entropie >= 6.3 && r.couplage >= 0.99 {
        return Err(ErreurVeilleur::ViolationTriade);
    }
    Ok(r)
}

/// **Veilleur-Adaptateur** : membrane de traduction, pas centre de décision.
///
/// - Traduit les rapports en `GradientH` (π/η dérivés) ;
/// - **Maintient le dernier état stable** en cas d'erreur (repli) ;
/// - **Trace le refus** et signale un **recours humain** le cas échéant.
#[derive(Debug)]
pub struct VeilleurStable {
    /// Dernier rapport valide (état stable conservé).
    dernier: Option<Rapport>,
    /// Nombre de refus tracés.
    n_refus: u64,
    /// `true` si un recours humain doit être déclenché.
    recours_humain: bool,
}

impl VeilleurStable {
    /// Nouveau Veilleur-Adaptateur : aucun état stable, aucun refus, pas de
    /// recours humain en attente.
    pub fn nouvelle() -> Self {
        Self {
            dernier: None,
            n_refus: 0,
            recours_humain: false,
        }
    }

    /// Ingeste un rapport : valide par construction, met à jour l'état stable,
    /// ou refuse et **conserve** le dernier état valide.
    pub fn ingerer(&mut self, entree: &str) -> Result<Rapport, ErreurVeilleur> {
        match ingere_rapport(entree) {
            Ok(r) => {
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

    /// Traduit le dernier rapport valide en `GradientH` (π/η).
    pub fn traduire_dernier(&self) -> Option<GradientH> {
        self.dernier.map(|r| GradientH {
            intensite: r.resonance.abs(),
            coherence: r.resonance,
            // π : entropie haute → contraction (anti-homogénéisation) ;
            // sinon ouverture pleine.
            porosite_cible: if r.entropie >= 6.3 { 0.6 } else { 1.0 },
            // η : tremor élevé → inertie (le bruit ne fait pas sauter la membrane).
            viscosite: (0.2 + 0.6 * r.tremor).clamp(0.0, 0.99),
        })
    }

    /// Dernier rapport valide (état stable conservé), s'il existe.
    pub fn dernier_etat(&self) -> Option<Rapport> {
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

    // ------------------------------------------------------------------
    // Q1 — réception π/η
    // ------------------------------------------------------------------

    #[test]
    fn types_copy_sans_allocation_chemin_critique() {
        // Preuve de sobriété : les types du chemin critique (GradientH,
        // MembranePiEta, Rapport) sont des valeurs `Copy` de taille fixe —
        // aucune allocation dynamique, aucun état global, aucun verrou.
        assert_eq!(std::mem::size_of::<GradientH>(), 32, "4×f64, taille fixe");
        assert_eq!(std::mem::size_of::<MembranePiEta>(), 16, "2×f64, taille fixe");
        assert_eq!(std::mem::size_of::<Rapport>(), 40, "4×f64 + u64, taille fixe");
        // `Copy` : aucun pointeur, aucun Vec, aucun String dans ces types.
        fn est_copy<T: Copy>() {}
        est_copy::<GradientH>();
        est_copy::<MembranePiEta>();
        est_copy::<Rapport>();
        est_copy::<ErreurVeilleur>();
    }

    #[test]
    fn reception_ouvre_en_resonance_et_ferme_en_bruit() {
        let mut m = MembranePiEta::nouvelle(0.35);
        // Résonance : membrane ouverte (reste à 1.0).
        m.recevoir(&GradientH::nouvelle(0.9));
        assert!((m.porosite - 1.0).abs() < 1e-9);
        // Bruit : contraction locale bornée.
        m.recevoir(&GradientH::nouvelle(-1.0));
        assert!(m.porosite < 1.0);
        assert!(m.porosite >= POROSITE_MIN);
        // La membrane contractée exige une résonance plus forte.
        assert!(m.seuil_effectif() > 0.35);
        // Réouverture après preuve de résonance : PROGRESSIVE (anti-
        // hyper-réactivité par η) — la porosité remonte de façon monotone
        // vers 1.0 cycle après cycle, sans saut.
        let avant = m.porosite;
        m.recevoir(&GradientH::nouvelle(1.0));
        assert!(
            m.porosite > avant,
            "la réouverture doit être croissante, {avant} → {}",
            m.porosite
        );
        for _ in 0..20 {
            m.recevoir(&GradientH::nouvelle(1.0));
        }
        assert!(
            (m.porosite - 1.0).abs() < 1e-3,
            "la réouverture rejoint l'ouverture pleine, porosité={}",
            m.porosite
        );
    }

    #[test]
    fn viscosite_borne_la_vitesse_de_reponse() {
        // η élevé (inertie forte) → pas petit → la porosité ne saute pas.
        let mut m = MembranePiEta::nouvelle(0.35);
        let mut g = GradientH::nouvelle(-1.0);
        g.viscosite = 0.9; // forte inertie
        m.recevoir(&g);
        let apres_1_pas = m.porosite;
        // Un seul pas ne doit pas atteindre immédiatement le plancher.
        assert!(
            apres_1_pas > POROSITE_MIN + 0.01,
            "inertie forte → décroissance lisse, porosité={apres_1_pas}"
        );
        // 10 000 cycles de bruit → borné au plancher, jamais de NaN/panique.
        for _ in 0..10_000 {
            m.recevoir(&g);
            assert!(m.porosite.is_finite());
            assert!((POROSITE_MIN..=1.0).contains(&m.porosite));
        }
        assert!((m.porosite - POROSITE_MIN).abs() < 1e-3);
    }

    #[test]
    fn pas_de_divergence_sur_10000_cycles_alternes() {
        let mut m = MembranePiEta::nouvelle(0.35);
        for i in 0..10_000u64 {
            let coherence = if i % 2 == 0 { 0.8 } else { -0.6 };
            m.recevoir(&GradientH::nouvelle(coherence));
            assert!(m.porosite.is_finite(), "NaN/Inf interdit (cycle {i})");
            assert!((POROSITE_MIN..=1.0).contains(&m.porosite));
        }
        // Pas de divergence : la porosité reste dans les bornes et finie.
        assert!(m.porosite >= POROSITE_MIN && m.porosite <= 1.0);
    }

    // ------------------------------------------------------------------
    // Q2 — ingestion pure + repli état stable
    // ------------------------------------------------------------------

    #[test]
    fn ingestion_valide_et_traduit_en_gradient() {
        let mut v = VeilleurStable::nouvelle();
        let rapport = v
            .ingerer("entropie=5.5;couplage=0.5;resonance=0.8;tremor=0.1;n_respirations=48")
            .expect("rapport valide");
        assert_eq!(rapport.entropie, 5.5);
        assert_eq!(rapport.couplage, 0.5);
        assert_eq!(rapport.n_respirations, 48);
        assert_eq!(v.n_refus(), 0);
        // Traduction → GradientH π/η (entropie < 6.3 → ouverture pleine).
        let g = v.traduire_dernier().expect("état stable présent");
        assert!((g.porosite_cible - 1.0).abs() < 1e-9);
        assert_eq!(g.coherence, 0.8);
    }

    #[test]
    fn refus_hors_bornes_maintient_le_dernier_etat_stable() {
        let mut v = VeilleurStable::nouvelle();
        v.ingerer("entropie=5.5;couplage=0.5;resonance=0.8;tremor=0.1")
            .expect("valide");
        // Rapport invalide : couplage hors bornes (2.0).
        let err = v.ingerer("entropie=5.5;couplage=2.0;resonance=0.8").unwrap_err();
        assert_eq!(err, ErreurVeilleur::HorsBornes("couplage"));
        assert_eq!(v.n_refus(), 1);
        // L'état stable est conservé (repli), pas écrasé par l'invalide.
        let stable = v.dernier_etat().expect("état stable conservé");
        assert_eq!(stable.couplage, 0.5);
    }

    #[test]
    fn violation_triade_declenche_recours_humain_trace() {
        let mut v = VeilleurStable::nouvelle();
        // Entropie max + couplage 1.0 = homogénéisation totale → violation.
        let err = v
            .ingerer("entropie=6.4;couplage=1.0;resonance=1.0")
            .unwrap_err();
        assert_eq!(err, ErreurVeilleur::ViolationTriade);
        assert!(v.recours_humain(), "le recours humain doit être tracé");
        assert!(v.dernier_etat().is_none(), "aucun état stable n'est imposé");
    }
}
