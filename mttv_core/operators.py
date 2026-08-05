#!/usr/bin/env python3
"""
operators.py — Opérateur de bascule Σ (singularité apériodique)
================================================================
Fonction `operateur_sigma` : singularité liminale à support temporel
compact (instant critique τ), conformément à SPEC-048 :

    Σ_τ(|Ψ(t)⟩) = p(τ)   avec support compact en τ
    Σ_t ≡ 0              ∀ t ≠ τ   (retrait fonctionnel)

Fonction `routeur_polyfocal` : routage du flux tétravalent entre N foyers
(perspectives), bascule topologique Σ + quorum MPVR (Θ ≥ 3).

Classe `HorlogeSigmaAperiodique` : planifie les instants critiques τ par
accumulation de frottement (tâtonnements / clinamen) — jamais par une
périodicité temporelle.

sig:0x4D5454562D464C50 · Ψ-ack: carbon_sp3_tetra
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Sequence, Tuple

from .matrices import POLES, TETRA_VERTICES, EtatTetravalent, to_sp3


# ─────────────────────────────────────────────────────────────────────────
# ÉVÉNEMENT Σ
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class EvenementSigma:
    """Résultat de l'opérateur de bascule Σ à l'instant critique τ.

    Attributes:
        tau: instant critique (support compact).
        declenche: True si la bascule a éclaté (clinamen mûr).
        impulsion: impulsion directionnelle p(τ) ∈ ℝ³ (boussole sp3).
        frottement_avant: frottement accumulé avant la bascule.
        frottement_apres: frottement après la bascule (0 si déclenchée).
    """

    tau: float
    declenche: bool
    impulsion: Tuple[float, float, float]
    frottement_avant: float
    frottement_apres: float

    def actif(self) -> bool:
        """L'opérateur est actif (impulsion non nulle) et déclenché."""
        return self.declenche and self.impulsion != (0.0, 0.0, 0.0)


def _impulsion_sp3(etat_psi: EtatTetravalent) -> Tuple[float, float, float]:
    """Impulsion directionnelle p(τ) : la « boussole créative ».

    Combiné du pôle dominant (direction sp3 du tétraèdre) et de la tension
    diachronique (dérivée du champ projetée sur la base sp3).
    """
    pole, part, _ = etat_psi.dominant()
    vertex = TETRA_VERTICES[POLES.index(pole)]
    tension = to_sp3(etat_psi.derivee())
    px = 0.7 * vertex[0] + 0.3 * tension[0]
    py = 0.7 * vertex[1] + 0.3 * tension[1]
    pz = 0.7 * vertex[2] + 0.3 * tension[2]
    n = math.sqrt(px * px + py * py + pz * pz)
    if n == 0.0:
        return (0.0, 0.0, 0.0)
    return (px / n, py / n, pz / n)


def operateur_sigma(
    etat_psi: EtatTetravalent,
    tau: float,
    frottement: float,
    t_courant: float,
    seuil_clinamen: float = 1.0,
    eps: float = 1e-3,
) -> EvenementSigma:
    """Opérateur de bascule Σ (singularité apériodique).

    Implémente le formalisme SPEC-048 §2.2 :
        - **Support compact** : Σ n'agit que dans la fenêtre |t − τ| ≤ ε.
          Partout ailleurs, Σ ≡ 0 (retrait fonctionnel : l'opérateur ne
          surveille rien, n'optimise rien, se retire radicalement).
        - **Clinamen** : à l'instant critique, la bascule n'éclate que si
          le frottement accumulé (tâtonnement) ≥ `seuil_clinamen`. Sinon
          le passage reste muet.

    Args:
        etat_psi: état du champ Ψ (pré-formel) portant la tension.
        tau: instant critique τ (support ponctuel).
        frottement: frottement accumulé (clinamen).
        t_courant: instant courant.
        seuil_clinamen: seuil de maturité du tâtonnement.
        eps: demi-largeur du support compact autour de τ.

    Returns:
        `EvenementSigma` : impulsion p(τ) si bascule, sinon (0, 0, 0).
    """
    # Retrait fonctionnel : hors du support compact, Σ ≡ 0.
    if abs(t_courant - tau) > eps:
        return EvenementSigma(tau, False, (0.0, 0.0, 0.0), frottement, frottement)

    # À l'instant critique : la bascule exige un clinamen mûr.
    if frottement < seuil_clinamen:
        return EvenementSigma(tau, False, (0.0, 0.0, 0.0), frottement, frottement)

    impulsion = _impulsion_sp3(etat_psi)
    return EvenementSigma(tau, True, impulsion, frottement, 0.0)


# ─────────────────────────────────────────────────────────────────────────
# HORLOGE Σ APÉRIODIQUE
# ─────────────────────────────────────────────────────────────────────────


