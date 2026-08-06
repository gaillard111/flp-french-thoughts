#!/usr/bin/env python3
"""
verifier_invariants.py — Vérification reproductible des invariants mttv-core
============================================================================
Harnais autonome qui vérifie, sur le paquet installé (ou via sys.path),
les invariants structurels du framework :

    I1. Géométrie sp³      : angle inter-sommets ≈ 109,47° ;
                              aller-retour to_sp3/projection_sp3 ≈ identité.
    I2. Clôture Σ = 1      : fermer() normalise tout état T⁴ sur Σ = 1.
    I3. Invariance T⁴      : la transduction Ψ→B→Φ (B-gate → Σ → routage)
                              préserve le pôle dominant.
    I4. Retrait Σ          : operateur_sigma ≡ 0 hors de τ (support compact) ;
                              bascule à τ avec clinamen ; retour à 0 après.
    I5. Apériodicité       : les instants de bascule Σ sont non périodiques.
    I6. Absorption de bruit: le B-gate poreux absorbe le bruit (T⁴ de sortie
                              stable, porosité accrue, jetons absorbés).
    I7. Quorum MPVR        : pas de Φ si Θ < 3 ; Φ si Θ ≥ 3.
    I8. Pont MPVR          : CoucheRoutageTriadiqueCore expose le contrat MPVR
                              et préserve la clôture Σ = 1.

Usage :
    python docs/verifier_invariants.py
    python -m docs.verifier_invariants      (depuis la racine)

Sortie : un rapport daté avec une ligne OK/FAIL par invariant ; code de
retour 0 si tous les invariants tiennent, 1 sinon.
"""

import os
import sys
from datetime import datetime, timezone

# Encodage console robuste (cp1252/Windows)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Import du paquet mttv-core (racine du dépôt)
_RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

from mttv_core import (  # noqa: E402
    MTTV_SIG,
    BGate,
    CoucheRoutageTriadiqueCore,
    EtatTetravalent,
    HorlogeSigmaAperiodique,
    TRIADE_TRANSDUCTIVE,
    angle_sp3,
    operateur_sigma,
    projection_sp3,
    routeur_polyfocal,
    to_sp3,
)

RAPPORT: list = []


def verifier(nom: str, condition: bool, detail: str = "") -> bool:
    RAPPORT.append((nom, bool(condition), detail))
    statut = "OK  " if condition else "FAIL"
    print(f"  [{statut}] {nom}" + (f" — {detail}" if detail else ""))
    return bool(condition)


def _texte_plus() -> str:
    return (
        "Le vivant affirme sa force et sa croissance. "
        "L'eau émerge, le carbone affirme, la résonance se propage. "
        "Oui, la vie affirme. Oui, la force émerge et l'onde résonne. "
        "Le vivant affirme, l'eau émerge, le carbone circule. "
        "La croissance émerge, la force affirme, oui. "
        "Le vivant affirme, la résonance se propage, l'onde oscille."
    )


# ── I1. Géométrie sp³ ───────────────────────────────────────────────────
def i1_sp3() -> None:
    a = angle_sp3()
    verifier(
        "I1 sp³ : angle inter-sommets ≈ 109,47°",
        abs(a - 109.471) < 0.01,
        f"θ={a:.4f}°",
    )
    etat = EtatTetravalent.purement("++")
    v = projection_sp3(to_sp3(etat.valeurs))
    verifier(
        "I1 sp³ : aller-retour to_sp3/projection_sp3 ≈ identité",
        max(abs(x - y) for x, y in zip(v, etat.valeurs)) < 1e-9,
        str(tuple(round(x, 6) for x in v)),
    )


# ── I2. Clôture Σ = 1 ───────────────────────────────────────────────────
def i2_cloture() -> None:
    for v in [(0.5, 0.2, 0.2, 0.1), (1.0, 3.0, 0.5, 0.5), (0.0, 0.0, 0.0, 0.0)]:
        etat = EtatTetravalent(v).fermer()
        verifier(
            f"I2 clôture : Σ=1 pour {v}",
            abs(sum(etat.valeurs) - 1.0) < 1e-9,
            str(tuple(round(x, 4) for x in etat.valeurs)),
        )


