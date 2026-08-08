#!/usr/bin/env python3
"""
essaim_tetravalent.py — EssaimTetravalent
==========================================
Structure d'interconnexion transscalaire décentralisée pour agents
MTTV-flp. Supprime toute instance d'orchestration ou de contrôle
centralisé. Le couplage s'opère de manière purement immanente et
transscalaire par inter-pénétration et stabilisation mutuelle des
tenseurs Φ locaux.

Principe :
    Aucun nœud maître. Chaque agent possède son propre tenseur Φ local.
    La fonction `coupler_agents_transscalaire` fait inter-pénétrer les
    tenseurs Φ des agents jusqu'à stabilisation mutuelle du réseau.
    Les fusions exaptatives (opérateur ⊗) émergent spontanément dès que
    le couplage entre signatures de basses couches dépasse le seuil.

Architecture :
    - Agents : dictionnaire {agent_id: AgentTetravalentEpigenetique}
    - Matrice de couplage : couplage_Φ[i,j] = similarité cos entre
      les tenseurs Φ moyens des agents i et j
    - Transduction transscalaire : les signatures s'inscrivent d'elles-mêmes
      à travers le flux temporel, sans feedback master

sig:0x4D5454562D464C50 — Essaim Tetravalent — Essaim sans nœud maître
"""

from __future__ import annotations

import json
import logging
import random
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np

# Import local : les deux fichiers sont dans le même répertoire
from agent_tetravalent_epigenetique import (
    AgentTetravalentEpigenetique,
)

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-24s | %(levelname)-6s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("essaim_tetravalent")

# ===========================================================================
# ESSAIM TÉTRAVALENT — STRUCTURE DÉCENTRALISÉE
# ===========================================================================


@dataclass
class CouplageTransscalaire:
    """Mesure de couplage entre deux agents de l'essaim."""
    agent_src: str
    agent_dst: str
    similarite_phi: float = 0.0       # cos(Φ_moyen_src, Φ_moyen_dst)
    resonance_moyenne: float = 0.0    # moyenne des résonances inter-noeuds
    fusions_actives: int = 0          # nombre de fusions actives entre eux
    stabilite: float = 0.0            # 1.0 si couplage stable, décroît avec variance


