//! # Transduction (Étape A) — la membrane et son seuil
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! Règle d'or 2 — Captation transductive et porosité de la membrane :
//! - **Amortissement passif** : signal / quorum local < seuil → membrane
//!   imperméable, signal étouffé et dissipé localement, CPU ≈ 0.
//! - **Transduction active** : potentiel ≥ seuil → membrane poreuse, le nœud
//!   s'active, s'individue, met à jour son état, propage le signal modifié
//!   exclusivement sur ses **trois (3) autres liaisons restantes**.
//!
//! Fidélité : interférence `tanh(0.5·s1 + 0.5·s2 + s1·s2·r)` et co-cicatrisation
//! par réalignement de Φ (référence Python). Aucune boucle, aucune allocation.

use super::types::{EtatMembrane, GradientH, Membrane, Signal, SignaturePhi};

/// Constante de réalignement plastique (référence : `gamma = 0.15`).
const GAMMA_REALIGNEMENT: f64 = 0.15;

/// Signal d'interférence non-linéaire : `tanh(0.5·s1 + 0.5·s2 + s1·s2·r)`.
///
/// Référence : `AgentTetravalentEpigenetique.interference_signal`.
/// Retour ∈ (-1, 1).
pub fn signal_interference(sig1: f64, sig2: f64, resonance: f64) -> f64 {
    (0.5 * sig1 + 0.5 * sig2 + sig1 * sig2 * resonance).tanh()
}

/// Évalue un signal entrant contre la membrane et détermine s'il transduit.
///
/// Retourne `true` si le potentiel franchit le seuil (membrane poreuse),
/// `false` sinon (amortissement passif).
pub fn franchit_seuil(membrane: &mut Membrane, resonance: f64) -> bool {
    membrane.evaluer(resonance) == EtatMembrane::Poreux
}

/// Résultat d'un cycle de transduction.
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum IssueTransduction {
    /// Signal étouffé (sous le seuil) — processeur au repos, rien n'est propagé.
    Amorti,
    /// Transduction active : le signal modifié est propagé sur les 3 liaisons aval.
    Propage(Signal),
}

