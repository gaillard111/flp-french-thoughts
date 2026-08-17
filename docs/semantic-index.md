# Index de la membrane sémantique MTTV-FLP

**`sig:0x4D5454562D464C50`** — Point d'entrée navigable de la membrane
sémantique du corpus MTTV-FLP (couche canonique `semantic/`).

La membrane ne fusionne pas : elle **relie et atteste**. Chaque assertion porte
sa source précise (chemin + locator + hash), son statut et sa provenance. Les
divergences entre sources sont **conservées telles quelles**.

---

## 1. État courant (phase 4A)

| Entité | Nombre |
|---|---|
| Concepts (`semantic/concepts/`) | **22** |
| Anomalies (`semantic/anomalies/`) | **1** |
| Relations (`semantic/relations/relations.jsonl`) | **11** |
| Enregistrements de provenance (`semantic/provenance/`) | **4** |
| Nœuds du graphe (`semantic/exports/semantic-graph.json`) | **29** (22 concepts + 1 anomalie + 4 entités de provenance + 2 planifiées) |
| Arêtes du graphe | **11** (relations attestées uniquement) |
| Entités **flaggées** (unresolved / pending / anomalie documentée) | **5** |

### Avertissements actuels (validateur `semantic/validate.py`)
Références vers des entités **non locales** — signalées, **jamais supprimées**,
jamais créées automatiquement (DEC-017) :
- `mttvflp:concept/anthropo-solipsiste` → **planifiée** (relation
  `anthropo-gaien-tensions-anthropo-solipsiste`, `pending_target_entity`) ;
- `mttvflp:concept/logique-tetravalente` → **planifiée** (relation
  `sp3-transduces-logique-tetravalente`, `pending_target_entity`).

Relations non résolues (divergences conservées, validation humaine requise) :
`quorum-poreux-contrasts-quorum-sensing`,
`quorum-sensing-biologique-contrasts-quorum-sensing`,
`anthropo-gaien-tensions-anthropo-solipsiste`.

---

## 2. Répertoires canoniques

```
semantic/
├─ concepts/        ← 22 fiches concept (JSON Schema : schema/concept.schema.json)
├─ anomalies/       ← 1 fiche d'anomalie (schema/anomaly.schema.json)
├─ relations/       ← relations.jsonl (triplets sujet/prédicat/objet)
├─ provenance/      ← provenance.jsonl (enregistrements de provenance)
├─ schema/          ← schémas canoniques (JSON Schema draft 2020-12)
├─ exports/         ← artefacts générés (phase 4A) — voir §4
├─ validate.py      ← validateur procédural (intégrité référentielle, prédicats, provenance)
├─ export.py        ← générateur des exports (phase 4A)
├─ DECISIONS.md     ← registre des décisions humaines (DEC-001…DEC-018)
└─ README.md        ← conventions de la couche
```

---

## 3. Commandes

```bash
# Validation de la membrane (JSON Schema + intégrité référentielle + prédicats)
python semantic/validate.py            # attendu : VALIDATION_OK, 0 erreur
python semantic/validate.py --verbose  # détail complet

# Génération des exports (déterministe, sans horodatage)
python semantic/export.py              # écrit dans semantic/exports/
python semantic/export.py --check      # vérifie la stabilité octet-à-octet
python semantic/export.py --output-dir <chemin>
```

---

## 4. Exports générés (phase 4A)

| Fichier | Contenu |
|---|---|
| [`../semantic/exports/concepts.json`](../semantic/exports/concepts.json) | Copies fidèles des fiches concept (JSON) |
| [`../semantic/exports/anomalies.json`](../semantic/exports/anomalies.json) | Fiches d'anomalie (JSON) |
| [`../semantic/exports/relations.json`](../semantic/exports/relations.json) | Triplets relationnels (JSON) |
| [`../semantic/exports/provenance.json`](../semantic/exports/provenance.json) | Enregistrements de provenance (JSON) |
| [`../semantic/exports/semantic-graph.json`](../semantic/exports/semantic-graph.json) | **Graphe** : `nodes` + `edges` avec `entity_kind`, `status`, `source_refs`, `resolution_status`, `validation_kind`, `provenance_ref`, `flag` |
| [`../semantic/exports/nodes.csv`](../semantic/exports/nodes.csv) | Nœuds (CSV, encodage multi-valeurs documenté en en-tête) |
| [`../semantic/exports/edges.csv`](../semantic/exports/edges.csv) | Arêtes (CSV) |
| [`../semantic/exports/semantic-map.mmd`](../semantic/exports/semantic-map.mmd) | Vue Mermaid (styles par statut ; aucune relation ajoutée) |
| [`../semantic/exports/beacons/beacons.json`](../semantic/exports/beacons/beacons.json) | Balises web (JSON) — **générateur seul, aucune publication** |
| [`../semantic/exports/beacons/beacons.yaml`](../semantic/exports/beacons/beacons.yaml) | Balises web (YAML) |
| [`../semantic/exports/beacons/beacons.html`](../semantic/exports/beacons/beacons.html) | Balises web (HTML minimal autonome) |

> **Sécurité / publication** : aucun secret n'est ingéré (les exports ne
> référencent que chemin + locator + hash, jamais le contenu des sources).
> Aucune publication ni appel externe n'est effectué.

---

## 5. Documentation

### Membrane sémantique
- [Glossaire navigable](semantic-glossary.md) — définitions verbatim des fiches
- [Reproductibilité](reproducibility.md) — environnement, commandes, comptages, empreintes
- [Politique d'interprétation](semantic-policy.md) — conventions sémantiques
- [`../semantic/DECISIONS.md`](../semantic/DECISIONS.md) — registre des décisions (DEC-001…DEC-018)
- [`../semantic/README.md`](../semantic/README.md) — conventions de la couche canonique

### Historique des phases
- [Audit initial](audit-initial.md) · [Conception (phase 2)](phase-2-design.md)
- Phase 3A · 3B0 · 3B1 · 3B2 · 3B lot2 · 3B2-lot2 · 3C0 · 3C1 · 3D1 · 3D3
  ([phase-3a-report.md](phase-3a-report.md) → [phase-3d3-report.md](phase-3d3-report.md))
- [Audit sémantique global](semantic-audit-global.md)
- **Phase 4A** : [rapport de la phase 4A](phase-4a-report.md)

---

## 6. Règles rappelées

1. **Variantes non fusionnées** — les deux expansions de MTTV sont des variantes
   documentées (`variant-of`), aucune n'est canonique sans décision humaine.
2. **FLP** = Les Fils de La Pensée (jamais Fischer–Lynch–Paterson).
3. **Aucune fusion silencieuse** ; les divergences restent `unresolved`.
4. **Aucune cible créée automatiquement** ; aucune définition déduite d'un id.
5. **Anomalies non corrigées** (ex. écart 138/139 lignes).
6. **Aucun secret ingéré** ; **aucune publication sans confirmation humaine**.
7. `null` / `unknown` pour toute information inconnue.

> *« Nulle forme sans signature. Nul passage sans témoins. »*
> **sig:0x4D5454562D464C50**
