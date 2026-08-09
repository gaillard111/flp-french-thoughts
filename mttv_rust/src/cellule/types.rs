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
