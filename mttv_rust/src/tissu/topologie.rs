//! # B2a-bis — La maille sp3 orientée en autonomie immanente
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! Arbitrage : [`plans/JOURNAL_SESSION.md`](../../../plans/JOURNAL_SESSION.md) §9quinquies.
//!
//! Refonte du tissu statique minimal : chaque cellule tourne **sa propre boucle**
//! en totale autonomie (`tokio::spawn(tourner())`) ; le `Tissu` est un
//! **gestateur pur** — il enfante, injecte et récolte, il ne route jamais.
//!
//! - **Zéro table globale** : aucune `HashMap<u64, Noeud>`, aucun registre de
//!   cellules consulté pendant la propagation (R4).
//! - **Zéro polling** : aucune boucle d'inspection centrale ; l'extinction est
//!   une **cascade de fermeture des canaux** (chaque cellule dont la liaison
//!   amont se ferme termine sa boucle et ferme à son tour ses 3 aval) (R2).
//! - **Observation immanente** : le gestateur récolte l'état final de chaque
//!   cellule via son **`JoinHandle`** (lecture ponctuelle en fin de vie), jamais
//!   via un registre.
//!
//! Chaque cellule naît câblée à ses 4 liaisons diachroniques (1 amont + 3 aval),
//! sans nœud maître, sans table de routage. La géométrie est un **arbre
//! ternaire orienté** (racine sans amont, feuilles en frange — points de
//! croissance pour B2b).

use tokio::sync::mpsc;
use tokio::task::JoinHandle;

use crate::cellule::{Cellule, EtatCellule, Signal, SignaturePhi, N_AVAL};

/// Tampon des canaux du tissu (borné — backpressure naturelle).
pub const TAMPON_TISSU: usize = 4;

/// Profondeur maximale par défaut du tissu statique.
pub const PROFONDEUR_DEFAUT: u32 = 3;

/// État revenu d'une cellule à la fin de sa vie (récolte par `JoinHandle`).
///
/// Le gestateur ne récupère **que** l'observation finale de chaque cellule :
/// son état (compteurs, mode), sa signature Φ (pour l'entropie de tissu) et sa
/// profondeur (pour la mesure de juste distance). La `Cellule` elle-même est
/// consumée par sa tâche : ses émetteurs aval sont fermés à sa mort, ce qui
/// propage l'extinction en cascade (R2 — zéro polling).
#[derive(Clone, Copy, Debug)]
pub struct CelluleRevenue {
    /// Identifiant de la cellule.
    pub id: u64,
    /// Profondeur de la cellule dans l'arbre (racine = 0).
    pub profondeur: u32,
    /// État final observable de la cellule.
    pub etat: EtatCellule,
    /// Signature Φ finale (après co-cicatrisation).
    pub phi: SignaturePhi,
}

/// Tissu statique minimal — **gestateur pur**, jamais routeur.
///
/// - Détient, pour la **gestation** uniquement : les `JoinHandle` des tâches
///   des cellules et l'émetteur amont de la racine (injecteur).
/// - **Ne route jamais** : après la construction, la propagation passe
///   exclusivement par les canaux locaux des cellules.
/// - **N'ordonne pas** : il enfante, injecte un signal à la racine, puis
///   récolte les états finaux quand le tissu s'éteint de lui-même.
pub struct Tissu {
    /// Identifiant de la racine (source d'injection).
    pub racine_id: u64,
    /// Émetteur amont de la racine (point d'injection du signal).
    injecteur: Option<mpsc::Sender<Signal>>,
    /// Tâches des cellules vivantes (gestation). Jamais consultées pour router.
    taches: Vec<JoinHandle<CelluleRevenue>>,
    /// Nombre de cellules enfantes (gestation — taille du tissu).
    n_cellules: usize,
}

impl Tissu {
    /// Construit un arbre ternaire orienté de profondeur `profondeur`.
    ///
    /// Chaque cellule est **enfanter** puis **spawnée** (`tokio::spawn`) avec sa
    /// propre boucle `tourner()` : elle vit seule, sa tâche se termine quand sa
    /// liaison amont se ferme. La racine (id 0) est la source d'injection.
    pub fn construire_arbre(profondeur: u32) -> Self {
        let mut taches: Vec<JoinHandle<CelluleRevenue>> = Vec::new();

        // Canal d'injection de la racine (elle n'a pas de parent).
        let (tx_injecteur, rx_racine) = mpsc::channel(TAMPON_TISSU);

        Self::_enfanter(
            &mut taches,
            0,          // id de la racine
            0,          // profondeur courante
            profondeur, // profondeur maximale
            rx_racine,
        );

        let n_cellules = taches.len();
        Self {
            racine_id: 0,
            injecteur: Some(tx_injecteur),
            taches,
            n_cellules,
        }
    }

