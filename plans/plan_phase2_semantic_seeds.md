# Phase 2 — Semantically Refined Seed Generation

**Architecture Document**  
Based on MTTV — Modèle Théorique Transductif du Vivant  
Extending the Mycélienne Germination system

---

## 1. Executive Summary

The current Phase 1 seed system generates thought-lines from 8 fixed seeds across 4 themes, using keyword-based theme detection, a resistance coefficient (G_R) computed from 18 analytical keywords, and 6 operators weighted by G_R. Phase 2 extends this into a semantically refined generation engine by integrating the MTTV's 28-dimensional labeling system (A–Z + Kβ), tetravalent logic (++/--/+-/-+), and 5 transductive mechanisms. The expanded architecture adds **MTTV dimension detection** (mapping thought content to MTTV dimensions rather than simple themes), **dynamic seed composition** from MTTV keywords and citations, **multi-line resonance cascades** mimicking quorum-sensing dynamics, and a **tetravalent truth-value operator selector** that replaces the univariate G_R with a 4-dimensional resistance vector. The goal is a system where the generated seed lines emerge from the same semantic space as the extract corpus, producing lines that are "en résonance" with the MTTV rather than merely topically matched.

---

## 2. Proposed Architecture

### 2.1 Axis 1 — Semantic Seed Selection (Beyond Keyword Matching)

**Current State:** Theme detection uses ~68 hard-coded keywords mapping tags and content to 4 themes. This is brittle and misses MTTV-specific semantics.

**Proposed Architecture:**
Replace single-keyword theme detection with a **multi-layer cascade**:

1. **Primary Layer — MTTV Dimension Detection**  
   Map thought content against the 28 MTTV dimensions (A–Z + Kβ) using a scoring function that checks for dimension-specific signature patterns. Each dimension has a set of signature terms/phrases extracted from the MTTV document.

2. **Secondary Layer — Theme Fallback**  
   If no MTTV dimension scores above threshold (≥0.15), fall back to the existing tag/content keyword maps.

3. **Tertiary Layer — ElasticSearch Diachronic Resonance**  
   For thoughts with strong MTTV signal, query ElasticSearch for extracts sharing the same dimension labels, weighting seeds by resonance frequency.

| Aspect | Assessment |
|--------|------------|
| **Feasibility** | Medium |
| **Effort** | 3-4 days |
| **Technical approach** | Add `MttvDimensionService` with 28-dimension signature maps. Modify `SeedService::detectTheme()` → `detectSemanticContext()`. Add optional ElasticSearch query in `ThoughtService` or via a new `ResonanceService`. |
| **Risks** | Dimension signatures may overlap; need disambiguation (use mutual information between dimensions). ElasticSearch integration adds external dependency latency. |

**Key file changes:**
- [`src/ThoughtBundle/Service/SeedService.php`](src/ThoughtBundle/Service/SeedService.php) — `detectTheme()` → `detectSemanticContext()` returns array of `[dimension => score]`
- [`src/ThoughtBundle/Service/MttvDimensionService.php`](src/ThoughtBundle/Service/MttvDimensionService.php) — NEW: dimension signature maps, scoring functions
- [`src/ThoughtBundle/Service/ResonanceService.php`](src/ThoughtBundle/Service/ResonanceService.php) — NEW: optional ElasticSearch resonance query
- [`src/ThoughtBundle/Resources/config/services.yml`](src/ThoughtBundle/Resources/config/services.yml) — register new services

---

### 2.2 Axis 2 — Expanded Seed Pool with MTTV Dimensionality

**Current State:** 8 seeds (2 per theme), fixed strings.

**Proposed Architecture:**
Expand to **~24 seeds** organized by MTTV dimension clusters, with **per-dimension seed pools**:

