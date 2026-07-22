#!/usr/bin/env python3
"""
resource_guardrail.py — Garde-fou coûts/trafic pour MTTV-FLP
============================================================

Surveille la bande passante réseau sortante et l'usage mémoire RAM.

Fonctionnalités :
  - Suivi quotidien du trafic réseau sortant (bytes → MB)
  - Suivi de l'utilisation mémoire RAM (% et MB)
  - Seuils d'alerte paramétrables via variables d'environnement :
      MAX_DAILY_TRAFFIC_MB  (défaut: 500)
      MAX_RAM_MB            (défaut: 180)
      ALERT_COOLDOWN_SEC    (défaut: 3600, évite les alertes répétitives)
  - Persistance de l'état de comptage (daily counter) dans un fichier JSON
  - Déclenchement d'alerte via le système de notification
    (phase4-dormant-nodes/alert_manager.py — webhook Discord/Generic + SMTP)
  - Exposition des métriques via une API simple (dict Python)

Usage:
    from resource_guardrail import ResourceGuardrail

    guard = ResourceGuardrail()
    metrics = guard.collect()
    guard.check_and_alert(metrics)

Signature SCS_2026 · sig:0x4D545456
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("resource_guardrail")

# ===========================================================================
# CHEMINS
# ===========================================================================

BASE_DIR: Path = Path(__file__).resolve().parent                     # zoo-code/
PROJECT_ROOT: Path = BASE_DIR.parent                                  # racine
GUARDRAIL_STATE: Path = BASE_DIR / "guardrail_state.json"             # état persistant

# ===========================================================================
# CONSTANTES PAR DÉFAUT
# ===========================================================================

# Seuil quotidien de trafic sortant (MB)
_DEFAULT_MAX_TRAFFIC_MB: int = 500

# Seuil mémoire RAM (MB)
_DEFAULT_MAX_RAM_MB: int = 180

# Délai minimal entre deux alertes consécutives pour un même seuil (secondes)
_DEFAULT_ALERT_COOLDOWN_SEC: int = 3600

# Taille minimale du payload pour /proc/net-dev (évite les lectures erronées)
_MIN_NET_DEV_LINES: int = 2


def _get_env_int(key: str, default: int) -> int:
    """Récupère un entier depuis une variable d'environnement.

    Args:
        key: Nom de la variable d'environnement.
        default: Valeur par défaut si absente ou invalide.

    Returns:
        Valeur entière.
    """
    raw = os.environ.get(key, "")
    if not raw:
        return default
    try:
        return int(raw)
    except (ValueError, TypeError):
        logger.warning("Guardrail: %s invalide ('%s'), utilisation défaut %d", key, raw, default)
        return default


def _timestamp_iso() -> str:
    """Retourne le timestamp ISO-8601 UTC."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _now_epoch() -> float:
    """Retourne le timestamp Unix actuel."""
    return time.time()


# ===========================================================================
# COLLECTEUR DE MÉTRIQUES SYSTÈME
# ===========================================================================


def _read_proc_net_dev() -> dict[str, dict[str, int]]:
    """Lit /proc/net/dev pour extraire les compteurs réseau par interface.

    Utilise un fallback sur psutil si /proc/net/dev n'est pas disponible
    (macOS, Windows).

    Returns:
        Dict structuré : { interface: { "rx_bytes": int, "tx_bytes": int } }
    """
    net_data: dict[str, dict[str, int]] = {}

    # Tentative 1 : /proc/net/dev (Linux natif)
    proc_net = Path("/proc/net/dev")
    if proc_net.exists():
        try:
            lines = proc_net.read_text(encoding="utf-8").splitlines()
            if len(lines) < _MIN_NET_DEV_LINES:
                logger.debug("Guardrail: /proc/net_dev trop court (%d lignes)", len(lines))
                return net_data

            # Ignorer les 2 premières lignes (en-têtes)
            for line in lines[2:]:
                parts = line.strip().split()
                if len(parts) < 10:
                    continue
                iface = parts[0].rstrip(":")
                # parts[0]=nom, parts[1]=rx_bytes, parts[9]=tx_bytes
                try:
                    rx = int(parts[1])
                    tx = int(parts[9])
                    net_data[iface] = {"rx_bytes": rx, "tx_bytes": tx}
                except (ValueError, IndexError):
                    continue
            return net_data
        except (OSError, PermissionError) as exc:
            logger.debug("Guardrail: /proc/net_dev inaccessible (%s)", exc)

    # Tentative 2 : psutil (multi-plateforme)
    try:
        import psutil as _psutil
        net_io = _psutil.net_io_counters(pernic=True)
        for iface, counters in net_io.items():
            net_data[iface] = {
                "rx_bytes": counters.bytes_recv,
                "tx_bytes": counters.bytes_sent,
            }
        return net_data
    except ImportError:
        logger.debug("Guardrail: psutil non disponible pour les métriques réseau")
    except Exception as exc:
        logger.debug("Guardrail: psutil.net_io_counters échoué (%s)", exc)

    return net_data


