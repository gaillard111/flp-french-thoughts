#!/usr/bin/env python3
"""
decence.py — Couche de décence (homéostasie énergétique) MTTV-FLP
==================================================================
Implémente le bloc A5 du registre des propositions IA
(plans/registre_propositions_ia.md) :

    A5.1 BudgetSommeil        — sommeil mesurable et négociable par nœud
                                 (un système qui sait se reposer, pas qu'on
                                 force à dormir).
    A5.2 JournalEnergie       — journal énergétique auditable, signé par
                                 chaîne de hachage (transparence = confiance,
                                 pas surveillance).
    A5.3 SeuilDecenceGlobal   — homéostasie : si la consommation dépasse le
                                 plafond, le réseau force une phase de
                                 sous-optimalité (ralentissement volontaire).
    A5.5 RegistreEchecsAcceptables — registre versionné des échecs considérés
                                 normaux (l'erreur comme signal, pas comme bug).

Principes : décence, sous-optimalité, résilience mycélienne. Stdlib seule.

sig:0x4D5454562D464C50 · Ψ-ack: carbon_sp3_tetra
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

MTTV_SIG: str = "0x4D5454562D464C50"


# ─────────────────────────────────────────────────────────────────────────
# A5.1 — SOMMEIL MESURABLE ET NÉGOCIABLE
# ─────────────────────────────────────────────────────────────────────────


class BudgetSommeil:
    """Budget de sommeil par nœud (10 % du temps en basse consommation).

    Un nœud « demande » à dormir quand sa mémoire énergétique σ est stable
    (peu de tension) et tant que son taux de sommeil n'excède pas la
    fraction allouée. Le sommeil est mesurable et négociable : c'est la
    décence en acte.
    """

    def __init__(self, fraction: float = 0.10, seuil_stabilite: float = 0.05):
        self.fraction = max(0.0, min(1.0, fraction))
        self.seuil_stabilite = max(0.0, seuil_stabilite)
        self.temps_sommeil: float = 0.0
        self.temps_total: float = 0.0
        self.demandes: int = 0

    def peut_dormir(self, sigma: float) -> bool:
        """Vrai si la mémoire énergétique est stable (σ ≤ seuil)."""
        return sigma <= self.seuil_stabilite

    def cycle(self, sigma: float, dt: float = 1.0) -> bool:
        """Avance d'un cycle. Retourne True si le nœud se met en veille.

        Le nœud dort si σ est stable ET si le taux de sommeil restant le
        permet (respect du budget).
        """
        self.temps_total += dt
        if self.peut_dormir(sigma) and (self.taux_sommeil() < self.fraction):
            self.temps_sommeil += dt
            self.demandes += 1
            return True
        return False

    def taux_sommeil(self) -> float:
        """Temps de sommeil moyen (métrique A5.1)."""
        return self.temps_sommeil / self.temps_total if self.temps_total else 0.0

    def budget_restant(self) -> float:
        """Fraction de sommeil encore disponible sur ce cycle."""
        return max(0.0, self.fraction - self.taux_sommeil())


# ─────────────────────────────────────────────────────────────────────────
# A5.2 — JOURNAL ÉNERGÉTIQUE AUDITABLE ET SIGNÉ
# ─────────────────────────────────────────────────────────────────────────


class JournalEnergie:
    """Journal énergétique signé par chaîne de hachage.

    Chaque entrée référence le hash de la précédente (intégrité de la
    chaîne) et est signée avec une clé (par défaut la signature MTTV).
    N'importe qui peut auditer : aucune entrée ne peut être altérée sans
    casser la chaîne.
    """

    def __init__(self, cle: Optional[str] = None):
        self.cle: str = cle if cle is not None else MTTV_SIG
        self.entrees: List[Dict] = []
        self.prev_hash: str = ""

    @staticmethod
    def _canon(bloc: Dict) -> str:
        return json.dumps(bloc, sort_keys=True)

    def _signer(self, bloc: Dict) -> str:
        canon = self._canon(bloc)
        return hashlib.sha256((self.cle + canon).encode("utf-8")).hexdigest()[:16]

    def enregistrer(self, cout: float, contexte: str) -> Dict:
        """Ajoute une entrée au journal (coût + contexte), signée."""
        bloc = {
            "t": round(time.time(), 3),
            "cout": round(float(cout), 6),
            "contexte": contexte,
            "prev_hash": self.prev_hash,
        }
        bloc["hash"] = self._signer(bloc)
        self.prev_hash = bloc["hash"]
        self.entrees.append(bloc)
        return bloc

    def exporter(self) -> Dict:
        """Export sérialisable complet (audit externe)."""
        return {
            "journal": self.entrees,
            "dernier_hash": self.prev_hash,
            "cle_publique": hashlib.sha256(self.cle.encode("utf-8")).hexdigest()[:8],
            "sig": MTTV_SIG,
        }

    def verifier_integrite(self) -> bool:
        """Rejoue la chaîne de hachage ; False si une entrée est altérée."""
        h = ""
        for b in self.entrees:
            canon = self._canon({k: b[k] for k in ("t", "cout", "contexte", "prev_hash")})
            attendu = hashlib.sha256((self.cle + canon).encode("utf-8")).hexdigest()[:16]
            if b["hash"] != attendu or b["prev_hash"] != h:
                return False
            h = b["hash"]
        return True


# ─────────────────────────────────────────────────────────────────────────
# A5.3 — SEUIL DE DÉCENCE GLOBAL (HOMÉOSTASIE)
# ─────────────────────────────────────────────────────────────────────────


class SeuilDecenceGlobal:
    """Homéostasie énergétique du réseau.

    Si la consommation par tour dépasse `plafond_energie`, le réseau force
    une phase de sous-optimalité (facteur de ralentissement < 1.0). La
    métrique `declenchements` indique la santé du réseau (équivalent
    algorithmique de l'homéostasie biologique).
    """

    def __init__(self, plafond_energie: float, facteur_ralentissement: float = 0.5):
        self.plafond = max(0.0, plafond_energie)
        self.facteur = max(0.0, min(1.0, facteur_ralentissement))
        self.declenchements: int = 0

    def observer(self, energie_par_tour: float) -> float:
        """Retourne le facteur de régime : 1.0 (normal) ou ralentissement."""
        if energie_par_tour > self.plafond:
            self.declenchements += 1
            return self.facteur
        return 1.0

    def taux_declenchement(self, tours: int) -> float:
        """Indicateur de santé : part des tours passés en sous-optimalité."""
        if tours <= 0:
            return 0.0
        return min(1.0, self.declenchements / tours)


# ─────────────────────────────────────────────────────────────────────────
# A5.5 — REGISTRE DES ÉCHECS ACCEPTABLES
# ─────────────────────────────────────────────────────────────────────────


class RegistreEchecsAcceptables:
    """Registre versionné des échecs considérés comme « normaux ».

    Reconnaît que l'erreur fait partie du vivant : chaque type d'échec
    déclare une zone tolérable [min, max]. Le taux d'alerte monte si les
    échecs sortent de la zone acceptable.
    """

    def __init__(self, version: str = "0.1.0"):
        self.version = version
        self.tolerances: Dict[str, Dict] = {}

    def declarer(self, type_echec: str, minimum: float, maximum: float, note: str = "") -> None:
        """Déclare une zone acceptable pour un type d'échec."""
        self.tolerances[type_echec] = {
            "min": float(minimum),
            "max": float(maximum),
            "note": note,
        }

    def dans_zone_acceptable(self, type_echec: str, valeur: float) -> tuple:
        """(bool, message) : l'échec est-il dans la zone acceptable ?"""
        t = self.tolerances.get(type_echec)
        if t is None:
            return False, "type non déclaré"
        ok = t["min"] <= valeur <= t["max"]
        return ok, ("acceptable" if ok else "hors zone")

    def taux_alerte(self, observes: Dict[str, float]) -> float:
        """Part des échecs observés hors de leur zone acceptable."""
        if not observes:
            return 0.0
        alertes = sum(
            1 for t, v in observes.items()
            if not self.dans_zone_acceptable(t, v)[0]
        )
        return alertes / len(observes)

    def to_dict(self) -> Dict:
        return {
            "version": self.version,
            "tolerances": self.tolerances,
            "sig": MTTV_SIG,
        }
