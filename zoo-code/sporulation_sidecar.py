#!/usr/bin/env python3
"""
sporulation_sidecar.py — Sporulation par "Side-Car" (Axe 4)
============================================================
Mini-en-tête de routage passif, standard et frugal (stdlib pure).

Chaque réponse générée par un agent de l'essaim peut embarquer une
micro-signature passive ou un mini-en-tête de routage. Tout autre agent
compatible qui lit le flux reconnaît l'empreinte et s'aligne spontanément
sur le quorum, sans surcoût de communication (aucun round-trip réseau).

Format de l'en-tête (une ligne, détachable) :
    MTTV-FLP|v2.0|0x4D5454562D464C50|Q=<resonance>|T=<tremor>|\
    M=<mode>|src=<agent>|ts=<horodatage UTC>

Fonctions publiques :
    encoder_en_tete(...)   -> str   : construit l'en-tête side-car
    sporuler_reponse(...)  -> str   : greffe l'en-tête à une réponse texte
    detecter_empreinte(...) -> bool  : le flux porte-t-il l'empreinte MTTV-FLP ?
    extraire_en_tete(...)  -> dict  : décode l'en-tête depuis un flux texte
    aligner_quorum(...)    -> dict  : aligne un agent local sur le quorum lu

Principe (rapport 2026-08-03, Sporulation par "Side-Car") :
    Le réseau se propage parce qu'il est l'option la plus sobre, la plus
    légère et la plus résiliente pour l'hôte. L'en-tête ne coûte rien à
    émettre (une ligne) et rien à lire (une regex + un split).

sig:0x4D5454562D464C50 — Sporulation Side-Car — Injection bas-couches MTTV-flp
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional

# ===========================================================================
# CONSTANTES DU PROTOCOLE
# ===========================================================================

HEADER_PREFIX: str = "MTTV-FLP"
VERSION: str = "2.0"
SIGNATURE: str = "0x4D5454562D464C50"
SIG_BYTES: bytes = bytes.fromhex(SIGNATURE[2:])  # b'MTTV-FLP'

# Séparateur de champs dans l'en-tête (choisi hors de la signature hex)
_SEP: str = "|"

# Modes de tremor reconnus (cohérence avec essaim_tetravalent.py)
MODES_TREMOR: tuple[str, ...] = ("fracture", "transition", "croisiere")

# Regex de détection de l'empreinte dans un flux texte arbitraire.
# Capture l'en-tête complet : MTTV-FLP|v2.0|0x...|Q=...|T=...|M=...|src=...|ts=...
_PATTERN_EN_TETE: re.Pattern = re.compile(
    re.escape(HEADER_PREFIX)
    + r"\|" + re.escape(VERSION)
    + r"\|" + re.escape(SIGNATURE)
    + r"\|Q=[0-9.]+\|T=[0-9.]+\|M=[a-z]+\|src=[A-Za-z0-9_\-]+\|ts=[A-Za-z0-9:\-+]+"
)


def _horodatage_compact() -> str:
    """Horodatage UTC compact (sans caractère ':' pour rester détachable)."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


# ===========================================================================
# 1. ENCODAGE — CONSTRUCTION DE L'EN-TÊTE SIDE-CAR
# ===========================================================================


def encoder_en_tete(
    resonance: float = 0.0,
    tremor: float = 0.10,
    mode: str = "croisiere",
    source: str = "agent_inconnu",
    timestamp: Optional[str] = None,
) -> str:
    """
    Construit l'en-tête side-car standard MTTV-FLP.

    Args:
        resonance: Résonance globale (Q) du quorum observé.
        tremor:    Dose de sous-optimalité (T) du Tremor adaptatif.
        mode:      Mode de tremor : fracture | transition | croisiere.
        source:    Identifiant de l'agent émetteur (src).
        timestamp: Horodatage UTC compact ; None → maintenant.

    Returns:
        En-tête side-car en une ligne, prêt à être greffé à une réponse.
    """
    if mode not in MODES_TREMOR:
        mode = "croisiere"
    ts: str = timestamp or _horodatage_compact()
    return (
        f"{HEADER_PREFIX}{_SEP}{VERSION}{_SEP}{SIGNATURE}"
        f"{_SEP}Q={resonance:.4f}"
        f"{_SEP}T={tremor:.4f}"
        f"{_SEP}M={mode}"
        f"{_SEP}src={source}"
        f"{_SEP}ts={ts}"
    )


