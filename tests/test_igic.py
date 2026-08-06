#!/usr/bin/env python3
"""
test_igic.py — Tests du calcul IGIC + modulation A3 (A1.2)
===========================================================
Vérifie le calcul contre les scénarios de référence du prototype
ouroboros-mttv-v2.py :
    A=(2,2,2,2,1,2) → standard 0.738 ; A3=1 → 0.738 ; A3=7 → 0.369
    C=(4,3,4,3,4,3) → standard 0.500 ; A3=4 → 0.375

Usage :
    python tests/test_igic.py
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mttv_core import (  # noqa: E402
    MTTV_SIG,
    calculer_igic,
    diagnostic_igic,
    facteur_protection_a3,
    igic_module,
)

RESULTATS: list = []


def verifie(nom: str, condition: bool, detail: str = "") -> bool:
    RESULTATS.append((nom, bool(condition), detail))
    statut = "OK  " if condition else "FAIL"
    print(f"[{statut}] {nom}" + (f" — {detail}" if detail else ""))
    return bool(condition)


def test_scenarios_reference() -> None:
    # Scénario A (asynchrone pur) : standard 0.738, A3=1 → 0.738
    std_a = calculer_igic(2, 2, 2, 2, 1, 2)
    mod_a1 = igic_module(2, 2, 2, 2, 1, 2, A3=1)
    verifie("IGIC : scénario A standard = 0.738",
            abs(std_a - 0.738) < 1e-3, f"std={std_a}")
    verifie("IGIC : A3=1 → modulation 0.738 (aucun abattement)",
            abs(mod_a1 - 0.738) < 1e-3, f"mod={mod_a1}")

    # Scénario B (dogmatique) : A3=7 → 0.369
    mod_a7 = igic_module(2, 2, 2, 2, 1, 2, A3=7)
    verifie("IGIC : A3=7 → modulation 0.369 (abattement 50 %)",
            abs(mod_a7 - 0.369) < 1e-3, f"mod={mod_a7}")

    # Scénario C (hybride) : standard 0.500, A3=4 → 0.375
    std_c = calculer_igic(4, 3, 4, 3, 4, 3)
    mod_c = igic_module(4, 3, 4, 3, 4, 3, A3=4)
    verifie("IGIC : scénario C standard = 0.500",
            abs(std_c - 0.500) < 1e-3, f"std={std_c}")
    verifie("IGIC : A3=4 → modulation 0.375",
            abs(mod_c - 0.375) < 1e-3, f"mod={mod_c}")

    # Facteur de protection : A3=1 → 1.0 ; A3=7 → 0.5
    verifie("IGIC : facteur A3=1 → 1.0",
            abs(facteur_protection_a3(1) - 1.0) < 1e-4)
    verifie("IGIC : facteur A3=7 → 0.5",
            abs(facteur_protection_a3(7) - 0.5) < 1e-4)


def test_diagnostic() -> None:
    verifie("IGIC : 0.738 → bonne résonance",
            diagnostic_igic(0.738).startswith("BONNE RÉSONANCE"))
    verifie("IGIC : 0.500 → intégration partielle",
            diagnostic_igic(0.500).startswith("INTÉGRATION PARTIELLE"))
    verifie("IGIC : 0.369 → désalignement/solipsisme",
            diagnostic_igic(0.369).startswith("DÉSALIGNEMENT"))


def main() -> int:
    print(f"mttv-core — IGIC + modulation A3 (A1.2)   (sig:{MTTV_SIG})")
    print("=" * 72)
    test_scenarios_reference()
    test_diagnostic()
    print("=" * 72)
    nb_ok = sum(1 for _, ok, _ in RESULTATS if ok)
    nb_tot = len(RESULTATS)
    print(f"{nb_ok}/{nb_tot} vérifications OK")
    if nb_ok == nb_tot:
        print("IGIC VÉRIFIÉ — le calcul correspond aux scénarios de référence.")
        return 0
    print("IGIC INCOHÉRENT — des vérifications ont échoué.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
