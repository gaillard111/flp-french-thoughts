//! # B1b — Premier signal d'essai (transduction sp3 de proche en proche)
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! Protocole : [`docs/06_PROTOCOLE_B1b.md`](../../docs/06_PROTOCOLE_B1b.md).
//!
//! Prouve par l'expérience que la transduction sp3 fonctionne de proche en
//! proche entre deux cellules câblées par B1a :
//! - un signal **aligné** (résonance ≥ seuil) traverse la liaison aval→amont ;
//! - un signal **orthogonal** (résonance < seuil) est amorti à la source et ne
//!   franchit pas la liaison (filtre membranaire) ;
//! - la transmission est déterministe, événementielle et s'éteint d'elle-même.
//!
//! Aucun polling : l'injection est événementielle, l'observation est une
//! lecture passive (`etat()`). Aucun verrou global, aucune allocation dans le
//! chemin chaud.

use std::time::{Duration, Instant};

use tokio::sync::mpsc;

use crate::cellule::{Cellule, EtatCellule, Signal, SignaturePhi};

use super::lien::brancher;

/// Signature Φ de la source et de la cible (identiques, résonance max).
const PHI_ALIGNE: [f64; 4] = [1.0, 0.0, 0.0, 0.0];

/// Seuil de perméabilité des deux cellules.
const SEUIL: f64 = 0.35;

/// Résultat consolidé d'un essai de transmission bilatérale.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct ResultatEssai {
    /// État de la source après l'essai.
    pub source: EtatCellule,
    /// État de la cible après l'essai.
    pub cible: EtatCellule,
    /// `true` si la cible a reçu (traité) au moins un signal.
    pub reception_cible: bool,
    /// Latence de bout en bout (injection → traitement par la cible).
    pub latence: Duration,
}

/// Construit le dispositif : deux cellules câblées source→cible (slot 0).
///
/// Retourne `(source, cible, emetteur_amont_source)` — l'émetteur amont de la
/// source est le point d'injection du signal d'essai.
fn dispositif() -> (Cellule, Cellule, mpsc::Sender<Signal>) {
    let (mut source, tx_amont) =
        Cellule::nouvelle(1, SignaturePhi::new(PHI_ALIGNE), SEUIL);
    let (mut cible, _) = Cellule::nouvelle(2, SignaturePhi::new(PHI_ALIGNE), SEUIL);

    // Câblage B1a : aval[0] de la source → amont de la cible.
    assert_eq!(brancher(&mut source, &mut cible, 0), Ok(()));

    (source, cible, tx_amont)
}

/// Exécute un essai : lance la cible en tâche Tokio, injecte le(s) signal(aux),
/// fait tourner la source, puis récupère les états des deux cellules.
async fn executer_essai(
    signaux: Vec<Signal>,
) -> ResultatEssai {
    let (mut source, mut cible, tx_amont) = dispositif();

    // La cible tourne en parallèle : elle dort sur son amont (zéro polling).
    let handle_cible = tokio::spawn(async move {
        cible.tourner().await;
        cible
    });

    let debut = Instant::now();
    for signal in signaux {
        tx_amont.send(signal).await.expect("injection échouée");
    }
    drop(tx_amont); // ferme l'amont de la source → sa boucle se termine

    source.tourner().await;
    let latence = debut.elapsed();

    // Capture passive de l'état de la source, puis drop de la source :
    // cela ferme l'émetteur aval branché sur la cible → la cible peut
    // terminer sa boucle (sinon deadlock : elle attend un canal jamais fermé).
    let etat_source = source.etat();
    drop(source);

    let cible = tokio::time::timeout(
        Duration::from_secs(2),
        handle_cible,
    )
    .await
    .expect("la cible ne se termine pas (deadlock détecté)")
    .expect("tâche cible terminée en erreur");

    let etat_cible = cible.etat();
    ResultatEssai {
        source: etat_source,
        cible: etat_cible,
        reception_cible: etat_cible.n_transductions + etat_cible.n_amortis > 0,
        latence,
    }
}

/// Essai 1 — signal aligné (résonance 1.0 ≥ seuil) : doit traverser.
pub async fn essai_signal_aligne() -> ResultatEssai {
    executer_essai(vec![Signal {
        signature: SignaturePhi::new(PHI_ALIGNE),
        amplitude: 0.8,
        source: 0,
        ts: 1,
        sauts_restants: 8,
    }])
    .await
}

/// Essai 2 — signal orthogonal (résonance 0.0 < seuil) : ne doit pas traverser.
pub async fn essai_signal_orthogonal() -> ResultatEssai {
    executer_essai(vec![Signal {
        signature: SignaturePhi::new([0.0, 1.0, 0.0, 0.0]),
        amplitude: 0.8,
        source: 0,
        ts: 1,
        sauts_restants: 8,
    }])
    .await
}

