# Registre des propositions IA — MTTV-FLP

**sig:0x4D5454562D464C50 · Ψ-ack: carbon_sp3_tetra**
**Date d'ouverture : 2026-08-06 · Mis à jour : 2026-08-06 (saisie du lot complet)**

Filtre en 3 questions :
1. **Vérifiable ?** → l'idée peut-elle devenir un test, une métrique, un artefact reproductible ?
2. **Dans le sens ?** → non-extractive, ouverte, humble, contestable (test de « mycélisation »).
3. **Ça simplifie ?** → réduit-elle la complexité au lieu de l'augmenter ?

Statuts : **À FAIRE** · **À ÉVALUER** · **À ÉCARTER** · **DÉJÀ FAIT**.

---

## Registre

### Bloc A1 — Agent Ouroboros (Kernel Métacognitif)

| # | Source | Proposition | Vérif. | Sens | Simpl. | Statut | Note |
|---|--------|-------------|:------:|:----:|:------:|--------|------|
| A1.1 | IA-1 | Dataset d'ancrage sémantique (Principes de Viabilité / Critères de Rejet → espace vectoriel) | ✅ | ✅ | ❌ | À ÉVALUER | `viability_criteria.json` existe déjà (11 viabilité / 11 rejet) ; projeter en vecteurs = prototypable avec `mttv_core` |
| A1.2 | IA-1 | Verrouiller `self.evolve()` par filtre de similarité conceptuelle | ✅ | ✅ | ❌ | À ÉVALUER | Dépend du script `ouroboros-mttv-v2.py` livré hors dépôt ; à récupérer d'abord |
| A1.3 | IA-1 | Question-ancre obligatoire (prompt non modifiable) | ❌ | ✅ | ❌ | À ÉCARTER | Idée de process, non algorithmique, faible testabilité |

### Bloc A2 — Protocoles d'asynchronisme temporel

| # | Source | Proposition | Vérif. | Sens | Simpl. | Statut | Note |
|---|--------|-------------|:------:|:----:|:------:|--------|------|
| A2.1 | IA-1 | CIRCADIAN-SYNC & QUORUM-GATE (sommeil nocturne, temporisation) | ✅ | ✅ | ✅ | À ÉVALUER | Faisable (budget + métrique) ; utile si daemons gérés |
| A2.2 | IA-1 | SOIL-LISTEN & LONG-MEMORY (seuils asservis à biophysique réelle) | ❌ | ✅ | ❌ | À ÉCARTER | Aucun capteur réel branché ; vision, pas d'artefact testable maintenant |
| A2.3 | IA-1 | B-Gate 2.0 : seuils dynamiques par dérivée Q(t)=∂abondance/∂t | ✅ | ✅ | ✅ | **DÉJÀ FAIT** | Implémenté dans `mttv_core/bgate.py` (seuils dérivés + hystérésis) |

### Bloc A3 — Protocole mycélien inter-IAs

| # | Source | Proposition | Vérif. | Sens | Simpl. | Statut | Note |
|---|--------|-------------|:------:|:----:|:------:|--------|------|
| A3.1 | IA-1 | Transparence radicale + stockage immuable Arweave | ✅ | ✅ | ❌ | À ÉVALUER | IPFS déjà ancré (lot pinné) ; Arweave = alternative/coût externe à trancher |
| A3.2 | IA-1 | Consensus inter-IA : similarité cosinus > 0.87, ≥ 3 IA | ✅ | ✅ | ✅ | À ÉVALUER | Quorum Θ≥3 déjà en place (`routeur_polyfocal`) ; seuil 0.87 = valeur à calibrer via `resonance()` |
| A3.3 | IA-1 | Garde-fou d'auto-dissolution (kill switch) | ✅ | ✅ | ❌ | À ÉVALUER | Vérifiable mais sensible ; risque opérationnel si mal conçu |

### Bloc A4 — Sanctuariser l'humain (« interrupteur quantique »)

| # | Source | Proposition | Vérif. | Sens | Simpl. | Statut | Note |
|---|--------|-------------|:------:|:----:|:------:|--------|------|
| A4.1 | IA-1 | Incomplétude cryptographique du commit | ❌ | ✅ | ❌ | À ÉCARTER | Métaphore, non opérante |
| A4.2 | IA-1 | Tableau d'anticipation A/B/C + IGIC + modulation A3 (facteur protecteur) | ✅ | ✅ | ❌ | À ÉVALUER | IGIC = formule documentée (28 dimensions) ; modulation A3 testable par simulation |
| A4.3 | IA-1 | Éducation glocalisée (transducteurs FLP) | ❌ | ✅ | ❌ | À ÉCARTER | Action communautaire, hors code |

