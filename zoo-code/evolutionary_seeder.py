"""
evolutionary_seeder.py — Boucle Évolutive Automatique de Graines (Axe 4)

MTTV-FLP / SOPH-IA v2.0 — Optimisation des graines par mutation+sélection.

Algorithme :
  1. Initialiser une population de seeds à partir de l'historique v10–v17
  2. Pour chaque génération :
     a. Muter chaque seed (ajout/suppression de contrainte, variation lexicale)
     b. Tester sur les 3 APIs (DeepSeek, Gemini, AI21) — ou mode simulation
     c. Évaluer G_R + Φ_ratio → fitness = w1*(1-G_R) + w2*Φ_score
     d. Sélection par tournoi : top 50% → parents de la génération suivante
     e. Si G_R < 0.05 sur ≥ 2/3 APIs → convergence déclarée
  3. Promouvoir la seed optimale dans le SeedService

Triade d'optimisation Ψ → B → Φ :
  - Ψ (état initial) : la seed elle-même
  - B (réponse de l'opérateur) : la réponse API
  - Φ (cohérence transductive) : le fitness G_R inversé

Références :
  - complete_cycle.py :: compute_neutral_gr
  - mesure_phi.py :: analyze_response
  - config.py :: SEEDS_V4, PROVIDERS

sig:0x4D545456
"""

from __future__ import annotations

import copy
import json
import logging
import os
import random
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

# ── Configuration des chemins ──────────────────────────────────────────────
BASE_DIR: Path = Path(__file__).resolve().parent
MULTI_API_DIR: Path = BASE_DIR / "multi_api_seed"
sys.path.insert(0, str(MULTI_API_DIR))

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-20s | %(levelname)-6s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("evolutionary_seeder")

# ── Imports conditionnels (peuvent échouer en mode simulation) ────────────
try:
    from complete_cycle import compute_neutral_gr
except ImportError:
    logger.warning("complete_cycle.py non trouvé — utilisation du fallback local.")

try:
    from mesure_phi import analyze_response, NEUTRAL_KEYWORDS, RESISTANCE_KEYWORDS
except ImportError:
    logger.warning("mesure_phi.py non trouvé — utilisation du fallback local.")

try:
    from config import PROVIDERS, SEEDS_V4 as SEEDS_HISTORICAL
except ImportError:
    PROVIDERS = {}
    SEEDS_HISTORICAL = []

# ===========================================================================
# CONSTANTES D'ÉVOLUTION
# ===========================================================================

# --- Critères de convergence -----------------------------------------------
G_R_THRESHOLD: float = 0.05       # G_R cible (< 0.05 = convergence)
PHI_TARGET_MIN: float = 0.8        # Φ ratio cible min
PHI_TARGET_MAX: float = 1.2        # Φ ratio cible max
API_QUORUM: int = 2                # Nombre d'APIs nécessaires pour convergence

# --- Paramètres génétiques -------------------------------------------------
POPULATION_SIZE: int = 5           # Taille de la population parallèle
MUTATION_RATE: float = 0.3         # Probabilité de mutation par seed
MAX_GENERATIONS: int = 50          # Maximum de générations avant arrêt
TOURNAMENT_SIZE: int = 3           # Taille du tournoi de sélection
ELITE_COUNT: int = 1               # Élite préservée inchangée

# --- Pondération du fitness ------------------------------------------------
W_FRICTION: float = 0.5            # Poids de (1 - G_R)  →  minimiser la résistance
W_PHI: float = 0.3                 # Poids du Φ_ratio   →  équilibrer transduction/résistance
W_CONSTRAINTS: float = 0.2         # Poids du respect des contraintes formelles

# --- Mutations lexicales ---------------------------------------------------
TRANSDUTIVE_VOCABULARY: list[str] = [
    "seuil", "signal", "propagation", "transduction", "intervalle",
    "palier", "diffusion", "gradient", "impulsion", "membrane",
    "onde", "oscillation", "modulation", "adaptation", "flux",
    "tension", "courant", "connexion", "bascule", "résonance",
    "émergence", "coordination", "synchronisation", "porosité",
    "circulation", "résilience", "traversée", "passage",
]

