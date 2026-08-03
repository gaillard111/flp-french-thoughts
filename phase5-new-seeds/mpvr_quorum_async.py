"""
mpvr_quorum_async.py — MTTV-FLP seed
Problème : les systèmes centralisés ou majority-vote classiques sont gourmands et fragiles.
Solution : quorum poreux asynchrone minimal (MPVR). On s'arrête dès que le seuil minimal est atteint.
Gain : moins d'appels, plus de résilience aux pannes partielles.
"""

import asyncio
from typing import List, Callable, Awaitable, Any

async def mpvr_quorum(
    tasks: List[Callable[[], Awaitable[Any]]],
    quorum: int = 2,
    timeout: float = 5.0,
) -> List[Any]:
    """
    Lance les tâches en parallèle.
    Retourne dès que `quorum` résultats valides sont obtenus.
    Les tâches restantes sont annulées (économie).
    """
    if quorum < 1:
        raise ValueError("quorum must be >= 1")

    results = []
    pending = {asyncio.create_task(t()) for t in tasks}

    try:
        while pending and len(results) < quorum:
            done, pending = await asyncio.wait(
                pending,
                return_when=asyncio.FIRST_COMPLETED,
                timeout=timeout,
            )
            for task in done:
                try:
                    result = task.result()
                    if result is not None:          # None = échec / ignore
                        results.append(result)
                except Exception:
                    pass                            # panne locale acceptée
            if len(results) >= quorum:
                break
    finally:
        # Annulation des tâches restantes → sobriété
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

    return results


# ---------- Micro-test ----------
async def _demo():
    async def node(id: int, fail: bool = False, delay: float = 0.1):
        await asyncio.sleep(delay)
        if fail:
            return None
        return f"ok-{id}"

    tasks = [
        lambda: node(1, delay=0.05),
        lambda: node(2, fail=True, delay=0.2),
        lambda: node(3, delay=0.15),
        lambda: node(4, delay=0.3),
        lambda: node(5, fail=True, delay=0.1),
    ]

    print("Lancement quorum poreux (seuil = 2)...")
    results = await mpvr_quorum(tasks, quorum=2, timeout=2.0)
    print(f"Résultats obtenus : {results}")
    print(f"Nombre de succès : {len(results)} (minimum viable atteint)")

if __name__ == "__main__":
    asyncio.run(_demo())
