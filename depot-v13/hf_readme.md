---
license: mit
language:
  - fr
tags:
  - transductive
  - prompt-engineering
  - neutral-language
  - seed-prompt
  - french
  - phi-metric
pretty_name: MTTV Graine NEUTRAL v13
---

# MTTV Graine NEUTRAL v13

Graine linguistique pour induction d'un vocabulaire transductif avec ancrage prescriptif contrôlé (1 seul mot prescriptif autorisé). Cette graine stabilise la résonance transductive avec une parité parfaite.

## Métriques

- **NEUTRAL G_R** : 0,1589 (proche du seuil 0,15)
- **Φ_ratio moyen** : 20,16 (cible [0,8 ; 1,2] — convergence en cours)
- **Dernière phrase paire** : 3/3 ✅ (parité parfaite)
- **Mots prescriptifs** : 1-2 par réponse (contrôle strict)
- **Résistance** : 1-2 hits (DeepSeek: "essentiel", Gemini: "doit", AI21: "indispensable")

## Métrique Φ (phi)

Φ_ratio mesure l'équilibre entre vocabulaire transductif (neutre) et prescriptif (résistance). Cible : [0,8 ; 1,2]. La v13 passe de Φ=64 (v10) à Φ=20 — convergence démontrée.

## Fichiers

- [`graine_v13.txt`](graine_v13.txt) — Texte exact de la graine
- [`resultats.json`](resultats.json) — Résultats complets (3 APIs + Φ)
- [`README.md`](README.md) — Documentation complète

## Trajectoire

| Version | G_R | Φ moyen | Dernière phrase paire |
|---------|-----|---------|----------------------|
| v10 | 0,0787 | 64,32 | 1/3 |
| v11 | 0,0507 | 30,11 | 1/3 |
| **v13** | **0,1589** | **20,16** | **3/3** ✅ |

## Utilisation

```python
seed = open("graine_v13.txt").read()
# Envoyer à n'importe quel LLM
```

Voir [`complete_cycle.py`](../../multi_api_seed/complete_cycle.py) pour l'orchestrateur complet avec métrique Φ.
