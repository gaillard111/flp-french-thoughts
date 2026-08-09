//! # B2a-bis — Propagation immanente + extinction en cascade + entropie de tissu
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! Arbitrage : [`plans/JOURNAL_SESSION.md`](../../../plans/JOURNAL_SESSION.md) §9quinquies.
//! Plan : [`docs/07_PLAN_B2a.md`](../../docs/07_PLAN_B2a.md).
//!
//! La propagation est **immanente** : le gestateur injecte un signal à la
//! racine, puis **ne fait plus rien**. Chaque cellule, dans sa propre tâche
//! (`tokio::spawn(tourner())`), reçoit le signal sur sa liaison amont, le
//! transduit et le diffuse sur ses 3 liaisons aval — de proche en proche.
//!
//! - **Zéro polling** : aucune boucle d'inspection centrale (R2).
//! - **Extinction en cascade** : quand le gestateur ferme l'amont de la racine
//!   (drop de l'injecteur), la racine termine sa boucle, ferme ses 3 aval, ce
//!   qui ferme l'amont des enfants, et ainsi de suite — le tissu retombe au
//!   repos de lui-même. Le potentiel décroissant (`sauts_restants`) borne la
//!   propagation (juste distance, anti-homogénéisation).
//! - **Observation immanente** : le gestateur **récolte** l'état final de chaque
//!   cellule via son `JoinHandle` (fin de vie), jamais via un registre global.
//!
//! Aucun verrou global, aucune table de routage.

use std::time::Duration;

use crate::cellule::{Signal, SignaturePhi};

use super::topologie::{CelluleRevenue, Tissu};

/// Nombre de sauts initial d'un signal injecté (potentiel de propagation).
pub const SAUTS_INITIAUX: u8 = 8;

/// Seuil d'alerte d'entropie de tissu (fraction du max théorique).
pub const SEUIL_ALERTE_ENTROPIE: f64 = 0.98;

/// Résultat d'une propagation immanente dans le tissu.
#[derive(Clone, Copy, Debug)]
pub struct ResultatPropagation {
    /// Nombre total de transductions dans le tissu.
    pub n_transductions: u64,
    /// Nombre total de signaux amortis dans le tissu.
    pub n_amortis: u64,
    /// Nombre de cellules ayant transduit au moins une fois.
    pub n_cellules_atteintes: u64,
    /// Profondeur réellement atteinte par le signal (juste distance).
    pub n_sauts: u32,
    /// Diversité de tissu après propagation : 1 − similarité moyenne des Φ.
    /// Élevée = sain ; basse ≈ 0 = homogénéisation (alerte C4).
    pub diversite_tissu: f64,
    /// Similarité moyenne des Φ (pour l'interprétation de la diversité).
    pub sim_moyenne: f64,
    /// Porosité moyenne des membranes après propagation (B3 — homéostasie du
    /// milieu). Proche de 1.0 = le tissu est resté perméable au signal
    /// cohérent ; basse = contraction défensive (bruit/incohérence).
    pub porosite_moyenne: f64,
    /// `true` si le tissu est retombé au repos (toutes les cellules ont rendu
    /// leur état — extinction en cascade complète).
    pub extinction: bool,
}

/// Injecte un signal aligné à la racine (avec `SAUTS_INITIAUX` sauts) et
/// laisse le tissu s'irradier puis s'éteindre **de lui-même**. Retourne les
/// métriques de propagation réelles.
pub async fn propager(tissu: &mut Tissu) -> ResultatPropagation {
    propager_avec_sauts(tissu, SAUTS_INITIAUX).await
}