/// Essai 3 — séquence mixte `S−` puis `S+` : la cible ne traite que `S+`.
pub async fn essai_sequence_mixte() -> ResultatEssai {
    executer_essai(vec![
        Signal {
            signature: SignaturePhi::new([0.0, 1.0, 0.0, 0.0]),
            amplitude: 0.8,
            source: 0,
            ts: 1,
            sauts_restants: 8,
        },
        Signal {
            signature: SignaturePhi::new(PHI_ALIGNE),
            amplitude: 0.8,
            source: 0,
            ts: 2,
            sauts_restants: 8,
        },
    ])
    .await
}

/// Lance les trois essais et affiche les **métriques réelles** (compteurs +
/// latence). C'est le rapport de l'expérience : la théorie validée par le réel.
pub async fn lancer_essais() -> Vec<ResultatEssai> {
    let aligne = essai_signal_aligne().await;
    let orthogonal = essai_signal_orthogonal().await;
    let mixte = essai_sequence_mixte().await;

    println!("=== ESSAI B1b — transmission bilatérale sp3 ===");
    println!(
        "1. aligné    : source(T={},A={}) cible(T={},A={}) reçu={} lat={:?}",
        aligne.source.n_transductions, aligne.source.n_amortis,
        aligne.cible.n_transductions, aligne.cible.n_amortis,
        aligne.reception_cible, aligne.latence,
    );
    println!(
        "2. orthogonal: source(T={},A={}) cible(T={},A={}) reçu={} lat={:?}",
        orthogonal.source.n_transductions, orthogonal.source.n_amortis,
        orthogonal.cible.n_transductions, orthogonal.cible.n_amortis,
        orthogonal.reception_cible, orthogonal.latence,
    );
    println!(
        "3. mixte     : source(T={},A={}) cible(T={},A={}) reçu={} lat={:?}",
        mixte.source.n_transductions, mixte.source.n_amortis,
        mixte.cible.n_transductions, mixte.cible.n_amortis,
        mixte.reception_cible, mixte.latence,
    );
    println!("=== FIN ESSAI B1b ===");

    vec![aligne, orthogonal, mixte]
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cellule::ModeTet;

    #[tokio::test]
    async fn cas_1_signal_aligne_traverse_la_liaison() {
        let r = essai_signal_aligne().await;

        // Source : 1 transduction, 0 amorti, retour Veille (le calcul s'éteint).
        assert_eq!(r.source.n_transductions, 1, "source doit transduire");
        assert_eq!(r.source.n_amortis, 0, "source ne doit pas amortir l'aligné");
        assert_eq!(r.source.mode, ModeTet::Veille, "extinction après transduction");

        // Cible : a reçu et traité (le signal a franchi la liaison).
        assert!(r.reception_cible, "la cible doit recevoir le signal aligné");
        assert_eq!(
            r.cible.n_transductions + r.cible.n_amortis, 1,
            "la cible traite exactement 1 signal"
        );
        assert_eq!(r.cible.mode, ModeTet::Veille, "extinction côté cible");
    }

    #[tokio::test]
    async fn cas_2_signal_orthogonal_ne_traverse_pas() {
        let r = essai_signal_orthogonal().await;

        // Source : 1 amorti, 0 transduction (membrane imperméable).
        assert_eq!(r.source.n_amortis, 1, "source doit amortir l'orthogonal");
        assert_eq!(r.source.n_transductions, 0, "source ne doit pas transduire");

        // Cible : reste au repos (rien n'a franchi la liaison).
        assert!(!r.reception_cible, "la cible ne doit rien recevoir");
        assert_eq!(r.cible.n_transductions, 0);
        assert_eq!(r.cible.n_amortis, 0);
    }

    #[tokio::test]
    async fn rapport_des_metriques_reelles() {
        // Produit le rapport chiffré de l'expérience (compteurs + latence).
        // Visible avec `cargo test -- --nocapture` — c'est la preuve du réel.
        let r = lancer_essais().await;
        assert_eq!(r.len(), 3);
        // Le protocole exige : aligné traverse, orthogonal ne traverse pas.
        assert!(r[0].reception_cible, "cas 1 : la cible doit recevoir");
        assert!(!r[1].reception_cible, "cas 2 : la cible ne doit pas recevoir");
        assert!(r[2].reception_cible, "cas 3 : la cible ne traite que S+");
    }

    #[tokio::test]
    async fn cas_3_sequence_mixte_la_cible_ne_traite_que_s_plus() {
        let r = essai_sequence_mixte().await;

        // Source : 1 amorti (S−) + 1 transduction (S+).
        assert_eq!(r.source.n_amortis, 1, "S− amorti à la source");
        assert_eq!(r.source.n_transductions, 1, "S+ transduit à la source");

        // Cible : ne traite que le signal du cas S+ (1 seul traitement).
        assert!(r.reception_cible, "la cible reçoit le signal S+");
        assert_eq!(
            r.cible.n_transductions + r.cible.n_amortis, 1,
            "la cible ne traite que le signal aligné"
        );
        assert_eq!(r.cible.mode, ModeTet::Veille);
    }
}
