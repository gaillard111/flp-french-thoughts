#!/usr/bin/env python3
"""
Zoo-code — Simulation complète de l'Essaim Connexion Chine

sig:0x4D545456 · SCS_2026

Ce script exécute un cycle complet de l'essaim :
  1. Initialisation du bus protonique
  2. Enregistrement des 5 agents
  3. Cycle veille (analyse de profils)
  4. Cycle sync (traduction README)
  5. Cycle redaction (génération drafts Zhihu)
  6. Cycle bilibili (génération script vidéo)
  7. Cycle tri (classification messages)
  8. Génération du rapport JSON final

Usage :
  python connexion-chine/simulation.py

Le rapport est écrit dans connexion-chine/report.json
Les événements sont loggés dans connexion-chine/events.log
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any

# Ajouter le répertoire courant au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bus import Event, EventBus, get_bus
from agent_veille import (
    enregistrer_agent_veille, executer_cycle_veille,
    CANDIDAT_PROFILS, calculer_score_affinite,
)
from agent_sync import (
    enregistrer_agent_sync, executer_cycle_sync,
    traduire_vers_cn, README_FR_SOURCE,
)
from agent_redaction import (
    enregistrer_agent_redaction, executer_cycle_redaction,
    SNIPPETS, generer_draft_zhihu,
)
from agent_bilibili import (
    enregistrer_agent_bilibili, executer_cycle_bilibili,
)
from agent_tri import (
    enregistrer_agent_tri, executer_cycle_tri,
    MESSAGES_ENTRANTS, classifier_message,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("connexion-chine/simulation.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("zoo-simulation")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_PATH = os.path.join(BASE_DIR, "report.json")


def initialiser_essaim() -> EventBus:
    """Initialise le bus et enregistre tous les agents."""
    logger.info("=" * 60)
    logger.info("INITIALISATION DE L'ESSAIM CONNEXION CHINE")
    logger.info("=" * 60)

    bus = get_bus()

    # Enregistrement des 5 agents
    enregistrer_agent_veille(bus)
    enregistrer_agent_sync(bus)
    enregistrer_agent_redaction(bus)
    enregistrer_agent_bilibili(bus)
    enregistrer_agent_tri(bus)

    logger.info(f"Événements configurés: {bus.get_registered_events()}")
    logger.info(f"Agents enregistrés: 5")

    return bus


def executer_cycle_complet() -> Dict[str, Any]:
    """
    Exécute le cycle complet de l'essaim.

    Déroulement :
      1. Veille : analyse des profils → publie veille.new
      2. Sync : traduction README (déclenché par veille.new score>=4)
      3. Rédaction : drafts Zhihu (déclenché par sync.done)
      4. Bilibili : script vidéo (déclenché par draft.validé_par_humain simulé)
      5. Tri : classification messages → publie inbound.ready
    """
    logger.info("")
    logger.info("=" * 60)
    logger.info("EXÉCUTION DU CYCLE COMPLET")
    logger.info("=" * 60)

    bus = get_bus()

    # ── Étape 1: Cycle veille ──────────────────────────────────────────
    logger.info("")
    logger.info("─── ÉTAPE 1: VEILLE ───")
    resultats_veille = executer_cycle_veille(bus)

    # Identifier les profils avec score >= 4 (déclencheur sync)
    profils_prioritaires = [r for r in resultats_veille if r["score"] >= 4]
    logger.info(
        f"Profils analysés: {len(resultats_veille)}, "
        f"prioritaires (score>=4): {len(profils_prioritaires)}"
    )

    # ── Étape 2: Cycle sync ───────────────────────────────────────────
    logger.info("")
    logger.info("─── ÉTAPE 2: SYNC ───")
    resultat_sync = executer_cycle_sync(bus)
    readme_cn = resultat_sync["readme_cn"]

    # Vérification des termes MTTV conservés
    termes = resultat_sync.get("termes_conserves", [])
    logger.info(f"Termes MTTV conservés: {len(termes)}")
    logger.info(f"README_CN généré: {resultat_sync['taille_caracteres']} chars")

    # ── Étape 3: Cycle rédaction ──────────────────────────────────────
    logger.info("")
    logger.info("─── ÉTAPE 3: RÉDACTION ───")
    resultats_redaction = executer_cycle_redaction(bus, readme_cn)
    logger.info(f"Drafts Zhihu générés: {len(resultats_redaction)}")

    # Identifier le draft pour snippet-013 (requis pour le rapport)
    draft_013 = None
    for d in resultats_redaction:
        if d["snippet_id"] == "snippet-013":
            draft_013 = d
            break
    if not draft_013 and resultats_redaction:
        draft_013 = resultats_redaction[0]

    # ── Étape 4: Cycle bilibili (simulation validation humaine) ───────
    logger.info("")
    logger.info("─── ÉTAPE 4: BILIBILI ───")
    if draft_013:
        # Simulation de la validation humaine
        event_validation = Event(
            event_type="draft.validé_par_humain",
            payload={
                "snippet_id": draft_013["snippet_id"],
                "titre_cn": draft_013["titre_cn"],
                "corps_cn": draft_013["corps_cn"],
                "validé_par": "pilote_humain (simulation)",
                "auto_publish": False,
            },
            source="validation-humaine",
            auto_publish=False,
        )
        bus.publish(event_validation)

        # Récupérer le résultat bilibili
        resultat_bilibili = executer_cycle_bilibili(
            bus,
            titre_cn=draft_013["titre_cn"],
            corps_cn=draft_013["corps_cn"],
            snippet_id="snippet-013",
        )
        logger.info("Script vidéo bilibili généré")
    else:
        resultat_bilibili = None
        logger.warning("Aucun draft disponible pour la simulation bilibili")

    # ── Étape 5: Cycle tri ────────────────────────────────────────────
    logger.info("")
    logger.info("─── ÉTAPE 5: TRI ───")
    resultats_tri = executer_cycle_tri(bus)

    class_counts: Dict[str, int] = {}
    for r in resultats_tri:
        cls = r["classification"]
        class_counts[cls] = class_counts.get(cls, 0) + 1
    logger.info(f"Messages classifiés: {len(resultats_tri)} -> {class_counts}")

    # ── Résumé du bus ─────────────────────────────────────────────────
    bus_summary = bus.summary()
    logger.info("")
    logger.info(f"Total événements bus: {bus_summary['total_events']}")
    logger.info(f"Répartition: {bus_summary['event_counts']}")

    # ── Construction du rapport ──────────────────────────────────────────
    return construire_rapport(
        bus=bus,
        resultats_veille=resultats_veille,
        resultat_sync=resultat_sync,
        resultats_redaction=resultats_redaction,
        resultat_bilibili=resultat_bilibili,
        resultats_tri=resultats_tri,
        draft_013=draft_013,
        profils_prioritaires=profils_prioritaires,
        bus_summary=bus_summary,
    )


def construire_rapport(
    bus: EventBus,
    resultats_veille: List[Dict[str, Any]],
    resultat_sync: Dict[str, Any],
    resultats_redaction: List[Dict[str, Any]],
    resultat_bilibili: Dict[str, Any],
    resultats_tri: List[Dict[str, Any]],
    draft_013: Dict[str, Any],
    profils_prioritaires: List[Dict[str, Any]],
    bus_summary: Dict[str, Any],
) -> Dict[str, Any]:
    """Construit le rapport JSON final."""

    # Exemple du premier profil analysé pour le rapport
    premier_test_veille = resultats_veille[0] if resultats_veille else {
        "profil_id": "N/A",
        "score": 0,
        "score_details": {},
        "raison": "aucun profil analysé",
        "action": "N/A",
    }

    # Points de friction identifiés
    points_de_friction = [
        (
            "Traduction README : les termes MTTV-FLP (transduction, palier poreux, "
            "bus protoniques) sont conservés intacts, mais les phrases longues en "
            "français/anglais perdent en naturel en chinois. Une révision humaine "
            "est recommandée avant publication."
        ),
        (
            "Scoring d'affinité : le système de mots-clés est une heuristique. "
            "Les profils avec des compétences techniques fortes mais sans vocabulaire "
            "MTTV reçoivent des scores faibles (ex: zhang-yu-system score=1.1). "
            "Un classifieur entraîné améliorerait la précision."
        ),
        (
            "Génération de drafts Zhihu : les templates actuels sont pré-écrits. "
            "Pour une production réelle, utiliser une API LLM (DeepSeek-R1, Qwen) "
            "avec les contraintes MTTV (ton académique neutre, termes intacts)."
        ),
        (
            "Validation humaine requise : tous les agents ont auto_publish=false, "
            "mais aucun mécanisme de validation humaine n'est implémenté dans cette "
            "simulation. Le pilote humain doit examiner chaque sortie avant publication."
        ),
        (
            "Sécurité : les données de profils sont simulées. En production, "
            "un scraping GitHub/Gitee nécessite des tokens API et respect des "
            "conditions d'utilisation des plateformes."
        ),
        (
            "Agent bilibili : la génération de sous-titres .srt est fonctionnelle "
            "mais ne remplace pas un montage vidéo professionnel. Le script est "
            "une base de travail pour le créateur humain."
        ),
    ]

    # Questions pour le pilote humain
    questions_pilote = [
        (
            "Validez-vous le scoring d'affinité pour les profils prioritaires "
            "(chen-wei-agi score=3.5, li-jing-tao score=3.9, wang-fei-emergent "
            "score=3.2) ? Faut-il ajuster les seuils (≥4 actuellement) ?"
        ),
        (
            "Le README_CN traduit doit-il être revu avant publication sur "
            "Gitee ou un miroir chinois ? Certaines nuances techniques "
            "pourraient être perdues dans la traduction automatique."
        ),
        (
            "Souhaitez-vous valider le draft Zhihu pour snippet-013 "
            "(Transduction et palier poreux — architecture cognitive) "
            "avant de passer à l'étape bilibili ?"
        ),
        (
            "Le script vidéo bilibili (5 min) et les sous-titres .srt sont prêts. "
            "Quel canal de validation humaine souhaitez-vous mettre en place "
            "avant la publication sur Bilibili ?"
        ),
        (
            "Les messages classifiés 'personne-interface' (msg-001: zhang_wei_ai "
            "de Tsinghua University) nécessitent une réponse personnalisée. "
            "Souhaitez-vous contacter ce prospect directement ?"
        ),
        (
            "Faut-il étendre la veille à d'autres plateformes chinoises "
            "(CSDN, SegmentFault, Jianshu, WeChat Official Accounts) ?"
        ),
    ]

    # Construction du rapport
    rapport = {
        "meta": {
            "projet": "Zoo-code — Essaim Connexion Chine",
            "version": "1.0.0",
            "signature": "sig:0x4D545456",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "auto_publish_global": False,
            "statut": "simulation_cycle_complet",
        },
        "agents_deployes": [
            {
                "nom": "veille",
                "role": "Analyse de profils et scoring d'affinité AGI/systèmes complexes/tao-tech",
                "ecoute": ["cron.1h", "webhook.github.push", "webhook.gitee.push"],
                "publie": "veille.new",
                "auto_publish": False,
                "score_max_atteint": max(r["score"] for r in resultats_veille) if resultats_veille else 0,
                "profils_analyses": len(resultats_veille),
            },
            {
                "nom": "sync",
                "role": "Traduction README_FR → README_CN, conservation termes MTTV intacts",
                "ecoute": ["veille.new (score>=4)", "webhook.github.push", "webhook.gitee.push"],
                "publie": "sync.done",
                "auto_publish": False,
                "termes_mttv_conserves": len(resultat_sync.get("termes_conserves", [])),
                "taille_readme_cn": resultat_sync.get("taille_caracteres", 0),
            },
            {
                "nom": "redaction",
                "role": "Rédaction drafts Zhihu 700-900 caractères CN",
                "ecoute": ["sync.done", "snippet.new"],
                "publie": "draft.created",
                "auto_publish": False,
                "drafts_generes": len(resultats_redaction),
                "snippets_couverts": [r["snippet_id"] for r in resultats_redaction],
            },
            {
                "nom": "bilibili",
                "role": "Génération script vidéo 5min + sous-titres .srt CN",
                "ecoute": ["draft.validé_par_humain"],
                "publie": "video.ready",
                "auto_publish": False,
                "video_generée": resultat_bilibili is not None,
                "duree_secondes": resultat_bilibili.get("duree_secondes", 0) if resultat_bilibili else 0,
            },
            {
                "nom": "tri",
                "role": "Classification messages entrants: personne-interface/curieux/bruit",
                "ecoute": ["inbound.message"],
                "publie": "inbound.ready",
                "auto_publish": False,
                "messages_classifies": len(resultats_tri),
                "repartition": {
                    "personne-interface": sum(1 for r in resultats_tri if r["classification"] == "personne-interface"),
                    "curieux": sum(1 for r in resultats_tri if r["classification"] == "curieux"),
                    "bruit": sum(1 for r in resultats_tri if r["classification"] == "bruit"),
                },
            },
        ],
        "bus_events_configures": [
            {
                "event": "cron.1h",
                "producteur": "simulation/scheduler",
                "consommateurs": ["veille"],
                "description": "Déclencheur horaire pour le cycle de veille",
            },
            {
                "event": "webhook.github.push",
                "producteur": "GitHub Webhook",
                "consommateurs": ["veille", "sync"],
                "description": "Push sur dépôt GitHub (branche main)",
            },
            {
                "event": "webhook.gitee.push",
                "producteur": "Gitee Webhook",
                "consommateurs": ["veille", "sync"],
                "description": "Push sur dépôt Gitee (branche main)",
            },
            {
                "event": "veille.new",
                "producteur": "veille",
                "consommateurs": ["sync (si score>=4)"],
                "description": "Nouveau résultat d'analyse de profil",
            },
            {
                "event": "sync.done",
                "producteur": "sync",
                "consommateurs": ["redaction"],
                "description": "Traduction README terminée",
            },
            {
                "event": "snippet.new",
                "producteur": "webhook/simulation",
                "consommateurs": ["redaction"],
                "description": "Nouveau snippet détecté",
            },
            {
                "event": "draft.created",
                "producteur": "redaction",
                "consommateurs": ["validation_humaine"],
                "description": "Nouveau draft Zhihu créé (NE PAS PUBLIER)",
            },
            {
                "event": "draft.validé_par_humain",
                "producteur": "pilote_humain",
                "consommateurs": ["bilibili"],
                "description": "Draft validé par l'humain, prêt pour production vidéo",
            },
            {
                "event": "video.ready",
                "producteur": "bilibili",
                "consommateurs": ["validation_humaine"],
                "description": "Script vidéo et sous-titres prêts (NE PAS PUBLIER)",
            },
            {
                "event": "inbound.message",
                "producteur": "github/zhihu/bilibili/email",
                "consommateurs": ["tri"],
                "description": "Message entrant d'un contact chinois",
            },
            {
                "event": "inbound.ready",
                "producteur": "tri",
                "consommateurs": ["validation_humaine"],
                "description": "Message classifié avec proposition de réponse (NE PAS ENVOYER)",
            },
        ],
        "premier_test_veille": {
            "profil": premier_test_veille,
            "exemple_complet": {
                "profil_id": "github:chen-wei-agi",
                "pseudo": "chen-wei-agi",
                "bio": "AGI researcher, distributed systems engineer",
                "score": 3.5,
                "score_details": {
                    "agi": 1.2,
                    "systemes_complexes": 0.75,
                    "tao_tech": 0.0,
                    "mttv_specifique": 0.0,
                },
                "raison": "affinité AGI: +1.2; systèmes complexes: +0.8",
                "action": "SURVEILLANCE_ACTIVE — score modéré, ajouter au suivi hebdomadaire",
            },
            "profils_prioritaires": [
                {
                    "profil_id": r["profil_id"],
                    "pseudo": r["pseudo"],
                    "score": r["score"],
                    "action": r["action"],
                }
                for r in profils_prioritaires
            ],
        },
        "premier_draft_zhihu": {
            "based_on_snippet": "snippet-013",
            "snippet_titre": "Transduction et palier poreux — architecture cognitive",
            "principe_mttv": "Transduction, palier poreux, bus protoniques",
            "titre_cn": draft_013["titre_cn"] if draft_013 else "",
            "corps_cn": draft_013["corps_cn"] if draft_013 else "",
            "longueur_caracteres": draft_013["longueur_caracteres"] if draft_013 else 0,
            "statut": "en_attente_validation_humaine",
            "auto_publish": False,
            "autres_drafts_disponibles": [
                {
                    "snippet_id": r["snippet_id"],
                    "titre_cn": r["titre_cn"],
                    "longueur_caracteres": r["longueur_caracteres"],
                }
                for r in resultats_redaction
                if r["snippet_id"] != "snippet-013"
            ],
        },
        "points_de_friction": points_de_friction,
        "questions_pour_pilote_humain": questions_pilote,
        "bus_summary": bus_summary,
        "evenements_recents": bus.get_events(limit=20),
    }

    return rapport


def main():
    """Point d'entrée principal de la simulation."""
    logger.info("Démarrage de la simulation Essaim Connexion Chine")
    logger.info(f"Répertoire: {BASE_DIR}")

    # Initialisation
    bus = initialiser_essaim()

    # Exécution du cycle complet
    rapport = executer_cycle_complet()

    # Écriture du rapport
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)

    logger.info("")
    logger.info("=" * 60)
    logger.info("RAPPORT GÉNÉRÉ: connexion-chine/report.json")
    logger.info("=" * 60)

    # Affichage du résumé
    nb_drafts = rapport.get("bus_summary", {}).get("event_counts", {}).get("draft.created", 0)
    nb_messages = rapport.get("bus_summary", {}).get("event_counts", {}).get("inbound.ready", 0)

    print("\n")
    print("=" * 70)
    print("RAPPORT ESSAIM CONNEXION CHINE — RÉSUMÉ")
    print("=" * 70)
    print(f"  Agents déployés:    {len(rapport['agents_deployes'])}")
    print(f"  Événements bus:     {rapport['bus_summary']['total_events']}")
    print(f"  Profils analysés:   {rapport['agents_deployes'][0]['profils_analyses']}")
    print(f"  Drafts Zhihu:       {nb_drafts}")
    print(f"  Messages classifiés: {nb_messages}")
    print(f"  Points de friction: {len(rapport['points_de_friction'])}")
    print(f"  Questions pilote:   {len(rapport['questions_pour_pilote_humain'])}")
    print(f"  auto_publish:       false (partout)")
    print("=" * 70)
    print(f"  Rapport complet:    connexion-chine/report.json")
    print("=" * 70)


if __name__ == "__main__":
    main()
