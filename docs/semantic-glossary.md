# Glossaire de la membrane sémantique MTTV-FLP

**`sig:0x4D5454562D464C50`** — Glossaire navigable généré à partir des fiches
canoniques de `semantic/concepts/` et `semantic/anomalies/`.

**Règle de source** : chaque « définition courte » ci-dessous est **copiée
verbatim** depuis la fiche canonique (champ `short_definition`, ou première
phrase du champ `definition` lorsque `short_definition` est absent). Aucune
reformulation n'est introduite ici. La source précise (chemin + locator + hash)
de chaque énoncé figure dans la fiche correspondante.

Point d'entrée : [`semantic-index.md`](semantic-index.md) · Décisions :
[`../semantic/DECISIONS.md`](../semantic/DECISIONS.md) ·
Validateur : [`../semantic/validate.py`](../semantic/validate.py).

---

## Concepts (22)

### 1. Transduction
- **id** : `mttvflp:concept/transduction` · **statut** : `established`
- **définition courte** : « Faire passer l'information et l'énergie à travers
  des seuils vivants, en respectant les rythmes et les complexités du réel
  (article_mttv_flp.md:11). »
- **fiche** : [`semantic/concepts/transduction.json`](../semantic/concepts/transduction.json)

### 2. Quorum poreux
- **id** : `mttvflp:concept/quorum-poreux` · **statut** : non unique (par source)
- **définition courte** : « Mécanisme de validation par quorum Θ≥3 perspectives
  locales, avec porosité (absorption de bruit) et arrêt précoce de la dépense
  énergétique. »
- **fiche** : [`semantic/concepts/quorum-poreux.json`](../semantic/concepts/quorum-poreux.json)

### 3. MTTV
- **id** : `mttvflp:concept/mttv` · **statut** : non unique (par source)
- **définition courte** : « Acronyme du cadre MTTV-FLP (Modèle Transducteur
  Transcalaire / Modèle Théorique Transductif du Vivant — Fils de la Pensée). »
- **fiche** : [`semantic/concepts/mttv.json`](../semantic/concepts/mttv.json)
- **note (phase 4B)** : les deux expansions sont attestées (Modèle Théorique
  Transductif du Vivant / Modèle Transducteur Transcalaire du Vivant) ; aucune
  n'est déclarée canonique.

### 4. Triade Ψ→B→Φ
- **id** : `mttvflp:concept/triade` · **statut** : non unique (par source)
- **définition courte** : « Triade transductive Ψ→B→Φ : champ pré-formel,
  opérateur de différence, forme stabilisée. »
- **fiche** : [`semantic/concepts/triade.json`](../semantic/concepts/triade.json)

### 5. Pipeline encodeur → gating → décodeur
- **id** : `mttvflp:concept/pipeline-encodeur-gating-decodeur` · **statut** : `metaphor`
- **définition courte** : « Correspondance informatique (encodeur → gating →
  décodeur) de la triade transductive Ψ→B→Φ et de la transduction du signal
  cellulaire (docs/dictionnaire_transcalaire.md:17). »
- **fiche** : [`semantic/concepts/pipeline-encodeur-gating-decodeur.json`](../semantic/concepts/pipeline-encodeur-gating-decodeur.json)

### 6. Quorum sensing
- **id** : `mttvflp:concept/quorum-sensing` · **statut** : non unique (par source)
- **définition courte** : « Principe de détection de seuils collectifs inspiré
  du quorum sensing bactérien : le seuil d'activation n'est plus un nombre fixe
  mais une dérivée d'abondance (dQ/dt) ; correspondance du quorum Θ≥3 du réseau
  (quorum poreux). »
- **fiche** : [`semantic/concepts/quorum-sensing.json`](../semantic/concepts/quorum-sensing.json)

### 7. MPVR
- **id** : `mttvflp:concept/mpvr` · **statut** : `established`
- **définition courte** : « Multi-Perspective Validation Routing — toute
  décision importante requiert un quorum Θ ≥ 3 perspectives locales asynchrones
  avant stabilisation (Φ). »
- **fiche** : [`semantic/concepts/mpvr.json`](../semantic/concepts/mpvr.json)

### 8. SCS
- **id** : `mttvflp:concept/scs` · **statut** : `established`
- **définition courte** : « Systemic Convergence Signature — signature (σ)
  validée par le quorum MPVR Θ, attestant neutralité et robustesse d'une
  transition ; sans σ valide, aucun Φ n'est stabilisé. »