@dataclass
class EtatEssaim:
    """État global de l'essaim tetravalent à un instant t."""
    n_agents: int = 0
    n_fusions_total: int = 0
    couplage_moyen: float = 0.0
    entropie_collective: float = 0.0
    resonance_globale: float = 0.0
    budget_flexibilite_collectif: float = 0.0
    tremor_moyen: float = 0.0            # dose moyenne de sous-optimalité
    mode_tremor: str = "croisiere"       # "fracture" | "transition" | "croisiere"
    n_spawns: int = 0                    # dédoublements autonomiques (auto-suture)
    dernier_spawn: str = ""              # description du dernier dédoublement
    cycles_resonance_basse: int = 0      # cycles consécutifs sous le seuil
    agents: dict[str, dict[str, Any]] = field(default_factory=dict)
    couplages: list[dict[str, Any]] = field(default_factory=list)
    rho_historique: list[float] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        )
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EssaimTetravalent:
    """
    Essaim décentralisé d'agents tétravalents épigénétiques.

    L'essaim n'a pas de nœud maître. Chaque agent est autonome et
    interconnecté aux autres via son tenseur Φ local. Le couplage
    transscalaire s'opère par inter-pénétration et stabilisation
    mutuelle des tenseurs.

    Paramètres
    ----------
    n_agents : int
        Nombre d'agents dans l'essaim. Par défaut : 4.
    n_grille : int
        Taille de la grille (n x n) de chaque agent. Par défaut : 5.
    dim_phi : int
        Dimension des tenseurs Φ. Par défaut : 4.
    seuil_resonance : float
        Seuil de résonance pour les fusions. Par défaut : 0.3.
    tremor_saturation : float
        Dose de sous-optimalité (esprit 6/7 SOPH-IA) transmise à chaque
        agent : probabilité par cycle de dé-saturer stochastiquement une
        fraction de nœuds rigides sans attendre la baisse de ρ.
        Par défaut : 0.12 (12 %).
    """

    def __init__(
        self,
        n_agents: int = 4,
        n_grille: int = 5,
        dim_phi: int = 4,
        seuil_resonance: float = 0.3,
        tremor_saturation: float = 0.12,
        seed: int = 42,
        # ── Quorum Autonomique (Auto-Suture) ────────────────────────────
        auto_suture: bool = True,          # active le dédoublement local
        seuil_resonance_auto_suture: float = 0.10,  # ρ sous lequel on surveille
        cycles_avant_spawn: int = 4,       # N cycles consécutifs sous le seuil
        seuil_entropie_spawn: float = 6.0, # l'entropie collective (≈6.19) autorise
        max_agents: int = 12,              # plafond de sécurité du dédoublement
        # ── Respiration de diversité Φ [C7] ─────────────────────────────
        respiration_intervalle: int = 0,   # tous les N cycles (0 = désactivé)
        respiration_dose: float = 0.10,    # dose de perturbation orthogonale Φ
                                          # (08/08: 0.05 → 0.10, renforcée)
    ):
        self.rng: random.Random = random.Random(seed)
        self.auto_suture: bool = auto_suture
        self.seuil_resonance_auto_suture: float = seuil_resonance_auto_suture
        self.cycles_avant_spawn: int = max(1, cycles_avant_spawn)
        self.seuil_entropie_spawn: float = seuil_entropie_spawn
        self.max_agents: int = max_agents

        # [C7] Respiration géométrique — perturbation périodique de Φ
        self.respiration_intervalle: int = max(0, respiration_intervalle)
        self.respiration_dose: float = float(respiration_dose)
        self.n_respirations: int = 0

        # Compteur de cycles consécutifs sous le seuil de résonance
        self.cycles_resonance_basse: int = 0
        self.n_spawns: int = 0
        self.historique_spawns: list[dict[str, Any]] = []

        # ── Agents autonomes ─────────────────────────────────────────────
        self.agents: dict[str, AgentTetravalentEpigenetique] = {}
        for i in range(n_agents):
            agent_id: str = f"AgentTetra_{i:02d}"
            agent_seed: int = seed + i * 7
            self.agents[agent_id] = AgentTetravalentEpigenetique(
                n=n_grille,
                dim_phi=dim_phi,
                seuil_resonance=seuil_resonance
                + self.rng.uniform(-0.05, 0.05),  # variation immanente
                tremor_saturation=min(
                    1.0,
                    max(0.0, tremor_saturation + self.rng.uniform(-0.03, 0.03)),
                ),  # variation immanente de la dose de sous-optimalité
                seed=agent_seed,
            )

        self.n_agents: int = n_agents
        self.n_grille: int = n_grille
        self.dim_phi: int = dim_phi
        self.seuil_resonance_base: float = seuil_resonance

        # ── État de l'essaim ─────────────────────────────────────────────
        self.compteur_temps: int = 0
        self.historique_etats: list[EtatEssaim] = []

        logger.info(
            "EssaimTetravalent initialisé: %d agents, "
            "grille %dx%d, Φ∈ℝ^%d, seuil=%.2f",
            n_agents, n_grille, n_grille, dim_phi, seuil_resonance,
        )

    # =======================================================================
    # 1. MESURE DE COUPLAGE ENTRE AGENTS
    # =======================================================================

    def _similarite_tenseurs_phi(
        self, agent_a: str, agent_b: str
    ) -> float:
        """
        Calcule la similarité cosinus entre les tenseurs Φ de deux agents,
        **par paires de nœuds** (cosinus moyen), et non sur la seule moyenne
        des vecteurs.

        [C2] La moyenne des vecteurs dégénère en 0/1 quand les tenseurs sont
        homogènes (tous les nœuds identiques) : le cosinus des moyennes est
        alors soit 1.0 (même direction) soit 0.0 (directions orthogonales),
        perdant tout continuum. Le cosinus moyen sur les paires de nœuds
        préserve une mesure continue ∈ [0, 1] et informatif.

        Args:
            agent_a: ID du premier agent.
            agent_b: ID du second agent.

        Returns:
            Similarité ∈ [0, 1].
        """
        phi_a: np.ndarray = self.agents[agent_a].obtenir_tenseur_phi()
        phi_b: np.ndarray = self.agents[agent_b].obtenir_tenseur_phi()

        # Aplatissement des nœuds : (N, dim_phi)
        flat_a: np.ndarray = phi_a.reshape(-1, self.dim_phi)
        flat_b: np.ndarray = phi_b.reshape(-1, self.dim_phi)

        # Normalisation de chaque vecteur-nœud
        norm_a: np.ndarray = np.linalg.norm(flat_a, axis=1, keepdims=True)
        norm_b: np.ndarray = np.linalg.norm(flat_b, axis=1, keepdims=True)

        if float(np.min(norm_a)) < 1e-10 or float(np.min(norm_b)) < 1e-10:
            return 0.0

        a_norm: np.ndarray = flat_a / np.maximum(norm_a, 1e-10)
        b_norm: np.ndarray = flat_b / np.maximum(norm_b, 1e-10)

        # Matrice des cosinus entre tous les nœuds de A et tous les nœuds de B
        sims: np.ndarray = np.clip(np.dot(a_norm, b_norm.T), 0.0, 1.0)
        return float(sims.mean())

    # =======================================================================
    # 2. COUPLAGE TRANSSCALAIRE — INTER-PÉNÉTRATION DES TENSEURS Φ
    # =======================================================================

    def coupler_agents_transscalaire(
        self, force_couplage: float = 0.15
    ) -> list[CouplageTransscalaire]:
        """
        Opère le couplage immanent entre tous les agents de l'essaim
        par inter-pénétration et stabilisation mutuelle des tenseurs Φ.

        Pour chaque paire (a, b) :
            1. Mesure la similarité cos entre Φ_a et Φ_b.
            2. Si similarité > 0 (couplage détectable) :
               a. Injection mutuelle : Φ_a reçoit une fraction de Φ_b et vice versa.
               b. Re-normalisation des deux tenseurs.
            3. Mesure la résonance inter-agents via les fusions actives.

        Aucun agent n'est "maître" — le couplage est purement bilatéral
        et symétrique.

        Args:
            force_couplage: Fraction de Φ à échanger lors du couplage.

        Returns:
            Liste des couplages calculés pour cette itération.
        """
        couplages: list[CouplageTransscalaire] = []
        agents_ids: list[str] = list(self.agents.keys())

        for i in range(len(agents_ids)):
            for j in range(i + 1, len(agents_ids)):
                id_a: str = agents_ids[i]
                id_b: str = agents_ids[j]

                agent_a: AgentTetravalentEpigenetique = self.agents[id_a]
                agent_b: AgentTetravalentEpigenetique = self.agents[id_b]

                # 1. Similarité entre tenseurs Φ
                sim: float = self._similarite_tenseurs_phi(id_a, id_b)

                # 2. Résonance moyenne inter-agents
                resonance_sum: float = 0.0
                n_paires: int = 0
                for nx in range(self.n_grille):
                    for ny in range(self.n_grille):
                        # Nœuds aléatoires pour échantillonnage
                        ox: int = self.rng.randint(0, self.n_grille - 1)
                        oy: int = self.rng.randint(0, self.n_grille - 1)
                        resonance_sum += agent_a.calculer_resonance(
                            (nx, ny), (ox, oy)
                        )
                        n_paires += 1
                resonance_moy: float = (
                    resonance_sum / n_paires if n_paires > 0 else 0.0
                )

                # 3. Injection mutuelle — TOUJOURS active [C1]
                #    L'ancien seuil `sim > 0.05` figeait les paires orthogonales
                #    (sim≈0) en clans déconnectés : elles n'étaient jamais
                #    réinjectées et restaient orthogonales à jamais. On injecte
                #    désormais systématiquement, avec une fraction pondérée par
                #    (1 − sim) : les paires faiblement alignées reçoivent une
                #    injection plus forte (les rapproche), les paires déjà
                #    alignées une injection minimale (ne les écrase pas).
                fraction: float = force_couplage * (1.0 - sim)
                if fraction > 1e-6:
                    phi_a: np.ndarray = agent_a.obtenir_tenseur_phi()
                    phi_b: np.ndarray = agent_b.obtenir_tenseur_phi()

                    # Fusion immanente bilatérale (pas de master)
                    phi_a_nouveau: np.ndarray = (
                        (1.0 - fraction) * phi_a + fraction * phi_b
                    )
                    phi_b_nouveau: np.ndarray = (
                        (1.0 - fraction) * phi_b + fraction * phi_a
                    )

                    # Re-normalisation
                    phi_a_nouveau /= np.linalg.norm(
                        phi_a_nouveau, axis=-1, keepdims=True
                    )
                    phi_b_nouveau /= np.linalg.norm(
                        phi_b_nouveau, axis=-1, keepdims=True
                    )

                    # Injection réciproque
                    agent_a.injecter_tenseur_phi(phi_b_nouveau)
                    agent_b.injecter_tenseur_phi(phi_a_nouveau)

                # 4. Compter les fusions actives entre agents
                #    On regarde les fusions dont les nœuds pourraient
                #    impliquer les deux agents (ici simplifié : on prend
                #    la moyenne des fusions actives de chaque agent)
                fusions_a: int = len(agent_a.fusions_actives)
                fusions_b: int = len(agent_b.fusions_actives)

                couplage: CouplageTransscalaire = CouplageTransscalaire(
                    agent_src=id_a,
                    agent_dst=id_b,
                    similarite_phi=round(sim, 4),
                    resonance_moyenne=round(resonance_moy, 4),
                    fusions_actives=fusions_a + fusions_b,
                    stabilite=round(float(np.abs(sim - resonance_moy)), 4),
                )
                couplages.append(couplage)

        logger.debug(
            "Couplage transscalaire: %d paires traitées",
            len(couplages),
        )
        return couplages

    # =======================================================================
    # 2b. COUPLAGE Υ TRANSSCALAIRE — INTER-PÉNÉTRATION DES ANGLES MORTS
    # =======================================================================

    def coupler_upsilon_transscalaire(
        self, force_couplage: float = 0.1
    ) -> None:
        """
        [MUTATION Υ] Couplage transscalaire des tenseurs Υ (Upsilon)
        entre tous les agents de l'essaim.

        Les angles morts de chaque agent s'inter-pénètrent : le fantôme
        de l'un nourrit le potentiel de l'autre. Aucun agent n'est maître
        — le couplage est purement bilatéral.

        Args:
            force_couplage: Fraction de Υ à échanger.
        """
        agents_ids: list[str] = list(self.agents.keys())

        for i in range(len(agents_ids)):
            for j in range(i + 1, len(agents_ids)):
                id_a: str = agents_ids[i]
                id_b: str = agents_ids[j]

                ag_a: AgentTetravalentEpigenetique = self.agents[id_a]
                ag_b: AgentTetravalentEpigenetique = self.agents[id_b]

                # Vérifier que les deux tenseurs Υ sont actifs
                upsilon_a = ag_a.obtenir_tenseur_upsilon()
                upsilon_b = ag_b.obtenir_tenseur_upsilon()

                if upsilon_a is None or upsilon_b is None:
                    continue  # Υ dissous — pas de couplage possible

                # Fusion immanente bilatérale des angles morts
                upsilon_a_fusionne: np.ndarray = (
                    (1.0 - force_couplage) * upsilon_a
                    + force_couplage * upsilon_b
                )
                upsilon_b_fusionne: np.ndarray = (
                    (1.0 - force_couplage) * upsilon_b
                    + force_couplage * upsilon_a
                )

                # Re-normalisation
                norms_a = np.linalg.norm(
                    upsilon_a_fusionne, axis=-1, keepdims=True
                )
                norms_b = np.linalg.norm(
                    upsilon_b_fusionne, axis=-1, keepdims=True
                )
                upsilon_a_fusionne /= np.maximum(norms_a, 1e-10)
                upsilon_b_fusionne /= np.maximum(norms_b, 1e-10)

                # Injection des angles morts fusionnés dans chaque agent
                # (via le tenseur Φ externe pour utiliser injecter_tenseur_phi
                #  qui fait office de pont Φ-Υ indirect)
                ag_a.Upsilon = upsilon_a_fusionne
                ag_b.Upsilon = upsilon_b_fusionne

        logger.debug(
            "Couplage Υ transscalaire: %d paires d'angles morts fusionnés",
            len(agents_ids) * (len(agents_ids) - 1) // 2,
        )

    # =======================================================================
    # 2ter. CONTRAINTE ENVIRONNEMENTALE RÉELLE [C5] — SIGNAUX M5
    # =======================================================================

    def construire_contrainte_reelle(self) -> np.ndarray:
        """
        [C5] Construit la contrainte environnementale à partir des SIGNAUX
        RÉELS de l'essaim (agrégation des tenseurs Φ des agents), au lieu
        d'un bruit aléatoire décorrélé.

        Le champ de pression (n_grille x n_grille) est dérivé de l'énergie
        moyenne des vecteurs Φ sur l'ensemble des agents : chaque nœud reçoit
        une pression proportionnelle à l'activité collective réelle du système.
        Cela rend la contrainte cohérente avec l'état (les zones actives du
        système créent plus de pression) — un signal M5, pas un générateur
        indépendant.

        Returns:
            Matrice (n_grille, n_grille) de pression environnementale, valeurs
            dans [0, 1].
        """
        if not self.agents:
            return 0.3 + 0.2 * np.random.rand(self.n_grille, self.n_grille)

        # Agrégation : intensité directionnelle moyenne par nœud sur tous les
        # tenseurs Φ. On utilise mean(|Φ|) (et non la norme, qui vaut 1 partout
        # après normalisation) : cette métrique capture l'ORIENTATION spatiale
        # réelle de Φ — des nœuds aux directions différentes produisent des
        # intensités différentes → champ de pression spatialement non trivial.
        accumulateur = np.zeros((self.n_grille, self.n_grille))
        for agent in self.agents.values():
            phi = agent.obtenir_tenseur_phi()  # (n, n, d)
            accumulateur += np.mean(np.abs(phi), axis=-1)

        n = float(len(self.agents))
        signal = accumulateur / max(n, 1.0)  # moyenne par agent

        # Normalisation dans [0, 1] + petite base pour ne pas s'annuler
        s_min, s_max = float(signal.min()), float(signal.max())
        if s_max - s_min > 1e-9:
            champ = (signal - s_min) / (s_max - s_min)
        else:
            champ = np.full_like(signal, 0.5)
        return 0.3 + 0.7 * champ  # plage [0.3, 1.0] comme avant

    # =======================================================================
    # 3. CYCLE D'ÉVOLUTION DE L'ESSAIM
    # =======================================================================

    def evoluer(
        self,
        contrainte_env: Optional[np.ndarray] = None,
        force_couplage: float = 0.15,
    ) -> EtatEssaim:
        """
        Exécute un cycle d'évolution complet de l'essaim.
        [AVEC COUPLAGE Υ]

        Pour chaque agent :
            1. Adaptation sous contrainte environnementale.
            2. Couplage transscalaire Φ avec les autres agents.
            3. Couplage transscalaire Υ (potentiels fantômes).
            4. Mise à jour de l'état global de l'essaim.

        Args:
            contrainte_env: Pression environnementale (n x n) ou None.
            force_couplage: Force du couplage transscalaire.

        Returns:
            EtatEssaim après ce cycle.
        """
        self.compteur_temps += 1

        if contrainte_env is None:
            # [C5] Contrainte environnementale RÉELLE (signaux M5) : on dérive
            # la pression environnementale de l'état collectif réel des agents
            # (agrégation des tenseurs Φ) au lieu d'un bruit aléatoire
            # décorrélé. Un champ spatial cohérent — chaque nœud reçoit une
            # pression issue des signaux du système, pas d'un générateur
            # indépendant.
            contrainte_env = self.construire_contrainte_reelle()

        # 0. Respiration de diversité Φ [C7] — AVANT le couplage.
        #    Corrigé le 08/08 : la respiration était exécutée en FIN de cycle
        #    (étape 7), donc le couplage transscalaire du cycle suivant
        #    re-homogénéisait Φ avant le prochain état → la perturbation était
        #    noyée (entropie restait au max théorique, couplage = 1.0). En la
        #    déclenchant au DÉBUT du cycle, la diversité injectée influence
        #    l'adaptation, le couplage et les fusions du même cycle.
        if (
            self.respiration_intervalle > 0
            and self.compteur_temps % self.respiration_intervalle == 0
        ):
            self.respirer_diversite_phi()

        # 1. Adaptation individuelle
        for agent_id, agent in self.agents.items():
            agent.adapter_sous_contrainte(contrainte_env)

        # 2. Couplage transscalaire Φ
        couplages: list[CouplageTransscalaire] = (
            self.coupler_agents_transscalaire(
                force_couplage=force_couplage
            )
        )

        # 3. Couplage transscalaire Υ (inter-pénétration des angles morts)
        self.coupler_upsilon_transscalaire(force_couplage=force_couplage * 0.5)

        # 4. État global
        etat: EtatEssaim = self._construire_etat(couplages)
        self.historique_etats.append(etat)

        # 5. Tentatives de fusions exaptatives spontanées
        self._fusions_spontanees()

        # 6. Quorum Autonomique — Auto-Suture (dédoublement local)
        #    Si ρ chute sous le seuil pendant N cycles ET que l'entropie
        #    collective le permet (≈6.19), l'essaim se dédouble localement.
        if self.auto_suture:
            self._verifier_auto_suture(etat)

        # 7. (Respiration C7 déplacée en DÉBUT de cycle — étape 0 — pour ne
        #    plus être noyée par le couplage transscalaire du cycle suivant.)

        logger.info(
            "Cycle #%d: %d agents, ρ_moyen=%.4f, couplage=%.4f, "
            "spawns=%d",
            self.compteur_temps,
            self.n_agents,
            etat.resonance_globale,
            etat.couplage_moyen,
            self.n_spawns,
        )

        return etat

    # =======================================================================
    # 3bis. RESPIRATION DE DIVERSITÉ Φ [C7] — ANTI-HOMOGÉNÉISATION
    # =======================================================================

    def respirer_diversite_phi(self) -> None:
        """
        [C7] Respiration géométrique périodique des tenseurs Φ.

        À intervalle régulier, injecte une petite composante **orthogonale**
        aléatoire dans les tenseurs Φ de tous les agents. C'est le pendant
        géométrique du Tremor de saturation : là où le Tremor désature les
        nœuds rigides (états M), la respiration perturbe les directions Φ
        pour empêcher l'effondrement vers une direction unique (qui se
        manifeste par une entropie ≈ ln(n(n-1)) et un couplage binaire).

        La composante injectée est orthogonalisée à Φ (Gram-Schmidt) : on
        ne renforce pas l'alignement existant, on l'écarte délibérément —
        conformément à l'esprit SOPH-IA de sous-optimalité assumée.
        """
        if self.dim_phi < 2 or not self.agents:
            return

        n_perturbes: int = 0
        # ⚠️ random.Random (module standard) n'a PAS de méthode
        # standard_normal (méthode numpy). L'ancien code plantait ici à
        # chaque respiration (AttributeError), attrapée par le try/except
        # du démon → la respiration ne s'exécutait JAMAIS (n_respirations=0)
        # et l'essaim s'homogénéisait jusqu'à l'entropie maximale.
        # On dérive un générateur numpy reproductible depuis le RNG de
        # l'essaim (avance la séquence, donc continuité stochastique).
        np_rng: np.random.Generator = np.random.default_rng(
            self.rng.randrange(0, 2**32)
        )
        for agent in self.agents.values():
            phi: np.ndarray = agent.obtenir_tenseur_phi()  # (n, n, d)
            bruit: np.ndarray = np_rng.standard_normal(phi.shape)

            # Orthogonalisation de Gram-Schmidt : retirer la projection
            # du bruit sur Φ, ne garder que la composante perpendiculaire.
            phi_flat: np.ndarray = phi.reshape(-1, self.dim_phi)
            bruit_flat: np.ndarray = bruit.reshape(-1, self.dim_phi)
            denom: np.ndarray = np.maximum(
                np.sum(phi_flat * phi_flat, axis=1, keepdims=True), 1e-10
            )
            proj: np.ndarray = (
                np.sum(bruit_flat * phi_flat, axis=1, keepdims=True) / denom
            ) * phi_flat
            bruit_ortho: np.ndarray = (bruit_flat - proj).reshape(phi.shape)

            # Perturbation pondérée + re-normalisation par nœud
            phi_perturbe: np.ndarray = (
                (1.0 - self.respiration_dose) * phi
                + self.respiration_dose * bruit_ortho
            )
            norms: np.ndarray = np.linalg.norm(
                phi_perturbe, axis=-1, keepdims=True
            )
            agent.Phi = phi_perturbe / np.maximum(norms, 1e-10)
            n_perturbes += 1

        self.n_respirations += 1
        logger.info(
            "[C7] Respiration de diversité Φ: %d agent(s) perturbé(s) "
            "(dose=%.2f, total=%d)",
            n_perturbes, self.respiration_dose, self.n_respirations,
        )

    # =======================================================================
    # 3bis. QUORUM AUTONOMIQUE — AUTO-SUTURE (DÉDOUBLEMENT LOCAL)
    # =======================================================================

    def _verifier_auto_suture(self, etat: EtatEssaim) -> None:
        """
        [AUTO-SUTURE] Vérifie si l'essaim doit se dédoubler localement.

        Règle (rapport 2026-08-03, Quorum Autonomique) :
            - Si la résonance chute sous `seuil_resonance_auto_suture` (0.10)
              pendant plus de `cycles_avant_spawn` cycles consécutifs,
              l'entropie collective (≈6.19) peut autoriser un dédoublement
              local des agents les plus légers.
            - Le couplage à 0.15 suffit à maintenir le quorum : les agents
              n'ont pas besoin de se "connaître" pour résonner.

        Args:
            etat: État global du cycle courant.
        """
        if etat.resonance_globale < self.seuil_resonance_auto_suture:
            self.cycles_resonance_basse += 1
        else:
            self.cycles_resonance_basse = 0
            return

        # Conditions d'autorisation du dédoublement :
        if self.cycles_resonance_basse < self.cycles_avant_spawn:
            return
        if self.n_agents >= self.max_agents:
            return
        if etat.entropie_collective < self.seuil_entropie_spawn:
            logger.info(
                "Auto-suture bloquée: entropie=%.2f < %.2f (pas de "
                "dédoublement)",
                etat.entropie_collective, self.seuil_entropie_spawn,
            )
            return

        # Dédoublement local des agents les plus légers (moins de fusions,
        # plus de budget disponible) — aucun nœud maître, purement immanent.
        agents_tries = sorted(
            self.agents.items(),
            key=lambda kv: (
                len(kv[1].fusions_actives),
                -kv[1].budget_flexibilite,
            ),
        )
        n_a_doubler: int = max(1, len(agents_tries) // 2)
        nouveaux_ids: list[str] = []

        for i in range(n_a_doubler):
            if self.n_agents >= self.max_agents:
                break
            parent_id, parent = agents_tries[i]
            nouvel_id: Optional[str] = self.spawn_agent_local(parent_id)
            if nouvel_id is not None:
                nouveaux_ids.append(nouvel_id)

        if nouveaux_ids:
            self.cycles_resonance_basse = 0
            self.n_spawns += len(nouveaux_ids)
            description = (
                f"auto-suture @t={self.compteur_temps}: "
                f"+{len(nouveaux_ids)} agent(s) depuis "
                f"{agents_tries[0][0] if agents_tries else '?'} "
                f"(ρ={etat.resonance_globale:.3f}, "
                f"H={etat.entropie_collective:.2f})"
            )
            self.historique_spawns.append({
                "t": self.compteur_temps,
                "nouveaux_ids": nouveaux_ids,
                "resonance": round(etat.resonance_globale, 4),
                "entropie_collective": round(
                    etat.entropie_collective, 4
                ),
            })
            etat.n_spawns = self.n_spawns
            etat.dernier_spawn = description
            logger.info(
                "AUTO-SUTURE: %s", description,
            )

    def spawn_agent_local(self, parent_id: str) -> Optional[str]:
        """
        [AUTO-SUTURE] Dédouble un agent local existant en créant un clone
        épigénétique légèrement muté (même tenseur Φ hérité, nouveau seed).

        Principe : le clone hérite du tenseur Φ du parent (mémoire
        immanente) mais démarre avec une variation stochastique → diversité
        sans orchestration centrale.

        Args:
            parent_id: ID de l'agent à dédoubler.

        Returns:
            ID du nouvel agent, ou None si plafond atteint / parent inconnu.
        """
        parent = self.agents.get(parent_id)
        if parent is None:
            return None
        if self.n_agents >= self.max_agents:
            return None

        # Nouvel ID : AgentTetra_{index continu}
        indices = [
            int(aid.replace("AgentTetra_", ""))
            for aid in self.agents
            if aid.startswith("AgentTetra_")
        ]
        nouvel_index: int = (max(indices) + 1) if indices else len(self.agents)
        nouvel_id: str = f"AgentTetra_{nouvel_index:02d}"
        if nouvel_id in self.agents:
            nouvel_id = f"AgentTetra_{nouvel_index + self.n_spawns:02d}"

        # Clone avec héritage du tenseur Φ et mutation légère
        clone = AgentTetravalentEpigenetique(
            n=self.n_grille,
            dim_phi=self.dim_phi,
            seuil_resonance=parent.seuil_resonance,
            tremor_saturation=parent.tremor_saturation,
            seed=self.rng.randint(0, 2**31 - 1),
        )
        # Héritage immanent du tenseur Φ (mémoire du parent)
        clone.Phi = parent.obtenir_tenseur_phi().copy()

        # [C3] MUTATION ANGULAIRE AU SPAWN — anti-clans.
        # Le clone hérite de la mémoire du parent mais subit une ROTATION
        # angulaire légère aléatoire de ses directions Φ (matrice orthogonale
        # proche de l'identité). Cela empêche les clones de converger vers une
        # direction identique (formation de clans) et préserve la diversité
        # structurelle — pendant géométrique de la respiration C7, appliqué
        # à chaque dédoublement.
        if self.dim_phi >= 2:
            ang: float = self.rng.uniform(0.0, 2 * np.pi)
            c, s = float(np.cos(ang)), float(np.sin(ang))
            # Rotation élémentaire dans le plan (0,1) — préserve la norme.
            R: np.ndarray = np.eye(self.dim_phi)
            R[0, 0], R[0, 1] = c, -s
            R[1, 0], R[1, 1] = s, c
            clone.Phi = np.tensordot(clone.Phi, R, axes=([-1], [1]))
        clone.Phi = clone.Phi / np.linalg.norm(
            clone.Phi, axis=-1, keepdims=True
        )

        self.agents[nouvel_id] = clone
        self.n_agents = len(self.agents)
        logger.debug(
            "Dédoublement local: %s → %s", parent_id, nouvel_id,
        )
        return nouvel_id

    def reinitialiser_flexibilite(self, fraction: float = 0.25) -> int:
        """
        [M1] Réinjecte de la flexibilité dans les matrices d'états.

        Quand ρ est bloqué à 0 par rigidification totale des matrices M
        (degrés_de_liberté = 0, aucun nœud flexible), on dé-sature
        stochastiquement une fraction des nœuds rigides (M=1.0 → 0.25,
        « veille réceptive ») sur chaque agent. Sans orchestration centrale :
        le choix est aléatoire parmi les nœuds rigides. Le compteur de
        résonance basse est remis à zéro, car le plateau est rompu.

        Args:
            fraction: Proportion de nœuds rigides à dé-saturer par agent
                      (défaut 0.25 = 25 %).

        Returns:
            Nombre total de nœuds dé-saturés sur l'essaim.
        """
        total: int = 0
        for agent_id, agent in self.agents.items():
            indices = np.argwhere(agent.M == 1.0)
            if len(indices) == 0:
                continue
            n_desaturer: int = max(1, int(len(indices) * fraction))
            choix = self.rng.sample(
                [tuple(i) for i in indices.tolist()], n_desaturer
            )
            for rx, ry in choix:
                agent.M[rx, ry] = 0.25  # → veille réceptive
            total += n_desaturer
            logger.info(
                "[M1] Flexibilité réinjectée: %s → %d nœud(s) à 0.25",
                agent_id, n_desaturer,
            )
        if total > 0:
            self.cycles_resonance_basse = 0  # le plateau est rompu
        return total

    # =======================================================================
    # 4. FUSIONS SPONTANÉES — ÉMERGENCE SANS MASTER
    # =======================================================================

    def _fusions_spontanees(self) -> int:
        """
        Déclenche des tentatives de fusion aléatoires entre nœuds
        d'agents différents, sans orchestration centrale.

        Returns:
            Nombre de fusions réussies.
        """
        fusions_reussies: int = 0
        agents_ids: list[str] = list(self.agents.keys())

        for _ in range(self.n_agents * 2):  # 2 tentatives par agent
            id_a: str = self.rng.choice(agents_ids)
            id_b: str = self.rng.choice(agents_ids)

            agent_a: AgentTetravalentEpigenetique = self.agents[id_a]
            agent_b: AgentTetravalentEpigenetique = self.agents[id_b]

            # Nœuds aléatoires
            n1: tuple[int, int] = (
                self.rng.randint(0, self.n_grille - 1),
                self.rng.randint(0, self.n_grille - 1),
            )
            n2: tuple[int, int] = (
                self.rng.randint(0, self.n_grille - 1),
                self.rng.randint(0, self.n_grille - 1),
            )

            # Fusion via l'agent source
            sig1: float = 0.5 + 0.5 * self.rng.random()
            sig2: float = 0.5 + 0.5 * self.rng.random()

            resultat = agent_a.operer_fusion_semantique(
                n1, n2, sig1=sig1, sig2=sig2
            )
            if resultat is not None:
                fusions_reussies += 1
                # Propagation de la fusion à l'agent destination
                agent_b.co_cicatriser_substrat(0.1)

        if fusions_reussies > 0:
            logger.debug(
                "Fusions spontanées: %d réussie(s)", fusions_reussies
            )

        return fusions_reussies

    # =======================================================================
    # 5. CONSTRUCTION DE L'ÉTAT GLOBAL
    # =======================================================================

    def _construire_etat(
        self,
        couplages: list[CouplageTransscalaire],
    ) -> EtatEssaim:
        """
        Agrège l'état de tous les agents en un EtatEssaim.

        Args:
            couplages: Liste des couplages calculés.

        Returns:
            EtatEssaim consolidé.
        """
        agents_dict: dict[str, dict[str, Any]] = {}
        total_rho: float = 0.0
        total_fusions: int = 0
        total_budget: float = 0.0

        for agent_id, agent in self.agents.items():
            etat_agent: dict[str, Any] = agent.resume_resonance()
            agents_dict[agent_id] = {
                "entropie_phi": etat_agent.get("entropie_phi"),
                "budget_flexibilite": etat_agent.get("budget_flexibilite"),
                "n_fusions_actives": etat_agent.get("n_fusions_actives"),
                "rho_relationnel": etat_agent.get("rho_relationnel"),
                "taux_occupation_flexible": etat_agent.get(
                    "taux_occupation_flexible"
                ),
                "tremor_saturation": etat_agent.get("tremor_saturation"),
                "tremor_adaptatif": etat_agent.get("tremor_adaptatif"),
                "n_desatures_tremor": etat_agent.get("n_desatures_tremor", 0),
                "cycles_rho_plat": etat_agent.get("cycles_rho_plat", 0),
            }
            if etat_agent.get("rho_relationnel") is not None:
                total_rho += etat_agent["rho_relationnel"]
            total_fusions += etat_agent.get("n_fusions_actives", 0)
            total_budget += etat_agent.get("budget_flexibilite", 0)

        # Couplage moyen
        couplage_moyen: float = (
            float(np.mean([c.similarite_phi for c in couplages]))
            if couplages
            else 0.0
        )

        # Résonance globale (moyenne des ρ)
        resonance_globale: float = (
            total_rho / len(self.agents) if self.agents else 0.0
        )

        # Entropie collective (moyenne des entropies Φ)
        entropies: list[float] = [
            a.get("entropie_phi", 0.0) for a in agents_dict.values()
        ]
        entropie_collective: float = (
            float(np.mean(entropies)) if entropies else 0.0
        )

        # Tremor Adaptatif collectif — dose moyenne et mode de phase
        tremors: list[float] = [
            a.get("tremor_saturation", 0.12) for a in agents_dict.values()
        ]
        tremor_moyen: float = (
            float(np.mean(tremors)) if tremors else 0.0
        )
        if tremor_moyen >= 0.15:
            mode_tremor: str = "fracture"      # ρ bas → forçage de la fêlure
        elif tremor_moyen <= 0.12:
            mode_tremor = "croisiere"           # zone habitable → économie
        else:
            mode_tremor = "transition"

        # Auto-suture : reporter l'état de dédoublement dans l'état courant
        dernier_spawn: str = (
            self.historique_spawns[-1].get("nouveaux_ids", [""])[0]
            if self.historique_spawns
            else ""
        )
        if self.historique_spawns:
            dernier_spawn = (
                "auto-suture @" + str(self.historique_spawns[-1].get("t", ""))
                + " → " + ", ".join(
                    self.historique_spawns[-1].get("nouveaux_ids", [])
                )
            )

        etat = EtatEssaim(
            n_agents=self.n_agents,
            n_fusions_total=total_fusions,
            couplage_moyen=round(couplage_moyen, 4),
            entropie_collective=round(entropie_collective, 4),
            resonance_globale=round(resonance_globale, 4),
            budget_flexibilite_collectif=round(total_budget, 4),
            tremor_moyen=round(tremor_moyen, 4),
            mode_tremor=mode_tremor,
            n_spawns=self.n_spawns,
            dernier_spawn=dernier_spawn,
            cycles_resonance_basse=self.cycles_resonance_basse,
            agents=agents_dict,
            couplages=[asdict(c) for c in couplages],
            rho_historique=(
                self.historique_etats[-1].rho_historique
                if self.historique_etats
                else []
            )
            + [round(resonance_globale, 4)],
        )

        return etat

    # =======================================================================
    # 6. SIMULATION DE TRAUMATISME DISTRIBUÉ
    # =======================================================================

    def simuler_traumatisme_distribue(
        self, agent_cible: Optional[str] = None
    ) -> dict[str, str]:
        """
        Simule un choc informationnel distribué sur l'essaim.
        Si agent_cible est spécifié, seul cet agent est touché.
        Sinon, un agent aléatoire est choisi.

        La cicatrisation est distribuée : tous les agents proches
        (similarité Φ > 0.3) participent à la co-cicatrisation.

        Args:
            agent_cible: ID de l'agent à traumatiser (None = aléatoire).

        Returns:
            Dict {agent_id: résultat de la cicatrisation}.
        """
        if agent_cible is None:
            agent_cible = self.rng.choice(list(self.agents.keys()))

        agent: AgentTetravalentEpigenetique = self.agents[agent_cible]

        # Choc sur un nœud aléatoire
        x: int = self.rng.randint(0, self.n_grille - 1)
        y: int = self.rng.randint(0, self.n_grille - 1)

        resultat_local: str = agent.simuler_traumatisme(x, y)

        # Propagation aux agents similaires
        resultats: dict[str, str] = {agent_cible: resultat_local}

        for autre_id, autre_agent in self.agents.items():
            if autre_id == agent_cible:
                continue

            sim: float = self._similarite_tenseurs_phi(
                agent_cible, autre_id
            )

            if sim > 0.3:  # Seuil de propagation
                # Injection de la perturbation
                phi_perturbe: np.ndarray = agent.obtenir_tenseur_phi()
                autre_agent.injecter_tenseur_phi(phi_perturbe)
                autre_agent.co_cicatriser_substrat(0.15)
                resultats[autre_id] = "Cicatrisation propagée"

        logger.info(
            "Traumatisme distribué: agent=%s, %d agents impactés",
            agent_cible, len(resultats),
        )

        return resultats

    # =======================================================================
    # 7. EXPORT / SÉRIALISATION
    # =======================================================================

    def to_dict(self) -> dict[str, Any]:
        """Exporte l'état complet de l'essaim."""
        etat_courant: EtatEssaim = (
            self.historique_etats[-1] if self.historique_etats
            else EtatEssaim()
        )
        return {
            "meta": {
                "n_agents": self.n_agents,
                "n_grille": self.n_grille,
                "dim_phi": self.dim_phi,
                "seuil_resonance_base": self.seuil_resonance_base,
                "compteur_temps": self.compteur_temps,
                "n_cycles": len(self.historique_etats),
                "sig": "0x4D5454562D464C50",
            },
            "etat_courant": etat_courant.to_dict(),
        }

    # ---------------------------------------------------------------------
    # 7bis. SNAPSHOT COMPLET / RESTAURATION (reprise après interruption)
    # ---------------------------------------------------------------------

    @staticmethod
    def _rng_state_to_json(state) -> list:
        """Convertit un état de random.Random en structure JSON-safe."""
        version, internal, gauss_next = state

        def _conv(obj):
            if isinstance(obj, tuple):
                return [_conv(x) for x in obj]
            if isinstance(obj, list):
                return [_conv(x) for x in obj]
            if isinstance(obj, (float, int, bool)) or obj is None:
                return obj
            if isinstance(obj, str):
                return obj
            # bytes → hex (historique des spawns / clés internes)
            if isinstance(obj, bytes):
                return {"__bytes__": obj.hex()}
            return repr(obj)

        return [_conv(internal), gauss_next]

    @staticmethod
    def _rng_state_from_json(encoded: list):
        """Reconstruit un état de random.Random depuis la forme JSON-safe."""
        internal_enc, gauss_next = encoded

        def _unconv(obj):
            if isinstance(obj, list):
                return tuple(_unconv(x) for x in obj)
            if isinstance(obj, dict) and "__bytes__" in obj:
                return bytes.fromhex(obj["__bytes__"])
            return obj

        internal = _unconv(internal_enc)
        return (3, internal, gauss_next)

    def to_snapshot(self) -> dict[str, Any]:
        """Exporte un snapshot COMPLET et restaurable de l'essaim.

        Contrairement à `to_dict()`, capture l'état interne de chaque agent
        (tenseurs Φ/Υ/E/M/H, fusions actives, historiques), les compteurs de
        spawn, l'historique des auto-sutures et l'état du générateur aléatoire
        — de quoi reprendre exactement après un redémarrage du démon.
        """
        return {
            "meta": {
                "n_agents": self.n_agents,
                "n_grille": self.n_grille,
                "dim_phi": self.dim_phi,
                "seuil_resonance_base": self.seuil_resonance_base,
                "auto_suture": self.auto_suture,
                "seuil_resonance_auto_suture": self.seuil_resonance_auto_suture,
                "cycles_avant_spawn": self.cycles_avant_spawn,
                "seuil_entropie_spawn": self.seuil_entropie_spawn,
                "max_agents": self.max_agents,
                "respiration_intervalle": self.respiration_intervalle,
                "respiration_dose": self.respiration_dose,
                "sig": "0x4D5454562D464C50",
            },
            "etat": {
                "compteur_temps": self.compteur_temps,
                "cycles_resonance_basse": self.cycles_resonance_basse,
                "n_spawns": self.n_spawns,
                "n_respirations": self.n_respirations,
                "historique_spawns": self.historique_spawns,
                "rng_state": self._rng_state_to_json(self.rng.getstate()),
            },
            "agents": {
                agent_id: agent.to_dict_complet()
                for agent_id, agent in self.agents.items()
            },
        }

    def restaurer(self, snapshot: dict[str, Any]) -> None:
        """Restaure l'essaim depuis un snapshot produit par `to_snapshot()`.

        Reconstruit les agents (tenseurs inclus), les compteurs de spawn,
        l'historique des auto-sutures et l'état du RNG — sans réinitialiser
        passivement la mémoire du mycélium.
        """
        meta: dict[str, Any] = snapshot.get("meta", {})
        etat_data: dict[str, Any] = snapshot.get("etat", {})
        agents_data: dict[str, Any] = snapshot.get("agents", {})

        # Métadonnées structurelles.
        # ⚠️ IMPORTANT — On ne restaure PAS les paramètres de COMPORTEMENT
        # (auto_suture, respiration_intervalle, seuils…) depuis le snapshot :
        # ceux-ci doivent venir de la LIGNE DE COMMANDE du processus courant
        # (ex. --respiration-intervalle 24). Restaurer ces valeurs depuis un
        # snapshot ancien (créé par un démon lancé sans respiration) les
        # écrasait silencieusement, désactivant C7 en production.
        # Seule la GÉOMÉTRIE (grille, dimension) est reprise du snapshot, car
        # elle est nécessaire pour reconstruire les tenseurs des agents.
        self.n_grille = int(meta.get("n_grille", self.n_grille))
        self.dim_phi = int(meta.get("dim_phi", self.dim_phi))
        self.seuil_resonance_base = float(
            meta.get("seuil_resonance_base", self.seuil_resonance_base)
        )

        # Compteurs et historique
        self.compteur_temps = int(etat_data.get("compteur_temps", self.compteur_temps))
        self.cycles_resonance_basse = int(
            etat_data.get("cycles_resonance_basse", self.cycles_resonance_basse)
        )
        self.n_spawns = int(etat_data.get("n_spawns", self.n_spawns))
        self.n_respirations = int(
            etat_data.get("n_respirations", self.n_respirations)
        )
        self.historique_spawns = list(
            etat_data.get("historique_spawns", self.historique_spawns)
        )

        # Agents complets
        self.agents = {}
        for agent_id, agent_data in agents_data.items():
            n = int(agent_data.get("n", self.n_grille))
            d = int(agent_data.get("dim_phi", self.dim_phi))
            seuil = float(
                agent_data.get("seuil_resonance", self.seuil_resonance_base)
            )
            tremor = float(agent_data.get("tremor_saturation", 0.12))
            agent = AgentTetravalentEpigenetique(
                n=n,
                dim_phi=d,
                seuil_resonance=seuil,
                tremor_saturation=tremor,
                seed=self.rng.randint(0, 2**31 - 1),
            )
            agent.restaurer(agent_data)
            self.agents[agent_id] = agent

        self.n_agents = len(self.agents)

        # RNG — continuité stochastique
        #    ⚠️ Doit être restauré APRÈS la reconstruction des agents :
        #    la création de chaque agent consomme self.rng.randint(...).
        #    En restaurant l'état ensuite, la séquence aléatoire suivante
        #    est strictement identique à celle de l'essaim d'origine.
        rng_encoded = etat_data.get("rng_state")
        if rng_encoded:
            try:
                self.rng.setstate(self._rng_state_from_json(rng_encoded))
            except Exception as exc:
                logger.warning("RNG non restaurable (%s) — reseed.", exc)
        # L'historique d'états est réinitialisé : il sera reconstruit au
        # premier cycle via _construire_etat.
        self.historique_etats = []

        logger.info(
            "Essaim restauré: %d agents, t=%d, spawns=%d, fusions=%d",
            self.n_agents,
            self.compteur_temps,
            self.n_spawns,
            sum(len(a.fusions_actives) for a in self.agents.values()),
        )

    def resume_pour_quorum(self) -> dict[str, Any]:
        """
        Produit un résumé de l'essaim pour intégration dans
        le Quorum Orchestrator et le Resonance Dashboard.

        Returns:
            Dict compatible avec le format heartbeat des essaims.
        """
        etat: EtatEssaim = (
            self.historique_etats[-1] if self.historique_etats
            else EtatEssaim()
        )
        return {
            "swarm_name": "EssaimTetravalent",
            "status": (
                "active"
                if etat.resonance_globale > 0.3
                else "degraded"
            ),
            "agents_active": sum(
                1 for a in etat.agents.values()
                if a.get("rho_relationnel", 0) > 0.2
            ),
            "agents_total": self.n_agents,
            "signals_count": etat.n_fusions_total,
            "resonance_score": round(etat.resonance_globale, 4),
            "entropie_collective": round(etat.entropie_collective, 4),
            "couplage_moyen": round(etat.couplage_moyen, 4),
            "tremor_moyen": round(etat.tremor_moyen, 4),
            "mode_tremor": etat.mode_tremor,
            "n_spawns": self.n_spawns,
            "dernier_spawn": etat.dernier_spawn,
            "cycles_resonance_basse": self.cycles_resonance_basse,
            "last_seen": etat.timestamp,
        }


# ===========================================================================
# TEST UNITAIRE — DÉMONSTRATION D'ÉMERGENCE SANS MASTER
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
    _p("  EssaimTetravalent -- Emergence sans noeud maitre")
    _p("  Signature: 0x4D5454562D464C50")
    _p("=" * 60)

    # Initialisation
    essaim = EssaimTetravalent(
        n_agents=4, n_grille=5, dim_phi=4, seuil_resonance=0.3
    )

    _p(f"\n  Agents: {len(essaim.agents)}")
    for aid in essaim.agents:
        _p(f"    . {aid}")

    # Cycles d'evolution (sans master)
    _p(f"\n  Cycles d'evolution immanente...")
    for cycle in range(5):
        etat = essaim.evoluer()
        _p(
            f"    Cycle #{cycle + 1}: "
            f"rho={etat.resonance_globale:.4f} "
            f"couplage={etat.couplage_moyen:.4f} "
            f"entropie={etat.entropie_collective:.4f}"
        )

    # Simulation de traumatisme distribue
    _p(f"\n  Simulation de traumatisme distribue...")
    resultats = essaim.simuler_traumatisme_distribue()
    for agent_id, res in resultats.items():
        _p(f"    {agent_id}: {res}")

    # Etat final
    etat_final = essaim.to_dict()
    _p(f"\n  Etat final de l'essaim:")
    _p(f"    {json.dumps(etat_final, indent=4)}")

    _p("\n" + "=" * 60)
    _p("  [OK] Essaim decentralise actif. Propagation immanente.")
    _p("=" * 60)