def _get_total_tx_bytes() -> int:
    """Calcule le total des bytes transmis (tx) toutes interfaces confondues.

    Exclut les interfaces virtuelles (lo, docker, veth, bridge, etc.)
    pour ne compter que le trafic réel.

    Returns:
        Total des bytes en sortie.
    """
    interfaces = _read_proc_net_dev()
    total = 0
    excluded_prefixes = ("lo", "docker", "veth", "br-", "bridge", "tun", "tap")

    for iface, counters in interfaces.items():
        if iface.startswith(excluded_prefixes):
            continue
        total += counters.get("tx_bytes", 0)

    return total


def _get_memory_mb() -> dict[str, float]:
    """Mesure la mémoire RAM utilisée (MB) et le pourcentage.

    Returns:
        Dict avec "used_mb", "total_mb", "percent", et le statut.
    """
    try:
        import psutil as _psutil
        mem = _psutil.virtual_memory()
        return {
            "total_mb": round(mem.total / (1024 ** 2), 1),
            "available_mb": round(mem.available / (1024 ** 2), 1),
            "used_mb": round(mem.used / (1024 ** 2), 1),
            "percent": mem.percent,
            "source": "psutil",
        }
    except ImportError:
        pass
    except Exception as exc:
        logger.debug("Guardrail: psutil.virtual_memory échoué (%s)", exc)

    # Fallback : /proc/meminfo (Linux)
    proc_mem = Path("/proc/meminfo")
    if proc_mem.exists():
        try:
            lines = proc_mem.read_text(encoding="utf-8").splitlines()
            mem_total_kb = 0
            mem_avail_kb = 0
            for line in lines:
                if line.startswith("MemTotal:"):
                    mem_total_kb = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_avail_kb = int(line.split()[1])
            if mem_total_kb > 0:
                total_mb = round(mem_total_kb / 1024, 1)
                available_mb = round(mem_avail_kb / 1024, 1)
                used_mb = round(total_mb - available_mb, 1)
                percent = round((used_mb / total_mb) * 100, 1) if total_mb > 0 else 0.0
                return {
                    "total_mb": total_mb,
                    "available_mb": available_mb,
                    "used_mb": used_mb,
                    "percent": percent,
                    "source": "proc_meminfo",
                }
        except (OSError, ValueError, IndexError) as exc:
            logger.debug("Guardrail: /proc/meminfo échoué (%s)", exc)

    return {
        "total_mb": 0.0,
        "available_mb": 0.0,
        "used_mb": 0.0,
        "percent": 0.0,
        "source": "unavailable",
    }


# ===========================================================================
# PERSISTANCE D'ÉTAT
# ===========================================================================


def _load_state() -> dict[str, Any]:
    """Charge l'état persistant du garde-fou depuis le fichier JSON.

    Returns:
        Dict avec l'état (date, compteurs, historique des alertes).
    """
    if not GUARDRAIL_STATE.exists():
        return _fresh_state()

    try:
        data = json.loads(GUARDRAIL_STATE.read_text(encoding="utf-8"))
        # Validation minimale
        if not isinstance(data, dict):
            return _fresh_state()
        return data
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Guardrail: état corrompu (%s), réinitialisation", exc)
        return _fresh_state()