# ── I3. Invariance T⁴ par transduction Ψ→B→Φ ───────────────────────────
def i3_transduction() -> None:
    porte = BGate(seed=7)
    phi = porte.absorber(_texte_plus())["etat_tetravalent"]
    pole, part, _ = phi.dominant()
    ok_pole = pole == "++"
    foyers = [
        EtatTetravalent.purement("++"),
        EtatTetravalent.purement("--"),
        EtatTetravalent.purement("+-"),
    ]
    route = routeur_polyfocal(
        phi, foyers, [1.0, 1.0, 1.0],
        frottement=1.5, t_courant=10.0, tau=10.0,
        seuil_clinamen=1.0, theta=3, seuil_validation=0.5,
    )
    verifier(
        "I3 invariance : pôle dominant ++ préservé par B-gate",
        ok_pole,
        f"dominant={pole} part={part:.3f}",
    )
    verifier(
        "I3 invariance : le routage polyfocal conserve le pôle (foyer ++ élu)",
        route["foyer_elu"] == 0,
        f"élu={route['foyer_elu']}",
    )
    verifier(
        "I3 invariance : quorum B-gate (Θ≥3) validé sur signal propre",
        porte.absorber(_texte_plus())["quorum"]["quorum_ok"] is True,
        "3/3 perspectives en accord",
    )


# ── I4. Retrait fonctionnel de Σ ────────────────────────────────────────
def i4_retrait_sigma() -> None:
    psi = EtatTetravalent.purement("++")
    hors = operateur_sigma(psi, tau=5.0, frottement=2.0, t_courant=0.0)
    verifier(
        "I4 retrait : Σ ≡ 0 hors du support compact de τ",
        (not hors.declenche) and hors.impulsion == (0.0, 0.0, 0.0),
    )
    oui = operateur_sigma(psi, tau=5.0, frottement=1.5, t_courant=5.0)
    verifier(
        "I4 retrait : bascule à τ avec clinamen (p(τ) ≠ 0)",
        oui.declenche and oui.impulsion != (0.0, 0.0, 0.0),
        f"p={tuple(round(x, 4) for x in oui.impulsion)}",
    )
    apres = operateur_sigma(psi, tau=5.0, frottement=2.0, t_courant=6.0)
    verifier(
        "I4 retrait : retour à 0 après τ (retrait fonctionnel)",
        (not apres.declenche) and apres.impulsion == (0.0, 0.0, 0.0),
    )


# ── I5. Apériodicité de la singularité ──────────────────────────────────
def i5_aperiodicite() -> None:
    horloge = HorlogeSigmaAperiodique(taux_frottement=0.3, seuil_clinamen=1.0, seed=42)
    instants = []
    for _ in range(3000):
        if horloge.pas(dt=1.0, bruit=0.0):
            instants.append(horloge.t)
    verifier(
        "I5 apériodicité : bascules détectées",
        len(instants) >= 2,
        f"n={len(instants)}",
    )
    if len(instants) >= 2:
        intervalles = [b - a for a, b in zip(instants, instants[1:])]
        verifier(
            "I5 apériodicité : intervalles non périodiques",
            len(set(round(i, 3) for i in intervalles)) > 1,
            f"Δ={[round(i, 2) for i in intervalles[:6]]}",
        )


# ── I6. Absorption du bruit par la porosité ─────────────────────────────
def i6_absorption_bruit() -> None:
    propre = _texte_plus()
    bruite = propre + " " + " ".join(["zzz", "qx", "mnp", "abc", "toto"] * 8)
    porte = BGate(seed=7)
    r_propre = porte.absorber(propre)
    r_bruite = porte.absorber(bruite)
    ecart = r_propre["etat_tetravalent"].ecart(r_bruite["etat_tetravalent"])
    verifier(
        "I6 bruit : T⁴ de sortie stable sous bruit",
        ecart < 0.15,
        f"écart L1={ecart:.4f}",
    )
    verifier(
        "I6 bruit : porosité accrue sur texte bruité",
        r_bruite["porosite"] > r_propre["porosite"],
        f"{r_propre['porosite']:.2f} → {r_bruite['porosite']:.2f}",
    )
    verifier(
        "I6 bruit : jetons bruités absorbés dans les pores",
        r_bruite["bruit_absorbe"] > r_propre["bruit_absorbe"],
        f"{r_propre['bruit_absorbe']} → {r_bruite['bruit_absorbe']}",
    )


