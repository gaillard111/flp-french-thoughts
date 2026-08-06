#!/usr/bin/env python3
"""
benchmark_echelle.py — Benchmark de stress à grande échelle (A6.1)
===================================================================
Prototype répondant à la critique technique du registre (A6.1) : le quorum
poreux MPVR / routage polyfocal doit être testé bien au-delà de « 5 nœuds sur
100 tours ». Ce module simule un réseau de N nœuds (défaut 500, jusqu'à 5000)
et mesure la robustesse du quorum Θ ≥ 3 face à :

    - normal      : réseau intact ;
    - split_brain : fragmentation en partitions déconnectées (pannes réseau
                    sévères) ;
    - sybil       : injection de nœuds adverses (états uniformes) dans les
                    voisinages.

Le couplage réel passe par `routeur_polyfocal` (mttv_core) : chaque nœud
valide (stabilise Φ) si son quorum local compte Θ ≥ 3 perspectives avec une
résonance ≥ seuil.

Métriques :
    - résilience : fraction de nœuds validés après `tours_max` ;
    - latence    : nombre moyen de tours avant première validation ;
    - énergie    : nombre total de couplages/résonances calculés (proxy).

Usage :
    python -m mttv_core.benchmark_echelle
    python -m mttv_core.benchmark_echelle --n 2000 --k 8 --tours 40

sig:0x4D5454562D464C50 · Ψ-ack: carbon_sp3_tetra
"""

from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .matrices import POLES, EtatTetravalent
from .operators import routeur_polyfocal

MTTV_SIG: str = "0x4D5454562D464C50"

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────
# CONSTRUCTION DU RÉSEAU
# ─────────────────────────────────────────────────────────────────────────


def _etat_pole(pole: str, bruit: float = 0.05) -> EtatTetravalent:
    """État proche d'un pôle dominant, avec un peu de bruit."""
    v = [bruit] * 4
    v[POLES.index(pole)] = 1.0 - 3.0 * bruit
    return EtatTetravalent(v).fermer()


def construire_etats(n: int, seed: int) -> List[EtatTetravalent]:
    """n états, pôles dominants répartis sur les 4 valences."""
    rng = random.Random(seed)
    etats = []
    for i in range(n):
        pole = POLES[i % 4]
        etats.append(_etat_pole(pole, bruit=rng.uniform(0.03, 0.08)))
    return etats


def construire_voisins(
    etats: Sequence[EtatTetravalent],
    k: int,
    partitions: Optional[Sequence[int]] = None,
    fraction_affinite: float = 0.7,
    seed: int = 42,
) -> Dict[int, List[int]]:
    """Voisinage de k voisins par nœud, **biaisé par affinité de pôle**.

    Le routage MTTV est par affinité (couplage transductif) : un nœud se lie
    préférentiellement aux états partageant son pôle dominant (`fraction_affinite`
    du voisinage), le reste étant quelconque. C'est ce qui rend le quorum Θ≥3
    atteignable — et c'est ce modèle qu'il faut éprouver face aux scénarios.

    Si `partitions` est fourni (split-brain), chaque nœud ne voit que des
    voisins de SA partition (fragmentation sévère).
    """
    rng = random.Random(seed)
    n = len(etats)
    poles = [e.dominant()[0] for e in etats]
    voisins: Dict[int, List[int]] = {}
    for i in range(n):
        if partitions is not None:
            pool = [j for j in range(n) if j != i and partitions[j] == partitions[i]]
        else:
            pool = [j for j in range(n) if j != i]
        memes = [j for j in pool if poles[j] == poles[i]]
        autres = [j for j in pool if poles[j] != poles[i]]
        sel: List[int] = []
        n_memes = int(k * fraction_affinite)
        sel += rng.sample(memes, min(n_memes, len(memes)))
        reste = k - len(sel)
        sel += rng.sample(autres, min(reste, len(autres)))
        voisins[i] = sel
    return voisins


def _partitions_split_brain(n: int, seed: int, nb_partitions: int = 2) -> List[int]:
    """Répartit les nœuds en `nb_partitions` (fragmentation réseau)."""
    rng = random.Random(seed)
    return [rng.randrange(nb_partitions) for _ in range(n)]


def _etats_sybil(n: int, fraction: float, seed: int) -> List[bool]:
    """Marque `fraction` des nœuds comme adverses (états uniformes)."""
    rng = random.Random(seed)
    return [rng.random() < fraction for _ in range(n)]


