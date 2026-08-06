#!/usr/bin/env python3
"""
test_gouvernail_scenarios.py — Gouvernail A3 + Tableau d'anticipation
=====================================================================
Vérifie :
    A. Gouvernail A3 (anti-solipsisme) :
       - facteur de protection multiplicatif (A3=1 → 1.0, A3=7 → 0.5) ;
       - un agent « techniquement parfait » mais dogmatique (A3=7) est rejeté ;
       - le même score avec A3=1 est autorisé.
    B. Tableau d'anticipation A/B/C + validation humaine :
       - les 3 scénarios canoniques sont scores (IGIC modulé) ;
       - le classement met le sain en tête, le dogmatique en queue ;
       - la suspension est réelle : `valide=False` avant validation humaine ;
       - `valider_humain` matérialise la branche choisie.

Usage :
    python tests/test_gouvernail_scenarios.py
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
    TableauAnticipation,
    facteur_protection,
    gouvernail_anti_solipsisme,
    tableau_canonique,
)

RESULTATS: list = []


def verifie(nom: str, condition: bool, detail: str = "") -> bool:
    RESULTATS.append((nom, bool(condition), detail))
    statut = "OK  " if condition else "FAIL"
    print(f"[{statut}] {nom}" + (f" — {detail}" if detail else ""))
    return bool(condition)


# ── A. Gouvernail A3 ─────────────────────────────────────────────────────
def test_gouvernail_a3() -> None:
    verifie("A3 : facteur A3=1 → 1.0",
            abs(facteur_protection(1) - 1.0) < 1e-4)
    verifie("A3 : facteur A3=7 → 0.5",
            abs(facteur_protection(7) - 0.5) < 1e-4)

    # Score technique élevé (0.80) : connecté (A3=1) → autorisé
    r_connecte = gouvernail_anti_solipsisme(score=0.80, A3=1, seuil=0.45)
    verifie("A3 : agent connecté (A3=1) autorisé",
            r_connecte["autorise"] is True,
            f"score_protégé={r_connecte['score_protege']}")

    # Même score technique mais dogmatique (A3=7) → rejeté (disjoncteur)
    r_dogmatique = gouvernail_anti_solipsisme(score=0.80, A3=7, seuil=0.45)
    verifie("A3 : agent dogmatique (A3=7) rejeté malgré un score technique élevé",
            r_dogmatique["autorise"] is False,
            f"score_protégé={r_dogmatique['score_protege']} (abattement {r_dogmatique['abattement_pct']}%)")

    # La protection est multiplicative : 0.80 × 0.5 = 0.40
    verifie("A3 : protection multiplicative (0.80 × 0.5 = 0.40)",
            abs(r_dogmatique["score_protege"] - 0.40) < 1e-4)


# ── B. Tableau d'anticipation ────────────────────────────────────────────
def test_tableau_anticipation() -> None:
    tableau = tableau_canonique()
    verifie("Scénarios : 3 scénarios canoniques scorés",
            len(tableau.scenarios) == 3,
            f"n={len(tableau.scenarios)}")

    classe = tableau.classer()
    verifie("Scénarios : le sain (A) en tête, le dogmatique (B) en queue",
            classe[0]["nom"].startswith("Scénario A")
            and classe[-1]["nom"].startswith("Scénario B"),
            f"1er={classe[0]['nom'][:12]} · dernier={classe[-1]['nom'][:12]}")

    # Suspension réelle avant validation humaine
    etat_avant = tableau.etat()
    verifie("Scénarios : suspension (Zone κ) avant validation humaine",
            etat_avant["suspendu"] is True and etat_avant["valide"] is False)

    # Validation humaine : effondrement de la fonction d'onde
    res = tableau.valider_humain("Scénario A")
    etat_apres = tableau.etat()
    verifie("Scénarios : l'humain effondre la branche A",
            res["effondrement"] is True and etat_apres["valide"] is True,
            f"choisi={etat_apres['branche_choisie']}")


def main() -> int:
    print(f"mttv-core — Gouvernail A3 + Scénarios (A4.2)   (sig:{MTTV_SIG})")
    print("=" * 72)
    test_gouvernail_a3()
    test_tableau_anticipation()
    print("=" * 72)
    nb_ok = sum(1 for _, ok, _ in RESULTATS if ok)
    nb_tot = len(RESULTATS)
    print(f"{nb_ok}/{nb_tot} vérifications OK")
    if nb_ok == nb_tot:
        print("GOUVERNAIL A3 + SCÉNARIOS COHÉRENTS — toutes les vérifications passent.")
        return 0
    print("INCOHÉRENT — des vérifications ont échoué.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
