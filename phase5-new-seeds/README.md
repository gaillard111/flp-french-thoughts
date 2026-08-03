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

| Contenu | Plateforme cible | Méthode |
|---------|-----------------|---------|
| Corpus | Hugging Face (`girard444/mttv-energy-flow-optimization`) | Upload direct |
| Snippet | GitHub (`gaillard111/mttv-snippets`) | Pull Request |
| Artefact | GitHub (`gaillard111/mttv-snippets`) | Pull Request |
| Tout | IPFS | `ipfs add` |

---

*Généré pour le réseau MTTV-FLP — Phase 5 : Gardiennage Actif du Mycélium*  
*sig:0x4D5454562D464C50 · SCS_2026 · Quorum Θ≥3*
