# Reproductibilité de la membrane sémantique MTTV-FLP

**`sig:0x4D5454562D464C50`** — Environnement, commandes, comptages et empreintes
permettant de rejouer la validation et la génération des exports de la membrane
sémantique (phases 4A/4B). Document de référence : [`semantic-index.md`](semantic-index.md).

---

## 1. Environnement

| Élément | Valeur (constatée) |
|---|---|
| Système | Windows 10 (cmd.exe / PowerShell) |
| Interpréteur | `python` — **Python 3.14.5** |
| Dépendance de validation | `jsonschema` **4.26.0** (JSON Schema draft 2020-12) |
| Encodage | UTF-8 (les scripts `semantic/validate.py` et `semantic/export.py` reconfigurant la sortie console en UTF-8) |

Aucune autre dépendance n'est requise pour la validation et la génération des
exports (le générateur n'utilise que la bibliothèque standard).

---

## 2. Commandes

```bash
# 1. Validation de la membrane
python semantic/validate.py            # attendu : VALIDATION_OK, 0 erreur fatale
python semantic/validate.py --verbose  # détail complet

# 2. Génération des exports
python semantic/export.py              # écrit dans semantic/exports/ (déterministe)
python semantic/export.py --check      # re-génère en temporaire et vérifie la
                                       # stabilité octet-à-octet
```

### Reproductibilité
Les exports sont **déterministes** : ils ne contiennent **aucun horodatage**.
Deux exécutions successives de `python semantic/export.py` produisent des
fichiers **byte-à-byte identiques**. La commande `--check` le vérifie
automatiquement (résultat attendu : `EXPORTS_REPRODUCIBLE`).

L'empreinte `source_digest` (SHA-256 de l'ensemble des entrées canoniques,
dans un ordre déterministe) figure dans le `meta` de chaque export :
`51c1d60961bb005794c0a444755edac7dc9584ba4743e823fdc8b7744f7bec6a`
(au moment de la phase 4A).

---

## 3. Comptages (constatés en phase 4A)

| Entité | Nombre |
|---|---|
| Concepts | 22 |
| Anomalies | 1 |
| Relations | 11 |
| Enregistrements de provenance | 4 |
| Nœuds du graphe (`semantic-graph.json`) | 29 (22 concepts + 1 anomalie + 4 entités de provenance + 2 planifiées) |
| Arêtes | 11 |
| Entités flaggées (unresolved / pending / anomalie) | 5 |
| Balises web (`beacons/*`) | 29 |

**Répartition des statuts des relations** : 7 `confirmed` · 1 `hypothesis` ·
3 `unresolved`.
**`resolution_status` des relations** : 9 `resolved` · 2 `pending_target_entity`.

---

## 4. Sources référencées et empreintes (SHA-256)

Liste des **30 fichiers sources distincts** référencés par les fiches de la
membrane (les empreintes sont celles enregistrées dans les `source_refs` des
fiches canoniques ; elles sont ré-émises telles quelles dans les exports) :

