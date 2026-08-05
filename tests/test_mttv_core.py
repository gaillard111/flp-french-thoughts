#!/usr/bin/env python3
"""
test_mttv_core.py — Cohérence du couplage mttv-core
====================================================
Vérifie l'intégration des trois briques du framework :
    1. ÉtatTetravalent (matrices.py, géométrie sp3).
    2. operateur_sigma / routeur_polyfocal (operators.py).
    3. BGate poreux (bgate.py).

Couplage vérifié : transduction Ψ→B→Φ, retrait fonctionnel de Σ,
apériodicité, absorption du bruit, quorum MPVR.

Usage :
    python tests/test_mttv_core.py
"""

import os
import sys

# Encodage console robuste (évite les erreurs Unicode sur cp1252/Windows).
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Permet d'importer le paquet `mttv_core` depuis la racine du workspace.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mttv_core import (  # noqa: E402
    MTTV_SIG,
    BGate,
    EtatTetravalent,
    HorlogeSigmaAperiodique,
    angle_sp3,
    operateur_sigma,
    projection_sp3,
    routeur_polyfocal,
    to_sp3,
)

RESULTATS: list = []


def verifie(nom: str, condition: bool, detail: str = "") -> bool:
    """Enregistre et affiche une vérification."""
    RESULTATS.append((nom, bool(condition), detail))
    statut = "OK  " if condition else "FAIL"
    print(f"[{statut}] {nom}" + (f" — {detail}" if detail else ""))
    return bool(condition)


# ─────────────────────────────────────────────────────────────────────────
# 1. GÉOMÉTRIE sp3
# ─────────────────────────────────────────────────────────────────────────


def test_sp3() -> None:
    # Angle inter-sommets du tétraèdre : signature du carbone sp3 ≈ 109,47°.
    a = angle_sp3()
    verifie(
        "sp3 : angle inter-sommets ≈ 109,47°",
        abs(a - 109.471) < 0.01,
        f"θ={a:.4f}°",
    )

    # Aller-retour to_sp3 → projection_sp3 ≈ identité (état fermé).
    etat = EtatTetravalent.purement("++")
    p3 = to_sp3(etat.valeurs)
    v = projection_sp3(p3)
    verifie(
        "sp3 : aller-retour to_sp3/projection_sp3 ≈ identité",
        max(abs(x - y) for x, y in zip(v, etat.valeurs)) < 1e-9,
        f"reconstruit={tuple(round(x, 6) for x in v)}",
    )

    # Clôture : Σ valeurs = 1 (invariant « clôture zéro »).
    ferme = EtatTetravalent((0.5, 0.2, 0.2, 0.1)).fermer()
    verifie(
        "sp3 : clôture Σ=1",
        abs(sum(ferme.valeurs) - 1.0) < 1e-9,
        str(tuple(round(x, 4) for x in ferme.valeurs)),
    )


# ─────────────────────────────────────────────────────────────────────────
# 2. TRANSDUCTION Ψ → B → Φ (INVARIANCE T⁴)
# ─────────────────────────────────────────────────────────────────────────