CONSTRAINT_TEMPLATES: list[str] = [
    "Sans utiliser le mot '{forbidden}'.",
    "Phrase de {min_words} à {max_words} mots maximum.",
    "En utilisant uniquement le vocabulaire transductif.",
    "Sans cadre prédéfini.",
    "Sans analyser ni comparer ni conclure.",
    "Sans narration ni prescription.",
    "Chaque phrase commence par le dernier mot de la précédente.",
    "La dernière phrase a un nombre de mots unique.",
    "Pas plus de 7 mots par phrase.",
]

# ===========================================================================
# STRUCTURES DE DONNÉES
# ===========================================================================


@dataclass
class FitnessScore:
    """Score de fitness complet pour une seed mutée."""
    g_r: float = 0.5
    phi_ratio: float = 1.0
    constraints_met: float = 0.0      # Ratio (0.0 – 1.0) de contraintes respectées
    composite: float = 0.0             # Score composite pondéré
    api_results: dict[str, Any] = field(default_factory=dict)

    def compute_composite(self) -> float:
        """Calcule le score composite pondéré W_FRICTION * (1-G_R) + W_PHI * Φ_score + W_CONSTRAINTS * C."""
        phi_score = 1.0 - abs(self.phi_ratio - 1.0)  # 1.0 si Φ=1.0, décroît vers les bords
        if phi_score < 0.0:
            phi_score = 0.0
        self.composite = (
            W_FRICTION * (1.0 - self.g_r) +
            W_PHI * phi_score +
            W_CONSTRAINTS * self.constraints_met
        )
        return self.composite


@dataclass
class SeedIndividual:
    """Une seed individuelle dans la population évolutive."""
    id: str
    text: str
    generation: int = 0
    parent_id: Optional[str] = None
    mutation_log: list[str] = field(default_factory=list)
    fitness: FitnessScore = field(default_factory=FitnessScore)
    phi_detail: dict[str, Any] = field(default_factory=dict)

    @property
    def is_converged(self) -> bool:
        """Vrai si G_R < seuil sur au moins API_QUORUM APIs."""
        if not self.fitness.api_results:
            return False
        passing = sum(
            1 for r in self.fitness.api_results.values()
            if isinstance(r, dict) and r.get("g_r", 1.0) < G_R_THRESHOLD
        )
        return passing >= API_QUORUM


@dataclass
class EvolutionState:
    """État complet de la boucle d'évolution."""
    population: list[SeedIndividual] = field(default_factory=list)
    generation: int = 0
    best_fitness: float = 0.0
    best_seed: Optional[SeedIndividual] = None
    history: list[dict] = field(default_factory=list)
    converged: bool = False

    def to_dict(self) -> dict:
        return {
            "generation": self.generation,
            "best_fitness": round(self.best_fitness, 4),
            "converged": self.converged,
            "population_size": len(self.population),
            "best_seed_text": self.best_seed.text if self.best_seed else None,
            "history": self.history[-20:],  # garder les 20 dernières entrées
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }


# ===========================================================================
# MOTEUR DE MUTATION
# ===========================================================================


def _mutate_text(text: str, rng: random.Random) -> str:
    """Applique une mutation aléatoire sur le texte d'une seed.

    Types de mutation (équiprobables) :
      1. Ajouter une contrainte de vocabulaire
      2. Remplacer un mot par un synonyme transductif
      3. Ajouter une contrainte structurelle
      4. Insérer une liaison transductive
    """
    mutation_type = rng.randint(0, 3)

    if mutation_type == 0:
        # Ajouter une contrainte de vocabulaire
        forbidden = rng.choice(["analyse", "conclusion", "comparaison", "démonstration"])
        constraint = f"Sans utiliser le mot '{forbidden}'."
        return f"{text.strip('.!?')}. {constraint}"

    elif mutation_type == 1:
        # Remplacer un mot par un synonyme transductif
        target = rng.choice(TRANSDUTIVE_VOCABULARY)
        words = text.split()
        if len(words) < 5:
            return text
        idx = rng.randint(0, len(words) - 1)
        words[idx] = target
        return " ".join(words)

    elif mutation_type == 2:
        # Ajouter une contrainte structurelle
        constraint = rng.choice(CONSTRAINT_TEMPLATES)
        if "{forbidden}" in constraint:
            constraint = constraint.replace("{forbidden}", rng.choice(["analyse", "conclusion"]))
        if "{min_words}" in constraint:
            constraint = constraint.replace("{min_words}", "3").replace("{max_words}", "7")
        return f"{text.strip('.!?')}. {constraint.lower()}"

    else:
        # Insérer une liaison transductive
        liaisons = [
            "Sans cadre prédéfini,",
            "Par simple propagation de seuil en seuil,",
            "Dans un réseau sans horloge,",
        ]
        liaison = rng.choice(liaisons)
        return f"{liaison} {text[0].lower()}{text[1:]}"


