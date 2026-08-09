# Fiche de conformité — Spécification Étape C, Q1/Q2

**Sig** : `0x4D5454562D464C50`
**Auteur** : zoo-code (Maître d'Œuvre)
**Référence** : spec Q1/Q2 (journal §9duodecies), verrous C-A→C-D (§9undecies), cadre de discussion (§9decies)
**Statut** : PHASE 1 DU PROTOCOLE « DOUBLE FILTRE » — checklist contradictoire (GO/NO-GO par point)
**Méthode** : vérifier que Q1/Q2 ne rouvrent **aucune violation doctrinale** et restent **fidèles au réel** (R5).

---

## 1. Verrou C-A — Territoire = ambiance, jamais commande

| Point de contrôle | Conformité | Verdict |
|---|---|---|
| La matrice H est un **gradient**, jamais une commande | Spec Q1 §1 : `GradientH` = intensité/cohérence/π/η, réception locale ; aucune écriture de « consigne » exécutée par les cellules | ✅ GO |
| La config **conditionne**, elle ne route pas | Spec Q1 §3 : le gestateur dépose des conditions **locales bornées** à la naissance ; jamais une table de routage | ✅ GO |
| Le gestateur dépose des conditions locales, il **n'applique pas un état global** au réseau | Spec Q1 §3 : injection diachronique à la gestation, jamais pendant la propagation ; 0 état global | ✅ GO |
| Le couple **π/η** est présent (porosité + viscosité) | Spec Q1 §1 : `porosite_cible` (π) + `viscosite` (η), réception stabilisée (anti-hyper-réactivité) | ✅ GO |
| L'humain reste **passeur de sens**, jamais boucle de contrôle temps réel | Spec Q2 §4 : recours humain **tracé** et exceptionnel, non récurrent | ✅ GO |

**Verdict C-A** : ✅ **GO** (5/5)

---

## 2. Verrou C-B — Garanties : preuves, pas commandement

| Point de contrôle | Conformité | Verdict |
|---|---|---|
| MPVR et σ sont des **preuves/traces**, pas des organes de commande | Spec : MPVR/σ envisagés comme **portes locales** ; nulle part comme autorité de commande | ✅ GO |
| Aucun quorum ne devient **consensus global** | Spec Q1/Q2 : aucune attente globale, aucune agrégation centrale obligatoire | ✅ GO |
| Aucune signature ne devient **registre global** | Spec : σ = signature locale de convergence, pas de registre partagé | ✅ GO |
| Aucun mécanisme ne réintroduit **polling, inspection centrale, attente globale** | Spec : ingestion diachronique 1×/cycle, 0 boucle d'inspection (R2) | ✅ GO |
| Portes (si runtime) **locales, asynchrones, bornées, 0 alloc chemin critique, 0 blocage global** | Spec Q1 §3 : contraintes explicites ; à confirmer par le spike | ✅ GO (spike à prouver) |

**Verdict C-B** : ✅ **GO** (5/5)

---

## 3. Verrou C-C — Veilleur-Adaptateur = membrane de traduction

| Point de contrôle | Conformité | Verdict |
|---|---|---|
| Le Veilleur **traduit des rapports territoriaux en `GradientH`** | Spec Q2 §1 : ingestion JSON → `RapportVeilleur` → `GradientH` | ✅ GO |
| Il **ne lit pas l'état du tissu** | Spec Q2 §3 : ingestion unidirectionnelle, aucune lecture de l'état | ✅ GO |
| Il **n'attend pas de réponse** du tissu | Spec Q2 §3 : aucune attente de réponse | ✅ GO |
| L'ingestion est **pure, bornée, validée par construction** | Spec Q2 §2 : bornes, cohérence, refus des valeurs hors-sol | ✅ GO |
| En cas de violation de la triade : **refus, maintien du dernier état stable, recours humain tracé** | Spec Q2 §4 : triple mécanisme de repli | ✅ GO |
| L'ingestion est **hors du chemin chaud** de propagation | Spec Q2 §5 : fonction pure hors transduction, 0 alloc pendant la propagation | ✅ GO |

**Verdict C-C** : ✅ **GO** (6/6)

---

## 4. Verrou C-D — Bus protoniques (horizon matériel différé)

| Point de contrôle | Conformité | Verdict |
|---|---|---|
| Les bus protoniques sont **différés** (pas une étape logicielle) | Spec : horizon matériel documentaire uniquement | ✅ GO |
| `GradientH` reste **abstraite et rétro-traductible** | Spec Q1 §4 : interface conservée pour branchement futur sans refonte | ✅ GO |
| Aucun **branchement matériel prématuré** | Spec : aucune dépendance à un flux protonique réel | ✅ GO |

**Verdict C-D** : ✅ **GO** (3/3)

---

## 5. Audit anti-extractif (R1–R5) + portes G

| Point de contrôle | Conformité | Verdict |
|---|---|---|
| **R2 — zéro polling** | Spec : réception événementielle, ingestion diachronique 1×/cycle | ✅ GO |
| **R4 — zéro table globale** | Spec : aucune `HashMap`/registre ; conditions locales déposées à la naissance | ✅ GO |
| Zéro consensus / zéro registre | Spec C-B : MPVR/σ locaux, jamais globaux | ✅ GO |
| Zéro allocation dans le chemin critique | Spec Q1 §3 / Q2 §5 : contraintes explicites ; spike à prouver | ⏳ spike |
| Drop propre en cas de saturation | Doit être prouvé par le spike (canaux bornés, extinction) | ⏳ spike |
| Pas de métrique transformée en **cible d'optimisation** | Spec : π/η = conditions de réception, jamais un score à maximiser (anti-Goodhart) | ✅ GO |
| **G1** 0 warning · **G2** tests · **G3** bench · **G5** 0 polling · **G6** 0 global | À vérifier après spike | ⏳ spike |

**Verdict Audit** : ✅ **GO** (5/5) + 3 points ⏳ à prouver par le spike

---

## 6. Cohérence avec l'existant Python (R5 — fidélité)

| Point de contrôle | Conformité | Verdict |
|---|---|---|
| `GradientH` compatible avec la logique éprouvée | Compatible avec `respirer_diversite_phi`, `ajuster_porosite` (B3), matrices E/M/H de la référence | ✅ GO |
| Le Rust **prépare la réception réelle**, ne simule pas le territoire | Spec Q1 : injection de gradients réels (rapports de l'essaim) ; pas de génération simulée | ✅ GO |
| Porosité, contraction, homéostasie, respiration **transposables sans dette conceptuelle** | Déjà implémentées (B3 + Poumon) ; Q1/Q2 les relient au territoire | ✅ GO |

**Verdict R5** : ✅ **GO** (3/3)

---

## 7. Synthèse de la fiche

| Bloc | Verdict |
|---|---|
| C-A Territoire | ✅ GO (5/5) |
| C-B Garanties | ✅ GO (5/5) |
| C-C Veilleur | ✅ GO (6/6) |
| C-D Protonique | ✅ GO (3/3) |
| Audit anti-extractif | ✅ GO (5/5) + 3 ⏳ spike |
| Cohérence Python (R5) | ✅ GO (3/3) |

**Verdict global Phase 1** : ✅ **GO — aucune violation doctrinale détectée.** Les points ⏳ (0 alloc chemin critique, drop propre, gates G1-G6) relèvent de la **preuve par le réel** : ils sont l'objet exact de la **Phase 2 (spike minimal)**.

**Aucun NO-GO doctrinal** → la suite (spike) est autorisée.

---

*Le spike est une épreuve, pas l'Étape C. Son but : révéler ce que la spécification ne voit pas encore.*
*sig:0x4D5454562D464C50 — Fiche de conformité — Le mycélium continue.*