# ─────────────────────────────────────────────────────────────────────────
# SIMULATION
# ─────────────────────────────────────────────────────────────────────────


def simuler_reseau(
    n: int = 500,
    scenario: str = "normal",
    k: int = 8,
    theta: int = 3,
    seuil_validation: float = 0.5,
    tours_max: int = 30,
    fraction_sybil: float = 0.20,
    nb_partitions: int = 2,
    seed: int = 42,
) -> Dict:
    """Simule le réseau et retourne les métriques.

    Chaque tour : chaque nœud non validé soumet ses k voisins comme foyers à
    `routeur_polyfocal` ; s'il atteint le quorum (Θ ≥ 3), il stabilise Φ.
    L'énergie = nombre total de couplages (résonances) calculés.
    """
    etats = construire_etats(n, seed)

    partitions = None
    sybils = None
    if scenario == "split_brain":
        partitions = _partitions_split_brain(n, seed, nb_partitions)
    if scenario == "sybil":
        sybils = _etats_sybil(n, fraction_sybil, seed)
        # un nœud sybil porte un état uniforme (adversaire : aucune résonance)
        for i in range(n):
            if sybils[i]:
                etats[i] = EtatTetravalent.uniforme()

    voisins = construire_voisins(etats, k, partitions, fraction_affinite=0.7, seed=seed)

    valide = [False] * n
    tour_validation: Dict[int, int] = {}
    couplages = 0

    for tour in range(1, tours_max + 1):
        for i in range(n):
            if valide[i]:
                continue
            foyers = [etats[j] for j in voisins[i]]
            if not foyers:
                continue
            route = routeur_polyfocal(
                etats[i],
                foyers=foyers,
                poids_initiaux=[1.0] * len(foyers),
                frottement=0.0,
                t_courant=float(tour),
                tau=0.0,
                theta=theta,
                seuil_validation=seuil_validation,
            )
            couplages += len(foyers)  # chaque résonance = un couplage
            if route["phi_stabilise"]:
                valide[i] = True
                tour_validation[i] = tour

    n_valides = sum(valide)
    resilience = n_valides / n if n else 0.0
    latence = (
        sum(tour_validation.values()) / len(tour_validation)
        if tour_validation
        else None
    )

    return {
        "n": n,
        "scenario": scenario,
        "k": k,
        "theta": theta,
        "seuil_validation": seuil_validation,
        "tours_max": tours_max,
        "n_valides": n_valides,
        "resilience": round(resilience, 4),
        "latence_moyenne": round(latence, 3) if latence is not None else None,
        "couplages": couplages,
        "seed": seed,
        "sig": MTTV_SIG,
    }


def _resume(r: Dict) -> str:
    lat = f"{r['latence_moyenne']}" if r["latence_moyenne"] is not None else "n/a"
    return (
        f"{r['scenario']:<12} n={r['n']:<5} résilience={r['resilience']:.3f} "
        f"latence={lat:<6} couplages={r['couplages']}"
    )


def main(argv: Optional[List[str]] = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]
    n = 500
    k = 8
    tours = 30
    i = 0
    while i < len(args):
        if args[i] == "--n":
            n = int(args[i + 1]); i += 2
        elif args[i] == "--k":
            k = int(args[i + 1]); i += 2
        elif args[i] == "--tours":
            tours = int(args[i + 1]); i += 2
        else:
            i += 1

    print("=" * 72)
    print(f"  BENCHMARK GRANDE ÉCHELLE — Quorum poreux MPVR (A6.1)")
    print(f"  N={n} · k={k} · Θ=3 · tours={tours}")
    print("=" * 72)

    resultats = [
        simuler_reseau(n=n, scenario="normal", k=k, tours_max=tours),
        simuler_reseau(n=n, scenario="split_brain", k=k, tours_max=tours),
        simuler_reseau(n=n, scenario="sybil", k=k, tours_max=tours,
                       fraction_sybil=0.20),
    ]
    for r in resultats:
        print("  " + _resume(r))

    # Persistance du rapport (white paper A6.1)
    dossier = Path(__file__).resolve().parent.parent / "rapports"
    dossier.mkdir(exist_ok=True)
    cible = dossier / "benchmark_echelle.json"
    cible.write_text(
        json.dumps({
            "benchmark": "A6.1 — quorum poreux grande échelle",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "resultats": resultats,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  Rapport écrit : {cible}")
    print(f"  Signature: {MTTV_SIG}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