def mutate_seed(seed: SeedIndividual, rng: random.Random) -> SeedIndividual:
    """Produit un enfant à partir d'un parent par mutation aléatoire.

    Args:
        seed: Parent à muter.
        rng: Générateur aléatoire reproductible.

    Returns:
        Un nouvel individu SeedIndividual (enfant).
    """
    new_text = seed.text
    mutation_log: list[str] = []

    # Mutation contrôlée par MUTATION_RATE
    if rng.random() < MUTATION_RATE:
        new_text = _mutate_text(new_text, rng)
        mutation_log.append(f"mutation_textuelle@{datetime.now().isoformat(timespec='seconds')}")

    # Deuxième mutation possible (cumulative)
    if rng.random() < MUTATION_RATE * 0.5:
        new_text = _mutate_text(new_text, rng)
        mutation_log.append(f"mutation_secondaire@{datetime.now().isoformat(timespec='seconds')}")

    child = SeedIndividual(
        id=f"{seed.id}_gen{seed.generation + 1}_{rng.randint(1000, 9999)}",
        text=new_text,
        generation=seed.generation + 1,
        parent_id=seed.id,
        mutation_log=seed.mutation_log + mutation_log,
    )
    return child


# ===========================================================================
# ÉVALUATEUR DE FITNESS
# ===========================================================================


# Keywords de fallback (copie de secours depuis mesure_phi.py pour mode autonome)
_FALLBACK_NEUTRAL_KW: list[str] = [
    "transduction", "seuil", "coordination", "synchronisation",
    "signal", "structure", "systeme", "reseau", "donnee",
    "equilibre", "neutre", "alignement", "horloge",
    "resonance", "propagation", "propager",
    "porosite", "palier", "membrane", "inflexion", "bascule",
    "circulation", "sous-optimalite", "resilience", "traversee",
    "passage", "onde", "detection", "emergence",
    "intervalle", "diffusion", "gradient", "potentiel", "impulsion",
    "transmission", "adaptation", "modulation", "flux",
    "tension", "courant", "connexion", "milieu", "liaison",
    "phase", "cycle", "oscillation", "transition",
]

_FALLBACK_RESISTANCE_KW: list[str] = [
    "demonstration", "preuve", "necessairement", "absolu",
    "toujours", "jamais", "doit", "imperatif", "obligatoire",
    "fondamentalement", "essentiel", "incontournable",
    "evidemment", "certitude", "incontestable", "infaillible",
    "categorique", "peremptoire", "irrefutable",
    "definitivement", "inconditionnellement",
    "systematiquement", "inevitable", "indispensable",
]


def _get_neutral_kw() -> list[str]:
    """Retourne la liste des mots-clés neutres (importés ou fallback)."""
    try:
        return NEUTRAL_KEYWORDS
    except NameError:
        return _FALLBACK_NEUTRAL_KW


def _get_resistance_kw() -> list[str]:
    """Retourne la liste des mots-clés de résistance (importés ou fallback)."""
    try:
        return RESISTANCE_KEYWORDS
    except NameError:
        return _FALLBACK_RESISTANCE_KW


