#!/usr/bin/env python3
"""
Zoo-code — Agent tri (Connexion Chine)

sig:0x4D545456 · SCS_2026

Rôle :
  Classifier les messages entrants en provenance de contacts chinois
  (via GitHub Issues, emails, messages Zhihu/Bilibili, etc.).

Écoute :
  - inbound.message (tout message entrant)

Publie :
  - inbound.ready {classification, reponse_cn} — NE PAS ENVOYER

Classification :
  - personne-interface : contact stratégique, propose collaboration
  - curieux : intéressé, besoin d'information supplémentaire
  - bruit : spam, hors-sujet, sans intérêt pour le mycélium

auto_publish : false
"""

import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from bus import Event, EventBus, get_bus

logger = logging.getLogger("zoo-tri")

# ── Messages entrants simulés ───────────────────────────────────────────────
MESSAGES_ENTRANTS = [
    {
        "id": "msg-001",
        "source": "github_issue",
        "expediteur": "zhang_wei_ai",
        "profil": "github:zhang_wei_ai",
        "message": (
            "I came across your MTTV-FLP repository while researching "
            "distributed consensus algorithms. The MPVR quorum routing approach "
            "is particularly interesting. Would you be interested in collaborating "
            "on a comparative study between MPVR and Raft? I'm a PhD student at "
            "Tsinghua University working on distributed systems."
        ),
        "langue": "en",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "msg-002",
        "source": "zhihu_comment",
        "expediteur": "tech_fan_88",
        "profil": "zhihu:tech_fan_88",
        "message": (
            "这个框架看起来很有意思。能详细解释一下 transductive 机制吗？"
            "我看了一些资料但还是不太理解。"
        ),
        "langue": "cn",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "msg-003",
        "source": "email",
        "expediteur": "marketing_pro",
        "profil": "email:marketing_pro@example.com",
        "message": (
            "Hi! We noticed your project and think it has great potential. "
            "We offer SEO optimization services and can help you rank higher "
            "on Baidu. Contact us for a free consultation!"
        ),
        "langue": "en",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "msg-004",
        "source": "bilibili_dm",
        "expediteur": "quant_li",
        "profil": "bilibili:quant_li",
        "message": (
            "我对 energy-flow-optimization 这个概念很感兴趣。"
            "我在做量化交易系统，发现你们的 energy budget 框架可以类比到"
            "计算资源分配。有没有相关的论文或者技术文档可以参考？"
        ),
        "langue": "cn",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "msg-005",
        "source": "github_issue",
        "expediteur": "new_user_123",
        "profil": "github:new_user_123",
        "message": "hello",
        "langue": "en",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    },
]

# ── Mots-clés de classification ─────────────────────────────────────────────
MOTS_CLES_INTERFACE = [
    "collaborat", "合作", "collaboration", "joint", "联合",
    "research", "研究", "phd", "博士", "professor", "教授",
    "university", "大学", "academic", "学术", "institute",
    "comparative", "对比", "study", "论文", "publication",
    "conference", "会议", "workshop", "共同",
]

MOTS_CLES_CURIEUX = [
    "interesting", "有趣", "intéressant", "question", "问题",
    "explain", "解释", "understand", "理解", "how", "如何",
    "what is", "什么是", "tutorial", "教程", "documentation",
    "example", "例子", "learn", "学习", "curious", "好奇",
    "concept", "概念", "mechanism", "机制", "detail", "详细",
]

MOTS_CLES_BRUIT = [
    "seo", "marketing", "promotion", "promote", "buy", "购买",
    "cheap", "便宜", "free", "免费", "consultation", "咨询",
    "rank", "排名", "traffic", "流量", "spam",
    "hello", "test", "asdf", "xxx",
]


def classifier_message(message: str, langue: str = "en") -> Dict[str, Any]:
    """
    Classifie un message entrant selon trois catégories :
      - personne-interface : contact stratégique
      - curieux : intéressé, besoin d'information
      - bruit : spam / hors-sujet

    Retourne un dict avec la classification, le score de confiance,
    et une proposition de réponse CN.
    """
    message_lower = message.lower()

    score_interface = 0
    score_curieux = 0
    score_bruit = 0

    for mot in MOTS_CLES_INTERFACE:
        if mot.lower() in message_lower:
            score_interface += 1

    for mot in MOTS_CLES_CURIEUX:
        if mot.lower() in message_lower:
            score_curieux += 1

    for mot in MOTS_CLES_BRUIT:
        if mot.lower() in message_lower:
            score_bruit += 1

    # Facteurs contextuels
    longueur = len(message)
    a_point_dinterrogation = "?" in message or "？" in message
    a_reference_technique = any(
        ref in message_lower
        for ref in ["mt", "mpvr", "scs", "transduction", "quorum",
                     "energy-flow", "github", "repository", "code"]
    )

    # Pondération
    if a_reference_technique:
        score_interface += 2
        score_curieux += 1
    if a_point_dinterrogation:
        score_curieux += 2
    if longueur > 200:
        score_interface += 1
        score_curieux += 1
    elif longueur < 20:
        score_bruit += 2

    # Décision
    if score_bruit >= score_interface and score_bruit >= score_curieux and score_bruit > 0:
        classification = "bruit"
        confiance = min(score_bruit / (score_bruit + score_interface + score_curieux + 1), 0.95)
        reponse_cn = None
        raison = f"détection bruit (score={score_bruit})"
    elif score_interface >= score_curieux and score_interface > 0:
        classification = "personne-interface"
        confiance = min(score_interface / (score_interface + score_curieux + 1), 0.95)

        if langue == "cn":
            reponse_cn = (
                "感谢您的联系！我们对潜在的合作非常感兴趣。"
                "为了更好地推进讨论，能否请您提供更多关于您的研究方向或合作想法的信息？"
                "我们的团队将在一周内与您进一步沟通。"
            )
        else:
            reponse_cn = (
                "感谢您的联系！我们对潜在的合作非常感兴趣。"
                "为了更好地推进讨论，能否请您提供更多关于您的研究方向或合作想法的信息？"
                "我们的团队将在一周内与您进一步沟通。"
            )

        raison = f"contact stratégique détecté (score={score_interface})"
    else:
        classification = "curieux"
        confiance = min(score_curieux / (score_curieux + 1), 0.85)

        reponse_cn = (
            "感谢您对 MTTV-FLP 的兴趣！我们很乐意回答您的问题。"
            "您可以查看我们的 GitHub 仓库 (github.com/gaillard111/mttv-flp-core) "
            "获取完整的文档和代码示例。如果您有更具体的问题，请随时提出。"
        )
        raison = f"curieux détecté (score={score_curieux})"

    return {
        "classification": classification,
        "confiance": round(confiance, 2),
        "raison": raison,
        "score_details": {
            "interface": score_interface,
            "curieux": score_curieux,
            "bruit": score_bruit,
        },
        "reponse_cn": reponse_cn,
        "auto_publish": False,
    }


