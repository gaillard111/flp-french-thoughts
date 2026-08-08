//! # Nœud sp3 — la cellule unique (Étape A)
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! L'unité fondamentale du réseau MTTV-FLP : un micro-nœud tridimensionnel
//! modélisé sur le carbone **sp3**, doté de **strictement quatre (4)** liaisons
//! asynchrones orientées dans le temps (diachroniques) :
//! - **1 liaison amont** (réception) : `mpsc::Receiver<Signal>` ;
//! - **3 liaisons aval** (émission) : `mpsc::Sender<Signal>`.
//!
//! Au repos, la cellule dort sur la liaison amont : **aucune boucle active,
//! CPU ≈ 0**. Le réveil est purement événementiel (un signal arrive).
//!
//! Règle d'or 2 : un signal sous le seuil est amorti (rien n'est émis) ;
//! un signal au-dessus du seuil est transduit puis propagé **exclusivement sur
//! les 3 liaisons aval**.

use tokio::sync::mpsc;

use super::transduction::{transduire, IssueTransduction};
use super::types::{Membrane, ModeTet, Signal, SignaturePhi};

/// Nombre de liaisons diachroniques d'une cellule (carbone sp3).
pub const N_LIAISONS: usize = 4;

/// Nombre de liaisons aval (émission) : les 3 liaisons restantes.
pub const N_AVAL: usize = 3;

/// Tampon des canaux (borné — sobriété, backpressure naturelle).
const TAMPON_CANAUX: usize = 4;

/// Cellule carbone sp3 — nœud du réseau MTTV-FLP.
#[derive(Debug)]
pub struct Cellule {
    /// Identifiant local unique.
    pub id: u64,
    /// Signature géométrique locale Φ (dim 4, auto-normalisée).
    pub phi: SignaturePhi,
    /// Membrane à seuil de perméabilité.
    pub membrane: Membrane,
    /// Mode tétravalent courant.
    pub mode: ModeTet,
    /// Compteur de cycles (diachronie).
    pub cycle: u64,
    /// Liaison amont (réception) — `None` une fois démontée par `tourner`.
    amont: Option<mpsc::Receiver<Signal>>,
    /// Liaisons aval (émission) — exactement 3.
    aval: [mpsc::Sender<Signal>; N_AVAL],
    /// Nombre de transductions actives (traçabilité sobriété).
    pub n_transductions: u64,
    /// Nombre de signaux amortis (traçabilité sobriété).
    pub n_amortis: u64,
}

impl Cellule {
    /// Construit une cellule sp3 : 1 canal amont, 3 canaux aval.
    ///
    /// Retourne la cellule **et** l'expéditeur de sa liaison amont (c'est par
    /// lui que le tissu — Étape B — alimentera la cellule depuis ses voisines).
    pub fn nouvelle(id: u64, phi: SignaturePhi, seuil: f64) -> (Self, mpsc::Sender<Signal>) {
        let (tx_amont, rx_amont) = mpsc::channel(TAMPON_CANAUX);
        let (tx_aval_0, _) = mpsc::channel(TAMPON_CANAUX);
        let (tx_aval_1, _) = mpsc::channel(TAMPON_CANAUX);
        let (tx_aval_2, _) = mpsc::channel(TAMPON_CANAUX);

        let cellule = Self {
            id,
            phi,
            membrane: Membrane::nouvelle(seuil),
            mode: ModeTet::Veille,
            cycle: 0,
            amont: Some(rx_amont),
            aval: [tx_aval_0, tx_aval_1, tx_aval_2],
            n_transductions: 0,
            n_amortis: 0,
        };

        (cellule, tx_amont)
    }

    /// Récupère les 3 émetteurs aval (pour connecter les voisines à l'Étape B).
    pub fn liaisons_aval(&self) -> [mpsc::Sender<Signal>; N_AVAL] {
        [
            self.aval[0].clone(),
            self.aval[1].clone(),
            self.aval[2].clone(),
        ]
    }

    /// Boucle de vie asynchrone de la cellule.
    ///
    /// La cellule **dort** sur la liaison amont (`recv().await`). À l'arrivée
    /// d'un signal :
    /// - sous le seuil → amorti (CPU ≈ 0, rien n'est émis) ;
    /// - au-dessus → transduction + propagation sur les 3 liaisons aval.
    ///
    /// Aucun polling : la tâche est suspendue par le runtime tant que rien
    /// n'arrive. Retourne quand le canal amont est fermé (fin de vie).
    pub async fn tourner(&mut self) {
        let mut amont = match self.amont.take() {
            Some(rx) => rx,
            None => return,
        };

        while let Some(signal) = amont.recv().await {
            self.cycle += 1;
            let issue = transduire(
                &mut self.phi,
                &mut self.membrane,
                &signal,
                self.id,
                self.cycle,
            );

            match issue {
                IssueTransduction::Amorti => {
                    self.n_amortis += 1;
                    self.mode = ModeTet::Veille;
                    // Rien n'est émis : le processeur se rendort.
                }
                IssueTransduction::Propage(sortant) => {
                    self.n_transductions += 1;
                    self.mode = ModeTet::Actif;
                    // Propagation exclusive sur les 3 liaisons aval.
                    for tx in &self.aval {
                        // Une voisine absente (récepteur fermé) ne bloque pas :
                        // échec d'envoi = signal dissipé localement.
                        let _ = tx.send(sortant).await;
                    }
                    self.mode = ModeTet::Veille; // le calcul s'éteint de lui-même
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tokio::time::{timeout, Duration};

    fn signal_alignes() -> Signal {
        Signal {
            signature: SignaturePhi::new([1.0, 0.0, 0.0, 0.0]),
            amplitude: 0.8,
            source: 0,
            ts: 0,
        }
    }

    #[test]
    fn cellule_a_quatre_liaisons() {
        let (c, _tx) = Cellule::nouvelle(1, SignaturePhi::new([1.0, 0.0, 0.0, 0.0]), 0.35);
        assert_eq!(c.liaisons_aval().len(), N_AVAL);
        assert_eq!(N_LIAISONS, N_AVAL + 1);
    }

    #[tokio::test]
    async fn boucle_amortit_signal_sous_seuil() {
        let (mut c, tx) =
            Cellule::nouvelle(1, SignaturePhi::new([1.0, 0.0, 0.0, 0.0]), 0.35);

        // Signal orthogonal (résonance ≈ 0 < 0.35) → amorti.
        let signal = Signal {
            signature: SignaturePhi::new([0.0, 1.0, 0.0, 0.0]),
            amplitude: 0.8,
            source: 0,
            ts: 0,
        };
        tx.send(signal).await.unwrap();
        drop(tx); // ferme l'amont → la boucle se termine

        timeout(Duration::from_secs(2), c.tourner())
            .await
            .expect("la boucle doit se terminer");
        assert_eq!(c.n_amortis, 1);
        assert_eq!(c.n_transductions, 0);
    }

    #[tokio::test]
    async fn boucle_propage_signal_au_dela_du_seuil() {
        let (mut c, tx) =
            Cellule::nouvelle(2, SignaturePhi::new([1.0, 0.0, 0.0, 0.0]), 0.35);

        tx.send(signal_alignes()).await.unwrap();
        drop(tx);

        timeout(Duration::from_secs(2), c.tourner())
            .await
            .expect("la boucle doit se terminer");
        assert_eq!(c.n_transductions, 1);
        assert_eq!(c.n_amortis, 0);
        // Après transduction le mode retombe en veille : le calcul s'éteint.
        assert_eq!(c.mode, ModeTet::Veille);
    }
}