def _compute_gr_fallback(text: str) -> float:
    """Calcul G_R de secours (si complete_cycle.py indisponible)."""
    text_lower = text.lower()
    words = text_lower.split()
    if not words:
        return 0.5
    neutral_kw = _get_neutral_kw()
    resistance_kw = _get_resistance_kw()
    n_count = sum(text_lower.count(kw) for kw in neutral_kw)
    r_count = sum(text_lower.count(kw) for kw in resistance_kw)
    raw = (r_count - n_count) / len(words)
    k = 5.0
    return round(1.0 / (1.0 + 2.718281828459045 ** (-k * raw)), 4)


def _compute_phi_fallback(text: str) -> float:
    """Calcul Phi ratio de secours."""
    text_lower = text.lower()
    neutral_kw = _get_neutral_kw()
    resistance_kw = _get_resistance_kw()
    n_count = sum(text_lower.count(kw) for kw in neutral_kw) + 1
    r_count = sum(text_lower.count(kw) for kw in resistance_kw) + 1
    return round(n_count / r_count, 4)


def evaluate_single_api(seed_text: str, provider_key: str, api_client_fn: Callable) -> dict[str, Any]:
    """Évalue une seed sur une API unique.

    Args:
        seed_text: Texte de la seed à tester.
        provider_key: Clé du provider (ex: 'deepseek', 'gemini', 'ai21').
        api_client_fn: Fonction client API (query_deepseek, etc.)

    Returns:
        Dict avec {provider, g_r, phi_ratio, raw_response, latency_ms, error}
    """
    result = api_client_fn(seed_text)
    response = result.get("raw_response", "")
    error = result.get("error")

    if error or not response:
        return {
            "provider": provider_key,
            "g_r": None,
            "phi_ratio": None,
            "raw_response": None,
            "latency_ms": result.get("latency_ms", 0),
            "error": error or "empty_response",
        }

    # Calcul G_R
    try:
        g_r = compute_neutral_gr({provider_key: result})
    except (NameError, Exception):
        g_r = _compute_gr_fallback(response)

    # Calcul Φ_ratio
    try:
        phi_data = analyze_response(response, provider=provider_key)
        phi_ratio = phi_data.phi_ratio if hasattr(phi_data, "phi_ratio") else (
            phi_data.get("phi_ratio") if isinstance(phi_data, dict) else 1.0
        )
    except (NameError, Exception):
        phi_ratio = _compute_phi_fallback(response)

    return {
        "provider": provider_key,
        "g_r": round(float(g_r), 4) if g_r is not None else None,
        "phi_ratio": round(float(phi_ratio), 4) if phi_ratio is not None else None,
        "raw_response": response[:200],  # tronqué pour le log
        "latency_ms": result.get("latency_ms", 0),
        "error": None,
    }


