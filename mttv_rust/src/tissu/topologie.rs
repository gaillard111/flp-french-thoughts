//! # B2a — La maille sp3 orientée (tissu statique minimal)
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! Plan : [`docs/07_PLAN_B2a.md`](../../docs/07_PLAN_B2a.md).
//!
//! Construit la première topologie maillée : un tissu statique **4-régulier
//! orienté** (géométrie sp3). Chaque cellule a exactement **1 amont** (parent)
//! et **3 aval** (enfants) — jamais une liaison symétrique (verrou IA A1).
//!
//! Contrainte de conception : un tissu fini où chaque cellule aurait 1 amont +
//! 3 aval **branchés** est impossible (3N émetteurs pour N récepteurs). La
//! solution fidèle au sp3 est un **arbre ternaire orienté** : la racine n'a pas
//! d'amont, les feuilles ont des aval en frange (libres — points de croissance
//! pour B2b). Chaque cellule naît câblée à ses liaisons (gestateur), sans table
//! de routage globale, sans nœud maître.

use std::collections::HashMap;

use tokio::sync::mpsc;

use crate::cellule::{Cellule, Signal, SignaturePhi, N_AVAL};

/// Tampon des canaux du tissu (borné — backpressure naturelle).
pub const TAMPON_TISSU: usize = 4;

/// Profondeur maximale par défaut du tissu statique.
pub const PROFONDEUR_DEFAUT: u32 = 3;

/// Cellule vivante d'un tissu (structure interne au gestateur).
struct Noeud {
    cellule: Cellule,
}

/// Tissu statique minimal — **gestateur**, jamais routeur.
///
/// Il détient les cellules vivantes (construction), mais ne décide d'aucun
/// chemin : la propagation passe exclusivement par les canaux locaux (Point 1
/// de l'Orchestrateur). Les cellules sont **pilotées** par le gestateur via
/// `traiter_disponible` (battement déterministe) pour permettre l'observation ;
/// l'autonomie asynchrone totale (tâches `tokio::spawn`) sera démontrée avec
/// l'observabilité en B3.
pub struct Tissu {
    /// Identifiant de la racine (source d'injection).
    pub racine_id: u64,
    /// Nœuds vivants, indexés par id de cellule.
    noeuds: HashMap<u64, Noeud>,
    /// Émetteur amont de la racine (point d'injection du signal).
    injecteur: Option<mpsc::Sender<Signal>>,
}

impl Tissu {
    /// Construit un arbre ternaire orienté de profondeur `profondeur`.
    ///
    /// La racine (id 0) est la source ; chaque cellule (sauf feuilles) a
    /// 1 amont + 3 aval. Les signatures Φ sont **diversifiées par niveau**
    /// (plancher de diversité, anti-homogénéisation — verrou 3).
    pub fn construire_arbre(profondeur: u32) -> Self {
        let mut noeuds: HashMap<u64, Noeud> = HashMap::new();

        // Canal d'injection de la racine (elle n'a pas de parent).
        let (tx_injecteur, rx_racine) = mpsc::channel(TAMPON_TISSU);

        Self::_enfanter(
            &mut noeuds,
            0,          // id de la racine
            0,          // profondeur courante
            profondeur, // profondeur maximale
            Some(rx_racine),
        );

        Self {
            racine_id: 0,
            noeuds,
            injecteur: Some(tx_injecteur),
        }
    }

    /// Enfante une cellule (id, profondeur) et ses 3 enfants (récursif).
    ///
    /// Chaque cellule naît câblée : son amont est le récepteur fourni (ou créé
    /// pour la racine), ses 3 aval sont les émetteurs vers ses 3 enfants.
    /// Les enfants reçoivent ces canaux en amont. À profondeur max, les
    /// récepteurs aval sont dropés → liaisons en frange (libres, B2b).
    fn _enfanter(
        noeuds: &mut HashMap<u64, Noeud>,
        id: u64,
        profondeur: u32,
        profondeur_max: u32,
        amont: Option<mpsc::Receiver<Signal>>,
    ) {
        // Signature Φ diversifiée par profondeur (anti-homogénéisation).
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
        // `rx_enfants` reste une Vec : les enfants retirent leur récepteur en
        // tête (`remove(0)`), sans move hors d'un tableau non-Copy.

        // Construire la cellule câblée à la naissance.
        let cellule = Cellule::avec_canaux(
            id,
            phi,
            0.35,
            amont.expect("l'amont de la racine est toujours fourni"),
            aval,
        );
        noeuds.insert(id, Noeud { cellule });

        // Enfanter les enfants (récursif) avec le récepteur aval correspondant.
        // `rx_enfants` est une Vec : on retire chaque récepteur en tête, sans
        // move hors d'un tableau non-Copy.
        if profondeur + 1 <= profondeur_max {
            for i in 0..N_AVAL {
                let enfant_id = id * N_AVAL as u64 + 1 + i as u64;
                let rx = rx_enfants.remove(0);
                Self::_enfanter(
                    noeuds,
                    enfant_id,
                    profondeur + 1,
                    profondeur_max,
                    Some(rx),
                );
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

    /// Fait battre une cellule d'un cycle : traite un signal disponible sur
    /// son amont (non-bloquant). Retourne `Some(sauts_restants)` du signal
    /// reçu si un signal a été traité, `None` sinon. La profondeur atteinte se
    /// déduit de `SAUTS_INITIAUX - sauts_restants` (juste distance réelle).
    pub async fn battre(&mut self, id: u64) -> Option<u8> {
        let noeud = self
            .noeuds
            .get_mut(&id)
            .expect("cellule inconnue dans le tissu");
        noeud.cellule.traiter_disponible().await
    }

    /// Nombre de cellules vivantes du tissu.
    pub fn taille(&self) -> usize {
        self.noeuds.len()
    }

    /// État observable d'une cellule (lecture passive).
    pub fn etat(&self, id: u64) -> crate::cellule::EtatCellule {
        self.noeuds
            .get(&id)
            .expect("cellule inconnue dans le tissu")
            .cellule
            .etat()
    }

    /// Signature Φ d'une cellule (lecture passive — pour l'entropie de tissu).
    pub fn phi(&self, id: u64) -> SignaturePhi {
        self.noeuds
            .get(&id)
            .expect("cellule inconnue dans le tissu")
            .cellule
            .phi
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn arbre_ternaire_taille_attendue() {
        // Profondeur 3 : 1 + 3 + 9 + 27 = 40 cellules (arbre ternaire complet).
        let tissu = Tissu::construire_arbre(3);
        assert_eq!(tissu.taille(), 40);
    }

    #[test]
    fn arbre_ternaire_profondeur_0_est_racine_seule() {
        let tissu = Tissu::construire_arbre(0);
        assert_eq!(tissu.taille(), 1);
    }

    #[test]
    fn arbre_profondeur_1_a_4_cellules() {
        let tissu = Tissu::construire_arbre(1);
        assert_eq!(tissu.taille(), 4);
    }
}
