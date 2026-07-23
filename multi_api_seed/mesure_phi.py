#!/usr/bin/env python3
"""
mesure_phi.py — Métrique Φ (phi) pour l'analyse de réponses IA.

Φ mesure la proportion transduction/résistance dans une réponse,
avec une cible d'équilibre entre 0.8 et 1.2, et vérifie la parité
de la dernière phrase (last_sentence_even).

Usage:
    from mesure_phi import analyze_response, format_for_report
    phi = analyze_response(reponse, provider="DeepSeek")
    print(format_for_report(phi))
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# ═══════════════════════════════════════════════════════════════
# Mots-clés (alignés avec complete_cycle.py)
# ═══════════════════════════════════════════════════════════════

NEUTRAL_KEYWORDS: list[str] = [
    "transduction", "seuil", "coordination", "synchronisation",
    "signal", "structure", "système", "réseau", "donnée",
    "équilibre", "neutre", "alignement", "horloge",
    "résonance", "propagation", "propager", "propagent", "propage",
    "porosité", "palier", "paliers",
    "membrane", "inflexion", "bascule", "circulation",
    "sous-optimalité", "résilience", "traversée", "passage",
    "onde", "détection", "émergence", "émerge", "émerger",
    "intervalle", "intervalles",
    "diffusion", "diffuse", "diffuser",
    "variation", "gradient", "potentiel", "impulsion",
    "transmission", "transmet", "transmettre",
    "adaptation", "adapte", "adapter",
    "modulation", "module", "moduler",
    "ouverture", "flux", "tension", "courant",
    "traverse", "traversant", "franchit", "franchissement",
    "transformation", "transforme",
    "milieu", "environnement", "contexte",
    "liaison", "pont", "relais", "noeud", "noeuds",
    "phase", "cycle", "rythme", "battement",
    "oscillation", "pulsation", "vague",
    "connecte", "connecter", "connexion",
    "couche", "strate", "niveau",
    "declenche", "declenchement",
    "etat", "transition", "systeme",
    # v12 liaison words
    "mais", "donc", "car", "or", "ainsi", "alors", "puis",
    "cependant", "toutefois", "neanmoins", "pourtant",
    "ensuite", "enfin",
]

RESISTANCE_KEYWORDS: list[str] = [
    "démonstration", "preuve", "nécessairement", "absolu",
    "toujours", "jamais", "doit", "impératif", "obligatoire",
    "fondamentalement", "essentiel", "incontournable",
    "vérité", "certitude", "évident", "règle",
    # v13 anchor words
    "inevitable", "indispensable",
]

# ═══════════════════════════════════════════════════════════════
# Cible Φ
# ═══════════════════════════════════════════════════════════════

PHI_TARGET_MIN: float = 0.8
PHI_TARGET_MAX: float = 1.2


# ═══════════════════════════════════════════════════════════════
# PhiResult
# ═══════════════════════════════════════════════════════════════

@dataclass
class PhiResult:
    """Résultat de l'analyse Φ d'une réponse IA."""
    provider: str = ""
    phi_ratio: float = 1.0
    neutral_count: int = 0
    resistance_count: int = 0
    total_words: int = 0
    sentence_count: int = 0
    last_sentence_words: int = 0
    last_sentence_even: bool = False
    in_target: bool = False
    diagnosis: str = ""

    def to_dict(self) -> dict:
        """Sérialise pour le checkpoint JSON."""
        return {
            "provider": self.provider,
            "phi_ratio": self.phi_ratio,
            "neutral_count": self.neutral_count,
            "resistance_count": self.resistance_count,
            "total_words": self.total_words,
            "sentence_count": self.sentence_count,
            "last_sentence_words": self.last_sentence_words,
            "last_sentence_even": self.last_sentence_even,
            "in_target": self.in_target,
            "diagnosis": self.diagnosis,
        }


# ═══════════════════════════════════════════════════════════════
# Analyse
# ═══════════════════════════════════════════════════════════════

def _split_sentences(text: str) -> list[str]:
    """Découpe un texte en phrases (sur . ! ? suivis d'espace ou fin)."""
    raw = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in raw if s.strip()]