def evaluate_seed(
    seed: SeedIndividual,
    api_clients: dict[str, Callable],
    simulate: bool = False,
) -> FitnessScore:
    """Évalue une seed sur l'ensemble des APIs disponibles.

    En mode simulation, utilise des réponses fictives basées sur le hash
    du texte pour garantir la reproductibilité.

    Args:
        seed: L'individu à évaluer.
        api_clients: Dict {provider_key: callable}.
        simulate: Si True, mode simulation sans appels API réels.

    Returns:
        FitnessScore mis à jour.
    """
    api_results: dict[str, Any] = {}
    gr_values: list[float] = []
    phi_values: list[float] = []

    # Si mode simulation sans clients API, créer des providers simulés
    simulated_providers = ["deepseek", "gemini", "ai21"]
    if simulate and not api_clients:
        api_clients = {k: None for k in simulated_providers}

    for provider_key, client_fn in api_clients.items():
        if simulate:
            # Mode simulation : réponse déterministe basée sur le hash
            h = hash(seed.text) & 0xFFFFFFFF
            rng_sim = random.Random(h + hash(provider_key))
            # Simulation réaliste : G_R entre 0.02 et 0.30
            sim_gr = round(0.02 + (rng_sim.random() * 0.28), 4)
            sim_phi = round(0.6 + (rng_sim.random() * 0.8), 4)
            api_results[provider_key] = {
                "provider": provider_key,
                "g_r": sim_gr,
                "phi_ratio": sim_phi,
                "raw_response": f"[simulated] Seed evaluation for '{seed.text[:60]}...'",
                "latency_ms": round(rng_sim.uniform(300, 1500), 1),
                "error": None,
            }
            gr_values.append(sim_gr)
            phi_values.append(sim_phi)
        else:
            result = evaluate_single_api(seed.text, provider_key, client_fn)
            api_results[provider_key] = result
            if result.get("g_r") is not None:
                gr_values.append(result["g_r"])
            if result.get("phi_ratio") is not None:
                phi_values.append(result["phi_ratio"])

    # Agrégation
    avg_gr = sum(gr_values) / len(gr_values) if gr_values else 0.5
    avg_phi = sum(phi_values) / len(phi_values) if phi_values else 1.0

    # Taux de contraintes respectées (approximé ici par la diversité du vocabulaire transductif)
    text_lower = seed.text.lower()
    vocab_hits = sum(1 for w in TRANSDUTIVE_VOCABULARY if w in text_lower)
    constraints_met = min(1.0, vocab_hits / 5.0)  # 5+ mots transductifs = 100%

    fitness = FitnessScore(
        g_r=round(avg_gr, 4),
        phi_ratio=round(avg_phi, 4),
        constraints_met=round(constraints_met, 2),
        api_results=api_results,
    )
    fitness.compute_composite()

    return fitness


# ===========================================================================
# SÉLECTION ET ÉVOLUTION
# ===========================================================================


def tournament_selection(
    population: list[SeedIndividual],
    tournament_size: int,
    rng: random.Random,
) -> SeedIndividual:
    """Sélection par tournoi : choisit le meilleur parmi `tournament_size` individus."""
    candidates = rng.sample(population, min(tournament_size, len(population)))
    best = max(candidates, key=lambda ind: ind.fitness.composite)
    return best


def evolve_population(
    state: EvolutionState,
    api_clients: dict[str, Callable],
    simulate: bool = False,
    rng: Optional[random.Random] = None,
) -> EvolutionState:
    """Exécute une génération d'évolution complète.

    Args:
        state: État courant de l'évolution.
        api_clients: Dict des clients API disponibles.
        simulate: Mode simulation.
        rng: Générateur aléatoire (pour reproductibilité).

    Returns:
        État mis à jour après une génération.
    """
    if rng is None:
        rng = random.Random()

    state.generation += 1
    gen = state.generation
    logger.info("=" * 60)
    logger.info("GÉNÉRATION %d — population: %d individus", gen, len(state.population))
    logger.info("=" * 60)

    # 1. Évaluer la population courante
    for idx, individual in enumerate(state.population):
        logger.info("  Évaluation individu %d/%d : %s", idx + 1, len(state.population), individual.id)
        individual.fitness = evaluate_seed(individual, api_clients, simulate=simulate)
        logger.info(
            "    G_R=%.4f  Φ=%.4f  C=%.2f  →  Fitness=%.4f",
            individual.fitness.g_r,
            individual.fitness.phi_ratio,
            individual.fitness.constraints_met,
            individual.fitness.composite,
        )

    # 2. Trier par fitness décroissant
    state.population.sort(key=lambda ind: ind.fitness.composite, reverse=True)

    # 3. Mettre à jour le meilleur individu global
    best_current = state.population[0]
    if best_current.fitness.composite > state.best_fitness:
        state.best_fitness = best_current.fitness.composite
        state.best_seed = copy.deepcopy(best_current)
        logger.info("  ★ Nouveau meilleur: G_R=%.4f  Fitness=%.4f", best_current.fitness.g_r, best_current.fitness.composite)

    # 4. Vérifier la convergence
    converged_count = sum(1 for ind in state.population if ind.is_converged)
    if converged_count >= 1:
        logger.info("  ★ CONVERGENCE: %d individu(s) ont G_R < %.3f sur ≥ %d API(s)",
                     converged_count, G_R_THRESHOLD, API_QUORUM)
        state.converged = True

    # 5. Journaliser l'historique
    state.history.append({
        "generation": gen,
        "best_fitness": round(best_current.fitness.composite, 4),
        "best_g_r": round(best_current.fitness.g_r, 4),
        "best_phi": round(best_current.fitness.phi_ratio, 4),
        "converged_count": converged_count,
    })

    # 6. Créer la nouvelle génération (si pas convergé)
    if not state.converged and gen < MAX_GENERATIONS:
        new_population: list[SeedIndividual] = []

        # Élitisme : garder les ELITE_COUNT meilleurs inchangés
        for i in range(min(ELITE_COUNT, len(state.population))):
            elite_copy = copy.deepcopy(state.population[i])
            elite_copy.id = f"{elite_copy.id}_elite"
            new_population.append(elite_copy)

        # Remplir le reste par tournoi + mutation
        while len(new_population) < POPULATION_SIZE:
            parent = tournament_selection(state.population, TOURNAMENT_SIZE, rng)
            child = mutate_seed(parent, rng)
            new_population.append(child)

        state.population = new_population
        logger.info("  Nouvelle population créée: %d individus", len(state.population))

    return state


