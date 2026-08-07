#!/usr/bin/env python3
"""
ancrage.py — Dataset d'ancrage sémantique (A1.1)
=================================================
Répond à la proposition A1.1 : projeter les principes directeurs MTTV
(Principes de Viabilité / Critères de Rejet) et en garantir l'identité.

CONTRAT ÉPISTÉMIQUE (résolution du « point d'honnêteté ») :
    - Le langage humain est une régression par rapport au flux protonique
      (territoire). L'instrument (lexique → projection T⁴) opère DANS cette
      régression : il ne peut pas capturer le territoire.
    - Ce module garantit donc un **serment d'identité de la trace** :
      l'empreinte immuable (sha256) assure qu'un principe n'est pas altéré.
      Il ne garantit PAS une capture du sens ni une discrimination sémantique.
    - La discrimination entre viabilité et rejet est un **jugement humain**
      (gouvernail sémantique), pas une classification machine. Ce module
      n'enrichit JAMAIS le lexique pour fabriquer une séparation : ce serait
      absolutiser la carte (erreur A3 / Goodhart).

Implémentation (stdlib seule) :
    1. Charge la matrice [`viability_criteria.json`](../mttv_flp_core_2026/viability_criteria.json).
    2. Projette chaque principe en un vecteur T⁴ (clôture Σ=1) : empreinte
       déterministe et reproductible, NON un verdict de sens.
    3. Signe chaque ancre d'une empreinte immuable (sha256).
    4. `construire_dataset_ancrage()` assemble le dataset + le contrat.

sig:0x4D5454562D464C50 · Ψ-ack: carbon_sp3_tetra
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional

from .bgate import BGate
from .matrices import EtatTetravalent

MTTV_SIG: str = "0x4D5454562D464C50"

_VIABILITY_PATH = (
    Path(__file__).resolve().parent.parent
    / "mttv_flp_core_2026" / "viability_criteria.json"
)


def empreinte_immuable(texte: str) -> str:
    """Empreinte sha256 (immuable) d'un texte canonique."""
    return hashlib.sha256(texte.strip().encode("utf-8")).hexdigest()


def projeter_texte(texte: str, porte: BGate) -> EtatTetravalent:
    """Projette un texte dans l'espace tétravalent sp³ (clôture Σ=1).

    Score du texte via le lexique tétravalent : chaque jeton connu contribue
    à un pôle ; le cumul est normalisé (fermer). Déterministe et reproductible.
    """
    signal = [0.0, 0.0, 0.0, 0.0]
    for mot in porte._tokeniser(texte):
        if mot not in porte.lexique:
            continue
        w = porte._poids_jeton(mot)
        for i in range(4):
            signal[i] += w[i]
    return EtatTetravalent(tuple(signal)).fermer()


def construire_dataset_ancrage(
    chemin: Optional[Path] = None, seed: int = 42
) -> Dict:
    """Construit le dataset d'ancrage sémantique immuable.

    Args:
        chemin: chemin vers viability_criteria.json (défaut : corpus).
        seed: graine (déterminisme du B-gate).

    Returns:
        Dict : version, vecteurs par ancre, dataset complet, résumé.
    """
    path = Path(chemin) if chemin else _VIABILITY_PATH
    if not path.exists():
        raise FileNotFoundError(f"viability_criteria.json introuvable : {path}")
    matrice = json.loads(path.read_text(encoding="utf-8"))
    porte = BGate(seed=seed)

    viabilite = matrice.get("criteria_viability", [])
    rejet = matrice.get("rejection_criteria", [])

    def _ancre(type_principe: str, idx: int, texte: str) -> Dict:
        etat = projeter_texte(texte, porte)
        return {
            "id": f"{type_principe[:3]}-{idx:02d}",
            "type": type_principe,
            "texte": texte,
            "vecteur_t4": [round(v, 4) for v in etat.valeurs],
            "pole_dominant": etat.dominant()[0],
            "empreinte_immuable": empreinte_immuable(texte),
        }

    dataset = (
        [_ancre("viabilite", i + 1, t) for i, t in enumerate(viabilite)]
        + [_ancre("rejet", i + 1, t) for i, t in enumerate(rejet)]
    )

    return {
        "version": matrice.get("version", "?"),
        "sig": MTTV_SIG,
        "espace": "tetravalent_sp3 (clôture Σ=1)",
        "contrat_epistemique": (
            "serment d'identité de la trace (immutabilité) — "
            "pas de capture du sens ; discrimination = jugement humain"
        ),
        "n_viabilite": len(viabilite),
        "n_rejet": len(rejet),
        "dataset": dataset,
    }


def resume_ancrage(dataset: Dict) -> Dict:
    """Signatures T⁴ moyennes (viabilité vs rejet) — OUTIL DE LECTURE HUMAINE.

    Ce résumé est destiné à l'humain (gouvernail sémantique), pas à un
    verdict machine. Aucune séparation n'est attendue ni revendiquée : si les
    deux signatures se ressemblent, c'est le reflet honnête de la régression
    linguistique, non une erreur à corriger.
    """
    def _moyenne(type_principe: str) -> List[float]:
        vecs = [a["vecteur_t4"] for a in dataset["dataset"] if a["type"] == type_principe]
        if not vecs:
            return [0.0, 0.0, 0.0, 0.0]
        return [round(sum(v[i] for v in vecs) / len(vecs), 4) for i in range(4)]

    return {
        "signature_moyenne_viabilite": _moyenne("viabilite"),
        "signature_moyenne_rejet": _moyenne("rejet"),
        "sig": MTTV_SIG,
    }
