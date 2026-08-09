//! # Types fondamentaux de la cellule (Étape A)
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! Transposition fidèle de la sémantique de référence :
//! [`agent_tetravalent_epigenetique.py`](../../../zoo-code/agent_tetravalent_epigenetique.py)
//! — tenseur Φ (signature géométrique auto-normalisée, dim 4), seuil de
//! résonance, signal d'interférence `tanh`, état tétravalent {0, 0.25, 0.75, 1}.
//!
//! Aucune allocation dynamique au cœur du nœud : tailles fixes (`[f64; 4]`).

/// Tenseur Φ — signature géométrique locale, dimension 4, auto-normalisée.
///
/// La résonance entre deux signatures est le **produit scalaire** de leurs
/// vecteurs (référence : `calculer_resonance` ∈ [-1, 1]).
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct SignaturePhi(pub [f64; 4]);

impl SignaturePhi {
    /// Construit une signature et la **normalise** (projection sur la sphère
    /// unité). Refuse la norme nulle en ramenant à l'identité canonique.
    pub fn new(valeurs: [f64; 4]) -> Self {
        let mut phi = Self(valeurs);
        phi.normaliser();
        phi
    }

    /// Normalise le vecteur (norme L2 → 1). Si la norme est quasi nulle,
    /// bascule sur la signature canonique (0, 0, 0, 1) pour éviter la
    /// division par zéro (anti-effondrement du tenseur).
    pub fn normaliser(&mut self) {
        let norme: f64 = self.0.iter().map(|x| x * x).sum::<f64>().sqrt();
        if norme > 1e-12 {
            for x in &mut self.0 {
                *x /= norme;
            }
        } else {
            self.0 = [0.0, 0.0, 0.0, 1.0];
        }
    }

    /// Résonance = produit scalaire normalisé ∈ [-1, 1].
    pub fn resonance(&self, autre: &Self) -> f64 {
        self.0
            .iter()
            .zip(autre.0.iter())
            .map(|(a, b)| a * b)
            .sum()
    }

    /// Réalignement plastique léger vers une autre signature (co-cicatrisation).
    /// `gamma` est la force du réalignement (référence : 0.15).
    pub fn realigner_vers(&mut self, autre: &Self, gamma: f64) {
        for (s, a) in self.0.iter_mut().zip(autre.0.iter()) {
            *s += gamma * (*a - *s);
        }
        self.normaliser();
    }

