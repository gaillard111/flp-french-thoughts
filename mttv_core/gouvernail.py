#!/usr/bin/env python3
"""
gouvernail.py — Gouvernail sémantique A3 (anti-solipsisme) — A1.2/A4.2
======================================================================
Généralise l'idée du facteur de protection A3 (extrait d'ouroboros-mttv-v2.py) :
une protection **multiplicative** (disjoncteur) appliquée à n'importe quel score
composite — pas seulement l'IGIC — pour pénaliser l'auto-isolement dogmatique
sans toucher au score « technique ».

Principe :
    A3 = indice de non-isolement source (1 = connecté ; 7 = isolé/dogmatique)
    facteur de protection = 1 − (A3 − 1)/12   →  A3=1 ⇒ 100 % ; A3=7 ⇒ 50 %
    score protégé = score × facteur

Un agent peut être techniquement parfait mais être rejeté s'il absolutise ses
formes (A3 élevé) : c'est le « disjoncteur » face à la dérive dogmatique.

sig:0x4D5454562D464C50 · Ψ-ack: carbon_sp3_tetra
"""

from __future__ import annotations

from typing import Dict

MTTV_SIG: str = "0x4D5454562D464C50"


def facteur_protection(A3: float) -> float:
    """Facteur de protection multiplicatif : A3=1 → 1.0 ; A3=7 → 0.5."""
    return max(0.0, 1.0 - (A3 - 1.0) / 12.0)


def abattement_pourcentage(A3: float) -> float:
    """Abattement en % appliqué au score : A3=1 → 0 % ; A3=7 → 50 %."""
    return round((1.0 - facteur_protection(A3)) * 100.0, 1)


def score_protege(score: float, A3: float) -> float:
    """Score composite protégé par le facteur A3."""
    return score * facteur_protection(A3)


def diagnostic_isolement(A3: float) -> str:
    """Qualifie le niveau d'isolement source d'un agent."""
    if A3 <= 2:
        return "connecté à la source"
    if A3 <= 5:
        return "isolement modéré"
    return "isolé / dogmatique (absolutisation)"


def gouvernail_anti_solipsisme(score: float, A3: float, seuil: float = 0.45) -> Dict:
    """Applique le gouvernail A3 à un score et tranche une autorisation.

    Args:
        score: score composite brut (IGIC, résonance, …), ∈ [0, 1].
        A3: indice de non-isolement source (1..7).
        seuil: score protégé minimal pour autoriser la mutation.

    Returns:
        Dict : score brut, A3, facteur, score protégé, abattement, autorisation.
    """
    prot = facteur_protection(A3)
    mod = score * prot
    autorise = mod >= seuil
    return {
        "score_brut": round(score, 4),
        "a3": A3,
        "diagnostic_a3": diagnostic_isolement(A3),
        "facteur_protection": round(prot, 4),
        "abattement_pct": abattement_pourcentage(A3),
        "score_protege": round(mod, 4),
        "seuil": seuil,
        "autorise": autorise,
        "verdict": "AUTORISÉ" if autorise else "REJETÉ — solipsisme / dogmatisme",
        "sig": MTTV_SIG,
    }
