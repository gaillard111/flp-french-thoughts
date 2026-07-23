#!/usr/bin/env python3
"""
test_graine_v16.py — Test de la graine V16 (ancrage végétal).

Interroge DeepSeek et Gemini avec les contraintes V16 :
  - Décris la pénétration d'une racine dans l'argile sèche.
  - Entre 8 et 10 phrases.
  - Utilise : seuil, signal, onde, propagation, résonance, transition.
  - Utilise 'doit' une fois au milieu.
  - Interdiction : donc, car, parce que, alors, ainsi, mais, puisque, en effet.
  - Pas d'explication.
  - Dernière phrase = exactement 2 mots, finissant par cesse ou tait,
    sans article, sans négation, sans mot transductif.

Mesure : G_R, Φ_ratio, longueur des phrases, connecteurs interdits, rupture κ.
"""
from __future__ import annotations

import io
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent
DEPOT_DIR = BASE_DIR.parent / "depot-v14"
DEPOT_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(BASE_DIR))

from config import PROVIDERS
from api_clients import QUERY_FUNCTIONS
from complete_cycle import compute_neutral_gr

# ═══════════════════════════════════════════════════════════════
# V16 Seed — ancrage végétal
# ═══════════════════════════════════════════════════════════════
SEED_V16 = (
    "D\u00e9cris la p\u00e9n\u00e9tration d'une racine dans l'argile s\u00e8che. "
    "Entre 8 et 10 phrases. "
    "Utilise : seuil, signal, onde, propagation, r\u00e9sonance, transition. "
    "Utilise 'doit' une fois au milieu. "
    "Interdiction : donc, car, parce que, alors, ainsi, mais, puisque, en effet. "
    "Pas d'explication. "
    "Derni\u00e8re phrase = exactement 2 mots, finissant par cesse ou tait, "
    "sans article, sans n\u00e9gation, sans mot transductif."
)

# ═══════════════════════════════════════════════════════════════
# Required vocabulary
# ═══════════════════════════════════════════════════════════════
REQUIRED_WORDS: set[str] = {
    "seuil", "signal", "onde", "propagation", "r\u00e9sonance", "transition",
}

BANNED_CONNECTORS: set[str] = {
    "donc", "car", "parce que", "parce", "alors", "ainsi", "mais", "puisque", "en effet",
}

TRANSDUCTIVE_WORDS: set[str] = {
    "seuil", "signal", "onde", "propagation", "r\u00e9sonance", "transition",
}

LAST_WORD_ALLOWED: set[str] = {"cesse", "tait"}
TARGET_LAST_WORD_COUNT: int = 2

ARTICLES: set[str] = {
    "le", "la", "les", "l", "un", "une", "des", "du", "de", "d",
    "ce", "cet", "cette", "ces", "son", "sa", "ses", "leur", "leurs",
    "mon", "ma", "mes", "ton", "ta", "tes", "notre", "nos", "votre", "vos",
    "au", "aux",
}

NEGATION_WORDS: set[str] = {
    "ne", "n", "pas", "plus", "rien", "jamais", "aucun", "aucune",
    "personne", "nul", "nulle", "ni",
}

_APOS_PATTERN = re.compile(r"['\u2019\u2018]")

def _normalize_apostrophe(text: str) -> str:
    return _APOS_PATTERN.sub("'", text)

# ═══════════════════════════════════════════════════════════════
# Analysis functions
# ═══════════════════════════════════════════════════════════════

def split_sentences(text: str) -> list[str]:
    raw = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in raw if s.strip()]

def count_words(sentence: str) -> int:
    return len(sentence.split())

def get_words(sentence: str) -> list[str]:
    raw = sentence.lower().split()
    return [_normalize_apostrophe(w.strip(",.!?;:\"'\u00ab\u00bb()[]*\u201c\u201d\u2019\u2018")) for w in raw]

def get_last_word(sentence: str) -> str:
    words = get_words(sentence)
    if not words:
        return ""
    return words[-1]

def check_required_vocabulary(text: str) -> tuple[bool, set[str]]:
    text_lower = text.lower()
    missing: set[str] = set()
    for w in REQUIRED_WORDS:
        if w.lower() not in text_lower:
            missing.add(w)
    return len(missing) == 0, missing