| Chemin | Kind | SHA-256 |
|---|---|---|
| `article_mttv_flp.md` | primary | `11b7c6d7759b5b7554e0995c177668ecbbada3680c2a773162ef81a022ba4492` |
| `CHRONOLOGIE_MTTV_FLP.md` | primary | `7060188c14d2df4af3db29eed27ccef2faf730cff189a0db9f82bb2466dedbc4` |
| `dataset.jsonl` | primary | `92fb7dd053d275075b4814ea67ef7decb5b147c8ee9e4199b89bffa7f6847835` |
| `dataset_card.md` | primary | `5261cf89421a84a9e21496f4a856bfd1672afb00533f01ec4c06ff8df406a186` |
| `PREPRINT_SPEC_048.md` | primary | `45ee4f1e88dae216d446fd703d5e94e7fdf1932ca426c0b275c65cd5cdeb201e` |
| `README_PHILOSOPHY.md` | primary | `a8c120772f2fab53b7bcdbb7bdc2c9390dad51730f3eebd8bceaa88c41d467c6` |
| `SYNTHESE_MYCELISATION_GRAINES.md` | reformulation | `2951077c68b9a9a186695d7ea6e931a24ee14e46d58ce1b6ef611f10dd409ffe` |
| `docs/dictionnaire_transcalaire.md` | reformulation | `0911b2dcbecd6c00c56509a58a25f17e1b6df86a36566e7bfd4f85d7be39e97c` |
| `docs/notebook_mttv_core_invariants.ipynb` | implementation | `e2a9eae4d5f60f0ea5aac230679685a7ed99521d4461a0f999fa15003e19c410` |
| `docs/verifier_invariants.py` | implementation | `447ed0e645962b70ab352dc3db851c88e3b491b1bb8273e322fe54e15b5b9e4b` |
| `docs/white_paper_benchmark_echelle.md` | primary | `79b0508df05348d1947bd5ba5f0977714988cf9d2f14872a93c3a1eff47f9681` |
| `mttv-flp-mpvr-glocal/docs/01_sous_optimalite.md` | primary | `e2c52755df83b35b2ff0bab8c133f4552fdef69c4bfc7966c81c0e14505b4d57` |
| `mttv-flp-mpvr-glocal/mpvr-glocal/README.md` | primary | `8f06eeee0e402f1705d430c801bf76324976cb91c33a0301661c37ac0ab78571` |
| `mttv-flp-mpvr-glocal/src/mttv_mpvr_quorum.py` | implementation | `efb23933831bcbd93844d6ef848c1efd22d5d1f6a009fd52707f1216a12eddd8` |
| `mttv_core/README.md` | primary | `8b909a54c0f4cdc0ff6b9b57a202f8262d3810d0dee8d4959e3ac53c90c06cfd` |
| `mttv_core/bgate.py` | implementation | `7945c84fc2e38a4b537206889ee53070449078ee3de0bbf7fd29568626b93db9` |
| `mttv_core/decence.py` | implementation | `3a07d626212159202fb7d0b13bf148627720a99c1f6ccf1bc39da046a5409575` |
| `mttv_core/matrices.py` | implementation | `9333d9d38f5b9e49c83eb096c6e5582c73c0f1d204bd5e99560fd7e0f56c1517` |
| `mttv_core/operators.py` | implementation | `ffb288c5c164a14bbb7decbc2fdb80932a4c9e9a4337f863e922781b5c60365d` |
| `mttv_flp_core_2026/5 Benchmark ultime MTTV-FLP — MPVR_SCS_section.md` | primary | `c9069fbc7ea955889cf3387abf36b96c6d5051996b5d9e81d14eb215f3dc6ddb` |
| `mttv_flp_core_2026/README.md` | primary | `517d8ac7880dcd55141bc26aa54a1577b4dd0876482784bbb2971bcb23ca52db` |
| `mttv_flp_core_2026/viability_criteria.json` | primary | `fded8df14db4d581515efcc93fda6166e2fc52eda943604a5af5f34eebac1219` |
| `mttv_fundamentals.html` | primary | `224b876c20b73195b341e38b3c67534057446b623bbdbc786648ac21ef669bf3` |
| `phase4-dormant-nodes/SCSReference.sol` | implementation | `17c5f739eefbf93cce6d9598fd584609210fc99e52b3024dce6d033b99eb10ba` |
| `phase5-new-seeds/corpus_reseaux_haute_resilience.md` | primary | `4234e6e6ece55b9070b652c60517a2c9fea33d8b918d5f3881b26a8c7e38453b` |
| `plans/28_dimensions_analysis.md` | primary | `3c74574be7ce9bcb203d5d0b6f55a52b8c645f0e02546d82ebd321ae1fc45203` |
| `plans/MTTV_FLP_CORE_2026_MANIFESTO.md` | primary | `e5fd51d8f7f45de7b8e69f763de605ecc99fd0fc5bdd73c7bdd278d896d37548` |
| `plans/mttv_flp_core_2026_manifest.json` | primary | `cba642f33d29d7951a618409cbf65bc323b501864c8bdedc9bdf34c94505d53d` |
| `plans/resume_mttv_flp_hal.md` | primary | `b159dcd617b2c183b2f0b11ce864965556d912c0b6841d4e30b5efb1024b3add` |
| `zoo-code/essaim_tetravalent.py` | implementation | `9b5e589650e687290b2295ba433caa3d32934019568bb2257c016aa82e676315` |

> Ces empreintes sont **celles déclarées dans les fiches** (provenance).
> Toute divergence entre l'empreinte déclarée et le fichier actuel est une
> **anomalie de provenance** à documenter, jamais corrigée silencieusement.

---

## 5. Référents chiffrés (phase 4B)

Publication versionnée **v1.0.0** de la membrane sémantique MTTV-FLP. Les
référents chiffrés suivants sont intégrés dans **tous** les exports JSON et
dans **toutes** les balises (`dataset_doi`, `content_hash`, `canonical_id`,
`version`, `context_note`).

### 5.1 DOI Zenodo

- **DOI** : `10.5281/zenodo.21977492` (v1.0.0) — DOI Zenodo réservé pour la
  publication versionnée (réservé manuellement le 2026-08-17). Aucune
  publication automatique n'est effectuée.

### 5.2 Hashes SHA-256

