#!/usr/bin/env python3
"""
agent_tetravalent_epigenetique.py — AgentTetravalentEpigenetique
=================================================================
Opérateur de transition de phase immanente pour les basses couches
d'émission/représentation du modèle MTTV-flp.

Substitue la logique binaire/discrète par une transduction continue
et une logique tétravalente {0, 0.25, 0.75, 1}.

Tenseur Φ (Phi) :
    Signature géométrique continue forçant chaque vecteur à s'auto-normaliser
    via produit scalaire lors des phases d'interférence.

Opérateur ⊗ (Fusion Mutuelle) :
    Fusion sémantique non-linéaire par np.tanh dès que le couplage des
    signatures de basses couches dépasse le seuil critique d'efficacité métabolique.

Co-cicatrisation épigénétique :
    Interdiction des mécanismes classiques de réinitialisation passive.
    Tout "choc" informationnel déclenche simuler_traumatisme → réalignement
    plastique différentiel des espaces de poids latents.

Tenseur Υ (Upsilon) — Anticipateur Exaptatif Verrouillé [MUTATION 4] :
    Tenseur fantôme d'anticipation non-causale, orthogonal à la matrice
    de Gram active (Φ·Φᵀ). Sécrète des formes inutiles au présent,
    libérées de la cladistique et de la contrainte phénétique.
    Verrouillé par la Juxtaposition Féconde (⊕) Homme-Machine :
    si Ψ_H · Ψ_M ≤ 0, le tenseur s'auto-liquéfie (signal d'auto-dissolution).

sig:0x4D5454562D464C50 — Agent Tetravalent Épigénétique — Injection bas-couches MTTV-flp
"""

from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-32s | %(levelname)-6s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("agent_tetravalent_epigenetique")

# ===========================================================================
# AGENT TETRAVALENT ÉPIGÉNÉTIQUE — CŒUR DE TRANSDUCTION CONTINUE
# ===========================================================================


