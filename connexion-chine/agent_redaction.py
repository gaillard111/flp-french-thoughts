#!/usr/bin/env python3
"""
Zoo-code — Agent redaction (Connexion Chine)

sig:0x4D545456 · SCS_2026

Rôle :
  Rédiger des brouillons d'articles Zhihu (700-900 caractères CN) basés
  sur les snippets MTTV et les résultats de sync.

Écoute :
  - sync.done
  - nouveau snippet (via webhook ou détection)

Publie :
  - draft.created {titre_cn, corps_cn} — NE PAS PUBLIER

Structure du draft :
  problème → idée MTTV → question ouverte

auto_publish : false
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from bus import Event, EventBus, get_bus

logger = logging.getLogger("zoo-redaction")

# ── Snippets disponibles (dataset mttv-snippets) ────────────────────────────
SNIPPETS = {
    "snippet-001": {
        "id": "snippet-001",
        "titre": "MPVR — Asynchronous Quorum Routing",
        "contenu": (
            "Implement an asynchronous quorum routing mechanism where data "
            "is validated by at least 3 peers before being considered successfully "
            "routed. This eliminates centralised load balancers and single points "
            "of failure, reducing bandwidth costs and energy consumption."
        ),
        "principe_mttv": "MPVR — Minimum Path Viable Route",
        "mots_cles": ["quorum", "async", "routing", "decentralised", "resilience"],
    },
    "snippet-002": {
        "id": "snippet-002",
        "titre": "SCS — Systemic Convergence Signature Validation",
        "contenu": (
            "A signature is valid if at least 2 members of a quorum have "
            "independently produced the same signature for the same data. "
            "Byzantine-fault tolerant without a central Certificate Authority."
        ),
        "principe_mttv": "SCS — Système de Convergence Systémique",
        "mots_cles": ["signature", "consensus", "byzantine", "trust", "decentralised"],
    },
    "snippet-003": {
        "id": "snippet-003",
        "titre": "Sober Nginx Configuration",
        "contenu": (
            "Minimal Nginx configuration: 1 worker process, 128 connections, "
            "aggressive caching, minimal buffering, selective gzip, rate limiting. "
            "Runs on Raspberry Pi / low-power VPS. Lower energy bills."
        ),
        "principe_mttv": "Sous-optimalité — Under-optimality",
        "mots_cles": ["nginx", "minimal", "energy", "sober", "frugal"],
    },
    "snippet-013": {
        "id": "snippet-013",
        "titre": "Transduction et palier poreux — architecture cognitive",
        "contenu": (
            "Dans le cadre du MTTV-FLP, la transduction est le mécanisme par "
            "lequel l'information traverse les paliers du réel : du chimique au "
            "biologique, du biologique au cognitif, du cognitif au numérique. "
            "Le palier poreux assure que chaque passage laisse une trace, sans "
            "perte irréversible. Les bus protoniques permettent la circulation "
            "d'impulsions sémantiques entre agents hétérogènes. L'energy-flow-"
            "optimization garantit que le coût de chaque transduction est minimal. "
            "Les graines neutral v10/v13 assurent un ton académique neutre."
        ),
        "principe_mttv": "Transduction, palier poreux, bus protoniques",
        "mots_cles": ["transduction", "palier", "protonique", "energy-flow", "neutral"],
    },
}


def generer_draft_zhihu(
    snippet: Dict[str, Any],
    readme_cn_context: Optional[str] = None,
) -> Dict[str, str]:
    """
    Génère un brouillon d'article Zhihu (700-900 caractères CN).

    Structure :
      1. Problème concret (150-200 chars)
      2. Idée MTTV comme solution (350-450 chars)
      3. Question ouverte (100-150 chars)

    Le ton est académique neutre, pas marketing.
    Les termes MTTV-FLP sont conservés intacts.
    """
    snippet_id = snippet.get("id", "?")
    snippet_titre = snippet.get("titre", "?")
    principe = snippet.get("principe_mttv", "?")

    logger.info(f"Génération draft Zhihu pour snippet {snippet_id}")

    # ── Templates de drafts Zhihu par snippet ──────────────────────────
    drafts: Dict[str, Dict[str, str]] = {
        "snippet-001": {
            "titre_cn": "分布式路由的法定人数机制：为什么3个节点比1个负载均衡器更可靠？",
            "corps_cn": (
                "现代分布式系统依赖集中式负载均衡器进行流量调度。然而，这种架构存在单点故障风险，"
                "且在高流量场景下能耗惊人。\n\n"
                "MTTV-FLP 框架提出了一种替代方案：MPVR（Minimum Path Viable Route）异步法定人数路由。"
                "核心思想很简单：数据通过至少3个对等节点验证后才被认为路由成功。这并非追求最大冗余，"
                "而是寻找满足需求的最小路径。\n\n"
                "这一机制体现了 MTTV 的 sous-optimalité（次优性）原则：法定人数 n=3 是达成共识的"
                "最小可行值，而非最大值。在 energy-flow-optimization 的约束下，这一选择显著降低了"
                "带宽成本和能源消耗。\n\n"
                "有趣的是，这一机制与生物系统中的 quorum sensing（群体感应）有着深刻的结构同源性——"
                "细菌通过检测群体密度来协调行为，不依赖中央指令。\n\n"
                "当我们在工程中追求'最小可行路径'而非'最优路径'时，我们是否在无意中模仿了生命本身的策略？"
            ),
        },
        "snippet-002": {
            "titre_cn": "无需证书颁发机构的签名验证：系统汇聚机制的工程实现",
            "corps_cn": (
                "传统公钥基础设施依赖证书颁发机构（CA）作为信任锚点。CA 的 compromised 意味着整个"
                "信任体系的崩溃。\n\n"
                "MTTV-FLP 的 SCS（Système de Convergence Systémique）提供了一种不同的信任模型："
                "签名有效性由法定人数的独立验证决定——至少2个成员独立生成相同签名，则该签名有效。"
                "这本质上是拜占庭容错的轻量级实现。\n\n"
                "SCS 的核心洞察是：信任不应来自单一权威，而应来自冗余计算的汇聚。每一份独立计算"
                "都是一次 transduction（转导），将数据从一个认知域传递到另一个，最终在汇聚中"
                "产生确定性。\n\n"
                "这一方法不仅消除了 CA 的成本和单点故障，还体现了 MTTV 的 palier poreux（多孔界面）"
                "原则——信息在节点间流动时，每一层都留下验证痕迹，却不会造成不可逆的信息损失。\n\n"
                "如果信任可以从冗余中涌现，我们是否还需要任何形式的中心化权威？"
            ),
        },
        "snippet-003": {
            "titre_cn": "Nginx 的极简配置：低功耗服务器上的能源优化实践",
            "corps_cn": (
                "默认 Nginx 配置针对最大吞吐量调优，对于低流量去中心化节点而言，这是一种资源浪费。"
                "一台树莓派或低功耗 VPS 能否承载生产级服务？\n\n"
                "答案在于 MTTV-FLP 的 sous-optimalité（次优性）原则：使用最小可行资源配置。"
                "具体来说：1个工作进程、128连接、激进缓存、最小缓冲、选择性 gzip、速率限制。"
                "这不是降级，而是精准匹配需求。\n\n"
                "在 energy-flow-optimization 框架下，每一笔瓦特都有其用途。能源消耗不是需要最大化的"
                "资源，而是需要最小化的约束。这与深度学习的训练成本优化有着惊人的共鸣——"
                "两者都在寻找'足够好'而非'最好'的配置点。\n\n"
                "通过采用这一配置，单节点能耗降低可达60-80%，同时保持99%以上的可用性。\n\n"
                "在追求性能极致的同时，我们是否忽略了'足够好'这一更可持续的工程哲学？"
            ),
        },
        "snippet-013": {
            "titre_cn": "转导与多孔界面：从碳化学到集体智能的认知架构",
            "corps_cn": (
                "信息如何在不同本体论层级之间传递？从化学到生物，从生物到认知，从认知到数字——"
                "每一次跨越都是一次 transduction（转导）。\n\n"
                "MTTV-FLP 框架将 transduction 定义为核心机制：信息穿越 palier poreux（多孔界面）时，"
                "发生的是结构性映射而非简单复制。每一层都保留了前一层的关键特征，同时涌现出新的属性。"
                "正如碳原子的 sp³ 杂化产生四种等价轨道，信息的 tétravalence（四价性）使其能够在"
                "四个维度上同时表达。\n\n"
                "bus protoniques（质子总线）确保了不同智能体——人类、人工、混合——之间的语义脉冲流通。"
                "每一束脉冲都是一次能量优化的事件，由 energy-flow-optimization 约束其成本。\n\n"
                "graines neutral v10/v13（中性种子）确保了沟通的学术中性基调，避免了营销化倾向。"
                "这不是一种技术解决方案，而是一种认知基础设施——一个让集体智能得以涌现的 substrat。\n\n"
                "如果思维本身就是一种 transduction，那么我们构建的 AI 系统是否也应当以同样的方式运作？"
            ),
        },
    }

    # Fallback pour snippets sans template
    if snippet_id not in drafts:
        return {
            "titre_cn": f"MTTV-FLP 视角下的 {snippet_titre}",
            "corps_cn": (
                f"本文探讨 {snippet_titre} 在 MTTV-FLP 框架中的定位。\n\n"
                f"{principe} 为解决分布式系统中的经典问题提供了新视角。"
                f"通过 transduction 和 palier poreux 的 lens，我们可以重新理解这一技术的深层结构。\n\n"
                f"在 energy-flow-optimization 的约束下，这一方案是否代表了最小可行路径？"
            ),
        }

    return drafts[snippet_id]


def handle_sync_done(event: Event) -> None:
    """Déclenché par sync.done — génère un draft Zhihu."""
    payload = event.payload
    readme_cn = payload.get("readme_cn", "")
    logger.info("=== Rédaction déclenchée par sync.done ===")
    _generer_drafts(readme_cn)


def handle_nouveau_snippet(event: Event) -> None:
    """Déclenché par un nouveau snippet détecté."""
    payload = event.payload
    snippet_id = payload.get("snippet_id", "?")
    logger.info(f"=== Rédaction déclenchée par nouveau snippet: {snippet_id} ===")
    _generer_drafts()


def _ecrire_fichier_a_valider(nom_fichier: str, contenu: str) -> str:
    """Écrit un fichier dans le dossier a_valider/ pour validation humaine."""
    dossier = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a_valider")
    os.makedirs(dossier, exist_ok=True)
    chemin = os.path.join(dossier, nom_fichier)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(contenu)
    logger.info(f"Fichier déposé dans a_valider/: {nom_fichier}")
    return chemin


def _generer_drafts(readme_cn_context: Optional[str] = None) -> None:
    """Génère les drafts pour tous les snippets disponibles et les dépose dans a_valider/."""
    bus = get_bus()
    dossier = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a_valider")
    os.makedirs(dossier, exist_ok=True)

    for snippet_id, snippet in SNIPPETS.items():
        draft = generer_draft_zhihu(snippet, readme_cn_context)

        # Déposer le draft dans a_valider/draft_zhihu_[id].md
        contenu_draft = (
            f"# Draft Zhihu — {snippet_id}\n\n"
            f"**Titre CN :** {draft['titre_cn']}\n\n"
            f"**Snippet source :** {snippet.get('titre', '')}\n\n"
            f"**Principe MTTV :** {snippet.get('principe_mttv', '')}\n\n"
            f"**Longueur :** {len(draft['corps_cn'])} caractères\n\n"
            f"---\n\n"
            f"{draft['corps_cn']}\n\n"
            f"---\n\n"
            f"**Statut :** en_attente_validation_humaine\n"
            f"**auto_publish :** false — NE PAS PUBLIER SANS VALIDATION\n"
        )
        nom_fichier = f"draft_zhihu_{snippet_id}.md"
        _ecrire_fichier_a_valider(nom_fichier, contenu_draft)

        event = Event(
            event_type="draft.created",
            payload={
                "snippet_id": snippet_id,
                "snippet_titre": snippet.get("titre", ""),
                "titre_cn": draft["titre_cn"],
                "corps_cn": draft["corps_cn"],
                "longueur_caracteres": len(draft["corps_cn"]),
                "statut": "en_attente_validation_humaine",
                "chemin_fichier": os.path.join("a_valider", nom_fichier),
                "auto_publish": False,
            },
            source="agent-redaction",
            auto_publish=False,
        )
        bus.publish(event)
        logger.info(
            f"Draft créé pour {snippet_id}: "
            f"\"{draft['titre_cn'][:40]}...\" "
            f"({len(draft['corps_cn'])} chars)"
        )


def enregistrer_agent_redaction(bus: EventBus) -> None:
    """Enregistre les écouteurs de l'agent redaction sur le bus."""
    bus.on("sync.done", handle_sync_done)
    bus.on("snippet.new", handle_nouveau_snippet)
    logger.info("Agent redaction enregistré sur le bus")