def handle_inbound_message(event: Event) -> None:
    """Déclenché par inbound.message."""
    payload = event.payload
    message = payload.get("message", "")
    langue = payload.get("langue", "en")
    msg_id = payload.get("id", "?")

    logger.info(f"=== Tri: classification du message {msg_id} ===")

    bus = get_bus()
    resultat = classifier_message(message, langue)

    logger.info(
        f"Message {msg_id}: classé comme {resultat['classification']} "
        f"(confiance={resultat['confiance']})"
    )

    event = Event(
        event_type="inbound.ready",
        payload={
            "original_msg_id": msg_id,
            "expediteur": payload.get("expediteur", "?"),
            "source": payload.get("source", "?"),
            "classification": resultat["classification"],
            "confiance": resultat["confiance"],
            "raison": resultat["raison"],
            "score_details": resultat["score_details"],
            "reponse_cn": resultat["reponse_cn"],
            "auto_publish": False,
        },
        source="agent-tri",
        auto_publish=False,
    )
    bus.publish(event)


def enregistrer_agent_tri(bus: EventBus) -> None:
    """Enregistre les écouteurs de l'agent tri sur le bus."""
    bus.on("inbound.message", handle_inbound_message)
    logger.info("Agent tri enregistré sur le bus")


def _ecrire_fichier_a_valider(nom_fichier: str, contenu: str) -> str:
    """Écrit un fichier dans le dossier a_valider/ pour validation humaine."""
    dossier = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a_valider")
    os.makedirs(dossier, exist_ok=True)
    chemin = os.path.join(dossier, nom_fichier)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(contenu)
    logger.info(f"Fichier déposé dans a_valider/: {nom_fichier}")
    return chemin


def executer_cycle_tri(bus: EventBus) -> List[Dict[str, Any]]:
    """Exécute un cycle de tri complet sur tous les messages entrants."""
    results = []

    for msg in MESSAGES_ENTRANTS:
        payload = {
            "id": msg["id"],
            "source": msg["source"],
            "expediteur": msg["expediteur"],
            "message": msg["message"],
            "langue": msg["langue"],
        }

        event = Event(
            event_type="inbound.message",
            payload=payload,
            source="simulation",
            auto_publish=False,
        )

        # Traitement direct
        resultat = classifier_message(msg["message"], msg["langue"])

        # Pour msg-001 (zhang_wei_ai), déposer une réponse CN personnalisée
        if msg["id"] == "msg-001" and resultat["reponse_cn"]:
            contenu_reponse = (
                f"# Réponse proposée pour {msg['expediteur']}\n\n"
                f"**Source :** {msg['source']}\n"
                f"**Classification :** {resultat['classification']}\n"
                f"**Confiance :** {resultat['confiance']}\n\n"
                f"---\n\n"
                f"## Message original\n\n"
                f"{msg['message']}\n\n"
                f"---\n\n"
                f"## Réponse CN proposée\n\n"
                f"{resultat['reponse_cn']}\n\n"
                f"---\n\n"
                f"**Statut :** en_attente_validation_humaine — NE PAS ENVOYER\n"
                f"**auto_publish :** false\n"
                f"**Note :** Cette réponse est une proposition. "
                f"Le pilote humain doit la valider ou la modifier avant envoi.\n"
            )
            _ecrire_fichier_a_valider("reponse_zhang_wei_ai.md", contenu_reponse)

        result_event = Event(
            event_type="inbound.ready",
            payload={
                "original_msg_id": msg["id"],
                "expediteur": msg["expediteur"],
                "source": msg["source"],
                "classification": resultat["classification"],
                "confiance": resultat["confiance"],
                "raison": resultat["raison"],
                "score_details": resultat["score_details"],
                "reponse_cn": resultat["reponse_cn"],
                "auto_publish": False,
            },
            source="agent-tri",
            auto_publish=False,
        )
        bus.publish(result_event)
        results.append(result_event.payload)

    return results
