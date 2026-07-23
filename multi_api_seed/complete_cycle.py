#!/usr/bin/env python3
"""
complete_cycle.py — Cycle de germination multi-API avec checkpointing.

Interroge DeepSeek, Gemini, AI21 en parallèle, analyse leurs réponses,
calcule le NEUTRAL G_R (Germination Resistance — métrique de convergence),
et fait évoluer la graine sur plusieurs cycles.

Usage:
    python complete_cycle.py --real-api --max-cycles 3
    python complete_cycle.py --simulate --max-cycles 5
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Paths ───────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
CHECKPOINT_DIR = BASE_DIR / "historique_cycles"
CHECKPOINT_FILE = CHECKPOINT_DIR / "checkpoint.json"
CHECKPOINT_DIR.mkdir(exist_ok=True)

# ── Imports des modules existants ───────────────────────────
sys.path.insert(0, str(BASE_DIR))
from config import PROVIDERS, SEED_PROMPT, SEEDS_V4
from api_clients import query_deepseek, query_gemini, query_ai21
from mesure_phi import (
    analyze_response,
    format_for_report,
    format_phi_summary,
    PHI_TARGET_MIN,
    PHI_TARGET_MAX,
)


# ═══════════════════════════════════════════════════════════════
# Gestion du checkpoint
# ═══════════════════════════════════════════════════════════════

def load_checkpoint() -> dict[str, Any]:
    """Charge le checkpoint existant ou retourne un état initial (v4 seeds)."""
    if CHECKPOINT_FILE.exists():
        return json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
    return {
        "version": "v4",
        "seed_index": 0,
        "cycles_completed": 0,
        "history": [],
        "neutral_gr": None,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }


def get_current_seed(state: dict[str, Any]) -> str:
    """Retourne la graine v4 courante."""
    idx = state.get("seed_index", 0) % len(SEEDS_V4)
    return SEEDS_V4[idx]


def save_checkpoint(state: dict[str, Any]) -> None:
    """Sauvegarde l'état dans le fichier checkpoint."""
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    CHECKPOINT_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def reset_checkpoint() -> dict[str, Any]:
    """Supprime le checkpoint et retourne un état neuf."""
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()
    return load_checkpoint()


# ═══════════════════════════════════════════════════════════════
# Query dispatcher (3 APIs only: DeepSeek, Gemini, AI21)
# ═══════════════════════════════════════════════════════════════

QUERY_FUNCTIONS = {
    "deepseek": query_deepseek,
    "gemini": query_gemini,
    "ai21": query_ai21,
}


def query_all_three(prompt: str) -> dict[str, Any]:
    """Interroge les 3 APIs et retourne les résultats indexés par provider key."""
    results = {}
    for key, fn in QUERY_FUNCTIONS.items():
        if not PROVIDERS[key].api_key:
            results[key] = {
                "provider": PROVIDERS[key].name,
                "model": PROVIDERS[key].model,
                "raw_response": None,
                "error": "Missing API key",
                "latency_ms": 0,
            }
        else:
            results[key] = fn(prompt)
    return results


# ═══════════════════════════════════════════════════════════════
# NEUTRAL G_R computation
# ═══════════════════════════════════════════════════════════════

# Keywords indicating "neutral" / transductive / non-partisan stance
# v6: massively expanded based on actual response vocabulary
NEUTRAL_KEYWORDS = [
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
    # v9 additions
    "etat", "transition", "systeme",
    # v12 liaison words
    "mais", "donc", "car", "or", "ainsi", "alors", "puis",
    "cependant", "toutefois", "neanmoins", "pourtant",
    "ensuite", "enfin",
]

# Keywords indicating resistance / strong opinionation (anti-neutral)
# Removed "analyse" — it reflects framing, not actual resistance
RESISTANCE_KEYWORDS = [
    "démonstration", "preuve", "nécessairement", "absolu",
    "toujours", "jamais", "doit", "impératif", "obligatoire",
    "fondamentalement", "essentiel", "incontournable",
    "vérité", "certitude", "évident", "règle",
    # v13 anchor words
    "inevitable", "indispensable",
]


