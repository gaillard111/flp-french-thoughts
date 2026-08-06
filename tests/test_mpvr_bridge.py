#!/usr/bin/env python3
"""
test_mpvr_bridge.py — Cohérence du pont mttv-core ↔ MPVR
=========================================================
Vérifie l'intégration de `CoucheRoutageTriadiqueCore` (mttv_core.mpvr_bridge)
avec le contrat de sortie du MPVR-v2-T4 (mttv_mpvr_quorum.py) :

    1. conversions EtatTetravalent ↔ dict MPVR (aller-retour ≈ identité)
    2. contrat de sortie : clés identiques au MPVR (statut, états, couplages,
       tâtonnements, bruit, transition Σ_τ, sig)
    3. couplage : routeur_polyfocal + operateur_sigma + BGate réellement
       mobilisés (texte → BGate → T⁴ ; tâtonnements → transition Σ_τ)
    4. déterminisme : même seed → mêmes résultats

Usage :
    python tests/test_mpvr_bridge.py
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
    CoucheRoutageTriadiqueCore,
    ETATS_TETRAVALENTS,
    TRIADE_TRANSDUCTIVE,
    EtatTetravalent,
    etats_to_tetravalent,
    tetravalent_to_etats,
)

RESULTATS: list = []


def verifie(nom: str, condition: bool, detail: str = "") -> bool:
    RESULTATS.append((nom, bool(condition), detail))
    statut = "OK  " if condition else "FAIL"
    print(f"[{statut}] {nom}" + (f" — {detail}" if detail else ""))
    return bool(condition)


# ── 1. Conversions ─────────────────────────────────────────────────────
def test_conversions() -> None:
    # dict MPVR → EtatTetravalent → dict MPVR (aller-retour ≈ identité)
    etats_mpvr = {"T++": 0.6, "T--": 0.1, "T+-": 0.2, "T-+": 0.1}
    etat = etats_to_tetravalent(etats_mpvr)
    retour = tetravalent_to_etats(etat)
    verifie(
        "conversion : aller-retour dict MPVR ≈ identité",
        all(abs(retour[k] - etats_mpvr[k]) < 1e-6 for k in ETATS_TETRAVALENTS),
        str(retour),
    )
    verifie(
        "conversion : clés = ETATS_TETRAVALENTS du MPVR",
        set(retour.keys()) == set(ETATS_TETRAVALENTS),
        str(sorted(retour.keys())),
    )


# ── 2. Contrat de sortie MPVR ──────────────────────────────────────────
def test_contrat_sortie() -> None:
    couche = CoucheRoutageTriadiqueCore(seed=42)
    res = couche.transduire_flux({"id": 0, "signal": 0.5})
    cles_requises = {
        "statut_transduction", "etats_tetravalents", "couplages_transductifs",
        "tattonnements_globaux", "bruit_absorbe_total", "transition_sigma_tau",
        "n_transitions_sigma_tau", "lag_diachronique", "timestamp", "sig",
    }
    verifie(
        "contrat : clés de sortie identiques au MPVR v2-T4",
        cles_requises.issubset(set(res.keys())),
        f"clés={sorted(res.keys())}",
    )
    verifie(
        "contrat : 3 nœuds × 4 états tétravalents",
        set(res["etats_tetravalents"].keys()) == set(TRIADE_TRANSDUCTIVE)
        and all(set(e.keys()) == set(ETATS_TETRAVALENTS)
                for e in res["etats_tetravalents"].values()),
        str(res["etats_tetravalents"].keys()),
    )
    verifie(
        "contrat : signature MTTV présente",
        res["sig"] == MTTV_SIG,
        res["sig"],
    )


# ── 3. Couplage réel (BGate + operateur_sigma + routeur_polyfocal) ────
def test_couplage() -> None:
    # Entrée textuelle → BGate poreux → T⁴ → triade (couplage B-gate).
    couche_texte = CoucheRoutageTriadiqueCore(seed=7)
    res_texte = couche_texte.transduire_flux({
        "id": 0,
        "texte": (
            "Le vivant affirme sa force et sa croissance. "
            "Oui, l'eau émerge, le carbone affirme, la résonance se propage. "
            "Le vivant affirme, la force émerge, oui."
        ),
    })
    etat_bio = etats_to_tetravalent(res_texte["etats_tetravalents"]["bio_vivant"])
    # Tolérance 1e-3 : la sérialisation dict MPVR arrondit à 4 décimales ;
    # l'invariant Σ=1 est exact sur EtatTetravalent (voir matrices.py).
    verifie(
        "couplage : BGate alimente la triade (T⁴ fermé)",
        abs(sum(etat_bio.valeurs) - 1.0) < 1e-3,
        str(tuple(round(x, 4) for x in etat_bio.valeurs)),
    )
    pole_bio, part_bio, _ = etat_bio.dominant()
    verifie(
        "couplage : le nœud bio_vivant reflète le pôle ++ du texte entrant",
        pole_bio == "++",
        f"dominant={pole_bio} part={part_bio:.3f}",
    )

    # Tâtonnements → transition Σ_τ (operateur_sigma / horloge apériodique).
    couche = CoucheRoutageTriadiqueCore(seed=42)
    n_transitions = 0
    for i in range(60):
        if i % 4 == 2:
            flux = {"id": i, "signal": 1.7, "incoherent": True, "bruit": True}
        elif i % 4 == 3:
            flux = {"id": i, "signal": -0.4, "bruit": True}
        else:
            flux = {"id": i, "signal": 0.5 + (i % 3) * 0.1}
        res = couche.transduire_flux(flux)
        if res["transition_sigma_tau"]:
            n_transitions += 1
    verifie(
        "couplage : tâtonnements → transitions Σ_τ",
        n_transitions > 0,
        f"transitions={n_transitions} cumulées={couche.n_transitions_sigma_tau}",
    )

    # Routage polyfocal : l'attention est réallouée (matrice ≠ initiale).
    matrice_finale = couche.matrice_attention
    initiale = [[0.5, 0.35, 0.15], [0.3, 0.4, 0.3], [0.2, 0.3, 0.5]]
    verifie(
        "couplage : matrice d'attention réallouée par le routage",
        matrice_finale != initiale,
        str(matrice_finale),
    )


# ── 4. Déterminisme ────────────────────────────────────────────────────
def test_determinisme() -> None:
    c1 = CoucheRoutageTriadiqueCore(seed=42)
    c2 = CoucheRoutageTriadiqueCore(seed=42)
    signaux = [{"id": i, "signal": 0.5 + (i % 3) * 0.1} for i in range(8)]
    r1 = c1.transduire_flux_multiples(signaux)
    r2 = c2.transduire_flux_multiples(signaux)
    verifie(
        "déterminisme : même seed → mêmes stats agrégées",
        r1 == r2,
        f"Δtransitions={r1['n_transitions_cumulees']}",
    )


def main() -> int:
    print(f"mttv-core ↔ MPVR — Test du pont   (sig:{MTTV_SIG})")
    print("=" * 72)
    test_conversions()
    test_contrat_sortie()
    test_couplage()
    test_determinisme()
    print("=" * 72)
    nb_ok = sum(1 for _, ok, _ in RESULTATS if ok)
    nb_tot = len(RESULTATS)
    print(f"{nb_ok}/{nb_tot} vérifications OK")
    if nb_ok == nb_tot:
        print("PONT MPVR COHÉRENT — toutes les vérifications passent.")
        return 0
    print("PONT MPVR INCOHÉRENT — des vérifications ont échoué.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