    /// **Poumon de diversité** — respiration géométrique locale (remède C4/C7).
    ///
    /// Injecte une composante **orthogonale** (Gram-Schmidt) à Φ, pondérée par
    /// `dose`, puis re-normalise. C'est le pendant exact de la référence Python
    /// [`respirer_diversite_phi`](../../../zoo-code/essaim_tetravalent.py:557) :
    /// on n'amplifie pas l'alignement existant, on l'**écarte délibérément**
    /// (SOPH-IA : sous-optimalité assumée) — c'est ce qui contrecarre le lissage
    /// de la co-cicatrisation (sans respiration, le tissu s'écrase à sim ≈ 0.963).
    ///
    /// **Local et sobre** : le bruit est **déterministe**, dérivé du `seed` local
    /// (identité/cycle de la cellule) — zéro allocation, zéro global, zéro
    /// polling. Chaque cellule respire vers une direction propre → diversité
    /// de tissu maintenue (plancher d'entropie au-dessus du seuil C4).
    pub fn respirer(&mut self, seed: u64, dose: f64) {
        // Bruit pseudo-aléatoire déterministe (SplitMix64) local au seed.
        let mut x: u64 = seed.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut bruit = [0.0f64; 4];
        for c in bruit.iter_mut() {
            x = (x ^ (x >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
            x = (x ^ (x >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
            x ^= x >> 31;
            // Normalise le bruit dans [-1, 1].
            *c = (x as f64 / u64::MAX as f64) * 2.0 - 1.0;
        }

        // Gram-Schmidt : retirer la projection du bruit sur Φ, ne garder que la
        // composante perpendiculaire (orthogonalisation, comme la référence).
        let norm2: f64 = self.0.iter().map(|v| v * v).sum::<f64>().max(1e-12);
        let projection: f64 = self
            .0
            .iter()
            .zip(bruit.iter())
            .map(|(a, b)| a * b)
            .sum::<f64>()
            / norm2;
        let mut ortho = [0.0f64; 4];
        for i in 0..4 {
            ortho[i] = bruit[i] - projection * self.0[i];
        }

        // Perturbation pondérée (1 − dose)·Φ + dose·ortho, puis normalisation.
        for i in 0..4 {
            self.0[i] = (1.0 - dose) * self.0[i] + dose * ortho[i];
        }
        self.normaliser();
    }
}

/// État tétravalent d'un nœud interne.
///
/// Transposition de la matrice M de référence :
/// - `Effondre` : 0.0  — effondré / mort
/// - `Veille`   : 0.25 — veille / réceptif passif
/// - `Actif`    : 0.75 — actif / émetteur
/// - `Sature`   : 1.0  — saturé / rigide
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ModeTet {
    /// 0.0 — effondré / mort.
    Effondre,
    /// 0.25 — veille / réceptif passif.
    Veille,
    /// 0.75 — actif / émetteur.
    Actif,
    /// 1.0 — saturé / rigide.
    Sature,
}

impl ModeTet {
    /// Valeur scalaire du mode (0.0, 0.25, 0.75, 1.0).
    pub fn valeur(self) -> f64 {
        match self {
            ModeTet::Effondre => 0.0,
            ModeTet::Veille => 0.25,
            ModeTet::Actif => 0.75,
            ModeTet::Sature => 1.0,
        }
    }
}

/// Signal transductif transporté entre cellules.
///
/// Il porte la signature du flux émis (pour la mesure de résonance à la
/// membrane), son amplitude (interférence non-linéaire), la source,
/// l'horodatage du cycle, et le **potentiel de propagation décroissant**
/// (leçon C4 / gradient §8 : sans ce potentiel, le signal homogénéise tout le
/// tissu ; il borne la propagation et garantit l'extinction naturelle).
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Signal {
    /// Signature géométrique du flux.
    pub signature: SignaturePhi,
    /// Amplitude du signal ∈ (-1, 1) (issue de l'interférence `tanh`).
    pub amplitude: f64,
    /// Identifiant de la cellule source.
    pub source: u64,
    /// Cycle / horodatage d'émission.
    pub ts: u64,
    /// Potentiel de propagation décroissant : sauts restants avant extinction.
    /// Décrémenté à chaque transduction ; à zéro, le signal s'éteint
    /// (échafaudage local temporaire, pas un TTL de routage — Point 3).
    pub sauts_restants: u8,
}

/// État courant de la membrane.
///
/// - `Impermeable` : signal sous le seuil → étouffé, processeur au repos.
/// - `Poreux` : potentiel franchi → transduction active.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum EtatMembrane {
    /// Signal sous le seuil → étouffé, processeur au repos.
    Impermeable,
    /// Potentiel franchi → transduction active.
    Poreux,
}

/// Membrane virtuelle métastable (Simondon) — seuil de perméabilité critique.
///
/// La porosité (`porosite` ∈ [0, 1]) s'ajustera dynamiquement à l'Étape C
/// (ouverture en résonance, contraction en bruit/attaque) — la base seuil
/// statique est posée ici.
#[derive(Clone, Copy, Debug)]
pub struct Membrane {
    /// Seuil critique de perméabilité (référence : `seuil_resonance` ≈ 0.35).
    pub seuil: f64,
    /// Porosité courante ∈ [0, 1] (1 = ouverte, 0 = contractée).
    pub porosite: f64,
    /// État courant de la membrane.
    pub etat: EtatMembrane,
}

impl Membrane {
    /// Nouvelle membrane avec un seuil donné, porosité initiale 1.0.
    pub fn nouvelle(seuil: f64) -> Self {
        Self {
            seuil,
            porosite: 1.0,
            etat: EtatMembrane::Impermeable,
        }
    }

    /// Évalue la résonance reçue contre le seuil et met à jour l'état.
    ///
    /// Retourne l'état résultant : `Poreux` si la résonance ≥ seuil,
    /// `Impermeable` sinon (amortissement passif).
    pub fn evaluer(&mut self, resonance: f64) -> EtatMembrane {
        // La porosité module le seuil effectif : plus la membrane est
        // contractée (porosite < 1), plus le seuil effectif est élevé.
        let seuil_effectif: f64 = self.seuil / self.porosite.max(1e-9);
        self.etat = if resonance >= seuil_effectif {
            EtatMembrane::Poreux
        } else {
            EtatMembrane::Impermeable
        };
        self.etat
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn signature_normalisee_et_resonance() {
        let a = SignaturePhi::new([3.0, 0.0, 0.0, 0.0]);
        let b = SignaturePhi::new([1.0, 1.0, 0.0, 0.0]);
        // a normalisé = (1,0,0,0) ; b normalisé = (√0.5, √0.5, 0, 0)
        let r = a.resonance(&b);
        assert!((r - std::f64::consts::FRAC_1_SQRT_2).abs() < 1e-9, "r={r}");
    }

    #[test]
    fn signature_nulle_devient_canonique() {
        let phi = SignaturePhi::new([0.0, 0.0, 0.0, 0.0]);
        assert_eq!(phi.0, [0.0, 0.0, 0.0, 1.0]);
    }

    #[test]
    fn mode_tet_valeurs() {
        assert_eq!(ModeTet::Effondre.valeur(), 0.0);
        assert_eq!(ModeTet::Veille.valeur(), 0.25);
        assert_eq!(ModeTet::Actif.valeur(), 0.75);
        assert_eq!(ModeTet::Sature.valeur(), 1.0);
    }

    #[test]
    fn membrane_franchit_seuil() {
        let mut m = Membrane::nouvelle(0.35);
        assert_eq!(m.evaluer(0.2), EtatMembrane::Impermeable);
        assert_eq!(m.evaluer(0.4), EtatMembrane::Poreux);
    }

    #[test]
    fn respiration_locale_deterministe_et_preserve_la_norme() {
        // La respiration (Poumon de Diversité C7) est déterministe pour un même
        // seed local, préserve la norme L2 (Φ reste sur la sphère unité) et
        // écarte la signature vers une direction propre (anti-lissage).
        let a = SignaturePhi::new([1.0, 0.0, 0.0, 0.0]);
        let mut b = a;
        b.respirer(7, 0.35);

        // Déterminisme : même seed → même résultat.
        let mut b2 = SignaturePhi::new([1.0, 0.0, 0.0, 0.0]);
        b2.respirer(7, 0.35);
        assert_eq!(b, b2, "la respiration doit être déterministe par seed");

        // Norme conservée (normalisation interne).
        let norme: f64 = b.0.iter().map(|x| x * x).sum::<f64>().sqrt();
        assert!((norme - 1.0).abs() < 1e-9, "Φ doit rester sur la sphère unité, norme={norme}");

        // Écartement : la composante orthogonale injectée réduit la résonance
        // avec la signature initiale (elle ne renforce pas l'alignement).
        let resonance = a.resonance(&b);
        assert!(
            resonance < 1.0,
            "la respiration doit écarter Φ de sa direction initiale, r={resonance}"
        );

        // Seeds différents → directions différentes (plancher de diversité).
        let mut c = SignaturePhi::new([1.0, 0.0, 0.0, 0.0]);
        c.respirer(11, 0.35);
        assert_ne!(b, c, "deux seeds différents doivent diverger");
    }

    #[test]
    fn respiration_est_bornee_non_cumulative() {
        // Point de vigilance conseil (B2b) : la respiration ne doit PAS
        // s'accumuler indéfiniment au fil des cycles de croissance. La dose
        // est appliquée à chaque cycle, mais Φ reste sur la sphère unité
        // (norme = 1 après normalisation) : aucune divergence, aucune explosion.
        // Après 10 000 respirations successives, la norme doit rester 1 et
        // les composantes rester finies (bornées dans [-1, 1]).
        let mut phi = SignaturePhi::new([1.0, 0.0, 0.0, 0.0]);
        for cycle in 0..10_000u64 {
            // Seed local déterministe (id + cycle), comme dans noeud.rs.
            let seed = 7u64
                .wrapping_mul(0x9E37_79B9_7F4A_7C15)
                .wrapping_add(cycle.wrapping_mul(0xBF58_476D_1CE4_E5B9));
            phi.respirer(seed, 0.35);
        }
        let norme: f64 = phi.0.iter().map(|x| x * x).sum::<f64>().sqrt();
        assert!(
            (norme - 1.0).abs() < 1e-9,
            "la respiration doit rester sur la sphère unité après 10k cycles, norme={norme}"
        );
        for c in &phi.0 {
            assert!(
                c.is_finite() && (-1.0..=1.0).contains(c),
                "composante Φ bornée dans [-1,1], obtenue {c}"
            );
        }
        // La résonance avec une autre signature reste bornée : pas d'explosion.
        let autre = SignaturePhi::new([0.0, 1.0, 0.0, 0.0]);
        let r = phi.resonance(&autre);
        assert!(
            r.is_finite() && (-1.0..=1.0).contains(&r),
            "résonance bornée après accumulation de respirations, r={r}"
        );
    }

    #[test]
    fn membrane_contractee_releve_le_seuil() {
        // Porosité 0.5 → seuil effectif 0.35/0.5 = 0.7 : une résonance de
        // 0.5 (poreuse à pleine ouverture) devient imperméable.
        let mut m = Membrane {
            seuil: 0.35,
            porosite: 0.5,
            etat: EtatMembrane::Impermeable,
        };
        assert_eq!(m.evaluer(0.5), EtatMembrane::Impermeable);
        assert_eq!(m.evaluer(0.8), EtatMembrane::Poreux);
    }
}
