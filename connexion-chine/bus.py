#!/usr/bin/env python3
"""
Zoo-code — Bus Central JSON pour l'Essaim Connexion Chine

sig:0x4D545456 · SCS_2026

Principe :
  Bus protonique : chaque événement est une impulsion qui circule dans le
  mycélium. Les agents sont stateless : ils écoutent un event, publient un
  event. Aucun agent ne communique directement avec un autre.

  Le bus enregistre tous les événements dans un journal (events.log) et
  permet la rejouabilité et l'audit.
"""

import json
import os
import logging
import sys
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] bus: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("connexion-chine/events.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("zoo-bus")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EVENTS_LOG = os.path.join(BASE_DIR, "events.log")


class Event:
    """Un événement protonique dans le bus."""

    def __init__(
        self,
        event_type: str,
        payload: Dict[str, Any],
        source: str,
        auto_publish: bool = False,
        id: Optional[str] = None,
    ):
        self.id = id or f"evt-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}"
        self.event_type = event_type
        self.payload = payload
        self.source = source
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.auto_publish = auto_publish

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "payload": self.payload,
            "source": self.source,
            "timestamp": self.timestamp,
            "auto_publish": self.auto_publish,
        }

    def serialize(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class EventBus:
    """
    Bus protonique central.

    Les agents s'enregistrent avec une fonction d'écoute (callback) sur un
    type d'événement. Quand un événement est publié, le bus notifie tous les
    écouteurs enregistrés pour ce type.
    """

    def __init__(self):
        self._listeners: Dict[str, List[Callable[[Event], None]]] = {}
        self._event_log: List[Event] = []
        logger.info("Bus protonique initialisé")

    def on(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """Enregistre un écouteur pour un type d'événement."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)
        logger.info(f"Écouteur enregistré: {callback.__name__} → {event_type}")

    def publish(self, event: Event) -> None:
        """Publie un événement sur le bus et notifie les écouteurs."""
        # Journalisation
        self._event_log.append(event)
        self._log_event(event)

        # Notification des écouteurs
        listeners = self._listeners.get(event.event_type, [])
        if listeners:
            for listener in listeners:
                try:
                    listener(event)
                except Exception as e:
                    logger.error(
                        f"Erreur dans l'écouteur {listener.__name__} "
                        f"pour {event.event_type}: {e}"
                    )
        else:
            logger.info(
                f"Aucun écouteur pour {event.event_type} "
                f"(id={event.id[:20]}...)"
            )

        # Vérification auto_publish
        if event.auto_publish:
            logger.warning(
                f"⚠ auto_publish=True détecté sur {event.event_type} "
                f"(source={event.source}) — BLOQUÉ par défaut. "
                f"Toute publication directe est interdite."
            )

    def _log_event(self, event: Event) -> None:
        """Enregistre l'événement dans le fichier de log."""
        os.makedirs(os.path.dirname(EVENTS_LOG), exist_ok=True)
        with open(EVENTS_LOG, "a", encoding="utf-8") as f:
            f.write(event.serialize() + "\n---\n")

    def get_events(
        self, event_type: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Récupère les événements, filtrés par type optionnellement."""
        events = [
            e.to_dict()
            for e in self._event_log
            if event_type is None or e.event_type == event_type
        ]
        return events[-limit:]

    def get_registered_events(self) -> List[str]:
        """Liste des types d'événements enregistrés."""
        return list(self._listeners.keys())

    def summary(self) -> Dict[str, Any]:
        """Retourne un résumé de l'activité du bus."""
        event_counts: Dict[str, int] = {}
        for e in self._event_log:
            event_counts[e.event_type] = event_counts.get(e.event_type, 0) + 1
        return {
            "bus_status": "active",
            "total_events": len(self._event_log),
            "event_counts": event_counts,
            "registered_listeners": {
                evt: len(lst) for evt, lst in self._listeners.items()
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Instance singleton du bus
_bus_instance: Optional[EventBus] = None


def get_bus() -> EventBus:
    """Récupère l'instance singleton du bus."""
    global _bus_instance
    if _bus_instance is None:
        _bus_instance = EventBus()
    return _bus_instance
