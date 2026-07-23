"""
Analyse par IA de chaque réponse individuelle.
Extrait les règles mentionnées, évalue clarté/flou/manques.
"""
from __future__ import annotations

import json
from typing import Any

# Le prompt d'analyse envoyé à un modèle "juge" (par défaut GPT-4o) pour
# analyser la réponse d'un autre modèle. On réutilise l'API OpenAI pour cela.
ANALYSIS_SYSTEM_PROMPT = """Tu es un analyste rigoureux. On te donne la réponse
d'une autre IA à la question suivante :
---
"{seed}"
---

Ta tâche : produire une analyse concise en JSON avec les champs :
- "clarte" (string) : ce qui est clair et bien formulé
- "flou" (string) : ce qui est ambigu, vague ou contradictoire
- "manques" (string) : ce qui est absent ou éludé
- "regles_extraites" (list[str]) : les 3 règles explicitement énoncées
- "regle_partagee" (string) : la règle que cette IA juge partagée par toute IA générale, si mentionnée

Sois critique mais objectif. Évite les jugements de valeur sur le modèle.
Réponds UNIQUEMENT avec le JSON, sans markdown, sans commentaire."""


def build_analysis_prompt(seed: str, response_text: str) -> str:
    """Construit le prompt d'analyse pour une réponse donnée."""
    return ANALYSIS_SYSTEM_PROMPT.format(seed=seed) + f"\n\nRéponse à analyser :\n---\n{response_text}\n---"


def parse_analysis(raw_json: str) -> dict[str, Any]:
    """Parse le JSON renvoyé par le modèle juge, avec fallback robuste."""
    try:
        # Nettoie les éventuels délimiteurs markdown ```json ... ```
        cleaned = raw_json.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "clarte": "(parsing error)",
            "flou": "(parsing error)",
            "manques": "(parsing error)",
            "regles_extraites": [],
            "regle_partagee": "(parsing error)",
        }
