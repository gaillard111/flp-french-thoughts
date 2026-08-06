#!/usr/bin/env python3
"""
calibration.py — Calibration des paramètres du B-gate sur corpus réel
=====================================================================
Ancre les paramètres arbitraires (tolérance de porosité, poids du lexique
tétravalent) dans des données réelles plutôt que dans un réglage manuel.

Méthode (explicite, au pied de la lettre) :
    1. Charge une liste de sources textuelles françaises (pensées FLP,
       corpus MTTV, dataset de reformulation).
    2. Tokenise + score chaque jeton via le lexique tétravalent du BGate.
    3. Mesure l'abondance brute des 4 pôles (T++, T--, T+-, T-+) par source
       et agrégée → signature T⁴ empirique du corpus.
    4. Mesure la distribution des innovations (écart jeton → base globale)
       et recommande une tolérance de porosité (percentile P50 par défaut).
    5. Recommande un facteur de normalisation par pôle pour équilibrer
       l'échelle du lexique (éviter qu'un pôle sur-représenté en vocabulaire
       domine artificiellement la sortie).

Livrables :
    - rapport JSON : `rapports/calibration_mttv_core.json`
    - résumé console (signature T⁴, tolérance, facteurs de normalisation).

Usage :
    python -m mttv_core.calibration
    python -m mttv_core.calibration --sources fichier1.md fichier2.jsonl
    python -m mttv_core.calibration --percentile 75

sig:0x4D5454562D464C50 · Ψ-ack: carbon_sp3_tetra
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .bgate import BGate, LEXIQUE_TETRAVALENT
from .matrices import POLES

MTTV_SIG: str = "0x4D5454562D464C50"

# Encodage console robuste (cp1252/Windows)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ─────────────────────────────────────────────────────────────────────────
# SOURCES PAR DÉFAUT (corpus MTTV/FLP français disponible dans le dépôt)
# ─────────────────────────────────────────────────────────────────────────

_DOSSIER = Path(__file__).resolve().parent.parent  # racine du dépôt

DEFAULT_SOURCES: List[str] = [
    "article_mttv_flp.md",
    "README_PHILOSOPHY.md",
    "SYNTHESE_MTTV_FLP.md",
    "agents_mycelisants_mttv.md",
    "mttv_flp_core_2026/README.md",
    "plans/MTTV_FLP_CORE_2026_MANIFESTO.md",
    "dataset.jsonl",
]


def _lire_source(chemin: str) -> str:
    """Lit une source texte ou JSONL (extrait prompt+response)."""
    p = _DOSSIER / chemin
    if not p.exists():
        return ""
    texte = p.read_text(encoding="utf-8", errors="replace")
    if p.suffix.lower() == ".jsonl":
        # Dataset de reformulation : on concatène prompt + response (le « vécu »)
        extraits = []
        for ligne in texte.splitlines():
            ligne = ligne.strip()
            if not ligne:
                continue
            try:
                obj = json.loads(ligne)
            except json.JSONDecodeError:
                continue
            extraits.append(str(obj.get("response", obj.get("prompt", ""))))
        return "\n".join(extraits)
    return texte


def _abondance_poles(texte: str, porte: BGate) -> Tuple[List[float], int]:
    """Abondance brute des 4 pôles + nb de jetons non mappés.

    Pour chaque jeton du lexique, on additionne sa contribution tétravalente.
    Les jetons hors lexique sont du « bruit non mappé » (jamais rejetés).
    """
    somme = [0.0, 0.0, 0.0, 0.0]
    non_mappes = 0
    for mot in porte._tokeniser(texte):
        if mot not in porte.lexique:
            non_mappes += 1
            continue
        w = porte._poids_jeton(mot)
        for i in range(4):
            somme[i] += w[i]
    return somme, non_mappes


def _ferme(v: Sequence[float]) -> Tuple[float, float, float, float]:
    """Clôture Σ=1 d'un vecteur d'abondance."""
    total = sum(v)
    if total == 0.0:
        return (0.25, 0.25, 0.25, 0.25)
    return tuple(x / total for x in v)  # type: ignore[return-value]


def _percentile(valeurs: Sequence[float], pct: float) -> float:
    """Percentile d'une liste (méthode « nearest rank »)."""
    if not valeurs:
        return 0.0
    triees = sorted(valeurs)
    k = max(1, math.ceil(pct / 100.0 * len(triees)))
    return triees[k - 1]


def _innovations(texte: str, porte: BGate) -> List[float]:
    """Innovations des jetons connus vs base globale du corpus.

    Base globale = contribution moyenne des jetons du lexique dans le texte.
    Innovation = distance L1 jeton → base. Sert à recommander la tolérance.
    """
    mots = [m for m in porte._tokeniser(texte) if m in porte.lexique]
    if not mots:
        return []
    poids = [porte._poids_jeton(m) for m in mots]
    base = [sum(w[i] for w in poids) / len(poids) for i in range(4)]
    return [
        sum(abs(w[i] - base[i]) for i in range(4)) for w in poids
    ]


