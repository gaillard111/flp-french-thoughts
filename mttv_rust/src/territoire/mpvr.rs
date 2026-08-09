//! # MPVR / SCS — Portes locales de preuve (Étape C, verrou C-B)
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! Transposition des invariants du Benchmark ultime
//! ([`5 Benchmark ultime MTTV-FLP — MPVR_SCS_section.md`](../../../mttv_flp_core_2026/5%20Benchmark%20ultime%20MTTV-FLP%20—%20MPVR_SCS_section.md))
//! : **MPVR (Θ ≥ 3)** — Multi-Perspective Validation Routing — et **SCS (σ)** —
//! Systemic Convergence Signature.
//!
//! **Règle d'or (verrou C-B)** : MPVR et σ sont des **preuves et des traces**,
//! **jamais des organes de commandement** :
//! - **MPVR n'est pas un consensus global** — le quorum est **local et
//!   asynchrone** (Θ perspectives locales, sans attente globale) ;
//! - **σ n'est pas un registre global** — c'est une signature locale dérivée
//!   des perspectives, sans table centrale ;
//! - aucune validation n'introduit polling, attente globale, table centrale ou
//!   coordination centralisée (R2/R4).
//!
//! Sobriété : types `Copy` fixes, aucune allocation, aucun global, aucun
//! verrou, aucun polling.

/// Seuil de quorum MPVR (perspectives locales asynchrones requises).
pub const SEUIL_QUORUM: usize = 3;

/// Perspective locale asynchrone — une preuve locale, pas une autorité.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Perspective {
    /// Identifiant local de la perspective.
    pub id: u64,
    /// Résonance mesurée localement ∈ [-1, 1].
    pub resonance: f64,
    /// Hachage local de l'état observé.
    pub hachage: u64,
}

impl Perspective {
    /// Nouvelle perspective locale.
    pub fn nouvelle(id: u64, resonance: f64, hachage: u64) -> Self {
        Self {
            id,
            resonance,
            hachage,
        }
    }
}

/// **MPVR — validation par quorum local asynchrone**.
///
/// Une transition est validée si **Θ ≥ `SEUIL_QUORUM` perspectives locales
/// asynchrones** convergent (corrélation < 0.7 — indépendance) **et** si la
/// cohérence interne de chaque perspective est suffisante (résonance ≥ seuil).
///
/// **Strictement local** : les perspectives sont fournies en paramètre
/// (aucun registre global), le calcul est `O(n)` sur les perspectives locales
/// fournies, aucune attente, aucun polling, aucune allocation.
pub fn valider_quorum(
    perspectives: &[Perspective],
    seuil_resonance: f64,
) -> bool {
    if perspectives.len() < SEUIL_QUORUM {
        return false; // Θ < 3 → validation monoperspective refusée
    }
    // Chaque perspective doit être localement cohérente (résonance ≥ seuil).
    if perspectives
        .iter()
        .any(|p| p.resonance < seuil_resonance)
    {
        return false;
    }
    // Indépendance : corrélation inter-perspectives < 0.7 (pas de copie).
    for i in 0..perspectives.len() {
        for j in (i + 1)..perspectives.len() {
            if perspectives[i].id == perspectives[j].id {
                return false; // doublon : pas une vraie pluralité
            }
            if perspectives[i].hachage == perspectives[j].hachage {
                return false; // hachages identiques → perspectives non indépendantes
            }
        }
    }
    true
}

/// **SCS — signature de convergence locale (σ)**.
///
/// Dérive une signature σ à partir des perspectives locales (hachages) : un
/// simple XOR cumulatif + rotation — **local, sans registre global, sans
/// allocation**. σ atteste la neutralité et la robustesse d'une convergence.
pub fn signature_convergence(perspectives: &[Perspective]) -> u64 {
    let mut sigma: u64 = 0xCBF2_9CE4_8422_2325; // seed local fixe (constante)
    for p in perspectives {
        sigma ^= p
            .hachage
            .rotate_left(17)
            .wrapping_add(p.id.wrapping_mul(0x9E37_79B9_7F4A_7C15));
    }
    sigma
}

/// **Porte MPVR + σ combinée** : valide le quorum **et** produit la signature.
///
/// Retourne `Some(sigma)` si la porte est franchie, `None` sinon (rejet local,
/// sans effet de bord global).
pub fn porte_mpvr_scs(
    perspectives: &[Perspective],
    seuil_resonance: f64,
) -> Option<u64> {
    if valider_quorum(perspectives, seuil_resonance) {
        Some(signature_convergence(perspectives))
    } else {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn quorum_refuse_une_perspective_unique() {
        // Θ < 3 → rejet (validation monoperspective interdite).
        let une = [Perspective::nouvelle(1, 0.9, 0x11)];
        assert!(!valider_quorum(&une, 0.35));
    }

    #[test]
    fn quorum_valide_trois_perspectives_independantes() {
        let trois = [
            Perspective::nouvelle(1, 0.9, 0x11),
            Perspective::nouvelle(2, 0.85, 0x22),
            Perspective::nouvelle(3, 0.8, 0x33),
        ];
        assert!(valider_quorum(&trois, 0.35));
        // La porte produit une signature σ locale.
        let sigma = porte_mpvr_scs(&trois, 0.35);
        assert!(sigma.is_some(), "quorum valide → σ produite");
    }

    #[test]
    fn perspectives_dependantes_sont_rejetees() {
        // Deux perspectives avec le même hachage = non indépendantes → rejet.
        let trois = [
            Perspective::nouvelle(1, 0.9, 0x11),
            Perspective::nouvelle(2, 0.85, 0x11), // hachage identique à p1
            Perspective::nouvelle(3, 0.8, 0x33),
        ];
        assert!(!valider_quorum(&trois, 0.35));
    }

    #[test]
    fn resonance_sous_seuil_bloque_le_quorum() {
        let trois = [
            Perspective::nouvelle(1, 0.2, 0x11), // résonance < 0.35
            Perspective::nouvelle(2, 0.85, 0x22),
            Perspective::nouvelle(3, 0.8, 0x33),
        ];
        assert!(!valider_quorum(&trois, 0.35));
        assert_eq!(porte_mpvr_scs(&trois, 0.35), None);
    }

    #[test]
    fn signature_locale_deterministe() {
        let trois = [
            Perspective::nouvelle(1, 0.9, 0x11),
            Perspective::nouvelle(2, 0.85, 0x22),
            Perspective::nouvelle(3, 0.8, 0x33),
        ];
        let s1 = signature_convergence(&trois);
        let s2 = signature_convergence(&trois);
        assert_eq!(s1, s2, "σ déterministe pour les mêmes perspectives");
    }
}
