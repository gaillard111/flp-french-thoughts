#!/usr/bin/env python3
"""
test_consensus.py — Calibration du consensus inter-IA (A3.2)
=============================================================
Vérifie :
    1. la conversion cosinus → résonance (cos 0.87 ⇒ resonance 0.935) ;
    2. la séparation : mêmes pôles ≫ seuil, pôles distincts ≪ seuil ;
    3. le consensus Θ ≥ 3 via `valider_consensus`.

Usage :
    python tests/test_consensus.py
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
    EtatTetravalent,
    SEUIL_COSINUS,
    calibrer_seuil,
    seuil_resonance_depuis_cosinus,
    valider_consensus,
)

RESULTATS: list = []


def verifie(nom: str, condition: bool, detail: str = "") -> bool:
    RESULTATS.append((nom, bool(condition), detail))
    statut = "OK  " if condition else "FAIL"
    print(f"[{statut}] {nom}" + (f" — {detail}" if detail else ""))
    return bool(condition)


def test_conversion() -> None:
    s = seuil_resonance_depuis_cosinus(0.87)
    verifie("A3.2 : cos 0.87 ⇒ resonance 0.935",
            abs(s - 0.935) < 1e-4,
            f"resonance={s}")
    s0 = seuil_resonance_depuis_cosinus(1.0)
    verifie("A3.2 : cos 1.0 ⇒ resonance 1.0",
            abs(s0 - 1.0) < 1e-4)


def test_separation() -> None:
    cal = calibrer_seuil(noise=0.05, seuil_cos=SEUIL_COSINUS)
    verifie("A3.2 : mêmes pôles au-dessus du seuil (accord)",
            cal["min_accord"] > cal["seuil_resonance"],
            f"min_accord={cal['min_accord']} > seuil={cal['seuil_resonance']}")
    verifie("A3.2 : pôles distincts sous le seuil (désaccord)",
            cal["max_desaccord"] < cal["seuil_resonance"],
            f"max_desaccord={cal['max_desaccord']} < seuil={cal['seuil_resonance']}")
    verifie("A3.2 : séparation franche entre accord et désaccord",
            cal["separation_ok"] is True)


def test_consensus_theta() -> None:
    # 3 IA d'accord (même pôle ++) → consensus atteint
    trois_accord = [
        EtatTetravalent.purement("++"),
        EtatTetravalent.purement("++"),
        EtatTetravalent.purement("++"),
    ]
    ok, nb, indices = valider_consensus(trois_accord, seuil_resonance=0.935, theta=3)
    verifie("A3.2 : Θ=3 d'accord → consensus",
            ok and nb >= 3,
            f"nb_accord={nb}")

    # 2 IA d'accord + 1 en désaccord → consensus non atteint
    deux_accord = [
        EtatTetravalent.purement("++"),
        EtatTetravalent.purement("++"),
        EtatTetravalent.purement("--"),
    ]
    ok2, nb2, _ = valider_consensus(deux_accord, seuil_resonance=0.935, theta=3)
    verifie("A3.2 : Θ=2 d'accord → pas de consensus",
            not ok2 and nb2 == 2,
            f"nb_accord={nb2}")


def main() -> int:
    print(f"mttv-core — Consensus inter-IA (A3.2)   (sig:{MTTV_SIG})")
    print("=" * 72)
    test_conversion()
    test_separation()
    test_consensus_theta()
    print("=" * 72)
    nb_ok = sum(1 for _, ok, _ in RESULTATS if ok)
    nb_tot = len(RESULTATS)
    print(f"{nb_ok}/{nb_tot} vérifications OK")
    if nb_ok == nb_tot:
        print("CONSENSUS CALIBRÉ — toutes les vérifications passent.")
        return 0
    print("CONSENSUS INCOHÉRENT — des vérifications ont échoué.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