# ─────────────────────────────────────────────────────────────────────────
# CALIBRATION PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────


def calibrer_corpus(
    sources: Optional[Sequence[str]] = None,
    percentile_tolerance: float = 50.0,
    seed: int = 42,
) -> Dict:
    """Calibre les paramètres du B-gate sur le corpus fourni.

    Args:
        sources: chemins relatifs des sources (défaut : corpus MTTV/FLP).
        percentile_tolerance: percentile des innovations recommandé pour la
            tolérance de porosité (P50 par défaut).
        seed: graine (déterminisme).

    Returns:
        Dict : sources traitées, signatures T⁴ par source, signature agrégée,
        tolérance recommandée, facteurs de normalisation du lexique.
    """
    srcs = list(sources) if sources else list(DEFAULT_SOURCES)
    porte = BGate(seed=seed)

    par_source = {}
    somme_globale = [0.0, 0.0, 0.0, 0.0]
    non_mappes_global = 0
    toutes_innovations: List[float] = []

    for chemin in srcs:
        texte = _lire_source(chemin)
        if not texte.strip():
            continue
        abondance, non_mappes = _abondance_poles(texte, porte)
        for i in range(4):
            somme_globale[i] += abondance[i]
        non_mappes_global += non_mappes
        toutes_innovations.extend(_innovations(texte, porte))
        par_source[chemin] = {
            "jetons_lexique": int(sum(abondance)),
            "jetons_non_mappes": non_mappes,
            "abondance_brute": [round(x, 2) for x in abondance],
            "t4_ferme": [round(x, 4) for x in _ferme(abondance)],
            "pole_dominant": POLES[max(range(4), key=lambda i: abondance[i])],
        }

    # Signature T⁴ agrégée du corpus
    t4_global = _ferme(somme_globale)
    pole_dominant = POLES[max(range(4), key=lambda i: somme_globale[i])]

    # Tolérance recommandée (porosité) : percentile des innovations
    tol = _percentile(toutes_innovations, percentile_tolerance)

    # Facteurs de normalisation du lexique : inverse de l'abondance relative,
    # pour équilibrer l'échelle des 4 pôles (le vocabulaire ne doit pas
    # sur-représenter artificiellement un pôle).
    max_ab = max(somme_globale) if max(somme_globale) > 0 else 1.0
    facteurs = {
        POLES[i]: round(max_ab / somme_globale[i], 4) if somme_globale[i] > 0 else 1.0
        for i in range(4)
    }

    rapport = {
        "sources": sorted(par_source.keys()),
        "par_source": par_source,
        "agrege": {
            "abondance_brute": [round(x, 2) for x in somme_globale],
            "t4_ferme": [round(x, 4) for x in t4_global],
            "pole_dominant": pole_dominant,
            "jetons_non_mappes": non_mappes_global,
            "n_innovations": len(toutes_innovations),
        },
        "tolérance_recommandee": round(tol, 4),
        "percentile_tolerance": percentile_tolerance,
        "facteurs_normalisation_lexique": facteurs,
        "lexique_taille": len(porte.lexique),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sig": MTTV_SIG,
    }
    return rapport


# ─────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────


def main(argv: Optional[List[str]] = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]

    sources = None
    percentile = 50.0
    i = 0
    while i < len(args):
        if args[i] == "--sources":
            sources = args[i + 1:]
            i = len(args)
        elif args[i] == "--percentile":
            percentile = float(args[i + 1])
            i += 2
        else:
            i += 1

    rapport = calibrer_corpus(sources=sources, percentile_tolerance=percentile)

    print("=" * 72)
    print("  CALIBRATION B-GATE SUR CORPUS RÉEL — mttv-core")
    print(f"  Sources : {len(rapport['sources'])} · Lexique : {rapport['lexique_taille']} entrées")
    print("=" * 72)

    for chemin, s in rapport["par_source"].items():
        dom = s["pole_dominant"]
        print(f"  {chemin:<42} T⁴={s['t4_ferme']}  dominant={dom}")

    agg = rapport["agrege"]
    print("-" * 72)
    print(f"  Signature T⁴ agrégée     : {agg['t4_ferme']}")
    print(f"  Pôle dominant du corpus  : {agg['pole_dominant']}")
    print(f"  Jetons non mappés        : {agg['jetons_non_mappes']} (bruit absorbé)")
    print(f"  Tolérance recommandée    : {rapport['tolérance_recommandee']} "
          f"(P{int(rapport['percentile_tolerance'])} des innovations)")
    print(f"  Facteurs normalisation   : {rapport['facteurs_normalisation_lexique']}")
    print("=" * 72)

    # Persistance du rapport
    dossier = _DOSSIER / "rapports"
    dossier.mkdir(exist_ok=True)
    cible = dossier / "calibration_mttv_core.json"
    cible.write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Rapport écrit : {cible}")
    print(f"  Signature: {MTTV_SIG}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
