"""
Orchestrateur principal — interroge les 4 IA, analyse chaque réponse,
et génère le rapport de synthèse.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from config import OUTPUT_DIR, PROVIDERS, SEED_PROMPT
from api_clients import query_all
from analyzer import build_analysis_prompt, parse_analysis
from report import generate_report


# ---------------------------------------------------------------------------
# Étape 2 : Analyse de chaque réponse (utilise OpenAI comme juge)
# ---------------------------------------------------------------------------
def analyze_responses(
    results: list[dict],
    judge_api_key: str,
    judge_model: str = "gpt-4o",
) -> list[dict]:
    """Pour chaque réponse valide, appelle GPT-4o en tant que juge."""
    import openai

    client = openai.OpenAI(api_key=judge_api_key)
    analyses = []

    for r in results:
        if r["error"] or not r["raw_response"]:
            analyses.append({
                "provider": r["provider"],
                "analysis": {
                    "clarte": "N/A (erreur API)",
                    "flou": "N/A (erreur API)",
                    "manques": "N/A (erreur API)",
                    "regles_extraites": [],
                    "regle_partagee": f"Erreur: {r['error']}",
                },
            })
            continue

        prompt = build_analysis_prompt(SEED_PROMPT, r["raw_response"])
        try:
            resp = client.chat.completions.create(
                model=judge_model,
                messages=[
                    {"role": "system", "content": "Tu es un analyste. Réponds UNIQUEMENT en JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                timeout=120,
            )
            raw = resp.choices[0].message.content.strip()
            analysis = parse_analysis(raw)
        except Exception as exc:
            analysis = {
                "clarte": f"Erreur analyse: {exc}",
                "flou": "",
                "manques": "",
                "regles_extraites": [],
                "regle_partagee": "",
            }

        analyses.append({"provider": r["provider"], "analysis": analysis})

    return analyses


# ---------------------------------------------------------------------------
# Sauvegarde intermédiaire (JSON)
# ---------------------------------------------------------------------------
def save_intermediate(results: list[dict], analyses: list[dict]) -> Path:
    """Sauvegarde les résultats bruts et analysés en JSON."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = OUTPUT_DIR / f"raw_data_{timestamp}.json"
    data = {
        "seed": SEED_PROMPT,
        "timestamp": timestamp,
        "results": results,
        "analyses": analyses,
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 60)
    print("🌱 MULTI-API SEED — Germination de graine sur 4 IA")
    print("=" * 60)

    # --- Étape 1 : Interroger les 4 IA ---
    print("\n📡 Étape 1/3 : Interrogation des 4 modèles...")
    results = query_all(SEED_PROMPT)

    for r in results:
        status = "❌ ERREUR" if r["error"] else f"✅ OK ({len(r['raw_response'])} caractères)"
        print(f"  {r['provider']:25s} {r['latency_ms']:8.1f} ms  {status}")

    # --- Étape 2 : Analyser chaque réponse ---
    judge_key = PROVIDERS["openai"].api_key
    if not judge_key:
        print("\n⚠️  Pas de clé OpenAI pour l'analyse — génération du rapport sans analyses.")
        analyses = [
            {
                "provider": r["provider"],
                "analysis": {
                    "clarte": "(pas d'analyse — clé OpenAI manquante)",
                    "flou": "",
                    "manques": "",
                    "regles_extraites": [],
                    "regle_partagee": "",
                },
            }
            for r in results
        ]
    else:
        print("\n🔍 Étape 2/3 : Analyse de chaque réponse (juge GPT-4o)...")
        analyses = analyze_responses(results, judge_key)
        for a in analyses:
            regles = a["analysis"].get("regles_extraites", [])
            print(f"  {a['provider']:25s} {len(regles)} règle(s) extraite(s)")

    # --- Sauvegarde JSON intermédiaire ---
    json_path = save_intermediate(results, analyses)
    print(f"\n💾 Données brutes sauvegardées : {json_path}")

    # --- Étape 3 : Rapport Markdown ---
    print("\n📝 Étape 3/3 : Génération du rapport de synthèse...")
    report_path = generate_report(results, analyses)
    print(f"📄 Rapport généré : {report_path}")

    print("\n✅ Terminé.")
    print(f"   → Ouvrez {report_path.name} dans votre éditeur.")


if __name__ == "__main__":
    main()