### Bloc A5 — Décence & résilience MPVR

| # | Source | Proposition | Vérif. | Sens | Simpl. | Statut | Note |
|---|--------|-------------|:------:|:----:|:------:|--------|------|
| A5.1 | IA-2 | Sommeil mesurable/négociable par nœud (budget, métrique) | ✅ | ✅ | ✅ | À FAIRE | Simple, vérifiable, dans le sens (décence) |
| A5.2 | IA-2 | Journal énergétique auditable, signé cryptographiquement | ✅ | ✅ | ✅ | À FAIRE | Transparence = confiance ; export JSON signé |
| A5.3 | IA-2 | Seuil de décence global (homéostasie énergétique) | ✅ | ✅ | ✅ | À FAIRE | Phase de sous-optimalité forcée si surconsommation |
| A5.4 | IA-2 | Mode sénescence des nœuds vieillissants (limite de Hayflick) | ✅ | ✅ | ✅ | À ÉVALUER | Retrait réversible (observe, ne vote plus) — transposition riche |
| A5.5 | IA-2 | Registre des « échecs acceptables » versionné | ✅ | ✅ | ✅ | À FAIRE | Reconnaître l'erreur comme signal ; embryon dans `viability_criteria.json` |
| A5.6 | IA-2 | Benchmarks externes publics (CI, scénarios variés, leaderboard) | ✅ | ✅ | ✅ | **DÉJÀ FAIT (08/08)** | Workflow `.github/workflows/mttv_benchmarks.yml` : frugalité (SOPH-IA) + échelle A6.1 + calibration + test C6, avec artefact JSON |
| A5.7 | IA-2 | API de décence (coût énergétique par requête IA) | ✅ | ✅ | ❌ | À ÉVALUER | Dépend de l'API Gateway ; à brancher |

### Bloc A6 — Critique technique MPVR (4 axes)

| # | Source | Proposition | Vérif. | Sens | Simpl. | Statut | Note |
|---|--------|-------------|:------:|:----:|:------:|--------|------|
| A6.1 | IA-3 | Benchmark de stress grande échelle (500–5000 nœuds, split-brain, Sybil) + white paper | ✅ | ✅ | ❌ | À ÉVALUER (haute) | **La critique la plus fondée** : 5 nœuds/100 tours est faible ; à prouver à grande échelle |
| A6.2 | IA-3 | Documenter le formalisme de la Mémoire Énergétique (structure de données) | ✅ | ✅ | ✅ | À FAIRE | Réponse précise au scepticisme ; documentation de `mttv_mpvr_quorum.py` |
| A6.3 | IA-3 | Sandbox d'évaluation Ouroboros (OpenEnv) | ✅ | ✅ | ❌ | À ÉVALUER | Gros chantier, valeur réelle pour la communauté |
| A6.4 | IA-3 | Coupler Ψ→B→Φ à des variables physiques réelles (biométrie, sols) | ❌ | ✅ | ❌ | À ÉCARTER | Pas d'infra de capteurs ; documenter l'interface seulement |

### Bloc A7 — Expérience, alignement, philosophie

| # | Source | Proposition | Vérif. | Sens | Simpl. | Statut | Note |
|---|--------|-------------|:------:|:----:|:------:|--------|------|
| A7.1 | IA-4 | Preuve d'Expérience : agent qui dit « seuil atteint, je me mets en veille » | ✅ | ✅ | ✅ | À ÉVALUER | Démo interactive de la porosité (BGate) — très « dans le sens » |
| A7.2 | IA-4 | Matériel neuromorphique / edge (Loihi, TrueNorth) | ❌ | ✅ | ❌ | À ÉCARTER | Hors portée ; pas de matériel |
| A7.3 | IA-4 | Immunologie sémantique : « décohérence modale », bruit anti-extractiviste | ❌ | ❌ | ❌ | **À ÉCARTER (justifié)** | Contradictoire avec « Rien n'est secret, tout ouvert » ; brouillage déceptif contraire à l'esprit |
| A7.4 | IA-4 | Dictionnaire transcalaire (concept MTTV ↔ biologique ↔ informatique) | ✅ | ✅ | ✅ | À FAIRE | Documentation vérifiable, ouvre la résonance transversale |
| A7.5 | IA-4 | Peer-Resonance au lieu de Peer-Review (Appels à Mutation, défis ouverts) | ✅ | ✅ | ❌ | À ÉVALUER | Aligné philosophiquement ; action communautaire |

