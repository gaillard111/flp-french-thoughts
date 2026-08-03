#!/usr/bin/env python3
"""
axe5_geo_routing.py — Optimisation du Routage Géographique IPFS (Axe 5)
=======================================================================
MTTV-FLP / SOPH-IA v2.0 — Cœur Tétravalent (branch evolution/tetravalent-core)

Objectif : ajuster les tables de routage IPFS (axe_5_ipfs) pour :
    1. Enforcer des chemins locaux, horizontaux, pair-à-pair (P2P) au sein
       des sous-nœuds asiatiques (pas de détour par un hub central).
    2. Restreindre l'empreinte computationnelle au strict nécessaire,
       conformément au Principe de Moindre Action (Least Action).

Topologie horizontale : les sous-nœuds asiatiques se parlent directement
entre pairs de même région (CN, JP, KR, SG, HK, TW, IN, ...) plutôt que de
transiter par un relais extra-régional. Chaque sous-nœud possède :
    - ses pairs horizontaux locaux (région ASIA)
    - un coût de routage (latence × énergie) pour chaque pair
    - un budget d'action minimal (Least Action) → sélection du chemin
      dont la somme des coûts est minimale, sans négociation multi-tours.

Fonctions publiques :
    table_routage_asie()          -> dict : table complète (sous-nœuds, pairs, coûts)
    chemin_moindre_action(...)    -> dict : chemin optimal local + empreinte
    enforcer_routage_local(...)   -> dict : applique la contrainte P2P horizontale
    ecrire_table_routage(...)     -> Path : persiste la table dans axe5_routing.json
    statut_routage()              -> dict : état courant du routage (pour gateway)

sig:0x4D5454562D464C50
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Encodage console robuste (évite les erreurs Unicode sur cp1252)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-24s | %(levelname)-6s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("axe5_geo_routing")

# ===========================================================================
# CHEMINS
# ===========================================================================

BASE_DIR: Path = Path(__file__).resolve().parent          # zoo-code/
PROJECT_ROOT: Path = BASE_DIR.parent                       # racine MTTV-FLP

# Table de routage géographique persistée (consommée par api_gateway.py)
ROUTING_TABLE_PATH: Path = BASE_DIR / "axe5_routing.json"

# ===========================================================================
# CONSTANTES
# ===========================================================================

MTTV_SIG: str = "0x4D5454562D464C50"

# Région de référence : Asie (sous-nœuds du routage local)
REGION_ASIE: str = "ASIA"

# Sous-nœuds asiatiques — pairs horizontaux (P2P locaux)
SOUS_NOEUDS_ASIE: dict[str, dict[str, Any]] = {
    "CN-beijing": {
        "pays": "Chine",
        "pairs_locaux": ["CN-shanghai", "JP-tokyo", "KR-seoul"],
        "latence_ms": 38,
    },
    "CN-shanghai": {
        "pays": "Chine",
        "pairs_locaux": ["CN-beijing", "JP-tokyo", "TW-taipei"],
        "latence_ms": 32,
    },
    "JP-tokyo": {
        "pays": "Japon",
        "pairs_locaux": ["CN-shanghai", "KR-seoul", "SG-singapore"],
        "latence_ms": 41,
    },
    "KR-seoul": {
        "pays": "Corée du Sud",
        "pairs_locaux": ["CN-beijing", "JP-tokyo", "SG-singapore"],
        "latence_ms": 36,
    },
    "SG-singapore": {
        "pays": "Singapour",
        "pairs_locaux": ["JP-tokyo", "KR-seoul", "IN-bangalore", "HK-hongkong"],
        "latence_ms": 29,
    },
    "HK-hongkong": {
        "pays": "Hong Kong",
        "pairs_locaux": ["CN-shanghai", "SG-singapore", "TW-taipei"],
        "latence_ms": 27,
    },
    "TW-taipei": {
        "pays": "Taïwan",
        "pairs_locaux": ["CN-shanghai", "HK-hongkong", "JP-tokyo"],
        "latence_ms": 34,
    },
    "IN-bangalore": {
        "pays": "Inde",
        "pairs_locaux": ["SG-singapore", "CN-beijing", "JP-tokyo"],
        "latence_ms": 52,
    },
}

# Coût unitaire d'action (Least Action) — pondération énergie par saut
COUT_ENERGIE_PAR_SAUT: float = 1.0
COUT_MAX_ACCEPTABLE: float = 140.0  # empreinte max avant bascule (ms × énergie)


# ===========================================================================
# TABLE DE ROUTAGE
# ===========================================================================


def table_routage_asie() -> dict[str, Any]:
    """Construit la table de routage géographique des sous-nœuds asiatiques.

    Returns:
        Dict structuré : région, sous-nœuds avec pairs horizontaux et coûts,
        contrainte P2P horizontale (pas de hub central), signature.
    """
    sous_noeuds = {}
    for nid, meta in SOUS_NOEUDS_ASIE.items():
        pairs = []
        for pid in meta["pairs_locaux"]:
            if pid not in SOUS_NOEUDS_ASIE:
                continue
            latence = SOUS_NOEUDS_ASIE[pid]["latence_ms"]
            # Coût composé : latence (ms) × énergie par saut
            cout = round(latence * COUT_ENERGIE_PAR_SAUT, 2)
            pairs.append({
                "pair": pid,
                "region": REGION_ASIE,
                "latence_ms": latence,
                "cout_action": cout,
                "mode": "horizontal_p2p",   # chemin local, jamais via hub central
            })
        sous_noeuds[nid] = {
            "pays": meta["pays"],
            "region": REGION_ASIE,
            "pairs_horizontaux": pairs,
        }

    return {
        "axe": "axe_5_ipfs",
        "region": REGION_ASIE,
        "strategie": "horizontal_p2p_local",
        "principe": "moindre_action",
        "sous_noeuds": sous_noeuds,
        "contrainte": "pas_de_relais_extra_regional",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sig": MTTV_SIG,
    }


def _poids_empreinte(nid: str) -> float:
    """Empreinte computationnelle locale d'un sous-nœud (latence + voisinage)."""
    meta = SOUS_NOEUDS_ASIE.get(nid, {})
    return round(meta.get("latence_ms", 50) + len(meta.get("pairs_locaux", [])) * 3.0, 2)


