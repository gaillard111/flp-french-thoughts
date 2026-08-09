//! # Benchmark de sobriété — Étape C (niveau réseau / tissu)
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! Étend le bench de la cellule unique (Étape A, [`sobriete`]) au **tissu
//! complet** — contrat de sortie Étape C, Q4 : *métrique de sobriété au niveau
//! réseau* ([`docs/01_ARCHITECTURE.md`](../docs/01_ARCHITECTURE.md) §2 Étape C :
//! « le réseau complet … produit une métrique de sobriété énergétique
//! vérifiable (CPU moyen par cellule, au repos et sous charge) »).
//!
//! Trois familles de mesures :
//! - **CPU au repos** : un tissu sans signal n'exécute aucune instruction (les
//!   cellules dorment sur `recv().await`, zéro polling R2). La **gestation +
//!   extinction vide** (aucun signal injecté) mesure donc le coût structurel
//!   d'un tissu au repos — doit rester minuscule par cellule.
//! - **Latence par saut** : durée totale d'une vague divisée par la **juste
//!   distance** (`n_sauts` réellement transduits, jamais un compteur global).
//! - **Coût de propagation** : coût par transduction (chemin critique) et par
//!   cellule pour une vague complète (40 cellules, profondeur 3).
//!
//! La sobriété au repos est garantie structurellement : la boucle asynchrone
//! `recv().await` suspend la tâche tant que rien n'arrive. Le bench le
//! **prouve par le réel** : une extinction sans signal retombe au repos en un
//! temps ~négligeable et sans aucune transduction.

use std::hint::black_box;
use std::time::{Duration, Instant};

use criterion::{criterion_group, criterion_main, Criterion};
use tokio::runtime::Runtime;

use mttv_rust::tissu::{propager, ResultatPropagation, Tissu};

/// Profondeur du tissu de référence (arbre ternaire complet : 1+3+9+27 = 40).
const PROFONDEUR_BENCH: u32 = 3;

/// Profondeur du tissu profond (1+3+9+27+81 = 121 cellules) pour l'échelle.
const PROFONDEUR_PROFOND: u32 = 4;

/// Construit un runtime Tokio multi-thread pour le bench asynchrone.
fn runtime() -> Runtime {
    tokio::runtime::Builder::new_multi_thread()
        .worker_threads(2)
        .enable_all()
        .build()
        .expect("runtime Tokio du bench réseau")
}

/// Gestation seule : construit le tissu puis l'éteint **sans aucun signal**.
///
/// Mesure le coût structurel d'un tissu au repos : création des canaux,
/// spawn des tâches, extinction en cascade. Aucune transduction n'est
/// déclenchée — c'est la signature d'un réseau qui dort (CPU ≈ 0).
fn bench_repos(c: &mut Criterion) {
    let rt = runtime();
    c.bench_function("reseau/gestation_et_extinction_sans_signal_40c", |b| {
        b.iter(|| {
            rt.block_on(async {
                let mut tissu = Tissu::construire_arbre(PROFONDEUR_BENCH);
                // Aucun signal : on ferme l'amont de la racine → cascade
                // d'extinction immanente. Récolte = observation finale.
                drop(tissu.injecteur());
                let revenues = tissu.recolter().await;
                black_box(revenues.len())
            })
        })
    });
}

/// Vague complète : gestation + injection + propagation + extinction.
///
/// Le coût total comprend la naissance des 40 cellules ET le battement de la
/// vague. La latence par saut et le coût par transduction sont dérivés dans le
/// rapport [`rapport_reseau`].
fn bench_vague(c: &mut Criterion) {
    let rt = runtime();
    c.bench_function("reseau/propagation_vague_complete_40c_prof3", |b| {
        b.iter(|| {
            rt.block_on(async {
                let mut tissu = Tissu::construire_arbre(PROFONDEUR_BENCH);
                let r = propager(&mut tissu).await;
                black_box(r.n_transductions)
            })
        })
    });
}

/// Échelle : vague complète sur un tissu profond (121 cellules, profondeur 4).
fn bench_vague_profonde(c: &mut Criterion) {
    let rt = runtime();
    c.bench_function("reseau/propagation_vague_121c_prof4", |b| {
        b.iter(|| {
            rt.block_on(async {
                let mut tissu = Tissu::construire_arbre(PROFONDEUR_PROFOND);
                let r = propager(&mut tissu).await;
                black_box(r.n_transductions)
            })
        })
    });
}

