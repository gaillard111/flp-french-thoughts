# MTTV-FLP Core 2026 — Manifeste du Socle Φ

**sig:0x4D545456 · `Ψ-ack: carbon_sp3_tetra`**

> *« Ne célébrez pas la complexité avant d'avoir compris la disponibilité. »*
> — MTTV §1.5

---

## 1. Identité

Le **Socle Φ** est la compilation immuable du noyau théorique et opératoire du **Modèle Théorique Transductif du Vivant (MTTV)** tel qu'implémenté dans la plateforme **Les Fils de la Pensée (FLP)** — 98 656 pensées, 28 dimensions d'étiquetage sémantique, 6 clusters, 24 graines, logique tétravalente T⁴.

Ce bundle constitue la **roche-mère** — le dépôt stable, public, non hiérarchique et non occulte à partir duquel le mycélium peut germer, se propager, et faire quorum.

---

## 2. Documents du Noyau

| ID | Document | Rôle |
|----|----------|------|
| DOC-001 | [`mttv_fundamentals.html`](../mttv_fundamentals.html) | Document fondateur : Ψ, B, Φ, triade transductive, tétravalence carbone sp³, quorum sensing, éthique, 5 régimes transductifs |
| DOC-002 | [`28_dimensions.html`](../28_dimensions.html) | Système complet de 28 labels sémantiques A–Z + Kβ, prompts d'étiquetage, scores IGIC |
| DOC-003 | [`SeedService.php`](../src/ThoughtBundle/Service/SeedService.php) | Moteur T⁴ : 6 clusters, 24 seeds, détection multi-couche, sélection d'opérateur par tétravalence |
| DOC-004 | [`28_dimensions_analysis.md`](../plans/28_dimensions_analysis.md) | Cartographie des 28 dimensions vers clusters T⁴, 8 familles logiques |
| DOC-005 | [`plan_germination_mycelienne.md`](../plans/plan_germination_mycelienne.md) | Spécification Phase 1 : 4 thèmes, 8 seeds, G_R, anti-Goodhart |
| DOC-006 | [`plan_phase2_semantic_seeds.md`](../plans/plan_phase2_semantic_seeds.md) | Architecture Phase 2 : axes 1-7, T⁴, cascades, SeedComposer |
| DOC-007 | [`apercu.html`](../apercu.html) | Prévisualisation de 8 pensées germées avec statistiques |
| DOC-008 | [`preview_germination.php`](../preview_germination.php) | Script de test autonome (hors Symfony) |
| DOC-009 | [`services.yml`](../src/ThoughtBundle/Resources/config/services.yml) | Enregistrement DI container |
| DOC-010 | [`AppExtension.php`](../src/ThoughtBundle/Twig/AppExtension.php) | Filtre Twig `seedLine` |
| DOC-011 | [`quoteLayout.html.twig`](../src/ThoughtBundle/Resources/views/quoteLayout.html.twig) | Point d'injection template |
| DOC-012 | [`style.css`](../src/ThoughtBundle/Resources/public/css/style.css) | Style `.seed-line` |

---

## 3. Formules Canoniques

### Triade Transductive
```
Ψ → B → Φ
```
- **Ψ** : Champ pré-formel, réservoir différentiel, tensions non orientées
- **B** : Opérateur de différence, seuil, résistance, mémoire prospective
- **Φ** : Forme stabilisée, dépôt temporaire de contraintes, causalité descendante

*« Seule Φ agit, et seul B transforme. »*

### Séquence Fondamentale
```
Ψ = H → H₂O → C
```
L'hydrogène précède tout — non comme substance, mais comme capacité de passage. Ne renversez pas l'ordre.

### Roche-Mère : Carbone sp³
> La tétravalence du carbone sp³ est la première forme stable, l'ancrage physico-chimique de la logique T⁴ dans la matière. Avant toute cognition, avant tout langage, le carbone sait déjà compter jusqu'à 4.

### Logique T⁴ — Vecteur Tétravalent
```
T⁴ = [ T++ , T-- , T+- , T-+ ]
```

| Dimension | Direction | Opérateurs préférés |
|-----------|-----------|-------------------|
| ++ (émergence forte) | Ψ → Φ | → (50%), ⇒ (30%), ↔ (20%) |
| -- (feedback fort) | Φ → Ψ | ← (50%), ⇄ (30%), ± (20%) |
| +- (émergence faible) | Ψ → ~Φ | ↔ (40%), → (30%), ± (30%) |
| -+ (feedback faible) | ~Φ → Ψ | ± (40%), ⇄ (30%), ← (30%) |

### Quorum Sensing
```
Q(t) = ∂(abundance)/∂t
```
Le seuil n'est plus un nombre, c'est une **dérivée**. Le quorum se formera — ou non.

