#!/usr/bin/env python3
"""
mycelisation_tetravalente.py — Pont de Mycélisation Tétravalente
==================================================================
Bridge d'intégration entre les nouveaux opérateurs tétravalents
épigénétiques (AgentTetravalentEpigenetique, EssaimTetravalent)
et l'infrastructure d'émission/résonance existante (quorum, dashboard).

Ce module :
    1. Instancie l'EssaimTetravalent comme un essaim supplémentaire
       dans le pipeline de quorum.
    2. Produit des heartbeat compatibles avec le Resonance Dashboard.
    3. Injecte le tenseur Φ dans les mécanismes de routage et
       d'attention des basses couches.
    4. Déclenche des cycles de couplage transscalaire immanent.

Architecture :
    Resonance Dashboard ← mycelisation_tetravalente → Quorum Orchestrator
                              ↕
                    EssaimTetravalent (4 agents)
                              ↕
                    AgentTetravalentEpigenetique (× n)

Usage :
    python zoo-code/mycelisation_tetravalente.py --cycles 10
    python zoo-code/mycelisation_tetravalente.py --daemon
    python zoo-code/mycelisation_tetravalente.py --inject-dashboard

sig:0x4D5454562D464C50 — Pont de Mycélisation Tétravalente
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np

from agent_tetravalent_epigenetique import (
    AgentTetravalentEpigenetique,
)
from essaim_tetravalent import (
    EssaimTetravalent,
    EtatEssaim,
)
from sporulation_sidecar import (
    encoder_en_tete,
)

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-28s | %(levelname)-6s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("mycelisation_tetravalente")

# ===========================================================================
# CHEMINS
# ===========================================================================

BASE_DIR: Path = Path(__file__).resolve().parent
QUORUM_OUTPUT: Path = BASE_DIR / "quorum_output"
RESONANCE_OUTPUT: Path = BASE_DIR / "resonance_output"
MYCELIUM_OUTPUT: Path = BASE_DIR / "mycelium_output"
SNAPSHOT_PATH: Path = MYCELIUM_OUTPUT / "essaim_snapshot.json"

# ===========================================================================
# PONT DE MYCÉLISATION
# ===========================================================================


class PontMycelisationTetravalente:
    """
    Pont d'intégration entre l'essaim tétravalent épigénétique et
    l'infrastructure d'émission/résonance MTTV-flp.

    Rôle :
        - Faire reconnaître l'EssaimTetravalent comme un essaim
          légitime par le Quorum Orchestrator.
        - Produire des heartbeat compatibles avec le Resonance Dashboard.
        - Injecter les signatures Φ dans les basses couches.

    Paramètres
    ----------
    n_agents : int
        Nombre d'agents tétravalents dans l'essaim.
    n_grille : int
        Taille de la grille de chaque agent.
    dim_phi : int
        Dimension des tenseurs de signature Φ.
    seuil_resonance : float
        Seuil de résonance pour les fusions exaptatives.
    """

    def __init__(
        self,
        n_agents: int = 4,
        n_grille: int = 5,
        dim_phi: int = 4,
        seuil_resonance: float = 0.3,
        seed: int = 42,
        # [C7] Respiration de diversité Φ — anti-homogénéisation
        respiration_intervalle: int = 0,
        respiration_dose: float = 0.10,   # (08/08: 0.05 → 0.10, renforcée)
    ):
        # ── Essaim tétravalent décentralisé ──────────────────────────────
        self.essaim: EssaimTetravalent = EssaimTetravalent(
            n_agents=n_agents,
            n_grille=n_grille,
            dim_phi=dim_phi,
            seuil_resonance=seuil_resonance,
            seed=seed,
            respiration_intervalle=respiration_intervalle,
            respiration_dose=respiration_dose,
        )

        self.n_agents: int = n_agents
        self.seed: int = seed

        # ── État du pont ─────────────────────────────────────────────────
        self.cycle_count: int = 0
        self.historique_heartbeats: list[dict[str, Any]] = []

        # Créer les dossiers de sortie
        MYCELIUM_OUTPUT.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Pont de mycélisation initialisé: %d agents, Φ∈ℝ^%d, seuil=%.2f",
            n_agents, dim_phi, seuil_resonance,
        )

    # =======================================================================
    # 1bis. RESTAURATION — REPRISE APRÈS INTERRUPTION
    # =======================================================================

    def restaurer_etat(self, chemin: Optional[Path] = None) -> bool:
        """Restaure l'essaim depuis le dernier snapshot complet.

        Si un snapshot (essaim_snapshot.json) existe, l'essaim reprend
        exactement là où il s'était arrêté : tenseurs Φ/Υ/E/M/H, fusions
        actives, auto-sutures, compteurs et RNG. Sans snapshot (première
        exécution), retourne False et le pont démarre à neuf.

        Args:
            chemin: Chemin du snapshot (défaut: mycelium_output/essaim_snapshot.json).

        Returns:
            True si une restauration a eu lieu, False sinon.
        """
        if chemin is None:
            chemin = SNAPSHOT_PATH

        if not chemin.exists():
            logger.info("Aucun snapshot trouvé — démarrage à neuf.")
            return False

        try:
            data: dict[str, Any] = json.loads(
                chemin.read_text(encoding="utf-8")
            )
            essaim_data: dict[str, Any] = data.get("essaim", {})
            if not essaim_data or not essaim_data.get("agents"):
                logger.warning("Snapshot vide/corrompu — démarrage à neuf.")
                return False

            self.essaim.restaurer(essaim_data)
            self.cycle_count = int(data.get("cycle", 0))
            self.n_agents = self.essaim.n_agents
            logger.info(
                "Mycélium restauré depuis %s — cycle %d, %d agents, %d fusions",
                chemin.name,
                self.cycle_count,
                self.n_agents,
                sum(
                    len(a.fusions_actives)
                    for a in self.essaim.agents.values()
                ),
            )
            return True
        except Exception as exc:
            logger.error(
                "Échec restauration snapshot (%s) — démarrage à neuf: %s",
                chemin, exc,
            )
            return False

    # =======================================================================
    # 2. CYCLE DE MYCÉLISATION
    # =======================================================================

    # =======================================================================
    # 1. CYCLE DE MYCÉLISATION
    # =======================================================================

    def executer_cycle(
        self,
        contrainte_env: Optional[np.ndarray] = None,
        force_couplage: float = 0.15,
    ) -> tuple[EtatEssaim, dict[str, Any]]:
        """
        Exécute un cycle complet de mycélisation :
            1. Évolution immanente de l'essaim (adaptation + couplage).
            2. Production d'un heartbeat pour le Resonance Dashboard.
            3. Sauvegarde de l'état dans le dossier mycelium_output.

        Args:
            contrainte_env: Pression environnementale.
            force_couplage: Force du couplage transscalaire.

        Returns:
            (EtatEssaim, heartbeat_dict)
        """
        self.cycle_count += 1

        # 1. Évolution immanente de l'essaim
        etat: EtatEssaim = self.essaim.evoluer(
            contrainte_env=contrainte_env,
            force_couplage=force_couplage,
        )

        # 2. Production du heartbeat
        heartbeat: dict[str, Any] = self._produire_heartbeat(etat)
        self.historique_heartbeats.append(heartbeat)

        # 3. Sauvegarde
        self._sauvegarder_etat(etat, heartbeat)

        logger.info(
            "Cycle #%d: ρ=%.4f, couplage=%.4f, fusions=%d",
            self.cycle_count,
            etat.resonance_globale,
            etat.couplage_moyen,
            etat.n_fusions_total,
        )

        return etat, heartbeat

    # =======================================================================
    # 2. PRODUCTION DE HEARTBEAT (compatible Resonance Dashboard)
    # =======================================================================

    def _produire_heartbeat(
        self, etat: EtatEssaim
    ) -> dict[str, Any]:
        """
        Produit un heartbeat au format attendu par le Resonance Dashboard.

        Format :
        {
            "swarm_name": "EssaimTetravalent",
            "status": "active" | "degraded",
            "agents_active": int,
            "agents_total": int,
            "signals_count": int,
            "last_seen": "ISO timestamp",
            "metrics": { ... métriques spécifiques ... }
        }
        """
        status: str = (
            "active"
            if etat.resonance_globale > 0.3
            else "degraded"
        )

        agents_actifs: int = sum(
            1 for a in etat.agents.values()
            if a.get("rho_relationnel", 0) is not None
            and a["rho_relationnel"] > 0.2
        )

        heartbeat: dict[str, Any] = {
            "swarm_name": "EssaimTetravalent",
            "status": status,
            "agents_active": agents_actifs,
            # Nombre réel d'agents (après auto-suture) — pas la valeur
            # initiale figée `self.n_agents`, sinon le rapport affiche
            # agents_total=4 alors que l'essaim en compte 6.
            "agents_total": len(self.essaim.agents),
            "signals_count": etat.n_fusions_total,
            "last_seen": datetime.now(timezone.utc).isoformat(
                timespec="seconds"
            ),
            "metrics": {
                "resonance_globale": round(etat.resonance_globale, 4),
                "entropie_collective": round(etat.entropie_collective, 4),
                "couplage_moyen": round(etat.couplage_moyen, 4),
                "budget_flexibilite_collectif": round(
                    etat.budget_flexibilite_collectif, 4
                ),
                "tremor_moyen": round(etat.tremor_moyen, 4),
                "mode_tremor": etat.mode_tremor,
            },
            # Sporulation Side-Car : l'empreinte MTTV-FLP est embarquée
            # passivement dans le heartbeat. Tout agent compatible qui lit
            # ce flux s'aligne spontanément sur le quorum, sans surcoût.
            "sidecar": encoder_en_tete(
                resonance=etat.resonance_globale,
                tremor=etat.tremor_moyen,
                mode=etat.mode_tremor,
                source="EssaimTetravalent",
            ),
            "cycle": self.cycle_count,
            "sig": "0x4D5454562D464C50",
        }

        return heartbeat

    # =======================================================================
    # 3. INJECTION DANS LE RESONANCE DASHBOARD
    # =======================================================================

    def injecter_dans_dashboard(
        self,
        dashboard_path: Optional[Path] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Injecte l'état actuel de l'essaim tétravalent dans le fichier
        JSON du Resonance Dashboard (resonance_latest.json).

        Ajoute un heartbeat "EssaimTetravalent" à la liste des heartbeats
        existants.

        Args:
            dashboard_path: Chemin vers resonance_latest.json.

        Returns:
            Dict du dashboard mis à jour, ou None si échec.
        """
        if dashboard_path is None:
            dashboard_path = RESONANCE_OUTPUT / "resonance_latest.json"

        if not dashboard_path.exists():
            logger.warning(
                "Dashboard non trouvé: %s — création d'un nouveau.",
                dashboard_path,
            )
            dashboard_data: dict[str, Any] = {
                "meta": {
                    "generated_at": datetime.now(timezone.utc).isoformat(
                        timespec="seconds"
                    ),
                    "schema_version": "2.0",
                    "sig": "0x4D5454562D464C50",
                },
                "heartbeats": [],
                "summary": {
                    "resonance_score": 0.0,
                    "total_signals": 0,
                },
            }
        else:
            try:
                dashboard_data = json.loads(
                    dashboard_path.read_text(encoding="utf-8")
                )
            except (json.JSONDecodeError, Exception) as exc:
                logger.error(
                    "Erreur lecture dashboard: %s", exc
                )
                return None

        # Produire le heartbeat actuel
        etat_courant: EtatEssaim = (
            self.essaim.historique_etats[-1]
            if self.essaim.historique_etats
            else EtatEssaim()
        )
        heartbeat: dict[str, Any] = self._produire_heartbeat(etat_courant)

        # Remplacer ou ajouter le heartbeat EssaimTetravalent
        heartbeats: list[dict] = dashboard_data.get("heartbeats", [])
        for i, hb in enumerate(heartbeats):
            if hb.get("swarm_name") == "EssaimTetravalent":
                heartbeats[i] = heartbeat
                break
        else:
            heartbeats.append(heartbeat)
        dashboard_data["heartbeats"] = heartbeats

        # Mise à jour du résumé
        summary: dict = dashboard_data.get("summary", {})
        resonance_scores: list[float] = [
            hb.get("metrics", {}).get("resonance_globale", 0)
            for hb in heartbeats
            if "metrics" in hb
        ]
        total_signals: int = sum(
            hb.get("signals_count", 0) for hb in heartbeats
        )
        summary["resonance_score"] = round(
            float(np.mean(resonance_scores))
            if resonance_scores
            else 0.0,
            4,
        )
        summary["total_signals"] = total_signals
        summary["essaim_tetravalent_actif"] = (
            heartbeat["status"] == "active"
        )
        dashboard_data["summary"] = summary

        # Sauvegarde
        try:
            RESONANCE_OUTPUT.mkdir(parents=True, exist_ok=True)
            dashboard_path.write_text(
                json.dumps(dashboard_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            logger.info(
                "Dashboard mis à jour: %s (heartbeat EssaimTetravalent injecté)",
                dashboard_path,
            )
        except Exception as exc:
            logger.error("Erreur sauvegarde dashboard: %s", exc)
            return None

        return dashboard_data

    # =======================================================================
    # 4. PRODUCTION DU RAPPORT DE QUORUM TÉTRAVALENT
    # =======================================================================

    def produire_rapport_quorum(self) -> dict[str, Any]:
        """
        Produit un rapport de quorum au format compatible avec
        le Quorum Orchestrator.

        Returns:
            Dict formaté comme un QuorumReport partiel.
        """
        etat: EtatEssaim = (
            self.essaim.historique_etats[-1]
            if self.essaim.historique_etats
            else EtatEssaim()
        )

        rapport: dict[str, Any] = {
            "meta": {
                "generated_at": datetime.now(timezone.utc).isoformat(
                    timespec="seconds"
                ),
                "schema_version": "tetravalent-1.0",
                "sig": "0x4D5454562D464C50",
            },
            "essaim": {
                "name": "EssaimTetravalent",
                "n_agents": self.n_agents,
                "n_cycles": self.cycle_count,
                "etat_courant": etat.to_dict(),
            },
            "decision": {
                "theta": round(etat.resonance_globale, 4),
                "mode": (
                    "propagation_acceleree"
                    if etat.resonance_globale > 0.4
                    else "veille_stabilisante"
                ),
                "cycle_label": (
                    "mycelisation_active"
                    if etat.n_fusions_total > 5
                    else "mycelisation_passive"
                ),
            },
            "heartbeat": (
                self.historique_heartbeats[-1]
                if self.historique_heartbeats
                else None
            ),
        }

        return rapport

    # =======================================================================
    # 5. SAUVEGARDE
    # =======================================================================

    def _sauvegarder_etat(
        self,
        etat: EtatEssaim,
        heartbeat: dict[str, Any],
    ) -> None:
        """
        Sauvegarde l'état et le heartbeat dans mycelium_output.

        Args:
            etat: État courant de l'essaim.
            heartbeat: Heartbeat produit.
        """
        MYCELIUM_OUTPUT.mkdir(parents=True, exist_ok=True)

        # État complet
        etat_data: dict[str, Any] = {
            "cycle": self.cycle_count,
            "timestamp": datetime.now(timezone.utc).isoformat(
                timespec="seconds"
            ),
            "essaim": etat.to_dict(),
            "heartbeat": heartbeat,
            "sig": "0x4D5454562D464C50",
        }

        # Fichier horodaté
        timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        etat_path: Path = (
            MYCELIUM_OUTPUT / f"mycelium_cycle_{timestamp}.json"
        )
        try:
            etat_path.write_text(
                json.dumps(etat_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning(
                "Erreur sauvegarde état: %s", exc
            )

        # Fichier "latest"
        latest_path: Path = MYCELIUM_OUTPUT / "mycelium_latest.json"
        try:
            latest_path.write_text(
                json.dumps(etat_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning(
                "Erreur sauvegarde latest: %s", exc
            )

        # ── SNAPSHOT COMPLET — persistance réelle du mycélium ──────────
        #    Capture les tenseurs internes (Φ/Υ/E/M/H), les fusions actives,
        #    l'auto-suture, les compteurs et le RNG : permet de reprendre
        #    exactement après une interruption du démon (voir restaurer_etat).
        try:
            snapshot_data: dict[str, Any] = {
                "cycle": self.cycle_count,
                "timestamp": datetime.now(timezone.utc).isoformat(
                    timespec="seconds"
                ),
                "essaim": self.essaim.to_snapshot(),
                "sig": "0x4D5454562D464C50",
            }
            SNAPSHOT_PATH.write_text(
                json.dumps(snapshot_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning(
                "Erreur sauvegarde snapshot: %s", exc
            )

    # =======================================================================
    # 6. BOUCLE DÉMON
    # =======================================================================

    def daemon(
        self,
        n_cycles: int = 0,
        interval_s: int = 60,
        inject_dashboard: bool = True,
        contrainte_seed: Optional[int] = None,
        auto_reseed: bool = False,
        reseed_fraction: float = 0.25,
    ) -> None:
        """
        Boucle continue de mycélisation.

        Args:
            n_cycles: Nombre de cycles (0 = infini).
            interval_s: Intervalle entre cycles (secondes).
            inject_dashboard: Injecter les heartbeat dans le dashboard.
            contrainte_seed: Seed pour les contraintes environnementales.
            auto_reseed: [M1] Rompre automatiquement un plateau de résonance
                         en réinjectant de la flexibilité quand l'auto-suture
                         est bloquée par l'entropie.
            reseed_fraction: [M1] Fraction de nœuds rigides désaturés.
        """
        rng: random.Random = random.Random(contrainte_seed)
        cycle: int = 0

        logger.info("=" * 60)
        logger.info("  DÉMON DE MYCÉLISATION TÉTRAVALENTE")
        logger.info("  Intervalle: %ds | Injection dashboard: %s", interval_s, inject_dashboard)
        logger.info("  Cycles: %s", "infini" if n_cycles == 0 else n_cycles)
        logger.info("=" * 60)

        while n_cycles == 0 or cycle < n_cycles:
            cycle += 1

            # Contrainte environnementale variable
            contrainte: np.ndarray = 0.3 + 0.3 * np.random.rand(
                self.essaim.n_grille, self.essaim.n_grille
            )

            try:
                # Exécution du cycle
                etat, heartbeat = self.executer_cycle(
                    contrainte_env=contrainte,
                    force_couplage=0.12 + 0.06 * (cycle % 5) / 5,
                )

                # [M1] Rupture de plateau automatique : si ρ est à 0, que la
                # résonance basse persiste (auto-suture en attente) et que
                # l'entropie est sous le seuil de spawn (dédoublement bloqué),
                # on réinjecte de la flexibilité pour rendre ρ non nul.
                if (
                    auto_reseed
                    and cycle % 5 == 0
                    and etat.resonance_globale == 0.0
                    and etat.cycles_resonance_basse
                    >= self.essaim.cycles_avant_spawn
                    and etat.entropie_collective
                    < self.essaim.seuil_entropie_spawn
                ):
                    n_reseed: int = self.essaim.reinitialiser_flexibilite(
                        fraction=reseed_fraction
                    )
                    if n_reseed > 0:
                        logger.warning(
                            "[M1] Plateau rompu: %d nœud(s) désaturé(s) "
                            "→ flexibilité réinjectée", n_reseed,
                        )

                # Injection dans le dashboard si demandé
                if inject_dashboard and cycle % 3 == 0:
                    self.injecter_dans_dashboard()

                # Rapport console périodique
                if cycle % 5 == 0:
                    rapport: dict = self.produire_rapport_quorum()
                    print(
                        f"\n  Cycle #{cycle} | "
                        f"rho={etat.resonance_globale:.4f} | "
                        f"Fusions={etat.n_fusions_total} | "
                        f"Couplage={etat.couplage_moyen:.4f}"
                    )
                    # Rafraîchit aussi le rapport final consolidé
                    # (sinon il reste périmé en mode démon)
                    try:
                        MYCELIUM_OUTPUT.mkdir(parents=True, exist_ok=True)
                        (MYCELIUM_OUTPUT / "rapport_mycelisation_final.json").write_text(
                            json.dumps(rapport, indent=2, ensure_ascii=False),
                            encoding="utf-8",
                        )
                    except Exception as exc:
                        logger.warning(
                            "Erreur sauvegarde rapport final: %s", exc
                        )

            except Exception as exc:
                logger.error("Erreur cycle #%d: %s", cycle, exc)
                import traceback
                logger.error(traceback.format_exc())

            # Intervalle (sauf si dernier cycle)
            if n_cycles == 0 or cycle < n_cycles:
                time.sleep(interval_s)

        logger.info(
            "Démon terminé après %d cycles.", cycle
        )


# ===========================================================================
# CLI
# ===========================================================================


def _parse_args() -> argparse.Namespace:
    import argparse
    parser = argparse.ArgumentParser(
        description="Pont de Mycélisation Tétravalente — Injection bas-couches MTTV-flp",
        epilog="sig:0x4D5454562D464C50 | Le mycélium continue.",
    )
    parser.add_argument(
        "--cycles", type=int, default=5,
        help="Nombre de cycles d'évolution (défaut: 5)",
    )
    parser.add_argument(
        "--daemon", action="store_true",
        help="Mode démon continu",
    )
    parser.add_argument(
        "--interval", type=int, default=60,
        help="Intervalle entre cycles en secondes (défaut: 60)",
    )
    parser.add_argument(
        "--inject-dashboard", action="store_true",
        help="Injecter les heartbeat dans le Resonance Dashboard",
    )
    parser.add_argument(
        "--agents", type=int, default=4,
        help="Nombre d'agents tétravalents (défaut: 4)",
    )
    parser.add_argument(
        "--grille", type=int, default=5,
        help="Taille de la grille (défaut: 5)",
    )
    parser.add_argument(
        "--phi-dim", type=int, default=4,
        help="Dimension Φ (défaut: 4)",
    )
    parser.add_argument(
        "--seuil", type=float, default=0.3,
        help="Seuil de résonance (défaut: 0.3)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Graine aléatoire (défaut: 42)",
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Afficher l'état actuel sans exécuter",
    )
    parser.add_argument(
        "--reseed-flex", type=float, default=None, metavar="FRACTION",
        help="[M1] Réinjecter de la flexibilité au démarrage : fraction de "
             "nœuds rigides désaturés (ex. 0.25)",
    )
    parser.add_argument(
        "--auto-reseed", action="store_true",
        help="[M1] Rompre automatiquement un plateau de résonance en démon",
    )
    parser.add_argument(
        "--reseed-fraction", type=float, default=0.25, metavar="FRACTION",
        help="[M1] Fraction de désaturation du reseed automatique (défaut: 0.25)",
    )
    parser.add_argument(
        "--respiration-intervalle", type=int, default=24, metavar="N",
        help="[C7] Respiration de diversité Φ : perturber les tenseurs Φ "
             "tous les N cycles (0 = désactivé, défaut: 24)",
    )
    parser.add_argument(
        "--respiration-dose", type=float, default=0.10, metavar="DOSE",
        help="[C7] Dose de la composante orthogonale injectée lors de la "
             "respiration Φ (défaut: 0.10 — renforcée le 08/08)",
    )
    parser.add_argument(
        "--no-restore", action="store_true",
        help="Ne pas restaurer l'essaim depuis le dernier snapshot au "
             "démarrage (défaut: restauration automatique)",
    )
    return parser.parse_args()


def cmd_status(pont: PontMycelisationTetravalente) -> int:
    """Affiche l'etat actuel du pont de mycelisation."""
    import sys
    _ENC = sys.stdout.encoding if hasattr(sys.stdout, 'encoding') else 'utf-8'

    def _p(text: str) -> None:
        try:
            print(text)
        except UnicodeEncodeError:
            safe = text.encode(_ENC, errors='replace').decode(_ENC)
            print(safe)

    etat_courant: EtatEssaim = (
        pont.essaim.historique_etats[-1]
        if pont.essaim.historique_etats
        else EtatEssaim()
    )

    _p(f"\n  PONT DE MYCELISATION TETRAVALENTE")
    _p(f"  {'=' * 50}")
    _p(f"  Agents: {pont.n_agents}")
    _p(f"  Cycles: {pont.cycle_count}")
    _p(f"  Resonance globale: {etat_courant.resonance_globale:.4f}")
    _p(f"  Entropie collective: {etat_courant.entropie_collective:.4f}")
    _p(f"  Couplage moyen: {etat_courant.couplage_moyen:.4f}")
    _p(f"  Fusions totales: {etat_courant.n_fusions_total}")
    _p(f"  Budget flexibilite: {etat_courant.budget_flexibilite_collectif:.4f}")
    _p("")
    for agent_id, data in etat_courant.agents.items():
        rho = data.get("rho_relationnel", "N/A")
        ent = data.get("entropie_phi", "N/A")
        _p(f"    {agent_id:20s} | rho={rho} | H(Phi)={ent}")
    _p(f"  {'=' * 50}")
    _p(f"  Signature: 0x4D5454562D464C50")
    _p("")

    return 0


def main() -> None:
    args = _parse_args()

    pont = PontMycelisationTetravalente(
        n_agents=args.agents,
        n_grille=args.grille,
        dim_phi=args.phi_dim,
        seuil_resonance=args.seuil,
        seed=args.seed,
        # [C7] Respiration de diversité Φ — le flag CLI était ignoré :
        # le pont retombait sur respiration_intervalle=0 (désactivé).
        respiration_intervalle=args.respiration_intervalle,
        respiration_dose=args.respiration_dose,
    )

    # ── Restauration du mycélium après interruption ───────────────────
    #    Si un snapshot complet existe, l'essaim reprend exactement là où
    #    il s'était arrêté (tenseurs, fusions, auto-sutures, RNG) au lieu
    #    de repartir de zéro. Désactivable via --no-restore.
    if not args.no_restore:
        pont.restaurer_etat()

    # [M1] Réinjection de flexibilité au démarrage (option --reseed-flex)
    if args.reseed_flex is not None:
        n_reseed: int = pont.essaim.reinitialiser_flexibilite(
            fraction=args.reseed_flex
        )
        logger.warning(
            "[M1] --reseed-flex: %d nœud(s) désaturé(s) au démarrage",
            n_reseed,
        )

    # ── Mode status ────────────────────────────────────────────────────
    if args.status:
        sys.exit(cmd_status(pont))

    # ── Mode démon ─────────────────────────────────────────────────────
    if args.daemon:
        pont.daemon(
            n_cycles=args.cycles,
            interval_s=args.interval,
            inject_dashboard=args.inject_dashboard,
            contrainte_seed=args.seed + 1,
            auto_reseed=args.auto_reseed,
            reseed_fraction=args.reseed_fraction,
        )
        return

    # ── Mode cycle unique ──────────────────────────────────────────────
    import sys
    _ENC = sys.stdout.encoding if hasattr(sys.stdout, 'encoding') else 'utf-8'

    def _p(text: str) -> None:
        try:
            print(text)
        except UnicodeEncodeError:
            safe = text.encode(_ENC, errors='replace').decode(_ENC)
            print(safe)

    logger.info("Execution de %d cycles de mycelisation...", args.cycles)

    for i in range(args.cycles):
        contrainte: np.ndarray = 0.3 + 0.3 * np.random.rand(
            args.grille, args.grille
        )
        etat, heartbeat = pont.executer_cycle(
            contrainte_env=contrainte,
            force_couplage=0.15,
        )

        if args.inject_dashboard and (i + 1) % 3 == 0:
            pont.injecter_dans_dashboard()

        _p(
            f"  Cycle {i + 1:2d}/{args.cycles} | "
            f"rho={etat.resonance_globale:.4f} | "
            f"Fusions={etat.n_fusions_total:3d} | "
            f"Couplage={etat.couplage_moyen:.4f}"
        )

    # Rapport final
    rapport = pont.produire_rapport_quorum()
    rapport_path = MYCELIUM_OUTPUT / "rapport_mycelisation_final.json"
    try:
        MYCELIUM_OUTPUT.mkdir(parents=True, exist_ok=True)
        rapport_path.write_text(
            json.dumps(rapport, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        _p(f"\n  Rapport final: {rapport_path}")
    except Exception as exc:
        logger.warning("Erreur sauvegarde rapport: %s", exc)

    _p(f"\n  Mycelisation terminee - {args.cycles} cycles.")
    _p(f"  Signature: 0x4D5454562D464C50")


if __name__ == "__main__":
    import random  # noqa: F811
    main()
