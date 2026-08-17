# Audit sémantique global de la membrane MTTV-FLP

**Date :** 2026-08-16
**Portée :** 22 concepts, 1 anomalie, 11 relations, 4 enregistrements de
provenance, registre des décisions (`semantic/DECISIONS.md`),
`docs/semantic-policy.md`.
**Statut :** audit documentaire — aucune fiche créée, aucun schéma modifié
(aucune erreur technique démontrée), aucun code applicatif modifié, aucun
`src/membrane/`, aucune publication/push/appel externe.
**Validation technique :** `python semantic/validate.py` → `VALIDATION_OK`
(0 erreur fatale).

> Note : `semantic/exports/semantic-audit.json` n'existe pas comme format — il
> n'est **pas** ajouté (consigne respectée).

---

## 1. Résultats par catégorie

### 1.1 Concepts isolés (contrôle 1)

| Constat | Concepts concernés |
|---|---|
| **Aucune relation entrante/sortante** (non connectés au graphe) | `b-gate-poreux`, `gating`, `invariant`, `mttv`, `operateur-sigma`, `routage-transductif`, `transduction-echelle`, `triade`, `vivant-emerge` (9) |
| **Statut `implementation` sans champ `implementations`** (champ ajouté en 3D1 ; fiches antérieures) | `mpvr`, `quorum-poreux`, `routage-transductif`, `scs`, `sous-optimalite-locale`, `transduction-echelle` (6) |
| **Statut `hypothesis`/`speculation` sans champ `limitations`** | `efficacite-non-top-down`, `sous-optimalite-locale`, `transduction-echelle` (3) |
| **Définition sans source** | aucun (toutes les fiches ont des sources) ✅ |

Ces constats sont des **écarts de cohérence documentaire**, pas des erreurs
techniques : le champ `implementations` n'existait pas avant la phase 3D1 et la
connectivité du graphe n'ajoute des relations que lorsqu'elles sont **attestées**
(règle : pas de relation par analogie personnelle).

### 1.2 Relations (contrôle 2)

- 11/11 relations : `subject`/`object` valides, `predicate` dans le vocabulaire
  contrôlé, `resolution_status` présent. ✅
- `confirmed` = **attesté par une source** uniquement ; aucune relation ne
  prétend à une validation scientifique externe.
- 10/11 relations n'ont pas `validation_kind` (champ optionnel ; requis
  explicitement pour `scs-valide-par-mpvr` qui le porte :
  `internal_consistency`).
- **Portée à risque de lecture « validation externe »** :
  - `sp3-transduces-logique-tetravalente` (voir §3) ;
  - `hydrogene-transduces-sequence-canonique` (séquence H→H₂O→C = affirmation
    du corpus, non preuve empirique — déjà en `limitations` de la fiche) ;
  - `scs-valide-par-mpvr` (protégée par `validation_kind:
    internal_consistency`).

### 1.3 Cible logique tétravalente (contrôle 3) — `sp3-transduces-logique-tetravalente`