/// Variante paramétrée : injecte un signal avec `sauts_initiaux` sauts.
///
/// Sert au **test de juste distance réelle** : un potentiel faible doit
/// empêcher d'atteindre les profondeurs profondes (le potentiel décroissant
/// borne la propagation, pas seulement la frange de l'arbre).
pub async fn propager_avec_sauts(
    tissu: &mut Tissu,
    sauts_initiaux: u8,
) -> ResultatPropagation {
    let injecteur = tissu.injecteur();

    // Signal aligné avec la racine (Φ = [1,0,0,0], profondeur 0).
    let signal = Signal {
        signature: SignaturePhi::new([1.0, 0.0, 0.0, 0.0]),
        amplitude: 0.8,
        source: tissu.racine_id,
        ts: 0,
        sauts_restants: sauts_initiaux,
    };
    injecteur.send(signal).await.expect("injection échouée");
    // Fermer l'amont de la racine → déclenche l'extinction en cascade.
    drop(injecteur);

    // Récolte immanente : le tissu s'éteint de lui-même (chaîne de fermeture
    // des canaux de proche en proche). Un tissu qui ne s'éteint pas est un
    // bug — jamais une attente infinie (leçon B1b) : timeout de sécurité.
    let revenues: Vec<CelluleRevenue> = tokio::time::timeout(
        Duration::from_secs(10),
        tissu.recolter(),
    )
    .await
    .expect("le tissu ne s'éteint pas (deadlock — canal jamais fermé)");

    // Agréger les états finaux (observation ponctuelle de chaque cellule).
    let mut n_transductions: u64 = 0;
    let mut n_amortis: u64 = 0;
    let mut n_cellules_atteintes: u64 = 0;
    let mut profondeur_max_transduite: u32 = 0;
    let mut somme_porosite: f64 = 0.0;
    let mut phis: Vec<SignaturePhi> = Vec::with_capacity(revenues.len());

    for r in &revenues {
        n_transductions += r.etat.n_transductions;
        n_amortis += r.etat.n_amortis;
        if r.etat.n_transductions > 0 {
            n_cellules_atteintes += 1;
            profondeur_max_transduite = profondeur_max_transduite.max(r.profondeur);
        }
        somme_porosite += r.porosite;
        phis.push(r.phi);
    }
    let porosite_moyenne: f64 = if revenues.is_empty() {
        0.0
    } else {
        somme_porosite / revenues.len() as f64
    };

    // Similarité moyenne des Φ (paires) — diversité = 1 − sim.
    let n = phis.len();
    let sim_moyenne: f64 = if n > 1 {
        let mut somme = 0.0;
        let mut paires = 0.0;
        for i in 0..n {
            for j in (i + 1)..n {
                somme += phis[i].resonance(&phis[j]);
                paires += 1.0;
            }
        }
        somme / paires
    } else {
        0.0
    };

    ResultatPropagation {
        n_transductions,
        n_amortis,
        n_cellules_atteintes,
        // Juste distance = profondeur maximale réellement atteinte par une
        // transduction (équivalent à `sauts_initiaux − sauts_min` des signaux
        // transduits), mesurée via la profondeur de naissance de chaque cellule.
        n_sauts: profondeur_max_transduite,
        diversite_tissu: (1.0 - sim_moyenne).clamp(0.0, 1.0),
        sim_moyenne,
        porosite_moyenne,
        // Toutes les cellules ont rendu leur état → le tissu est au repos.
        extinction: true,
    }
}