def test_transduction_invariance() -> None:
    # Texte propre, uniformément dominé par le pôle ++ (affirmation).
    texte_clean = (
        "Le vivant affirme sa force et sa croissance. "
        "L'eau émerge, le carbone affirme, la résonance se propage. "
        "Oui, la vie affirme. Oui, la force émerge et l'onde résonne. "
        "Le vivant affirme, l'eau émerge, le carbone circule. "
        "La croissance émerge, la force affirme, oui. "
        "Le vivant affirme, la résonance se propage, l'onde oscille."
    )
    porte = BGate(seed=7)
    res = porte.absorber(texte_clean)
    etat = res["etat_tetravalent"]

    verifie(
        "transduction : T⁴ de sortie fermé (Σ=1)",
        abs(sum(etat.valeurs) - 1.0) < 1e-9,
        str(tuple(round(x, 4) for x in etat.valeurs)),
    )

    pole, part, _ = etat.dominant()
    verifie(
        "transduction : pôle dominant ++",
        pole == "++",
        f"dominant={pole} part={part:.3f}",
    )

    # Couplage : le T⁴ traverse Σ puis le routeur sans perdre sa structure.
    foyers = [
        EtatTetravalent.purement("++"),
        EtatTetravalent.purement("--"),
        EtatTetravalent.purement("+-"),
    ]
    route = routeur_polyfocal(
        etat, foyers, [1.0, 1.0, 1.0],
        frottement=1.5, t_courant=10.0, tau=10.0,
        seuil_clinamen=1.0, theta=3, seuil_validation=0.5,
    )
    verifie(
        "transduction : le routage conserve le pôle (foyer ++ élu)",
        route["foyer_elu"] == 0,
        f"élu={route['foyer_elu']}",
    )

    # Couplage B-gate : un signal cohérent valide le quorum MPVR (Θ ≥ 3).
    verifie(
        "transduction : quorum B-gate (Θ≥3) sur texte propre",
        res["quorum"]["quorum_ok"] is True,
        str(res["quorum"]),
    )


# ─────────────────────────────────────────────────────────────────────────
# 3. RETRAIT FONCTIONNEL DE Σ
# ─────────────────────────────────────────────────────────────────────────


def test_retrait_sigma() -> None:
    psi = EtatTetravalent.purement("++")

    # Hors du support compact : Σ ≡ 0 (même avec frottement).
    evt_hors = operateur_sigma(psi, tau=5.0, frottement=2.0, t_courant=0.0)
    verifie(
        "retrait : Σ ≡ 0 hors de τ (support compact)",
        (not evt_hors.declenche) and evt_hors.impulsion == (0.0, 0.0, 0.0),
        str(evt_hors.impulsion),
    )

    # À τ sans clinamen : pas de bascule (muet).
    evt_sans = operateur_sigma(psi, tau=5.0, frottement=0.5, t_courant=5.0)
    verifie(
        "retrait : pas de bascule à τ sans clinamen mûr",
        not evt_sans.declenche,
    )

    # À τ avec clinamen : bascule, impulsion p(τ) non nulle.
    evt_oui = operateur_sigma(psi, tau=5.0, frottement=1.5, t_courant=5.0)
    verifie(
        "retrait : bascule à τ (p(τ) ≠ 0)",
        evt_oui.declenche and evt_oui.impulsion != (0.0, 0.0, 0.0),
        f"p={tuple(round(x, 4) for x in evt_oui.impulsion)}",
    )

    # Immédiatement après τ : retour à zéro (retrait fonctionnel).
    evt_apres = operateur_sigma(psi, tau=5.0, frottement=2.0, t_courant=6.0)
    verifie(
        "retrait : retour à 0 après τ (retrait fonctionnel)",
        (not evt_apres.declenche) and evt_apres.impulsion == (0.0, 0.0, 0.0),
    )


# ─────────────────────────────────────────────────────────────────────────
# 4. APÉRIODICITÉ DE LA SINGULARITÉ
# ─────────────────────────────────────────────────────────────────────────


def test_aperiodicite() -> None:
    horloge = HorlogeSigmaAperiodique(
        taux_frottement=0.3, seuil_clinamen=1.0, seed=42,
    )
    instants = []
    for _ in range(5000):
        if horloge.pas(dt=1.0, bruit=0.0):
            instants.append(horloge.t)

    verifie(
        "apériodicité : plusieurs bascules détectées",
        len(instants) >= 2,
        f"n={len(instants)}",
    )

    if len(instants) >= 2:
        intervalles = [b - a for a, b in zip(instants, instants[1:])]
        non_periodique = len(set(round(i, 3) for i in intervalles)) > 1
        verifie(
            "apériodicité : intervalles non périodiques",
            non_periodique,
            f"Δ={[round(i, 2) for i in intervalles[:6]]}",
        )


# ─────────────────────────────────────────────────────────────────────────
# 5. ABSORPTION DU BRUIT PAR LA POROSITÉ
# ─────────────────────────────────────────────────────────────────────────