class HorlogeSigmaAperiodique:
    """Horloge de bascule Σ non périodique.

    Le prochain instant critique τ n'est **jamais** fixé par une périodicité
    temporelle : il émerge de l'accumulation de frottement (tâtonnements /
    clinamen), y compris une composante stochastique (brisure de symétrie,
    Δθ_clinamen ≠ 0). La séquence de bascules est ainsi apériodique.
    """

    def __init__(
        self,
        taux_frottement: float = 0.3,
        seuil_clinamen: float = 1.0,
        amplitude_tatonnement: float = 0.15,
        seed: int = 42,
    ):
        self.taux_frottement = taux_frottement
        self.seuil_clinamen = seuil_clinamen
        self.amplitude_tatonnement = amplitude_tatonnement
        self.rng = random.Random(seed)
        self.frottement = 0.0
        self.t = 0.0
        self.instants_bascule: List[float] = []
        self.t_derniere_bascule: float = 0.0

    def pas(self, dt: float = 1.0, bruit: float = 0.0) -> bool:
        """Avance d'un pas temporel et accumule le frottement.

        Le frottement reçoit la base (`taux_frottement`), le `bruit` du
        milieu, et une composante stochastique de tâtonnement. Quand le
        seuil de clinamen est franchi, une bascule Σ éclate (support
        ponctuel) et le frottement se vide (retrait fonctionnel).

        Returns:
            True si une bascule Σ s'est produite à cet instant.
        """
        self.t += dt
        tatonnement = self.rng.uniform(-self.amplitude_tatonnement,
                                       self.amplitude_tatonnement)
        self.frottement += self.taux_frottement * dt + bruit + tatonnement
        if self.frottement >= self.seuil_clinamen:
            self.instants_bascule.append(self.t)
            self.t_derniere_bascule = self.t
            self.frottement = 0.0
            return True
        return False


# ─────────────────────────────────────────────────────────────────────────
# ROUTAGE POLYFOCAL
# ─────────────────────────────────────────────────────────────────────────


def routeur_polyfocal(
    entree: EtatTetravalent,
    foyers: Sequence[EtatTetravalent],
    poids_initiaux: Sequence[float],
    frottement: float,
    t_courant: float,
    tau: float,
    seuil_clinamen: float = 1.0,
    theta: int = 3,
    eps: float = 1e-3,
    seuil_validation: float = 0.5,
) -> dict:
    """Routage polyfocal du flux tétravalent entre N foyers (perspectives).

    Étapes (plan §3.2) :
        1. Score tétravalent de chaque foyer (résonance avec l'entrée +
           équilibre propre).
        2. Application de l'opérateur Σ : à l'instant critique τ, l'impulsion
           p(τ) bascule topologiquement les poids de routage (boost du foyer
           le plus aligné avec la boussole sp3).
        3. Sélection du foyer dominant (moindre action : le flux suit le
           foyer de plus forte résonance, sans négociation multi-tours).
        4. Quorum MPVR : un Φ n'est stabilisé que si Θ ≥ `theta`
           perspectives valident (invariant point 8.1 du benchmark).

    Args:
        entree: état tétravalent entrant (issu du B-gate, champ Ψ→B).
        foyers: perspectives candidates, chacune portant un EtatTetravalent.
        poids_initiaux: distribution de routage initiale (N valeurs).
        frottement: frottement global du milieu (clinamen).
        t_courant: instant courant.
        tau: instant critique de la bascule Σ.
        seuil_clinamen: seuil de maturité du tâtonnement.
        theta: quorum minimal de perspectives validantes (MPVR, Θ ≥ 3).
        eps: support compact de Σ.
        seuil_validation: résonance minimale pour qu'une perspective valide.

    Returns:
        Dict : poids finaux, foyer élu, résonances, événement Σ, état du
        quorum MPVR, et `phi_stabilise`.
    """
    n = len(foyers)
    if n == 0:
        raise ValueError("routeur_polyfocal : aucun foyer fourni")
    if len(poids_initiaux) != n:
        raise ValueError("routeur_polyfocal : poids_initiaux de longueur != n")

    # 1. Scores tétravalents : résonance avec l'entrée + équilibre propre.
    resonances = [entree.resonance(f) for f in foyers]
    equilibres = [f.equilibre() for f in foyers]
    scores = [0.7 * r + 0.3 * e for r, e in zip(resonances, equilibres)]

    # 2. Bascule Σ : l'impulsion p(τ) booste le foyer le plus aligné.
    evt = operateur_sigma(entree, tau, frottement, t_courant,
                          seuil_clinamen, eps)
    if evt.actif():
        meilleur = max(
            range(n),
            key=lambda i: sum(a * b for a, b in zip(
                evt.impulsion,
                TETRA_VERTICES[POLES.index(foyers[i].dominant()[0])],
            )),
        )
        boost = [1.0] * n
        boost[meilleur] = 1.5
    else:
        boost = [1.0] * n

    # 3. Poids de routage finals, normalisés.
    brut = [pi * s * b for pi, s, b in zip(poids_initiaux, scores, boost)]
    total = sum(brut)
    poids_finaux = [x / total for x in brut] if total > 0 else [1.0 / n] * n
    foyer_elu = max(range(n), key=lambda i: poids_finaux[i])

    # 4. Quorum MPVR : Θ perspectives doivent valider pour stabiliser Φ.
    nb_validations = sum(1 for r in resonances if r >= seuil_validation)
    quorum_ok = nb_validations >= theta

    return {
        "poids_finaux": poids_finaux,
        "foyer_elu": foyer_elu,
        "resonances": resonances,
        "scores": scores,
        "sigma": evt,
        "quorum": {
            "perspectives": n,
            "nb_validations": nb_validations,
            "theta": theta,
            "quorum_ok": quorum_ok,
        },
        "phi_stabilise": quorum_ok,
    }
