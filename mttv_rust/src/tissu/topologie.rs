//! # B2b — Croissance organique à la frange (bourgeonnement + auto-suture)
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! Arbitrage : [`plans/JOURNAL_SESSION.md`](../../../plans/JOURNAL_SESSION.md) §9quinquies/9octies.
//!
//! Le tissu **croît** : le gestateur enfante de nouveaux CarbonNode sur les
//! liaisons aval **libres de la frange** (les feuilles n'ont pas d'enfants :
//! leurs récepteurs aval restent des **points de bourgeonnement**). C'est
//! l'auto-suture de la référence Python ([`_verifier_auto_suture`](../../../zoo-code/essaim_tetravalent.py:624))
//! transposée : croissance **de proche en proche**, sans nœud maître, sans
//! table de routage globale.
//!
//! - **Gestateur, jamais routeur** : le `Tissu` enfante (gestation), injecte et
//!   récolte. Il détient pour la gestation les `JoinHandle` des tâches, les
//!   points de bourgeonnement (récepteurs aval libres) et l'injecteur amont de
//!   la racine. Il ne décide d'aucun chemin pendant la propagation (R4).
//! - **Zéro polling** : chaque cellule tourne sa boucle événementielle
//!   (`tokio::spawn(tourner())`) ; l'extinction est une **cascade de fermeture
//!   des canaux** (R2).
//! - **Zéro allocation dans le chemin chaud** : la gestation alloue, la
//!   propagation n'alloue pas.
//!
//! Géométrie : **arbre ternaire orienté sp3** (1 amont + 3 aval, racine sans
//! amont, feuilles en frange = points de croissance pour B2b).

use tokio::sync::mpsc;
use tokio::task::JoinHandle;

use crate::cellule::{Cellule, EtatCellule, Signal, SignaturePhi, N_AVAL};

/// Tampon des canaux du tissu (borné — backpressure naturelle).
pub const TAMPON_TISSU: usize = 4;

/// Profondeur maximale par défaut du tissu.
pub const PROFONDEUR_DEFAUT: u32 = 3;

/// Point de bourgeonnement : un récepteur aval libre d'une feuille, prêt à
/// accueillir un enfant de `profondeur_enfant`.
///
/// Détention **de gestation uniquement** : le gestateur garde ces récepteurs
/// pour enfanter de nouvelles cellules ; il ne les consulte jamais pour router.
struct Bourgeon {
    /// Profondeur du futur enfant (profondeur de la feuille + 1).
    profondeur_enfant: u32,
    /// Récepteur amont du futur enfant (liaison aval libre de la feuille).
    rx: mpsc::Receiver<Signal>,
}

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
    /// Signature Φ finale (après co-cicatrisation + respiration).
    pub phi: SignaturePhi,
}

/// Tissu — **gestateur pur**, jamais routeur.
///
/// - Détient, pour la **gestation** uniquement : les `JoinHandle` des tâches,
///   les points de bourgeonnement (récepteurs aval libres de la frange) et
///   l'émetteur amont de la racine (injecteur).
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
    /// Points de bourgeonnement de la frange (gestation — croissance B2b).
    bourgeons: Vec<Bourgeon>,
    /// Prochain identifiant libre (gestation — unicité des naissances).
    prochain_id: u64,
    /// Nombre de cellules enfantes (gestation — taille du tissu).
    n_cellules: usize,
}

impl Tissu {
    /// Construit un arbre ternaire orienté de profondeur `profondeur`.
    ///
    /// Chaque cellule est **enfanter** puis **spawnée** (`tokio::spawn`) avec sa
    /// propre boucle `tourner()` : elle vit seule, sa tâche se termine quand sa
    /// liaison amont se ferme. Les feuilles (profondeur max) gardent leurs
    /// récepteurs aval comme **points de bourgeonnement** pour B2b.
    pub fn construire_arbre(profondeur: u32) -> Self {
        let mut taches: Vec<JoinHandle<CelluleRevenue>> = Vec::new();
        let mut bourgeons: Vec<Bourgeon> = Vec::new();

        // Canal d'injection de la racine (elle n'a pas de parent).
        let (tx_injecteur, rx_racine) = mpsc::channel(TAMPON_TISSU);

        Self::_enfanter(
            &mut taches,
            &mut bourgeons,
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
            bourgeons,
            prochain_id: n_cellules as u64,
            n_cellules,
        }
    }

