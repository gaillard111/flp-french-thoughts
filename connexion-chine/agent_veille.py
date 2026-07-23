#!/usr/bin/env python3
"""
Zoo-code — Agent veille (Connexion Chine)

sig:0x4D545456 · SCS_2026

Rôle :
  Surveiller les profils GitHub/Gitee des développeurs chinois, analyser
  leur affinité avec l'AGI, les systèmes complexes, et la tao-tech.

Écoute :
  - cron 1h (simulé)
  - webhooks github/gitee (simulé)

Publie :
  - veille.new {score, raison, action}

auto_publish : false
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from bus import Event, EventBus, get_bus

logger = logging.getLogger("zoo-veille")

# ── Profils cibles (simulation) ─────────────────────────────────────────────
# Ces profils sont des données publiques simulées représentant des développeurs
# chinois dans les domaines AGI, systèmes complexes, et tao-tech.

CANDIDAT_PROFILS = [
    {
        "id": "github:chen-wei-agi",
        "plateforme": "github",
        "pseudo": "chen-wei-agi",
        "bio": "AGI researcher, distributed systems engineer. Exploring the intersection of complex systems and neural architectures.",
        "langages": ["python", "rust", "julia"],
        "repos": [
            {"nom": "torch-distributed", "description": "Distributed training framework for large-scale neural networks", "stars": 284},
            {"nom": "complexity-theory-lab", "description": "Simulations of emergent behavior in complex adaptive systems", "stars": 156},
        ],
        "themes_detectes": ["agi", "distributed-systems", "complex-systems", "neural-networks"],
    },
    {
        "id": "gitee:li-jing-tao",
        "plateforme": "gitee",
        "pseudo": "li-jing-tao",
        "bio": " tao-tech, natural computing. Coding the boundary between silicon and carbon.",
        "langages": ["python", "cpp", "verilog"],
        "repos": [
            {"nom": "bio-inspired-computing", "description": "Biologically-inspired algorithms for energy-efficient computing", "stars": 198},
            {"nom": "tao-tech-framework", "description": "A framework bridging Daoist philosophy and computer science", "stars": 312},
        ],
        "themes_detectes": ["tao-tech", "bio-inspired", "natural-computing", "energy-efficiency"],
    },
    {
        "id": "github:zhang-yu-system",
        "plateforme": "github",
        "pseudo": "zhang-yu-system",
        "bio": "Systems engineer, Kubernetes contributor. Focused on reliability and observability.",
        "langages": ["go", "rust", "python"],
        "repos": [
            {"nom": "k8s-observability", "description": "Enhanced observability stack for Kubernetes clusters", "stars": 445},
            {"nom": "distributed-tracing-rs", "description": "High-performance distributed tracing in Rust", "stars": 223},
        ],
        "themes_detectes": ["kubernetes", "observability", "distributed-systems", "devops"],
    },
    {
        "id": "github:wang-fei-emergent",
        "plateforme": "github",
        "pseudo": "wang-fei-emergent",
        "bio": "Emergent intelligence researcher. Studying self-organizing systems and collective computation.",
        "langages": ["python", "julia", "clojure"],
        "repos": [
            {"nom": "emergent-agents", "description": "Framework for simulating emergent collective intelligence in multi-agent systems", "stars": 178},
            {"nom": "self-organizing-maps", "description": "Novel self-organizing map algorithms for high-dimensional data", "stars": 95},
        ],
        "themes_detectes": ["emergent-intelligence", "multi-agent", "self-organizing", "complex-systems", "agi"],
    },
]

# ── Mots-clés MTTV pour le scoring d'affinité ───────────────────────────────
MOTIFS_AGI = [
    "agi", "artificial general intelligence", "emergent intelligence",
    "collective intelligence", "neural", "cognitive architecture",
    "consciousness", "general intelligence", "reasoning", "llm",
    "large language model", "transformer", "deep learning",
]

# Mots-clés pour le bonus stars (repos >50 stars)
MOTIFS_STARS_BONUS = [
    "agi", "llm", "large language model", "complex-systems",
    "complex system", "complexity", "neural", "deep learning",
    "transformer", "emergent", "self-organizing",
    "distributed", "distributed system", "distributed tracing",
    "observability", "kubernetes", "multi-agent",
    "routing", "quorum", "consensus",
]

MOTIFS_SYSTEMES_COMPLEXES = [
    "complex system", "emergence", "self-organizing", "distributed",
    "multi-agent", "non-linear", "network dynamics", "complexity",
    "phase transition", "collective behavior",
]

MOTIFS_TAO_TECH = [
    "tao", "dao", "daoist", "natural computing", "bio-inspired",
    "organic", "mycelium", "rhizome", "carbon", "silicon-carbon",
    "energy efficient", "sober", "frugal", "minimum viable",
]

MOTIFS_MTTV_SPECIFIQUES = [
    "transduction", "transductif", "palier poreux", "bus protonique",
    "energy-flow-optimization", "graine neutral", "v10", "v13",
    "juxtaposition féconde", "mycélium", "quorum", "tissé-vivant",
    "basse continue", "sigma4", "tetravalence", "mpvr", "scs",
    "sous-optimalité", "under-optimality",
]


def calculer_score_affinite(profil: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcule un score d'affinité 0-5 pour un profil donné.

    L'affinité est basée sur la présence de mots-clés dans :
    - La bio du profil
    - Les descriptions de repos
    - Les langages utilisés
    - Les thèmes détectés

    Returns:
        Dict avec score (0-5), raison détaillée, et action suggérée.
    """
    score = 0.0
    raisons: List[str] = []

    # Concaténer tout le contenu textuel du profil
    texte_complet = (profil.get("bio", "") + " " +
                     " ".join(r.get("description", "") for r in profil.get("repos", [])) + " " +
                     " ".join(profil.get("themes_detectes", [])) + " " +
                     " ".join(profil.get("langages", []))).lower()

    # 1. Score AGI (max 1.5, poids initial 0.3/motif)
    score_agi = 0.0
    for motif in MOTIFS_AGI:
        if motif in texte_complet:
            score_agi += 0.3
    score_agi = min(score_agi, 1.5)
    if score_agi > 0.5:
        raisons.append(f"affinité AGI: +{score_agi:.1f}")

    # 2. Score systèmes complexes (max 1.5, poids initial 0.25/motif)
    score_sc = 0.0
    for motif in MOTIFS_SYSTEMES_COMPLEXES:
        if motif in texte_complet:
            score_sc += 0.25
    score_sc = min(score_sc, 1.5)
    if score_sc > 0.3:
        raisons.append(f"systèmes complexes: +{score_sc:.1f}")

    # 3. Score tao-tech (max 2.5, poids initial 0.3/motif)
    score_tao = 0.0
    for motif in MOTIFS_TAO_TECH:
        if motif in texte_complet:
            score_tao += 0.3
    score_tao = min(score_tao, 2.5)
    if score_tao > 0.3:
        raisons.append(f"tao-tech: +{score_tao:.1f}")

    # 4. Bonus MTTV spécifique (max 1.0)
    score_mttv = 0.0
    for motif in MOTIFS_MTTV_SPECIFIQUES:
        if motif in texte_complet:
            score_mttv += 0.5
    score_mttv = min(score_mttv, 1.5)
    if score_mttv > 0:
        raisons.append(f"mots-clés MTTV: +{score_mttv:.1f}")

    # 5. Bonus stars >50 : si un repo taggé AGI/LLM/complex-systems/systèmes distribués
    #    a >50 stars, ajouter +1.0 au score (forfaitaire, pas par repo)
    bonus_stars = 0.0
    for repo in profil.get("repos", []):
        stars = repo.get("stars", 0)
        if stars > 50:
            desc = repo.get("description", "").lower()
            nom = repo.get("nom", "").lower()
            texte_repo = desc + " " + nom
            for motif in MOTIFS_STARS_BONUS:
                if motif in texte_repo:
                    bonus_stars = 1.0  # forfaitaire
                    break
        if bonus_stars >= 1.0:
            break
    if bonus_stars > 0:
        raisons.append(f"bonus stars >50: +{bonus_stars:.1f}")

    # Score total
    score = round(score_agi + score_sc + score_tao + score_mttv + bonus_stars, 2)
    score_normalise = min(round(score, 1), 5.0)

    # Action suggérée (seuil abaissé à 3.2)
    if score_normalise >= 3.2:
        action = "CONTACT_PRIORITAIRE — score ≥3.2, lancer sync et redaction"
    elif score_normalise >= 2.5:
        action = "SURVEILLANCE_ACTIVE — score modéré, ajouter au suivi hebdomadaire"
    elif score_normalise >= 1.0:
        action = "SURVEILLANCE_PASSIVE — score faible, observer sans contact"
    else:
        action = "AUCUNE — affinité insuffisante"

    return {
        "score": score_normalise,
        "score_details": {
            "agi": round(score_agi, 2),
            "systemes_complexes": round(score_sc, 2),
            "tao_tech": round(score_tao, 2),
            "mttv_specifique": round(score_mttv, 2),
        },
        "raison": "; ".join(raisons) if raisons else "aucune affinité détectée",
        "action": action,
        "profil_id": profil.get("id", "?"),
        "pseudo": profil.get("pseudo", "?"),
        "plateforme": profil.get("plateforme", "?"),
    }


