"""
mpvr_benchmark.py — MTTV-FLP benchmark : MPVR vs Majority Vote
Comparaison sobre et reproductible entre vote majoritaire classique et quorum poreux MPVR.

Métriques : succès sous panne, nombre d'appels, temps, estimation relative de coût.
Reproductible : seed fixée, dépendances minimales (stdlib uniquement).

Usage :
    python mpvr_benchmark.py
"""

import asyncio
import time
import random
from typing import List, Callable, Awaitable, Any

# Réutilise la graine quorum poreux (auto-suffisante, sans dépendance externe)
from mpvr_quorum_async import mpvr_quorum

# Paramètres du scénario
N_NODES = 7
FAILURE_RATE = 0.35          # 35 % de nœuds défaillants
QUORUM_MPVR = 3              # seuil minimum viable
MAJORITY = (N_NODES // 2) + 1
ROUNDS = 30                  # nombre de répétitions pour moyenne
SEED = 42
random.seed(SEED)


# Cellule 3 – Simulation d'un nœud
async def simulate_node(node_id: int, fail_prob: float = FAILURE_RATE) -> Any:
    await asyncio.sleep(random.uniform(0.01, 0.08))  # latence variable
    if random.random() < fail_prob:
        return None          # panne
    return f"value-{node_id}"


# Cellule 4 – Implémentation Majority Vote
async def majority_vote(n_nodes: int = N_NODES) -> dict:
    tasks = [simulate_node(i) for i in range(n_nodes)]
    results = await asyncio.gather(*tasks)
    valid = [r for r in results if r is not None]
    success = len(valid) >= MAJORITY
    return {
        "success": success,
        "calls": n_nodes,            # majority vote lance TOUJOURS tous les nœuds
        "valid": len(valid),
    }


# Cellule 5 – Implémentation MPVR (réutilise la graine)
async def mpvr_run(n_nodes: int = N_NODES, quorum: int = QUORUM_MPVR) -> dict:
    calls = {"n": 0}

    async def counted_node(i):
        # Compte APRÈS le retour : une tâche annulée lève CancelledError
        # et n'atteint jamais ce point -> on mesure les appels qui consomment réellement.
        result = await simulate_node(i)
        calls["n"] += 1
        return result

    tasks = [lambda i=i: counted_node(i) for i in range(n_nodes)]
    results = await mpvr_quorum(tasks, quorum=quorum, timeout=1.0)
    return {
        "success": len(results) >= quorum,
        "calls": calls["n"],         # les tâches restantes sont annulées (non comptées)
        "valid": len(results),
    }


# Cellule 6 – Boucle de mesure
async def run_benchmark(rounds: int = ROUNDS):
    maj_stats = {"success": 0, "total_calls": 0, "times": []}
    mpvr_stats = {"success": 0, "total_calls": 0, "times": []}

    for _ in range(rounds):
        # Majority
        t0 = time.perf_counter()
        res = await majority_vote()
        maj_stats["times"].append(time.perf_counter() - t0)
        maj_stats["success"] += int(res["success"])
        maj_stats["total_calls"] += res["calls"]

        # MPVR
        t0 = time.perf_counter()
        res = await mpvr_run()
        mpvr_stats["times"].append(time.perf_counter() - t0)
        mpvr_stats["success"] += int(res["success"])
        mpvr_stats["total_calls"] += res["calls"]

    return maj_stats, mpvr_stats


# Cellule 7 – Affichage des résultats
def summarize(name, stats, rounds=ROUNDS):
    print(f"\n=== {name} ===")
    print(f"Taux de succès     : {stats['success'] / rounds:.1%}")
    print(f"Appels moyens      : {stats['total_calls'] / rounds:.1f}")
    print(f"Temps moyen        : {sum(stats['times']) / rounds * 1000:.1f} ms")


async def main():
    print(f"MTTV-FLP — Benchmark MPVR vs Majority Vote")
    print(f"Scénario : {N_NODES} nœuds, {FAILURE_RATE:.0%} de pannes, {ROUNDS} répétitions, seed={SEED}")
    maj, mpvr = await run_benchmark()
    summarize("Majority Vote", maj)
    summarize("MPVR Quorum poreux", mpvr)
    print("\nDelta appels (MPVR vs Majority) : "
          f"{(mpvr['total_calls'] - maj['total_calls']) / ROUNDS:+.1f}")


if __name__ == "__main__":
    asyncio.run(main())