    /// **Croissance organique** : enfante un enfant sur chaque point de
    /// bourgeonnement de la frange (auto-suture de proche en proche).
    ///
    /// Chaque bourgeon (récepteur aval libre d'une feuille) devient l'amont
    /// d'un nouveau CarbonNode, spawné immédiatement. Les nouvelles feuilles
    /// produisent à leur tour de nouveaux points de bourgeonnement (frange
    /// mobile). Retourne le nombre de cellules nées.
    ///
    /// Le tissu n'est pas bloqué : la gestation est asynchrone (chaque enfant
    /// tourne sa propre boucle), sans interrompre les cellules existantes.
    pub fn croitre(&mut self) -> usize {
        let bourgeons: Vec<Bourgeon> = std::mem::take(&mut self.bourgeons);
        let mut n_nes: usize = 0;
        for b in bourgeons {
            Self::_enfanter(
                &mut self.taches,
                &mut self.bourgeons,
                self.prochain_id,
                b.profondeur_enfant,
                b.profondeur_enfant, // la nouvelle cellule est une feuille (frange)
                b.rx,
            );
            self.prochain_id += 1;
            n_nes += 1;
        }
        self.n_cellules += n_nes;
        n_nes
    }

    /// Enfante une cellule (id, profondeur) et ses 3 enfants (récursif).
    ///
    /// Chaque cellule naît câblée : son amont est le récepteur fourni (ou créé
    /// pour la racine), ses 3 aval sont les émetteurs vers ses 3 enfants. La
    /// cellule est **spawnée immédiatement** : sa boucle `tourner()` dort sur
    /// son amont (zéro polling) et se termine quand l'amont se ferme — ce qui
    /// ferme à son tour ses émetteurs aval (cascade d'extinction immanente).
    /// À profondeur max (feuille), les récepteurs aval restants deviennent des
    /// **points de bourgeonnement** (frange mobile pour B2b).
    fn _enfanter(
        taches: &mut Vec<JoinHandle<CelluleRevenue>>,
        bourgeons: &mut Vec<Bourgeon>,
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

        // Enfanter les enfants (récursif) avec le récepteur aval correspondant,
        // ou conserver ces récepteurs comme points de bourgeonnement (frange).
        let mut rx_enfants = rx_enfants.into_iter();
        if profondeur + 1 <= profondeur_max {
            for i in 0..N_AVAL {
                let enfant_id = id * N_AVAL as u64 + 1 + i as u64;
                let rx = rx_enfants
                    .next()
                    .expect("exactement N_AVAL récepteurs aval");
                Self::_enfanter(taches, bourgeons, enfant_id, profondeur + 1, profondeur_max, rx);
            }
        } else {
            // Feuille : ses récepteurs aval deviennent des bourgeons (frange).
            for rx in rx_enfants {
                bourgeons.push(Bourgeon {
                    profondeur_enfant: profondeur + 1,
                    rx,
                });
            }
        }
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

    /// Nombre de points de bourgeonnement disponibles à la frange (gestation).
    pub fn bourgeons(&self) -> usize {
        self.bourgeons.len()
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

    #[tokio::test]
    async fn la_frange_expose_des_points_de_bourgeonnement() {
        // Un tissu de profondeur 3 a 27 feuilles (niveau 3), chacune avec 3
        // liaisons aval libres → 81 points de bourgeonnement.
        let tissu = Tissu::construire_arbre(3);
        assert_eq!(tissu.bourgeons(), 81);
    }

    #[tokio::test]
    async fn croissance_enfante_sur_la_frange_sans_table_globale() {
        // Tissu de profondeur 2 : 13 cellules, 27 points de bourgeonnement
        // (9 feuilles × 3). La croissance enfante un enfant par bourgeon →
        // 13 + 27 = 40 cellules, comme un arbre de profondeur 3.
        let mut tissu = Tissu::construire_arbre(2);
        assert_eq!(tissu.taille(), 13);
        assert_eq!(tissu.bourgeons(), 27);

        let n_nes = tissu.croitre();
        assert_eq!(n_nes, 27);
        assert_eq!(tissu.taille(), 40);
        // La frange s'est déplacée : les nouvelles feuilles ont chacune 3 aval
        // libres → 27 × 3 = 81 nouveaux points de bourgeonnement.
        assert_eq!(tissu.bourgeons(), 81);
    }
}