def test_absorption_bruit() -> None:
    texte_clean = (
        "Le vivant affirme sa force et sa croissance. "
        "L'eau émerge, le carbone affirme, la résonance se propage. "
        "Oui, la vie affirme. Oui, la force émerge et l'onde résonne. "
        "Le vivant affirme, l'eau émerge, le carbone circule. "
        "La croissance émerge, la force affirme, oui. "
        "Le vivant affirme, la résonance se propage, l'onde oscille."
    )
    bruit = " ".join(
        ["zzz", "qx", "mnp", "abc", "toto", "lorem", "ipsum", "dolor"] * 6
    )
    texte_bruite = texte_clean + " " + bruit

    porte = BGate(seed=7)
    res_clean = porte.absorber(texte_clean)
    res_bruite = porte.absorber(texte_bruite)

    ecart = res_clean["etat_tetravalent"].ecart(res_bruite["etat_tetravalent"])
    verifie(
        "bruit : T⁴ de sortie peu affecté par le bruit",
        ecart < 0.15,
        f"écart L1={ecart:.4f}",
    )
    verifie(
        "bruit : porosité plus haute sur texte bruité",
        res_bruite["porosite"] > res_clean["porosite"],
        f"porosité {res_clean['porosite']:.2f} → {res_bruite['porosite']:.2f}",
    )
    verifie(
        "bruit : jetons bruités absorbés dans les pores",
        res_bruite["bruit_absorbe"] > res_clean["bruit_absorbe"],
        f"absorbés {res_clean['bruit_absorbe']} → {res_bruite['bruit_absorbe']}",
    )


# ─────────────────────────────────────────────────────────────────────────
# 6. QUORUM MPVR (Θ ≥ 3)
# ─────────────────────────────────────────────────────────────────────────


def test_quorum_mpvr() -> None:
    entree = EtatTetravalent.purement("++")

    # 3 foyers mais 2 seulement résonnent (le 3e est opposé) → pas de Φ.
    foyers_2 = [
        EtatTetravalent.purement("++"),
        EtatTetravalent.purement("++"),
        EtatTetravalent.purement("--"),  # résonance faible (opposé)
    ]
    route_2 = routeur_polyfocal(
        entree, foyers_2, [1.0, 1.0, 1.0],
        frottement=0.0, t_courant=0.0, tau=1.0,
        theta=3, seuil_validation=0.5,
    )
    verifie(
        "quorum : pas de Φ stabilisé si Θ < 3",
        route_2["phi_stabilise"] is False,
        str(route_2["quorum"]),
    )

    # 3 foyers résonnants → quorum atteint → Φ stabilisé.
    foyers_3 = [
        EtatTetravalent.purement("++"),
        EtatTetravalent.purement("++"),
        EtatTetravalent.purement("++"),
    ]
    route_3 = routeur_polyfocal(
        entree, foyers_3, [1.0, 1.0, 1.0],
        frottement=0.0, t_courant=0.0, tau=1.0,
        theta=3, seuil_validation=0.5,
    )
    verifie(
        "quorum : Φ stabilisé si Θ ≥ 3",
        route_3["phi_stabilise"] is True,
        str(route_3["quorum"]),
    )


# ─────────────────────────────────────────────────────────────────────────
# LANCEMENT
# ─────────────────────────────────────────────────────────────────────────


def main() -> int:
    print(f"mttv-core — Test de cohérence du couplage   (sig:{MTTV_SIG})")
    print("=" * 72)
    test_sp3()
    test_transduction_invariance()
    test_retrait_sigma()
    test_aperiodicite()
    test_absorption_bruit()
    test_quorum_mpvr()
    print("=" * 72)
    nb_ok = sum(1 for _, ok, _ in RESULTATS if ok)
    nb_tot = len(RESULTATS)
    print(f"{nb_ok}/{nb_tot} vérifications OK")
    if nb_ok == nb_tot:
        print("COUPLAGE COHÉRENT — toutes les vérifications passent.")
        return 0
    print("COUPLAGE INCOHÉRENT — des vérifications ont échoué.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
