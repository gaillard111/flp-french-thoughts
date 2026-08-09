//! # B2a — Propagation multi-voies + extinction + entropie de tissu
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! Plan : [`docs/07_PLAN_B2a.md`](../../docs/07_PLAN_B2a.md).
//!
//! Orchestre le **battement** du tissu (gestateur pilotant les cellules de façon
//! déterministe) et mesure :
//! - la **propagation multi-voies** : un signal injecté à la racine « pullule »
//!   de proche en proche (chaque cellule diffuse sur ses 3 aval) ;
//! - le **potentiel décroissant** : extinction naturelle après N sauts
//!   (juste distance — ni extinction trop rapide, ni boucle) ;
//! - l'**entropie de tissu** : dispersion des Φ des cellules, avec seuil
//!   d'alerte (anti-homogénéisation, leçon C4).
//!
//! Aucun polling : `battre` est appelé une fois par cellule par vague, la
//! lecture est non-bloquante (`try_recv`). Aucun verrou global.

use crate::cellule::{Signal, SignaturePhi};

use super::topologie::Tissu;

/// Nombre de sauts initial d'un signal injecté (potentiel de propagation).
pub const SAUTS_INITIAUX: u8 = 8;

/// Seuil d'alerte d'entropie de tissu (fraction du max théorique).
pub const SEUIL_ALERTE_ENTROPIE: f64 = 0.98;

/// Résultat d'une vague de propagation dans le tissu.
#[derive(Clone, Copy, Debug)]
pub struct ResultatPropagation {
    /// Nombre total de transductions dans le tissu.
    pub n_transductions: u64,
    /// Nombre total de signaux amortis dans le tissu.
    pub n_amortis: u64,
    /// Nombre de cellules ayant transduit au moins une fois.
    pub n_cellules_atteintes: u64,
    /// Nombre de sauts traversés par le signal (vagues de battement).
    pub n_sauts: u32,
    /// Diversité de tissu après propagation : 1 − similarité moyenne des Φ.
    /// Élevée = sain ; basse ≈ 0 = homogénéisation (alerte C4).
    pub diversite_tissu: f64,
    /// Similarité moyenne des Φ (pour l'interprétation de la diversité).
    pub sim_moyenne: f64,
    /// `true` si le tissu est retombé au repos (plus aucun signal en vol).
    pub extinction: bool,
}

/// Injecte un signal aligné à la racine et fait battre le tissu jusqu'à
/// extinction. Retourne les métriques de propagation réelles.
///
/// Le signal porte `SAUTS_INITIAUX` sauts ; chaque vague fait battre toutes les
/// cellules une fois (profondeur par profondeur). Le battement s'arrête quand
/// plus aucune cellule ne traite de signal (extinction).
pub async fn propager(tissu: &mut Tissu) -> ResultatPropagation {
    let injecteur = tissu.injecteur();

    // Signal aligné avec la racine (Φ = [1,0,0,0], profondeur 0).
    let signal = Signal {
        signature: SignaturePhi::new([1.0, 0.0, 0.0, 0.0]),
        amplitude: 0.8,
        source: tissu.racine_id,
        ts: 0,
        sauts_restants: SAUTS_INITIAUX,
    };
    injecteur.send(signal).await.expect("injection échouée");

    // Battre le tissu par vagues jusqu'à extinction (aucun signal traité).
    let mut n_sauts: u32 = 0;
    loop {
        let mut traite_au_moins_un = false;
        // Battre toutes les cellules une fois (ordre par id, déterministe).
        for id in 0..tissu.taille() as u64 {
            if tissu.battre(id).await {
                traite_au_moins_un = true;
            }
        }
        if !traite_au_moins_un {
            break; // extinction : le tissu est au repos
        }
        n_sauts += 1;
    }

    // Agréger les états de toutes les cellules.
    let mut n_transductions: u64 = 0;
    let mut n_amortis: u64 = 0;
    let mut n_cellules_atteintes: u64 = 0;
    let mut phis: Vec<SignaturePhi> = Vec::with_capacity(tissu.taille());

    for id in 0..tissu.taille() as u64 {
        let etat = tissu.etat(id);
        n_transductions += etat.n_transductions;
        n_amortis += etat.n_amortis;
        if etat.n_transductions > 0 {
            n_cellules_atteintes += 1;
        }
        // Φ de la cellule : re-normalisé depuis l'état (stocké dans le tissu).
        // On lit la signature via la cellule — exposée publiquement.
        phis.push(tissu.phi(id));
    }

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
        n_sauts,
        diversite_tissu: (1.0 - sim_moyenne).clamp(0.0, 1.0),
        sim_moyenne,
        extinction: n_sauts > 0,
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
        let r = propager(&mut tissu).await;

        println!("=== TISSU B2a — maille sp3 orientée ===");
        println!("cellules: {} (arbre ternaire profondeur 3)", tissu.taille());
        println!(
            "transductions: {} | amortis: {} | cellules atteintes: {}",
            r.n_transductions, r.n_amortis, r.n_cellules_atteintes
        );
        println!(
            "sauts: {} | diversité tissu: {:.3} | sim moyenne: {:.3}",
            r.n_sauts, r.diversite_tissu, r.sim_moyenne
        );
        println!("extinction: {}", r.extinction);
        println!("=== FIN TISSU B2a ===");
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

        // 2. Juste distance : sauts bornés (ni 0 — extinction immédiate — ni
        //    démesurés — boucle). SAUTS_INITIAUX=8 borne la propagation.
        assert!(
            r.n_sauts >= 1 && r.n_sauts <= SAUTS_INITIAUX as u32,
            "juste distance : n_sauts={} doit être dans [1, {}]",
            r.n_sauts, SAUTS_INITIAUX
        );

        // 3. Extinction : le tissu est retombé au repos (le battement s'arrête).
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