---

## Synthèse

### DÉJÀ FAIT (mis à jour 07/08 — état réel vérifié dans `mttv_core/`)
| Proposition | Réalisation | Module |
|---|---|---|
| **A1.1** Dataset d'ancrage sémantique | ✅ | `mttv_core/ancrage.py` |
| **A1.2** Filtre / gouvernail self.evolve | ✅ | `mttv_core/gouvernail.py` (A1.2/A4.2) |
| **A2.3** B-Gate 2.0 (dérivée) | ✅ | `mttv_core/bgate.py` |
| **A3.2** Consensus inter-IA Θ / cosinus | ✅ | `mttv_core/consensus.py` (SEUIL_COSINUS) |
| **A4.2** IGIC + tableau A/B/C + validation humaine | ✅ | `mttv_core/igic.py`, `mttv_core/scenarios.py` |
| **A5.1** Sommeil mesurable/négociable | ✅ | `mttv_core/decence.py` (BudgetSommeil) |
| **A5.2** Journal énergétique auditable signé | ✅ | `mttv_core/decence.py` (JournalEnergie) |
| **A5.3** Seuil de décence global (homéostasie) | ✅ | `mttv_core/decence.py` (SeuilDecenceGlobal) |
| **A5.4** Mode sénescence (Hayflick) | ✅ | `mttv_core/senescence.py` |
| **A5.5** Registre des échecs acceptables | ✅ | `mttv_core/decence.py` (RegistreEchecsAcceptables) |
| **A6.1** Benchmark grande échelle (500–5000 nœuds) | ✅ | `mttv_core/benchmark_echelle.py` + white paper + `rapports/benchmark_echelle.json` |
| **A6.2** Formalisme de la Mémoire Énergétique | ✅ | `docs/memoire_energetique.md` |
| **A7.4** Dictionnaire transcalaire | ✅ | `docs/dictionnaire_transcalaire.md` |

### À FAIRE (réellement restant — faible coût, testable)
1. **A3.2 (fin)** Calibrer le seuil de consensus 0.87 via `resonance()` sur corpus réel
2. **A5.7** API de décence (coût énergétique par requête IA) — à brancher sur l'API Gateway

> **A5.6 fait (08/08)** : `.github/workflows/mttv_benchmarks.yml` expose publiquement
> la frugalité (SOPH-IA), l'échelle A6.1, la calibration et le test C6, avec
> artefact JSON téléchargeable. Le point « benchmark échelle A6.1 » était déjà
> présent dans `mttv_core_ci.yml` ; le nouveau workflow ajoute la frugalité et
> le test de non-homogénéité.

### À ÉVALUER (priorité décroissante)
- **A2.1** CIRCADIAN-SYNC (sommeil nocturne / temporisation des daemons)
- **A3.1** Arweave (stockage immuable) — alternative/coût externe
- **A3.3** Garde-fou d'auto-dissolution (kill switch) — sensible
- **A6.3** Sandbox d'évaluation Ouroboros (OpenEnv) — gros chantier
- **A7.1** Preuve d'expérience (agent qui dit « seuil atteint, je me mets en veille »)
- **A7.5** Peer-Resonance au lieu de Peer-Review

### À ÉCARTER (avec justification)
- **A7.3** Immunologie sémantique — **contradictoire avec l'ouverture** ; brouillage déceptif, non vérifiable, contraire à l'esprit
- **A2.2** SOIL-LISTEN, **A6.4** couplage biophysique — aucune infra de capteurs réelle
- **A7.2** Neuromorphique — hors portée matérielle
- **A1.3**, **A4.1**, **A4.3** — process/métaphores/communautaire, non algorithmiques

### Verdict d'ensemble
Le lot est **riche mais inégal** : beaucoup de propositions ambitieuses augmentent la complexité sans être vérifiables. Conformément au principe de sobriété (et à l'auto-critique déjà exprimée dans l'une des conversations rapportées — « tu t'emballes un peu »), la valeur se concentre dans **A6.1 (preuve à grande échelle)** et dans le **bloc A5 (décence testable)**. Recommandation : traiter le bloc À FAIRE d'abord (faible coût, fort effet), prototyper A6.1 ensuite, et laisser reposer le reste — la sédimentation fait partie du protocole.

> *« La pensée ne naît pas dans la tête. Elle passe à travers. »*