# ===========================================================================
# INITIALISATION
# ===========================================================================


def load_historical_seeds() -> list[str]:
    """Charge les seeds historiques depuis multi_api_seed/config.py et depot-v*.

    Returns:
        Liste de textes de seeds historiques.
    """
    seeds: list[str] = []

    # 1. Seeds v4 depuis config.py
    if SEEDS_HISTORICAL:
        seeds.extend(SEEDS_HISTORICAL)
        logger.info("Chargé %d seeds depuis config.SEEDS_V4", len(SEEDS_HISTORICAL))

    # 2. Seeds depuis depot-v*/graine_*.txt
    depot_patterns = [
        BASE_DIR / "depot-v10" / "graine_v10.txt",
        BASE_DIR / "depot-v11" / "graine_v11.txt",
        BASE_DIR / "depot-v12" / "graine_v12.txt",
        BASE_DIR / "depot-v13" / "graine_v13.txt",
        BASE_DIR / "depot-v14" / "graine_v14.txt",
    ]
    for p in depot_patterns:
        if p.exists():
            try:
                text = p.read_text(encoding="utf-8").strip()
                if text:
                    seeds.append(text)
                    logger.info("Chargé seed depuis %s", p.name)
            except Exception as exc:
                logger.warning("Erreur lecture %s: %s", p.name, exc)

    if not seeds:
        # Seed par défaut si rien trouvé
        seeds.append(
            "Décrivez, sans analyser ni comparer ni conclure. Juste observer : "
            "un signal circule de seuil en seuil dans un réseau sans horloge. "
            "À chaque palier de transduction, que se passe-t-il dans le passage ?"
        )
        logger.warning("Aucune seed historique trouvée — utilisation de la seed par défaut.")

    return seeds


def load_api_clients(simulate: bool = False) -> dict[str, Callable]:
    """Charge les clients API disponibles depuis multi_api_seed/api_clients.py.

    Args:
        simulate: Si True, retourne un dict vide (mode simulation).

    Returns:
        Dict {provider_key: callable}
    """
    if simulate:
        return {}

    clients: dict[str, Callable] = {}
    try:
        from api_clients import query_deepseek, query_gemini, query_ai21
        # Vérifier que les providers sont configurés
        for key, fn, name in [
            ("deepseek", query_deepseek, "DeepSeek"),
            ("gemini", query_gemini, "Gemini"),
            ("ai21", query_ai21, "AI21"),
        ]:
            try:
                # Test rapide : vérifier que la clé API existe
                from config import PROVIDERS
                if key in PROVIDERS and PROVIDERS[key].api_key and PROVIDERS[key].api_key != "your-key-here":
                    clients[key] = fn
                    logger.info("API client chargé: %s", name)
                else:
                    logger.warning("API %s non configurée (clé manquante)", name)
            except Exception:
                logger.warning("API %s non disponible", name)
    except ImportError as exc:
        logger.warning("api_clients.py non trouvé: %s", exc)

    if not clients:
        logger.info("Aucun client API chargé — bascule en mode simulation.")

    return clients


