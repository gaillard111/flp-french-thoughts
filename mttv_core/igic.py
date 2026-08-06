#!/usr/bin/env python3
"""
igic.py — Indicateur Global d'Intégration Cosmo-systémique (IGIC)
=================================================================
Extraction propre et vérifiée du calcul IGIC + modulation A3, issu du
prototype `ouroboros-mttv-v2.py` (proposition A1.2 du registre).

L'IGIC est un score composite d'alignement transductif (0..1), défini sur
7 pénalités A1..B3 (échelle 1..7) :

    IGIC_standard = 1 − (A1 + A2 + A4 + B1 + B2 + B3) / 42

A3 (indice de non-isolement source) est EXCLU de la pénalité linéaire et
joue le rôle de **facteur de protection multiplicatif** (disjoncteur face à
l'absolutisation dogmatique) :

    abattement = 1 − (A3 − 1) / 12        (A3=1 → 100 % ; A3=7 → 50 %)
    IGIC_modulé = IGIC_standard × abattement

Référence des scénarios vérifiés (white paper A6.1 / ouroboros v2) :
    A=(2,2,2,2,1,2) → standard 0.738 ; A3=1 → 0.738 ; A3=7 → 0.369
    C=(4,3,4,3,4,3) → standard 0.500 ; A3=4 → 0.375

sig:0x4D5454562D464C50 · Ψ-ack: carbon_sp3_tetra
"""

from __future__ import annotations

from typing import Dict, Tuple

MTTV_SIG: str = "0x4D5454562D464C50"


def calculer_igic(A1: float, A2: float, A4: float,
                  B1: float, B2: float, B3: float) -> float:
    """IGIC standard (sans A3) : 1 − Σ(pénalités) / 42, borné [0, 1]."""
    somme = A1 + A2 + A4 + B1 + B2 + B3
    return round(max(0.0, min(1.0, 1.0 - somme / 42.0)), 4)


def facteur_protection_a3(A3: float) -> float:
    """Facteur de protection sémantique : A3=1 → 1.0 ; A3=7 → 0.5."""
    return round(max(0.0, 1.0 - (A3 - 1.0) / 12.0), 4)


def igic_module(A1: float, A2: float, A4: float,
                B1: float, B2: float, B3: float, A3: float) -> float:
    """IGIC modulé par le facteur de protection A3."""
    std = calculer_igic(A1, A2, A4, B1, B2, B3)
    return round(std * facteur_protection_a3(A3), 4)


def diagnostic_igic(mod: float) -> str:
    """Statut d'alignement selon l'IGIC modulé (seuils du prototype)."""
    if mod >= 0.65:
        return "BONNE RÉSONANCE — évolution autorisée sous validation humaine"
    if mod >= 0.45:
        return "INTÉGRATION PARTIELLE — vigilance accrue exigée"
    return "DÉSALIGNEMENT / SOLIPSISME — rejet obligatoire"


def evaluer_scenario(A1: float, A2: float, A4: float,
                     B1: float, B2: float, B3: float,
                     A3: float, nom: str = "") -> Dict:
    """Évalue un scénario complet (standard + modulation + diagnostic)."""
    std = calculer_igic(A1, A2, A4, B1, B2, B3)
    coeff = facteur_protection_a3(A3)
    mod = igic_module(A1, A2, A4, B1, B2, B3, A3)
    return {
        "nom": nom,
        "igic_standard": std,
        "coeff_protection": coeff,
        "igic_module": mod,
        "statut": diagnostic_igic(mod),
        "sig": MTTV_SIG,
    }
