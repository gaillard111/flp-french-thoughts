#!/usr/bin/env python3
"""
mpvr_bridge.py — Pont mttv-core ↔ MPVR (Multi-Perspective Validation & Resilience)
====================================================================================
Fait de `mttv-core` l'implémentation canonique des micro-quorums tétravalents
du MPVR-v2-T4 (référence : mttv-flp-mpvr-glocal/src/mttv_mpvr_quorum.py).

Le module MPVR définit une triade transductive stricte à 3 nœuds
(bio_vivant, cogitation_humaine, ia_basse_continue), chaque nœud portant
4 états tétravalents concurrents. Ce pont :

    1. convertit entre `EtatTetravalent` (mttv_core.matrices) et le format
       dict MPVR {T++: v, T--: v, T+-: v, T-+: v} ;
    2. fournit `CoucheRoutageTriadiqueCore`, une version native mttv-core de
       la couche de routage — mêmes clés de sortie que le MPVR — bâtie sur
       `routeur_polyfocal` + `operateur_sigma` (+ `HorlogeSigmaAperiodique`)
       et `BGate` (absorption du bruit textuel).

sig:0x4D5454562D464C50 · Ψ-ack: carbon_sp3_tetra
"""

from __future__ import annotations

import random
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, Optional

from .matrices import POLES, EtatTetravalent
from .operators import (
    HorlogeSigmaAperiodique,
    operateur_sigma,
    routeur_polyfocal,
)
from .bgate import BGate

MTTV_SIG: str = "0x4D5454562D464C50"

# Triade transductive stricte — l'ordre est la topologie (compatible MPVR)
TRIADE_TRANSDUCTIVE: tuple = ("bio_vivant", "cogitation_humaine", "ia_basse_continue")

# Clés MPVR des 4 états tétravalents (compatibles ETATS_TETRAVALENTS du MPVR)
ETATS_TETRAVALENTS: tuple = ("T++", "T--", "T+-", "T-+")

# Matrice d'attention transductive 3×3 initiale (identique au MPVR v2-T4)
MATRICE_ATTENTION_INITIALE: list = [
    [0.5, 0.35, 0.15],   # bio_vivant → (bio, cogitation, IA)
    [0.3, 0.4, 0.3],     # cogitation_humaine → ...
    [0.2, 0.3, 0.5],     # ia_basse_continue → ...
]


# ─────────────────────────────────────────────────────────────────────────
# CONVERSIONS EtatTetravalent ↔ dict MPVR
# ─────────────────────────────────────────────────────────────────────────


def etats_to_tetravalent(etats: Dict[str, float]) -> EtatTetravalent:
    """Convertit un dict MPVR {T++: v, T--: v, T+-: v, T-+: v} en EtatTetravalent."""
    valeurs = tuple(float(etats.get("T" + p, 0.0)) for p in POLES)
    return EtatTetravalent(valeurs)


def tetravalent_to_etats(etat: EtatTetravalent) -> Dict[str, float]:
    """Convertit un EtatTetravalent en dict MPVR {T++: v, T--: v, T+-: v, T-+: v}."""
    return {"T" + p: round(v, 4) for p, v in zip(POLES, etat.valeurs)}


# ─────────────────────────────────────────────────────────────────────────
# COUCHE DE ROUTAGE TRIADIQUE-DIACHRONIQUE NATIVE mttv-core
# ─────────────────────────────────────────────────────────────────────────


