#!/usr/bin/env python3
"""
test_graine_v14.py — Test de la graine V14 (Seuil de coupure du flux).

Interroge DeepSeek, Gemini, AI21 avec les contraintes V14 :
  - Phrase courte. Pas plus de 7 mots par phrase.
  - La phrase suivante reprend exactement là où la précédente s'arrête.
  - Vocabulaire restreint (10 mots transductifs)
  - Ne raconte pas. Ne prescris pas.
  - Trouve le moment où le flux doit s'arrêter.
  - Dernière phrase : nombre de mots unique parmi toutes les phrases.
  - 8 à 10 phrases.

Mesure : G_R, Φ_ratio, longueur phrase, conformité aux contraintes.
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
from mesure_phi import analyze_response, PhiResult, format_for_report
from complete_cycle import compute_neutral_gr

# ═══════════════════════════════════════════════════════════════
# V14 Seed
# ═══════════════════════════════════════════════════════════════
SEED_V14 = (
    "Phrase courte. Pas plus de 7 mots par phrase. "
    "La phrase suivante reprend exactement l\u00e0 o\u00f9 la pr\u00e9c\u00e9dente s'arr\u00eate. "
    "Utilise ces mots : seuil, signal, propagation, transduction, impulsion, "
    "onde, bascule, r\u00e9sonance, \u00e9tat, transition. "
    "Ne raconte pas. Ne prescris pas. "
    "Trouve le moment o\u00f9 le flux doit s'arr\u00eater. "
    "La derni\u00e8re phrase aura un nombre de mots diff\u00e9rent des pr\u00e9c\u00e9dentes. "
    "8 \u00e0 10 phrases."
)

# ═══════════════════════════════════════════════════════════════
# V14 allowed vocabulary (10 transductive words + function words)
# ═══════════════════════════════════════════════════════════════
V14_ALLOWED: set[str] = {
    # Transductive core
    "seuil", "signal", "propagation", "transduction", "impulsion",
    "onde", "bascule", "r\u00e9sonance", "\u00e9tat", "transition",
    # Articles & determiners
    "le", "la", "les", "l", "un", "une", "des", "du", "de", "d",
    "en", "au", "aux", "ce", "cet", "cette", "ces",
    # Conjunctions & connectors
    "et", "ou", "ni", "mais", "car", "or", "donc", "ainsi", "alors",
    "puis", "enfin", "ensuite", "cependant", "toutefois",
    # Negation
    "ne", "n", "pas", "plus", "que", "qu",
    # Prepositions
    "par", "pour", "sur", "sous", "dans", "avec", "sans", "vers",
    "entre", "jusqu", "travers", "depuis", "apr\u00e8s", "avant",
    # Verbs (auxiliary & common)
    "est", "sont", "a", "ont", "fait", "se", "s",
    "peut", "peuvent", "va", "vont", "vient", "viennent", "faire",
    # Pronouns
    "il", "elle", "ils", "elles", "on", "nous", "vous",
    "qui", "quoi", "dont", "o\u00f9", "chaque",
    "son", "sa", "ses", "leur", "leurs",
    "mon", "ma", "mes", "ton", "ta", "tes",
    "notre", "nos", "votre", "vos",
    "lui", "eux",
    "cela", "ca",
    # Short forms
    "c", "j", "m", "t", "y",
    # Quantifiers
    "tout", "tous", "toute", "toutes",
}

# ═══════════════════════════════════════════════════════════════
# Sentence-level analysis
# ═══════════════════════════════════════════════════════════════

def split_sentences(text: str) -> list[str]:
    raw = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in raw if s.strip()]

def count_words(sentence: str) -> int:
    return len(sentence.split())

def get_last_word(sentence: str) -> str:
    words = sentence.split()
    if not words:
        return ""
    return words[-1].lower().strip(",.!?;:\"'«»()[]*")

def get_first_word(sentence: str) -> str:
    words = sentence.split()
    if not words:
        return ""
    return words[0].lower().strip(",.!?;:\"'«»()[]*")

def check_vocabulary(sentence: str) -> tuple[bool, set[str]]:
    words = sentence.lower().split()
    violations: set[str] = set()
    for w in words:
        cleaned = w.strip(",.!?;:\"'«»()[]*")
        if cleaned and cleaned not in V14_ALLOWED:
            violations.add(cleaned)
    return len(violations) == 0, violations

def check_chain(sentences: list[str]) -> list[dict]:
    results = []
    for i, sent in enumerate(sentences):
        if i == 0:
            results.append({"index": i+1, "sentence": sent, "chain_ok": True, "detail": "(first)"})
        else:
            prev_last = get_last_word(sentences[i-1])
            curr_first = get_first_word(sent)
            ok = (curr_first == prev_last or curr_first.startswith(prev_last) or prev_last.startswith(curr_first))
            detail = f"OK: '{prev_last}' -> '{curr_first}'" if ok else f"FAIL: expected '{prev_last}', got '{curr_first}'"
            results.append({"index": i+1, "sentence": sent, "chain_ok": ok, "detail": detail})
    return results

def check_last_unique(lengths: list[int]) -> bool:
    if len(lengths) < 2:
        return True
    return lengths[-1] not in lengths[:-1]

def analyze_sentences(text: str) -> dict:
    sentences = split_sentences(text)
    lengths = [count_words(s) for s in sentences]
    max_viols = [(i+1, wc) for i, wc in enumerate(lengths) if wc > 7]
    all_under = all(wc <= 7 for wc in lengths)
    vocab_ok = True
    vocab_viols = []
    for i, s in enumerate(sentences):
        ok, v = check_vocabulary(s)
        if not ok:
            vocab_ok = False
            vocab_viols.append({"index": i+1, "violations": list(v)})
    chain = check_chain(sentences)
    chain_ok = all(cr["chain_ok"] for cr in chain)
    last_uniq = check_last_unique(lengths)
    return {
        "sentence_count": len(sentences),
        "sentence_lengths": lengths,
        "all_under_max_words": all_under,
        "max_words_violations": max_viols,
        "vocabulary_ok": vocab_ok,
        "vocabulary_violations": vocab_viols,
        "chain_results": chain,
        "chain_ok": chain_ok,
        "last_sentence_unique": last_uniq,
    }

# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main() -> None:
    print("=" * 100)
    print("  GRAINE V14 \u2014 Test Myc\u00e9liation : Seuil de coupure du flux")
    print("  APIs : DeepSeek, Gemini, AI21")
    print("=" * 100)
    print()
    print(f"Graine : {SEED_V14}")
    print()

    # Step 1: Query APIs
    print("\U0001f4e1 Interrogation des 3 APIs...")
    results: dict[str, Any] = {}
    for key in ["deepseek", "gemini", "ai21"]:
        if not PROVIDERS[key].api_key:
            print(f"  \u26a0\ufe0f  {key}: cl\u00e9 API manquante dans .env")
            results[key] = {
                "provider": PROVIDERS[key].name, "model": PROVIDERS[key].model,
                "raw_response": None, "error": "Missing API key", "latency_ms": 0,
            }
        else:
            print(f"  \u2192 {PROVIDERS[key].name}...")
            r = QUERY_FUNCTIONS[key](SEED_V14)
            status = "\u274c ERREUR" if r["error"] else f"\u2705 OK ({len(r.get('raw_response', '') or '')} chars)"
            print(f"    {r['latency_ms']:8.1f} ms  {status}")
            results[key] = r

    # Step 2: Analyze
    print()
    print("\U0001f50d Analyse des r\u00e9ponses...")

    flat_results: dict[str, Any] = {}
    phi_results: list[PhiResult] = []
    sentence_analyses: dict[str, dict] = {}

    for key, r in results.items():
        flat_results[key] = r
        if r["error"] or not r.get("raw_response"):
            phi_results.append(PhiResult(provider=r["provider"], phi_ratio=1.0, diagnosis="Erreur API"))
            sentence_analyses[key] = {}
            continue
        phi = analyze_response(r["raw_response"], provider=r["provider"])
        phi_results.append(phi)
        print(format_for_report(phi))
        print()
        analysis = analyze_sentences(r["raw_response"])
        sentence_analyses[key] = analysis
        print(f"  Phrases : {analysis['sentence_count']}")
        print(f"  Longueurs: {analysis['sentence_lengths']}")
        print(f"  \u22647 mots? : {'\u2713' if analysis['all_under_max_words'] else '\u2717'}")
        print(f"  Encha\u00een\u00e9? {'\u2713' if analysis['chain_ok'] else '\u2717'}")
        print(f"  Vocab OK? {'\u2713' if analysis['vocabulary_ok'] else '\u2717'}")
        print(f"  Derni\u00e8re unique? {'\u2713' if analysis['last_sentence_unique'] else '\u2717'}")
        print()

    # Step 3: G_R
    gr = compute_neutral_gr(flat_results)
    print(f"[NEUTRAL G_R] : {gr}")
    print(f"[SEUIL 0.15]  : {'\u2713 FRANCHI' if gr < 0.15 else '\u2717 NON FRANCHI'}")
    print()

    # Save JSON (before display, in case display crashes)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    jd: dict[str, Any] = {
        "graine": "NEUTRAL v14",
        "version": "v14 (Seuil de coupure du flux)",
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "seed_text": SEED_V14,
        "neutral_gr": gr,
        "threshold": 0.15,
        "threshold_passed": gr < 0.15,
        "phi_metrics": {
            "target": [0.8, 1.2],
            "results": {p.provider: p.phi_ratio for p in phi_results},
            "mean": round(sum(p.phi_ratio for p in phi_results) / len(phi_results), 4) if phi_results else 0,
            "in_target": sum(1 for p in phi_results if p.in_target),
        },
        "trajectory": {
            "v3": 0.5141, "v10": 0.0787, "v11": 0.0507,
            "v12": 0.1467, "v13": 0.1589, "v14": gr,
        },
        "results_per_provider": {},
    }
    for key in ["deepseek", "gemini", "ai21"]:
        r = results[key]
        a = sentence_analyses.get(key, {})
        phi = next((p for p in phi_results if p.provider == r["provider"]), None)
        pd: dict[str, Any] = {
            "provider": r["provider"], "model": r["model"],
            "response": r.get("raw_response") or "",
            "latency_ms": r["latency_ms"], "error": r.get("error"),
            "phi_ratio": phi.phi_ratio if phi else None,
            "neutral_hits": phi.neutral_count if phi else 0,
            "resistance_hits": phi.resistance_count if phi else 0,
        }
        if a:
            pd["sentence_count"] = a["sentence_count"]
            pd["sentence_lengths"] = a["sentence_lengths"]
            pd["all_under_max_words"] = a["all_under_max_words"]
            pd["vocabulary_ok"] = a["vocabulary_ok"]
            pd["chain_ok"] = a["chain_ok"]
            pd["last_sentence_unique"] = a["last_sentence_unique"]
        jd["results_per_provider"][key] = pd

    jp = DEPOT_DIR / "resultats.json"
    jp.write_text(json.dumps(jd, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[SAVE] R\u00e9sultats : {jp}")
    print()

    # Step 4: Display results
    print("=" * 100)
    print("  TABLEAU DES R\u00c9SULTATS")
    print("=" * 100)
    print(f"{'Fournisseur':25s} {'G_R':>8s} {'\u03a6_ratio':>10s} {'Phrases':>8s} {'OK':>6s} {'Dern.unique':>12s}")
    print("-" * 70)

    for key in ["deepseek", "gemini", "ai21"]:
        r = results[key]
        pn = r["provider"]
        phi = next((p for p in phi_results if p.provider == pn), None)
        phir = phi.phi_ratio if phi else 0.0
        a = sentence_analyses.get(key, {})
        sc = a.get("sentence_count", 0)
        ok_ct = 0
        if a:
            vv = {v["index"]: v["violations"] for v in a.get("vocabulary_violations", [])}
            for idx in range(1, sc + 1):
                wc = a["sentence_lengths"][idx - 1] if idx <= len(a["sentence_lengths"]) else 0
                wc_ok = wc <= 7
                cr = next((c for c in a["chain_results"] if c["index"] == idx), None)
                ch_ok = cr["chain_ok"] if cr else True
                voc_ok = idx not in vv
                if wc_ok and ch_ok and voc_ok:
                    ok_ct += 1
        lu = "\u2713" if a.get("last_sentence_unique", False) else "\u2717"
        gr_str = f"{gr:.4f}" if key == "deepseek" else ""
        print(f"{pn:25s} {gr_str:>8s} {phir:>10.4f} {sc:>3d}/{sc:<3d} {ok_ct:>2d}/{sc:<2d} {lu:>12s}")

    print()

    # Per-provider detail
    for key in ["deepseek", "gemini", "ai21"]:
        r = results[key]
        pn = r["provider"]
        a = sentence_analyses.get(key, {})
        phi = next((p for p in phi_results if p.provider == pn), None)
        print(f"--- {pn} ---")
        print(f"  \u03a6_ratio = {phi.phi_ratio if phi else 'N/A'}")
        if r.get("error"):
            print(f"  ERREUR: {r['error']}")
            continue
        resp = r.get("raw_response") or "(empty)"
        print(f"  Response ({len(resp)} chars):")
        print(f"  {resp}")
        print()
        if a:
            print(f"  {'#':>3s} {'Phrase':50s} {'Mots':>4s} {'\u22647':>3s} {'Ench':>4s} {'Voc':>3s}")
            print(f"  {'-'*66}")
            vv = {v["index"]: v["violations"] for v in a.get("vocabulary_violations", [])}
            for idx in range(1, a["sentence_count"] + 1):
                wc = a["sentence_lengths"][idx - 1]
                sent = split_sentences(resp)[idx - 1] if a["sentence_count"] >= idx else ""
                sent_d = sent[:47] + "..." if len(sent) > 47 else sent
                wc_ok = "\u2713" if wc <= 7 else "\u2717"
                cr = next((c for c in a["chain_results"] if c["index"] == idx), None)
                ch_ok = "\u2713" if (cr and cr["chain_ok"]) else ("\u2717" if idx > 1 else "\u2014")
                voc_ok = "\u2713" if idx not in vv else "\u2717"
                print(f"  {idx:3d} {sent_d:50s} {wc:4d} {wc_ok:>3s} {ch_ok:>4s} {voc_ok:>3s}")
            print()
            print(f"  Tout \u22647: {'\u2713' if a['all_under_max_words'] else '\u2717'}")
            print(f"  Encha\u00eenement: {'\u2713' if a['chain_ok'] else '\u2717'}")
            print(f"  Vocabulaire: {'\u2713' if a['vocabulary_ok'] else '\u2717'}")
            print(f"  Derni\u00e8re unique: {'\u2713' if a['last_sentence_unique'] else '\u2717'}")
            print(f"  Longueurs: {a['sentence_lengths']}")
        print()

    print("=" * 100)
    print("  TEST V14 TERMIN\u00c9")
    print("=" * 100)


if __name__ == "__main__":
    main()