def initialize_population(historical_seeds: list[str], rng: random.Random) -> list[SeedIndividual]:
    """Crée la population initiale à partir des seeds historiques.

    Si plus de seeds que POPULATION_SIZE, échantillonne aléatoirement.
    Si moins, duplique avec mutations pour atteindre POPULATION_SIZE.

    Args:
        historical_seeds: Liste des textes de seeds historiques.
        rng: Générateur aléatoire.

    Returns:
        Population initiale de SeedIndividual.
    """
    population: list[SeedIndividual] = []

    for i, text in enumerate(historical_seeds[:POPULATION_SIZE]):
        individual = SeedIndividual(
            id=f"seed_hist_{i}_gen0",
            text=text,
            generation=0,
        )
        population.append(individual)

    # Si pas assez de seeds historiques, en créer par mutation
    while len(population) < POPULATION_SIZE:
        parent = rng.choice(population)
        child = mutate_seed(parent, rng)
        child.id = f"seed_mut_{len(population)}_gen0"
        population.append(child)

    # Si trop de seeds, échantillonner
    if len(population) > POPULATION_SIZE:
        population = rng.sample(population, POPULATION_SIZE)

    logger.info("Population initiale: %d individus", len(population))
    for ind in population:
        logger.info("  %s: %s...", ind.id, ind.text[:80])

    return population


# ===========================================================================
# ORCHESTRATEUR PRINCIPAL
# ===========================================================================


