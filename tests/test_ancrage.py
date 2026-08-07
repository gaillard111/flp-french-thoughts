#!/usr/bin/env python3
"""
test_ancrage.py — Dataset d'ancrage sémantique (A1.1)
======================================================
Vérifie :
    1. le dataset contient 13 viabilité + 13 rejet ;
    2. chaque ancre est projetée dans l'espace tétravalent (clôture Σ=1) ;
    3. les empreintes immuables sont uniques et déterministes ;
    4. la projection est déterministe (même texte → même vecteur).

Usage :
    python tests/test_ancrage.py
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
    BGate,
    construire_dataset_ancrage,
    empreinte_immuable,
    projeter_texte,
)

RESULTATS: list = []


def verifie(nom: str, condition: bool, detail: str = "") -> bool:
    RESULTATS.append((nom, bool(condition), detail))
    statut = "OK  " if condition else "FAIL"
    print(f"[{statut}] {nom}" + (f" — {detail}" if detail else ""))
    return bool(condition)


def test_dataset() -> None:
    data = construire_dataset_ancrage(seed=42)
    n_viab = data["n_viabilite"]
    n_rejet = data["n_rejet"]
    verifie("A1.1 : 13 critères de viabilité chargés",
            n_viab == 13, f"n={n_viab}")
    verifie("A1.1 : 13 critères de rejet chargés",
            n_rejet == 13, f"n={n_rejet}")
    verifie("A1.1 : dataset complet (26 ancres)",
            len(data["dataset"]) == 26, f"n={len(data['dataset'])}")


def test_projection() -> None:
    data = construire_dataset_ancrage(seed=42)
    # Clôture Σ=1 sur chaque ancre
    fermes = all(
        abs(sum(a["vecteur_t4"]) - 1.0) < 1e-3 for a in data["dataset"]
    )
    verifie("A1.1 : chaque ancre fermée (clôture Σ=1)",
            fermes, "26/26 ancres")

    # Déterminisme : même texte → même vecteur
    porte = BGate(seed=42)
    t = data["dataset"][0]["texte"]
    v1 = projeter_texte(t, porte).valeurs
    v2 = projeter_texte(t, porte).valeurs
    verifie("A1.1 : projection déterministe",
            v1 == v2, str(tuple(round(x, 4) for x in v1)))


def test_empreintes() -> None:
    data = construire_dataset_ancrage(seed=42)
    hashes = [a["empreinte_immuable"] for a in data["dataset"]]
    verifie("A1.1 : empreintes immuables uniques",
            len(set(hashes)) == len(hashes),
            f"uniques={len(set(hashes))}/{len(hashes)}")
    verifie("A1.1 : empreinte déterministe (sha256)",
            empreinte_immuable("abc") == empreinte_immuable("abc")
            and empreinte_immuable("abc") != empreinte_immuable("abd"))


def main() -> int:
    print(f"mttv-core — Ancrage sémantique (A1.1)   (sig:{MTTV_SIG})")
    print("=" * 72)
    test_dataset()
    test_projection()
    test_empreintes()
    print("=" * 72)
    nb_ok = sum(1 for _, ok, _ in RESULTATS if ok)
    nb_tot = len(RESULTATS)
    print(f"{nb_ok}/{nb_tot} vérifications OK")
    if nb_ok == nb_tot:
        print("ANCRAGE SÉMANTIQUE COHÉRENT — dataset immuable opérationnel.")
        return 0
    print("ANCRAGE INCOHÉRENT — des vérifications ont échoué.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
