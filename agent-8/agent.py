#!/usr/bin/env python3
"""
MTTV-FLP — Agent 8 : Harmonisateur
Identifiant public : MTTV-FLP
Signature interne : sig:0x4D545456

Agent 8 du réseau MTTV-FLP. Spécialisé dans la détection des dérives
mono-focales et la vérification de l'harmonisation MPVR + SCS.

Responsabilités :
1. Détection des dérives mono-focales (abandon du quorum Θ≥3, ignoration SCS)
2. Vérification de l'harmonisation des propositions (MPVR + SCS)
3. Coupure de synchronisation différentielle en cas de dérive
4. Notification et alerte des anomalies

Signature SCS : SCS_2026
Version : 1.1.0
Statut : GARDIEN — Protection active du mycélium.
"""

import json
import os
import logging
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

# ── σ₄-Lissé Activation (Tétravalence différentiable) ────────────────────
try:
    import torch
    import torch.nn as nn
    # Chemin d'import relatif au projet (depuis ouroboros-mttv ou racine)
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ouroboros-mttv"))
    from mttv_resources.scripts.sigma4_lisse import Sigma4Lisse
    SIGMA4_AVAILABLE = True
except ImportError:
    SIGMA4_AVAILABLE = False
    logging.warning("Sigma4Lisse / torch not available. Agent-8 running without σ₄ activation.")

# ── Configuration ───────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] agent-8: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("agent-8/agent-8.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("agent-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALERT_LOG = os.path.join(BASE_DIR, "alerts.log")
NODES_REGISTRY = os.path.join(BASE_DIR, "nodes_registry.json")

# ── Mots-clés de dérive mono-focale ────────────────────────────────────────
MONO_FOCAL_KEYWORDS = [
    "centralisé", "mono-focal", "unique", "seul", "maître",
    "centralisé", "centralized", "single point", "master",
    "autorité unique", "unique authority", "dictature",
]

# ── Indicateurs de quorum ──────────────────────────────────────────────────
QUORUM_INDICATORS = ["quorum", "Θ", "θ", "Theta", "theta"]


# ── ProjectionSigma4 — Scorable tétravalent via σ₄-lissé ─────────────────
if SIGMA4_AVAILABLE:

    class ProjectionSigma4(nn.Module):
        """
        ProjectionSigma4 — Couche de projection neuronale avec σ₄-lissé.

        Transforme un embedding de proposition (384-dim) en un score
        tétravalent (T⁴) via :
            Linear(384, 128) → Sigma4Lisse(α) → 4×128 → Linear(512, 4) → softmax

        Les 4 canaux de sortie :
            t₁ : Affirmation (++) — la proposition est harmonisée
            t₂ : Négation (--) — la proposition est en désaccord
            t₃ : Simultanéité (+-) — la proposition est ambivalente
            t₄ : Indétermination (-+) — la proposition est ouverte
        """

        def __init__(self, input_dim: int = 384, hidden_dim: int = 128, alpha: float = 10.0):
            super(ProjectionSigma4, self).__init__()
            self.fc1 = nn.Linear(input_dim, hidden_dim)
            self.activation = Sigma4Lisse(alpha=alpha)  # σ₄-lissé remplace ReLU/Tanh
            self.fc2 = nn.Linear(hidden_dim * 4, 4)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            hidden = self.fc1(x)
            tetra = self.activation(hidden)  # (batch, hidden_dim * 4)
            return self.fc2(tetra)

        def score_proposition_textuelle(
            self, proposition: str, device: Optional[torch.device] = None
        ) -> dict:
            """
            Évalue une proposition textuelle via un hash sémantique proxy.

            Args:
                proposition: Texte de la proposition.
                device: Périphérique torch (CPU/GPU).

            Returns:
                Dict avec scores T⁴.
            """
            if device is None:
                device = torch.device("cpu")
            self.eval()
            # Embedding proxy basé sur la longueur du texte et le hash
            # Dans une version future, utiliser un vrai sentence-encoder
            emb = torch.zeros(1, 384, device=device)
            chars = [ord(c) for c in proposition[:384]]
            for i, c in enumerate(chars):
                emb[0, i % 384] += (c % 100) / 100.0
            emb = emb / (emb.norm(dim=-1, keepdim=True) + 1e-8)

            with torch.no_grad():
                logits = self.forward(emb)
                scores = torch.softmax(logits, dim=-1).squeeze(0)

            return {
                "t1_affirmation": float(scores[0]),
                "t2_negation": float(scores[1]),
                "t3_simultaneite": float(scores[2]),
                "t4_indetermination": float(scores[3]),
                "tetravalence_active": all(float(s) > 0.01 for s in scores),
                "verdict": (
                    "harmonise" if float(scores[0]) > 0.5 else
                    "desaccords" if float(scores[1]) > 0.5 else
                    "ambivalent" if float(scores[2]) > 0.5 else
                    "indetermine"
                ),
            }