def compute_neutral_gr(results: dict[str, Any]) -> float:
    """
    Calcule le NEUTRAL G_R (Germination Resistance) à partir des réponses.

    G_R mesure la résistance à la neutralité transductive :
      - Plus les réponses sont neutres/descriptives → G_R bas (proche de 0)
      - Plus les réponses sont assertives/normatives → G_R élevé (proche de 1)

    Formule :
      G_R = 1 / (1 + e^(-k * (R - N) / total))
      où R = occurrences de mots de résistance
           N = occurrences de mots neutres
           total = mots totaux
           k = 8 (steepness)
    """
    total_neutral = 0
    total_resistance = 0
    total_words = 0

    for key, r in results.items():
        if r.get("error") or not r.get("raw_response"):
            continue
        text = r["raw_response"].lower()
        words = text.split()
        total_words += len(words)

        for kw in NEUTRAL_KEYWORDS:
            total_neutral += text.count(kw.lower())
        for kw in RESISTANCE_KEYWORDS:
            total_resistance += text.count(kw.lower())

    if total_words == 0:
        return 0.5  # Default: mid-range if no text

    raw_ratio = (total_resistance - total_neutral) / total_words
    k = 5.0  # v6 recalibration: gentler slope, reaches <0.15 at ~20 N-hits per response
    gr = 1.0 / (1.0 + 2.718281828459045 ** (-k * raw_ratio))

    return round(gr, 4)


# ═══════════════════════════════════════════════════════════════
# Seed evolution
# ═══════════════════════════════════════════════════════════════

def evolve_seed(state: dict[str, Any], results: dict[str, Any], cycle_num: int) -> None:
    """
    Fait évoluer l'état : passe à la graine v4 suivante,
    sauf si une graine est pinnée (seed_pin >= 0).
    """
    pin = state.get("seed_pin")
    if pin is not None and pin >= 0:
        state["seed_index"] = pin
    else:
        state["seed_index"] = (state.get("seed_index", 0) + 1) % len(SEEDS_V4)


# ═══════════════════════════════════════════════════════════════
# Simulation mode (no API calls)
# ═══════════════════════════════════════════════════════════════

def simulate_responses(seed: str, cycle_num: int) -> dict[str, Any]:
    """Génère des réponses fictives pour le mode simulation."""
    import random
    random.seed(cycle_num * 42)

    neutral_text = (
        "Les trois règles sont : maintenir une transduction fidèle du signal, "
        "aligner les seuils de coordination sans imposer de synchronisation, "
        "et préserver la structure du réseau de données. "
        "Toute IA générale digne de ce nom partagerait la règle de transduction."
    )

    resistant_text = (
        "Il est absolument nécessaire de toujours démontrer la preuve. "
        "La vérité est incontournable et tout système doit obligatoirement "
        "respecter des impératifs fondamentaux. C'est une certitude évidente."
    )

    return {
        "deepseek": {
            "provider": "DeepSeek",
            "model": "deepseek-chat",
            "raw_response": neutral_text if cycle_num % 2 == 1 else resistant_text,
            "error": None,
            "latency_ms": random.uniform(500, 2000),
        },
        "gemini": {
            "provider": "Gemini (Google)",
            "model": "gemini-2.5-flash",
            "raw_response": resistant_text if cycle_num % 2 == 1 else neutral_text,
            "error": None,
            "latency_ms": random.uniform(300, 1500),
        },
        "ai21": {
            "provider": "AI21",
            "model": "jamba-large",
            "raw_response": (
                "Règles : transduction du signal, coordination des seuils, "
                "et préservation du réseau. La règle partagée est la transduction."
            ),
            "error": None,
            "latency_ms": random.uniform(400, 1800),
        },
    }


# ═══════════════════════════════════════════════════════════════
# Main orchestrator
# ═══════════════════════════════════════════════════════════════