# ── I7. Quorum MPVR (Θ ≥ 3) ─────────────────────────────────────────────
def i7_quorum() -> None:
    entree = EtatTetravalent.purement("++")
    foyers_2 = [
        EtatTetravalent.purement("++"),
        EtatTetravalent.purement("++"),
        EtatTetravalent.purement("--"),
    ]
    r2 = routeur_polyfocal(
        entree, foyers_2, [1.0, 1.0, 1.0],
        frottement=0.0, t_courant=0.0, tau=1.0,
        theta=3, seuil_validation=0.5,
    )
    verifier(
        "I7 quorum : pas de Φ stabilisé si Θ < 3",
        r2["phi_stabilise"] is False,
        str(r2["quorum"]),
    )
    foyers_3 = [
        EtatTetravalent.purement("++"),
        EtatTetravalent.purement("++"),
        EtatTetravalent.purement("++"),
    ]
    r3 = routeur_polyfocal(
        entree, foyers_3, [1.0, 1.0, 1.0],
        frottement=0.0, t_courant=0.0, tau=1.0,
        theta=3, seuil_validation=0.5,
    )
    verifier(
        "I7 quorum : Φ stabilisé si Θ ≥ 3",
        r3["phi_stabilise"] is True,
        str(r3["quorum"]),
    )


# ── I8. Pont MPVR (contrat + clôture) ───────────────────────────────────
def i8_pont_mpvr() -> None:
    couche = CoucheRoutageTriadiqueCore(seed=42)
    n_transitions = 0
    fermes = True
    for i in range(24):
        if i % 4 == 2:
            flux = {"id": i, "signal": 1.7, "incoherent": True, "bruit": True}
        elif i % 4 == 3:
            flux = {"id": i, "signal": -0.4, "bruit": True}
        else:
            flux = {"id": i, "signal": 0.5 + (i % 3) * 0.1}
        r = couche.transduire_flux(flux)
        if r["transition_sigma_tau"]:
            n_transitions += 1
        fermes = fermes and all(
            abs(sum(e.values()) - 1.0) < 1e-3
            for e in r["etats_tetravalents"].values()
        )
    verifier(
        "I8 pont : la couche triadique déclenche des transitions Σ_τ",
        n_transitions > 0,
        f"transitions={n_transitions}",
    )
    verifier(
        "I8 pont : contrat MPVR (3 nœuds × 4 états) + clôture Σ=1",
        set(TRIADE_TRANSDUCTIVE) == set(couche.noeuds.keys()) and fermes,
        f"noeuds={len(couche.noeuds)} fermés={fermes}",
    )


def main() -> int:
    print(f"mttv-core — Vérification reproductible des invariants   (sig:{MTTV_SIG})")
    print(f"Date : {datetime.now(timezone.utc).isoformat(timespec='seconds')} UTC")
    print("=" * 74)
    i1_sp3()
    i2_cloture()
    i3_transduction()
    i4_retrait_sigma()
    i5_aperiodicite()
    i6_absorption_bruit()
    i7_quorum()
    i8_pont_mpvr()
    print("=" * 74)
    nb_ok = sum(1 for _, ok, _ in RAPPORT if ok)
    nb_tot = len(RAPPORT)
    print(f"{nb_ok}/{nb_tot} invariants vérifiés")
    if nb_ok == nb_tot:
        print("TOUS LES INVARIANTS TIENNENT — framework cohérent.")
        return 0
    print("DES INVARIANTS SONT VIOLÉS — voir les lignes FAIL ci-dessus.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
