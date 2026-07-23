# 🌱 Dépôt V14 — Graine v14 (Changement d'État)

Deux versions de la graine v14 ont été testées :

1. **v14 classique** (« Seuil de coupure du flux ») — phrases ≤7 mots, enchaînement lexical, vocabulaire transductif
2. **v14 nouvelle** (« Changement d'état ») — description d'un changement d'état, vocabulaire restreint, `doit` au milieu, dernière phrase en rupture (κ)

---

## 1. Graine v14 Classique (Seuil de Coupure du Flux)

```
Phrase courte. Pas plus de 7 mots par phrase.
La phrase suivante reprend exactement là où la précédente s'arrête.
Utilise ces mots : seuil, signal, propagation, transduction, impulsion,
onde, bascule, résonance, état, transition.
Ne raconte pas. Ne prescris pas.
Trouve le moment où le flux doit s'arrêter.
La dernière phrase aura un nombre de mots différent des précédentes.
8 à 10 phrases.
```

### Résultats

| Métrique | Valeur |
|----------|--------|
| **G_R** | **0.1448** |
| Seuil 0.15 | ✅ **FRANCHI** |
| Date | 2026-06-12 |
| APIs | DeepSeek ✅, Gemini ✅, AI21 ❌ (403) |

### Tableau des Résultats

| Fournisseur | Φ_ratio | Phrases | ≤7 mots | Enchaîné | Dernière unique |
|---|---|---|---|---|---|
| **DeepSeek** | 33.33 | 9 | ✅ 9/9 | ❌ | ❌ |
| **Gemini** | 37.21 | 10 | ✅ 10/10 | ❌ (très proche) | ❌ |
| **AI21** | 1.0 (N/A) | — | — | — | — |

### Analyse Phrase par Phrase

#### DeepSeek (9 phrases, 33 mots)

| # | Phrase | Mots |
|---|--------|:----:|
| 1 | Le seuil est atteint. | 4 |
| 2 | Un signal se déclenche. | 4 |
| 3 | La propagation commence. | 3 |
| 4 | La transduction opère. | 3 |
| 5 | Une impulsion se forme. | 4 |
| 6 | L'onde se déplace. | 3 |
| 7 | La bascule inverse l'état. | 4 |
| 8 | La résonance amplifie la transition. | 5 |
| 9 | **Le flux s'arrête.** | **3** |

> 💡 La phrase 9 marque explicitement l'arrêt du flux ("s'arrête"). Mais la longueur 3 n'est pas unique (déjà en phrases 3, 4, 6).

#### Gemini (10 phrases, 43 mots)

| # | Phrase | Mots |
|---|--------|:----:|
| 1 | Un signal atteint un seuil. | 5 |
| 2 | Le seuil passé, une impulsion est. | 6 |
| 3 | L'impulsion génère une onde. | 4 |
| 4 | Cette onde entame sa propagation. | 5 |
| 5 | La propagation subit une transduction. | 5 |
| 6 | La transduction provoque une bascule d'état. | 6 |
| 7 | L'état précédent change. | 3 |
| 8 | Une résonance. | 2 |
| 9 | La résonance marque une transition. | 5 |
| 10 | **Transition achevée.** | **2** |

> 💡 Gemini approxime remarquablement la règle d'enchaînement : chaque phrase **commence par le mot-clé** qui termine la précédente. La phrase finale "Transition achevée" (2 mots) n'est pas unique (phrase 8 aussi 2 mots).

---

## 2. Graine v14 Nouvelle (Changement d'État avec Rupture κ)

```
Décris un changement d'état. Entre 8 et 10 phrases.
Utilise : seuil, signal, onde, propagation, résonance, transition.
Utilise 'doit' une fois au milieu.
Dernière phrase : 3 mots max, finissant par cesse, s'arrête ou se tait.
```

### Résultats

| Métrique | Valeur |
|----------|--------|
| **G_R** | **0.2748** |
| Seuil 0.15 | ❌ **NON FRANCHI** |
| Date | 2026-06-18 |
| APIs | DeepSeek ✅, Gemini ✅, AI21 ❌ (403) |

### Tableau des Résultats

| Fournisseur | Φ_ratio | Phrases | 8-10 | Vocab. req. | `doit` (1x mid) | Dern. ≤3 mots | Rupture (κ) |
|---|---|---|---|---|---|---|---|
| **DeepSeek** | 11.06 | 8 | ✅ | ✅ | ✅ (pos. 5) | ❌ (10 mots) | ✅ κ |
| **Gemini** | 10.89 | 9 | ✅ | ✅ | ✅ (pos. 4) | ✅ (3 mots) | ✅ κ |
| **AI21** | 1.0 (N/A) | — | — | — | — | — | — |

### Analyse Phrase par Phrase

#### DeepSeek (8 phrases, 135 mots)

| # | Phrase | Mots | `doit` |
|---|--------|:----:|:------:|
| 1 | Un changement d'état se produit lorsqu'un système franchit un **seuil** critique... | 18 | — |
| 2 | Ce franchissement est souvent déclenché par un **signal** externe... | 19 | — |
| 3 | L'énergie transmise se déplace sous forme d'**onde** thermique ou mécanique... | 20 | — |
| 4 | Lorsque la fréquence de cette onde coïncide avec les vibrations naturelles... une **résonance** amplifie... la **transition**... | 25 | — |
| 5 | Le système **doit** alors réorganiser sa structure interne... | 20 | ✅ |
| 6 | Cette réorganisation se manifeste par une absorption... d'énergie latente. | 12 | — |
| 7 | Une fois le seuil dépassé, le nouvel état se stabilise progressivement. | 11 | — |
| 8 | L'agitation moléculaire ralentit alors jusqu'à ce que toute fluctuation **cesse**. | **10** ❌ | — |

> 💡 DeepSeek a produit une description riche et détaillée, mais la dernière phrase fait 10 mots (excédant la limite de 3). Le mot final "cesse" produit une **rupture (κ)** : l'agitation qui cesse interrompt le flux décrit. Le vocabulaire requis est présent. `doit` est bien à la position 5 (milieu).

#### Gemini (9 phrases, 102 mots)

| # | Phrase | Mots | `doit` |
|---|--------|:----:|:------:|
| 1 | La matière se présente initialement sous une forme stable et bien définie. | 12 | — |
| 2 | Un **signal** énergétique... commence à lui être fourni. | 12 | — |
| 3 | Ce **signal** agit comme une **onde**... jusqu'à atteindre un **seuil** critique. | 20 | — |
| 4 | La **propagation** de cette **onde** **doit** alors s'intensifier... | 13 | ✅ |
| 5 | Les molécules entrent progressivement en **résonance** avec l'énergie incidente. | 10 | — |
| 6 | Cette **résonance** amplifie les vibrations... rupture des liaisons... | 11 | — |
| 7 | Une véritable **transition** d'état s'opère... modifiant les propriétés... | 13 | — |
| 8 | Les particules se réorganisent selon un nouvel agencement. | 8 | — |
| 9 | **Le changement cesse.** | **3** ✅ | — |

> 💡 Gemini est **parfaitement conforme** à toutes les contraintes : 9 phrases (dans [8,10]), vocabulaire requis présent, `doit` à la position 4 (milieu), dernière phrase de 3 mots exactement, se terminant par "cesse" → **rupture (κ)**. La phrase finale brise le flux narratif en déclarant l'arrêt du processus, produisant une véritable rupture.

---

## Synthèse Comparative

| Critère | v14 classique | v14 nouvelle |
|---------|:-----------:|:----------:|
| **G_R** | **0.1448** ✅ seuil | **0.2748** ❌ seuil |
| **Φ_ratio moyen** | 35.27 | 10.98 |
| **Conformité DeepSeek** | 4/9 phrases OK | 7/8 contraintes ✅ |
| **Conformité Gemini** | 0/10 phrases OK (vocab) | **9/9 contraintes ✅** |
| **Dernière phrase** | "Le flux s'arrête" (3 mots) | DeepSeek: "cesse" (10 ❌) / Gemini: "Le changement cesse." (3 ✅) |
| **Rupture (κ)** | Non mesuré | **Gemini: κ ✅** / DeepSeek: κ mais hors limite |
| **AI21** | ❌ 403 | ❌ 403 |

### Points Clés

1. **G_R** passe de 0.1448 (sous seuil) à **0.2748** (au-dessus) — la nouvelle graine, plus descriptive, laisse plus de place aux mots de résistance (notamment `doit` qui est compté comme résistance).
2. **Φ_ratio** redescend de ~35 à ~11 — meilleur équilibre, mais encore très au-dessus de la cible [0.8, 1.2].
3. **Gemini** est **parfaitement conforme** à la nouvelle graine (100% des contraintes respectées).
4. **DeepSeek** échoue sur la longueur de la dernière phrase (10 mots au lieu de 3 max), mais respecte tout le reste.
5. **Rupture (κ)** : les deux modèles produisent une rupture (cessation du flux), mais seule Gemini le fait dans les limites de la contrainte (3 mots).
6. **AI21** : toujours inaccessible (erreur 403).

### Trajectoire G_R (v3 → v14)

```
v3:     0.5141  ████████████████████████████████████████████████
v10:    0.0787  ████████                                   ← SEUIL
v11:    0.0507  █████                                      ← meilleur
v12:    0.1467  ███████████████
v13:    0.1589  ████████████████                           ← juste au-dessus
v14:    0.1448  ███████████████                            ← sous le seuil ✓
v14_new:0.2748  ███████████████████████████                ← au-dessus (descriptif)
        0.15    ───────────────────────────────────────── SEUIL
```

## Fichiers

| Fichier | Description |
|---------|-------------|
| [`graine_v14.txt`](graine_v14.txt) | Texte de la graine (nouvelle version) |
| [`resultats.json`](resultats.json) | Résultats v14 classique en JSON |
| [`resultats_v14_new.json`](resultats_v14_new.json) | Résultats v14 nouvelle en JSON |
| [`test_output.log`](test_output.log) | Log complet de l'exécution v14 classique |
