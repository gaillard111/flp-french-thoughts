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
pub(crate) const TAMPON_CANAUX: usize = 4;

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

    /// Construit une cellule **câblée à la naissance** : l'amont et les 3 aval
    /// sont des canaux **injectés** par le gestateur (tissu), jamais créés en
    /// interne pendant la propagation. C'est la primitive de gestation du tissu.
    pub fn avec_canaux(
        id: u64,
        phi: SignaturePhi,
        seuil: f64,
        amont: mpsc::Receiver<Signal>,
        aval: [mpsc::Sender<Signal>; N_AVAL],
    ) -> Self {
        Self {
            id,
            phi,
            membrane: Membrane::nouvelle(seuil),
            mode: ModeTet::Veille,
            cycle: 0,
            amont: Some(amont),
            aval,
            n_transductions: 0,
            n_amortis: 0,
        }
    }

    /// Récupère les 3 émetteurs aval (pour connecter les voisines à l'Étape B).
    pub fn liaisons_aval(&self) -> [mpsc::Sender<Signal>; N_AVAL] {
        [
            self.aval[0].clone(),
            self.aval[1].clone(),
            self.aval[2].clone(),
        ]
    }

    /// Remplace la liaison aval `idx` par un émetteur injecté (raccordement
    /// d'une voisine aval par le gestateur). Ne fait rien si `idx >= N_AVAL`.
    pub fn remplacer_aval(&mut self, idx: usize, tx: mpsc::Sender<Signal>) -> bool {
        if idx >= N_AVAL {
            return false;
        }
        self.aval[idx] = tx;
        true
    }

    /// Remplace la liaison amont par un récepteur injecté (raccordement d'une
    /// voisine amont par le gestateur). Ne fait rien si l'amont est déjà pris
    /// par une boucle en cours.
    pub fn remplacer_amont(&mut self, rx: mpsc::Receiver<Signal>) -> bool {
        if self.amont.is_some() {
            // L'amont n'est retiré que par `tourner` (fin de vie) ; tant qu'il
            // est présent, la cellule est vivante et peut être re-câblée.
            self.amont = Some(rx);
            true
        } else {
            false
        }
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
            self._traiter(signal).await;
        }
    }

    /// Traite **au plus un** signal disponible sur la liaison amont (lecture
    /// non-bloquante `try_recv`). Retourne `Some(sauts_restants)` du signal
    /// **reçu** (avant décrément) **uniquement si le signal a été transduit**
    /// (pas s'il a été amorti — le potentiel à zéro ou le sous-seuil ne compte
    /// pas comme un saut atteint). `None` si rien à traiter.
    ///
    /// Utilisé par le gestateur pour piloter le battement (observation) et
    /// mesurer la profondeur réellement atteinte (juste distance). Aucun
    /// polling : `try_recv` est appelé une fois.
    pub async fn traiter_disponible(&mut self) -> Option<u8> {
        let signal = match self.amont.as_mut() {
            Some(rx) => match rx.try_recv() {
                Ok(s) => s,
                Err(_) => return None, // canal vide ou fermé → rien à traiter
            },
            None => return None,
        };
        let sauts_recus = signal.sauts_restants;
        let a_transduit = self._traiter(signal).await;
        if a_transduit { Some(sauts_recus) } else { None }
    }

    /// Logique commune de traitement d'un signal (transduction + propagation).
    /// Retourne `true` si le signal a été transduit (propage), `false` s'il a
    /// été amorti (sous le seuil ou potentiel à zéro).
    async fn _traiter(&mut self, signal: Signal) -> bool {
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
                false
            }
            IssueTransduction::Propage(sortant) => {
                self.n_transductions += 1;
                self.mode = ModeTet::Actif;
                // Propagation exclusive sur les 3 liaisons aval.
                for tx in &self.aval {
                    // Une voisine absente (récepteur fermé) ne bloque pas :
                    // échec d'envoi = signal dissipé localement.
                    let _ = tx.try_send(sortant);
                }
                self.mode = ModeTet::Veille; // le calcul s'éteint de lui-même
                true
            }
        }
    }

    /// État observable de la cellule — **strictement passif**.
    ///
    /// Lecture seule (`&self`), aucun effet de bord, aucun verrou, aucune
    /// allocation. Sert à l'observation de l'essai B1b (et au rapport) : les
    /// compteurs et le mode sont copiés par valeur, sans toucher à la cellule.
    pub fn etat(&self) -> EtatCellule {
        EtatCellule {
            id: self.id,
            cycle: self.cycle,
            mode: self.mode,
            n_transductions: self.n_transductions,
            n_amortis: self.n_amortis,
        }
    }
}

/// État observable d'une cellule (copie passive, pour observation).
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct EtatCellule {
    /// Identifiant de la cellule.
    pub id: u64,
    /// Compteur de cycles.
    pub cycle: u64,
    /// Mode tétravalent courant.
    pub mode: ModeTet,
    /// Nombre de transductions actives.
    pub n_transductions: u64,
    /// Nombre de signaux amortis.
    pub n_amortis: u64,
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
            sauts_restants: 8,
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
            sauts_restants: 8,
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