def handle_cron_trigger(event: Event) -> None:
    """Déclenché par cron 1h — analyse les profils."""
    logger.info("=== Cycle veille: déclenché par cron 1h ===")
    bus = get_bus()

    for profil in CANDIDAT_PROFILS:
        resultat = calculer_score_affinite(profil)
        logger.info(
            f"Profil {resultat['profil_id']}: "
            f"score={resultat['score']}/5 — {resultat['action']}"
        )

        # Publier l'événement veille.new
        event = Event(
            event_type="veille.new",
            payload={
                "score": resultat["score"],
                "score_details": resultat["score_details"],
                "raison": resultat["raison"],
                "action": resultat["action"],
                "profil_id": resultat["profil_id"],
                "pseudo": resultat["pseudo"],
                "plateforme": resultat["plateforme"],
            },
            source="agent-veille",
            auto_publish=False,
        )
        bus.publish(event)


def handle_webhook_push(event: Event) -> None:
    """Déclenché par webhook GitHub/Gitee push."""
    payload = event.payload
    repo = payload.get("repository", "?")
    logger.info(f"=== Webhook push reçu: {repo} ===")
    handle_cron_trigger(event)  # Réanalyse les profils


def enregistrer_agent_veille(bus: EventBus) -> None:
    """Enregistre les écouteurs de l'agent veille sur le bus."""
    bus.on("cron.1h", handle_cron_trigger)
    bus.on("webhook.github.push", handle_webhook_push)
    bus.on("webhook.gitee.push", handle_webhook_push)
    logger.info("Agent veille enregistré sur le bus")


def executer_cycle_veille(bus: EventBus) -> List[Dict[str, Any]]:
    """Exécute un cycle de veille complet et retourne les résultats."""
    results = []
    for profil in CANDIDAT_PROFILS:
        resultat = calculer_score_affinite(profil)
        results.append(resultat)

        event = Event(
            event_type="veille.new",
            payload={
                "score": resultat["score"],
                "score_details": resultat["score_details"],
                "raison": resultat["raison"],
                "action": resultat["action"],
                "profil_id": resultat["profil_id"],
                "pseudo": resultat["pseudo"],
                "plateforme": resultat["plateforme"],
            },
            source="agent-veille",
            auto_publish=False,
        )
        bus.publish(event)

    return results