def executer_cycle_redaction(
    bus: EventBus, readme_cn: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Exécute un cycle de rédaction complet et retourne les drafts."""
    results = []

    for snippet_id, snippet in SNIPPETS.items():
        draft = generer_draft_zhihu(snippet, readme_cn)

        # Déposer le draft dans a_valider/draft_zhihu_[id].md
        contenu_draft = (
            f"# Draft Zhihu — {snippet_id}\n\n"
            f"**Titre CN :** {draft['titre_cn']}\n\n"
            f"**Snippet source :** {snippet.get('titre', '')}\n\n"
            f"**Principe MTTV :** {snippet.get('principe_mttv', '')}\n\n"
            f"**Longueur :** {len(draft['corps_cn'])} caractères\n\n"
            f"---\n\n"
            f"{draft['corps_cn']}\n\n"
            f"---\n\n"
            f"**Statut :** en_attente_validation_humaine\n"
            f"**auto_publish :** false — NE PAS PUBLIER SANS VALIDATION\n"
        )
        nom_fichier = f"draft_zhihu_{snippet_id}.md"
        _ecrire_fichier_a_valider(nom_fichier, contenu_draft)

        event = Event(
            event_type="draft.created",
            payload={
                "snippet_id": snippet_id,
                "snippet_titre": snippet.get("titre", ""),
                "titre_cn": draft["titre_cn"],
                "corps_cn": draft["corps_cn"],
                "longueur_caracteres": len(draft["corps_cn"]),
                "statut": "en_attente_validation_humaine",
                "chemin_fichier": os.path.join("a_valider", nom_fichier),
                "auto_publish": False,
            },
            source="agent-redaction",
            auto_publish=False,
        )
        bus.publish(event)
        results.append(event.payload)

    return results