/// Exécute un cycle complet de transduction sur un signal entrant.
///
/// - **Palpe le territoire** (B3) : la résonance mesurée forme le gradient
///   local (matrice H) qui **module la porosité** de la membrane avant
///   l'évaluation du seuil (ouverture en résonance, contraction en bruit).
/// - Si < seuil → `IssueTransduction::Amorti` (aucune propagation, CPU ≈ 0).
/// - Sinon → réaligne localement Φ (co-cicatrisation), construit le signal
///   modifié par interférence et le renvoie pour propagation sur les 3 aval.
///
/// Paramètres (purs) :
/// - `phi` : signature locale Φ de la cellule (mise à jour en place).
/// - `membrane` : membrane à seuil (état et porosité mis à jour en place).
/// - `signal` : signal entrant.
/// - `source` : identifiant de la cellule (devient source du signal émis).
/// - `ts` : horodatage du cycle courant.
pub fn transduire(
    phi: &mut SignaturePhi,
    membrane: &mut Membrane,
    signal: &Signal,
    source: u64,
    ts: u64,
) -> IssueTransduction {
    let resonance: f64 = phi.resonance(&signal.signature);

    // Étape C — Matrice H : la résonance locale est le gradient territorial
    // palpé par la cellule (règle d'or 3). La porosité s'ajuste avant le seuil
    // via le couple π/η : résonance → ouverture vers π, bruit → contraction,
    // η amortit (réouverture progressive, anti-hyper-réactivité).
    membrane.ajuster_porosite(&GradientH::nouvelle(resonance));

    if !franchit_seuil(membrane, resonance) {
        return IssueTransduction::Amorti;
    }

    // Potentiel de propagation décroissant : à zéro, le signal s'éteint.
    // C'est l'anti-homogénéisation (leçon C4) : sans ce potentiel, le signal
    // homogénéiserait tout le tissu (extinction forcée, pas de boucle).
    if signal.sauts_restants == 0 {
        return IssueTransduction::Amorti;
    }

    // Co-cicatrisation : réalignement plastique de Φ vers le signal reçu.
    phi.realigner_vers(&signal.signature, GAMMA_REALIGNEMENT);

    // Signal modifié par interférence non-linéaire.
    let amplitude: f64 = signal_interference(
        signal.amplitude,
        resonance,
        resonance,
    );

    let sortant = Signal {
        signature: *phi,
        amplitude,
        source,
        ts,
        sauts_restants: signal.sauts_restants - 1,
    };

    IssueTransduction::Propage(sortant)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn interference_sous_seuil() {
        let mut phi = SignaturePhi::new([1.0, 0.0, 0.0, 0.0]);
        let mut membrane = Membrane::nouvelle(0.35);
        // Signature orthogonale → résonance ≈ 0 < seuil → amorti.
        let signal = Signal {
            signature: SignaturePhi::new([0.0, 1.0, 0.0, 0.0]),
            amplitude: 0.8,
            source: 1,
            ts: 0,
            sauts_restants: 8,
        };
        let issue = transduire(&mut phi, &mut membrane, &signal, 7, 1);
        assert_eq!(issue, IssueTransduction::Amorti);
        assert_eq!(membrane.etat, EtatMembrane::Impermeable);
    }

    #[test]
    fn transduction_au_dela_du_seuil() {
        let mut phi = SignaturePhi::new([1.0, 0.0, 0.0, 0.0]);
        let mut membrane = Membrane::nouvelle(0.35);
        // Signature alignée → résonance ≈ 1 ≥ seuil → propage.
        let signal = Signal {
            signature: SignaturePhi::new([1.0, 0.0, 0.0, 0.0]),
            amplitude: 0.8,
            source: 1,
            ts: 0,
            sauts_restants: 8,
        };
        let issue = transduire(&mut phi, &mut membrane, &signal, 7, 1);
        match issue {
            IssueTransduction::Propage(sortant) => {
                assert_eq!(sortant.source, 7);
                assert_eq!(sortant.ts, 1);
                assert!(sortant.amplitude.abs() <= 1.0);
            }
            IssueTransduction::Amorti => panic!("devrait transduire"),
        }
        assert_eq!(membrane.etat, EtatMembrane::Poreux);
    }

    #[test]
    fn co_cicatrisation_realigne_phi() {
        let mut phi = SignaturePhi::new([1.0, 0.0, 0.0, 0.0]);
        let mut membrane = Membrane::nouvelle(0.35);
        // Cible partiellement alignée : résonance = 0.8 ≥ seuil → transduction.
        let cible = SignaturePhi::new([0.8, 0.6, 0.0, 0.0]);
        let resonance_avant = phi.resonance(&cible);
        assert!((resonance_avant - 0.8).abs() < 1e-9);

        let signal = Signal {
            signature: cible,
            amplitude: 0.8,
            source: 1,
            ts: 0,
            sauts_restants: 8,
        };
        let issue = transduire(&mut phi, &mut membrane, &signal, 7, 1);
        // La transduction doit propager (signal modifié, source = 7).
        let IssueTransduction::Propage(sortant) = issue else {
            panic!("devrait transduire");
        };
        assert_eq!(sortant.source, 7);
        assert_eq!(sortant.ts, 1);
        // Après réalignement, Φ s'est rapproché de la cible (résonance ↑).
        let resonance_apres = phi.resonance(&cible);
        assert!(
            resonance_apres > resonance_avant,
            "Φ devrait se rapprocher de la cible ({resonance_avant} -> {resonance_apres})"
        );
    }

    #[test]
    fn signal_interference_borne() {
        let s = signal_interference(0.8, 0.6, 0.5);
        assert!((-1.0..1.0).contains(&s));
    }
}