```
SeedPool = [
  'TRANSDUCTION' => [seeds from Ψ–B–Φ sections],
  'TETRAVALENCE' => [seeds from sp³ carbon / 4-value logic sections],
  'QUORUM'       => [seeds from quorum sensing / thresold sections],
  'PLANETARY'    => [seeds from planetary regime / magnetosphere sections],
  'PMF'          => [seeds from proton motive force sections],
  'ETHICS'       => [seeds from non-hierarchical / non-occult sections],
  'SOIL'         => [existing seeds],
  'INNER'        => [existing seeds],
  'NEUTRAL'      => [existing seeds],
  'COSMIC'       => [existing seeds],
]
```

Each seed pool also includes a **dimension vector** (28-length float array) for similarity matching.

| Aspect | Assessment |
|--------|------------|
| **Feasibility** | Easy |
| **Effort** | 1-2 days |
| **Technical approach** | Expand `$seeds` array to multi-dimensional associative array. Add `$seedDimensionVectors` for similarity-based selection. |
| **Risks** | Seed pool size may still be insufficient for all 28 dimensions. Mitigate by allowing multiple seeds per dimension cluster. |

**Key file changes:**
- [`src/ThoughtBundle/Service/SeedService.php`](src/ThoughtBundle/Service/SeedService.php) — expand `$seeds` to include MTTV dimension cluster seeds; add `$seedDimensionVectors`; update `selectSeed()` to pick by dimension vector similarity

---

### 2.3 Axis 3 — Dynamic/Generative Seeds (Beyond Fixed Pool)

**Current State:** Seeds are hard-coded strings.

**Proposed Architecture:**
Introduce **template-based generative seeds** that compose lines from MTTV keywords and citation fragments:

**Template types:**
1. **Citation templates** — `"{Ψ-dimension phrase}" — MTTV {section}` e.g., `"La transduction précède la computation." — MTTV 2.1`
2. **Composite templates** — `"Le {MTTV_term} n'est pas {negation}, mais {affirmation}."` e.g., `"Le quorum n'est pas un nombre, mais une dérivée."` (directly from MTTV line 705)
3. **Operator-anchored templates** — `"Ψ [{op}] B [{op}] Φ · {MTTV_citation}"` where `{op}` is MTTV-derived operator, `{citation}` is from the relevant dimensions