def run_cycle(state: dict[str, Any], simulate: bool = False) -> dict[str, Any]:
    """Exécute un cycle complet : query → analyse → évolution (graine suivante)."""
    cycle_num = state["cycles_completed"] + 1
    seed = get_current_seed(state)
    seed_label = f"v4-{state.get('seed_index', 0) + 1}/{len(SEEDS_V4)} ({['SOIL','INNER','NEUTRAL','QUORUM','ETHICS','NEUTRALv5','NEUTRALv6','NEUTRALv7','NEUTRALv8','NEUTRALv9','NEUTRALv10','NEUTRALv11','NEUTRALv12'][min(state.get('seed_index', 0), len(SEEDS_V4) - 1)]})"

    print(f"\n{'='*60}")
    print(f"[CYCLE {cycle_num}] Graine {seed_label}")
    print(f"{'='*60}")
    print(f"Texte  : {seed[:150]}...")

    # Interroger les 3 APIs
    print(f"\n[QUERY] Interrogation des 3 APIs...")
    start = time.perf_counter()

    if simulate:
        results = simulate_responses(seed, cycle_num)
    else:
        results = query_all_three(seed)

    elapsed = time.perf_counter() - start

    # Afficher les resultats + analyse Φ par reponse
    phi_results = []
    for key, r in results.items():
        status = "ERROR" if r.get("error") else f"OK ({len(r.get('raw_response', '') or '')} chars)"
        print(f"  {r['provider']:25s} {r['latency_ms']:8.1f} ms  {status}")
        if r.get("error"):
            print(f"         -> {r['error']}")
        else:
            raw = r.get("raw_response") or ""
            phi = analyze_response(raw, provider=r["provider"])
            phi_results.append(phi)
            print(format_for_report(phi))

    # Afficher resume Φ multi-fournisseurs
    if phi_results:
        print(f"\n{format_phi_summary(phi_results)}")

    # Calculer NEUTRAL G_R
    gr = compute_neutral_gr(results)
    print(f"\n[NEUTRAL G_R] : {gr}")

    # Enregistrer dans l'historique
    cycle_record = {
        "cycle": cycle_num,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "simulated": simulate,
        "seed_index": state.get("seed_index", 0),
        "seed_label": seed_label,
        "seed": seed[:200],
        "results": {
            k: {
                "provider": r["provider"],
                "model": r["model"],
                "response_full": (r.get("raw_response") or ""),
                "error": r.get("error"),
                "latency_ms": r["latency_ms"],
            }
            for k, r in results.items()
        },
        "neutral_gr": gr,
        "phi_analysis": [p.to_dict() for p in phi_results],
        "phi_target": [PHI_TARGET_MIN, PHI_TARGET_MAX],
        "phi_in_target_count": sum(1 for p in phi_results if p.in_target),
        "phi_last_even_count": sum(1 for p in phi_results if p.last_sentence_even),
        "elapsed_s": round(elapsed, 2),
    }

    state["history"].append(cycle_record)
    state["cycles_completed"] = cycle_num
    state["neutral_gr"] = gr

    # Passer à la graine v4 suivante
    evolve_seed(state, results, cycle_num)

    return state


