#!/usr/bin/env python3
"""
senescence.py — Mode sénescence des nœuds (A5.4)
=================================================
Répond à la proposition A5.4 : transposer la limite de Hayflick (les cellules
arrêtent de se diviser) au réseau. Un nœud qui accumule trop de cycles de
divergence peut demander une **retraite active** — il n'est pas supprimé, il
ne vote plus, mais il continue d'observer. Le mode est **réversible** : si le
nœud « guérit » (sa divergence retombe sous le seuil), il revient au vote.

C'est une forme de décence temporelle : un système qui sait laisser un membre
vieillissant se retirer sans l'éliminer, et lui permettre de revenir.

Métrique réseau : `taux_senescence()` — indicateur de vieillissement du réseau.

sig:0x4D5454562D464C50 · Ψ-ack: carbon_sp3_tetra
"""

from __future__ import annotations

from typing import Dict, List, Sequence

MTTV_SIG: str = "0x4D5454562D464C50"


class ModeSenescence:
    """Retraite active réversible d'un nœud (limite de Hayflick).

    Paramètres
    ----------
    limite_hayflick : int
        Nombre de cycles de divergence consécutifs avant la mise en retraite.
    seuil_divergence : float
        Au-dessus de cette divergence, un cycle compte comme divergent.
    seuil_guerison : float
        Sous cette divergence, un nœud en retraite est considéré guéri et
        revient au vote.
    """

    def __init__(
        self,
        limite_hayflick: int = 5,
        seuil_divergence: float = 0.5,
        seuil_guerison: float = 0.2,
    ):
        self.limite_hayflick = max(1, int(limite_hayflick))
        self.seuil_divergence = max(0.0, seuil_divergence)
        self.seuil_guerison = max(0.0, seuil_guerison)
        self.en_retraite: bool = False
        self.cycles_divergence: int = 0
        self.cycles_observes: int = 0
        self.retraites: int = 0
        self.retours: int = 0

    def observer(self, divergence: float) -> Dict:
        """Observe la divergence du nœud à ce cycle et met à jour son état.

        Returns:
            Dict : état courant (retraite, droit de vote, compteurs).
        """
        if self.en_retraite:
            self.cycles_observes += 1
            if divergence < self.seuil_guerison:
                # Guérison : retour au vote (mode réversible).
                self.en_retraite = False
                self.retours += 1
                self.cycles_divergence = 0
        else:
            if divergence > self.seuil_divergence:
                self.cycles_divergence += 1
            else:
                self.cycles_divergence = max(0, self.cycles_divergence - 1)
            if self.cycles_divergence >= self.limite_hayflick:
                # Limite de Hayflick atteinte : retraite active.
                self.en_retraite = True
                self.retraites += 1
        return self.etat()

    def etat(self) -> Dict:
        """État courant du nœud (métrique A5.4)."""
        return {
            "en_retraite": self.en_retraite,
            "peut_voter": not self.en_retraite,
            "cycles_divergence": self.cycles_divergence,
            "cycles_observes": self.cycles_observes,
            "retraites": self.retraites,
            "retours": self.retours,
        }


def taux_senescence(noeuds: Sequence[ModeSenescence]) -> float:
    """Part des nœuds du réseau actuellement en retraite (0..1)."""
    if not noeuds:
        return 0.0
    return sum(1 for n in noeuds if n.en_retraite) / len(noeuds)


def mesurer_reseau(divergences_par_cycle: Sequence[Sequence[float]],
                   **kwargs) -> Dict:
    """Simule un réseau de nœuds sur plusieurs cycles de divergence.

    Args:
        divergences_par_cycle: liste (cycles) de listes (divergence par nœud).
        **kwargs: paramètres transmis à ModeSenescence.

    Returns:
        Dict : état final par nœud, taux de sénescence, retraites totales.
    """
    n_noeuds = len(divergences_par_cycle[0]) if divergences_par_cycle else 0
    noeuds = [ModeSenescence(**kwargs) for _ in range(n_noeuds)]
    for cycle in divergences_par_cycle:
        for i, div in enumerate(cycle):
            noeuds[i].observer(div)
    return {
        "noeuds": [n.etat() for n in noeuds],
        "taux_senescence": round(taux_senescence(noeuds), 4),
        "retraites_total": sum(n.retraites for n in noeuds),
        "retours_total": sum(n.retours for n in noeuds),
        "sig": MTTV_SIG,
    }