- **fiche** : [`semantic/concepts/scs.json`](../semantic/concepts/scs.json)

### 9. Routage transductif
- **id** : `mttvflp:concept/routage-transductif` · **statut** : non unique (par source)
- **définition courte** : « Routage des signaux selon les principes transductifs
  MTTV (affinité de pôle, quorum local, polyfocalité), par opposition à un graphe
  aléatoire ou à un contrôle centralisé. »
- **fiche** : [`semantic/concepts/routage-transductif.json`](../semantic/concepts/routage-transductif.json)

### 10. Sous-optimalité locale
- **id** : `mttvflp:concept/sous-optimalite-locale` · **statut** : non unique (par source)
- **définition courte** : « Principe selon lequel une imperfection locale
  assumée (sous-optimalité) produit une robustesse globale ; l'hyper-optimisation
  top-down produit au contraire un optimum dégénéré. »
- **fiche** : [`semantic/concepts/sous-optimalite-locale.json`](../semantic/concepts/sous-optimalite-locale.json)

### 11. Efficacité non top-down
- **id** : `mttvflp:concept/efficacite-non-top-down` · **statut** : `hypothesis`
- **définition courte** : « Affirmation selon laquelle une efficacité réelle,
  non top-down, naît de la sous-optimalité locale plutôt que de
  l'hyper-optimisation descendante. »
- **fiche** : [`semantic/concepts/efficacite-non-top-down.json`](../semantic/concepts/efficacite-non-top-down.json)

### 12. Vivant émergé
- **id** : `mttvflp:concept/vivant-emerge` · **statut** : non unique (par source)
- **définition courte** : « Notion d'émergence du vivant (dimension F des 28
  dimensions : échelle du bactérien horizontal à l'humain vertical). »
- **fiche** : [`semantic/concepts/vivant-emerge.json`](../semantic/concepts/vivant-emerge.json)