/// Diversité de tissu : écart moyen des signatures Φ des cellules.
///
/// Référence (leçon C4) : en homogénéisation, tous les Φ sont **alignés**
/// (similarité ≈ 1.0) — c'est l'anomalie à détecter. La diversité de tissu est
/// donc `1 − similarité_moyenne` :
/// - élevée (proche de 1) → Φ diversifiés → tissu sain ;
/// - basse (proche de 0) → Φ alignés → **homogénéisation** (alerte C4).
///
/// Métrique simple, robuste, sans allocation : une seule passe sur les paires.
pub fn diversite_tissu(phis: &[SignaturePhi]) -> f64 {
    let n = phis.len();
    if n < 2 {
        return 1.0; // un seul Φ : pas d'homogénéisation possible
    }

    let mut somme_sim: f64 = 0.0;
    let mut n_paires: f64 = 0.0;
    for i in 0..n {
        for j in (i + 1)..n {
            somme_sim += phis[i].resonance(&phis[j]);
            n_paires += 1.0;
        }
    }
    let sim_moyenne: f64 = somme_sim / n_paires;
    (1.0 - sim_moyenne).clamp(0.0, 1.0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn diversite_tissu_nulle_quand_alignes() {
        // Tous les Φ alignés → homogénéisation → diversité ≈ 0 (alerte C4).
        let phis = vec![
            SignaturePhi::new([1.0, 0.0, 0.0, 0.0]),
            SignaturePhi::new([1.0, 0.0, 0.0, 0.0]),
            SignaturePhi::new([1.0, 0.0, 0.0, 0.0]),
            SignaturePhi::new([1.0, 0.0, 0.0, 0.0]),
        ];
        let d = diversite_tissu(&phis);
        assert!(d < 0.1, "alignés → diversité ~0 (homogénéisation), obtenu {d}");
    }

    #[test]
    fn diversite_tissu_elevee_quand_diversifies() {
        // Φ à directions réellement écartées (dont des signes opposés) →
        // similarités moyennes basses → diversité élevée (tissu sain).
        let phis = vec![
            SignaturePhi::new([1.0, 0.0, 0.0, 0.0]),
            SignaturePhi::new([0.0, 1.0, 0.0, 0.0]),
            SignaturePhi::new([-1.0, 0.0, 0.0, 0.0]),
            SignaturePhi::new([0.0, -1.0, 0.0, 0.0]),
        ];
        let d = diversite_tissu(&phis);
        assert!(d > 0.5, "diversifié → diversité élevée, obtenu {d}");
    }

    #[tokio::test]
    async fn rapport_des_metriques_b2a() {
        // Produit le rapport chiffré du tissu (topologie + propagation).
        // Visible avec `cargo test -- --nocapture` — la preuve du réel.
        use super::super::topologie::Tissu;

        let mut tissu = Tissu::construire_arbre(3);
        let taille = tissu.taille(); // capture AVANT propager (la récolte vide les tâches)
        let r = propager(&mut tissu).await;

        println!("=== TISSU B2a-bis — maille sp3 orientée (immanente) ===");
        println!("cellules: {} (arbre ternaire profondeur 3)", taille);
        println!(
            "transductions: {} | amortis: {} | cellules atteintes: {}",
            r.n_transductions, r.n_amortis, r.n_cellules_atteintes
        );
        println!(
            "sauts: {} | diversité tissu: {:.3} | sim moyenne: {:.3}",
            r.n_sauts, r.diversite_tissu, r.sim_moyenne
        );
        println!(
            "porosité moyenne (B3/matrice H): {:.3} | extinction: {}",
            r.porosite_moyenne, r.extinction
        );
        println!("=== FIN TISSU B2a-bis ===");
    }

    #[tokio::test]
    async fn potentiel_faible_borne_la_propagation() {
        use super::super::topologie::Tissu;

        // Tissu profond (profondeur 4 = 1+3+9+27+81 = 121 cellules). Un signal
        // avec un potentiel FAIBLE (2 sauts) ne doit PAS atteindre les niveaux
        // profonds : le potentiel décroissant borne la propagation — c'est la
        // preuve que ce n'est pas seulement la frange qui arrête (contre le
        // soupçon du conseil 1 : compteur réinitialisé/global — il ne l'est pas).
        let mut tissu = Tissu::construire_arbre(4);
        let taille = tissu.taille();
        let r = propager_avec_sauts(&mut tissu, 2).await;

        // Potentiel 2 → 1 niveau de transduction au-delà de la racine :
        // racine (reçue à 2) + 3 enfants (reçus à 1) = 4 cellules transductrices.
        // Les petits-enfants reçoivent 0 → amortis (n_sauts = 1, pas 4).
        assert_eq!(
            r.n_sauts, 1,
            "potentiel 2 → 1 niveau transduit, obtenu {}",
            r.n_sauts
        );

        // 4 cellules transduisent (racine + 3 enfants) ; le tissu de 121
        // cellules n'est pas irrigué en profondeur — la propagation est bornée.
        assert_eq!(
            r.n_cellules_atteintes, 4,
            "potentiel 2 → 4 cellules transductrices, obtenu {}",
            r.n_cellules_atteintes
        );
        assert!(
            r.n_transductions < taille as u64,
            "le potentiel doit borner ({} transductions < {} cellules)",
            r.n_transductions,
            taille
        );

        // Le potentiel est décrémenté localement (pas global) : un signal avec
        // plus de sauts va plus loin (comparé à juste_distance, n_sauts=3).
        assert!(r.extinction, "le tissu doit revenir au repos");
    }

    #[tokio::test]
    async fn poumon_de_diversite_releve_la_diversite_au_dessus_du_seuil_c4() {
        use super::super::topologie::Tissu;

        // Remède C4/C7 : la respiration locale à l'extinction doit maintenir la
        // diversité du tissu BIEN AU-DESSUS du seuil d'homogénéisation observé
        // sans respiration (diversité ≈ 0.037, sim ≈ 0.963). La valeur réelle
        // mesurée (dose 0.35) est ≈ 0.24 — marge large, preuve robuste.
        let mut tissu = Tissu::construire_arbre(3);
        let r = propager(&mut tissu).await;

        assert!(
            r.diversite_tissu > 0.037,
            "la respiration doit maintenir la diversité au-dessus du seuil C4 (0.037), obtenu {}",
            r.diversite_tissu
        );
        assert!(
            r.diversite_tissu > 0.10,
            "le Poumon de Diversité doit relever nettement la diversité (> 0.10), obtenu {}",
            r.diversite_tissu
        );
        assert!(
            r.sim_moyenne < 0.963,
            "la similarité moyenne doit redescendre sous 0.963 (anti-lissage), obtenu {}",
            r.sim_moyenne
        );
        // La propagation reste intacte : le tissu s'irradie puis s'éteint.
        assert!(r.extinction, "le tissu doit revenir au repos");
    }

    #[tokio::test]
    async fn matrice_h_porosite_adapte_et_homeostasie_du_milieu() {
        use super::super::topologie::Tissu;

        // B3 — Matrice H / homéostasie du milieu : les cellules palpent leur
        // territoire (résonance locale) et ajustent leur porosité. Face à un
        // signal cohérent (aligné), la membrane s'ouvre (résonance → porosité
        // → 1.0) : le milieu reste perméable et la propagation stable. La
        // porosité reste bornée dans [POROSITE_MIN, 1.0] (homéostasie).
        let mut tissu = Tissu::construire_arbre(3);
        let r = propager(&mut tissu).await;

        // Propagation stable face au signal : extinction et atteintes.
        assert!(
            r.n_cellules_atteintes >= 40,
            "le signal cohérent doit irradier le tissu (40), obtenu {}",
            r.n_cellules_atteintes
        );
        assert!(r.extinction, "le tissu doit revenir au repos (homéostasie)");

        // Homéostasie : porosité agrégée (métrique, pas une table globale) —
        // la membrane s'est ouverte en résonance et reste bornée dans [0,1].
        assert!(
            (0.0..=1.0).contains(&r.porosite_moyenne),
            "porosité moyenne dans [0,1], obtenue {}",
            r.porosite_moyenne
        );
        // Résonance forte → porosité ouverte (moyenne > 0.9), le milieu est
        // perméable au signal cohérent (pas de contraction par le bruit).
        assert!(
            r.porosite_moyenne > 0.9,
            "la porosité moyenne doit rester ouverte en résonance (> 0.9), obtenue {}",
            r.porosite_moyenne
        );
    }

    #[tokio::test]
    async fn croissance_b2b_preserve_le_plancher_diversite() {
        use super::super::topologie::Tissu;

        // B2b : le tissu croît à la frange (bourgeonnement), puis le signal
        // pullule dans le tissu agrandi. Grâce au Poumon de Diversité (déjà en
        // place AVANT la croissance), l'arrivée des nouvelles cellules ne doit
        // pas écraser le plancher d'entropie : diversité > 0.200 (au lieu de
        // ~0.037 sans respiration).
        let mut tissu = Tissu::construire_arbre(2); // 13 cellules
        assert_eq!(tissu.taille(), 13);

        // Croissance : une génération de bourgeons à la frange (9 feuilles × 3
        // aval = 27 nouveaux nœuds) → 40 cellules, comme un arbre de profondeur 3.
        let n_nes = tissu.croitre();
        assert_eq!(n_nes, 27);
        assert_eq!(tissu.taille(), 40);

        let r = propager(&mut tissu).await;

        // Preuve par le réel : rapport chiffré de la croissance (visible avec
        // `cargo test -- --nocapture`).
        println!("=== TISSU B2b — croissance à la frange ===");
        println!(
            "cellules: {} | transductions: {} | amortis: {} | atteintes: {}",
            tissu.taille(), r.n_transductions, r.n_amortis, r.n_cellules_atteintes
        );
        println!(
            "sauts: {} | diversité tissu: {:.3} | sim moyenne: {:.3}",
            r.n_sauts, r.diversite_tissu, r.sim_moyenne
        );
        println!("extinction: {}", r.extinction);
        println!("=== FIN TISSU B2b ===");

        // Le signal pullule dans le tissu agrandi : toutes les cellules atteintes.
        assert!(
            r.n_cellules_atteintes >= 40,
            "le signal doit atteindre le tissu agrandi (40), obtenu {}",
            r.n_cellules_atteintes
        );
        assert!(r.extinction, "le tissu agrandi doit revenir au repos");

        // Conservation de l'entropie : le plancher de diversité est maintenu
        // grâce au poumon actif (remède C4/C7), bien au-dessus du seuil 0.037.
        assert!(
            r.diversite_tissu > 0.200,
            "la croissance doit préserver le plancher de diversité (> 0.200), obtenu {}",
            r.diversite_tissu
        );
        assert!(
            r.sim_moyenne < 0.963,
            "la similarité moyenne doit rester sous 0.963 après croissance, obtenu {}",
            r.sim_moyenne
        );
    }

    #[tokio::test]
    async fn juste_distance_pullulement_puis_extinction() {
        use super::super::topologie::Tissu;

        // Tissu statique de profondeur 3 (40 cellules). Le signal injecté à la
        // racine doit pulluler de proche en proche (multi-voies) puis s'éteindre
        // par le potentiel décroissant — sans boucle, sans extinction immédiate.
        let mut tissu = Tissu::construire_arbre(3);
        let r = propager(&mut tissu).await;

        // 1. Le signal a pullulé : plusieurs cellules ont transduit.
        assert!(
            r.n_cellules_atteintes >= 4,
            "le signal doit atteindre plusieurs cellules (multi-voies), obtenu {}",
            r.n_cellules_atteintes
        );
        assert!(
            r.n_transductions >= 4,
            "plusieurs transductions attendues, obtenu {}",
            r.n_transductions
        );

        // 2. Juste distance (mesure réelle) : avec SAUTS_INITIAUX=8 et profondeur
        //    3, le signal traverse exactement 3 niveaux → n_sauts == 3. C'est la
        //    profondeur atteinte, pas le nombre de vagues de battement.
        assert_eq!(
            r.n_sauts, 3,
            "profondeur atteinte attendue = 3, obtenu {}",
            r.n_sauts
        );

        // 3. Extinction : le tissu est retombé au repos (toutes les cellules ont
        //    rendu leur état — extinction en cascade immanente).
        assert!(r.extinction, "le tissu doit revenir au repos");

        // 4. Observation documentée (leçon C4) : le tissu STATIQUE homogénéise
        //    (la co-cicatrisation aligne les Φ → diversité → 0). C'est le
        //    phénomène réel que C4 détecte dans le Python — l'anti-homogénéisation
        //    ACTIVE (respiration de diversité) sera le verrou de B3. On mesure
        //    et on documente, on n'asserte pas un succès d'anti-homogénéisation.
        assert!(
            (0.0..=1.0).contains(&r.diversite_tissu),
            "diversité de tissu dans [0,1], obtenu {}",
            r.diversite_tissu
        );
        assert!(
            (0.0..=1.0).contains(&r.sim_moyenne),
            "similarité moyenne dans [0,1], obtenu {}",
            r.sim_moyenne
        );
    }
}