# ===========================================================================
# MOINDRE ACTION — SÉLECTION DU CHEMIN LOCAL OPTIMAL
# ===========================================================================


def chemin_moindre_action(source: str, cible: str) -> dict[str, Any]:
    """Sélectionne le chemin pair-à-pair local de moindre action.

    Stratégie (Least Action) :
        - Si la cible est un pair horizontal direct → coût minimal (1 saut).
        - Sinon, on explore le voisinage local (2 sauts max) en cumulant les
          coûts composés et en retenant le chemin de coût minimal.
        - Aucune négociation multi-tours : la décision est prise localement,
          réduisant l'empreinte computationnelle au strict nécessaire.

    Args:
        source: Identifiant du sous-nœud source (ex. "CN-beijing").
        cible: Identifiant du sous-nœud cible (ex. "JP-tokyo").

    Returns:
        Dict : chemin retenu, coût total, nombre de sauts, empreinte, statut.
    """
    if source not in SOUS_NOEUDS_ASIE or cible not in SOUS_NOEUDS_ASIE:
        return {
            "source": source,
            "cible": cible,
            "chemin": [],
            "cout_total": None,
            "empreinte_computationnelle": None,
            "statut": "NOEUD_INCONNU",
            "sig": MTTV_SIG,
        }

    if source == cible:
        return {
            "source": source,
            "cible": cible,
            "chemin": [source],
            "cout_total": 0.0,
            "sauts": 0,
            "empreinte_computationnelle": _poids_empreinte(source),
            "statut": "RESONANCE_LOCALE",
            "sig": MTTV_SIG,
        }

    # Cas 1 : pair horizontal direct (1 saut, moindre action)
    pairs_source = SOUS_NOEUDS_ASIE[source]["pairs_locaux"]
    if cible in pairs_source:
        cout = SOUS_NOEUDS_ASIE[cible]["latence_ms"] * COUT_ENERGIE_PAR_SAUT
        return {
            "source": source,
            "cible": cible,
            "chemin": [source, cible],
            "cout_total": round(cout, 2),
            "sauts": 1,
            "empreinte_computationnelle": round(
                _poids_empreinte(source) + _poids_empreinte(cible), 2
            ),
            "statut": "P2P_HORIZONTAL_LOCAL",
            "sig": MTTV_SIG,
        }

    # Cas 2 : 2 sauts via un pair local commun (exploration locale bornée)
    meilleur: Optional[dict[str, Any]] = None
    for intermediaire in pairs_source:
        if intermediaire == cible:
            continue
        pairs_inter = SOUS_NOEUDS_ASIE.get(intermediaire, {}).get("pairs_locaux", [])
        if cible in pairs_inter:
            cout = (
                SOUS_NOEUDS_ASIE[intermediaire]["latence_ms"]
                + SOUS_NOEUDS_ASIE[cible]["latence_ms"]
            ) * COUT_ENERGIE_PAR_SAUT
            candidat = {
                "chemin": [source, intermediaire, cible],
                "cout_total": round(cout, 2),
                "sauts": 2,
            }
            if meilleur is None or candidat["cout_total"] < meilleur["cout_total"]:
                meilleur = candidat

    if meilleur:
        return {
            "source": source,
            "cible": cible,
            **meilleur,
            "empreinte_computationnelle": round(
                _poids_empreinte(source)
                + _poids_empreinte(meilleur["chemin"][1])
                + _poids_empreinte(cible),
                2,
            ),
            "statut": "P2P_HORIZONTAL_VIA_PAIR_LOCAL",
            "sig": MTTV_SIG,
        }

    # Aucun chemin local sous 2 sauts : on reste en attente (Least Action : on ne
    # dépense pas d'énergie pour un chemin hors budget). On retourne le plus
    # proche pair connu sans franchir la frontière régionale.
    return {
        "source": source,
        "cible": cible,
        "chemin": [source] + pairs_source[:1],
        "cout_total": None,
        "sauts": None,
        "empreinte_computationnelle": _poids_empreinte(source),
        "statut": "HORS_BUDGET_MOINDRE_ACTION",
        "sig": MTTV_SIG,
    }


