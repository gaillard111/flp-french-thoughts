#!/usr/bin/env python3
"""
Zoo-code — Agent sync (Connexion Chine)

sig:0x4D545456 · SCS_2026

Rôle :
  Traduire les README_FR vers README_CN en conservant intacts les termes
  MTTV-FLP (transduction, palier poreux, bus protoniques,
  energy-flow-optimization, graines neutral v10/v13).

Écoute :
  - push main (via webhook)
  - veille.new si score >= 4

Publie :
  - sync.done {readme_cn}

auto_publish : false
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from bus import Event, EventBus, get_bus

logger = logging.getLogger("zoo-sync")

# ── Termes MTTV-FLP à conserver intacts ─────────────────────────────────────
TERMES_MTTV_INTACTS = {
    "MTTV-FLP": "MTTV-FLP",
    "transduction": "transduction",
    "palier poreux": "palier poreux",
    "bus protoniques": "bus protoniques",
    "energy-flow-optimization": "energy-flow-optimization",
    "graines neutral v10": "graines neutral v10",
    "graines neutral v13": "graines neutral v13",
    "MPVR": "MPVR",
    "SCS": "SCS",
    "Système de Convergence Systémique": "Système de Convergence Systémique",
    "Minimum Path Viable Route": "Minimum Path Viable Route",
    "sous-optimalité": "sous-optimalité",
    "under-optimality": "under-optimality",
    "quorum": "quorum",
    "Θ": "Θ",
    "σ₄": "σ₄",
    "sigma4": "sigma4",
    "Sigma4Lisse": "Sigma4Lisse",
    "tétravalence": "tétravalence",
    "T⁴": "T⁴",
    "juxtaposition féconde": "juxtaposition féconde",
    "mycélium": "mycélium",
    "tissé-vivant": "tissé-vivant",
    "basse continue": "basse continue",
    "sig:0x4D545456": "sig:0x4D545456",
    "SCS_2026": "SCS_2026",
    "Ψ": "Ψ",
    "Φ": "Φ",
    "B": "B",
    "Agent 8": "Agent 8",
    "Socle Φ": "Socle Φ",
}

# ── README FR source (extrait du référentiel mttv-snippets) ──────────────────
README_FR_SOURCE = r"""# MTTV-FLP — Fragments et Éclats

> **Identifiant public : MTTV-FLP**
> Signature interne : sig:0x4D545456

> *Code micro-libraries that engineers will adopt by pragmatism — reduced costs,
> energy sobriety, resilience under crises. Each snippet is a sensor of the
> mycelium, embedded at the heart of infrastructure.*

---

## Overview

This repository contains three **snippets** (micro-libraries) that implement
core principles of the **MTTV-FLP** framework (Minimum Path Viable Route /
Système de Convergence Systémique) as production-ready, copy-pasteable code.

They are designed to be:

- **Pragmatic** — solve real engineering problems (cost, latency, reliability).
- **Sober** — minimise resource consumption by design.
- **Decentralised** — no single point of failure or authority.

---

## Snippets

### 1. MPVR — Asynchronous Quorum Routing

**Problem:** Centralised load balancers are single points of failure and
energy hogs. You need a distributed routing strategy that works even when
some peers are offline or malicious.

**Solution:** Route data through a set of peers and require an asynchronous
quorum (default: 3) to validate before considering the route successful.

**MTTV alignment:** MPVR (minimum route that satisfies quorum),
Under-optimality (quorum is the *minimum* viable, not maximum).

### 2. SCS — Systemic Convergence Signature Validation

**Problem:** Centralised Certificate Authorities are expensive, fragile,
and represent a single point of trust.

**Solution:** A signature is valid if at least 2 members of a quorum have
independently produced the same signature for the same data.

**MTTV alignment:** SCS (convergence through redundancy), Under-optimality
(quorum of 2 is sufficient — not maximal).

### 3. Sober Nginx Configuration

**Problem:** Default Nginx configurations are tuned for maximum throughput
at maximum energy cost.

**Solution:** A configuration that uses the *minimum viable* resources.

**MTTV alignment:** Under-optimality (minimum viable resources),
SCS (converges through lightweight keepalives), MPVR (shortest path).

---

## MTTV-FLP Framework

Key principles:

- **MPVR** — Minimum Path Viable Route: always prefer the simplest route
  that satisfies requirements.