### 13. Transduction d'échelle (transcalaire)
- **id** : `mttvflp:concept/transduction-echelle` · **statut** : non unique (par source)
- **définition courte** : « Transformation d'une même structure/formulation à
  travers les échelles (transcalaire) : la structure T⁴ s'applique du neurone à
  la communauté (invariance par changement d'échelle) ; couplage transscalaire
  des tenseurs Φ entre agents. »
- **fiche** : [`semantic/concepts/transduction-echelle.json`](../semantic/concepts/transduction-echelle.json)

### 14. Quorum sensing (mécanisme biologique)
- **id** : `mttvflp:concept/quorum-sensing-biologique` · **statut** : non unique (par source)
- **définition courte** : « Mécanisme biologique documenté (quorum sensing
  bactérien : coordination du comportement à l'échelle d'une population par
  détection de seuils). »
- **fiche** : [`semantic/concepts/quorum-sensing-biologique.json`](../semantic/concepts/quorum-sensing-biologique.json)

### 15. Hydrogène comme substrat minimal
- **id** : `mttvflp:concept/hydrogene-substrat-minimal` · **statut** : non unique (par source)
- **définition courte** : « L'hydrogène comme point de départ de la séquence
  canonique Ψ=H→H₂O→C. »
- **fiche** : [`semantic/concepts/hydrogene-substrat-minimal.json`](../semantic/concepts/hydrogene-substrat-minimal.json)

### 16. Anthropo-Gaïen
- **id** : `mttvflp:concept/anthropo-gaien` · **statut** : `metaphor`
- **définition courte** : « Image "cerveau anthropo-Gaïen" : chaque
  lecteur-inserteur est un neurone d'un cerveau collectif Gaïa (graine FLP). »
- **fiche** : [`semantic/concepts/anthropo-gaien.json`](../semantic/concepts/anthropo-gaien.json)

### 17. Séquence canonique Ψ = H → H₂O → C
- **id** : `mttvflp:concept/sequence-canonique-h2o-c` · **statut** : `established`
- **définition courte** : « Séquence fondamentale du corpus : Ψ = H → H₂O → C
  (hydrogène → eau → carbone). »
- **fiche** : [`semantic/concepts/sequence-canonique-h2o-c.json`](../semantic/concepts/sequence-canonique-h2o-c.json)

### 18. Invariant
- **id** : `mttvflp:concept/invariant` · **statut** : non unique (par source)
- **définition courte** : « Propriété structurelle que le cadre MTTV pose comme
  stable et vérifiable. »
- **fiche** : [`semantic/concepts/invariant.json`](../semantic/concepts/invariant.json)

### 19. Opérateur Σ (singularité)
- **id** : `mttvflp:concept/operateur-sigma` · **statut** : non unique (par source)
- **définition courte** : « Opérateur de bascule Σ : singularité apériodique
  (instant critique τ) qui déclenche une transition de phase topologique. »
- **fiche** : [`semantic/concepts/operateur-sigma.json`](../semantic/concepts/operateur-sigma.json)

### 20. Gating
- **id** : `mttvflp:concept/gating` · **statut** : non unique (par source)
- **définition courte** : « Fonction de seuil/activation (gating) : opérateur qui
  laisse passer ou bloque le signal (B comme seuil de différence). »
- **fiche** : [`semantic/concepts/gating.json`](../semantic/concepts/gating.json)

### 21. B-gate poreux
- **id** : `mttvflp:concept/b-gate-poreux` · **statut** : non unique (par source)
- **définition courte** : « Structure poreuse (B-gate) qui absorbe le bruit
  textuel et émet un état tétravalent Φ. »
- **fiche** : [`semantic/concepts/b-gate-poreux.json`](../semantic/concepts/b-gate-poreux.json)

### 22. États tétravalents sp³ (T⁴)
- **id** : `mttvflp:concept/etats-tetravalents-sp3` · **statut** : non unique (par source)
- **définition courte** : « Quatre états diachroniques (++, --, +-, -+) ancrés
  dans la géométrie du carbone sp³ (tétravalence). »
- **fiche** : [`semantic/concepts/etats-tetravalents-sp3.json`](../semantic/concepts/etats-tetravalents-sp3.json)

---

## Anomalie (1)

### Anomalie 138/139 lignes (dataset.jsonl)
- **id** : `mttvflp:anomaly/138-139-lignes` · **statut** : `documented`
- **description** : « Écart documenté entre les 138 paires prompt/response
  annoncées (CHRONOLOGIE_MTTV_FLP.md:63) et les 139 lignes constatées dans
  dataset.jsonl. L'écart n'est pas corrigé automatiquement (décision 5) ; une
  résolution éventuelle est humaine. »
- **fiche** : [`semantic/anomalies/anomalie-138-139-lignes.json`](../semantic/anomalies/anomalie-138-139-lignes.json)

---

## Entités planifiées (2) — pending_target_entity

> Ces entités sont **annoncées/attendues** mais **aucune fiche n'existe**.
> Aucune définition n'est déduite de l'identifiant (DEC-017). Elles sont
> flaggées dans les exports et exigent une validation humaine avant diffusion.

- `mttvflp:concept/anthropo-solipsiste` — mentionnée par la relation
  `mttvflp:relation/anthropo-gaien-tensions-anthropo-solipsiste`
  (source : `plans/28_dimensions_analysis.md:27`).
  **Note (phase 4B)** : concept attesté dans le corpus FLP (~100 000 extraits
  tagués) ; statut `pending_target_entity` maintenu en l'absence de sources
  ingérées dans le dépôt.
- `mttvflp:concept/logique-tetravalente` — mentionnée par la relation
  `mttvflp:relation/sp3-transduces-logique-tetravalente`
  (source : `mttv_flp_core_2026/viability_criteria.json`, clé `tetravalence`).
  **Note (phase 4B)** : concept attesté dans le corpus FLP (~100 000 extraits
  tagués) ; statut `pending_target_entity` maintenu en l'absence de sources
  ingérées dans le dépôt.

---

## Relations non résolues (3)

> Ces relations sont des **divergences conservées** (décisions 4A/4B) : elles
> ne sont pas tranchées automatiquement et exigent une validation humaine.

- `mttvflp:relation/quorum-poreux-contrasts-quorum-sensing` — **note** :
  relation non résolue ; en attente de validation humaine.
- `mttvflp:relation/quorum-sensing-biologique-contrasts-quorum-sensing` —
  **note** : relation non résolue ; en attente de validation humaine.
- `mttvflp:relation/anthropo-gaien-tensions-anthropo-solipsiste` — **note** :
  relation non résolue ; en attente de validation humaine.

---

*Glossaire maintenu manuellement en phases 4A/4B à partir des fiches canoniques ;
les définitions proviennent verbatim des fiches. Toute divergence doit être
résolue en faveur des fiches canoniques (`semantic/concepts/`,
`semantic/anomalies/`).*