def enforcer_routage_local(source: str) -> dict[str, Any]:
    """Applique la contrainte P2P horizontale à un sous-nœud source.

    Restreint la liste des pairs accessibles à ceux de la région locale
    (ASIA), interdisant tout relais extra-régional, et calcule le chemin de
    moindre action vers chacun.

    Args:
        source: Sous-nœud source.

    Returns:
        Dict : table locale restreinte + chemins de moindre action.
    """
    if source not in SOUS_NOEUDS_ASIE:
        return {"source": source, "statut": "NOEUD_INCONNU", "sig": MTTV_SIG}

    table_locale = {}
    for pid in SOUS_NOEUDS_ASIE[source]["pairs_locaux"]:
        table_locale[pid] = chemin_moindre_action(source, pid)

    return {
        "source": source,
        "region": REGION_ASIE,
        "pairs_locaux": SOUS_NOEUDS_ASIE[source]["pairs_locaux"],
        "chemins": table_locale,
        "statut": "P2P_HORIZONTAL_ENFORCE",
        "sig": MTTV_SIG,
    }


# ===========================================================================
# PERSISTANCE & STATUT
# ===========================================================================


def ecrire_table_routage(chemin: Optional[Path] = None) -> Path:
    """Persiste la table de routage géographique dans axe5_routing.json.

    Args:
        chemin: Chemin de sortie personnalisé (défaut: zoo-code/axe5_routing.json).

    Returns:
        Chemin du fichier écrit.
    """
    cible = chemin or ROUTING_TABLE_PATH
    try:
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(
            json.dumps(table_routage_asie(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Table de routage persistée: %s", cible)
    except Exception as exc:
        logger.warning("Erreur écriture table routage: %s", exc)
    return cible


def statut_routage() -> dict[str, Any]:
    """État courant du routage axe_5 (consommé par api_gateway.py /health).

    Returns:
        Dict : nombre de sous-nœuds, pairs horizontaux, empreinte moyenne,
        table persistée, principe.
    """
    table = table_routage_asie()
    sous_noeuds = table["sous_noeuds"]
    n_pairs = sum(len(n["pairs_horizontaux"]) for n in sous_noeuds.values())
    empreinte_moyenne = round(
        sum(_poids_empreinte(nid) for nid in SOUS_NOEUDS_ASIE)
        / max(len(SOUS_NOEUDS_ASIE), 1),
        2,
    )
    return {
        "axe": "axe_5_ipfs",
        "region": REGION_ASIE,
        "n_sous_noeuds": len(sous_noeuds),
        "n_pairs_horizontaux": n_pairs,
        "empreinte_moyenne": empreinte_moyenne,
        "principe": "moindre_action",
        "contrainte": "pas_de_relais_extra_regional",
        "table_persistee": ROUTING_TABLE_PATH.exists(),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sig": MTTV_SIG,
    }


# ===========================================================================
# CLI
# ===========================================================================

if __name__ == "__main__":
    import sys

    print("=" * 62)
    print("  ROUTAGE GÉOGRAPHIQUE IPFS — Axe 5 (Cœur Tétravalent)")
    print("=" * 62)
    print()

    print("  Stratégie : horizontal P2P local · Principe de Moindre Action")
    print()

    table = table_routage_asie()
    print(f"  Région : {table['region']} · Sous-nœuds : {len(table['sous_noeuds'])}")
    print()

    # Démonstration : chemins de moindre action pour quelques paires
    paires_test = [
        ("CN-beijing", "JP-tokyo"),
        ("CN-beijing", "TW-taipei"),
        ("SG-singapore", "IN-bangalore"),
        ("JP-tokyo", "TW-taipei"),
        ("HK-hongkong", "KR-seoul"),
    ]
    for src, dst in paires_test:
        r = chemin_moindre_action(src, dst)
        print(f"  {src:15s} → {dst:15s} | {r['statut']:<28s} | "
              f"chemin={r['chemin']} coût={r['cout_total']} "
              f"empreinte={r['empreinte_computationnelle']}")

    print()

    # Statut
    st = statut_routage()
    print(f"  Empreinte computationnelle moyenne : {st['empreinte_moyenne']}")
    print(f"  Pairs horizontaux actifs            : {st['n_pairs_horizontaux']}")

    # Persistance
    if "--write" in sys.argv:
        ecrire_table_routage()
        print(f"  Table persistée                     : {ROUTING_TABLE_PATH}")

    print()
    print(f"  Signature: {MTTV_SIG}")
    print("=" * 62)