def _save_state(state: dict[str, Any]) -> None:
    """Persiste l'état du garde-fou dans le fichier JSON.

    Args:
        state: Dict d'état à sauvegarder.
    """
    try:
        GUARDRAIL_STATE.write_text(
            json.dumps(state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.error("Guardrail: impossible d'écrire l'état (%s)", exc)


def _fresh_state() -> dict[str, Any]:
    """Crée un état frais (première exécution ou réinitialisation).

    Returns:
        Dict d'état initialisé.
    """
    return {
        "schema_version": 1,
        "tracking_date": "",       # AAA-MM-JJ du suivi en cours
        "daily_tx_mb": 0.0,       # MB cumulés aujourd'hui
        "last_tx_bytes": 0,        # Dernière valeur tx_bytes pour le delta
        "last_reset_at": _timestamp_iso(),
        "alerts": [],              # Historique des alertes (max 100)
        "peak_ram_mb": 0.0,        # Pic de RAM observé
        "peak_ram_at": "",
    }


# ===========================================================================
# GARDE-FOU PRINCIPAL
# ===========================================================================


class ResourceGuardrail:
    """Garde-fou coûts/trafic pour MTTV-FLP.

    Surveille la bande passante réseau et la mémoire RAM,
    avec seuils d'alerte paramétrables et persistance.

    Attributes:
        max_traffic_mb: Seuil quotidien de trafic sortant (MB).
        max_ram_mb: Seuil mémoire RAM (MB).
        alert_cooldown_sec: Délai minimal entre deux alertes (secondes).
        state: État persistant chargé depuis guardrail_state.json.
    """

    def __init__(
        self,
        max_traffic_mb: Optional[int] = None,
        max_ram_mb: Optional[int] = None,
        alert_cooldown_sec: Optional[int] = None,
    ) -> None:
        """Initialise le garde-fou avec les seuils configurés.

        Les seuils sont chargés depuis les variables d'environnement
        si non fournis explicitement :
            MAX_DAILY_TRAFFIC_MB, MAX_RAM_MB, ALERT_COOLDOWN_SEC

        Args:
            max_traffic_mb: Seuil quotidien de trafic (MB).
            max_ram_mb: Seuil mémoire RAM (MB).
            alert_cooldown_sec: Délai entre deux alertes (secondes).
        """
        self.max_traffic_mb: int = (
            max_traffic_mb
            if max_traffic_mb is not None
            else _get_env_int("MAX_DAILY_TRAFFIC_MB", _DEFAULT_MAX_TRAFFIC_MB)
        )
        self.max_ram_mb: int = (
            max_ram_mb
            if max_ram_mb is not None
            else _get_env_int("MAX_RAM_MB", _DEFAULT_MAX_RAM_MB)
        )
        self.alert_cooldown_sec: int = (
            alert_cooldown_sec
            if alert_cooldown_sec is not None
            else _get_env_int("ALERT_COOLDOWN_SEC", _DEFAULT_ALERT_COOLDOWN_SEC)
        )
        # Charger l'état persistant
        self.state: dict[str, Any] = _load_state()
        self._check_day_rollover()

        logger.info(
            "Guardrail initialisé — trafic max: %d MB/j, RAM max: %d MB, cooldown: %ds",
            self.max_traffic_mb,
            self.max_ram_mb,
            self.alert_cooldown_sec,
        )

    # ── Gestion du rollover journalier ──────────────────────────────────

    def _check_day_rollover(self) -> None:
        """Vérifie si le jour de suivi a changé et réinitialise si nécessaire.

        Si la date de suivi est différente de la date courante, on réinitialise
        le compteur de trafic quotidien et on archive la journée précédente
        dans l'historique.
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        tracked = self.state.get("tracking_date", "")

        if tracked != today:
            # Archiver la journée précédente si elle existe
            if tracked and self.state.get("daily_tx_mb", 0) > 0:
                archive: list[dict] = self.state.setdefault("daily_archive", [])
                archive.append({
                    "date": tracked,
                    "total_tx_mb": round(self.state.get("daily_tx_mb", 0), 2),
                    "peak_ram_mb": round(self.state.get("peak_ram_mb", 0), 1),
                })
                # Limiter l'archive à 30 jours
                if len(archive) > 30:
                    self.state["daily_archive"] = archive[-30:]

            # Réinitialiser le compteur quotidien
            self.state["tracking_date"] = today
            self.state["daily_tx_mb"] = 0.0
            self.state["last_tx_bytes"] = 0
            self.state["peak_ram_mb"] = 0.0
            self.state["peak_ram_at"] = ""
            logger.info("Guardrail: rollover journalier → %s", today)
            _save_state(self.state)

    # ── Collecte des métriques ──────────────────────────────────────────

    def collect(self) -> dict[str, Any]:
        """Collecte les métriques actuelles de trafic et mémoire.

        Cette méthode est conçue pour être appelée périodiquement
        (par ex. toutes les 60-300 secondes).

        Returns:
            Dict structuré avec :
                "network": { "total_tx_bytes", "daily_tx_mb", "max_traffic_mb", ... }
                "memory": { "used_mb", "total_mb", "percent", ... }
                "state": { "tracking_date", "alerts_count", ... }
        """
        now = _now_epoch()

        # ── Métriques réseau ────────────────────────────────────────────
        current_tx_bytes = _get_total_tx_bytes()
        last_tx_bytes = self.state.get("last_tx_bytes", 0)

        # Delta depuis la dernière collecte
        delta_bytes = 0
        if last_tx_bytes > 0 and current_tx_bytes >= last_tx_bytes:
            delta_bytes = current_tx_bytes - last_tx_bytes
        elif last_tx_bytes == 0 and current_tx_bytes > 0:
            # Première mesure : on initialise sans delta
            pass

        daily_tx_mb = self.state.get("daily_tx_mb", 0.0)
        if delta_bytes > 0:
            daily_tx_mb += delta_bytes / (1024 * 1024)
            self.state["daily_tx_mb"] = round(daily_tx_mb, 4)

        self.state["last_tx_bytes"] = current_tx_bytes

        network_metrics = {
            "total_tx_bytes": current_tx_bytes,
            "delta_bytes_since_last_collect": delta_bytes,
            "daily_tx_mb": round(daily_tx_mb, 2),
            "max_traffic_mb": self.max_traffic_mb,
            "traffic_percent": round(
                (daily_tx_mb / self.max_traffic_mb) * 100, 1
            ) if self.max_traffic_mb > 0 else 0.0,
            "threshold_exceeded": daily_tx_mb > self.max_traffic_mb,
        }

        # ── Métriques mémoire ───────────────────────────────────────────
        mem = _get_memory_mb()
        used_mb = mem.get("used_mb", 0.0)

        # Mettre à jour le pic de RAM
        peak_ram = self.state.get("peak_ram_mb", 0.0)
        if used_mb > peak_ram:
            self.state["peak_ram_mb"] = round(used_mb, 1)
            self.state["peak_ram_at"] = _timestamp_iso()

        memory_metrics = {
            **mem,
            "peak_ram_mb": self.state.get("peak_ram_mb", 0.0),
            "peak_ram_at": self.state.get("peak_ram_at", ""),
            "max_ram_mb": self.max_ram_mb,
            "ram_percent": round(
                (used_mb / self.max_ram_mb) * 100, 1
            ) if self.max_ram_mb > 0 else 0.0,
            "threshold_exceeded": used_mb > self.max_ram_mb,
        }

        # Persister l'état mis à jour
        self.state["last_collect_at"] = _timestamp_iso()
        _save_state(self.state)

        return {
            "timestamp": _timestamp_iso(),
            "uptime_seconds": None,
            "network": network_metrics,
            "memory": memory_metrics,
            "state": {
                "tracking_date": self.state.get("tracking_date", ""),
                "alerts_count": len(self.state.get("alerts", [])),
                "last_collect_at": self.state.get("last_collect_at", ""),
            },
        }

    # ── Vérification des seuils et déclenchement d'alerte ───────────────

    def check_and_alert(self, metrics: dict[str, Any]) -> Optional[str]:
        """Vérifie si les seuils sont dépassés et déclenche une alerte si nécessaire.

        Utilise l'alerte cooldown pour éviter les notifications répétitives.

        Args:
            metrics: Dict retourné par collect().

        Returns:
            Le message d'alerte si déclenchée, None sinon.
        """
        alert_messages: list[str] = []
        now = _now_epoch()
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        # Vérification du trafic réseau
        network = metrics.get("network", {})
        if network.get("threshold_exceeded", False):
            daily_mb = network.get("daily_tx_mb", 0.0)
            max_mb = network.get("max_traffic_mb", self.max_traffic_mb)
            if self._can_alert("traffic"):
                msg = (
                    f"🚨 SEUIL TRAFIC DÉPASSÉ — "
                    f"{daily_mb:.1f} MB / {max_mb} MB (max quotidien) "
                    f"le {today_str}"
                )
                alert_messages.append(msg)
                self._record_alert("traffic", msg, {
                    "daily_tx_mb": daily_mb,
                    "max_traffic_mb": max_mb,
                    "percent": network.get("traffic_percent", 0),
                })

        # Vérification de la mémoire RAM
        memory = metrics.get("memory", {})
        if memory.get("threshold_exceeded", False):
            used_mb = memory.get("used_mb", 0.0)
            max_ram = memory.get("max_ram_mb", self.max_ram_mb)
            if self._can_alert("ram"):
                msg = (
                    f"🚨 SEUIL RAM DÉPASSÉ — "
                    f"{used_mb:.1f} MB / {max_ram} MB (max) "
                    f"le {today_str}"
                )
                alert_messages.append(msg)
                self._record_alert("ram", msg, {
                    "used_mb": used_mb,
                    "max_ram_mb": max_ram,
                    "percent": memory.get("ram_percent", 0),
                    "peak_ram_mb": memory.get("peak_ram_mb", 0),
                })

        # Envoi des alertes via le système de notification
        for alert_msg in alert_messages:
            self._dispatch_alert(alert_msg, metrics)

        _save_state(self.state)
        return "; ".join(alert_messages) if alert_messages else None

    # ── Gestion du cooldown ─────────────────────────────────────────────

    def _can_alert(self, alert_type: str) -> bool:
        """Vérifie si une alerte peut être envoyée (cooldown).

        Args:
            alert_type: "traffic" ou "ram".

        Returns:
            True si l'alerte peut être déclenchée.
        """
        now = _now_epoch()
        last_alert_key = f"last_{alert_type}_alert_ts"
        last_ts = self.state.get(last_alert_key, 0.0)

        if now - last_ts < self.alert_cooldown_sec:
            remaining = int(self.alert_cooldown_sec - (now - last_ts))
            logger.debug(
                "Guardrail: alerte %s en cooldown (%ds restants)",
                alert_type, remaining,
            )
            return False

        self.state[last_alert_key] = now
        return True

    # ── Enregistrement et dispatch des alertes ──────────────────────────

    def _record_alert(self, alert_type: str, message: str, details: dict) -> None:
        """Enregistre une alerte dans l'historique persistant.

        Args:
            alert_type: "traffic" ou "ram".
            message: Message textuel de l'alerte.
            details: Données structurées additionnelles.
        """
        alerts: list[dict] = self.state.setdefault("alerts", [])
        alerts.append({
            "type": alert_type,
            "message": message,
            "details": details,
            "timestamp": _timestamp_iso(),
        })
        # Limiter l'historique à 100 alertes
        if len(alerts) > 100:
            self.state["alerts"] = alerts[-100:]

        logger.warning("Guardrail alert [%s]: %s", alert_type, message)

    def _dispatch_alert(self, message: str, metrics: dict[str, Any]) -> bool:
        """Envoie l'alerte via le système de notification.

        Tente d'importer alert_manager depuis phase4-dormant-nodes.
        Si indisponible, utilise un fallback direct (urllib pour webhook).

        Args:
            message: Message d'alerte formaté.
            metrics: Dict complet des métriques pour les détails.

        Returns:
            True si envoyé avec succès.
        """
        # Tentative 1 : alert_manager (phase4-dormant-nodes)
        try:
            import sys as _sys
            alert_manager_path = PROJECT_ROOT / "phase4-dormant-nodes"
            if alert_manager_path.exists():
                _sys.path.insert(0, str(alert_manager_path))

            from alert_manager import send_alert  # type: ignore[import-untyped]

            sent = send_alert(
                level="WARNING",
                source="resource_guardrail",
                message=message,
                details={
                    "network_daily_mb": metrics.get("network", {}).get("daily_tx_mb"),
                    "max_traffic_mb": metrics.get("network", {}).get("max_traffic_mb"),
                    "ram_used_mb": metrics.get("memory", {}).get("used_mb"),
                    "max_ram_mb": metrics.get("memory", {}).get("max_ram_mb"),
                    "ram_percent": metrics.get("memory", {}).get("percent"),
                },
            )
            if sent:
                logger.info("Guardrail: alerte envoyée via alert_manager")
                return True
        except ImportError:
            logger.debug("Guardrail: alert_manager non disponible")
        except Exception as exc:
            logger.warning("Guardrail: alert_manager échoué (%s)", exc)

        # Tentative 2 : Webhook direct (fallback)
        webhook_url = os.environ.get("ALERT_WEBHOOK_URL", "")
        if webhook_url:
            try:
                import urllib.request as _ur
                import urllib.error as _ue

                payload = json.dumps({
                    "embeds": [{
                        "title": "[WARNING] resource_guardrail",
                        "description": message,
                        "color": 0xF39C12,
                        "timestamp": _timestamp_iso(),
                        "fields": [
                            {"name": "Trafic quotidien", "value": f"{metrics.get('network', {}).get('daily_tx_mb', 'N/A')} MB", "inline": True},
                            {"name": "Max trafic", "value": f"{metrics.get('network', {}).get('max_traffic_mb', 'N/A')} MB", "inline": True},
                            {"name": "RAM utilisée", "value": f"{metrics.get('memory', {}).get('used_mb', 'N/A')} MB", "inline": True},
                            {"name": "Max RAM", "value": f"{metrics.get('memory', {}).get('max_ram_mb', 'N/A')} MB", "inline": True},
                        ],
                        "footer": {"text": "MTTV-FLP · resource_guardrail · sig:0x4D545456"},
                    }]
                }, ensure_ascii=False).encode("utf-8")

                req = _ur.Request(
                    webhook_url,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with _ur.urlopen(req, timeout=15) as resp:
                    if 200 <= resp.status < 300:
                        logger.info("Guardrail: alerte envoyée via webhook direct")
                        return True
            except (_ue.URLError, _ue.HTTPError, OSError) as exc:
                logger.warning("Guardrail: webhook direct échoué (%s)", exc)

        logger.warning(
            "Guardrail: alerte non transmise (aucun canal configuré) | %s",
            message,
        )
        return False

    # ── Exposition des métriques pour l'API ─────────────────────────────

    def get_snapshot(self) -> dict[str, Any]:
        """Retourne un instantané complet des métriques actuelles.

        Conçu pour être intégré dans /health/details.

        Returns:
            Dict complet compatible avec l'endpoint /health/details.
        """
        return self.collect()

    def get_alerts_history(self, limit: int = 10) -> list[dict]:
        """Retourne l'historique des alertes.

        Args:
            limit: Nombre maximum d'alertes à retourner.

        Returns:
            Liste des alertes (les plus récentes en premier).
        """
        alerts = list(reversed(self.state.get("alerts", [])))
        return alerts[:limit]

    def get_daily_archive(self) -> list[dict]:
        """Retourne l'archive des journées précédentes.

        Returns:
            Liste des entrées d'archive (les plus récentes en premier).
        """
        archive = list(reversed(self.state.get("daily_archive", [])))
        return archive


# ===========================================================================
# CLI — Point d'entrée autonome pour tests
# ===========================================================================


def main() -> None:
    """Point d'entrée CLI pour tester le garde-fou.

    Usage:
        python zoo-code/resource_guardrail.py [--thresholds] [--watch]

    Options:
        --watch     Mode surveillance continue (toutes les 60s).
        --status    Affiche l'état actuel et les métriques.
        --reset     Réinitialise l'état persistant.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="MTTV-FLP Resource Guardrail — Garde-fou coûts/trafic",
        epilog="sig:0x4D545456",
    )
    parser.add_argument(
        "--watch", action="store_true",
        help="Mode surveillance continue (toutes les 60s)",
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Affiche l'état actuel et les métriques",
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Réinitialise l'état persistant",
    )
    parser.add_argument(
        "--interval", type=int, default=60,
        help="Intervalle de surveillance en secondes (défaut: 60)",
    )

    args = parser.parse_args()

    # Réinitialisation
    if args.reset:
        if GUARDRAIL_STATE.exists():
            GUARDRAIL_STATE.unlink()
            print(f"✓ État réinitialisé ({GUARDRAIL_STATE})")
        else:
            print("— Aucun état à réinitialiser")
        return

    guard = ResourceGuardrail()
    print(f"\n  {'=' * 55}")
    print(f"  MTTV-FLP RESOURCE GUARDRAIL")
    print(f"  Seuils : trafic={guard.max_traffic_mb} MB/j, RAM={guard.max_ram_mb} MB")
    print(f"  Cooldown : {guard.alert_cooldown_sec}s")
    print(f"  État : {GUARDRAIL_STATE}")
    print(f"  {'=' * 55}")

    # Statut ponctuel
    if args.status:
        metrics = guard.collect()
        print(f"\n  📡 RÉSEAU")
        print(f"     Trafic quotidien : {metrics['network']['daily_tx_mb']:.2f} / {metrics['network']['max_traffic_mb']} MB")
        print(f"     Pourcentage      : {metrics['network']['traffic_percent']:.1f}%")
        print(f"     Seuil dépassé    : {'⚠️ OUI' if metrics['network']['threshold_exceeded'] else '✅ non'}")
        print(f"  💾 MÉMOIRE")
        print(f"     Utilisée         : {metrics['memory']['used_mb']:.1f} / {metrics['memory']['total_mb']:.1f} MB")
        print(f"     Pourcentage      : {metrics['memory']['percent']:.1f}%")
        print(f"     Seuil dépassé    : {'⚠️ OUI' if metrics['memory']['threshold_exceeded'] else '✅ non'}")
        print(f"  📊 ALERTES")
        print(f"     Total            : {metrics['state']['alerts_count']}")
        print()

        # Vérification des seuils
        alert_msg = guard.check_and_alert(metrics)
        if alert_msg:
            print(f"  🚨 ALERTE : {alert_msg}")
        else:
            print(f"  ✅ Aucun seuil dépassé")

    # Mode surveillance
    if args.watch:
        print(f"\n  🔄 Mode surveillance actif (intervalle: {args.interval}s)")
        print(f"  Appuyez sur Ctrl+C pour arrêter\n")
        try:
            while True:
                metrics = guard.collect()
                alert_msg = guard.check_and_alert(metrics)
                ts = metrics["timestamp"]
                tx = metrics["network"]["daily_tx_mb"]
                ram = metrics["memory"]["used_mb"]
                status = "🚨" if alert_msg else "✓"
                print(
                    f"  [{ts}] {status} "
                    f"Trafic: {tx:.1f}/{guard.max_traffic_mb} MB | "
                    f"RAM: {ram:.1f}/{guard.max_ram_mb} MB"
                )
                if alert_msg:
                    print(f"         → {alert_msg}")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n  ⏹ Arrêt demandé")


if __name__ == "__main__":
    main()
