//! # Benchmark de sobriété — Étape A (cellule unique)
//!
//! **Sig** : `0x4D5454562D464C50`
//!
//! Mesure la **frugalité** du chemin critique de la cellule sp3 :
//! - latence d'un cycle d'**amortissement passif** (signal sous le seuil,
//!   CPU ≈ 0, rien n'est propagé) ;
//! - latence d'un cycle de **transduction active** (membrane poreuse) ;
//! - taille mémoire **fixe** d'une cellule (aucune allocation dynamique).
//!
//! La sobriété au repos (processeur endormi sur la liaison amont, zéro polling)
//! est garantie structurellement par la boucle asynchrone `recv().await` : une
//! cellule qui n'a rien à faire n'exécute aucune instruction.

use std::hint::black_box;

use criterion::{criterion_group, criterion_main, Criterion};
use mttv_rust::cellule::{
    transduire, IssueTransduction, Membrane, Signal, SignaturePhi,
};

fn signal_alignes() -> Signal {
    Signal {
        signature: SignaturePhi::new([1.0, 0.0, 0.0, 0.0]),
        amplitude: 0.8,
        source: 0,
        ts: 0,
    }
}

fn signal_orthogonal() -> Signal {
    Signal {
        signature: SignaturePhi::new([0.0, 1.0, 0.0, 0.0]),
        amplitude: 0.8,
        source: 0,
        ts: 0,
    }
}

fn bench_amortissement(c: &mut Criterion) {
    c.bench_function("transduction/amortie_sous_seuil", |b| {
        b.iter(|| {
            let mut phi = SignaturePhi::new([1.0, 0.0, 0.0, 0.0]);
            let mut membrane = Membrane::nouvelle(0.35);
            let s = signal_orthogonal();
            let issue =
                transduire(&mut phi, &mut membrane, black_box(&s), 7, 1);
            debug_assert_eq!(issue, IssueTransduction::Amorti);
            black_box(issue)
        })
    });
}

fn bench_transduction(c: &mut Criterion) {
    c.bench_function("transduction/active_au_dela_du_seuil", |b| {
        b.iter(|| {
            let mut phi = SignaturePhi::new([1.0, 0.0, 0.0, 0.0]);
            let mut membrane = Membrane::nouvelle(0.35);
            let s = signal_alignes();
            let issue =
                transduire(&mut phi, &mut membrane, black_box(&s), 7, 1);
            debug_assert!(matches!(issue, IssueTransduction::Propage(_)));
            black_box(issue)
        })
    });
}

fn bench_taille_cellule(_c: &mut Criterion) {
    // La cellule est une valeur de taille fixe, sans allocation dynamique :
    // la RAM par nœud est bornée et connue à la compilation.
    println!(
        "taille_memoire: cellule={} octets (fixe, sans allocation)",
        std::mem::size_of::<mttv_rust::cellule::Cellule>()
    );
    println!(
        "taille_memoire: signature_phi={} octets",
        std::mem::size_of::<SignaturePhi>()
    );
}

criterion_group!(
    sobriete,
    bench_amortissement,
    bench_transduction,
    bench_taille_cellule
);
criterion_main!(sobriete);
