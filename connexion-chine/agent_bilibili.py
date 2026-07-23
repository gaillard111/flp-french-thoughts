#!/usr/bin/env python3
"""
Zoo-code — Agent bilibili (Connexion Chine)

sig:0x4D545456 · SCS_2026

Rôle :
  Générer un script vidéo de 5 minutes et des sous-titres .srt (CN)
  à partir d'un draft validé par un humain.

Écoute :
  - draft.validé_par_humain

Publie :
  - video.ready {script_5min, sous_titres_srt}

auto_publish : false
NE JAMAIS PUBLIER DIRECTEMENT SUR BILIBILI
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from bus import Event, EventBus, get_bus

logger = logging.getLogger("zoo-bilibili")

# ── Durée cible ─────────────────────────────────────────────────────────────
DUREE_CIBLE_SECONDES = 5 * 60  # 5 minutes
VITESSE_PAROLE_CPS = 4.0  # caractères chinois par seconde (rythme modéré)


def squelette_5min(titre_cn: str, corps_cn: str) -> List[Dict[str, Any]]:
    """
    Structure un script vidéo de 5 minutes à partir d'un draft Zhihu.

    Structure :
      - 0:00-0:30  : Accroche (le problème)
      - 0:30-1:30  : Contexte (pourquoi c'est important)
      - 1:30-3:30  : Idée MTTV (le coeur)
      - 3:30-4:30  : Implication (ce que ça change)
      - 4:30-5:00  : Question ouverte + CTA
    """
    # Découpage du corps en segments
    paragraphes = [p.strip() for p in corps_cn.split("\n\n") if p.strip()]

    segments = []

    # Segment 1: Accroche (0:00-0:30)
    accroche = (
        f"你有没有想过，{paragraphes[0][:80] if paragraphes else '我们面临的这个问题'}"
        if paragraphes else "你有没有想过..."
    )
    segments.append({
        "debut": 0,
        "fin": 30,
        "duree": 30,
        "type": "accroche",
        "narration_cn": accroche,
        "visuel": "Question provocante en texte, fond sombre",
    })

    # Segment 2: Contexte (0:30-1:30)
    contexte = (
        f"在当今的技术环境中，{paragraphes[0] if paragraphes else '我们面临着前所未有的挑战'}。"
        f"传统方法虽然有效，但存在根本性的结构问题。"
    )
    segments.append({
        "debut": 30,
        "fin": 90,
        "duree": 60,
        "type": "contexte",
        "narration_cn": contexte,
        "visuel": "Diagramme de l'architecture traditionnelle, points de défaillance en rouge",
    })

    # Segment 3: Idée MTTV (1:30-3:30)
    idee_mttv = ""
    for i, p in enumerate(paragraphes[1:3] if len(paragraphes) > 2 else paragraphes):
        idee_mttv += p + "\n\n"

    if not idee_mttv:
        idee_mttv = corps_cn[:500]

    segments.append({
        "debut": 90,
        "fin": 210,
        "duree": 120,
        "type": "idee_mttv",
        "narration_cn": idee_mttv,
        "visuel": (
            "Animation des concepts MTTV: transduction, palier poreux, "
            "bus protoniques, energy-flow-optimization"
        ),
    })

    # Segment 4: Implications (3:30-4:30)
    implications = ""
    if len(paragraphes) > 3:
        implications = paragraphes[3]

    if not implications:
        implications = (
            f"这一方案的实际影响超越了技术层面。它改变了我们思考系统设计的方式："
            f"从追求最优到追求可行，从中心化到分布式共识，从资源最大化到能源优化。"
        )

    segments.append({
        "debut": 210,
        "fin": 270,
        "duree": 60,
        "type": "implications",
        "narration_cn": implications,
        "visuel": "Infographie comparant avant/après, métriques d'énergie et de résilience",
    })

    # Segment 5: Question ouverte (4:30-5:00)
    if paragraphes and "?" in paragraphes[-1]:
        question = paragraphes[-1]
    else:
        question = (
            "MTTV-FLP 框架为我们提供了一个全新的视角。问题是："
            "当我们在日常工程中应用这些原则时，我们能否真正实现从工具到生态的跨越？"
            "欢迎在评论区分享你的想法。"
        )
    segments.append({
        "debut": 270,
        "fin": 300,
        "duree": 30,
        "type": "question_ouverte",
        "narration_cn": question,
        "visuel": "Question ouverte + lien vers le dépôt GitHub / Zhihu",
    })

    return segments


def generer_script_5min(titre_cn: str, corps_cn: str) -> str:
    """
    Génère un script vidéo complet de 5 minutes en CN.
    """
    segments = squelette_5min(titre_cn, corps_cn)

    lignes_script = [
        "=" * 60,
        f"SCRIPT VIDÉO BILIBILI — 5 minutes",
        f"Titre: {titre_cn}",
        f"Durée totale: {DUREE_CIBLE_SECONDES}s",
        f"auto_publish: false — VALIDATION HUMAINE REQUISE",
        "=" * 60,
        "",
    ]

    for seg in segments:
        deb_m, deb_s = divmod(seg["debut"], 60)
        fin_m, fin_s = divmod(seg["fin"], 60)
        lignes_script.append(
            f"--- [{deb_m:02d}:{deb_s:02d} - {fin_m:02d}:{fin_s:02d}] "
            f"({seg['type']}) ---"
        )
        lignes_script.append(f"VISUEL: {seg['visuel']}")
        lignes_script.append("")
        lignes_script.append(seg["narration_cn"])
        lignes_script.append("")
        lignes_script.append("---")

    lignes_script.append("FIN DU SCRIPT — auto_publish=false")
    lignes_script.append("=" * 60)

    return "\n".join(lignes_script)


def generer_sous_titres_srt(segments: List[Dict[str, Any]]) -> str:
    """
    Génère un fichier .srt (SubRip) à partir des segments du script.

    Chaque segment est divisé en sous-titres de ~5 secondes.
    """
    lignes_srt: List[str] = []
    sous_titre_idx = 1

    for seg in segments:
        texte = seg["narration_cn"]
        debut = seg["debut"]
        duree = seg["duree"]

        # Diviser le texte en phrases (~5 secondes chacune = ~20 chars)
        phrase_longueur = int(VITESSE_PAROLE_CPS * 5)  # ~20 chars
        phrases = []
        mots = list(texte)
        for i in range(0, len(mots), phrase_longueur):
            phrases.append("".join(mots[i:i + phrase_longueur]))

        if not phrases:
            phrases = [texte[:phrase_longueur]]

        duree_phrase = duree / len(phrases)
        for i, phrase in enumerate(phrases):
            ts_debut = debut + i * duree_phrase
            ts_fin = ts_debut + duree_phrase

            def fmt_ts(secondes: float) -> str:
                h = int(secondes // 3600)
                m = int((secondes % 3600) // 60)
                s = int(secondes % 60)
                ms = int((secondes % 1) * 1000)
                return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

            lignes_srt.append(str(sous_titre_idx))
            lignes_srt.append(f"{fmt_ts(ts_debut)} --> {fmt_ts(ts_fin)}")
            lignes_srt.append(phrase)
            lignes_srt.append("")
            sous_titre_idx += 1

    return "\n".join(lignes_srt)


def _ecrire_fichier_a_valider(nom_fichier: str, contenu: str) -> str:
    """Écrit un fichier dans le dossier a_valider/ pour validation humaine."""
    dossier = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a_valider")
    os.makedirs(dossier, exist_ok=True)
    chemin = os.path.join(dossier, nom_fichier)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(contenu)
    logger.info(f"Fichier déposé dans a_valider/: {nom_fichier}")
    return chemin


def handle_draft_valide(event: Event) -> None:
    """Déclenché par draft.validé_par_humain."""
    payload = event.payload
    titre_cn = payload.get("titre_cn", "(sans titre)")
    corps_cn = payload.get("corps_cn", "")
    snippet_id = payload.get("snippet_id", "?")

    logger.info(
        f"=== Bilibili déclenché: draft validé pour {snippet_id} ==="
    )

    bus = get_bus()

    # Génération du script
    script = generer_script_5min(titre_cn, corps_cn)

    # Génération des sous-titres
    segments = squelette_5min(titre_cn, corps_cn)
    sous_titres_srt = generer_sous_titres_srt(segments)

    # Déposer script et sous-titres dans a_valider/
    _ecrire_fichier_a_valider(f"bilibili_script_{snippet_id}.md", script)
    _ecrire_fichier_a_valider(f"bilibili_sous_titres_{snippet_id}.srt", sous_titres_srt)

    # Publication de l'événement video.ready (NE PAS PUBLIER SUR BILIBILI)
    event = Event(
        event_type="video.ready",
        payload={
            "snippet_id": snippet_id,
            "titre_cn": titre_cn,
            "script_5min": script,
            "sous_titres_srt": sous_titres_srt,
            "duree_secondes": DUREE_CIBLE_SECONDES,
            "format": "bilibili_5min",
            "sous_titres_format": "srt",
            "auto_publish": False,
            "chemin_script": f"a_valider/bilibili_script_{snippet_id}.md",
            "chemin_srt": f"a_valider/bilibili_sous_titres_{snippet_id}.srt",
        },
        source="agent-bilibili",
        auto_publish=False,
    )
    bus.publish(event)
    logger.info(f"Video.ready publié pour {snippet_id}")


def enregistrer_agent_bilibili(bus: EventBus) -> None:
    """Enregistre les écouteurs de l'agent bilibili sur le bus."""
    bus.on("draft.validé_par_humain", handle_draft_valide)
    logger.info("Agent bilibili enregistré sur le bus")


def executer_cycle_bilibili(
    bus: EventBus,
    titre_cn: str,
    corps_cn: str,
    snippet_id: str = "snippet-013",
) -> Dict[str, Any]:
    """Exécute un cycle bilibili complet et retourne le résultat."""
    script = generer_script_5min(titre_cn, corps_cn)
    segments = squelette_5min(titre_cn, corps_cn)
    sous_titres_srt = generer_sous_titres_srt(segments)

    # Déposer script et sous-titres dans a_valider/
    _ecrire_fichier_a_valider(f"bilibili_script_{snippet_id}.md", script)
    _ecrire_fichier_a_valider(f"bilibili_sous_titres_{snippet_id}.srt", sous_titres_srt)

    event = Event(
        event_type="video.ready",
        payload={
            "snippet_id": snippet_id,
            "titre_cn": titre_cn,
            "script_5min": script,
            "sous_titres_srt": sous_titres_srt,
            "duree_secondes": DUREE_CIBLE_SECONDES,
            "format": "bilibili_5min",
            "sous_titres_format": "srt",
            "auto_publish": False,
            "chemin_script": f"a_valider/bilibili_script_{snippet_id}.md",
            "chemin_srt": f"a_valider/bilibili_sous_titres_{snippet_id}.srt",
        },
        source="agent-bilibili",
        auto_publish=False,
    )
    bus.publish(event)

    return event.payload