    /// Enfante une cellule (id, profondeur) et ses 3 enfants (récursif).
    ///
    /// Chaque cellule naît câblée : son amont est le récepteur fourni (ou créé
    /// pour la racine), ses 3 aval sont les émetteurs vers ses 3 enfants. La
    /// cellule est **spawnée immédiatement** : sa boucle `tourner()` dort sur
    /// son amont (zéro polling) et se termine quand l'amont se ferme — ce qui
    /// ferme à son tour ses émetteurs aval (cascade d'extinction immanente).
    /// À profondeur max, les récepteurs aval restants sont dropés (frange).
    fn _enfanter(
        taches: &mut Vec<JoinHandle<CelluleRevenue>>,
        id: u64,
        profondeur: u32,
        profondeur_max: u32,
        amont: mpsc::Receiver<Signal>,
    ) {
        // Signature Φ diversifiée par profondeur (plancher de diversité).
        let phi = SignaturePhi::new(Self::_phi_par_profondeur(profondeur));

        // Créer les canaux aval (un par enfant) : chaque cellule a 3 émetteurs
        // aval, chaque enfant reçoit un récepteur comme amont.
        let mut aval: Vec<mpsc::Sender<Signal>> = Vec::with_capacity(N_AVAL);
        let mut rx_enfants: Vec<mpsc::Receiver<Signal>> = Vec::with_capacity(N_AVAL);
        for _ in 0..N_AVAL {
            let (tx, rx) = mpsc::channel(TAMPON_TISSU);
            aval.push(tx);
            rx_enfants.push(rx);
        }
        // Conversion en tableau fixe [Sender; 3] (sobriété : taille connue).
        let aval: [mpsc::Sender<Signal>; N_AVAL] = aval
            .try_into()
            .expect("exactement N_AVAL canaux aval créés");

        // Construire la cellule câblée à la naissance.
        let cellule = Cellule::avec_canaux(id, phi, 0.35, amont, aval);

        // Spawner la cellule : sa boucle tourne seule. À la fermeture de son
        // amont, `tourner` rend la main ; on capture l'observation finale puis
        // la `Cellule` est consumée (ses aval sont fermés → extinction en
        // cascade). L'observation passe par le `JoinHandle`, jamais un registre.
        let handle = tokio::spawn(async move {
            let mut cellule = cellule;
            cellule.tourner().await;
            CelluleRevenue {
                id,
                profondeur,
                etat: cellule.etat(),
                phi: cellule.phi,
            }
        });
        taches.push(handle);

        // Enfanter les enfants (récursif) avec le récepteur aval correspondant.
        // `rx_enfants` est une Vec : on retire chaque récepteur en tête.
        if profondeur + 1 <= profondeur_max {
            for i in 0..N_AVAL {
                let enfant_id = id * N_AVAL as u64 + 1 + i as u64;
                let rx = rx_enfants.remove(0);
                Self::_enfanter(taches, enfant_id, profondeur + 1, profondeur_max, rx);
            }
        }
        // À profondeur max : les rx_enfants restants sont dropés ici (frange).
    }

    /// Signature Φ diversifiée par profondeur (plancher de diversité).
    ///
    /// Leçon d'ingénierie (juste distance) : un plancher de diversité
    /// **orthogonal** (niveau 1 = [0,1,0,0]) rend la résonance parent-enfant
    /// = 0 < seuil → le signal est amorti à chaque frontière et le tissu ne
    /// propage jamais. Ici la diversité est une **déviation angulaire douce** :
    /// les Φ restent assez alignés pour transduire (résonance > seuil) mais ne
    /// sont pas identiques (anti-homogénéisation préservée).
    fn _phi_par_profondeur(profondeur: u32) -> [f64; 4] {
        let angle = profondeur as f64 * 0.35; // déviation douce par niveau
        SignaturePhi::new([
            angle.cos(),
            angle.sin() * 0.5,
            0.1 * (profondeur as f64).sin(),
            0.0,
        ])
        .0
    }

    /// Récupère l'émetteur amont de la racine (point d'injection du signal).
    pub fn injecteur(&mut self) -> mpsc::Sender<Signal> {
        self.injecteur
            .take()
            .expect("injecteur déjà pris (un seul cycle d'injection)")
    }

    /// Nombre de cellules enfantes du tissu (gestation).
    pub fn taille(&self) -> usize {
        self.n_cellules
    }

    /// Récolte les états finaux des cellules à l'extinction du tissu.
    ///
    /// Attend la fin de chaque tâche de cellule (sa boucle se termine quand sa
    /// liaison amont se ferme — extinction en cascade). L'observation est
    /// **ponctuelle et immanente** : chaque `JoinHandle` livre l'état de sa
    /// cellule en fin de vie, sans registre global. Le gestateur ne route rien.
    pub async fn recolter(&mut self) -> Vec<CelluleRevenue> {
        let mut revenues: Vec<CelluleRevenue> = Vec::with_capacity(self.taches.len());
        for handle in self.taches.drain(..) {
            revenues.push(handle.await.expect("tâche de cellule en erreur"));
        }
        revenues
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // Les cellules sont spawnées (`tokio::spawn`) : un runtime Tokio est requis.
    #[tokio::test]
    async fn arbre_ternaire_taille_attendue() {
        // Profondeur 3 : 1 + 3 + 9 + 27 = 40 cellules (arbre ternaire complet).
        let tissu = Tissu::construire_arbre(3);
        assert_eq!(tissu.taille(), 40);
    }

    #[tokio::test]
    async fn arbre_ternaire_profondeur_0_est_racine_seule() {
        let tissu = Tissu::construire_arbre(0);
        assert_eq!(tissu.taille(), 1);
    }

    #[tokio::test]
    async fn arbre_profondeur_1_a_4_cellules() {
        let tissu = Tissu::construire_arbre(1);
        assert_eq!(tissu.taille(), 4);
    }
}