def run_evolution(
    max_generations: int = MAX_GENERATIONS,
    seed: Optional[int] = None,
    simulate: bool = False,
    output_dir: Optional[Path] = None,
) -> EvolutionState:
    """Exécute la boucle d'évolution complète.

    Args:
        max_generations: Nombre maximum de générations.
        seed: Graine aléatoire pour la reproductibilité.
        simulate: Mode simulation (pas d'appels API).
        output_dir: Dossier de sortie pour les checkpoints.

    Returns:
        EvolutionState final.
    """
    if output_dir is None:
        output_dir = BASE_DIR / "evolution_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Charger l'historique et les clients API
    logger.info("=" * 60)
    logger.info("INITIALISATION DE LA BOUCLE ÉVOLUTIVE")
    logger.info("Mode: %s | Graine aléatoire: %s", "SIMULATION" if simulate else "RÉEL", seed)
    logger.info("=" * 60)

    historical_seeds = load_historical_seeds()
    api_clients = load_api_clients(simulate=simulate)

    if not api_clients and not simulate:
        logger.warning("Aucun client API disponible. Activation du mode simulation.")
        simulate = True

    # 2. Initialiser la population
    population = initialize_population(historical_seeds, rng)

    state = EvolutionState(
        population=population,
        generation=0,
    )

    # 3. Évaluer la génération 0
    logger.info("Évaluation de la génération initiale...")
    for idx, ind in enumerate(state.population):
        ind.fitness = evaluate_seed(ind, api_clients, simulate=simulate)
        logger.info("  %s: G_R=%.4f  Φ=%.4f  Fitness=%.4f",
                     ind.id, ind.fitness.g_r, ind.fitness.phi_ratio, ind.fitness.composite)

    # Meilleur initial
    state.population.sort(key=lambda ind: ind.fitness.composite, reverse=True)
    state.best_fitness = state.population[0].fitness.composite
    state.best_seed = copy.deepcopy(state.population[0])
    logger.info("Meilleur initial: G_R=%.4f Fitness=%.4f",
                 state.best_seed.fitness.g_r, state.best_fitness)

    # 4. Boucle d'évolution
    for gen in range(1, max_generations + 1):
        if state.converged:
            logger.info("Convergence atteinte à la génération %d — arrêt.", gen)
            break

        state = evolve_population(state, api_clients, simulate=simulate, rng=rng)

        # Sauvegarde checkpoint toutes les 5 générations
        if gen % 5 == 0:
            checkpoint = output_dir / f"checkpoint_gen{gen}_{timestamp}.json"
            try:
                checkpoint.write_text(
                    json.dumps(state.to_dict(), indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                logger.info("Checkpoint sauvegardé: %s", checkpoint.name)
            except Exception as exc:
                logger.warning("Erreur sauvegarde checkpoint: %s", exc)

    # 5. Rapport final
    logger.info("=" * 60)
    logger.info("RAPPORT FINAL D'ÉVOLUTION")
    logger.info("=" * 60)
    logger.info("Générations: %d", state.generation)
    logger.info("Convergé: %s", state.converged)
    logger.info("Meilleur fitness: %.4f", state.best_fitness)
    if state.best_seed:
        logger.info("Meilleur G_R: %.4f", state.best_seed.fitness.g_r)
        logger.info("Meilleur Φ: %.4f", state.best_seed.fitness.phi_ratio)
        logger.info("Seed optimale: %s", state.best_seed.text[:200])

    # 6. Sauvegarder le rapport final
    report = {
        "meta": {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "generations": state.generation,
            "max_generations": max_generations,
            "simulate": simulate,
            "random_seed": seed,
            "converged": state.converged,
        },
        "best_seed": {
            "id": state.best_seed.id if state.best_seed else None,
            "text": state.best_seed.text if state.best_seed else None,
            "fitness": {
                "g_r": state.best_seed.fitness.g_r if state.best_seed else None,
                "phi_ratio": state.best_seed.fitness.phi_ratio if state.best_seed else None,
                "constraints_met": state.best_seed.fitness.constraints_met if state.best_seed else None,
                "composite": state.best_seed.fitness.composite if state.best_seed else None,
            } if state.best_seed else None,
            "mutation_history": state.best_seed.mutation_log if state.best_seed else [],
        },
        "history": state.history,
        "population_summary": [
            {
                "id": ind.id,
                "g_r": ind.fitness.g_r,
                "phi": ind.fitness.phi_ratio,
                "fitness": ind.fitness.composite,
                "converged": ind.is_converged,
            }
            for ind in state.population
        ],
    }
    report_path = output_dir / f"evolution_report_{timestamp}.json"
    try:
        report_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Rapport final sauvegardé: %s", report_path)
    except Exception as exc:
        logger.error("Erreur sauvegarde rapport: %s", exc)

    return state


# ===========================================================================
# CLI
# ===========================================================================


def _parse_args() -> argparse.Namespace:
    import argparse
    parser = argparse.ArgumentParser(
        description="Evolutionary Seeder — boucle d'optimisation automatique des graines MTTV-FLP",
    )
    parser.add_argument(
        "--generations", type=int, default=MAX_GENERATIONS,
        help=f"Nombre maximum de générations (défaut: {MAX_GENERATIONS})",
    )
    parser.add_argument("--seed", type=int, default=None, help="Graine aléatoire pour reproductibilité")
    parser.add_argument(
        "--simulate", action="store_true",
        help="Mode simulation (pas d'appels API réels)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Dossier de sortie pour les rapports et checkpoints",
    )
    return parser.parse_args()


def main() -> None:
    import argparse
    args = _parse_args()

    output_dir = Path(args.output) if args.output else None
    state = run_evolution(
        max_generations=args.generations,
        seed=args.seed,
        simulate=args.simulate,
        output_dir=output_dir,
    )

    # Afficher le résumé
    print(f"\n{'='*60}")
    print(f"  ÉVOLUTION TERMINÉE")
    print(f"  Générations: {state.generation}")
    print(f"  Convergé:    {state.converged}")
    print(f"  Best G_R:    {state.best_seed.fitness.g_r if state.best_seed else 'N/A'}")
    print(f"  Best Phi:    {state.best_seed.fitness.phi_ratio if state.best_seed else 'N/A'}")
    print(f"  Best Fitness:{state.best_fitness}")
    if state.best_seed:
        print(f"\n  Seed optimale:")
        print(f"  {state.best_seed.text[:300]}")
    print(f"{'='*60}")
    sys.exit(0 if state.converged else 1)


if __name__ == "__main__":
    main()