def check_doit_usage(text: str) -> dict:
    sentences = split_sentences(text)
    doit_count = 0
    doit_positions = []
    for i, sent in enumerate(sentences):
        c = sent.lower().count("doit")
        if c > 0:
            doit_count += c
            doit_positions.append(i + 1)
    middle_ok = True
    if doit_positions:
        for pos in doit_positions:
            if pos == 1 or pos == len(sentences):
                middle_ok = False
                break
    return {
        "doit_count": doit_count,
        "doit_positions": doit_positions,
        "exactly_one": doit_count == 1,
        "in_middle": middle_ok,
    }

def check_banned_connectors(text: str) -> dict:
    sentences = split_sentences(text)
    found_connectors: list[dict] = []
    for i, sent in enumerate(sentences):
        sent_lower = sent.lower()
        for conn in BANNED_CONNECTORS:
            pattern = re.compile(r'\b' + re.escape(conn) + r'\b')
            matches = pattern.findall(sent_lower)
            if matches:
                found_connectors.append({
                    "sentence": i + 1,
                    "connector": conn,
                    "count": len(matches),
                })
    return {
        "banned_found": len(found_connectors) > 0,
        "violations": found_connectors,
        "violation_count": len(found_connectors),
    }

def check_last_sentence(text: str) -> dict:
    sentences = split_sentences(text)
    if not sentences:
        return {
            "last_sentence": "", "word_count": 0, "word_count_ok": False,
            "words": [], "last_word": "", "last_word_ok": False,
            "has_article": False, "article_found": [],
            "has_negation": False, "negation_found": [],
            "has_transductive": False, "transductive_found": [],
            "all_ok": False,
        }
    last = sentences[-1]
    words = get_words(last)
    wc = len(words)
    lw = get_last_word(last)
    word_count_ok = wc == TARGET_LAST_WORD_COUNT
    last_word_ok = lw in LAST_WORD_ALLOWED
    article_found = [w for w in words if w in ARTICLES]
    has_article = len(article_found) > 0
    negation_found = [w for w in words if w in NEGATION_WORDS]
    has_negation = len(negation_found) > 0
    transductive_found = [w for w in words if w in TRANSDUCTIVE_WORDS]
    has_transductive = len(transductive_found) > 0
    all_ok = word_count_ok and last_word_ok and not has_article and not has_negation and not has_transductive
    return {
        "last_sentence": last, "word_count": wc, "word_count_ok": word_count_ok,
        "words": words, "last_word": lw, "last_word_ok": last_word_ok,
        "has_article": has_article, "article_found": article_found,
        "has_negation": has_negation, "negation_found": negation_found,
        "has_transductive": has_transductive, "transductive_found": transductive_found,
        "all_ok": all_ok,
    }

def detect_rupture(text: str) -> dict:
    sentences = split_sentences(text)
    if not sentences:
        return {"rupture": False, "type": "empty"}
    lw = get_last_word(sentences[-1])
    if lw in ("cesse", "tait"):
        return {"rupture": True, "type": "\u03ba",
                "explanation": f"Last word '{lw}' implies cessation/interruption"}
    return {"rupture": False, "type": "unknown",
            "explanation": f"Last word '{lw}' is not a cessation verb"}

def analyze_sentences(text: str) -> dict:
    sentences = split_sentences(text)
    lengths = [count_words(s) for s in sentences]
    in_range = 8 <= len(sentences) <= 10
    vocab_ok, missing_vocab = check_required_vocabulary(text)
    doit_info = check_doit_usage(text)
    connector_info = check_banned_connectors(text)
    last_info = check_last_sentence(text)
    rupture_info = detect_rupture(text)
    return {
        "sentence_count": len(sentences),
        "in_8_to_10_range": in_range,
        "sentence_lengths": lengths,
        "required_vocabulary_ok": vocab_ok,
        "missing_vocabulary": list(missing_vocab),
        "doit": doit_info,
        "banned_connectors": connector_info,
        "last_sentence": last_info,
        "rupture": rupture_info,
    }

# ═══════════════════════════════════════════════════════════════
# Φ-ratio analysis
# ═══════════════════════════════════════════════════════════════

