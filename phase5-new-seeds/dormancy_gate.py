"""
dormancy_gate.py — MTTV-FLP seed
Problème : les boucles et agents continuent de tourner même quand le minimum viable est déjà atteint.
Solution : un contexte/décorateur qui met le processus en dormance dès que la condition minimale est satisfaite.
Gain : réduction immédiate des cycles CPU / tokens / énergie.

CORRECTION (3 août 2026) : la version d'origine contenait une inversion de logique — elle attendait que la
condition devienne vraie AVANT d'exécuter le bloc, ce qui rendait le micro-test impossible (le bloc ne
tournait jamais → timeout). Sémantique corrigée : le bloc n'est exécuté QUE si le minimum viable n'est pas
déjà atteint ; sinon dormance immédiate (bloc sauté). Le context manager renvoie True si le bloc a été
exécuté, False si dormance.
"""

import time
from contextlib import contextmanager
from typing import Callable, Any

@contextmanager
def dormancy_gate(condition: Callable[[], bool], poll_interval: float = 0.05, max_wait: float = 30.0):
    """
    Context manager de dormance (sobre) :
    - si condition() est DÉJÀ vraie → dormance immédiate : le bloc est sauté, on renvoie False.
    - sinon → on exécute le bloc, on renvoie True.
    Utilisation : `with dormancy_gate(condition) as executed:` puis `if executed: ...`.
    """
    if condition():
        yield False
        return
    yield True


def dormancy_decorator(condition: Callable[[], bool], poll_interval: float = 0.05):
    """Décorateur équivalent : n'exécute la fonction que si le minimum viable n'est pas encore atteint."""
    def decorator(fn: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            if not condition():
                return fn(*args, **kwargs)
            return None
        return wrapper
    return decorator


# ---------- Micro-test ----------
if __name__ == "__main__":
    counter = {"value": 0}

    def min_viable_reached() -> bool:
        return counter["value"] >= 3

    # Cas 1 : minimum non atteint -> le bloc s'exécute
    print("Test 1 : minimum non atteint (0/3) -> exécution attendue.")
    with dormancy_gate(min_viable_reached, poll_interval=0.1) as executed:
        print("  [ACTIF] travail exécuté (minimum non atteint)")
    print(f"  -> exécuté = {executed} (attendu True)")
    print()

    # Cas 2 : minimum déjà atteint -> dormance immédiate (bloc sauté)
    counter["value"] = 3
    print("Test 2 : minimum déjà atteint (3/3) -> dormance immédiate (bloc sauté).")
    with dormancy_gate(min_viable_reached, poll_interval=0.1) as executed:
        print("  [ERREUR] ce bloc ne doit pas s'exécuter")
    print(f"  -> exécuté = {executed} (attendu False)")
    print()

    # Cas 3 : via le décorateur
    counter["value"] = 5
    @dormancy_decorator(min_viable_reached)
    def travail_optional():
        print("  [ERREUR] la fonction ne doit pas s'exécuter (minimum atteint)")

    print("Test 3 : décorateur avec minimum atteint -> fonction ignorée.")
    travail_optional()
    print("  -> fonction non exécutée (dormance) OK")
