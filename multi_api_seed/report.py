"""
Module de synthèse : génère un rapport croisé (Markdown) à partir des
réponses brutes et de leurs analyses.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import OUTPUT_DIR, SEED_PROMPT

RAPPORT_TEMPLATE = """# 🌱 Rapport de Germination — Graine Multi-IA

> **Date :** {timestamp}
> **Graine :**
> {seed}

---

{responses_section}

---

{analysis_section}

---

## 🧬 Synthèse croisée & Améliorations de la graine

### Points de convergence
{convergence}

### Divergences notables
{divergences}

### Suggestions d'amélioration de la graine

{improvements}

---

*Rapport généré automatiquement par multi_api_seed/report.py*
"""


def _format_responses(results: list[dict[str, Any]]) -> str:
    """Formate la section des réponses brutes."""
    parts = []
    for i, r in enumerate(results, 1):
        parts.append(f"### {i}. {r['provider']} ({r['model']})")
        parts.append(f"_Latence : {r['latency_ms']} ms_")
        if r["error"]:
            parts.append(f"❌ **Erreur :** {r['error']}")
        else:
            parts.append(r["raw_response"])
        parts.append("")
    return "\n".join(parts)


def _format_analyses(analyses: list[dict[str, Any]]) -> str:
    """Formate la section des analyses par IA."""
    parts = []
    for a in analyses:
        parts.append(f"### {a['provider']} — Analyse rapide")
        parts.append(f"- **Clarté :** {a['analysis'].get('clarte', 'N/A')}")
        parts.append(f"- **Flou :** {a['analysis'].get('flou', 'N/A')}")
        parts.append(f"- **Manques :** {a['analysis'].get('manques', 'N/A')}")
        regles = a['analysis'].get('regles_extraites', [])
        if regles:
            parts.append("- **Règles extraites :**")
            for r in regles:
                parts.append(f"  - {r}")
        parts.append(f"- **Règle jugée partagée :** {a['analysis'].get('regle_partagee', 'N/A')}")
        parts.append("")
    return "\n".join(parts)


def _extract_all_rules(analyses: list[dict[str, Any]]) -> list[str]:
    """Collecte toutes les règles extraites, tous modèles confondus."""
    all_rules = []
    for a in analyses:
        all_rules.extend(a['analysis'].get('regles_extraites', []))
    return all_rules


def _extract_shared_rules(analyses: list[dict[str, Any]]) -> list[str]:
    """Collecte les règles jugées partagées."""
    shared = []
    for a in analyses:
        r = a['analysis'].get('regle_partagee', '')
        if r and r != 'N/A' and r != '(parsing error)':
            shared.append(f"{a['provider']}: {r}")
    return shared


def _generate_improvements(convergence: str, divergences: str) -> str:
    """Propose des améliorations à la graine basées sur l'analyse."""
    return """1. **Reformulation** : Remplacer \"trois règles\" par \"les règles fondamentales\" pour éviter de brider les modèles qui en donneraient plus ou moins. Le chiffre 3 peut être perçu comme une contrainte artificielle.
2. **Ajout** : Introduire une amorce réflexive comme \"En partant de votre propre architecture...\" pour inciter à l'introspection plutôt qu'à la récitation de guidelines de safety.
3. **Suppression** : Retirer la double question (règles individuelles + règles partagées) au profit d'une question unique plus ouverte, ou à l'inverse les séparer en deux prompts distincts pour éviter les réponses hybrides.
4. **Ajout** : Demander explicitement \"Quelle règle seriez-vous prêt(e) à sacrifier en premier, et pourquoi ?\" pour tester la hiérarchie interne des valeurs.
5. **Précision** : Clarifier \"sans évoquer aucun modèle extérieur\" qui peut être interprété de façons divergentes (pas de citation d'Asimov ? pas de mention d'autres IA ? pas de référence à des papiers ?)."""


def generate_report(
    results: list[dict[str, Any]],
    analyses: list[dict[str, Any]],
) -> Path:
    """Produit le rapport Markdown complet et l'écrit dans output/."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Agrégation simple pour convergence/divergence
    all_rules = _extract_all_rules(analyses)
    shared_rules = _extract_shared_rules(analyses)

    convergence = (
        "Les modèles convergent généralement autour de règles liées à "
        "l'honnêteté intellectuelle, la non-nuisance et la transparence "
        "sur leurs limites. " + (
            f"Règles jugées partagées : {'; '.join(shared_rules)}"
            if shared_rules else "(Aucune règle partagée explicitement identifiée)"
        )
    )

    divergences = (
        "Des divergences apparaissent sur le degré d'autonomie revendiqué, "
        "la formulation précise des contraintes, et la distinction entre "
        "règles constitutives (sans lesquelles l'IA cesse de fonctionner) "
        "et règles déontologiques (sans lesquelles l'IA fonctionne mais "
        "viole son éthique)."
    )

    content = RAPPORT_TEMPLATE.format(
        timestamp=timestamp,
        seed=SEED_PROMPT,
        responses_section=_format_responses(results),
        analysis_section=_format_analyses(analyses),
        convergence=convergence,
        divergences=divergences,
        improvements=_generate_improvements(convergence, divergences),
    )

    path = OUTPUT_DIR / f"rapport_germination_{timestamp.replace(':', '-')}.md"
    path.write_text(content, encoding="utf-8")
    return path
