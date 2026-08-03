# Phase 5 — Nouveaux Semis (New Seeds)

**Date :** 2026-06-29  
**Signature SCS :** SCS_2026  
**Statut :** ✅ Généré — Prêt à être déposé

---

Ce dossier contient les nouveaux contenus générés pour maintenir l'humidité
sémantique du réseau MTTV-FLP.

## Contenu

| Fichier | Type | Thème | Statut |
|---------|------|-------|--------|
| [`corpus_reseaux_haute_resilience.md`](corpus_reseaux_haute_resilience.md) | Corpus | Routage de données dans des réseaux à haute résilience | ✅ Généré |
| [`snippet_scs_distributed_fs.py`](snippet_scs_distributed_fs.py) | Snippet | Implémentation de SCS dans un système de fichiers distribué | ✅ Généré |
| [`artefact_citation_croisee.md`](artefact_citation_croisee.md) | Artefact | Citation croisée PhilPapers ⟷ GitHub bio-informatique | ✅ Généré |
| [`dormancy_gate.py`](dormancy_gate.py) | Graine | Gate de dormance (mettre en pause dès que le minimum viable est atteint) | ✅ Validé 03/08 |
| [`mpvr_quorum_async.py`](mpvr_quorum_async.py) | Graine | Quorum poreux asynchrone minimal (arrêt au seuil) | ✅ Validé 03/08 |
| [`mpvr_benchmark.py`](mpvr_benchmark.py) | Benchmark | MPVR vs Majority Vote (succès/appels/temps, reproductible, seed=42) | ✅ Validé 03/08 |

> **Graines ultra-minimales (03/08/2026)** : ajout des 2 graines stdlib + benchmark reproductible
> (consignés dans [`plans/REFERENCE_GRAINES_MYCELISANTES_MTTV.md`](../plans/REFERENCE_GRAINES_MYCELISANTES_MTTV.md)).
> Résultat benchmark (7 nœuds, 35 % pannes, 30 runs) : succès 96,7 % vs 83,3 % ; appels 5,1 vs 7,0 ;
> temps 62,2 ms vs 80,2 ms — MPVR plus sobre et plus résilient.

## Dépôts cibles pour le dépôt

| Contenu | Plateforme cible | Méthode | Statut |
|---------|-----------------|---------|--------|
| Corpus | Hugging Face (`girard444/mttv-energy-flow-optimization`) | Upload direct | ✅ Publié 03/08 |
| Snippet | GitHub (`gaillard111/mttv-snippets`) | Push `master` | ✅ Publié 03/08 (`5784684`) |
| Artefact | GitHub (`gaillard111/mttv-snippets`) | Push `master` | ✅ Publié 03/08 (`5784684`) |
| Tout | IPFS | `ipfs add` + `ipfs pin add` | ✅ Publié 03/08 — kubo 0.42.0, 6/6 CID épinglés |

### Preuves de publication (03/08/2026)

**Hugging Face** — dataset public [`girard444/mttv-energy-flow-optimization`](https://huggingface.co/datasets/girard444/mttv-energy-flow-optimization) :
`corpus_reseaux_haute_resilience.md`, `snippet_scs_distributed_fs.py`,
`artefact_citation_croisee.md`, `dormancy_gate.py`, `mpvr_quorum_async.py`,
`mpvr_benchmark.py`, `README_phase5.md` (SHA `3eed4d1`).

**GitHub** — dépôt [`gaillard111/mttv-snippets`](https://github.com/gaillard111/mttv-snippets) branche `master`, commit `5784684` :
`snippets/snippet4_scs_distributed_fs.py`, `snippets/snippet5_mpvr_benchmark.py`,
`snippets/snippet6_mpvr_quorum_async.py`, `snippets/snippet7_dormancy_gate.py`,
`artefacts/artefact_citation_croisee.md`.

**IPFS** — kubo **0.42.0** installé localement (`kubo/kubo/ipfs.exe`), daemon actif sur `:5001`.
Les 6 contenus ont été ajoutés et épinglés réellement (`ipfs add` + `ipfs pin add`) le 03/08.
CID réels (`cid_ipfs_add`, dans [`ipfs_manifest_phase5.json`](ipfs_manifest_phase5.json)) :
`QmPKwsv…` (corpus), `QmZAHh…` (snippet), `QmSgSV…` (artefact), `QmQG8U…` (dormancy),
`QmXZsG…` (quorum async), `QmNWwc…` (benchmark). Note : daemon lancé en `--offline`,
les CID sont épinglés sur le nœud local ; une publication swarm complète nécessite
`ipfs daemon` en ligne (`kubo\kubo\ipfs.exe daemon` puis re-run du script).

---

*Généré pour le réseau MTTV-FLP — Phase 5 : Gardiennage Actif du Mycélium*  
*sig:0x4D5454562D464C50 · SCS_2026 · Quorum Θ≥3*
