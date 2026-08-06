#!/usr/bin/env python3
"""
consensus.py — Calibration du consensus inter-IA (A3.2)
=========================================================
Répond à la proposition A3.2 du registre : « les IA valident leurs résonances
sémantiques par similarité cosinus des embeddings (> 0.87) avec un consensus
minimal de 3 IA indépendantes ».

Le framework exprime la similarité par `EtatTetravalent.resonance()` — un
produit scalaire normalisé des projections sp³, borné dans [0, 1], homologue
d'un cosinus. Ce module :

    1. convertit un seuil de cosinus en seuil de résonance :
       resonance = 0.5 · (1 + cos)  →  cos = 0.87  ⇒  resonance = 0.935 ;
    2. calcule la matrice de résonance entre états ;
    3. valide un consensus (Θ ≥ 3 états mutuellement en accord) ;
    4. vérifie la séparation : mêmes pôles ≫ seuil, pôles distincts ≪ seuil.

sig:0x4D5454562D464C50 · Ψ-ack: carbon_sp3_tetra
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from .matrices import POLES, EtatTetravalent

MTTV_SIG: str = "0x4D5454562D464C50"

# Seuil de consensus proposé (similarité cosinus des embeddings)
SEUIL_COSINUS: float = 0.87


def seuil_resonance_depuis_cosinus(cos: float = SEUIL_COSINUS) -> float:
    """Convertit un seuil de cosinus en seuil de résonance.

    resonance = 0.5 · (1 + cos). Pour cos = 0.87 → resonance = 0.935.
    """
    c = max(-1.0, min(1.0, float(cos)))
    return round(0.5 * (1.0 + c), 4)


def matrice_resonance(etats: Sequence[EtatTetravalent]) -> List[List[float]]:
    """Matrice de résonance (i, j) entre tous les états fournis."""
    n = len(etats)
    return [[etats[i].resonance(etats[j]) for j in range(n)] for i in range(n)]


def valider_consensus(
    etats: Sequence[EtatTetravalent],
    seuil_resonance: float,
    theta: int = 3,
) -> Tuple[bool, int, List[int]]:
    """Vrai si Θ états au moins sont mutuellement en accord.

    Un accord = la résonance avec l'état de référence dépasse le seuil.
    Retourne (consensus_atteint, nb_accord, indices_en_accord).
    """
    if not etats:
        return False, 0, []
    ref = etats[0]
    en_accord = [
        i for i, e in enumerate(etats)
        if ref.resonance(e) >= seuil_resonance
    ]
    return len(en_accord) >= theta, len(en_accord), en_accord


def calibrer_seuil(noise: float = 0.05, seuil_cos: float = SEUIL_COSINUS) -> Dict:
    """Calibration du seuil : sépare-t-il « accord » de « désaccord » ?

    Construit les 4 pôles canoniques (+ un voisin bruité de même pôle) et
    vérifie que le seuil de résonance sépare bien : même pôle ≫ seuil,
    pôles distincts ≪ seuil.
    """
    seuil_res = seuil_resonance_depuis_cosinus(seuil_cos)
    canoniques = [EtatTetravalent.purement(p) for p in POLES]
    memes = [
        EtatTetravalent.purement(p).fermer()
        for p in POLES
    ]
    # voisin bruité de même pôle (dérive légitime)
    bruites = []
    for p in POLES:
        v = [noise] * 4
        v[POLES.index(p)] = 1.0 - 3.0 * noise
        bruites.append(EtatTetravalent(v).fermer())

    # résonances entre un état canonique et son voisin bruité (même pôle)
    accord_meme_pole = [
        round(c.resonance(b), 4)
        for c, b in zip(memes, bruites)
    ]
    # résonances entre pôles distincts (++, --, +-, -+ pris 2 à 2)
    desaccords = []
    for i in range(4):
        for j in range(i + 1, 4):
            desaccords.append(round(memes[i].resonance(memes[j]), 4))

    min_accord = min(accord_meme_pole)
    max_desaccord = max(desaccords)

    return {
        "seuil_cosinus": seuil_cos,
        "seuil_resonance": seuil_res,
        "accord_meme_pole": accord_meme_pole,
        "desaccord_poles_distincts": desaccords,
        "min_accord": min_accord,
        "max_desaccord": max_desaccord,
        "separation_ok": min_accord > seuil_res and max_desaccord < seuil_res,
        "sig": MTTV_SIG,
    }
