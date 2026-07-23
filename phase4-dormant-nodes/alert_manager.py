#!/usr/bin/env python3
"""
alert_manager.py — Système d'alerte unifié MTTV-FLP
====================================================
Webhook (Discord/Generic) + fallback SMTP pour les scripts
phase4-dormant-nodes et l'ensemble de l'écosystème.

Usage:
    from alert_manager import send_alert

    send_alert("CRITICAL", "ipfs_active_pinner", "CID échec x3", details={...})

Variables d'environnement (fichier .env ou variables système) :
    ALERT_WEBHOOK_URL  : URL du webhook (Discord, Slack, Teams, etc.)
    SMTP_*             : identifiants SMTP (fallback si webhook échoue)

Signature SCS : SCS_2026
sig:0x4D545456
"""

from __future__ import annotations

import json
import logging
import os
import smtplib
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("alert_manager")

# ─── Chemins ────────────────────────────────────────────────────────────────
BASE_DIR: Path = Path(__file__).resolve().parent
ENV_PATH: Path = BASE_DIR / ".env"

# ─── Helpers ────────────────────────────────────────────────────────────────


def _load_env() -> dict[str, str]:
    """Charge les variables depuis .env si le fichier existe.

    Retourne un dict avec les valeurs trouvées (priorité aux variables
    d'environnement système si déjà définies).
    """
    env: dict[str, str] = {}

    # Lire le fichier .env
    if ENV_PATH.exists():
        try:
            for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("\"'")
                if key not in os.environ:  # ne pas écraser les vars système
                    env[key] = value
        except Exception as exc:
            logger.warning("Erreur lecture .env: %s", exc)

    # Priorité aux variables d'environnement système
    for key in [
        "ALERT_WEBHOOK_URL",
        "SMTP_SERVER", "SMTP_PORT",
        "SENDER_EMAIL", "SENDER_PASSWORD", "RECIPIENT_EMAIL",
    ]:
        sys_val = os.environ.get(key)
        if sys_val:
            env[key] = sys_val

    return env


def _get_env(key: str, default: str = "") -> str:
    """Récupère une variable d'environnement avec cache."""
    return _load_env().get(key, default)


def _timestamp() -> str:
    """ISO-8601 timestamp UTC."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ===========================================================================
# WEBHOOK — Canal primaire
# ===========================================================================

WEBHOOK_URL: str = _get_env("ALERT_WEBHOOK_URL", "")


def send_webhook(
    level: str,
    source: str,
    message: str,
    details: Optional[dict[str, Any]] = None,
    url: Optional[str] = None,
) -> bool:
    """Envoie une alerte via webhook Discord-compatible.

    Args:
        level: Niveau de sévérité (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        source: Nom du composant émetteur.
        message: Message textuel de l'alerte.
        details: Données structurées additionnelles.
        url: URL du webhook (défaut: ALERT_WEBHOOK_URL du .env).

    Returns:
        True si envoyé avec succès.
    """
    target_url = url or WEBHOOK_URL
    if not target_url:
        logger.debug("Aucune URL de webhook configurée. Alerte non envoyée.")
        return False

    payload: dict[str, Any] = {
        "embeds": [
            {
                "title": f"[{level}] {source}",
                "description": message,
                "color": _level_color(level),
                "timestamp": _timestamp(),
                "footer": {"text": "MTTV-FLP · sig:0x4D545456"},
            }
        ]
    }

    if details:
        fields = [{"name": k, "value": str(v)[:1024], "inline": True}
                  for k, v in details.items()]
        payload["embeds"][0]["fields"] = fields

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        target_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if 200 <= resp.status < 300:
                logger.info("Webhook envoyé avec succès → %s [%s]", source, level)
                return True
            else:
                logger.warning("Webhook retourné HTTP %d", resp.status)
                return False
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
        logger.warning("Échec webhook (%s): %s", target_url[:40], exc)
        return False


def _level_color(level: str) -> int:
    """Convertit un niveau texte en couleur Discord embed."""
    mapping = {
        "DEBUG": 0x808080,      # gris
        "INFO": 0x3498DB,       # bleu
        "WARNING": 0xF39C12,    # orange
        "ERROR": 0xE74C3C,      # rouge
        "CRITICAL": 0x8E44AD,   # violet
    }
    return mapping.get(level.upper(), 0xFFFF00)


# ===========================================================================
# SMTP — Fallback
# ===========================================================================

SMTP_SERVER: str = _get_env("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT: int = int(_get_env("SMTP_PORT", "587"))
SENDER_EMAIL: str = _get_env("SENDER_EMAIL", "")
SENDER_PASSWORD: str = _get_env("SENDER_PASSWORD", "")
RECIPIENT_EMAIL: str = _get_env("RECIPIENT_EMAIL", "")


def send_smtp_alert(
    level: str,
    source: str,
    message: str,
    details: Optional[dict[str, Any]] = None,
) -> bool:
    """Envoie une alerte par email SMTP (fallback).

    Args:
        level: Niveau de sévérité.
        source: Nom du composant émetteur.
        message: Message textuel.
        details: Données additionnelles.

    Returns:
        True si envoyé avec succès.
    """
    if not all([SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL]):
        logger.debug("SMTP non configuré. Alerte non envoyée par email.")
        return False

    subject = f"[MTTV-FLP] {level} — {source}"
    body_lines: list[str] = [
        f"Niveau   : {level}",
        f"Source   : {source}",
        f"Message  : {message}",
        f"Timestamp: {_timestamp()}",
        f"Signature: 0x4D545456",
    ]
    if details:
        body_lines.append("")
        body_lines.append("Détails :")
        body_lines.append(json.dumps(details, indent=2, ensure_ascii=False))

    msg = MIMEText("\n".join(body_lines), "plain", "utf-8")
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL
    msg["Subject"] = subject

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.starttls(context=context)
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        logger.info("Alerte SMTP envoyée → %s [%s]", source, level)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP auth échouée pour %s", SENDER_EMAIL)
    except smtplib.SMTPException as exc:
        logger.error("SMTP error: %s", exc)
    except (TimeoutError, OSError) as exc:
        logger.error("Réseau SMTP: %s", exc)
    except Exception as exc:
        logger.error("Erreur SMTP inattendue: %s", exc)

    return False


# ===========================================================================
# ENVOI UNIFIÉ — Webhook primaire, SMTP fallback
# ===========================================================================


def send_alert(
    level: str,
    source: str,
    message: str,
    details: Optional[dict[str, Any]] = None,
    *,
    force_smtp: bool = False,
) -> bool:
    """Envoie une alerte via webhook (canal primaire) avec fallback SMTP.

    Args:
        level: Niveau de sévérité.
        source: Nom du composant.
        message: Message de l'alerte.
        details: Données structurées additionnelles.
        force_smtp: Si True, utilise SMTP uniquement (ignore webhook).

    Returns:
        True si au moins un canal a fonctionné.
    """
    # Webhook (primaire)
    sent = False
    if not force_smtp and WEBHOOK_URL:
        sent = send_webhook(level, source, message, details)

    # SMTP (fallback ou forcé)
    if force_smtp or not sent:
        if send_smtp_alert(level, source, message, details):
            sent = True

    if not sent:
        logger.warning(
            "Alerte non transmise (aucun canal configuré) | %s | %s",
            source, message,
        )

    return sent