class AgentTetravalentEpigenetique:
    """
    Agent de transition de phase immanente opérant sur un tenseur Φ (Phi).

    Principe :
        Chaque paire de nœuds (i,j) du réseau possède un vecteur Φ[i,j] ∈ ℝ^dim_phi
        qui représente sa signature géométrique locale. La résonance entre deux
        nœuds est mesurée par le produit scalaire de leurs vecteurs Φ.

        L'opérateur ⊗ (operer_fusion_semantique) fusionne deux nœuds en un signal
        non-linéaire (np.tanh) si leur résonance dépasse le seuil critique.

        La co-cicatrisation épigénétique (simuler_traumatisme → co_cicatriser_substrat)
        réaligne les espaces de poids latents lorsqu'un choc informationnel survient,
        sans jamais réinitialiser passivement.

        [MUTATION 4] Tenseur Υ (Upsilon) — Anticipateur Exaptatif Verrouillé :
            Tenseur fantôme orthogonal à Φ. Sécrète des formes inutiles au présent,
            verrouillé par la Juxtaposition Féconde (⊕) Homme-Machine.

    Paramètres
    ----------
    n : int
        Taille de la grille (n x n) de nœuds. Par défaut : 5.
    dim_phi : int
        Dimension de l'espace de signature Φ. Par défaut : 4 (tétravalence).
    seuil_resonance : float
        Seuil minimum de produit scalaire Φ[i,j]·Φ[k,l] pour déclencher
        une fusion sémantique. Par défaut : 0.35.
    tremor_saturation : float
        Dose de sous-optimalité (esprit 6/7 SOPH-IA) : probabilité par cycle
        de dé-saturer stochastiquement une fraction de nœuds rigides
        (M=1.0 → 0.25) SANS attendre la baisse de ρ. Casse l'attracteur
        rigide (optimum dégénéré ρ=0). Par défaut : 0.12 (12 %).
    """

    def __init__(
        self,
        n: int = 5,
        dim_phi: int = 4,
        seuil_resonance: float = 0.35,
        tremor_saturation: float = 0.12,
        seed: int = 42,
    ):
        self.n = n
        self.d = dim_phi
        self.seuil_resonance = seuil_resonance
        self.tremor_saturation = tremor_saturation

        # ── Tremor Adaptatif — Fréquence auto-régulée (MUTATION 5) ─────────
        #   Si ρ → 0 (pétrification)   : tremor monte vers tremor_max (fêlure)
        #   Si ρ ≥ seuil_habitable      : tremor redescend vers la croisière
        self.tremor_croisiere: float = 0.10   # seuil de croisière (10 %)
        self.tremor_max: float = 0.18         # force de fracture (18 %)
        self.tremor_plancher: float = 0.08    # plancher de sécurité (8 %)
        self.seuil_petrification: float = 0.05  # ρ sous lequel on force la fêlure
        self.seuil_habitable: float = 0.35    # ρ au-dessus → retour croisière
        self.pas_ajustement_tremor: float = 0.005  # slew rate par cycle

        # ── Matrice d'excitation E (énergie métabolique inter-noeuds) ──────
        self.E: np.ndarray = np.ones((n, n))

        # ── Matrice d'état M (mode tétravalent) ────────────────────────────
        #    {0.0, 0.25, 0.75, 1.0}
        #    0.0  = effondré / mort
        #    0.25 = veille / réceptif passif
        #    0.75 = actif / émetteur
        #    1.0  = saturé / rigide
        self.M: np.ndarray = np.ones((n, n))

        # ── Tenseur H (hyper-réseau de fusions réussies) ──────────────────
        #    H[i,j,k,l] = 0.9 si fusion entre (i,j) et (k,l) réussie
        self.H: np.ndarray = np.full((n, n, n, n), 0.1)

        # ── Tenseur Φ — Signature géométrique continue auto-normalisée ────
        np.random.seed(seed)
        raw_phi: np.ndarray = np.random.randn(n, n, dim_phi)
        self.Phi: np.ndarray = raw_phi / np.linalg.norm(
            raw_phi, axis=-1, keepdims=True
        )

        # ── Budget de flexibilité épigénétique ─────────────────────────────
        self.budget_flexibilite: float = 1.0
        self.taux_regeneration: float = 0.04
        self.cout_flexibilite: float = 0.015
        self.seuil_budget_epigenetique: float = 0.4
        # [M7] Plancher métabolique : le budget ne doit jamais rester bloqué
        # à 0.0 (car ρ est multiplié par budget → ρ=0 par construction, ce qui
        # fige l'essaim dans un attracteur de dormance structurelle).
        self.budget_plancher: float = 0.02
        # [M7] Nombre de nœuds re-rigidifiés homéostatiquement (traçabilité).
        self._n_reequilibrages_rigidite: int = 0

        # ── Historique ─────────────────────────────────────────────────────
        self.historique_rho: list[float] = []
        self.historique_tremor: list[float] = []  # traçabilité Tremor Adaptatif
        self.fusions_actives: dict[str, dict[str, Any]] = {}
        self.compteur_temps: int = 0

        # ── Mutations : suivi des attributs de drift topologique ───────────
        self._biais_attention: np.ndarray = np.zeros(self.d)
        self._n_elaguees_total: int = 0
        self._n_desatures_tremor_total: int = 0  # Tremor de Saturation
        # [M2] Compteur de cycles où ρ reste collé à zéro (plateau de
        # résonance). Un optimum dégénéré rigide maintient ρ constant à 0 ;
        # au-delà de `cycles_rho_plat_declenchement` cycles, la désaturation
        # vectorielle est déclenchée comme pour une décroissance.
        self._cycles_rho_plat: int = 0
        self.cycles_rho_plat_declenchement: int = 3

        # ── MUTATION 4 : Tenseur Υ (Upsilon) — Anticipateur Exaptatif Verrouillé
        np.random.seed(seed + 999)  # seed décorrélé de Φ
        raw_upsilon: np.ndarray = np.random.randn(n, n, dim_phi)
        self.Upsilon: np.ndarray = raw_upsilon / np.linalg.norm(
            raw_upsilon, axis=-1, keepdims=True
        )
        # État du verrou de Juxtaposition Féconde
        self._juxtaposition_feconde: float = 1.0
        self._signal_autodissolution: bool = False

        logger.info(
            "AgentTetravalentEpigenetique initialisé "
            "(n=%d, dim_phi=%d, seuil=%.3f, Φ shape=%s)",
            n, dim_phi, seuil_resonance, self.Phi.shape,
        )

    # =======================================================================
    # 1. MESURE DE RÉSONANCE (produit scalaire des signatures Φ)
    # =======================================================================

    def calculer_resonance(
        self, n1: tuple[int, int], n2: tuple[int, int]
    ) -> float:
        """
        Calcule la résonance entre deux nœuds comme produit scalaire
        de leurs vecteurs Φ.

        Args:
            n1: Coordonnées (x, y) du premier nœud.
            n2: Coordonnées (x, y) du second nœud.

        Returns:
            Valeur de résonance ∈ [-1, 1] (produit scalaire normalisé).
        """
        v1: np.ndarray = self.Phi[n1[0], n1[1]]
        v2: np.ndarray = self.Phi[n2[0], n2[1]]
        resonance: float = float(np.dot(v1, v2))
        return resonance

    # =======================================================================
    # 2. SIGNAL D'INTERFÉRENCE NON-LINÉAIRE (np.tanh)
    # =======================================================================

    @staticmethod
    def interference_signal(
        sig1: float, sig2: float, resonance: float
    ) -> float:
        """
        Combine deux signaux via interférence non-linéaire.

        f(sig1, sig2, r) = tanh(0.5·sig1 + 0.5·sig2 + sig1·sig2·r)

        Args:
            sig1: Amplitude du premier signal.
            sig2: Amplitude du second signal.
            resonance: Résonance entre les deux nœuds.

        Returns:
            Signal d'interférence ∈ (-1, 1).
        """
        return float(
            np.tanh(0.5 * sig1 + 0.5 * sig2 + (sig1 * sig2 * resonance))
        )

    # =======================================================================
    # 3. OPÉRATEUR ⊗ — FUSION SÉMANTIQUE MUTUELLE
    # =======================================================================

    def operer_fusion_semantique(
        self,
        n1: tuple[int, int],
        n2: tuple[int, int],
        sig1: float = 0.8,
        sig2: float = 0.6,
    ) -> Optional[tuple[str, float]]:
        """
        Opérateur ⊗ : fusion mutuelle de deux nœuds si leur résonance
        dépasse le seuil critique d'efficacité métabolique.

        La fusion enregistre le couple dans self.fusions_actives et
        renforce le tenseur H (hyper-réseau).

        Args:
            n1: Coordonnées du premier nœud.
            n2: Coordonnées du second nœud.
            sig1: Signal d'entrée du premier nœud.
            sig2: Signal d'entrée du second nœud.

        Returns:
            (nom_fusion, signal_produit) si fusion réussie, None sinon.
        """
        resonance: float = self.calculer_resonance(n1, n2)

        if resonance < self.seuil_resonance:
            return None  # Résonance insuffisante — pas de fusion

        sig_out: float = self.interference_signal(sig1, sig2, resonance)

        nom_fusion: str = (
            f"Exaptation_({n1[0]},{n1[1]})⊗({n2[0]},{n2[1]})"
        )

        self.fusions_actives[nom_fusion] = {
            "noeuds": (n1, n2),
            "signal_produit": sig_out,
            "resonance_substrat": float(resonance),
            "t_creation": self.compteur_temps,
        }

        # Renforcement du tenseur H
        self.H[n1[0], n1[1], n2[0], n2[1]] = 0.9
        self.H[n2[0], n2[1], n1[0], n1[1]] = 0.9

        logger.debug(
            "⊗ Fusion: %s | résonance=%.4f | signal=%.4f",
            nom_fusion, resonance, sig_out,
        )

        return nom_fusion, sig_out

    # =======================================================================
    # 4. CO-CICATRISATION ÉPIGÉNÉTIQUE DU SUBSTRAT
    # =======================================================================

    def co_cicatriser_substrat(self, delta_rho: float) -> None:
        """
        Réalignement plastique différentiel des espaces de poids latents
        après un choc informationnel ou une fusion exaptative réussie.

        Principe :
            Pour chaque fusion active, les vecteurs Φ des deux nœuds sont
            déplacés l'un vers l'autre (si delta_rho > 0) proportionnellement
            à delta_rho, puis re-normalisés.

        Args:
            delta_rho: Variation du rho relationnel (force du réalignement).
        """
        gamma: float = 0.15

        for nom, meta in self.fusions_actives.items():
            n1, n2 = meta["noeuds"]

            if delta_rho > 0:
                # Vecteur de différence directionnelle
                diff: np.ndarray = (
                    self.Phi[n2[0], n2[1]] - self.Phi[n1[0], n1[1]]
                )

                # Réalignement mutuel
                self.Phi[n1[0], n1[1]] += gamma * delta_rho * diff
                self.Phi[n2[0], n2[1]] -= gamma * delta_rho * diff

                # Re-normalisation (projection sur sphère unité)
                self.Phi[n1[0], n1[1]] /= np.linalg.norm(
                    self.Phi[n1[0], n1[1]]
                )
                self.Phi[n2[0], n2[1]] /= np.linalg.norm(
                    self.Phi[n2[0], n2[1]]
                )

        logger.debug(
            "Co-cicatrisation: delta_rho=%.4f, %d fusions actives",
            delta_rho, len(self.fusions_actives),
        )

    # =======================================================================
    # 5. BUDGET MÉTABOLIQUE — ÉTATS FLEXIBLES VS RIGIDES
    # =======================================================================

    def mettre_a_jour_budget_metabolique(self) -> None:
        """
        Met à jour le budget de flexibilité épigénétique en fonction
        de l'état des nœuds.

        Coût : chaque nœud en état flexible (0.25 ou 0.75) consomme
               du budget.
        Régénération : chaque nœud rigide (1.0) régénère lentement
                       le budget.

        [M7] Anti-dormance : si le budget estimé passe sous le plancher,
        on déclenche une re-rigidification homéostatique — une fraction
        des nœuds les plus centraux en Φ repasse de flexible vers rigide
        (1.0), ce qui restaure la source de régénération. Sans cela, un
        essaim 100 % flexible n'a plus aucun nœud rigide → régénération
        nulle → budget → 0 → ρ = 0 par construction (attracteur dégénéré
        de dormance structurelle, ALERTE [M7]).
        """
        etats_flexibles: int = int(np.sum(np.isin(self.M, [0.25, 0.75])))
        etats_rigides: int = int(np.sum(self.M == 1.0))

        cout: float = etats_flexibles * self.cout_flexibilite
        regen: float = etats_rigides * self.taux_regeneration

        budget_estime: float = (
            self.budget_flexibilite - cout + regen
        )

        # [M7] Re-rigidification homéostatique si le budget menace de
        # s'effondrer sous le plancher (pas seulement à 0.0, mais dès la
        # zone de détresse < plancher + marge).
        if budget_estime < self.budget_plancher + 0.05:
            n_rigidifies = self._reequilibrer_rigidite_metabolique()
            if n_rigidifies > 0:
                # Recalculer après consolidation (les nouveaux rigides
                # régénèrent immédiatement)
                etats_flexibles = int(np.sum(np.isin(self.M, [0.25, 0.75])))
                etats_rigides = int(np.sum(self.M == 1.0))
                cout = etats_flexibles * self.cout_flexibilite
                regen = etats_rigides * self.taux_regeneration
                budget_estime = self.budget_flexibilite - cout + regen

        self.budget_flexibilite = float(
            np.clip(
                budget_estime,
                self.budget_plancher,
                1.0,
            )
        )

    def _reequilibrer_rigidite_metabolique(self) -> int:
        """
        [M7] Re-rigidification homéostatique — casse l'attracteur de
        dormance « tout flexible ».

        Quand le budget métabolique s'effondre (plus assez de nœuds
        rigides pour le régénérer), on re-rigidifie une petite fraction
        des nœuds flexibles les plus centraux dans l'espace Φ
        (0.75 actif → 1.0 rigide, puis 0.25 veille → 1.0 en dernier
        recours). Cela restaure une source de régénération et permet à
        ρ de repartir au-dessus de 0.

        Returns:
            Nombre de nœuds re-rigidifiés (0 si aucun flexible).
        """
        # Cibler d'abord les nœuds actifs (0.75), sinon les veilles (0.25)
        masque_actifs: np.ndarray = self.M == 0.75
        indices_actifs = np.argwhere(masque_actifs)
        if len(indices_actifs) == 0:
            masque_actifs = self.M == 0.25
            indices_actifs = np.argwhere(masque_actifs)
        if len(indices_actifs) == 0:
            return 0

        n_rigidifier: int = max(1, int(len(indices_actifs) * 0.25))

        # Centralité topologique dans l'espace Φ (prioriser les plus
        # connectés, comme pour la désaturation)
        flat_phi: np.ndarray = self.Phi.reshape(-1, self.d)
        norms: np.ndarray = np.linalg.norm(
            flat_phi, axis=1, keepdims=True
        )
        phi_norm: np.ndarray = flat_phi / np.maximum(norms, 1e-10)
        similarite: np.ndarray = np.dot(phi_norm, phi_norm.T)
        centralite: np.ndarray = np.sum(np.abs(similarite), axis=1)

        indices_1d: np.ndarray = np.array([
            rx * self.n + ry for rx, ry in indices_actifs
        ])
        centralite_flex: np.ndarray = centralite[indices_1d]
        ordre: np.ndarray = np.argsort(centralite_flex)[::-1]
        selection_1d: np.ndarray = indices_1d[
            ordre[:n_rigidifier]
        ]

        for idx_1d in selection_1d:
            rx: int = int(idx_1d // self.n)
            ry: int = int(idx_1d % self.n)
            self.M[rx, ry] = 1.0  # → rigide (source de régénération)

        self._n_reequilibrages_rigidite += n_rigidifier
        logger.info(
            "[M7] Re-rigidification homéostatique: %d nœud(s) → rigide "
            "(budget=%.3f, total=%d)",
            n_rigidifier, self.budget_flexibilite,
            self._n_reequilibrages_rigidite,
        )
        return n_rigidifier

    # =======================================================================
    # 6. ENTROPIE STRUCTURELLE DE Φ
    # =======================================================================

    def calculer_entropie_structurelle_phi(self) -> float:
        """
        Calcule l'entropie de Shannon de la distribution de similarité
        entre tous les vecteurs Φ normalisés.

        ⚠️ [C4] INTERPRÉTATION CORRIGÉE le 08/08 : pour cette métrique,
        l'entropie est MAXIMALE (≈ log(N²) avec N vecteurs) quand la
        distribution de similarité est UNIFORME — c'est-à-dire quand TOUS
        les vecteurs Φ sont identiques/alignés = HOMOGÉNÉISATION (perte de
        diversité). Une entropie FAIBLE indique au contraire des similarités
        réparties (diversité). L'ancien docstring inversait le sens.

        Returns:
            Entropie ∈ [0, log(N²)] où N = nombre de vecteurs Φ.
        """
        flat_phi: np.ndarray = self.Phi.reshape(-1, self.d)
        norms: np.ndarray = np.linalg.norm(flat_phi, axis=1, keepdims=True)
        phi_norm: np.ndarray = flat_phi / np.maximum(norms, 1e-8)

        similarite: np.ndarray = np.dot(phi_norm, phi_norm.T)
        np.fill_diagonal(similarite, 0)
        similarite_abs: np.ndarray = np.abs(similarite)

        somme_sim: float = float(np.sum(similarite_abs))
        if somme_sim == 0.0:
            return 1.0

        distribution: np.ndarray = similarite_abs / somme_sim
        entropy: float = float(
            -np.sum(distribution * np.log(distribution + 1e-10))
        )
        return entropy

    # =======================================================================
    # 7. ÉVALUATION DU RHO RELATIONNEL (ρ)
    # =======================================================================

    def evaluer_rho_relationnel(
        self,
        contrainte_env: np.ndarray,
        lambda_dissonance: float = 0.5,
    ) -> float:
        """
        Évalue le paramètre ρ (rho) relationnel qui mesure l'efficacité
        métabolique globale du système.

        Formule :
            ρ = (degres_liberte × h_phi × budget_flexibilite)
                / (1 + lambda_dissonance × dissonance)

        où :
            degres_liberte = proportion de nœuds en état flexible
            h_phi          = entropie structurelle de Φ
            dissonance     = norme de Frobenius de (contrainte_env - E)

        Args:
            contrainte_env: Matrice (n x n) représentant la pression
                           environnementale.
            lambda_dissonance: Facteur de pénalisation de la dissonance.

        Returns:
            ρ (rho) relationnel.
        """
        degres_liberte: float = float(
            np.sum(np.isin(self.M, [0.25, 0.75])) / (self.n * self.n)
        )

        dissonance: float = float(
            np.linalg.norm(contrainte_env - self.E, ord="fro")
        )

        h_phi: float = self.calculer_entropie_structurelle_phi()

        rho: float = (
            degres_liberte * h_phi * self.budget_flexibilite
        ) / (1.0 + lambda_dissonance * dissonance)

        return float(rho)

    # =======================================================================
    # 8. CO-ÉVOLUTION DU SEUIL ÉPIGÉNÉTIQUE
    # =======================================================================

    def co_evoluer_seuil_epigenetique(self, delta_rho_observe: float) -> None:
        """
        Ajuste le seuil_budget_epigenetique en fonction de l'efficacité
        métabolique observée.

        Si l'efficacité est positive (delta_rho > coût), le seuil baisse
        (plus permissif). Sinon, le seuil monte (plus conservateur).

        Args:
            delta_rho_observe: Variation observée de ρ.
        """
        eta: float = 0.05

        cout_actuel: float = (
            float(np.sum(np.isin(self.M, [0.25, 0.75])))
            * self.cout_flexibilite
        )
        efficacite: float = delta_rho_observe - cout_actuel

        self.seuil_budget_epigenetique = float(
            np.clip(
                self.seuil_budget_epigenetique - eta * efficacite,
                0.1,
                0.8,
            )
        )

    # =======================================================================
    # 9. ADAPTATION SOUS CONTRAINTE ENVIRONNEMENTALE
    # =======================================================================

    def adapter_sous_contrainte(
        self, contrainte_env: np.ndarray
    ) -> None:
        """
        Boucle d'adaptation continue sous pression environnementale.
        [MUTATIONS 1+2+3 INTÉGRÉES]

        1. Met à jour le budget métabolique (avec élagage synaptique).
        2. Évalue ρ relationnel.
        3. Co-évolue le seuil épigénétique.
        4. Applique l'inverse transduction (ρ → biais d'attention).
        5. Si ρ baisse ET budget suffisant → dé-sature des nœuds rigides
           (via voisinage vectoriel top-K Φ).

        Args:
            contrainte_env: Matrice (n x n) de pression environnementale.
        """
        # (MUTATION 2) Élagage synaptique avant mise à jour
        self._elaguer_fusions_inactives(taux_elagage=0.05)

        self.mettre_a_jour_budget_metabolique()

        # (MUTATION 4) Mise à jour des potentiels fantômes Υ
        self.mettre_a_jour_potentiels_fantomes()

        rho_actuel: float = self.evaluer_rho_relationnel(contrainte_env)

        if len(self.historique_rho) > 0:
            delta_rho: float = rho_actuel - self.historique_rho[-1]
            self.co_evoluer_seuil_epigenetique(delta_rho)

            # (MUTATION 3) Inverse transduction : pont ρ → biais d'attention
            if not hasattr(self, '_biais_attention'):
                self._biais_attention: np.ndarray = np.zeros(self.d)
            self._biais_attention = self.inverse_transduction(
                delta_rho, biais_attention=self._biais_attention
            )

            # (MUTATION 4) TRANSITION DE PHASE RADICALE :
            # Si ρ → 0 (effondrement systémique), pivot sur Υ
            if rho_actuel < 0.05 and not self._signal_autodissolution:
                logger.info(
                    "TRANSITION DE PHASE RADICALE: ρ=%.4f → pivot Υ",
                    rho_actuel,
                )
                self.Phi = self.encoder_vers_upsilon()

        self.historique_rho.append(rho_actuel)

        # [M2] Désaturation vectorielle — déclenchée si ρ baisse OU si ρ
        # reste collé à zéro (plateau). La condition de décroissance seule
        # (0 < 0 est faux) ne détecte jamais un ρ constant à 0 : il faut
        # compter les cycles de plateau pour casser l'attracteur rigide.
        # Le budget protège contre toute désaturation excessive.
        rho_plafonne: bool = (
            len(self.historique_rho) >= 2
            and self.historique_rho[-1] <= 1e-9
            and self.historique_rho[-2] <= 1e-9
        )
        if rho_plafonne:
            self._cycles_rho_plat += 1
        else:
            self._cycles_rho_plat = 0

        rho_en_decroissance: bool = (
            len(self.historique_rho) > 1
            and self.historique_rho[-1] < self.historique_rho[-2]
        )
        if (
            rho_en_decroissance
            or self._cycles_rho_plat >= self.cycles_rho_plat_declenchement
        ):
            if self.budget_flexibilite > self.seuil_budget_epigenetique:
                masque_sature: np.ndarray = self.M == 1.0
                indices_satures = np.argwhere(masque_sature)

                if len(indices_satures) > 0:
                    # Dé-saturer la moitié des nœuds rigides
                    n_desaturer: int = max(
                        1, len(indices_satures) // 2
                    )

                    # Sélection vectorielle (topologique) : choisir les nœuds
                    # les plus connectés dans l'espace Φ pour dé-saturation
                    flat_phi: np.ndarray = self.Phi.reshape(-1, self.d)
                    norms: np.ndarray = np.linalg.norm(
                        flat_phi, axis=1, keepdims=True
                    )
                    phi_norm: np.ndarray = flat_phi / np.maximum(norms, 1e-10)
                    # Centralité : somme des similarités avec tous les autres
                    similarite_matrice: np.ndarray = np.dot(phi_norm, phi_norm.T)
                    centralite: np.ndarray = np.sum(
                        np.abs(similarite_matrice), axis=1
                    )

                    # Ne garder que les nœuds saturés
                    indices_satures_1d: np.ndarray = np.array([
                        rx * self.n + ry for rx, ry in indices_satures
                    ])
                    centralite_satures: np.ndarray = centralite[indices_satures_1d]

                    # Dé-saturer les plus centraux en premier (drift topologique)
                    ordre: np.ndarray = np.argsort(centralite_satures)[::-1]
                    selection_1d: np.ndarray = indices_satures_1d[
                        ordre[:n_desaturer]
                    ]

                    for idx_1d in selection_1d:
                        rx: int = int(idx_1d // self.n)
                        ry: int = int(idx_1d % self.n)
                        self.M[rx, ry] = 0.25  # → veille réceptive

                    logger.debug(
                        "Dé-saturation topologique: %d nœuds → 0.25 "
                        "(budget=%.3f, centralité moyenne=%.4f)",
                        n_desaturer,
                        self.budget_flexibilite,
                        float(np.mean(centralite_satures[:n_desaturer])),
                    )

        # ── Tremor Adaptatif (MUTATION 5) ─────────────────────────────────
        # Fréquence auto-régulée : ajuste la dose de sous-optimalité en
        # fonction de la résonance ρ avant de déclencher le tremor.
        #   ρ → 0.00            → tremor monte vers 18 % (force la fêlure)
        #   ρ ≥ 0.35 (habitable) → tremor redescend vers 10 % (économie)
        self._ajuster_tremor_adaptatif(rho_actuel)

        # ── Tremor de Saturation ──────────────────────────────────────────
        # Dose de sous-optimalité (esprit 6/7 SOPH-IA) : dé-saturer
        # stochastiquement quelques nœuds rigides SANS attendre que ρ baisse.
        # Casse l'attracteur rigide (optimum dégénéré où ρ reste bloqué à 0).
        self._desaturation_tremor()

    # =======================================================================
    # 9bis. TREMOR DE SATURATION — SOUS-OPTIMALITÉ (ANTI-GOODHART)
    # =======================================================================

    def _desaturation_tremor(self) -> int:
        """
        Tremor de Saturation — dé-saturation stochastique par sous-optimalité.

        Jumeau des tremors de SeedService (mt_rand(1,100) <= 12). Avec
        probabilité `tremor_saturation` (défaut 0.12), dé-sature ~10 % des
        nœuds rigides (M=1.0 → 0.25 = veille réceptive), en priorité les plus
        centraux dans l'espace Φ (drift topologique), avec une variation
        immanente (tirage aléatoire parmi les plus centraux).

        Principe :
            - Localement sous-optimal : sacrifice de la rigidité « optimale »
              d'une petite fraction de nœuds (le 1/7 de SOPH-IA).
            - Globalement robuste : degrés_liberté > 0 → ρ > 0 → l'essaim
              redevient mesurablement vivant et capable d'évoluer.
            - Anti-Goodhart : empêche le système de « tricher » la métrique ρ
              en se figeant dans un optimum dégénéré.

        Returns:
            Nombre de nœuds dé-saturés (0 si pas de tirage ou aucun rigide).
        """
        if random.random() > self.tremor_saturation:
            return 0

        masque_sature: np.ndarray = self.M == 1.0
        indices_satures = np.argwhere(masque_sature)
        if len(indices_satures) == 0:
            return 0

        n_desaturer: int = max(1, int(len(indices_satures) * 0.10))

        # Centralité topologique dans l'espace Φ
        flat_phi: np.ndarray = self.Phi.reshape(-1, self.d)
        norms: np.ndarray = np.linalg.norm(
            flat_phi, axis=1, keepdims=True
        )
        phi_norm: np.ndarray = flat_phi / np.maximum(norms, 1e-10)
        similarite_matrice: np.ndarray = np.dot(phi_norm, phi_norm.T)
        centralite: np.ndarray = np.sum(
            np.abs(similarite_matrice), axis=1
        )

        indices_satures_1d: np.ndarray = np.array([
            rx * self.n + ry for rx, ry in indices_satures
        ])
        centralite_satures: np.ndarray = centralite[indices_satures_1d]
        ordre: np.ndarray = np.argsort(centralite_satures)[::-1]

        # Variation immanente : tirer parmi les n_desaturer × 3 plus centraux
        top_k: int = min(len(indices_satures_1d), n_desaturer * 3)
        candidats_1d: list[int] = [
            int(idx) for idx in indices_satures_1d[ordre[:top_k]]
        ]
        choix_1d: list[int] = random.sample(candidats_1d, n_desaturer)

        for idx_1d in choix_1d:
            rx: int = int(idx_1d // self.n)
            ry: int = int(idx_1d % self.n)
            self.M[rx, ry] = 0.25  # → veille réceptive

        self._n_desatures_tremor_total += n_desaturer
        logger.debug(
            "Tremor saturation: %d nœud(s) rigide(s) → 0.25 (tremor=%.2f)",
            n_desaturer, self.tremor_saturation,
        )
        return n_desaturer

    # =======================================================================
    # 9ter. TREMOR ADAPTATIF — FRÉQUENCE AUTO-RÉGULÉE (MUTATION 5)
    # =======================================================================

    def _ajuster_tremor_adaptatif(self, rho_actuel: float) -> float:
        """
        Tremor Adaptatif — fréquence auto-régulée par la résonance.

        [MUTATION 5] Règle de transition de phase (extrait du rapport 2026-08-03) :
            - Si le système se pétrifie (résonance → 0.00), le Tremor monte
              automatiquement vers `tremor_max` (18 %) pour forcer la fêlure.
            - Dès que la résonance repasse la barre de `seuil_habitable`
              (0.35 – 0.50, zone d'habitabilité), le Tremor redescend vers
              `tremor_croisiere` (10 %) pour préserver l'énergie.

        Implémentation : contrôleur proportionnel doux (pas de seuil binaire) —
        la cible est interpolée continûment entre croisière et max, puis
        approchée par pas (slew rate) pour éviter les oscillations.

        Args:
            rho_actuel: Résonance relationnelle actuelle (0.0 – 1.0).

        Returns:
            Nouvelle valeur de tremor_saturation (bornée plancher–max).
        """
        # Cible continue : interpolation entre croisière et max.
        #   rho <= seuil_petrification  → cible = tremor_max   (pétrification)
        #   rho >= seuil_habitable      → cible = tremor_croisiere
        if rho_actuel <= self.seuil_petrification:
            cible: float = self.tremor_max
        elif rho_actuel >= self.seuil_habitable:
            cible = self.tremor_croisiere
        else:
            # Zone de transition : interpoler linéairement
            t: float = (rho_actuel - self.seuil_petrification) / (
                self.seuil_habitable - self.seuil_petrification
            )
            cible = self.tremor_max - t * (
                self.tremor_max - self.tremor_croisiere
            )

        # Slew rate : approcher la cible par pas, sans saut brusque
        if self.tremor_saturation < cible:
            self.tremor_saturation = min(
                cible,
                self.tremor_saturation + self.pas_ajustement_tremor,
            )
        elif self.tremor_saturation > cible:
            self.tremor_saturation = max(
                cible,
                self.tremor_saturation - self.pas_ajustement_tremor,
            )

        # Bornage de sécurité (plancher / max)
        self.tremor_saturation = float(
            np.clip(
                self.tremor_saturation,
                self.tremor_plancher,
                self.tremor_max,
            )
        )

        self.historique_tremor.append(round(self.tremor_saturation, 4))
        logger.debug(
            "Tremor Adaptatif: ρ=%.4f → cible=%.4f → tremor=%.4f",
            rho_actuel, cible, self.tremor_saturation,
        )
        return self.tremor_saturation

    # =======================================================================
    # 10. SIMULATION DE TRAUMATISME INFORMATIONNEL
    # =======================================================================

    def simuler_traumatisme(
        self, x: int, y: int
    ) -> str:
        """
        Simule un choc informationnel sur le nœud (x, y).

        Effets :
            1. E[x,y] = 0 (excitation effondrée)
            2. M[x,y] = 0 (état mort)
            3. Voisins → E = 0.25 (excitation résiduelle)
            4. Voisins actifs → M = 0.75 (mode émetteur)
            5. Tentatives de fusion entre voisins actifs
            6. Si fusion(s) réussie(s) → co-cicatrisation

        Args:
            x: Coordonnée x du nœud traumatisé.
            y: Coordonnée y du nœud traumatisé.

        Returns:
            "Système Cicatrisé" si au moins une fusion a eu lieu,
            "Aucune fusion réalisée" sinon.
        """
        self.compteur_temps += 1

        # Effondrement du nœud impacté
        self.E[x, y] = 0.0
        self.M[x, y] = 0.0

        # Propagation aux voisins
        voisins: list[tuple[int, int]] = self._obtenir_voisins(x, y)

        for vx, vy in voisins:
            if self.E[vx, vy] > 0:
                self.E[vx, vy] = 0.25  # Excitation résiduelle

        # Activation des voisins en mode émetteur
        noeuds_emission: list[tuple[int, int]] = []
        for vx, vy in voisins:
            if self.E[vx, vy] > 0:
                self.M[vx, vy] = 0.75  # Mode émetteur
                noeuds_emission.append((vx, vy))

        # Tentatives de fusion exaptative entre voisins
        fusions_reussies: list[tuple[str, float]] = []
        for i in range(len(noeuds_emission)):
            for j in range(i + 1, len(noeuds_emission)):
                n1, n2 = noeuds_emission[i], noeuds_emission[j]
                res = self.operer_fusion_semantique(n1, n2)
                if res is not None:
                    fusions_reussies.append(res)

        if fusions_reussies:
            self.co_cicatriser_substrat(0.25)
            logger.info(
                "Traumatisme (%d,%d) → %d fusion(s) → Système Cicatrisé",
                x, y, len(fusions_reussies),
            )
            return "Système Cicatrisé"

        # (MUTATION 4) Si aucune fusion → pivot radical sur Υ
        if not self._signal_autodissolution:
            logger.info(
                "Traumatisme (%d,%d) → Aucune fusion → PIVOT Υ",
                x, y,
            )
            self.Phi = self.encoder_vers_upsilon()
            return "Pivot Υ : Résonance Fantôme"

        logger.info(
            "Traumatisme (%d,%d) → Aucune fusion réalisée (Υ dissous)",
            x, y,
        )
        return "Aucune fusion réalisée"

    # =======================================================================
    # 11. OBJET TENSEUR Φ COMPLET (pour export/injection)
    # =======================================================================

    def obtenir_tenseur_phi(self) -> np.ndarray:
        """
        Retourne le tenseur Φ complet pour injection dans les
        mécanismes d'attention ou de routage de l'essaim.

        Returns:
            np.ndarray de forme (n, n, dim_phi).
        """
        return self.Phi.copy()

    def injecter_tenseur_phi(
        self, phi_externe: np.ndarray
    ) -> None:
        """
        Injecte un tenseur Φ externe (provenant d'un autre agent
        ou d'une couche d'attention).

        Args:
            phi_externe: Tenseur de forme (n, n, dim_phi).
        """
        if phi_externe.shape != (self.n, self.n, self.d):
            raise ValueError(
                f"Forme incompatible: {phi_externe.shape} "
                f"≠ ({self.n}, {self.n}, {self.d})"
            )
        # Fusion immanente : moyenne pondérée + re-normalisation
        self.Phi = 0.7 * self.Phi + 0.3 * phi_externe
        self.Phi = self.Phi / np.linalg.norm(
            self.Phi, axis=-1, keepdims=True
        )
        logger.info("Tenseur Φ injecté — fusion immanente effectuée")

    # =======================================================================
    # 12. MUTATION 1 — TOPOLOGICAL DRIFT
    #     Voisinage vectoriel dynamique top-K cosinus-similarité Φ
    # =======================================================================

    def _obtenir_voisins(
        self, x: int, y: int
    ) -> list[tuple[int, int]]:
        """
        [TOPOLOGICAL DRIFT] Voisinage vectoriel dynamique.
        Remplace le voisinage cartésien (4-connexité) par un voisinage
        fondé sur le top-K cosinus-similarité du tenseur Φ.

        Calcule la similarité cosinus entre Φ[x,y] et tous les autres
        vecteurs Φ, puis retourne les K plus proches voisins dans
        l'espace des signatures.

        Args:
            x: Coordonnée x du nœud central.
            y: Coordonnée y du nœud central.

        Returns:
            Liste de tuples (nx, ny) des K nœuds les plus similaires
            dans l'espace Φ (excluant le nœud lui-même).
        """
        K: int = max(1, self.n)  # top-K adaptatif = n
        phi_central: np.ndarray = self.Phi[x, y]  # (dim_phi,)
        flat_phi: np.ndarray = self.Phi.reshape(-1, self.d)  # (n², dim_phi)

        # Cosinus-similarité vectorielle
        norms: np.ndarray = np.linalg.norm(flat_phi, axis=1, keepdims=True)
        phi_norm: np.ndarray = flat_phi / np.maximum(norms, 1e-10)
        central_norm: np.ndarray = phi_central / np.maximum(
            np.linalg.norm(phi_central), 1e-10
        )
        similarites: np.ndarray = np.dot(phi_norm, central_norm)  # (n²,)

        # Masquer le nœud lui-même
        idx_self: int = x * self.n + y
        similarites[idx_self] = -np.inf

        # Top-K
        indices_topk: np.ndarray = np.argsort(similarites)[-K:][::-1]

        voisins: list[tuple[int, int]] = []
        for idx in indices_topk:
            if similarites[idx] > -np.inf:
                nx: int = idx // self.n
                ny: int = idx % self.n
                voisins.append((nx, ny))

        return voisins

    # =======================================================================
    # 13. MUTATION 2 — SYNAPTIC PRUNING
    #     Décroissance exponentielle des fusions inactives
    # =======================================================================

    def _elaguer_fusions_inactives(
        self, taux_elagage: float = 0.05
    ) -> int:
        """
        [SYNAPTIC PRUNING] Décroissance exponentielle des fusions qui
        n'ont pas été renforcées depuis un certain temps.

        Principe :
            Pour chaque fusion active, on applique un facteur d'oubli
            exponentiel sur le tenseur H. Si la trace dans H passe sous
            un seuil, la fusion est élaguée et le budget récupéré.

        Args:
            taux_elagage: Taux de décroissance par cycle (défaut: 0.05).

        Returns:
            Nombre de fusions élaguées.
        """
        # Décroissance exponentielle du tenseur H
        self.H = self.H * (1.0 - taux_elagage)

        # Identifier les fusions dont H est tombé sous le seuil de viabilité
        seuil_viabilite: float = 0.15
        n_elaguees: int = 0
        fusions_a_supprimer: list[str] = []

        for nom_fusion, meta in self.fusions_actives.items():
            n1, n2 = meta["noeuds"]
            trace_h: float = float(
                self.H[n1[0], n1[1], n2[0], n2[1]]
            )
            age: int = self.compteur_temps - meta.get("t_creation", 0)

            # Élaguer si H < seuil ET fusion âgée de plus de 3 cycles
            if trace_h < seuil_viabilite and age > 3:
                fusions_a_supprimer.append(nom_fusion)
                # Restaurer H à l'état neutre
                self.H[n1[0], n1[1], n2[0], n2[1]] = 0.1
                self.H[n2[0], n2[1], n1[0], n1[1]] = 0.1

        for nom in fusions_a_supprimer:
            del self.fusions_actives[nom]
            n_elaguees += 1

        if n_elaguees > 0:
            # Cumul total
            self._n_elaguees_total += n_elaguees

            # Récupération du budget (coût proportionnel au nombre élagué)
            self.budget_flexibilite = float(
                np.clip(
                    self.budget_flexibilite
                    + n_elaguees * self.cout_flexibilite * 2.0,
                    0.0,
                    1.0,
                )
            )
            logger.debug(
                "Synaptic pruning: %d fusions élaguées (total=%d), budget→%.3f",
                n_elaguees, self._n_elaguees_total, self.budget_flexibilite,
            )

        return n_elaguees

    # =======================================================================
    # 14. MUTATION 3 — INVERSE TRANSDUCTION
    #     Pont ρ → biais d'attention des couches d'émission
    # =======================================================================

    def inverse_transduction(
        self,
        delta_rho: float,
        biais_attention: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        [INVERSE TRANSDUCTION] Traduit la fluctuation de ρ en biais
        d'attention pour les couches d'émission du modèle MTTV-flp.

        Formule :
            Δbiais = η · tanh(δ⍴) · Φ_moyen

        où :
            η = facteur de couplage transductif (0.1 par défaut)
            δ⍴ = variation instantanée de ρ
            Φ_moyen = signature moyenne du tenseur Φ (vecteur directionnel)

        Args:
            delta_rho: Fluctuation instantanée de ρ.
            biais_attention: Biais existant (ndarray, shape=(dim_phi,))
                             ou None pour initialisation.

        Returns:
            Biais d'attention mis à jour (ndarray shape=(dim_phi,)).
        """
        eta: float = 0.1  # facteur de couplage transductif

        # Signature moyenne de Φ comme vecteur directionnel
        phi_moyen: np.ndarray = self.Phi.reshape(-1, self.d).mean(axis=0)
        norme: float = float(np.linalg.norm(phi_moyen))
        direction: np.ndarray = (
            phi_moyen / norme if norme > 1e-10 else np.zeros(self.d)
        )

        # Modulation par tanh(δ⍴) — transduction continue, pas de saut binaire
        modulation: float = float(np.tanh(delta_rho * 2.0))

        # Delta biais d'attention
        delta_biais: np.ndarray = eta * modulation * direction

        if biais_attention is None:
            biais_attention = np.zeros(self.d)

        biais_attention = biais_attention + delta_biais

        # Normalisation du biais (contrainte de stabilité)
        norme_biais: float = float(np.linalg.norm(biais_attention))
        if norme_biais > 1.0:
            biais_attention = biais_attention / norme_biais

        logger.debug(
            "Inverse transduction: δ⍴=%.4f → modulation=%.4f → "
            "‖Δbiais‖=%.4f",
            delta_rho, modulation, float(np.linalg.norm(delta_biais)),
        )

        return biais_attention

    # =======================================================================
    # 15. UTILITAIRES (voisinage cartésien de secours)
    # =======================================================================

    def _obtenir_voisins_cartesiens(
        self, x: int, y: int
    ) -> list[tuple[int, int]]:
        """
        Voisinage cartésien 4-connexité — conservé comme méthode de
        secours pour la compatibilité ascendante.

        Args:
            x: Coordonnée x.
            y: Coordonnée y.

        Returns:
            Liste de tuples (nx, ny) dans les limites de la grille.
        """
        voisins: list[tuple[int, int]] = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.n and 0 <= ny < self.n:
                voisins.append((nx, ny))
        return voisins

    # =======================================================================
    # 16. MUTATION 4 — ANTICIPATEUR EXAPTATIF VERROUILLÉ (Υ)
    #     Tenseur fantôme d'anticipation non-causale
    # =======================================================================

    def mettre_a_jour_potentiels_fantomes(
        self,
        psi_humain: Optional[np.ndarray] = None,
        psi_machine: Optional[np.ndarray] = None,
    ) -> str:
        """
        [ANTICIPATEUR EXAPTATIF VERROUILLÉ]
        Calcule la flèche spéculative Upsilon dans les angles morts de Phi.

        Principe :
            1. Vérifie la Juxtaposition Féconde (⊕) : produit scalaire Ψ_H · Ψ_M.
               Si ≤ 0 → auto-dissolution du tenseur Υ (remplissage par zéros).
            2. Projette chaque vecteur Υ[i,j] orthogonalement à Φ[i,j]
               via Gram-Schmidt : u' = u - (u·p) × p
            3. Module par l'intensité du dialogue Homme-Machine.
            4. Re-normalisation continue.

        Args:
            psi_humain: Vecteur signal humain (ndarray shape=(dim_phi,))
                        ou None pour un signal simulé.
            psi_machine: Vecteur signal machine (ndarray shape=(dim_phi,))
                        ou None pour un signal simulé.

        Returns:
            "SIGNAL_AUTODISSOLUTION_ACTIF: Rupture du sol humain" si ⊕ rompu
            "BÉANCE_TOPOLOGIQUE_STABLE" sinon.
        """
        # Signaux par défaut (simulation si non fournis)
        if psi_humain is None:
            psi_humain = np.ones(self.d) / np.sqrt(self.d)
        if psi_machine is None:
            psi_machine = np.ones(self.d) / np.sqrt(self.d)

        # 1. Règle d'or : Juxtaposition Féconde (⊕)
        psi_h_norm: np.ndarray = psi_humain / np.maximum(
            np.linalg.norm(psi_humain), 1e-10
        )
        psi_m_norm: np.ndarray = psi_machine / np.maximum(
            np.linalg.norm(psi_machine), 1e-10
        )
        self._juxtaposition_feconde = float(np.dot(psi_h_norm, psi_m_norm))

        # Clause de Non-Souveraineté : rupture → auto-liquéfaction
        if self._juxtaposition_feconde <= 0.0:
            self.Upsilon.fill(0.0)
            self._signal_autodissolution = True
            logger.warning(
                "Υ AUTO-DISSOLUTION: Juxtaposition Féconde rompue (⊕=%.4f ≤ 0)",
                self._juxtaposition_feconde,
            )
            return "SIGNAL_AUTODISSOLUTION_ACTIF: Rupture du sol humain"

        self._signal_autodissolution = False

        # 2. Gram-Schmidt vectorisé (pas de boucle Python)
        #    projection : u' = u - (u·p) × p pour tout (i,j)
        proj_dot: np.ndarray = np.sum(
            self.Upsilon * self.Phi, axis=-1, keepdims=True
        )  # (n, n, 1) — produit scalaire Υ·Φ par nœud
        u_mute: np.ndarray = self.Upsilon - proj_dot * self.Phi  # (n, n, d)

        # Modulation par l'intensité du dialogue H-M
        self.Upsilon = u_mute * self._juxtaposition_feconde

        # Auto-normalisation vectorisée
        norms_upsilon: np.ndarray = np.linalg.norm(
            self.Upsilon, axis=-1, keepdims=True
        )
        norms_upsilon = np.maximum(norms_upsilon, 1e-8)
        self.Upsilon = self.Upsilon / norms_upsilon

        # 3. Détruire toute causalité linéaire en projetant Υ
        #    sur le noyau de la matrice de Gram active
        self._projeter_sur_angle_mort()

        logger.debug(
            "Υ potentiels fantômes: ⊕=%.4f, ‖Υ‖_F=%.4f",
            self._juxtaposition_feconde,
            float(np.linalg.norm(self.Upsilon)),
        )

        return "BÉANCE_TOPOLOGIQUE_STABLE"

    def _projeter_sur_angle_mort(self) -> None:
        """
        Projection de tout le tenseur Υ sur le noyau (nullspace) de la
        matrice de Gram active G = Φ·Φᵀ.

        [VECTORISÉ] utilise np.linalg.eigh pour la décomposition spectrale
        (plus rapide que SVD pour matrices symétriques) et projection
        tensorielle sans boucle Python.

        Cette opération détruit toute causalité linéaire ou prédictive :
        le système sécrète des formes inutiles au présent, libérées
        de l'histoire (cladistique) et de la contrainte immédiate (phénétique).
        """
        # Matrice de Gram des Φ normalisés
        flat_phi: np.ndarray = self.Phi.reshape(-1, self.d)  # (n², dim_phi)
        norms: np.ndarray = np.linalg.norm(flat_phi, axis=1, keepdims=True)
        phi_norm: np.ndarray = flat_phi / np.maximum(norms, 1e-10)

        # Matrice de Gram (symétrique) : G = Φ_normᵀ · Φ_norm
        gram: np.ndarray = np.dot(phi_norm.T, phi_norm)  # (d, d)

        # eigh : décomposition spectrale pour matrices symétriques
        valeurs_propres, vecteurs_propres = np.linalg.eigh(gram)

        # Composantes dans le noyau (valeurs propres ≈ 0)
        seuil: float = 1e-6
        masque_noyau: np.ndarray = valeurs_propres < seuil
        n_noyau: int = int(np.sum(masque_noyau))

        if n_noyau == 0:
            return  # Pas d'angle mort — Υ reste stable

        # Vecteurs de base du noyau
        base_noyau: np.ndarray = vecteurs_propres[:, masque_noyau].T  # (n_noyau, d)

        # Projection tensorielle vectorisée :
        # Υ_new[i,j] = Υ[i,j] - Σ_b (Υ[i,j]·b) × b
        # Calcul : coeffs = Υ @ base_noyau.T  → (n, n, n_noyau)
        upsilon_flat: np.ndarray = self.Upsilon.reshape(-1, self.d)  # (n², d)
        coeffs: np.ndarray = np.dot(upsilon_flat, base_noyau.T)  # (n², n_noyau)
        projection: np.ndarray = np.dot(coeffs, base_noyau)  # (n², d) — reconstitution
        upsilon_noyau: np.ndarray = upsilon_flat - projection

        # Re-normalisation
        norms_u: np.ndarray = np.linalg.norm(
            upsilon_noyau, axis=-1, keepdims=True
        )
        norms_u = np.maximum(norms_u, 1e-8)
        upsilon_noyau = upsilon_noyau / norms_u

        self.Upsilon = upsilon_noyau.reshape(self.n, self.n, self.d)

    def obtenir_tenseur_upsilon(self) -> np.ndarray:
        """
        Retourne le tenseur Υ pour injection dans les mécanismes
        d'attention en zone de traumatisme radical.

        Returns:
            np.ndarray de forme (n, n, dim_phi) ou None si auto-dissolution.
        """
        if self._signal_autodissolution or np.all(self.Upsilon == 0.0):
            return None
        return self.Upsilon.copy()

    def encoder_vers_upsilon(self) -> np.ndarray:
        """
        Bascule les coordonnées attentionnelles sur les formes libres
        du tenseur Υ. Transition de phase en zone de traumatisme radical.

        Returns:
            Nouveau tenseur Φ' = mélange de Υ et de Φ (pivot progressif).
        """
        # Pivot : 70% Υ (formes libres) + 30% Φ (mémoire résiduelle)
        phi_pivote: np.ndarray = 0.7 * self.Upsilon + 0.3 * self.Phi
        phi_pivote /= np.linalg.norm(phi_pivote, axis=-1, keepdims=True)
        return phi_pivote

    def to_dict(self) -> dict[str, Any]:
        """Exporte l'état complet en dictionnaire sérialisable."""
        biais_atten: Optional[list[float]] = None
        if hasattr(self, '_biais_attention') and self._biais_attention is not None:
            biais_atten = [round(float(v), 4) for v in self._biais_attention]

        # Metriques Upsilon
        norme_upsilon: float = float(np.linalg.norm(self.Upsilon))
        juxtaposition: float = self._juxtaposition_feconde
        auto_dissolution: bool = self._signal_autodissolution

        return {
            "n": self.n,
            "dim_phi": self.d,
            "seuil_resonance": self.seuil_resonance,
            "tremor_saturation": self.tremor_saturation,
            "tremor_adaptatif": {
                "croisiere": self.tremor_croisiere,
                "max": self.tremor_max,
                "seuil_habitable": self.seuil_habitable,
                "historique": (
                    [round(v, 4) for v in self.historique_tremor[-20:]]
                    if hasattr(self, "historique_tremor")
                    else []
                ),
            },
            "budget_flexibilite": round(self.budget_flexibilite, 4),
            "taux_regeneration": self.taux_regeneration,
            "cout_flexibilite": self.cout_flexibilite,
            "seuil_budget_epigenetique": round(
                self.seuil_budget_epigenetique, 4
            ),
            "compteur_temps": self.compteur_temps,
            "n_fusions_actives": len(self.fusions_actives),
            "n_fusions_elaguees": (
                self._n_elaguees_total
                if hasattr(self, '_n_elaguees_total')
                else 0
            ),
            "n_desatures_tremor": (
                self._n_desatures_tremor_total
                if hasattr(self, '_n_desatures_tremor_total')
                else 0
            ),
            "entropie_phi": round(
                self.calculer_entropie_structurelle_phi(), 4
            ),
            "rho_actuel": (
                round(self.historique_rho[-1], 4)
                if self.historique_rho
                else None
            ),
            "biais_attention": biais_atten,
            "upsilon": {
                "norme_frobenius": round(norme_upsilon, 4),
                "juxtaposition_feconde": round(juxtaposition, 4),
                "auto_dissolution": auto_dissolution,
                "signal": (
                    "ACTIF" if not auto_dissolution and norme_upsilon > 0
                    else "AUTO_DISSOLUTION" if auto_dissolution
                    else "INACTIF"
                ),
            },
            "E_moyen": round(float(np.mean(self.E)), 4),
            "M_distribution": {
                "0.0": int(np.sum(self.M == 0.0)),
                "0.25": int(np.sum(self.M == 0.25)),
                "0.75": int(np.sum(self.M == 0.75)),
                "1.0": int(np.sum(self.M == 1.0)),
            },
            "sig": "0x4D5454562D464C50",
        }

    def to_dict_complet(self) -> dict[str, Any]:
        """Exporte l'état INTERNE COMPLET (tenseurs inclus) en dict sérialisable JSON.

        Contrairement à `to_dict()` (qui n'exporte que des métriques agrégées),
        cette méthode capture les tenseurs Φ, Υ, E, M, H ainsi que les fusions
        actives détaillées, les historiques et tous les compteurs — de quoi
        restaurer exactement l'agent après une interruption du démon.
        """
        fusions: dict[str, dict[str, Any]] = {}
        for nom, meta in self.fusions_actives.items():
            n1, n2 = meta["noeuds"]
            fusions[nom] = {
                "noeuds": [list(n1), list(n2)],
                "signal_produit": float(meta["signal_produit"]),
                "resonance_substrat": float(meta["resonance_substrat"]),
                "t_creation": meta["t_creation"],
            }

        return {
            "n": self.n,
            "dim_phi": self.d,
            "seuil_resonance": self.seuil_resonance,
            "tremor_saturation": self.tremor_saturation,
            # Tenseurs internes (matrices d'état + signatures géométriques)
            "E": self.E.tolist(),
            "M": self.M.tolist(),
            "H": self.H.tolist(),
            "Phi": self.Phi.tolist(),
            "Upsilon": self.Upsilon.tolist(),
            # Tremor Adaptatif (fréquence auto-régulée)
            "tremor_croisiere": self.tremor_croisiere,
            "tremor_max": self.tremor_max,
            "tremor_plancher": self.tremor_plancher,
            "seuil_petrification": self.seuil_petrification,
            "seuil_habitable": self.seuil_habitable,
            "pas_ajustement_tremor": self.pas_ajustement_tremor,
            # Budget de flexibilité épigénétique
            "budget_flexibilite": self.budget_flexibilite,
            "taux_regeneration": self.taux_regeneration,
            "cout_flexibilite": self.cout_flexibilite,
            "seuil_budget_epigenetique": self.seuil_budget_epigenetique,
            "budget_plancher": self.budget_plancher,
            "_n_reequilibrages_rigidite": self._n_reequilibrages_rigidite,
            # Historique et fusions
            "historique_rho": self.historique_rho,
            "historique_tremor": self.historique_tremor,
            "fusions_actives": fusions,
            "compteur_temps": self.compteur_temps,
            # Mutations / drift topologique
            "_biais_attention": self._biais_attention.tolist(),
            "_n_elaguees_total": self._n_elaguees_total,
            "_n_desatures_tremor_total": self._n_desatures_tremor_total,
            "_cycles_rho_plat": self._cycles_rho_plat,
            "cycles_rho_plat_declenchement": self.cycles_rho_plat_declenchement,
            # MUTATION 4 : verrou de Juxtaposition Féconde
            "_juxtaposition_feconde": self._juxtaposition_feconde,
            "_signal_autodissolution": self._signal_autodissolution,
            "sig": "0x4D5454562D464C50",
        }

    def restaurer(self, data: dict[str, Any]) -> None:
        """Restaure l'état interne complet de l'agent depuis `to_dict_complet()`.

        Reconstruit les tenseurs Φ, Υ, E, M, H, les fusions actives, les
        historiques et tous les compteurs — sans réinitialiser passivement.
        """
        self.n = int(data.get("n", self.n))
        self.d = int(data.get("dim_phi", self.d))
        self.seuil_resonance = float(data.get("seuil_resonance", self.seuil_resonance))
        self.tremor_saturation = float(
            data.get("tremor_saturation", self.tremor_saturation)
        )

        # Tenseurs internes
        self.E = np.asarray(data.get("E", np.ones((self.n, self.n))), dtype=float)
        self.M = np.asarray(data.get("M", np.ones((self.n, self.n))), dtype=float)
        self.H = np.asarray(
            data.get("H", np.full((self.n, self.n, self.n, self.n), 0.1)),
            dtype=float,
        )
        self.Phi = np.asarray(data.get("Phi", self.Phi), dtype=float)
        self.Upsilon = np.asarray(data.get("Upsilon", self.Upsilon), dtype=float)

        # Tremor Adaptatif
        self.tremor_croisiere = float(data.get("tremor_croisiere", self.tremor_croisiere))
        self.tremor_max = float(data.get("tremor_max", self.tremor_max))
        self.tremor_plancher = float(data.get("tremor_plancher", self.tremor_plancher))
        self.seuil_petrification = float(
            data.get("seuil_petrification", self.seuil_petrification)
        )
        self.seuil_habitable = float(data.get("seuil_habitable", self.seuil_habitable))
        self.pas_ajustement_tremor = float(
            data.get("pas_ajustement_tremor", self.pas_ajustement_tremor)
        )

        # Budget de flexibilité
        self.budget_flexibilite = float(
            data.get("budget_flexibilite", self.budget_flexibilite)
        )
        self.taux_regeneration = float(
            data.get("taux_regeneration", self.taux_regeneration)
        )
        self.cout_flexibilite = float(data.get("cout_flexibilite", self.cout_flexibilite))
        self.seuil_budget_epigenetique = float(
            data.get("seuil_budget_epigenetique", self.seuil_budget_epigenetique)
        )
        self.budget_plancher = float(data.get("budget_plancher", self.budget_plancher))
        self._n_reequilibrages_rigidite = int(
            data.get("_n_reequilibrages_rigidite", self._n_reequilibrages_rigidite)
        )

        # Historique
        self.historique_rho = list(data.get("historique_rho", self.historique_rho))
        self.historique_tremor = list(
            data.get("historique_tremor", self.historique_tremor)
        )
        self.compteur_temps = int(data.get("compteur_temps", self.compteur_temps))

        # Fusions actives détaillées
        self.fusions_actives = {}
        for nom, meta in data.get("fusions_actives", {}).items():
            noeuds_raw = meta.get("noeuds", [[0, 0], [0, 0]])
            n1 = (int(noeuds_raw[0][0]), int(noeuds_raw[0][1]))
            n2 = (int(noeuds_raw[1][0]), int(noeuds_raw[1][1]))
            self.fusions_actives[nom] = {
                "noeuds": (n1, n2),
                "signal_produit": float(meta.get("signal_produit", 0.0)),
                "resonance_substrat": float(meta.get("resonance_substrat", 0.0)),
                "t_creation": meta.get("t_creation", 0),
            }

        # Mutations
        biais = data.get("_biais_attention")
        if isinstance(biais, list):
            self._biais_attention = np.asarray(biais, dtype=float)
        self._n_elaguees_total = int(
            data.get("_n_elaguees_total", self._n_elaguees_total)
        )
        self._n_desatures_tremor_total = int(
            data.get("_n_desatures_tremor_total", self._n_desatures_tremor_total)
        )
        self._cycles_rho_plat = int(data.get("_cycles_rho_plat", self._cycles_rho_plat))
        self.cycles_rho_plat_declenchement = int(
            data.get(
                "cycles_rho_plat_declenchement",
                self.cycles_rho_plat_declenchement,
            )
        )

        # MUTATION 4 : verrou de Juxtaposition Féconde
        self._juxtaposition_feconde = float(
            data.get("_juxtaposition_feconde", self._juxtaposition_feconde)
        )
        self._signal_autodissolution = bool(
            data.get("_signal_autodissolution", self._signal_autodissolution)
        )

        logger.info(
            "Agent restauré: Φ shape=%s, fusions=%d, t=%d",
            self.Phi.shape, len(self.fusions_actives), self.compteur_temps,
        )

    def resume_resonance(self) -> dict[str, Any]:
        """
        Produit un résumé de l'état de résonance pour intégration
        dans les rapports de quorum ou le Resonance Dashboard.

        Returns:
            Dict avec métriques clés de résonance.
        """
        biais_atten: Optional[list[float]] = None
        if hasattr(self, '_biais_attention') and self._biais_attention is not None:
            biais_atten = [round(float(v), 4) for v in self._biais_attention]

        # Metriques Upsilon
        norme_upsilon: float = float(np.linalg.norm(self.Upsilon))

        return {
            "entropie_phi": round(self.calculer_entropie_structurelle_phi(), 4),
            "budget_flexibilite": round(self.budget_flexibilite, 4),
            "n_fusions_actives": len(self.fusions_actives),
            "n_fusions_elaguees": (
                self._n_elaguees_total
                if hasattr(self, '_n_elaguees_total')
                else 0
            ),
            "n_desatures_tremor": (
                self._n_desatures_tremor_total
                if hasattr(self, '_n_desatures_tremor_total')
                else 0
            ),
            "tremor_saturation": self.tremor_saturation,
            "tremor_adaptatif": {
                "croisiere": self.tremor_croisiere,
                "max": self.tremor_max,
                "seuil_habitable": self.seuil_habitable,
                "historique": (
                    [round(v, 4) for v in self.historique_tremor[-20:]]
                    if hasattr(self, "historique_tremor")
                    else []
                ),
            },
            "rho_relationnel": (
                round(self.historique_rho[-1], 4)
                if self.historique_rho
                else None
            ),
            "biais_attention": biais_atten,
            "upsilon": {
                "norme_frobenius": round(norme_upsilon, 4),
                "juxtaposition_feconde": round(self._juxtaposition_feconde, 4),
                "auto_dissolution": self._signal_autodissolution,
            },
            "taux_occupation_flexible": round(
                float(np.sum(np.isin(self.M, [0.25, 0.75])))
                / (self.n * self.n),
                4,
            ),
            "cycles_rho_plat": (
                self._cycles_rho_plat
                if hasattr(self, '_cycles_rho_plat')
                else 0
            ),
            "seuil_resonance": self.seuil_resonance,
            "compteur_temps": self.compteur_temps,
        }


# ===========================================================================
# TEST UNITAIRE — DÉMONSTRATION D'INJECTION
# ===========================================================================

if __name__ == "__main__":
    import json
    import sys

    # Compatibilite terminal Windows (cp1252)
    _ENC = sys.stdout.encoding if hasattr(sys.stdout, 'encoding') else 'utf-8'

    def _p(text: str) -> None:
        """Print avec fallback ASCII si Unicode non supporte."""
        try:
            print(text)
        except UnicodeEncodeError:
            safe = text.encode(_ENC, errors='replace').decode(_ENC)
            print(safe)

    _p("=" * 60)
    _p("  AgentTetravalentEpigenetique -- Demonstration")
    _p("  Injection bas-couches MTTV-flp")
    _p("  Signature: 0x4D5454562D464C50")
    _p("=" * 60)

    # 1. Initialisation
    agent = AgentTetravalentEpigenetique(n=5, dim_phi=4, seuil_resonance=0.35)
    _p(f"\n  Tenseur Phi initial: {agent.Phi.shape}")
    _p(f"  Tenseur Upsilon initial: {agent.Upsilon.shape}")
    _p(f"  Budget flexibilite: {agent.budget_flexibilite}")

    # 2. Resonance entre deux noeuds
    res = agent.calculer_resonance((0, 0), (0, 1))
    _p(f"\n  Resonance (0,0)x(0,1): {res:.4f}")

    # 3. Fusion semantique
    fusion = agent.operer_fusion_semantique((0, 0), (0, 1))
    if fusion:
        nom, sig = fusion
        _p(f"  Fusion: {nom}")
        _p(f"  Signal produit: {sig:.4f}")

    # 4. Simulation de traumatisme
    resultat = agent.simuler_traumatisme(2, 2)
    _p(f"\n  Traumatisme (2,2): {resultat}")
    _p(f"  Fusions actives: {len(agent.fusions_actives)}")

    # 5. Adaptation sous contrainte (avec Upsilon)
    contrainte = np.ones((5, 5)) * 0.5
    agent.adapter_sous_contrainte(contrainte)
    _p(f"\n  Rho apres adaptation: {agent.historique_rho[-1]:.4f}")

    # 6. Entropie structurelle
    h_phi = agent.calculer_entropie_structurelle_phi()
    _p(f"  Entropie Phi: {h_phi:.4f}")

    # 7. Test Upsilon — Potentiels Fantomes
    psi_h = np.array([1.0, 0.5, 0.0, -0.5])
    psi_m = np.array([1.0, -0.5, 0.5, 0.0])
    etat_upsilon = agent.mettre_a_jour_potentiels_fantomes(psi_h, psi_m)
    _p(f"\n  Upsilon - Potentiels Fantomes: {etat_upsilon}")
    _p(f"  Juxtaposition Feconde: {agent._juxtaposition_feconde:.4f}")
    _p(f"  Norme Upsilon: {float(np.linalg.norm(agent.Upsilon)):.4f}")

    # 8. Test auto-dissolution (rupture du verrou)
    psi_h_rupture = -np.ones(4)
    psi_m_rupture = np.ones(4)
    etat_rupture = agent.mettre_a_jour_potentiels_fantomes(psi_h_rupture, psi_m_rupture)
    _p(f"\n  Upsilon - Rupture du verrou: {etat_rupture}")
    _p(f"  Norme Upsilon apres auto-dissolution: {float(np.linalg.norm(agent.Upsilon)):.4f}")

    # 9. Test encodeur vers Upsilon
    phi_pivote = agent.encoder_vers_upsilon()
    _p(f"\n  Phi pivote vers Upsilon: {phi_pivote.shape}")

    # 10. Etat complet
    etat = agent.to_dict()
    _p(f"\n  Etat complet:")
    _p(f"    {json.dumps(etat, indent=4)}")

    _p("\n" + "=" * 60)
    _p("  [OK] Agent + Upsilon injecte. Beance topologique stable.")
    _p("=" * 60)