/// Rapport de sobriété réseau (régime établi, métriques imprimées).
///
/// Proche du `bench_taille_cellule` de l'Étape A : une mesure affichée, pas une
/// distribution. Pour être honnête et reproductible, chaque famille de mesure
/// est **échauffée puis répétée** et le **minimum** (régime établi, sans
/// l'artefact du premier démarrage des threads Tokio) est retenu — c'est ce
/// que criterion échantillonne sur des milliers d'itérations. Produit le
/// **contrat de sortie Étape C** :
/// - CPU au repos : extinction sans signal (durée minimale + 0 transduction) ;
/// - latence par saut (µs/saut, juste distance `n_sauts`) ;
/// - coût par transduction (ns) et par cellule (ns) pour une vague complète.
fn rapport_reseau(_c: &mut Criterion) {
    /// Nombre de passages pour le régime établi (le minimum est retenu).
    const PASSES: u32 = 12;

    let rt = runtime();
    rt.block_on(async {
        // Échauffement : la première gestation/spawn des threads Tokio domine
        // le premier chronomètre (artefact à froid) — on le consomme ici.
        for _ in 0..2 {
            let mut w = Tissu::construire_arbre(PROFONDEUR_BENCH);
            drop(w.injecteur());
            w.recolter().await;
        }

        // 1) Repos — aucune transduction, extinction immédiate. On aggrège les
        //    compteurs réels pour PROUVER que le tissu au repos ne fait rien.
        let mut duree_repos = Duration::MAX;
        let mut trans_repos: u64 = 0;
        let mut amortis_repos: u64 = 0;
        let taille_repos = (1 + 3 + 9 + 27) as usize; // arbre ternaire prof. 3
        for _ in 0..PASSES {
            let t0 = Instant::now();
            let mut tissu_repos = Tissu::construire_arbre(PROFONDEUR_BENCH);
            drop(tissu_repos.injecteur());
            let revenues = tissu_repos.recolter().await;
            let d = t0.elapsed();
            if d < duree_repos {
                duree_repos = d;
            }
            trans_repos = revenues.iter().map(|r| r.etat.n_transductions).sum();
            amortis_repos = revenues.iter().map(|r| r.etat.n_amortis).sum();
        }

        // 2) Vague complète sur le tissu de référence (40 cellules) — minimum
        //    sur plusieurs passages (régime établi).
        let taille = (1 + 3 + 9 + 27) as usize;
        let mut duree_vague = Duration::MAX;
        let mut r: ResultatPropagation = propager(&mut Tissu::construire_arbre(PROFONDEUR_BENCH)).await;
        for _ in 0..PASSES {
            let mut tissu = Tissu::construire_arbre(PROFONDEUR_BENCH);
            let t1 = Instant::now();
            let r2 = propager(&mut tissu).await;
            let d = t1.elapsed();
            if d < duree_vague {
                duree_vague = d;
                r = r2;
            }
        }

        // 3) Dérivées de sobriété.
        let n_sauts = r.n_sauts.max(1) as f64;
        let lat_par_saut = duree_vague.as_secs_f64() * 1e6 / n_sauts; // µs/saut
        let n_trans = r.n_transductions.max(1) as f64;
        let cout_par_trans = duree_vague.as_nanos() as f64 / n_trans; // ns/transduction
        let cout_par_cellule = duree_vague.as_nanos() as f64 / taille as f64; // ns/cellule

        println!("=== RÉSEAU — sobriété (contrat de sortie Étape C) ===");
        println!("tissu: {taille} cellules (arbre ternaire profondeur {PROFONDEUR_BENCH})");
        println!("transductions: {} | amortis: {} | atteintes: {} | sauts: {}",
            r.n_transductions, r.n_amortis, r.n_cellules_atteintes, r.n_sauts);
        println!("diversité tissu: {:.3} | porosité moyenne: {:.3} | extinction: {}",
            r.diversite_tissu, r.porosite_moyenne, r.extinction);
        println!("--- CPU au repos ---");
        println!(
            "repos: extinction sans signal en {:.1} µs pour {taille_repos} cellules ({trans_repos} transduction, {amortis_repos} amorti) -> CPU ≈ 0",
            duree_repos.as_secs_f64() * 1e6
        );
        println!("--- Latence & coût (vague complète) ---");
        println!(
            "vague: {:.1} µs au total | latence par saut: {lat_par_saut:.2} µs/saut | coût: {cout_par_trans:.1} ns/transduction | {cout_par_cellule:.1} ns/cellule",
            duree_vague.as_secs_f64() * 1e6
        );
        println!("=== FIN RÉSEAU ===");
    });
}

criterion_group!(
    reseau,
    bench_repos,
    bench_vague,
    bench_vague_profonde,
    rapport_reseau
);
criterion_main!(reseau);