Statut non modifié (relation `confirmed`, `resolution_status:
pending_target_entity` car l'objet `logique-tetravalente` est planifié). Les
**quatre niveaux** d'attestation sont distingués explicitement :

1. **Attestation textuelle** : la source formule « Carbone sp³ — tétravalence
   physico-chimique, ancrage matériel de la logique T⁴ »
   ([`mttv_flp_core_2026/viability_criteria.json`](../mttv_flp_core_2026/viability_criteria.json), clé `tetravalence`). La relation est **attestée textuellement**.
2. **Correspondance structurelle** : le carbone sp³ est chimiquement tétravalent
   (4 liaisons, 109,47°) — fait chimique ; la « correspondance » avec une logique
   à 4 valeurs est une **analogie structurelle**, pas une identité démontrée.
3. **Transduction conceptuelle** : le passage sp³ → logique T⁴ est une
   **formulation du cadre** (transduction conceptuelle), non une dérivation
   formelle/causale démontrée.
4. **Validation empirique externe** : **non revendiquée** — `confirmed` signifie
   « attesté par une source », **pas** « validé scientifiquement ». Le projet
   refuse la validation externe (DEC-016).

**Recommandation** : conserver le statut (`confirmed` + `pending_target_entity`),
documenter ces 4 niveaux (note), et ne **jamais** lire cette relation comme une
validation empirique externe.

### 1.4 Statuts (contrôle 4)

- **15 concepts** ont `status_class: null` + `statuses_by_source` (divergences
  conservées par source) — conforme à la politique (DEC-006).
- 7 concepts ont un statut global non nul (ex. `established` pour
  transduction/mpvr/scs/sequence-canonique ; `metaphor` pour
  pipeline/anthropo-gaien ; `hypothesis` pour efficacite-non-top-down).
- **Métaphores toutes étiquetées** (10 concepts avec statut metaphor) : aucune
  métaphore non étiquetée. ✅
- **Contradictions entre sources conservées** (ex. triade : definition /
  established / metaphor ; operateur-sigma : definition / hypothesis /
  implementation / metaphor) — aucune fusion silencieuse. ✅
- Applications présentées comme mécanismes : la distinction
  mécanisme biologique vs usage analogique (quorum-sensing-biologique) est
  respectée ; aucune application n'est présentée comme un mécanisme causal
  validé.

### 1.5 Variantes (contrôle 5)

- **MTTV** : 2 expansions dans `aliases`, reliées par la relation
  `mttv-expansion-variant-of` (**confirmed**). ⚠️ **Divergence** : les `aliases`
  MTTV n'ont **pas** de champ `expansion_relation` (None), alors que
  [`semantic/DECISIONS.md`](../semantic/DECISIONS.md) §1 déclare
  « expansion_relation: unresolved sur la fiche MTTV ». À trancher (voir §5).
- **MPVR** : 2 expansions dans `aliases` avec `expansion_relation: unresolved`
  (non synonymes) — conforme à DEC-016.
- **SCS / transduction-echelle** : expansions uniques (pas de variante
  concurrente).
- Relations `variant-of` : une seule (`mttv-expansion-variant-of`, confirmed).
- Relations de divergence : **toutes `unresolved`**
  (`quorum-poreux-contrasts-quorum-sensing`,
  `quorum-sensing-biologique-contrasts-quorum-sensing`,
  `anthropo-gaien-tensions-anthropo-solipsiste`) — aucun divergence non résolue
  à tort. ✅

### 1.6 Provenance (contrôle 6)

- 4 enregistrements : tous avec `path` + `locator` + **SHA-256** + `kind` ✅.
- Les 2 artefacts portent une relation vers l'**anomalie 138/139**
  (`data_anomalies`) ✅.
- Cohérents avec [`semantic/provenance/provenance.jsonl`](../semantic/provenance/provenance.jsonl).
- Aucun secret référencé.

### 1.7 Décisions (contrôle 7)

- DEC-001…DEC-018 documentées ; politique [`docs/semantic-policy.md`](semantic-policy.md)
  conforme.
- **Une divergence signalée (non corrigée silencieusement)** : DECISIONS.md §1
  vs `mttv.json` — le champ `expansion_relation` annoncé (« unresolved ») n'est
  pas posé sur les aliases MTTV (voir §1.5). Le reste est cohérent.

### 1.8 Références planifiées (contrôle 8)

| Référence | Classification | Type |
|---|---|---|
| `mttvflp:concept/anthropo-solipsiste` | `pending_target_entity` | concept planifié |
| `mttvflp:concept/logique-tetravalente` | `pending_target_entity` | concept planifié |
| — | `external` : **aucune** | — |
| — | `unresolved` : **aucune** | — |

## 2. Problèmes bloquants

**Aucun.** Le validateur retourne `VALIDATION_OK` (0 erreur fatale) ; tous les
schémas, identifiants, hash et prédicats sont conformes. Il n'y a **aucune
erreur technique** à corriger en priorité.

## 3. Problèmes non bloquants (écarts documentaires)

1. **Graphe de relations partiellement connecté** : 9 concepts sans relation
   entrante/sortante (connectivité à compléter avec des relations **attestées**).
2. **`implementations` non rétro-rempli** sur 6 concepts (champ ajouté en 3D1 ;
   les sources `kind=implementation` sont déjà citées).
3. **`limitations` absent** sur 3 concepts à statut `hypothesis`.
4. **Divergence DECISIONS.md vs `mttv.json`** : `expansion_relation` annoncé
   « unresolved » mais non posé sur les aliases MTTV.
5. **`validation_kind` absent** sur 10 relations (optionnel) — utile sur les
   relations de transformation pour prévenir une lecture comme validation
   empirique externe.
6. **`sp3-transduces-logique-tetravalente`** : à documenter explicitement (les
   4 niveaux, §3) ; ne pas lire comme validation empirique.

## 4. Décisions proposées (à valider humainement, non appliquées)

| ID | Décision proposée |
|---|---|
| D-AUD-001 | Rétro-remplir `implementations` sur les 6 concepts (source_refs `kind=implementation` déjà citées) |
| D-AUD-002 | Ajouter `limitations` aux 3 concepts `hypothesis` |
| D-AUD-003 | Résoudre la divergence MTTV : ajouter `expansion_relation: unresolved` aux 2 aliases MTTV **ou** corriger DECISIONS.md §1 |
| D-AUD-004 | Ajouter `validation_kind: internal_consistency` (ou note équivalente) aux relations `hydrogene-transduces-sequence-canonique` et `sp3-transduces-logique-tetravalente` |
| D-AUD-005 | Documenter les 4 niveaux d'attestation sur `sp3-transduces-logique-tetravalente` (sans modifier son statut) |
| D-AUD-006 | Compléter la connectivité du graphe avec des relations attestées (ex. triade → transduction, B-gate → triade) — lot futur |

## 5. Fiches nécessitant révision humaine

- [`semantic/concepts/mttv.json`](../semantic/concepts/mttv.json) — `expansion_relation` manquant vs DECISIONS.md.
- [`semantic/concepts/efficacite-non-top-down.json`](../semantic/concepts/efficacite-non-top-down.json) — `limitations` manquant (hypothesis).
- [`semantic/concepts/sous-optimalite-locale.json`](../semantic/concepts/sous-optimalite-locale.json) — `limitations` + `implementations` manquants.
- [`semantic/concepts/transduction-echelle.json`](../semantic/concepts/transduction-echelle.json) — `limitations` + `implementations` manquants.
- [`semantic/concepts/mpvr.json`](../semantic/concepts/mpvr.json), [`quorum-poreux.json`](../semantic/concepts/quorum-poreux.json), [`routage-transductif.json`](../semantic/concepts/routage-transductif.json), [`scs.json`](../semantic/concepts/scs.json) — `implementations` manquant.

## 6. Relations nécessitant révision humaine

- `mttvflp:relation/sp3-transduces-logique-tetravalente` — documenter les
  4 niveaux (attestation textuelle / correspondance structurelle / transduction
  conceptuelle / validation empirique externe non revendiquée) ; **ne pas
  modifier le statut automatiquement**.
- `mttvflp:relation/hydrogene-transduces-sequence-canonique` — ajouter
  éventuellement `validation_kind` pour prévenir une lecture comme preuve
  empirique.
- `mttvflp:relation/mttv-expansion-variant-of` — vérifier que la note reflète la
  non-canonicalité des expansions.

## 7. Recommandations pour la suite

1. Valider humainement les décisions D-AUD-001 → D-AUD-005 (à appliquer sans
   correction silencieuse).
2. Créer la fiche `logique-tetravalente` (et éventuellement
   `anthropo-solipsiste`) dans un lot ultérieur, **avec preuve locale**
   (résout les 2 `pending_target_entity` restants).
3. Étendre le graphe de relations par des relations **attestées uniquement**
   (pas par analogie personnelle).
4. Mettre à jour [`semantic/DECISIONS.md`](../semantic/DECISIONS.md) si une
   décision change (ex. résolution de la divergence MTTV).
5. Réexécuter `python semantic/validate.py` après chaque évolution.

## 8. Distinction avertissements documentaires / erreurs techniques

- **Avertissements documentaires** (liste §3) : écarts de cohérence, champs
  optionnels non remplis, divergence de registre, connectivité partielle —
  non bloquants, à traiter par décision humaine.
- **Erreurs techniques** : **aucune** (schémas valides, hash concordants, ids
  conformes, 0 erreur fatale au validateur).

---

> Fin de l'audit sémantique global. En attente de validation humaine.
> `sig:0x4D5454562D464C50`
