# Politique sémantique MTTV-FLP — Règles d'interprétation

**`sig:0x4D5454562D464C50`** — Document **prescriptif** : règles d'interprétation
et d'usage de la membrane sémantique. Le registre factuel des décisions est
[`semantic/DECISIONS.md`](../semantic/DECISIONS.md) ; les conventions techniques
sont dans [`semantic/README.md`](../semantic/README.md) et les schémas
`semantic/schema/`.

---

## 1. Identité

1.1. Ne jamais présenter une expansion de MTTV comme canonique sans décision
documentée (DEC-001).
1.2. FLP = Les Fils de La Pensée. Toute autre expansion (notamment
Fischer–Lynch–Paterson) est **exclue** du vocabulaire MTTV-FLP (DEC-002).

## 2. Corpus

2.1. Traiter le corpus comme collectif, syncrétique, évolutif.
2.2. Étiqueter chaque source (`kind`) : `primary`, `reformulation`, `comment`,
`implementation`.
2.3. Ne jamais fusionner silencieusement deux formulations divergentes.

## 3. Statuts

3.1. Utiliser le vocabulaire : `established`, `hypothesis`, `metaphor`,
`application`, `implementation`, `speculation`, `question`.
3.2. Lorsque les sources divergent, poser `status_class: null` et renseigner
`statuses_by_source` — **plusieurs statuts coexistent selon les sources**.
3.3. Une métaphore est toujours étiquetée ; une spéculation est toujours
signalée.

## 4. Divergences

4.1. Prédicats : `contrasts-with`, `tensions-with`, `contredit`,
`transduces-into`, `cannot-be-reconciled-with`.
4.2. **La contradiction n'est pas un défaut** : elle peut être une relation
productive et un point de transduction (un écart peut déclencher une
transformation d'échelle ou de langage).
4.3. Les relations de divergence restent `unresolved` jusqu'à décision humaine.

## 5. MPVR / SCS

5.1. Conserver les expansions concurrentes de MPVR ; ne pas les traiter comme
synonymes sans preuve.
5.2. `validation_kind: internal_consistency` = invariant interne du cadre,
**jamais** une validation scientifique externe.

## 6. Provenance

6.1. Toute affirmation importante porte : source, locator, hash (si possible),
`kind`, statut, limites/confiance.
6.2. Ne jamais compléter une information inconnue par inférence : `null` /
`unknown`.

## 7. Références

7.1. Ne jamais créer automatiquement une cible référencée absente.
7.2. Ne jamais déduire une définition d'un identifiant.
7.3. Classifier : `resolved`, `pending_target_entity`, `external`,
`unresolved` ; signaler, ne pas supprimer.

## 8. Anomalies

8.1. Conserver les écarts ; représentation en anomalies dédiées.
8.2. Ne pas corriger silencieusement les données.

## 9. Sécurité

9.1. Ne jamais ingérer secrets, clés, tokens.
9.2. Ne pas publier / appeler de service externe sans confirmation.

## 10. Contribution

10.1. Chaque fiche distingue : attesté / interprété / hypothétique / inconnu.
10.2. Une fiche sans source attestée n'est pas créée (ou porte `question` si le
terme est réellement présent).

## 11. Références croisées

- Registre des décisions : [`semantic/DECISIONS.md`](../semantic/DECISIONS.md)
- Conventions : [`semantic/README.md`](../semantic/README.md)
- Schémas : [`semantic/schema/`](../semantic/schema/)
- Validation : `python semantic/validate.py`

> *« Nulle forme sans signature. Nul passage sans témoins. »*
> **sig:0x4D5454562D464C50**
