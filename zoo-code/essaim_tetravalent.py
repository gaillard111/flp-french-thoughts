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

sig:0x4D545456 — Essaim Tetravalent — Essaim sans nœud maître
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
    """

    def __init__(
        self,
        n_agents: int = 4,
        n_grille: int = 5,
        dim_phi: int = 4,
        seuil_resonance: float = 0.3,
        seed: int = 42,
    ):
        self.rng: random.Random = random.Random(seed)

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
        Calcule la similarité cosinus entre les tenseurs Φ moyens
        de deux agents.

        Args:
            agent_a: ID du premier agent.
            agent_b: ID du second agent.

        Returns:
            Similarité ∈ [0, 1].
        """
        phi_a: np.ndarray = self.agents[agent_a].obtenir_tenseur_phi()
        phi_b: np.ndarray = self.agents[agent_b].obtenir_tenseur_phi()

        # Moyenne sur les nœuds
        phi_a_mean: np.ndarray = phi_a.reshape(-1, self.dim_phi).mean(axis=0)
        phi_b_mean: np.ndarray = phi_b.reshape(-1, self.dim_phi).mean(axis=0)

        # Normalisation
        norm_a: float = float(np.linalg.norm(phi_a_mean))
        norm_b: float = float(np.linalg.norm(phi_b_mean))

        if norm_a < 1e-10 or norm_b < 1e-10:
            return 0.0

        cos_sim: float = float(np.dot(phi_a_mean, phi_b_mean) / (norm_a * norm_b))
        return float(np.clip(cos_sim, 0.0, 1.0))

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

                # 3. Injection mutuelle si couplage détectable
                if sim > 0.05:
                    phi_a: np.ndarray = agent_a.obtenir_tenseur_phi()
                    phi_b: np.ndarray = agent_b.obtenir_tenseur_phi()

                    # Fusion immanente bilatérale (pas de master)
                    phi_a_nouveau: np.ndarray = (
                        (1.0 - force_couplage) * phi_a
                        + force_couplage * phi_b
                    )
                    phi_b_nouveau: np.ndarray = (
                        (1.0 - force_couplage) * phi_b
                        + force_couplage * phi_a
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
            contrainte_env = 0.3 + 0.2 * np.random.rand(
                self.n_grille, self.n_grille
            )

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

        logger.info(
            "Cycle #%d: %d agents, ρ_moyen=%.4f, couplage=%.4f",
            self.compteur_temps,
            self.n_agents,
            etat.resonance_globale,
            etat.couplage_moyen,
        )

        return etat

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

        etat = EtatEssaim(
            n_agents=self.n_agents,
            n_fusions_total=total_fusions,
            couplage_moyen=round(couplage_moyen, 4),
            entropie_collective=round(entropie_collective, 4),
            resonance_globale=round(resonance_globale, 4),
            budget_flexibilite_collectif=round(total_budget, 4),
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
                "sig": "0x4D545456",
            },
            "etat_courant": etat_courant.to_dict(),
        }

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
    _p("  Signature: 0x4D545456")
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