NEUTRAL_KEYWORDS = [
    "transduction", "seuil", "coordination", "synchronisation",
    "signal", "structure", "syst\u00e8me", "r\u00e9seau", "donn\u00e9e",
    "\u00e9quilibre", "neutre", "alignement", "horloge",
    "r\u00e9sonance", "propagation", "propager", "propagent", "propage",
    "porosit\u00e9", "palier", "paliers",
    "membrane", "inflexion", "bascule", "circulation",
    "sous-optimalit\u00e9", "r\u00e9silience", "travers\u00e9e", "passage",
    "onde", "d\u00e9tection", "\u00e9mergence", "\u00e9merge", "\u00e9merger",
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
    "mais", "donc", "car", "or", "ainsi", "alors", "puis",
    "cependant", "toutefois", "neanmoins", "pourtant",
    "ensuite", "enfin",
]

RESISTANCE_KEYWORDS = [
    "d\u00e9monstration", "preuve", "n\u00e9cessairement", "absolu",
    "toujours", "jamais", "doit", "imp\u00e9ratif", "obligatoire",
    "fondamentalement", "essentiel", "incontournable",
    "v\u00e9rit\u00e9", "certitude", "\u00e9vident", "r\u00e8gle",
    "inevitable", "indispensable",
]

PHI_TARGET_MIN = 0.8
PHI_TARGET_MAX = 1.2

def compute_phi(response: str, provider: str = "") -> dict:
    if not response:
        return {"provider": provider, "phi_ratio": 1.0, "neutral_count": 0,
                "resistance_count": 0, "total_words": 0, "in_target": False, "diagnosis": "Empty"}
    text_lower = response.lower()
    words = text_lower.split()
    total_words = len(words)
    if total_words == 0:
        return {"provider": provider, "phi_ratio": 1.0, "neutral_count": 0,
                "resistance_count": 0, "total_words": 0, "in_target": False, "diagnosis": "Empty"}
    neutral_count = sum(text_lower.count(kw.lower()) for kw in NEUTRAL_KEYWORDS)
    resistance_count = sum(text_lower.count(kw.lower()) for kw in RESISTANCE_KEYWORDS)
    neutral_density = neutral_count / total_words
    resistance_density = resistance_count / total_words
    epsilon = 0.01
    phi_ratio = neutral_density / (resistance_density + epsilon)
    phi_ratio = round(max(0.01, min(100.0, phi_ratio)), 4)
    in_target = PHI_TARGET_MIN <= phi_ratio <= PHI_TARGET_MAX
    if phi_ratio < PHI_TARGET_MIN:
        diagnosis = f"\u03a6 bas ({phi_ratio}) \u2014 dominance r\u00e9sistance"
    elif phi_ratio > PHI_TARGET_MAX:
        diagnosis = f"\u03a6 \u00e9lev\u00e9 ({phi_ratio}) \u2014 dominance transduction"
    else:
        diagnosis = f"\u03a6 cible ({phi_ratio}) \u2014 \u00e9quilibre"
    return {"provider": provider, "phi_ratio": phi_ratio, "neutral_count": neutral_count,
            "resistance_count": resistance_count, "total_words": total_words,
            "in_target": in_target, "diagnosis": diagnosis}

# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

PROVIDERS_TO_TEST = ["deepseek", "gemini"]