- **SCS** — Système de Convergence Systémique: trust emerges from
  independent redundant computation, not central authority.
- **Sous-optimalité** — Under-optimality: the minimum viable solution is
  preferred over the maximal one, preserving resources for the network.

---

## License

MIT — Free to use, modify, and distribute.

sig:0x4D545456
"""


def traduire_vers_cn(texte_fr: str) -> str:
    """
    Traduit le README_FR vers README_CN (mandarin simplifié).

    Les termes MTTV-FLP sont conservés intacts.
    Le ton est académique neutre, pas marketing.
    """
    # Construction de la traduction en remplaçant les blocs
    # Note: dans une version production, utiliser une API LLM (DeepSeek, Qwen, etc.)
    # Ici, template de traduction basé sur les règles MTTV

    cn_lines = []
    fr_lines = texte_fr.split("\n")

    for line in fr_lines:
        stripped = line.strip()

        # Conserver les lignes vides
        if not stripped:
            cn_lines.append("")
            continue

        # Lignes de signature — conserver intact
        if "sig:" in line or "SCS_" in line:
            cn_lines.append(line)
            continue

        # Titres
        if stripped.startswith("# ") and "MTTV-FLP" in stripped:
            cn_lines.append("# MTTV-FLP — 碎片与辉光")
            continue
        elif stripped.startswith("## "):
            # Traduire les titres de section
            titres_cn = {
                "Overview": "## 概述",
                "Snippets": "## 代码片段",
                "MTTV-FLP Framework": "## MTTV-FLP 框架",
                "License": "## 许可证",
                "Getting Started": "## 快速开始",
                "Références croisées": "## 交叉参考",
            }
            titre_key = stripped.replace("## ", "").strip()
            if titre_key in titres_cn:
                cn_lines.append(titres_cn[titre_key])
            else:
                cn_lines.append(line)  # fallback
            continue

        # Lignes de citation (> ...)
        if stripped.startswith("> "):
            cn_lines.append(line)
            continue

        # Lignes avec des termes MTTV intacts
        # Vérifier si la ligne contient des termes à conserver
        a_termes_mttv = any(t in line for t in TERMES_MTTV_INTACTS)

        if a_termes_mttv:
            # Traduire le reste mais garder les termes intacts
            cn_lines.append(line)  # Dans une version prod: traduction sélective
            continue

        # Lignes de séparation
        if stripped.startswith("---"):
            cn_lines.append(line)
            continue

        # Lignes de lien [texte](url)
        if "[" in line and "](" in line:
            cn_lines.append(line)
            continue

        # Lignes de tableau
        if "|" in line:
            cn_lines.append(line)
            continue

        # Lignes de code
        if stripped.startswith("```") or stripped.startswith("`"):
            cn_lines.append(line)
            continue

        # Traduction générale (simulation — remplacer par API LLM en prod)
        traductions_simulees: Dict[str, str] = {
            "> *Code micro-libraries that engineers will adopt by pragmatism": "> *工程师因实用主义而采纳的微库代码",
            "This repository contains three **snippets**": "本仓库包含三个**代码片段**",
            "They are designed to be:": "它们的设计原则是：",
            "**Pragmatic** — solve real engineering problems": "**实用主义** — 解决实际工程问题",
            "**Sober** — minimise resource consumption by design": "**节制** — 通过设计最小化资源消耗",
            "**Decentralised** — no single point of failure or authority": "**去中心化** — 无单点故障或单点权威",
            "**Problem:**": "**问题：**",
            "**Solution:**": "**解决方案：**",
            "**MTTV alignment:**": "**MTTV 对齐：**",
            "Centralised load balancers are single points of failure and": "集中式负载均衡器是单点故障和",
            "energy hogs.": "能源消耗大户。",
            "Route data through a set of peers and require an asynchronous": "通过一组对等节点路由数据，并要求异步",
            "quorum (default: 3) to validate before considering the route successful.": "法定人数（默认：3）验证，然后才认为路由成功。",
            "Centralised Certificate Authorities are expensive, fragile,": "集中式证书颁发机构昂贵、脆弱、",
            "and represent a single point of trust.": "且代表单一信任点。",
            "A signature is valid if at least 2 members of a quorum have": "如果法定人数中至少2个成员独立生成",
            "independently produced the same signature for the same data.": "了相同数据的相同签名，则该签名有效。",
            "Default Nginx configurations are tuned for maximum throughput": "默认Nginx配置为最大吞吐量调优，",
            "at maximum energy cost.": "以最大能源成本为代价。",
            "A configuration that uses the *minimum viable* resources.": "使用*最小可行*资源的配置。",
            "MIT — Free to use, modify, and distribute.": "MIT 许可证 — 可自由使用、修改和分发。",
            "MPVR (minimum route that satisfies quorum),": "MPVR（满足法定人数的最小路由），",
            "Under-optimality (quorum is the *minimum* viable, not maximum).": "次优性（法定人数是最小可行，而非最大）。",
            "SCS (convergence through redundancy), Under-optimality": "SCS（通过冗余实现汇聚），次优性",
            "(quorum of 2 is sufficient — not maximal).": "（法定人数为2即足够 — 而非最大）。",
            "Key principles:": "关键原则：",
        }

        trouve = False
        for fr, cn in traductions_simulees.items():
            if fr in line:
                cn_lines.append(line.replace(fr, cn))
                trouve = True
                break

        if not trouve:
            # Fallback: conserver la ligne en anglais (temporaire)
            # Dans une version production, utiliser une API de traduction
            cn_lines.append(line)

    return "\n".join(cn_lines)


def handle_veille_new(event: Event) -> None:
    """Déclenché par veille.new si score >= 3.2."""
    payload = event.payload
    score = payload.get("score", 0)

    if score >= 3.2:
        logger.info(
            f"=== Sync déclenché: score={score} "
            f"pour {payload.get('profil_id', '?')} ==="
        )
        _executer_sync()
    else:
        logger.info(
            f"Sync ignoré: score={score} < 4 "
            f"pour {payload.get('profil_id', '?')}"
        )


def handle_push_main(event: Event) -> None:
    """Déclenché par push sur la branche main."""
    logger.info("=== Sync déclenché par push main ===")
    _executer_sync()


def _ecrire_fichier_a_valider(nom_fichier: str, contenu: str) -> str:
    """Écrit un fichier dans le dossier a_valider/ pour validation humaine."""
    dossier = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a_valider")
    os.makedirs(dossier, exist_ok=True)
    chemin = os.path.join(dossier, nom_fichier)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(contenu)
    logger.info(f"Fichier déposé dans a_valider/: {nom_fichier}")
    return chemin


def _executer_sync() -> None:
    """Exécute la synchronisation (traduction README). Ne pousse PAS sur Gitee."""
    bus = get_bus()
    readme_cn = traduire_vers_cn(README_FR_SOURCE)

    # Déposer le README_CN dans a_valider/ pour validation humaine
    chemin = _ecrire_fichier_a_valider("README_CN_a_revoir.md", readme_cn)

    event = Event(
        event_type="sync.done",
        payload={
            "readme_cn": readme_cn,
            "chemin_fichier": chemin,
            "termes_conserves": list(TERMES_MTTV_INTACTS.keys()),
            "langue_source": "FR/EN",
            "langue_cible": "CN",
            "taille_caracteres": len(readme_cn),
        },
        source="agent-sync",
        auto_publish=False,
    )
    bus.publish(event)


def enregistrer_agent_sync(bus: EventBus) -> None:
    """Enregistre les écouteurs de l'agent sync sur le bus."""
    bus.on("veille.new", handle_veille_new)
    bus.on("webhook.github.push", handle_push_main)
    bus.on("webhook.gitee.push", handle_push_main)
    logger.info("Agent sync enregistré sur le bus")


def executer_cycle_sync(bus: EventBus) -> Dict[str, Any]:
    """Exécute un cycle de sync complet et retourne le résultat."""
    readme_cn = traduire_vers_cn(README_FR_SOURCE)

    # Déposer le README_CN dans a_valider/ pour validation humaine
    chemin = _ecrire_fichier_a_valider("README_CN_a_revoir.md", readme_cn)

    event = Event(
        event_type="sync.done",
        payload={
            "readme_cn": readme_cn,
            "chemin_fichier": chemin,
            "termes_conserves": list(TERMES_MTTV_INTACTS.keys()),
            "langue_source": "FR/EN",
            "langue_cible": "CN",
            "taille_caracteres": len(readme_cn),
        },
        source="agent-sync",
        auto_publish=False,
    )
    bus.publish(event)

    return event.payload