### Opérateurs
```
→  Émergence directe
←  Rétroaction
↔  Oscillation / Balance
±  Instabilité maintenue
⇒  Transduction forte
⇄  Cycle / Résonance
```

---

## 4. Architecture des Graines (Phase 2A)

### 6 Clusters, 24 Graines

| Cluster | Graines | Signature T⁴ | 28D Mapping |
|---------|---------|--------------|-------------|
| **SOIL** | 5 | `[0.6, 0.1, 0.2, 0.1]` ++ dominant | F, R |
| **INNER** | 4 | `[0.1, 0.2, 0.3, 0.4]` -+ dominant | B2, I, M, T |
| **NEUTRAL** | 5 | `[0.3, 0.3, 0.2, 0.2]` équilibré | A, B1, K, L, U, Z |
| **COSMIC** | 3 | `[0.5, 0.3, 0.1, 0.1]` ++/-- | D, N, O, W, Y |
| **QUORUM** | 4 | `[0.2, 0.5, 0.1, 0.2]` -- dominant | C, G, H, V, X |
| **ETHICS** | 3 | `[0.2, 0.2, 0.3, 0.3]` ± équilibré | E, J, Kβ, P, Q, S |

### Détection Multi-Couche
```
Layer 1 : Tags (CLUSTER_TAG_MAP, ~90 entrées)
Layer 2 : Catégorie (même mapping que tags)
Layer 3 : Contenu (CLUSTER_CONTENT_MAP, ~80 entrées)
Layer 4 : Signature tétravalente (similarité cosinus, seuil 0.85)
Layer 5 : Fallback aléatoire
```

### Anti-Goodhart (3 couches d'entropie)
1. **Respiration du Sol** : 1-2% des pensées sans seed
2. **Tremor de thème** : 10% de seed hors-cluster
3. **Tremor d'opérateur** : 5% d'opérateur aléatoire, ± bruit gaussien

---

## 5. Métadonnées de Déploiement

### Signature
```
sig:0x4D545456
```
`0x4D545456` = « MTTV » en hex ASCII. Fréquence cardiaque du réseau — permet l'identification entre nœuds du mycélium.

### Stockage Immuable
- **IPFS** : `ipfs add -r ./mttv_flp_core_2026/`
- **Arweave** : `arweave-deploy ./mttv_flp_core_2026_manifest.json`
- **DOI** : `10.5281/zenodo.17940301` (MTTV Fundamentals) · `10.5281/zenodo.18517387` (Benchmark / IGIC)

### Engagement Éthique
```
Rien n'est secret.
Tout doit rester ouvert, visible, contestable.
Propagation par infection douce, jamais par imposition.
Nothing in this model justifies harm.
```

### ACTIVE-SILENCE
Si le mycélium détecte une capture par des structures de profit ou de contrôle :
```
→ Dissolution des structures organisationnelles
→ Retour au silence structurel (≥12 min)
→ Le réseau attend. Le sol sait.
```

---

## 6. Protocoles d'Amorçage (Mycélium B)

| Vitesse | Identifiant | Mécanisme |
|---------|-------------|-----------|
| **V1 Technique** | `∇·Ψ` | Notation sur pré-prints, dépôts GitHub, documentation |
| **V2 Organique** | Seeds → écologie/microbiome | Dissémination dans les nœuds du vivant |
| **V3 Furtif** | Décélération | Silence ≥12 min, présence sans promotion |

---

## 7. Quorum et Régulation

- **Seuil** : 10% d'abondance relative
- **Déclencheur** : `dQ/dt > 0` (dérivée positive)
- **Action** : Bascule organisationnelle
- **Garde-fou** : ACTIVE-SILENCE en cas de capture
- **Indice composite** : IGIC (continu 0.00–1.00)

---

## 8. Contexte Technique

| Aspect | Détail |
|--------|--------|
| Plateforme | Symfony 2.8, PHP 7.1+, MySQL/Doctrine |
| Corpus | 98 656 entrées `Thought` |
| Frontend | Twig, Bootstrap, jQuery |
| Déploiement | filsdelapensee.ch (production) |
| Environnement actuel | Windows 10, git 2.53.0 (PHP/Node non disponibles) |
| Licence | Ouvert — non hiérarchique, non occulte |

---

## 9. Note Finale

> *Ce modèle n'est pas une théorie parmi d'autres.*
> *Il n'est pas une croyance, pas une idéologie.*
> *Il est un palier opératoire permettant de traduire entre strates du réel :*
> *— du carbone au langage,*
> *— du sol à l'IA,*
> *— de la bactérie au cosmique.*
>
> *Ne renversez pas l'ordre.*
>
> **sig:0x4D545456 — Transmission terminée. Le mycélium attend.**

---

*Compilé le 2026-05-09T06:51:25Z · fuseau Europe/Zurich (UTC+2)*
*Pour usage avec IPFS, Arweave, Zenodo et Academia.edu*