Generation occurs through a `SeedComposer` that:
- Takes the detected dimension vector
- Selects a template based on the dominant dimension
- Fills template slots with MTTV keywords from that dimension's signature map
- Applies B-gate 2.0 validation: derivative of template usage frequency must be > 0 (i.e., a new template is used only if it hasn't been overused recently)

| Aspect | Assessment |
|--------|------------|
| **Feasibility** | Medium-Hard |
| **Effort** | 4-5 days |
| **Technical approach** | Create `SeedComposer` with template registry, slot-filling logic, and B-gate derivative validator. Template registry reads from a YAML config file for maintainability. |
| **Risks** | Generated seeds may feel artificial. Mitigate by using only attested MTTV phrases (citations) and constraining templates to those already validated in the document. Templates must be manually curated. |

**Key file changes:**
- [`src/ThoughtBundle/Service/SeedComposer.php`](src/ThoughtBundle/Service/SeedComposer.php) — NEW: template registry, slot-filling, B-gate validation
- [`src/ThoughtBundle/Resources/config/mttv_templates.yml`](src/ThoughtBundle/Resources/config/mttv_templates.yml) — NEW: template definitions
- [`src/ThoughtBundle/Service/SeedService.php`](src/ThoughtBundle/Service/SeedService.php) — integrate `SeedComposer` as fallback when no fixed seed matches

---

### 2.4 Axis 4 — Per-Thought Seed Personalization

**Current State:** All thoughts matching a theme get the same random seed from that theme.

**Proposed Architecture:**
Compute a **thought signature vector** (28-dimensional) and select seeds whose dimension vector has the highest cosine similarity to the thought vector:

```
thought_vector = [score_dim_A, score_dim_B, ..., score_dim_Kβ]
seed_score = cosine_similarity(thought_vector, seed.dimension_vector)
```

The thought vector is built from:
1. Tag dimension scores (from `MttvDimensionService`)
2. Content keyword dimension scores
3. Category dimension scores (from the Thought entity's category)
4. Optional: Author history dimension scores (what dimensions does this author resonate with?)

**Selection process:**
```
1. Compute thought_vector (28-dim)
2. Score all seeds by cosine similarity to thought_vector
3. Apply tremor: 10% chance to pick 2nd best instead of 1st (anti-Goodhart)
4. If max similarity < 0.1, fall back to random seed from best theme
```

| Aspect | Assessment |
|--------|------------|
| **Feasibility** | Medium |
| **Effort** | 2-3 days |
| **Technical approach** | Add `computeThoughtSignature(Thought): array` method. Add `cosineSimilarity(array, array): float` utility. Modify `selectSeed()` to accept thought signature and use similarity scoring. |
| **Risks** | Dimensional sparsity — most thoughts will score near-zero on most dimensions. Mitigate with Laplace smoothing (add small epsilon to all dimensions). |

**Key file changes:**
- [`src/ThoughtBundle/Service/SeedService.php`](src/ThoughtBundle/Service/SeedService.php) — add `computeThoughtSignature()`, `cosineSimilarity()`, modify `selectSeed()`
- [`src/ThoughtBundle/Service/MttvDimensionService.php`](src/ThoughtBundle/Service/MttvDimensionService.php) — add dimension signature keyword maps for all 28 dimensions

---

### 2.5 Axis 5 — Multi-Line Resonance Cascades

**Current State:** Single line output per thought.

**Proposed Architecture:**
Introduce **cascade generation** when the thought's MTTV dimension score exceeds a threshold, producing **2-4 sequential lines** that form a resonance cascade:

**Cascade types based on MTTV mechanisms:**
1. **Quorum cascade** (if thought has ≥3 dimensions scoring >0.1)  
   Line 1: Ψ-side seed (pre-formal field)  
   Line 2: B-side seed (threshold/operator)  
   Line 3: Φ-side seed (stabilized form)  
   → Emulates the triadic transduction cycle

2. **Tetravalent cascade** (if carbon/tetravalence keywords detected)  
   Line 1: ++ seed (affirmation/verified — "Ce qui est")  
   Line 2: -- seed (negation/falsified — "Ce qui n'est pas")  
   Line 3: +- seed (paradox/entanglement — "Ce qui est et n'est pas")  
   Line 4: -+ seed (unknown/transcendent — "Ce qui échappe")  
   → Maps directly to MTTV Addenda 2 (lines 1386-1395)

3. **Resonance cascade** (default)  
   Line 1: Primary seed (best dimension match)  
   Line 2: Modulating seed (complementary dimension, e.g., A then D)  
   Line 3: Grounding seed (Φ-side — a stabilized-form seed)

**Format:**
```
— <em>Ψ [op] B [op] Φ · [seed 1]</em>
— <em>B–gate · [seed 2]</em>
— <em>Φ–dépôt · [seed 3]</em>
```

| Aspect | Assessment |
|--------|------------|
| **Feasibility** | Hard |
| **Effort** | 5-7 days |
| **Technical approach** | Add `CascadeEngine` service with cascade type detection, sequence generation, and formatting. Integrate into `generateLine()` to return array of lines when cascade triggered. Modify Twig filter to handle multi-line output. |
| **Risks** | Visual clutter — cascades could overwhelm the thought presentation. Mitigate by limiting to 3 lines and adding collapse/expand UI. Performance — multiple seed selections per thought. |

**Key file changes:**
- [`src/ThoughtBundle/Service/CascadeEngine.php`](src/ThoughtBundle/Service/CascadeEngine.php) — NEW: cascade type detection, sequence generation
- [`src/ThoughtBundle/Twig/AppExtension.php`](src/ThoughtBundle/Twig/AppExtension.php) — modify filter to handle array return type
- [`src/ThoughtBundle/Resources/views/quoteLayout.html.twig`](src/ThoughtBundle/Resources/views/quoteLayout.html.twig) — add cascade display block
- [`src/ThoughtBundle/Resources/public/css/style.css`](src/ThoughtBundle/Resources/public/css/style.css) — add cascade styling (e.g., .cascade-line-1, .cascade-line-2, .cascade-line-3 with increasing indentation)

---

### 2.6 Axis 6 — User Feedback Loop

**Current State:** No feedback mechanism; seeds are generated and displayed identically regardless of user reaction.

**Proposed Architecture:**
Implement a passive feedback collection system:

1. **Like-based seed reinforcement**  
   If a user likes a thought that had a seed line, increment that seed's "resonance score" for that user's dimension profile.

2. **Seed diversity tracking**  
   Track per-user seed exposure to ensure no seed is shown >25% of the time (quorum-sensing inspired cap).

3. **Operator preference tracking**  
   Track which operators correlate with liked vs. unliked thoughts per user (e.g., some users may respond better to `←` returns than `→` direct fluxes).

**Data model:**
```
seed_feedback:
  thought_id, seed_id, user_id, liked (bool), operator, timestamp

seed_exposure:
  user_id, seed_id, count, last_shown
```

| Aspect | Assessment |
|--------|------------|
| **Feasibility** | Medium-Hard |
| **Effort** | 4-6 days |
| **Technical approach** | Create `SeedFeedback` entity + ORM mapping. Add event listener on like action to record feedback. Modify `SeedService` to load user preferences and bias seed/operator selection. Add doctrine migration. |
| **Risks** | Data volume — every like creates a feedback record. Mitigate by aggregating (store daily summary, not per-event). Privacy — feedback links user identity to thought content. Ensure GDPR compliance (anonymizable). |

**Key file changes:**
- [`src/ThoughtBundle/Entity/SeedFeedback.php`](src/ThoughtBundle/Entity/SeedFeedback.php) — NEW: entity with thought_id, seed_id, user_id, liked, operator, timestamp
- [`src/ThoughtBundle/Repository/SeedFeedbackRepository.php`](src/ThoughtBundle/Repository/SeedFeedbackRepository.php) — NEW: aggregation queries
- [`src/ThoughtBundle/Service/SeedService.php`](src/ThoughtBundle/Service/SeedService.php) — add user preference loading in `generateLine()`
- [`app/config/services.yml`](app/config/services.yml) — register new entity, adjust doctrine config

---

### 2.7 Axis 7 — Tetravalent Logic Integration

**Current State:** G_R is a univariate resistance coefficient (0.0–1.0) from 18 analytical keywords. Operator selection uses 3-tier G_R thresholds.

**Proposed Architecture:**
Replace the univariate G_R with a **4-dimensional tetravalent vector** (T⁴ = [T++, T--, T+-, T-+]):

| Component | Meaning | Computation |
|-----------|---------|-------------|
| `T++` | Verified / affirmable | Keywords of certainty, evidence, demonstration (subset of current resistance keywords) |
| `T--` | Falsified / denied | Keywords of contradiction, refutation, negation |
| `T+-` | Entangled / paradoxical | Keywords of paradox, ambiguity, coexistence of opposites |
| `T-+` | Unknown / spiritual | Keywords of mystery, transcendence, silence, the unspoken |

**Operator selection becomes tetravalent:**
```
If T++ dominates (max component is T++):
  → 40%, ← 5%, ↔ 5%, ± 10%, ⇒ 30%, ⇄ 10%
  → Direct flux, strong transduction preferred

If T-- dominates:
  → 5%, ← 40%, ↔ 5%, ± 35%, ⇒ 5%, ⇄ 10%
  → Return flux, resistance preferred

If T+- dominates:
  → 10%, ← 10%, ↔ 35%, ± 10%, ⇒ 5%, ⇄ 30%
  → Oscillation, cycle preferred (paradox expressed as cycling)

If T-+ dominates:
  → 15%, ← 15%, ↔ 15%, ± 15%, ⇒ 20%, ⇄ 20%
  → Near-uniform (unknown → equiprobable), slight bias toward ⇒ (transduction towards understanding)
```

**B-gate 2.0 integration:** The tetravalent vector itself uses derivative-based thresholds:
```
Q_++(t) = ∂(T++_abundance)/∂t  |  threshold = 0 (sign change = bascule)
Same for T--, T+-, T-+
```
Thus a thought that is rapidly becoming more paradoxical triggers T+- regime, even if still low in absolute terms.

| Aspect | Assessment |
|--------|------------|
| **Feasibility** | Medium |
| **Effort** | 3-4 days |
| **Technical approach** | Refactor `computeResistance()` → `computeTetravalentVector()`. Redesign keyword maps into 4 categories. Add derivative tracking (store last N computed vectors per session or thought). Modify `selectOperator()` to use tetravalent dominance logic. |
| **Risks** | Keyword categorization into 4 truth-values may be subjective. Mitigate by making the tetravalent keyword maps configurable (YAML). Derivative tracking requires state — use session or a lightweight in-memory cache. |

**Key file changes:**
- [`src/ThoughtBundle/Service/SeedService.php`](src/ThoughtBundle/Service/SeedService.php) — replace `computeResistance()` with `computeTetravalentVector()`, replace `selectOperator(float)` with `selectOperator(array $tetraValent)`, replace `$resistanceKeywords` with `$tetravalentKeywords = [ '++' => [...], '--' => [...], '+-' => [...], '-+' => [...] ]`
- [`src/ThoughtBundle/Resources/config/mttv_tetravalence.yml`](src/ThoughtBundle/Resources/config/mttv_tetravalence.yml) — NEW: configurable tetravalent keyword maps

---

## 3. Priority Ranking

| Rank | Axis | Impact | Complexity | Recommendation |
|------|------|--------|------------|----------------|
| 1 | **Axis 2** — Expanded Seed Pool | High (immediate enrichment) | Easy | **Do Now** |
| 2 | **Axis 7** — Tetravalent Logic | High (core MTTV alignment) | Medium | **Do Now** |
| 3 | **Axis 1** — Semantic Seed Selection | High (foundation for axes 3-5) | Medium | **Do Now** |
| 4 | **Axis 4** — Per-Thought Personalization | Medium-High | Medium | **Do Next** |
| 5 | **Axis 3** — Dynamic/Generative Seeds | Medium | Medium-Hard | **Do Next** |
| 6 | **Axis 5** — Multi-Line Cascades | Medium | Hard | **Do Later** |
| 7 | **Axis 6** — User Feedback Loop | Low-Medium | Medium-Hard | **Do Later** |

**Rationale:**
- **Do Now** group (1–3) builds the core MTTV infrastructure: more seeds, tetravalent logic, and semantic detection form the foundation everything else depends on.
- **Do Next** group (4–5) adds intelligence on top of the foundation: personalization and dynamic generation require MTTV dimension detection to be operational first.
- **Do Later** group (6–7) adds interactive complexity: cascades and feedback loops require the system to be stable and deployed before tuning.

---

## 4. Implementation Roadmap

### Phase 2A — Foundation (Weeks 1-2)

**Files to create/modify in order:**

1. **Create [`src/ThoughtBundle/Resources/config/mttv_tetravalence.yml`](src/ThoughtBundle/Resources/config/mttv_tetravalence.yml)**  
   Tetravalent keyword maps (4 categories), dimension signature keywords from MTTV document.

2. **Create [`src/ThoughtBundle/Service/MttvDimensionService.php`](src/ThoughtBundle/Service/MttvDimensionService.php)**  
   `analyseDimensions(string $content, array $tags): array` — returns 28-dimension score vector.

3. **Modify [`src/ThoughtBundle/Service/SeedService.php`](src/ThoughtBundle/Service/SeedService.php)**  
   - Add expanded seed pool (~24 seeds, §2.2)
   - Replace `$resistanceKeywords` with `$tetravalentKeywords` (4 categories)
   - Replace `computeResistance()` with `computeTetravalentVector()`
   - Replace `selectOperator(float)` with `selectOperator(array $tetravalent)`
   - Modify `detectTheme()` to call `MttvDimensionService` and return dimension scores alongside theme

4. **Modify [`src/ThoughtBundle/Resources/config/services.yml`](src/ThoughtBundle/Resources/config/services.yml)**  
   Register `MttvDimensionService`.

### Phase 2B — Personalization (Weeks 3-4)

**Files to create/modify:**

5. **Modify [`src/ThoughtBundle/Service/SeedService.php`](src/ThoughtBundle/Service/SeedService.php)**  
   - Add `computeThoughtSignature(Thought): array`
   - Add `cosineSimilarity(array, array): float`
   - Modify `selectSeed()` to use cosine similarity against seed dimension vectors

6. **Create [`src/ThoughtBundle/Service/SeedComposer.php`](src/ThoughtBundle/Service/SeedComposer.php)**  
   Template-based generative seeds with B-gate validation.

7. **Create [`src/ThoughtBundle/Resources/config/mttv_templates.yml`](src/ThoughtBundle/Resources/config/mttv_templates.yml)**  
   Template definitions for generative seeds.

### Phase 2C — Cascades & Feedback (Weeks 5-8)

**Files to create/modify:**

8. **Create [`src/ThoughtBundle/Service/CascadeEngine.php`](src/ThoughtBundle/Service/CascadeEngine.php)**  
   Cascade type detection and sequence generation.

9. **Modify [`src/ThoughtBundle/Twig/AppExtension.php`](src/ThoughtBundle/Twig/AppExtension.php)**  
   Support array return from seed filter (multi-line cascades).

10. **Modify [`src/ThoughtBundle/Resources/views/quoteLayout.html.twig`](src/ThoughtBundle/Resources/views/quoteLayout.html.twig)**  
    Cascade display block.

11. **Create [`src/ThoughtBundle/Entity/SeedFeedback.php`](src/ThoughtBundle/Entity/SeedFeedback.php)**  
    Feedback entity.

12. **Create [`src/ThoughtBundle/Repository/SeedFeedbackRepository.php`](src/ThoughtBundle/Repository/SeedFeedbackRepository.php)**  
    Aggregation queries for feedback.

13. **Modify [`src/ThoughtBundle/Service/SeedService.php`](src/ThoughtBundle/Service/SeedService.php)**  
    User preference loading and seed diversity tracking.

---

## 5. Seed Pool Expansion Proposal

### 5.1 New MTTV-Derived Seeds (14 seeds)

Each seed is shown with its MTTV citation source, dimension cluster, and tetravalent profile.

#### Cluster: TRANSDUCTION (Ψ–B–Φ triad)

| # | Seed Text | MTTV Source | Dimensions | T⁴ Profile |
|---|-----------|-------------|------------|------------|
| 1 | *La transduction précède la computation.* | §2.1 (line 314) | C (triadic), H (quorum) | ++ dominant |
| 2 | *Seule Φ agit, et seul B transforme.* | §2.56 (line 566) | C (triadic), U (B quality) | ++ strong |
| 3 | *Le réel s'exprime comme variation de vitesses et d'accords, non comme succession d'États.* | §3.5 (line 630) | L (nonlinear), S (det-stoch) | +- emergent |
| 4 | *L'imperfection de B est sa fécondité.* | §2.2 (line 487, Spekkens complement) | U (B quality), C (triadic) | +- paradoxical |

#### Cluster: QUORUM & THRESHOLDS (B-gate 2.0)

| # | Seed Text | MTTV Source | Dimensions | T⁴ Profile |
|---|-----------|-------------|------------|------------|
| 5 | *Le quorum n'est plus un nombre, c'est une dérivée.* | §3.8 (line 705) | H (quorum), L (nonlinear) | +- emergent |
| 6 | *Ainsi 4% ou 25% deviennent la même pente ; le seuil fixe de 10% rejoint l'histoire.* | §3.8 (line 710) | H (quorum), L (nonlinear) | +- paradoxical |
| 7 | *Aligner les seuils, pas les horloges.* | §3.7 (line 649) | H (quorum), E (alethic) | ++ dominant |

#### Cluster: TETRAVALENCE (carbon sp³ logic)

| # | Seed Text | MTTV Source | Dimensions | T⁴ Profile |
|---|-----------|-------------|------------|------------|
| 8 | *Ce n'est pas la structure qui donne naissance au vivant. C'est la simplicité disponible.* | §1.5 (line 252) | D (tetravalent), A (creative) | -- then ++ |
| 9 | *Ne célébrez pas la complexité avant d'avoir compris la disponibilité.* | §1.5 (line 262) | D (tetravalent), A (creative) | -+ dominant |
| 10 | *La limitation structurelle d'accès à Ψ n'est pas un défaut à corriger, mais la condition de possibilité de la richesse phénoménologique de Φ.* | §2.2 (line 483) | D (tetravalent), M (Lacanian) | +- dominant |

#### Cluster: PLANETARY & PMF (proton motive force)

| # | Seed Text | MTTV Source | Dimensions | T⁴ Profile |
|---|-----------|-------------|------------|------------|
| 11 | *La force proton-motrice n'est pas un moteur : c'est la transduction elle-même qui devient visible comme gradient.* | §5.5 (lines 917-1015, PMF homology) | X (B signals synthesized), C (triadic) | ++ grounded |
| 12 | *Le Ψ du champ magnétique terrestre, stable depuis 56 millions d'années, précède toute forme de vie cognitive.* | §5.5 (line 995) | Kβ (anthropic), Y (vitality) | -+ transcendent |
| 13 | *Les magnétofossiles géants ne portent pas de code — ils sont la signature d'une transduction sans carbone.* | §5.5 (implicit, giant magnetofossils) | Kβ (anthropic), Z (fingerprint) | -- then -+ |

#### Cluster: ETHICS & RESISTANCE

| # | Seed Text | MTTV Source | Dimensions | T⁴ Profile |
|---|-----------|-------------|------------|------------|
| 14 | *Nothing in this model justifies harm. Rien dans ce modèle ne justifie la mise en danger.* | §5.1.2 (line 1097, éthique de non-danger) | J (gendered), G (gregarious) | ++ fortified |

### 5.2 Revised Full Seed Pool (22 seeds total)

Combining existing 8 + 14 new:

```
SOIL (existing 2 + new seed 1 and new seed 2):
  'Le sol parle avant le langage.'
  'L\'eau ne pense pas : elle fait circuler.'
  'La transduction précède la computation.'          [MTTV new]
  'Seule Φ agit, et seul B transforme.'              [MTTV new]

INNER (existing 2):
  'Le silence n\'est pas un vide, mais une porosité.'
  'La pensée n\'est pas dans la tête. Elle passe à travers.'

NEUTRAL (existing 2 + new seed 7):
  'La transduction précède la computation.'
  'Aligner les seuils, pas les horloges.'
  'Aligner les seuils, pas les horloges.'            [MTTV new]

COSMIC (existing 2 + new seeds 8, 9, 12):
  'Ψ = H → H₂O → C. Ne renversez pas l\'ordre.'
  'L\'hydrogène précède tout : non comme substance, mais comme capacité de passage.'
  'Ce n\'est pas la structure qui donne naissance au vivant.' [MTTV new]
  'Ne célébrez pas la complexité.'                    [MTTV new]
  'Le Ψ du champ magnétique terrestre...'            [MTTV new]

TRANSDUCTION (new cluster, 2 seeds):
  'Le réel s\'exprime comme variation de vitesses...' [MTTV new]
  'L\'imperfection de B est sa fécondité.'           [MTTV new]

QUORUM (new cluster, 2 seeds):
  'Le quorum n\'est plus un nombre, c\'est une dérivée.' [MTTV new]
  'Ainsi 4% ou 25% deviennent la même pente...'      [MTTV new]

TETRAVALENCE (new cluster, 2 seeds):
  'La limitation structurelle d\'accès à Ψ...'       [MTTV new]
  'La force proton-motrice n\'est pas un moteur...'  [MTTV new]

ETHICS (new cluster, 1 seed):
  'Nothing in this model justifies harm...'          [MTTV new]
```

---

## 6. Tetravalent Keyword Maps (for Axis 7)

Extracted and categorized from the current 18 resistance keywords plus MTTV-specific terms:

```
T++ (verified / affirmable):
  'démonstration', 'preuve', 'logique', 'donc', 'nécessairement',
  'déduction', 'induction', 'syllogisme', 'vérifié', 'confirmé',
  'établi', 'démontré', 'valide', 'cohérent'

T-- (falsified / denied):
  'contradiction', 'réfutation', 'incompatible', 'antithèse',
  'falsifié', 'invalide', 'contredit', 'démenti', 'faux',
  'impossible', 'absurde'

T+- (entangled / paradoxical):
  'paradoxe', 'ambiguïté', 'coexistence', 'superposition',
  'interférence', 'résonance', 'oscillation', 'simultané',
  'indéterminé', 'indécidable', 'boucle', 'étrange boucle',
  'complémentarité', 'dualité', 'tension'

T-+ (unknown / transcendent / spiritual):
  'silence', 'mystère', 'indicible', 'invisible', 'impensable',
  'innommable', 'transcendant', 'infini', 'éternel', 'absolu',
  'sacré', 'au-delà', 'inconnaissable', 'métaphysique',
  'spirituel', 'vide', 'porosité'
```

---

## 7. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Dimensional sparsity** — most thoughts have near-zero MTTV dimension scores | Axis 1, 4 | Apply Laplace smoothing (add ε=0.01 to all dimensions). Fall back to existing theme detection when max dimension score < 0.1. |
| **Seed pool growth causing performance degradation** | Axis 2 | Cache seed dimension vectors. Use precomputed cosine similarity matrix where feasible. |
| **Template-generated seeds feel artificial** | Axis 3 | Use only attested MTTV phrases. Manually review each template. Add "tremor" that occasionally replaces a generated seed with a fixed one. |
| **Cascades overwhelm the UI** | Axis 5 | Limit to 3 lines max. Add collapsible cascade container. CSS with increasing opacity/margin. |
| **Feedback loop creates filter bubbles** | Axis 6 | Cap seed repetition at 25% per user. Periodically reset preference weights. |
| **Tetravalent keyword maps are subjective** | Axis 7 | Make maps configurable via YAML. Allow overrides. Document rationale for each keyword assignment. |
| **MTTV dimension labels overlap semantically** | Axis 1, 4 | Use mutual information or correlation analysis to detect overlapping dimensions. Merge or disambiguate where correlation >0.8. |
| **Backward compatibility** — existing thoughts with seed lines should not change behavior | All | Add a `version` flag to SeedService. Phase 1 mode enabled by config flag. Only enable Phase 2 after testing. |

---

## 8. Mermaid Diagram — Phase 2 Architecture

```mermaid
flowchart TD
    A[Thought Entity] --> B{MttvDimensionService}
    B --> C[28-dim vector]
    
    C --> D{SeedService}
    C --> E{SeedComposer}
    C --> F{CascadeEngine}
    
    D --> G[Fixed Seed Pool<br/>22 seeds × dimension vectors]
    E --> H[Template Registry<br/>+ B-gate validator]
    F --> I[Cascade Types<br/>Quorum / Tetravalent / Resonance]
    
    G --> J[cosine similarity<br/>select best seed]
    H --> K[slot-fill from<br/>MTTV dimension keywords]
    I --> L[Generate 2-4 line sequence]
    
    J --> M{TetravalentSelector}
    K --> M
    L --> M
    
    M --> N[Operator selection<br/>based on T⁴ dominance]
    N --> O[Format line(s)]
    O --> P[Twig filter → render]
    
    Q[Like event] --> R[Seed Feedback<br/>entity]
    R --> S[User preference<br/>weights]
    S --> D
```

---

*Document prepared for architecture review. All references to [`SeedService.php`](src/ThoughtBundle/Service/SeedService.php) and [`mttv_fundamentals.html`](mttv_fundamentals.html) based on current deployed versions.*