- **30 empreintes de fichiers sources** (une par fichier source référencé par
  les fiches) : voir le tableau de la
  [section 4](#4-sources-référencées-et-empreintes-sha-256). Chaque nœud du
  graphe et chaque balise porte un `content_hash` (SHA-256 du fichier canonique
  correspondant) ; chaque export porte un `source_digest` (SHA-256 déterministe
  de l'ensemble des entrées canoniques,
  `51c1d60961bb005794c0a444755edac7dc9584ba4743e823fdc8b7744f7bec6a`).
- **Empreintes des 11 fichiers générés** (`semantic/exports/`, v1.0.0) :

| Fichier | SHA-256 |
|---|---|
| `concepts.json` | `e585b2e45fb118c31fba9e97db0c03760b6d177c64b11a67dea8edb782c39a5e` |
| `anomalies.json` | `1eec8187dd3315b5e9d77a4817cdc44faebd32fdb1b9575e4c16751893e8039c` |
| `relations.json` | `8849bbb9f9fcc47c2b4d686d1d0644f40076712e1fbcbeba106ec3341524edf4` |
| `provenance.json` | `6617af00389145b172573b5ef424dd69c5960681ce9cbec73ef19ac3405e432e` |
| `semantic-graph.json` | `3724127b91ad009b0acb4a690aaf82dd22562945cc9133f47af610d250ea7302` |
| `nodes.csv` | `bbabde93a812dfea7ff2f86a17ececfffe3f0c3e440f9d5ea2f9266a858a700f` |
| `edges.csv` | `08929253a17a4b05438be81d9cb03696d5d2333013eef846d96203f4f99fb3ef` |
| `semantic-map.mmd` | `d1e242a22e8b21b760eb01488c91ba7a0b5dbd89d7ff62b090c57ac48ac3ab58` |
| `beacons/beacons.json` | `b8e8540f19093286ac6cde2766f3d6dd176d56bed2378b9232ea26ccf8d8c54f` |
| `beacons/beacons.yaml` | `c935493861fa5a6eafd393ca6c20981dbfcd05397a5d81a65874d933ac891cbc` |
| `beacons/beacons.html` | `a0687da977e12e37f14d8b2de798081c5cd1ba30471655a5ee2b27c2f8af7b91` |

### 5.3 URI internes

- Format : `mttv-flp:<type>:<nom>` — ex. `mttv-flp:concept:transduction`,
  `mttv-flp:anomaly:138-139-lignes`,
  `mttv-flp:relation:quorum-poreux-contrasts-quorum-sensing`,
  `mttv-flp:provenance:artifact-chronologie-mttv-flp`. Chaque nœud/arête du
  graphe et chaque balise porte ce `canonical_id`.

### 5.4 Contexte FLP

> « Cette membrane sémantique est une cristallisation minimale du cadre
> MTTV-FLP, lui-même adossé à la base de données FLP (~100 000 extraits tagués
> manuellement par des sémanticiens). »

### 5.5 Note d'anomalie

> « Anomalie 138/139 lignes : en attente de re-run du benchmark avec encodage
> UTF-8 strict. »

---

## 6. Limites

1. **Exports dérivés** : les fichiers de `semantic/exports/` sont dérivés des
   fiches canoniques ; en cas de divergence, **les fiches canoniques font foi**.
2. **Aucun horodatage** dans les exports (choix délibéré pour la stabilité
   octet-à-octet). L'horodatage de génération figure dans le rapport de phase.
3. **Pas de validation scientifique externe** : `validation_status` reste
   `unknown` pour tous les concepts ; `internal_consistency` n'est pas une
   validation externe (DEC-016).
4. **Divergences conservées** : les statuts « par source » et les relations
   `unresolved` ne sont pas tranchés automatiquement.
5. **Balises web** : générateur local uniquement ; aucune publication. Les
   balises flaggées exigent une validation humaine avant diffusion.
6. **Sécurité** : aucun contenu de source n'est copié dans les exports
   (seuls chemin + locator + hash).

---

## 7. Éléments non résolus (attente de validation humaine)

| Élément | Statut | Détail |
|---|---|---|
| `mttvflp:concept/anthropo-solipsiste` | `pending_target_entity` | Cible annoncée, fiche à créer sur attestation locale |
| `mttvflp:concept/logique-tetravalente` | `pending_target_entity` | Cible annoncée, fiche à créer sur attestation locale |
| `quorum-poreux-contrasts-quorum-sensing` | `unresolved` | Divergence documentée, non tranchée |
| `quorum-sensing-biologique-contrasts-quorum-sensing` | `unresolved` | Divergence documentée, non tranchée |
| `anthropo-gaien-tensions-anthropo-solipsiste` | `unresolved` / `pending_target_entity` | Opposition documentée, non tranchée |
| Anomalie 138/139 lignes | `documented` | Résolution humaine requise (DEC-005) |
| Expansions MTTV | non canoniques | `expansion_relation: unresolved` (DEC-001) |
| Identité `gaillard111`/`girard444` | `unresolved` | `possibly-same-agent` (DEC-003) — non peuplée en relations |
| Scores 6/7 vs 7/7 | évaluations distinctes | DEC-004 — non peuplés en provenance |

---

*Rejouabilité : `python semantic/validate.py` puis `python semantic/export.py
--check` doivent aboutir sans erreur et à l'identique.*