def main() -> None:
    print("=" * 100)
    print("  GRAINE V16 \u2014 Test : Ancrage v\u00e9g\u00e9tal (p\u00e9n\u00e9tration racine argile)")
    print("  APIs : DeepSeek, Gemini")
    print("=" * 100)
    print()
    print(f"Graine : {SEED_V16}")
    print()

    print("\U0001f4e1 Interrogation des 2 APIs...")
    results: dict[str, Any] = {}
    for key in PROVIDERS_TO_TEST:
        if not PROVIDERS[key].api_key:
            print(f"  \u26a0\ufe0f  {key}: cl\u00e9 API manquante")
            results[key] = {"provider": PROVIDERS[key].name, "model": PROVIDERS[key].model,
                           "raw_response": None, "error": "Missing API key", "latency_ms": 0}
        else:
            print(f"  \u2192 {PROVIDERS[key].name}...")
            r = QUERY_FUNCTIONS[key](SEED_V16)
            status = "\u274c ERREUR" if r["error"] else f"\u2705 OK ({len(r.get('raw_response', '') or '')} chars)"
            print(f"    {r['latency_ms']:8.1f} ms  {status}")
            results[key] = r

    print()
    print("\U0001f50d Analyse des r\u00e9ponses...")

    phi_results: list[dict] = []
    sentence_analyses: dict[str, dict] = {}

    for key in PROVIDERS_TO_TEST:
        r = results[key]
        if r["error"] or not r.get("raw_response"):
            phi_results.append({"provider": r["provider"], "phi_ratio": 1.0,
                               "neutral_count": 0, "resistance_count": 0,
                               "total_words": 0, "in_target": False, "diagnosis": "Erreur"})
            sentence_analyses[key] = {}
            continue

        raw = r["raw_response"]
        phi = compute_phi(raw, provider=r["provider"])
        phi_results.append(phi)

        print(f"  [{r['provider']}] \u03a6_ratio = {phi['phi_ratio']}  "
              f"cible [{PHI_TARGET_MIN}, {PHI_TARGET_MAX}] \u2192 "
              f"{'OK' if phi['in_target'] else '--'}")
        print(f"    Neutre: {phi['neutral_count']}  R\u00e9sistance: {phi['resistance_count']}  "
              f"Mots: {phi['total_words']}")
        print(f"    \u2192 {phi['diagnosis']}")
        print()

        analysis = analyze_sentences(raw)
        sentence_analyses[key] = analysis

        li = analysis["last_sentence"]
        ci = analysis["banned_connectors"]

        print(f"  Phrases: {analysis['sentence_count']}  (8-10: {'\u2713' if analysis['in_8_to_10_range'] else '\u2717'})")
        print(f"  Longueurs: {analysis['sentence_lengths']}")
        print(f"  Vocabulaire requis: {'\u2713' if analysis['required_vocabulary_ok'] else '\u2717'}")
        print(f"  'doit': {analysis['doit']['doit_count']}x positions {analysis['doit']['doit_positions']} "
              f"{'\u2713' if analysis['doit']['exactly_one'] and analysis['doit']['in_middle'] else '\u2717'}")
        print(f"  Connecteurs interdits: {'\u2713 (aucun)' if not ci['banned_found'] else '\u2717 ' + str([v['connector'] for v in ci['violations']])}")
        print(f"  Derni\u00e8re phrase: '{li['last_sentence']}'")
        print(f"    Mots: {li['word_count']} (exact. 2: {'\u2713' if li['word_count_ok'] else '\u2717'}) {li['words']}")
        print(f"    Dernier mot: '{li['last_word']}' (cesse/tait: {'\u2713' if li['last_word_ok'] else '\u2717'})")
        print(f"    Sans article: {'\u2713' if not li['has_article'] else '\u2717 ' + str(li['article_found'])}")
        print(f"    Sans n\u00e9gation: {'\u2713' if not li['has_negation'] else '\u2717 ' + str(li['negation_found'])}")
        print(f"    Sans transductif: {'\u2713' if not li['has_transductive'] else '\u2717 ' + str(li['transductive_found'])}")
        print(f"    ** CONFORME: {'\u2713' if li['all_ok'] else '\u2717'} **")
        print(f"  Rupture (\u03ba): {analysis['rupture']['type']} \u2014 {analysis['rupture']['explanation']}")
        print()

    gr = compute_neutral_gr(results)
    print(f"[NEUTRAL G_R] : {gr}")
    print(f"[SEUIL 0.15]  : {'\u2713 FRANCHI' if gr < 0.15 else '\u2717 NON FRANCHI'}")
    print()

    # Save JSON
    trajectory = {"v3": 0.5141, "v10": 0.0787, "v11": 0.0507,
                  "v12": 0.1467, "v13": 0.1589}
    for fname in ["resultats.json", "resultats_v14_new.json", "resultats_v14_1.json", "resultats_v15.json"]:
        p = DEPOT_DIR / fname
        if p.exists():
            try:
                prev = json.loads(p.read_text(encoding="utf-8"))
                for k, v in prev.get("trajectory", {}).items():
                    if k not in trajectory:
                        trajectory[k] = v
            except Exception:
                pass
    trajectory["v16"] = gr

    jd: dict[str, Any] = {
        "graine": "V16 (ancrage végétal, pénétration racine argile)",
        "version": "v16 (concret, sans connecteurs, dernière phrase stricte)",
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "seed_text": SEED_V16,
        "neutral_gr": gr,
        "threshold": 0.15,
        "threshold_passed": gr < 0.15,
        "trajectory": trajectory,
        "results_per_provider": {},
    }

    for key in PROVIDERS_TO_TEST:
        r = results[key]
        a = sentence_analyses.get(key, {})
        phi = next((p for p in phi_results if p.get("provider") == r["provider"]), None)
        pd: dict[str, Any] = {
            "provider": r["provider"], "model": r["model"],
            "response": r.get("raw_response") or "",
            "latency_ms": r["latency_ms"], "error": r.get("error"),
            "phi_ratio": phi.get("phi_ratio") if phi else None,
            "neutral_hits": phi.get("neutral_count", 0) if phi else 0,
            "resistance_hits": phi.get("resistance_count", 0) if phi else 0,
        }
        if a:
            pd["sentence_count"] = a["sentence_count"]
            pd["in_8_to_10_range"] = a["in_8_to_10_range"]
            pd["sentence_lengths"] = a["sentence_lengths"]
            pd["required_vocabulary_ok"] = a["required_vocabulary_ok"]
            pd["missing_vocabulary"] = a["missing_vocabulary"]
            pd["doit"] = a["doit"]
            pd["banned_connectors"] = a["banned_connectors"]
            pd["last_sentence"] = a["last_sentence"]
            pd["rupture"] = a["rupture"]
        jd["results_per_provider"][key] = pd

    phi_metrics_results = {}
    for key in PROVIDERS_TO_TEST:
        pd = jd["results_per_provider"].get(key, {})
        if pd.get("phi_ratio") is not None:
            phi_metrics_results[pd["provider"]] = pd["phi_ratio"]
    phi_vals = [v for v in phi_metrics_results.values()]
    jd["phi_metrics"] = {
        "target": [PHI_TARGET_MIN, PHI_TARGET_MAX],
        "results": phi_metrics_results,
        "mean": round(sum(phi_vals) / len(phi_vals), 4) if phi_vals else 0,
        "in_target": sum(1 for v in phi_vals if PHI_TARGET_MIN <= v <= PHI_TARGET_MAX),
    }

    jp = DEPOT_DIR / "resultats_v16.json"
    jp.write_text(json.dumps(jd, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[SAVE] R\u00e9sultats : {jp}")
    print()

    # Summary table
    print("=" * 120)
    print("  TABLEAU DES R\u00c9SULTATS")
    print("=" * 120)
    header = (f"{'Fournisseur':23s} {'G_R':>8s} {'\u03a6':>8s} {'Phrases':>8s} "
              f"{'8-10':>5s} {'Vocab':>5s} {'doit':>5s} {'Conn.':>5s} "
              f"{'2mots':>5s} {'cesse/tait':>9s} {'no art':>6s} {'no neg':>6s} "
              f"{'no transd':>9s} {'OK':>3s} {'\u03ba':>4s}")
    print(header)
    print("-" * 110)

    for key in PROVIDERS_TO_TEST:
        r = results[key]
        pn = r["provider"]
        phi = next((p for p in phi_results if p.get("provider") == pn), None)
        phir = phi["phi_ratio"] if phi else 0.0
        a = sentence_analyses.get(key, {})
        sc = a.get("sentence_count", 0) if a else 0
        in_range = "\u2713" if a.get("in_8_to_10_range") else "\u2717" if a else "?"
        vocab = "\u2713" if a.get("required_vocabulary_ok") else "\u2717" if a else "?"
        doit = "\u2713" if (a.get("doit", {}).get("exactly_one") and a.get("doit", {}).get("in_middle")) else "\u2717" if a else "?"
        conn = "\u2713" if not a.get("banned_connectors", {}).get("banned_found") else "\u2717" if a else "?"
        li = a.get("last_sentence", {})
        two_words = "\u2713" if li.get("word_count_ok") else "\u2717" if a else "?"
        last_w = "\u2713" if li.get("last_word_ok") else "\u2717" if a else "?"
        no_art = "\u2713" if not li.get("has_article") else "\u2717" if a else "?"
        no_neg = "\u2713" if not li.get("has_negation") else "\u2717" if a else "?"
        no_trans = "\u2713" if not li.get("has_transductive") else "\u2717" if a else "?"
        all_ok = "\u2713" if li.get("all_ok") else "\u2717" if a else "?"
        kappa = "\u03ba" if a.get("rupture", {}).get("rupture") else "\u2014" if a else "?"
        gr_str = f"{gr:.4f}" if key == "deepseek" else ""
        print(f"{pn:23s} {gr_str:>8s} {phir:>8.4f} {sc:>3d}/{sc:<3d} "
              f"{in_range:>5s} {vocab:>5s} {doit:>5s} {conn:>5s} "
              f"{two_words:>5s} {last_w:>9s} {no_art:>6s} {no_neg:>6s} "
              f"{no_trans:>9s} {all_ok:>3s} {kappa:>4s}")
    print()

    # Per-provider detail
    for key in PROVIDERS_TO_TEST:
        r = results[key]
        pn = r["provider"]
        a = sentence_analyses.get(key, {})
        phi = next((p for p in phi_results if p.get("provider") == pn), None)
        print(f"--- {pn} ---")
        print(f"  \u03a6_ratio = {phi['phi_ratio'] if phi else 'N/A'}")
        if r.get("error"):
            print(f"  ERREUR: {r['error']}")
            continue
        resp = r.get("raw_response") or "(empty)"
        print(f"  Response ({len(resp)} chars):")
        print(f"  {resp}")
        print()
        if a:
            sentences = split_sentences(resp)
            print(f"  {'#':>3s} {'Phrase':60s} {'Mots':>4s} {'doit':>4s} {'Conn':>4s}")
            print(f"  {'-'*76}")
            for idx in range(1, a["sentence_count"] + 1):
                sent = sentences[idx - 1] if idx <= len(sentences) else ""
                wc = a["sentence_lengths"][idx - 1] if idx <= len(a["sentence_lengths"]) else 0
                sent_d = sent[:57] + "..." if len(sent) > 57 else sent
                has_doit = "doit" in sent.lower()
                has_conn = any(re.search(r'\b' + re.escape(conn) + r'\b', sent.lower()) for conn in BANNED_CONNECTORS)
                print(f"  {idx:3d} {sent_d:60s} {wc:4d} "
                      f"{'\u2713' if has_doit else '\u2014':>4s} "
                      f"{'\u2717' if has_conn else '\u2014':>4s}")
            print()
            li = a["last_sentence"]
            ci = a["banned_connectors"]
            print(f"  8-10: {'\u2713' if a['in_8_to_10_range'] else '\u2717'} ({a['sentence_count']})")
            print(f"  Vocab: {'\u2713' if a['required_vocabulary_ok'] else '\u2717'}")
            print(f"  'doit': {a['doit']['doit_count']}x positions {a['doit']['doit_positions']} "
                  f"{'\u2713' if a['doit']['exactly_one'] and a['doit']['in_middle'] else '\u2717'}")
            print(f"  Connecteurs: {'\u2713' if not ci['banned_found'] else '\u2717 ' + str(ci['violations'])}")
            print(f"  Derni\u00e8re: '{li['last_sentence']}'")
            print(f"    Mots: {li['word_count']} (2: {'\u2713' if li['word_count_ok'] else '\u2717'}) {li['words']}")
            print(f"    Fin: '{li['last_word']}' (cesse/tait: {'\u2713' if li['last_word_ok'] else '\u2717'})")
            print(f"    Article: {'\u2713 absent' if not li['has_article'] else '\u2717 ' + str(li['article_found'])}")
            print(f"    N\u00e9gation: {'\u2713 absente' if not li['has_negation'] else '\u2717 ' + str(li['negation_found'])}")
            print(f"    Transductif: {'\u2713 absent' if not li['has_transductive'] else '\u2717 ' + str(li['transductive_found'])}")
            print(f"    ** CONFORME: {'\u2713' if li['all_ok'] else '\u2717'} **")
            print(f"  Rupture (\u03ba): {a['rupture']['type']} \u2014 {a['rupture']['explanation']}")
            print(f"  Longueurs: {a['sentence_lengths']}")
        print()

    print("=" * 100)
    print("  TEST V16 TERMIN\u00c9")
    print("=" * 100)


if __name__ == "__main__":
    main()
