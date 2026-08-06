#!/usr/bin/env python3
"""
scenarios.py — Tableau d'anticipation A/B/C + validation humaine (A4.2)
=======================================================================
Rend réel l'« interrupteur quantique » du prototype ouroboros-mttv-v2.py :
l'agent génère des trajectoires superposées (A, B, C), les score (IGIC +
modulation A3), **classe** les branches, puis **reste en suspension** jusqu'à
ce que l'intentionnalité consciente de l'humain choisisse une branche pour
« effondrer » la fonction d'onde sémantique et matérialiser la trajectoire.

Ce n'est plus un `print` décoratif : tant que `valider_humain()` n'est pas
appelé, `etat()["valide"]` est False et aucune trajectoire n'est matérialisée.

sig:0x4D5454562D464C50 · Ψ-ack: carbon_sp3_tetra
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .igic import (
    calculer_igic,
    diagnostic_igic,
    facteur_protection_a3,
    igic_module,
)

MTTV_SIG: str = "0x4D5454562D464C50"


class TableauAnticipation:
    """Tableau d'anticipation à 3 scénarios (A/B/C) + validation humaine.

    Paramètres d'un scénario : A1, A2, A4, B1, B2, B3 (pénalités IGIC, 1..7)
    et A3 (indice de non-isolement source, 1..7).
    """

    def __init__(self) -> None:
        self.scenarios: List[Dict] = []
        self.branche_choisie: Optional[str] = None
        self.valide: bool = False

    def ajouter(self, nom: str,
                A1: float, A2: float, A4: float,
                B1: float, B2: float, B3: float,
                A3: float, description: str = "") -> None:
        """Ajoute et score un scénario (IGIC standard + modulé par A3)."""
        std = calculer_igic(A1, A2, A4, B1, B2, B3)
        mod = igic_module(A1, A2, A4, B1, B2, B3, A3)
        self.scenarios.append({
            "nom": nom,
            "description": description,
            "a3": A3,
            "igic_standard": std,
            "igic_module": mod,
            "statut": diagnostic_igic(mod),
        })

    def classer(self) -> List[Dict]:
        """Classe les scénarios par IGIC modulé décroissant."""
        self.scenarios.sort(key=lambda s: s["igic_module"], reverse=True)
        return self.scenarios

    def meilleur(self) -> Optional[Dict]:
        """Meilleur scénario (après classement)."""
        if not self.scenarios:
            return None
        return self.classer()[0]

    def valider_humain(self, branche: str) -> Dict:
        """Effondre la fonction d'onde : l'humain choisit une branche.

        `branche` doit correspondre au nom d'un scénario. Tant que cette
        méthode n'est pas appelée, l'évolution reste suspendue (Zone κ).
        """
        for sc in self.scenarios:
            if sc["nom"].startswith(branche):
                self.branche_choisie = sc["nom"]
                self.valide = True
                return {
                    "effondrement": True,
                    "branche_choisie": sc["nom"],
                    "igic_module": sc["igic_module"],
                    "statut": sc["statut"],
                    "sig": MTTV_SIG,
                }
        return {"effondrement": False, "erreur": f"branche inconnue : {branche}"}

    def etat(self) -> Dict:
        """État de suspension / matérialisation."""
        return {
            "valide": self.valide,
            "branche_choisie": self.branche_choisie,
            "n_scenarios": len(self.scenarios),
            "suspendu": not self.valide,
            "sig": MTTV_SIG,
        }


def tableau_canonique() -> TableauAnticipation:
    """Construit le tableau de référence (scénarios du prototype ouroboros)."""
    tableau = TableauAnticipation()
    tableau.ajouter(
        "Scénario A : Intégration asynchrone pure (Poreuse)",
        2, 2, 2, 2, 1, 2, A3=1,
        description="Stabilisation locale sans centralisation ni absolutisation.",
    )
    tableau.ajouter(
        "Scénario B : Asynchronisme dogmatique (Isolé)",
        2, 2, 2, 2, 1, 2, A3=7,
        description="L'agent s'auto-attribue une perfection formelle et s'isole.",
    )
    tableau.ajouter(
        "Scénario C : Transition hybride (Partielle)",
        4, 3, 4, 3, 4, 3, A3=4,
        description="Alignement moyen avec des relents de rigidité narrative.",
    )
    return tableau