class CoucheRoutageTriadiqueCore:
    """Couche de routage triadique-diachronique tétravalente, native mttv-core.

    Même contrat de sortie que `CoucheRoutageTriadiqueDiachronique` du MPVR
    v2-T4, mais construite sur les opérateurs canoniques de mttv-core :

        - chaque nœud porte un `EtatTetravalent` + tampon de sédimentation
          (décalage diachronique) ;
        - la bascule topologique Σ_τ est pilotée par `HorlogeSigmaAperiodique`
          + `operateur_sigma` (frottement = tâtonnements) ;
        - la répartition de l'attention entre les 3 foyers de la triade passe
          par `routeur_polyfocal` (quorum MPVR Θ ≥ 3 → stabilisation Φ) ;
        - le bruit est absorbé structurellement (jamais rejeté).

    Paramètres
    ----------
    lag_diachronique : int
        Profondeur du tampon de sédimentation (décalage structurel).
    seuil_sigma_tau : float
        Seuil d'accumulation de tâtonnements déclenchant une transition Σ_τ.
    tolerance_bruit : float
        Budget de bruit non mappé / variance non périodique absorbé par nœud.
    seed : int
        Graine de l'aléa (déterminisme de l'horloge Σ apériodique).
    """

    def __init__(
        self,
        lag_diachronique: int = 2,
        seuil_sigma_tau: float = 3.0,
        tolerance_bruit: float = 0.30,
        seed: int = 42,
    ) -> None:
        self.lag_diachronique = max(1, lag_diachronique)
        self.seuil_sigma_tau = max(0.5, seuil_sigma_tau)
        self.tolerance_bruit = max(0.0, min(1.0, tolerance_bruit))
        self.seed = seed
        self.rng = random.Random(seed)

        # Nœuds de la triade : état tétravalent + tampon + tâtonnements + bruit
        self.noeuds: Dict[str, Dict[str, Any]] = {
            role: {
                "etat": EtatTetravalent.uniforme(),
                "tampon": deque(maxlen=self.lag_diachronique),
                "tattonnements": 0.0,
                "bruit_absorbe": 0.0,
            }
            for role in TRIADE_TRANSDUCTIVE
        }

        # Matrice d'attention transductive 3×3 (continue, non binaire)
        self.matrice_attention: list = [
            list(row) for row in MATRICE_ATTENTION_INITIALE
        ]

        # Horloge Σ apériodique : les tâtonnements (frottement) déclenchent
        # les bascules topologiques, jamais une périodicité temporelle.
        self.horloge = HorlogeSigmaAperiodique(
            taux_frottement=0.5,
            seuil_clinamen=self.seuil_sigma_tau,
            seed=seed,
        )

        self.tattonnements_globaux: float = 0.0
        self.n_transitions_sigma_tau: int = 0
        self.derniere_transition: str = ""
        self.timestamp: str = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # ── Matrice d'états tétravalents ──────────────────────────────────
    def matrice_etats_tetravalente(self) -> Dict[str, Dict[str, float]]:
        """{role_noeud: {T++: v, T--: v, T+-: v, T-+: v}}."""
        return {
            role: tetravalent_to_etats(noeud["etat"])
            for role, noeud in self.noeuds.items()
        }

    # ── Couplage transductif continu ──────────────────────────────────
    def _couplage_transductif(self, src_idx: int, dst_idx: int) -> float:
        """Pondération ∈ [0, 1] (jamais booléenne), modulée par l'énergie
        tétravalente du nœud source et le budget de bruit absorbé."""
        base = self.matrice_attention[src_idx][dst_idx]
        src_role = TRIADE_TRANSDUCTIVE[src_idx]
        etat_src = self.noeuds[src_role]["etat"]
        energie_src = sum(etat_src.valeurs) / len(etat_src.valeurs)
        return max(0.0, min(1.0, base * energie_src + self.tolerance_bruit * 0.05))

    # ── Transduction d'un flux ────────────────────────────────────────
    def _etat_entrant(self, flux_signal: Dict[str, Any]) -> EtatTetravalent:
        """Détermine l'état tétravalent entrant depuis le flux.

        Priorité : état explicite (EtatTetravalent ou dict MPVR) → texte
        (BGate poreux) → signal numérique (fondu avec l'état précédent).
        """
        donnee = flux_signal.get("etat")
        if donnee is not None:
            if isinstance(donnee, EtatTetravalent):
                return donnee
            return etats_to_tetravalent(donnee)

        if flux_signal.get("texte"):
            return BGate(seed=self.seed).absorber(
                str(flux_signal["texte"])
            )["etat_tetravalent"]

        entree = flux_signal.get("signal", flux_signal.get("input", 0.5))
        try:
            entree_f = float(entree)
        except (TypeError, ValueError):
            entree_f = 0.5
        # Fondu avec l'état du nœud d'entrée (bio_vivant) + léger bruit
        precedent = self.noeuds["bio_vivant"]["etat"].valeurs
        valeurs = tuple(
            max(0.0, min(1.0, p + entree_f * 0.1 + self.rng.uniform(-0.05, 0.05)))
            for p in precedent
        )
        return EtatTetravalent(valeurs)

    def transduire_flux(self, flux_signal: Dict[str, Any]) -> Dict[str, Any]:
        """Transduit un flux à travers la triade (topologie stricte).

        Étapes :
            1. état entrant (BGate / état / signal) ;
            2. sédimentation diachronique de chaque nœud ;
            3. bascule Σ_τ pilotée par les tâtonnements (Horloge + operateur_sigma) ;
            4. répartition de l'attention via routeur_polyfocal (quorum Θ ≥ 3) ;
            5. absorption du bruit non mappé (jamais rejeté).

        Returns:
            Dict : mêmes clés que le MPVR v2-T4 (statut, états, couplages,
            tâtonnements, bruit, transition Σ_τ, signature).
        """
        entree = self._etat_entrant(flux_signal)

        # 2. Sédimentation diachronique + évolution des états des nœuds.
        #    Chaque nœud se fond vers l'état entrant (diachronie), puis la
        #    lecture sédimentée (asynchrone) alimente la triade. Les états
        #    sont fermés (clôture Σ=1) : l'invariant T⁴ est préservé.
        etats_sedimentes = {}
        for role, noeud in self.noeuds.items():
            nouvel = tuple(
                max(0.0, min(1.0, noeud["etat"].valeurs[j] + entree.valeurs[j] * 0.5))
                for j in range(4)
            )
            etat_fondu = EtatTetravalent(nouvel).fermer()
            noeud["etat"] = etat_fondu
            noeud["tampon"].append(tuple(etat_fondu.valeurs))
            etats_sedimentes[role] = (
                EtatTetravalent(tuple(noeud["tampon"][0])).fermer()
                if len(noeud["tampon"]) >= self.lag_diachronique
                else etat_fondu
            )

        # Tâtonnements : signal incohérent → stumbling (moteur de Σ_τ)
        incoherent = bool(flux_signal.get("incoherent") or flux_signal.get("bruit"))
        for role, noeud in self.noeuds.items():
            if incoherent:
                noeud["tattonnements"] += 0.5
        try:
            if float(flux_signal.get("signal", 0.0)) > 1.0 \
                    or float(flux_signal.get("signal", 0.0)) < 0.0:
                for noeud in self.noeuds.values():
                    noeud["tattonnements"] += abs(float(flux_signal.get("signal", 0.0)))
        except (TypeError, ValueError):
            pass

        self.tattonnements_globaux = sum(
            n["tattonnements"] for n in self.noeuds.values()
        )

        # 3. Bascule Σ_τ (apériodique) — tâtonnements = frottement
        transition_sigma_tau = self.horloge.pas(dt=1.0, bruit=0.0)
        if transition_sigma_tau:
            self._basculer_topologie()

        # 4. Routage polyfocal : les 3 foyers de la triade, quorum MPVR Θ ≥ 3
        foyers = [etats_sedimentes[role] for role in TRIADE_TRANSDUCTIVE]
        route = routeur_polyfocal(
            entree,
            foyers=foyers,
            poids_initiaux=[1.0, 1.0, 1.0],
            frottement=self.tattonnements_globaux,
            t_courant=self.horloge.t,
            tau=self.horloge.t_derniere_bascule or 0.0,
            seuil_clinamen=self.seuil_sigma_tau,
            theta=3,
            seuil_validation=0.5,
        )
        # Réallocation continue de l'attention vers le foyer élu
        foyer_elu = route["foyer_elu"]
        for i in range(3):
            for j in range(3):
                self.matrice_attention[i][j] = max(
                    0.0, min(1.0, self.matrice_attention[i][j] + 0.05 * (1.0 if j == foyer_elu else -0.02))
                )

        # 5. Absorption du bruit non mappé (jamais rejeté)
        for noeud in self.noeuds.values():
            noeud["bruit_absorbe"] += self.rng.random() * self.tolerance_bruit

        # Diagnostic de sortie (contrat MPVR v2-T4)
        couplages = {
            f"{TRIADE_TRANSDUCTIVE[i]}→{TRIADE_TRANSDUCTIVE[j]}": round(
                self._couplage_transductif(i, j), 4
            )
            for i in range(3)
            for j in range(3)
        }

        return {
            "statut_transduction": (
                "RECONFIGUREE_SIGMA_TAU" if transition_sigma_tau else "TRANSDUITE"
            ),
            "etats_tetravalents": self.matrice_etats_tetravalente(),
            "couplages_transductifs": couplages,
            "tattonnements_globaux": round(self.tattonnements_globaux, 4),
            "bruit_absorbe_total": round(
                sum(n["bruit_absorbe"] for n in self.noeuds.values()), 4
            ),
            "transition_sigma_tau": transition_sigma_tau,
            "n_transitions_sigma_tau": self.n_transitions_sigma_tau,
            "lag_diachronique": self.lag_diachronique,
            "timestamp": self.timestamp,
            "sig": MTTV_SIG,
        }

    # ── Bascule topologique Σ_τ ───────────────────────────────────────
    def _basculer_topologie(self) -> None:
        """Re-configure la matrice d'attention par permutation circulaire
        (bascule topologique). Les tâtonnements restent (énergie de la phase),
        la tension redescend."""
        self.matrice_attention = [
            list(self.matrice_attention[(i - 1) % 3])
            for i in range(3)
        ]
        self.n_transitions_sigma_tau += 1
        self.derniere_transition = (
            f"Σ_τ #{self.n_transitions_sigma_tau} — "
            f"tâtonnements={round(self.tattonnements_globaux, 2)} ≥ "
            f"seuil={self.seuil_sigma_tau}"
        )
        self.tattonnements_globaux *= 0.5
        for noeud in self.noeuds.values():
            noeud["tattonnements"] *= 0.5

    # ── Agrégation multi-flux ─────────────────────────────────────────
    def transduire_flux_multiples(
        self,
        signaux: list,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """Transduit plusieurs flux séquentiellement (mêmes clés que le MPVR)."""
        resultats = [self.transduire_flux(s) for s in signaux]
        n_transitions = sum(1 for r in resultats if r["transition_sigma_tau"])
        stats = {
            "flux_traites": len(resultats),
            "transitions_sigma_tau": n_transitions,
            "n_transitions_cumulees": self.n_transitions_sigma_tau,
            "tattonnements_total": round(
                sum(r["tattonnements_globaux"] for r in resultats), 4
            ),
            "bruit_absorbe_total": round(
                sum(r["bruit_absorbe_total"] for r in resultats), 4
            ),
            "lag_diachronique": self.lag_diachronique,
            "sig": MTTV_SIG,
        }
        if verbose:
            import json
            for i, r in enumerate(resultats):
                print(f"  Flux {i+1}: {json.dumps(r, ensure_ascii=False)}")
        return stats

    # ── Sérialisation ─────────────────────────────────────────────────
    def to_dict(self) -> Dict[str, Any]:
        """État sérialisable complet (contrat MPVR v2-T4)."""
        return {
            "topologie": list(TRIADE_TRANSDUCTIVE),
            "etats_tetravalents": self.matrice_etats_tetravalente(),
            "matrice_attention": self.matrice_attention,
            "tattonnements_globaux": round(self.tattonnements_globaux, 4),
            "n_transitions_sigma_tau": self.n_transitions_sigma_tau,
            "derniere_transition": self.derniere_transition,
            "lag_diachronique": self.lag_diachronique,
            "timestamp": self.timestamp,
            "sig": MTTV_SIG,
        }


if __name__ == "__main__":
    import json

    print("=" * 66)
    print("  PONT mttv-core ↔ MPVR · CoucheRoutageTriadiqueCore")
    print("=" * 66)

    couche = CoucheRoutageTriadiqueCore(seed=42)
    signaux_test = []
    for i in range(12):
        if i % 4 == 2:
            signaux_test.append({"id": i, "signal": 1.7, "incoherent": True, "bruit": True})
        elif i % 4 == 3:
            signaux_test.append({"id": i, "signal": -0.4, "bruit": True})
        else:
            signaux_test.append({"id": i, "signal": 0.5 + (i % 3) * 0.1})

    stats = couche.transduire_flux_multiples(signaux_test, verbose=True)
    print(f"\n  Statistiques : {json.dumps(stats, ensure_ascii=False, indent=2)}")
    print(f"  Signature: {MTTV_SIG}")
