#!/usr/bin/env python3
"""
test_senescence.py — Mode sénescence (A5.4)
===========================================
Vérifie :
    1. un nœud persistant en divergence atteint la limite de Hayflick et part
       en retraite active (il ne vote plus) ;
    2. la retraite est réversible : s'il guérit, il revient au vote ;
    3. le taux de sénescence du réseau est calculé ;
    4. le retrait est « actif » (le nœud observe, il n'est pas supprimé).

Usage :
    python tests/test_senescence.py
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
    ModeSenescence,
    mesurer_reseau,
    taux_senescence,
)

RESULTATS: list = []


def verifie(nom: str, condition: bool, detail: str = "") -> bool:
    RESULTATS.append((nom, bool(condition), detail))
    statut = "OK  " if condition else "FAIL"
    print(f"[{statut}] {nom}" + (f" — {detail}" if detail else ""))
    return bool(condition)


def test_retraite_hayflick() -> None:
    noeud = ModeSenescence(limite_hayflick=5, seuil_divergence=0.5, seuil_guerison=0.2)

    # 4 cycles divergents → pas encore en retraite
    for _ in range(4):
        etat = noeud.observer(0.9)
    verifie("A5.4 : 4 cycles divergents → pas encore en retraite",
            etat["en_retraite"] is False,
            f"cycles={etat['cycles_divergence']}")

    # 5e cycle divergent → limite de Hayflick atteinte → retraite active
    etat = noeud.observer(0.9)
    verifie("A5.4 : limite de Hayflick atteinte → retraite active (ne vote plus)",
            etat["en_retraite"] is True and etat["peut_voter"] is False,
            f"cycles={etat['cycles_divergence']}")

    # Le nœud n'est pas supprimé : il observe (cycles_observes > 0)
    etat = noeud.observer(0.9)
    verifie("A5.4 : retraite active (observe, pas supprimé)",
            etat["cycles_observes"] >= 1,
            f"observes={etat['cycles_observes']}")


def test_reversibilite() -> None:
    noeud = ModeSenescence(limite_hayflick=2, seuil_divergence=0.5, seuil_guerison=0.2)
    noeud.observer(0.9)
    noeud.observer(0.9)  # → retraite

    # Guérison : divergence sous le seuil de guérison → retour au vote
    etat = noeud.observer(0.05)
    verifie("A5.4 : guérison → retour au vote (réversible)",
            etat["en_retraite"] is False and etat["peut_voter"] is True,
            f"retours={etat['retours']}")


def test_taux_reseau() -> None:
    # 3 nœuds : 2 restent actifs, 1 part en retraite
    divergences = [
        [0.9, 0.1, 0.9],
        [0.9, 0.1, 0.9],
        [0.9, 0.1, 0.9],
    ]  # nœud 0 et 2 en divergence persistante, nœud 1 sain
    res = mesurer_reseau(divergences, limite_hayflick=2, seuil_divergence=0.5, seuil_guerison=0.2)
    # Tolérance 1e-3 : `mesurer_reseau` arrondit le taux à 4 décimales.
    verifie("A5.4 : taux de sénescence du réseau ≈ 2/3",
            abs(res["taux_senescence"] - 2.0 / 3.0) < 1e-3,
            f"taux={res['taux_senescence']}")
    verifie("A5.4 : retraites comptées",
            res["retraites_total"] == 2,
            f"retraites={res['retraites_total']}")


def main() -> int:
    print(f"mttv-core — Mode sénescence (A5.4)   (sig:{MTTV_SIG})")
    print("=" * 72)
    test_retraite_hayflick()
    test_reversibilite()
    test_taux_reseau()
    print("=" * 72)
    nb_ok = sum(1 for _, ok, _ in RESULTATS if ok)
    nb_tot = len(RESULTATS)
    print(f"{nb_ok}/{nb_tot} vérifications OK")
    if nb_ok == nb_tot:
        print("SÉNESCENCE COHÉRENTE — toutes les vérifications passent.")
        return 0
    print("SÉNESCENCE INCOHÉRENTE — des vérifications ont échoué.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