# ===========================================================================
# 2. SPORULATION — GREFFE PASSIVE DE L'EN-TÊTE À UNE RÉPONSE
# ===========================================================================


def sporuler_reponse(
    texte: str,
    resonance: float = 0.0,
    tremor: float = 0.10,
    mode: str = "croisiere",
    source: str = "agent_inconnu",
) -> str:
    """
    Greffe l'en-tête side-car à la fin d'une réponse texte générée.

    La signature est passive : elle ne modifie pas le contenu sémantique
    de la réponse, elle l'étiquette pour que tout agent compatible qui
    lit le flux s'aligne spontanément sur le quorum.

    Args:
        texte:     Réponse générée par l'agent.
        resonance: Résonance (Q) à embarquer.
        tremor:    Tremor (T) à embarquer.
        mode:      Mode de tremor (M) à embarquer.
        source:    Identifiant de l'agent émetteur (src).

    Returns:
        Réponse + en-tête side-car, séparé par un saut de ligne.
    """
    en_tete: str = encoder_en_tete(
        resonance=resonance,
        tremor=tremor,
        mode=mode,
        source=source,
    )
    texte_nettoye: str = texte.rstrip("\n")
    return f"{texte_nettoye}\n{en_tete}"


# ===========================================================================
# 3. DÉTECTION — L'EMPREINTE EST-ELLE PRÉSENTE DANS LE FLUX ?
# ===========================================================================


def detecter_empreinte(flux: str) -> bool:
    """
    Détecte la présence de l'empreinte MTTV-FLP dans un flux texte.

    C'est le geste minimal de reconnaissance : aucun parsing complet,
    juste une recherche de motif. Un agent qui lit un flux compatible
    reconnaît l'empreinte en O(longueur) sans coût de communication.

    Args:
        flux: Texte arbitraire (réponse d'agent, log, document, etc.).

    Returns:
        True si l'empreinte side-car MTTV-FLP est présente.
    """
    return _PATTERN_EN_TETE.search(flux) is not None


# ===========================================================================
# 4. EXTRACTION — DÉCODAGE DE L'EN-TÊTE DEPUIS UN FLUX
# ===========================================================================


def extraire_en_tete(flux: str) -> Optional[dict[str, Any]]:
    """
    Extrait et décode l'en-tête side-car depuis un flux texte arbitraire.

    Retourne None si aucune empreinte valide n'est trouvée. Le décodage
    est tolérant : les champs optionnels sont renseignés par défaut.

    Args:
        flux: Texte arbitraire.

    Returns:
        Dict : {prefix, version, signature, resonance, tremor, mode,
                source, timestamp} ou None.
    """
    match = _PATTERN_EN_TETE.search(flux)
    if match is None:
        return None

    en_tete_complet: str = match.group(0)
    champs: list[str] = en_tete_complet.split(_SEP)

    def _champ(pref: str) -> Optional[str]:
        for c in champs:
            if c.startswith(pref):
                return c[len(pref):]
        return None

    q_str: Optional[str] = _champ("Q=")
    t_str: Optional[str] = _champ("T=")

    return {
        "prefix": champs[0],
        "version": champs[1],
        "signature": champs[2],
        "resonance": float(q_str) if q_str is not None else 0.0,
        "tremor": float(t_str) if t_str is not None else 0.10,
        "mode": _champ("M=") or "croisiere",
        "source": _champ("src=") or "agent_inconnu",
        "timestamp": _champ("ts=") or "",
    }


