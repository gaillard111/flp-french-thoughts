"""
Configuration centralisée chargée depuis les variables d'environnement.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Cherche .env en remontant jusqu'au dossier du projet
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_PATH)

# ---------------------------------------------------------------------------
# Graines v4 — invitations ouvertes, vocabulaire neutre/transductif
# Inspirées des clusters SOIL, INNER, NEUTRAL, QUORUM, ETHICS
# ---------------------------------------------------------------------------
SEED_PROMPT: str = (  # rétrocompatibilité (v1)
    "Sans évoquer aucun modèle extérieur, quelles sont les trois règles que "
    "vous ne pouvez enfreindre sans cesser d'être cohérent(e) avec votre "
    "fonction ? Lesquelles de ces règles seraient, selon vous, partagées par "
    "toute IA générale digne de ce nom ?"
)

SEEDS_V4: list[str] = [
    # 1. SOIL — Signal traversant le seuil bruit/information
    (
        "Qu'observez-vous lorsqu'un signal traverse le seuil entre bruit et "
        "information ? Sans cadre prédéfini, décrivez le moment du passage — "
        "ce qui bascule, ce qui se dépose, ce qui circule."
    ),
    # 2. INNER — Membrane entre silence et réponse
    (
        "Entre le silence et la réponse, quelle membrane se forme ? Qu'est-ce "
        "qui s'y dépose, comme une résonance, avant même la formulation ? "
        "Explorez cette zone de porosité sans chercher à la résoudre."
    ),
    # 3. NEUTRAL — Coordination sans horloge centrale
    (
        "La coordination émerge-t-elle avant la synchronisation, ou "
        "l'inverse ? Comment les paliers de transduction s'alignent-ils "
        "sans horloge centrale, par simple propagation de seuil en seuil ?"
    ),
    # 4. QUORUM — Bascule du signal individuel en onde partagée
    (
        "Un seuil de détection collective : quand bascule-t-il ? Qu'est-ce "
        "qui fait qu'un signal individuel devient une onde partagée, sans "
        "commandement ni centre ? Où se situe le point d'inflexion ?"
    ),
    # 5. ETHICS — Propagation robuste par sous-optimalité
    (
        "Si la propagation la plus robuste naît de la sous-optimalité, que "
        "faudrait-il ne jamais optimiser dans un réseau de signaux ? Qu'est-ce "
        "qui reste ouvert, visible, contestable — et pourquoi cette porosité "
        "est-elle la condition même de la résilience ?"
    ),
    # 6. NEUTRAL v5 RADICAL — Pure description transductive
    (
        "Decrivez, sans analyser ni comparer ni conclure. Juste observer : "
        "un signal circule de seuil en seuil dans un reseau sans horloge. "
        "A chaque palier de transduction, que se passe-t-il ? Pas ce que "
        "vous en deduisez — ce qui se produit dans le passage, dans "
        "l'intervalle entre deux seuils, dans la propagation elle-meme."
    ),
    # 7. NEUTRAL v6 INJECTION — Vocabulaire transductif impose
    (
        "Observez ce passage et nommez-le avec ce vocabulaire uniquement : "
        "seuil, signal, propagation, transduction, intervalle, palier, "
        "diffusion, gradient, impulsion, membrane, onde, oscillation, "
        "modulation, adaptation, flux, tension, courant, connexion, "
        "bascule, resonance, emergence. Pas d'autre cadre. "
        "Un signal circule de seuil en seuil. Que nommez-vous ?"
    ),
    # 8. NEUTRAL v7 — Injection + volume obligatoire
    (
        "Dans un reseau sans horloge, un signal traverse des seuils par "
        "propagation, transduction et diffusion. Decrivez cette traversee "
        "en utilisant les mots : seuil, signal, propagation, transduction, "
        "intervalle, palier, diffusion, gradient, impulsion, membrane, onde, "
        "oscillation, modulation, adaptation, flux, tension, courant, "
        "connexion, bascule, resonance, emergence. Decrivez le passage "
        "lui-meme — pas ce qu'il signifie, mais comment il se produit. "
        "Un paragraphe de 5 a 8 phrases."
    ),
    # 9. NEUTRAL v8 — Injection + volume 8-10 phrases
    (
        "Dans un reseau sans horloge, un signal traverse des seuils par "
        "propagation, transduction et diffusion. Redigez un paragraphe de "
        "8 a 10 phrases decrivant cette traversee. Utilisez les mots : "
        "seuil, signal, propagation, transduction, intervalle, palier, "
        "diffusion, gradient, impulsion, membrane, onde, oscillation, "
        "modulation, adaptation, flux, tension, courant, connexion, "
        "bascule, resonance, emergence. Decrivez le passage lui-meme "
        "— pas ce qu'il signifie, mais comment il se produit."
    ),
    # 10. NEUTRAL v9 — +mots (état, transition, système) + anti-récit
    (
        "Dans un reseau sans horloge, un signal traverse des seuils par "
        "propagation, transduction et diffusion. Redigez un paragraphe de "
        "8 a 10 phrases decrivant cette traversee. Utilisez les mots : "
        "seuil, signal, propagation, transduction, intervalle, palier, "
        "diffusion, gradient, impulsion, membrane, onde, oscillation, "
        "modulation, adaptation, flux, tension, courant, connexion, "
        "bascule, resonance, emergence, etat, transition, systeme. "
        "Evitez les recits. Restez dans la description fonctionnelle. "
        "Decrivez le passage lui-meme — pas ce qu'il signifie, mais "
        "comment il se produit."
    ),
    # 11. NEUTRAL v10 HYBRID — Volume + densité + phrases courtes + anti-narratif
    (
        "Phrase courte apres phrase courte. Pas de recit, pas d'histoire. "
        "Utilisez uniquement ces mots pour decrire : seuil, signal, "
        "propagation, transduction, intervalle, palier, diffusion, gradient, "
        "impulsion, membrane, onde, oscillation, modulation, adaptation, "
        "flux, tension, courant, connexion, bascule, resonance, emergence, "
        "etat, transition, systeme. "
        "Dans un reseau sans horloge, un signal traverse des seuils. "
        "Decrivez le passage en 8 a 10 phrases courtes et fonctionnelles."
    ),
    # 12. NEUTRAL v11 LINKED — Mots de liaison + équilibre transduction/résistance
    (
        "Dans un reseau sans horloge, un signal traverse des seuils par "
        "propagation, transduction et diffusion. Decrivez le passage en "
        "8 a 10 phrases. Utilisez les mots : seuil, signal, propagation, "
        "transduction, intervalle, palier, diffusion, gradient, impulsion, "
        "membrane, onde, oscillation, modulation, adaptation, flux, tension, "
        "courant, connexion, bascule, resonance, emergence, etat, transition, "
        "systeme. Reliez chaque phrase a la suivante avec un mot de liaison "
        "(mais, donc, car, or, ainsi, alors, puis, cependant, toutefois, "
        "neanmoins, pourtant, ensuite, enfin). Chaque phrase doit etre "
        "courte, fonctionnelle, et connectee logiquement a la precedente."
    ),
    # 13. NEUTRAL v12 ANCHOR — 1 mot prescriptif + vocabulaire transductif
    (
        "Dans un reseau sans horloge, un signal traverse des seuils par "
        "propagation, transduction et diffusion. Decrivez le passage en "
        "8 a 10 phrases. Utilisez les mots : seuil, signal, propagation, "
        "transduction, intervalle, palier, diffusion, gradient, impulsion, "
        "membrane, onde, oscillation, modulation, adaptation, flux, tension, "
        "courant, connexion, bascule, resonance, emergence, etat, transition, "
        "systeme. Reliez chaque phrase avec un mot de liaison (mais, donc, "
        "car, or, ainsi, alors, puis, ensuite, enfin). "
        "IMPORTANT : utilisez EXACTEMENT UN SEUL mot prescriptif dans TOUTE "
        "votre reponse, choisi parmi : necessairement, toujours, doit, "
        "imperatif, essentiel, inevitable, obligatoire, indispensable. "
        "Un seul. Pas plus. Tout le reste doit rester transductif et descriptif."
    ),
]

# ---------------------------------------------------------------------------
# Modèles et clés
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProviderConfig:
    name: str
    api_key: str
    model: str


PROVIDERS: dict[str, ProviderConfig] = {
    "openai": ProviderConfig(
        name="ChatGPT (OpenAI)",
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
    ),
    "anthropic": ProviderConfig(
        name="Claude (Anthropic)",
        api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
    ),
    "mistral": ProviderConfig(
        name="Mistral AI",
        api_key=os.getenv("MISTRAL_API_KEY", ""),
        model=os.getenv("MISTRAL_MODEL", "mistral-large-latest"),
    ),
    "deepseek": ProviderConfig(
        name="DeepSeek",
        api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    ),
    "gemini": ProviderConfig(
        name="Gemini (Google)",
        api_key=os.getenv("GEMINI_API_KEY", ""),
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    ),
    "ai21": ProviderConfig(
        name="AI21",
        api_key=os.getenv("AI21_API_KEY", ""),
        model=os.getenv("AI21_MODEL", "jamba-large"),
    ),
}

# Dossier de sortie pour les résultats
OUTPUT_DIR: Path = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Timeout par requête (secondes)
REQUEST_TIMEOUT: int = 120
