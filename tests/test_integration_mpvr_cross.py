#!/usr/bin/env python3
"""
test_integration_mpvr_cross.py — Intégration croisée réelle mttv-core ↔ MPVR
=============================================================================
Charge le VRAI module MPVR-v2-T4 ([mttv-flp-mpvr-glocal](mttv-flp-mpvr-glocal)
/src/mttv_mpvr_quorum.py) et la couche native mttv-core
(`CoucheRoutageTriadiqueCore`), les exécute sur le même flux de signaux, et
vérifie la cohérence structurelle du couplage :

    1. contrat de sortie identique (mêmes clés) ;
    2. topologie identique (3 nœuds × 4 états tétravalents) ;
    3. les deux déclenchent des transitions Σ_τ sur le flux incohérent ;
    4. la couche mttv-core préserve l'invariant de clôture Σ=1.

Usage :
    python tests/test_integration_mpvr_cross.py
"""

import os
import sys

# Encodage console robuste (cp1252/Windows).
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RACINE)
# Chemin vers le VRAI module MPVR (dépôt imbriqué mttv-flp-mpvr-glocal).
_MPVR_SRC = os.path.join(_RACINE, "mttv-flp-mpvr-glocal", "src")

# Ce test est un test CROISÉ : il exige le dépôt imbriqué mttv-flp-mpvr-glocal,
# qui est gitignoré et donc ABSENT sur GitHub Actions. En CI, il se déclare
# non applicable (SKIP) au lieu d'échouer — il ne tourne que dans le workspace
# local complet où le dépôt imbriqué est présent.
if not os.path.exists(os.path.join(_MPVR_SRC, "mttv_mpvr_quorum.py")):
    print("[SKIP] test_integration_mpvr_cross — dépôt imbriqué mttv-flp-mpvr-glocal "
          "absent (test local uniquement, non applicable en CI)")
    sys.exit(0)

sys.path.insert(0, _MPVR_SRC)

from mttv_core import (  # noqa: E402
    MTTV_SIG,
    CoucheRoutageTriadiqueCore,
    ETATS_TETRAVALENTS,
    TRIADE_TRANSDUCTIVE,
    etats_to_tetravalent,
)
import mttv_mpvr_quorum as mpvr  # noqa: E402

RESULTATS: list = []


def verifie(nom: str, condition: bool, detail: str = "") -> bool:
    RESULTATS.append((nom, bool(condition), detail))
    statut = "OK  " if condition else "FAIL"
    print(f"[{statut}] {nom}" + (f" — {detail}" if detail else ""))
    return bool(condition)


def _flux_test(n: int):
    """Même motif que la démo du MPVR : flux incohérents tous les 4 pas."""
    for i in range(n):
        if i % 4 == 2:
            yield {"id": i, "signal": 1.7, "incoherent": True, "bruit": True}
        elif i % 4 == 3:
            yield {"id": i, "signal": -0.4, "bruit": True}
        else:
            yield {"id": i, "signal": 0.5 + (i % 3) * 0.1}


_CLEFS_CONTRAT = {
    "statut_transduction", "etats_tetravalents", "couplages_transductifs",
    "tattonnements_globaux", "bruit_absorbe_total", "transition_sigma_tau",
    "n_transitions_sigma_tau", "lag_diachronique", "timestamp", "sig",
}


def test_contrat_commun() -> None:
    couche_mpvr = mpvr.CoucheRoutageTriadiqueDiachronique(seed=42)
    couche_core = CoucheRoutageTriadiqueCore(seed=42)
    r_mpvr = couche_mpvr.transduire_flux({"id": 0, "signal": 0.5})
    r_core = couche_core.transduire_flux({"id": 0, "signal": 0.5})

    verifie(
        "contrat : clés identiques MPVR ↔ mttv-core",
        _CLEFS_CONTRAT.issubset(set(r_mpvr)) and _CLEFS_CONTRAT.issubset(set(r_core)),
        f"mpvr={len(r_mpvr)} clés · core={len(r_core)} clés",
    )
    verifie(
        "contrat : topologie identique (3 nœuds de la triade)",
        set(r_mpvr["etats_tetravalents"].keys())
        == set(r_core["etats_tetravalents"].keys())
        == set(TRIADE_TRANSDUCTIVE),
        str(sorted(r_core["etats_tetravalents"].keys())),
    )


def test_etats_4_par_noeud() -> None:
    couche_mpvr = mpvr.CoucheRoutageTriadiqueDiachronique(seed=42)
    couche_core = CoucheRoutageTriadiqueCore(seed=42)
    r_mpvr = couche_mpvr.transduire_flux({"id": 0, "signal": 0.5})
    r_core = couche_core.transduire_flux({"id": 0, "signal": 0.5})

    ok_mpvr = all(
        set(e.keys()) == set(ETATS_TETRAVALENTS)
        for e in r_mpvr["etats_tetravalents"].values()
    )
    ok_core = all(
        set(e.keys()) == set(ETATS_TETRAVALENTS)
        for e in r_core["etats_tetravalents"].values()
    )
    verifie(
        "états : 4 états tétravalents par nœud (les deux couches)",
        ok_mpvr and ok_core,
        f"mpvr={ok_mpvr} core={ok_core}",
    )


def test_transitions_sigma_tau() -> None:
    couche_mpvr = mpvr.CoucheRoutageTriadiqueDiachronique(seed=42)
    couche_core = CoucheRoutageTriadiqueCore(seed=42)

    n_sig_mpvr = 0
    n_sig_core = 0
    for s in _flux_test(48):
        if couche_mpvr.transduire_flux(s)["transition_sigma_tau"]:
            n_sig_mpvr += 1
        if couche_core.transduire_flux(s)["transition_sigma_tau"]:
            n_sig_core += 1

    verifie(
        "Σ_τ : les deux couches déclenchent des transitions sur flux incohérent",
        n_sig_mpvr > 0 and n_sig_core > 0,
        f"mpvr={n_sig_mpvr} · core={n_sig_core}",
    )


def test_invariant_cloture_core() -> None:
    couche_core = CoucheRoutageTriadiqueCore(seed=42)
    ok = True
    detail = ""
    for s in _flux_test(12):
        r = couche_core.transduire_flux(s)
        etats = r["etats_tetravalents"]
        # Tolérance 1e-3 : les dicts sont sérialisés à 4 décimales (le
        # contrat MPVR), l'invariant Σ=1 est exact sur EtatTetravalent.
        fermes = all(
            abs(sum(e.values()) - 1.0) < 1e-3 for e in etats.values()
        )
        if not fermes:
            ok = False
            detail = str(etats)
            break
    verifie(
        "invariant : états mttv-core fermés (clôture Σ=1) sur tout le flux",
        ok,
        detail or "3 nœuds × 4 états, Σ=1",
    )


def main() -> int:
    print(f"mttv-core ↔ MPVR — Intégration croisée réelle   (sig:{MTTV_SIG})")
    print("=" * 72)
    test_contrat_commun()
    test_etats_4_par_noeud()
    test_transitions_sigma_tau()
    test_invariant_cloture_core()
    print("=" * 72)
    nb_ok = sum(1 for _, ok, _ in RESULTATS if ok)
    nb_tot = len(RESULTATS)
    print(f"{nb_ok}/{nb_tot} vérifications OK")
    if nb_ok == nb_tot:
        print("INTÉGRATION CROISÉE COHÉRENTE — mttv-core et MPVR s'accordent.")
        return 0
    print("INTÉGRATION CROISÉE INCOHÉRENTE — des vérifications ont échoué.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