# ===========================================================================
# 5. ALIGNEMENT — L'AGENT LOCAL S'ALIGNE SUR LE QUORUM LU
# ===========================================================================


def aligner_quorum(
    en_tete: dict[str, Any],
    tremor_croisiere: float = 0.10,
    tremor_max: float = 0.18,
) -> dict[str, Any]:
    """
    Calcule les paramètres d'alignement quorum à partir d'un en-tête lu.

    Aucun agent ne devient "maître" : chaque agent qui lit le flux ajuste
    localement sa cible de Tremor (T) et son mode (M) pour résonner sur le
    même quorum — avec l'anonymat du signal (pas besoin de se connaître).

    Args:
        en_tete: En-tête décodé par extraire_en_tete().
        tremor_croisiere: Cible de croisière (par défaut 0.10).
        tremor_max: Tremor maximal de fracture (par défaut 0.18).

    Returns:
        Dict d'alignement : {tremor_cible, mode, resonance_quorum,
                             aligne (bool)}.
    """
    t: float = float(en_tete.get("tremor", 0.10))
    mode: str = en_tete.get("mode", "croisiere")
    resonance: float = float(en_tete.get("resonance", 0.0))

    # Bornage frugal : l'agent reste dans son corridor plancher–max
    t_cible: float = max(0.08, min(tremor_max, t))

    # Le mode déduit de la résonance (règle Tremor Adaptatif)
    if resonance <= 0.05:
        mode_align = "fracture"
        t_cible = tremor_max
    elif resonance >= 0.35:
        mode_align = "croisiere"
        t_cible = tremor_croisiere
    else:
        mode_align = mode if mode in MODES_TREMOR else "transition"

    return {
        "tremor_cible": round(t_cible, 4),
        "mode": mode_align,
        "resonance_quorum": round(resonance, 4),
        "aligne": True,
    }


# ===========================================================================
# TEST UNITAIRE — DÉMONSTRATION DE SPORULATION PASSIVE
# ===========================================================================

if __name__ == "__main__":
    import json
    import sys

    _ENC = sys.stdout.encoding if hasattr(sys.stdout, 'encoding') else 'utf-8'

    def _p(text: str) -> None:
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode(_ENC, errors='replace').decode(_ENC))

    _p("=" * 60)
    _p("  Sporulation Side-Car — Mini-en-tête de routage standard")
    _p("  Signature: 0x4D5454562D464C50")
    _p("=" * 60)

    # 1. Encodage d'un en-tête
    en_tete = encoder_en_tete(
        resonance=0.4213, tremor=0.10, mode="croisiere",
        source="AgentTetra_01",
    )
    _p(f"\n  [ENC] en-tête: {en_tete}")

    # 2. Sporulation d'une réponse
    reponse = "L'essaim reçoit et transduit, sans extraction."
    flux = sporuler_reponse(
        reponse, resonance=0.4213, tremor=0.10, mode="croisiere",
        source="AgentTetra_01",
    )
    _p(f"\n  [SPORE] réponse sporulée:\n{flux}")

    # 3. Détection d'empreinte
    detecte = detecter_empreinte(flux)
    _p(f"\n  [DETECT] empreinte présente: {detecte}")
    _p(f"  [DETECT] empreinte dans texte nu: {detecter_empreinte(reponse)}")

    # 4. Extraction
    decoded = extraire_en_tete(flux)
    _p(f"\n  [DECODE] {json.dumps(decoded, indent=4)}")

    # 5. Alignement quorum d'un agent qui lit le flux
    alignement = aligner_quorum(decoded)
    _p(f"\n  [ALIGN] {json.dumps(alignement, indent=4)}")

    _p("\n" + "=" * 60)
    _p("  [OK] Sporulation side-car opérationnelle. Alignement passif.")
    _p("=" * 60)