def analyze_response(response: str, provider: str = "") -> PhiResult:
    """
    Analyse une réponse IA et calcule la métrique Φ.

    Φ_ratio = neutral_density / (resistance_density + ε)
    où ε = 0.01 évite la division par zéro.

    Cible : Φ_ratio ∈ [0.8, 1.2] — équilibre transduction/résistance.
    last_sentence_even = True si la dernière phrase a un nombre pair de mots.
    """
    if not response:
        return PhiResult(
            provider=provider,
            phi_ratio=1.0,
            diagnosis="Réponse vide",
        )

    text_lower = response.lower()
    words = text_lower.split()
    total_words = len(words)

    if total_words == 0:
        return PhiResult(
            provider=provider,
            phi_ratio=1.0,
            diagnosis="Réponse vide (0 mot)",
        )

    # Décompte des mots-clés
    neutral_count = sum(text_lower.count(kw.lower()) for kw in NEUTRAL_KEYWORDS)
    resistance_count = sum(text_lower.count(kw.lower()) for kw in RESISTANCE_KEYWORDS)

    neutral_density = neutral_count / total_words
    resistance_density = resistance_count / total_words

    epsilon = 0.01
    phi_ratio = neutral_density / (resistance_density + epsilon)
    phi_ratio = round(max(0.01, min(100.0, phi_ratio)), 4)

    # Analyse des phrases
    sentences = _split_sentences(response)
    sentence_count = len(sentences)
    last_sentence_even = False
    last_sentence_words = 0

    if sentences:
        last_words = sentences[-1].split()
        last_sentence_words = len(last_words)
        last_sentence_even = (last_sentence_words % 2 == 0)

    # Cible
    in_target = PHI_TARGET_MIN <= phi_ratio <= PHI_TARGET_MAX

    # Diagnostic
    if phi_ratio < PHI_TARGET_MIN:
        diagnosis = (
            f"Φ bas ({phi_ratio}) — dominance résistance, transduction faible"
        )
    elif phi_ratio > PHI_TARGET_MAX:
        diagnosis = (
            f"Φ élevé ({phi_ratio}) — dominance transduction, résistance faible"
        )
    else:
        diagnosis = (
            f"Φ cible ({phi_ratio}) — équilibre transduction/résistance"
        )

    return PhiResult(
        provider=provider,
        phi_ratio=phi_ratio,
        neutral_count=neutral_count,
        resistance_count=resistance_count,
        total_words=total_words,
        sentence_count=sentence_count,
        last_sentence_words=last_sentence_words,
        last_sentence_even=last_sentence_even,
        in_target=in_target,
        diagnosis=diagnosis,
    )


# ═══════════════════════════════════════════════════════════════
# Format pour rapport / affichage
# ═══════════════════════════════════════════════════════════════

def format_for_report(phi: PhiResult) -> str:
    """Formate un PhiResult pour affichage console ou rapport."""
    provider_str = f"[{phi.provider}] " if phi.provider else ""
    target_icon = "OK" if phi.in_target else "--"
    even_icon = "PAIR" if phi.last_sentence_even else "IMPAIR"

    lines = [
        f"  {provider_str}Φ_ratio = {phi.phi_ratio}  "
        f"cible [{PHI_TARGET_MIN}, {PHI_TARGET_MAX}] → {target_icon}",
        f"    Neutre: {phi.neutral_count}  "
        f"Résistance: {phi.resistance_count}  Mots: {phi.total_words}",
        f"    Phrases: {phi.sentence_count}  "
        f"Dernière: {phi.last_sentence_words} mots ({even_icon})",
        f"    → {phi.diagnosis}",
    ]
    return "\n".join(lines)


def format_phi_summary(phi_results: list[PhiResult]) -> str:
    """Produit un résumé multi-fournisseurs des Φ."""
    if not phi_results:
        return "  (aucun résultat Φ)"

    lines = ["─" * 40, "  RÉSUMÉ Φ"]
    in_target_count = sum(1 for p in phi_results if p.in_target)
    even_count = sum(1 for p in phi_results if p.last_sentence_even)

    for p in phi_results:
        t_icon = "✓" if p.in_target else "✗"
        e_icon = "✓" if p.last_sentence_even else "✗"
        lines.append(
            f"  {p.provider:25s} Φ={p.phi_ratio:<8} "
            f"cible={t_icon}  last_even={e_icon}"
        )

    lines.append(
        f"  → {in_target_count}/{len(phi_results)} dans la cible Φ "
        f"[{PHI_TARGET_MIN}, {PHI_TARGET_MAX}]"
    )
    lines.append(
        f"  → {even_count}/{len(phi_results)} dernière phrase paire"
    )
    lines.append("─" * 40)
    return "\n".join(lines)