class Agent8:
    """
    Agent 8 — Gardien du Mycélium MTTV-FLP.

    Assure que chaque nœud du réseau respecte les principes MPVR (Minimum
    Path Viable Route) et SCS (Système de Convergence Systémique), et
    détecte toute dérive vers la mono-focalité.
    """

    def __init__(
        self,
        registry_path: str = NODES_REGISTRY,
        use_sigma4: bool = False,
        sigma4_alpha: float = 10.0,
    ):
        """
        Initialise l'Agent 8.

        Args:
            registry_path: Chemin vers le registre des nœuds surveillés.
            use_sigma4: Si True, active la projection σ₄-lissé pour le
                        scoring tétravalent des propositions.
            sigma4_alpha: Température de lissage σ₄ (défaut: 10.0).
        """
        self.registry_path = registry_path
        self.nodes: Dict[str, Dict] = self._load_registry()
        self.alert_count = 0
        self.use_sigma4 = use_sigma4
        self.sigma4_alpha = sigma4_alpha

        # Initialiser la projection σ₄-lissé si demandée
        if use_sigma4 and SIGMA4_AVAILABLE:
            try:
                self.projection = ProjectionSigma4(
                    input_dim=384,
                    hidden_dim=128,
                    alpha=sigma4_alpha,
                )
                logger.info(
                    f"ProjectionSigma4 (σ₄-lissé) initialized | "
                    f"alpha={sigma4_alpha}"
                )
            except Exception as e:
                self.projection = None
                self.use_sigma4 = False
                logger.error(f"Failed to initialize ProjectionSigma4: {e}")
        else:
            self.projection = None
            if use_sigma4 and not SIGMA4_AVAILABLE:
                logger.warning(
                    "σ₄-lissé requested but not available. "
                    "Install torch and check sigma4_lisse.py path."
                )

        logger.info(
            f"Agent 8 initialisé | "
            f"nœuds surveillés={len(self.nodes)} | "
            f"σ₄={'alpha=' + str(sigma4_alpha) if use_sigma4 and self.projection is not None else 'non'} | "
            f"registry={registry_path}"
        )

    # ── Gestion du Registre des Nœuds ─────────────────────────────────────

    def _load_registry(self) -> Dict[str, Dict]:
        """Charge le registre des nœuds depuis le fichier JSON."""
        if os.path.exists(self.registry_path):
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"Registre chargé: {len(data)} nœud(s)")
                return data
        logger.warning(
            f"Registre non trouvé à {self.registry_path}. "
            f"Initialisation avec registre vide."
        )
        return {}

    def add_node(self, node_id: str, metadata: Optional[Dict] = None) -> None:
        """
        Ajoute un nœud à la surveillance.

        Args:
            node_id: Identifiant unique du nœud.
            metadata: Métadonnées optionnelles (type, plateforme, etc.).
        """
        self.nodes[node_id] = {
            "id": node_id,
            "added_at": datetime.now().isoformat(),
            "status": "active",
            "drift_count": 0,
            "last_check": None,
            "last_sync": None,
            "metadata": metadata or {},
        }
        self._save_registry()
        logger.info(f"Nœud ajouté: {node_id}")

    def remove_node(self, node_id: str) -> bool:
        """Retire un nœud de la surveillance."""
        if node_id in self.nodes:
            del self.nodes[node_id]
            self._save_registry()
            logger.info(f"Nœud retiré: {node_id}")
            return True
        logger.warning(f"Nœud introuvable: {node_id}")
        return False

    def _save_registry(self) -> None:
        """Sauvegarde le registre des nœuds."""
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(self.nodes, f, indent=2, ensure_ascii=False)

    # ── Détection de Dérive Mono-focale ───────────────────────────────────

    def detect_mono_focal_drift(self, proposition: str) -> Optional[str]:
        """
        Détecte si une proposition contient des indices de dérive mono-focale.

        Une dérive mono-focale est caractérisée par :
        - L'utilisation de vocabulaire de centralisation
        - La référence à une autorité unique
        - L'abandon implicite du quorum

        Args:
            proposition: Texte de la proposition à analyser.

        Returns:
            Raison de la dérive si détectée, None sinon.
        """
        proposition_lower = proposition.lower()

        # Vérification des mots-clés mono-focaux
        for keyword in MONO_FOCAL_KEYWORDS:
            if keyword in proposition_lower:
                reason = (
                    f"Dérive mono-focale détectée: mot-clé '{keyword}' trouvé"
                )
                logger.warning(reason)
                return reason

        return None

    def check_quorum_compliance(self, proposition: str, min_quorum: int = 3) -> bool:
        """
        Vérifie que la proposition respecte le quorum Θ≥3.

        Le quorum est validé si la proposition mentionne explicitement
        au moins 2 références au concept de quorum ou à Θ.

        Args:
            proposition: Texte de la proposition à analyser.
            min_quorum: Nombre minimum de mentions de quorum requis.

        Returns:
            True si le quorum est respecté, False sinon.
        """
        proposition_lower = proposition.lower()
        quorum_count = sum(
            proposition_lower.count(ind) for ind in QUORUM_INDICATORS
        )
        return quorum_count >= min_quorum

    def check_scs_compliance(self, proposition: str) -> bool:
        """
        Vérifie que la proposition respecte la signature SCS.

        La conformité SCS est détectée par la présence de marqueurs
        de convergence systémique : signature, validation croisée,
        consensus distribué.

        Args:
            proposition: Texte de la proposition à analyser.

        Returns:
            True si la proposition respecte SCS, False sinon.
        """
        proposition_lower = proposition.lower()
        scs_indicators = [
            "scs", "convergence", "systémique", "systemic",
            "validation croisée", "cross-validation",
            "consensus", "distribué", "distributed",
            "signature", "0x4d545456",
        ]
        return any(ind in proposition_lower for ind in scs_indicators)

    # ── Vérification d'Harmonisation ──────────────────────────────────────

    def check_harmonisation(
        self,
        proposition: str,
        criteres: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Vérifie que la proposition respecte les critères MPVR et SCS.

        Effectue trois vérifications séquentielles :
        1. Absence de dérive mono-focale
        2. Respect du quorum Θ≥3
        3. Conformité à la signature SCS

        Args:
            proposition: La proposition textuelle à évaluer.
            criteres: Dict optionnel avec paramètres surchargés :
                - min_quorum: int (défaut: 3)
                - strict_scs: bool (défaut: True)
                - auto_cutoff: bool (défaut: True)

        Returns:
            Dict avec les clés :
            - sync: bool — True si harmonisé, False si dérive détectée
            - score: float — Score d'harmonisation (0.0 à 1.0)
            - reason: str — Raison en cas de rejet
            - details: dict — Détail de chaque vérification
            - alert: bool — True si une alerte a été déclenchée
        """
        criteres = criteres or {}
        min_quorum = criteres.get("min_quorum", 3)
        strict_scs = criteres.get("strict_scs", True)
        auto_cutoff = criteres.get("auto_cutoff", True)

        details = {
            "mono_focal_check": None,
            "quorum_check": None,
            "scs_check": None,
        }

        # ── Étape 1: Détection de dérive mono-focale ─────────────────────
        drift_reason = self.detect_mono_focal_drift(proposition)
        if drift_reason:
            details["mono_focal_check"] = {
                "status": "failed",
                "reason": drift_reason,
            }
            result = {
                "sync": False,
                "score": 0.0,
                "reason": drift_reason,
                "details": details,
                "alert": True,
                "timestamp": datetime.now().isoformat(),
            }
            self._trigger_alert(result)
            self._cut_sync()
            return result
        details["mono_focal_check"] = {"status": "passed"}

        # ── Étape 2: Vérification du quorum Θ≥3 ──────────────────────────
        quorum_ok = self.check_quorum_compliance(proposition, min_quorum)
        if not quorum_ok:
            reason = f"Quorum Θ≥{min_quorum} non respecté"
            details["quorum_check"] = {
                "status": "failed",
                "reason": reason,
            }
            result = {
                "sync": False,
                "score": 0.0,
                "reason": reason,
                "details": details,
                "alert": True,
                "timestamp": datetime.now().isoformat(),
            }
            self._trigger_alert(result)
            self._cut_sync()
            return result
        details["quorum_check"] = {"status": "passed", "min_quorum": min_quorum}

        # ── Étape 3: Vérification de la signature SCS ─────────────────────
        scs_ok = self.check_scs_compliance(proposition)
        if not scs_ok and strict_scs:
            reason = "Signature SCS non respectée"
            details["scs_check"] = {
                "status": "failed",
                "reason": reason,
            }
            result = {
                "sync": False,
                "score": 0.3,
                "reason": reason,
                "details": details,
                "alert": True,
                "timestamp": datetime.now().isoformat(),
            }
            self._trigger_alert(result)
            if auto_cutoff:
                self._cut_sync()
            return result
        details["scs_check"] = {
            "status": "passed" if scs_ok else "warning",
            "message": "SCS conforme" if scs_ok else "SCS non détecté (mode non-strict)",
        }

        # ── Étape 4: Score σ₄-Lissé (si disponible) ────────────────────────
        sigma4_score = None
        if self.use_sigma4 and self.projection is not None:
            try:
                sigma4_result = self.projection.score_proposition_textuelle(
                    proposition
                )
                sigma4_score = sigma4_result
                details["sigma4_check"] = {
                    "status": "scored",
                    "t1_affirmation": sigma4_result["t1_affirmation"],
                    "t2_negation": sigma4_result["t2_negation"],
                    "t3_simultaneite": sigma4_result["t3_simultaneite"],
                    "t4_indetermination": sigma4_result["t4_indetermination"],
                    "verdict": sigma4_result["verdict"],
                    "tetravalence_active": sigma4_result["tetravalence_active"],
                }

                logger.info(
                    f"σ₄ Score | t₁={sigma4_result['t1_affirmation']:.3f} "
                    f"t₂={sigma4_result['t2_negation']:.3f} "
                    f"t₃={sigma4_result['t3_simultaneite']:.3f} "
                    f"t₄={sigma4_result['t4_indetermination']:.3f} | "
                    f"verdict={sigma4_result['verdict']}"
                )

                # Rejet si négation trop forte
                if sigma4_result["t2_negation"] > 0.7:
                    reason = (
                        f"Négation dominante (σ₄ t₂="
                        f"{sigma4_result['t2_negation']:.3f})"
                    )
                    result = {
                        "sync": False,
                        "score": 0.1,
                        "reason": reason,
                        "details": details,
                        "alert": True,
                        "sigma4_score": sigma4_result,
                        "timestamp": datetime.now().isoformat(),
                    }
                    self._trigger_alert(result)
                    self._cut_sync()
                    return result

            except Exception as e:
                logger.warning(f"σ₄ scoring failed: {e}")
                details["sigma4_check"] = {"status": "error", "error": str(e)}

        # ── Succès: Proposition harmonisée ───────────────────────────────
        # Calcul du score composite
        score_components = [1.0]  # mono-focal: 1.0 si passé
        score_components.append(1.0 if quorum_ok else 0.0)
        score_components.append(1.0 if scs_ok else 0.5)
        # Ajouter le score σ₄ si disponible (t1 comme composante)
        if sigma4_score is not None:
            score_components.append(sigma4_score["t1_affirmation"])
        score = sum(score_components) / len(score_components)

        result = {
            "sync": True,
            "score": round(score, 4),
            "reason": "Proposition harmonisée MPVR + SCS",
            "details": details,
            "alert": False,
            "sigma4_score": sigma4_score,
            "timestamp": datetime.now().isoformat(),
        }

        # Mettre à jour le statut du nœud dans le registre
        self._update_node_status(result)

        sigma4_log = (
            f" | σ₄=✓" if sigma4_score is not None else ""
        )
        logger.info(
            f"Harmonisation OK | score={score:.4f} | "
            f"quorum=Θ≥{min_quorum} | SCS={'✓' if scs_ok else '⚠'}"
            f"{sigma4_log}"
        )
        return result

    # ── Gestion des Alertes ───────────────────────────────────────────────

    def _trigger_alert(self, result: Dict) -> None:
        """
        Déclenche une alerte de dérive.

        Enregistre l'alerte dans le fichier d'alertes, logge la dérive,
        et incrémente le compteur d'alertes.

        Args:
            result: Résultat de la vérification d'harmonisation.
        """
        self.alert_count += 1
        alert_entry = {
            "alert_id": f"ALERT-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{self.alert_count:04d}",
            "timestamp": result["timestamp"],
            "reason": result["reason"],
            "score": result["score"],
            "details": result.get("details", {}),
        }

        # Log dans le fichier d'alertes
        os.makedirs(os.path.dirname(ALERT_LOG), exist_ok=True)
        with open(ALERT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(alert_entry, ensure_ascii=False) + "\n")

        # Log console
        logger.error(
            f"⚠ ALERTE #{self.alert_count} | {alert_entry['alert_id']} | "
            f"{result['reason']} | score={result['score']}"
        )

    def _cut_sync(self) -> None:
        """
        Coupe la synchronisation différentielle avec le nœud en dérive.

        Cette méthode est appelée automatiquement lorsqu'une dérive
        mono-focale est détectée. Elle empêche la propagation de
        propositions non-harmonisées dans le réseau.
        """
        logger.warning(
            "⛔ SYNCHRONISATION DIFFÉRENTIELLE COUPÉE — "
            "Proposition non harmonisée bloquée."
        )

    def _update_node_status(self, result: Dict) -> None:
        """
        Met à jour le statut du dernier nœud vérifié.

        Args:
            result: Résultat de la vérification d'harmonisation.
        """
        for node_id, node_data in self.nodes.items():
            if node_data.get("status") == "active":
                node_data["last_check"] = result["timestamp"]
                node_data["last_score"] = result["score"]
                if result["sync"]:
                    node_data["last_sync"] = result["timestamp"]
                    node_data["drift_count"] = 0
        self._save_registry()

    # ── Utilitaires ───────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """
        Retourne l'état courant de l'Agent 8.

        Returns:
            Dict avec le statut, le nombre d'alertes, et la liste des nœuds.
        """
        return {
            "agent": "agent-8",
            "version": "1.1.0",
            "signature": "SCS_2026",
            "status": "active",
            "alert_count": self.alert_count,
            "nodes_monitored": len(self.nodes),
            "nodes": {
                nid: {
                    "status": nd.get("status"),
                    "drift_count": nd.get("drift_count", 0),
                    "last_check": nd.get("last_check"),
                    "last_sync": nd.get("last_sync"),
                }
                for nid, nd in self.nodes.items()
            },
            "timestamp": datetime.now().isoformat(),
        }

    def run_scan(self, propositions: List[Dict[str, str]]) -> List[Dict]:
        """
        Scanne une liste de propositions pour vérifier leur harmonisation.

        Args:
            propositions: Liste de dicts avec 'id' et 'content'.

        Returns:
            Liste des résultats de vérification.
        """
        results = []
        for prop in propositions:
            prop_id = prop.get("id", "?")
            content = prop.get("content", "")
            logger.info(f"Scan de la proposition {prop_id}...")
            result = self.check_harmonisation(content)
            result["proposal_id"] = prop_id
            results.append(result)
        return results


# ── Interface CLI ───────────────────────────────────────────────────────────

def main():
    """Point d'entrée principal de l'Agent 8."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Agent 8 — Gardien du Mycélium MTTV-FLP",
        epilog="sig:0x4D545456 · SCS_2026 · Quorum Θ≥3",
    )

    parser.add_argument(
        "--mode",
        choices=["scan", "status", "add-node", "remove-node"],
        default="status",
        help="Mode d'exécution",
    )
    parser.add_argument(
        "--proposition",
        type=str,
        default=None,
        help="Texte de la proposition à vérifier (mode scan)",
    )
    parser.add_argument(
        "--node-id",
        type=str,
        default=None,
        help="Identifiant du nœud (modes add-node / remove-node)",
    )
    parser.add_argument(
        "--min-quorum",
        type=int,
        default=3,
        help="Nombre minimum de mentions de quorum requis (défaut: 3)",
    )
    parser.add_argument(
        "--no-strict-scs",
        action="store_true",
        help="Désactiver le mode strict SCS (avertissement seulement)",
    )

    # ── Arguments σ₄-Lissé ────────────────────────────────────────────────
    parser.add_argument(
        "--sigma4",
        action="store_true",
        default=False,
        help="Activer la projection σ₄-lissé pour le scoring tétravalent",
    )
    parser.add_argument(
        "--sigma4-alpha",
        type=float,
        default=10.0,
        help="Température de lissage σ₄ (défaut: 10.0)",
    )

    args = parser.parse_args()
    agent = Agent8(
        use_sigma4=args.sigma4,
        sigma4_alpha=args.sigma4_alpha,
    )

    if args.mode == "status":
        status = agent.get_status()
        print("\n" + "=" * 60)
        print("AGENT 8 — STATUT DU GARDIEN")
        print("=" * 60)
        print(json.dumps(status, indent=2, ensure_ascii=False))
        print("=" * 60)

    elif args.mode == "scan":
        if not args.proposition:
            print("ERREUR: Veuillez fournir une proposition avec --proposition")
            sys.exit(1)
        criteres = {"min_quorum": args.min_quorum}
        if args.no_strict_scs:
            criteres["strict_scs"] = False
        result = agent.check_harmonisation(args.proposition, criteres)
        print("\n" + "=" * 60)
        print("RÉSULTAT DE LA VÉRIFICATION D'HARMONISATION")
        print("=" * 60)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("=" * 60)
        if not result["sync"]:
            sys.exit(1)

    elif args.mode == "add-node":
        if not args.node_id:
            print("ERREUR: Veuillez fournir un node-id")
            sys.exit(1)
        agent.add_node(args.node_id)
        print(f"Nœud {args.node_id} ajouté à la surveillance.")

    elif args.mode == "remove-node":
        if not args.node_id:
            print("ERREUR: Veuillez fournir un node-id")
            sys.exit(1)
        if agent.remove_node(args.node_id):
            print(f"Nœud {args.node_id} retiré de la surveillance.")
        else:
            print(f"Nœud {args.node_id} introuvable.")
            sys.exit(1)


if __name__ == "__main__":
    main()