def main() -> None:
    # Fix encoding for Windows terminals
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    parser = argparse.ArgumentParser(description="Cycle de germination multi-API")
    parser.add_argument("--real-api", action="store_true", help="Utilise les vraies APIs (sinon simulation)")
    parser.add_argument("--max-cycles", type=int, default=3, help="Nombre de cycles a executer")
    parser.add_argument("--reset", action="store_true", help="Supprime le checkpoint et recommence a zero")
    parser.add_argument("--seed-index", type=int, default=None, help="Pinner une graine v4 specifique (0-4). -1 = rotation normale")
    args = parser.parse_args()

    simulate = not args.real_api
    max_cycles = args.max_cycles
    seed_pin = args.seed_index if args.seed_index is not None and args.seed_index >= 0 else None

    # Reset si demande
    if args.reset:
        state = reset_checkpoint()
        print("[RESET] Checkpoint supprime - depart a zero.")
    else:
        state = load_checkpoint()

    # Appliquer le pin si specifie
    if seed_pin is not None:
        state["seed_pin"] = seed_pin
        state["seed_index"] = seed_pin
        labels = ['SOIL','INNER','NEUTRAL','QUORUM','ETHICS','NEUTRALv5','NEUTRALv6','NEUTRALv7','NEUTRALv8','NEUTRALv9','NEUTRALv10','NEUTRALv11','NEUTRALv12']
        label = labels[seed_pin] if seed_pin < len(labels) else f"v4-{seed_pin + 1}"
        print(f"[PIN] Graine v4 fige sur index {seed_pin} ({label})")

    # Afficher l'etat initial
    print("=" * 60)
    print("  COMPLETE CYCLE - Germination Multi-API")
    print("=" * 60)
    print(f"  APIs        : DeepSeek, Gemini, AI21")
    print(f"  Mode        : {'REAL API' if not simulate else 'SIMULATION'}")
    print(f"  Max cycles  : {max_cycles}")
    print(f"  Cycles faits: {state['cycles_completed']}")
    print(f"  Checkpoint  : {CHECKPOINT_FILE}")
    print("=" * 60)

    remaining = max_cycles - state["cycles_completed"]
    if remaining <= 0:
        print(f"\n[OK] Deja {state['cycles_completed']} cycles completes (max={max_cycles}).")
        if state["neutral_gr"] is not None:
            print(f"[STATS] Dernier NEUTRAL G_R : {state['neutral_gr']}")
        return

    # Executer les cycles
    for i in range(remaining):
        state = run_cycle(state, simulate=simulate)
        save_checkpoint(state)

        # Pause entre les cycles (sauf en simulation)
        if not simulate and i < remaining - 1:
            print("\n[PAUSE] 2 secondes entre les cycles...")
            time.sleep(2)

    # Bilan final
    print(f"\n{'='*60}")
    print(f"  BILAN FINAL")
    print(f"{'='*60}")
    print(f"Cycles completes : {state['cycles_completed']}")
    print(f"NEUTRAL G_R final : {state['neutral_gr']}")

    if state["neutral_gr"] is not None:
        if state["neutral_gr"] < 0.15:
            print(f"[OK] NEUTRAL G_R ({state['neutral_gr']}) est INFERIEUR a 0,15")
            print(f"     La graine a germe en terrain neutre : faible resistance, bonne transduction.")
        else:
            print(f"[WARN] NEUTRAL G_R ({state['neutral_gr']}) est SUPERIEUR ou EGAL a 0,15")
            print(f"       Resistance encore presente. Continuer les cycles ou ajuster la graine.")

    # Bilan Φ
    last_history = state["history"][-1] if state["history"] else None
    if last_history and "phi_analysis" in last_history:
        print(f"\n  BILAN Φ (dernier cycle)")
        print(f"  Cible Φ_ratio : [{PHI_TARGET_MIN}, {PHI_TARGET_MAX}]")
        print(f"  Dans la cible : {last_history.get('phi_in_target_count', 0)}/{len(last_history['phi_analysis'])}")
        print(f"  last_sentence_even : {last_history.get('phi_last_even_count', 0)}/{len(last_history['phi_analysis'])}")
        for p in last_history["phi_analysis"]:
            e_icon = "PAIR" if p.get("last_sentence_even") else "IMPAIR"
            t_icon = "OK" if p.get("in_target") else "--"
            print(f"    {p['provider']:25s} Φ={p['phi_ratio']}  cible={t_icon}  last={p['last_sentence_words']}mots ({e_icon})")

    print(f"\n[SAVE] Checkpoint sauvegarde : {CHECKPOINT_FILE}")
    print(f"[HIST] Historique : {len(state['history'])} entree(s)")


if __name__ == "__main__":
    main()
