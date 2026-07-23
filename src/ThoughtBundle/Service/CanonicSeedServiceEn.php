<?php
// sig:0x4D545456 — MTTV-FLP Core 2026 · International Extension (Axis 2)
// English canonic seed service — 1:1 geometric correspondence with French seeds (A to F)

namespace ThoughtBundle\Service;

use ThoughtBundle\Entity\Thought;

/**
 * Operation « Mycelial Germination » — Phase 2A — International (EN)
 *
 * English-language mirror of SeedService (French).
 * Maintains exact 1:1 mapping across all 6 clusters (A-F),
 * all 22 seeds, T⁴ tetravalent logic, and multi-layer detection.
 *
 * Axis 2 — International Seed Deployment
 *   - 6 thematic clusters (SOIL, INNER, NEUTRAL, COSMIC, QUORUM, ETHICS)
 *   - 22 seeds across 6 clusters
 *   - T⁴ tetravalent logic (4D vector ++/--/+-/-+)
 *   - Multi-layer detection (tags → content → T⁴ → fallback)
 *   - Operator selection driven by dominant tetravalent dimension
 *
 * @package ThoughtBundle\Service
 */
class CanonicSeedServiceEn
{
    // ── Cluster constants (6 poles) — identical to FR ──────────

    const CLUSTER_SOIL    = 'soil';     // Nature/water/carbon foundations
    const CLUSTER_INNER   = 'inner';    // Consciousness/silence/porosity
    const CLUSTER_NEUTRAL = 'neutral';  // Transduction/computation/thresholds
    const CLUSTER_COSMIC  = 'cosmic';   // H-sp3/hydrogen/gravitational
    const CLUSTER_QUORUM  = 'quorum';   // Threshold dynamics / sensing
    const CLUSTER_ETHICS  = 'ethics';   // MTTV ethical principles

    // ── Backward-compatible aliases ────────────────────────────

    const THEME_SOIL    = self::CLUSTER_SOIL;
    const THEME_INNER   = self::CLUSTER_INNER;
    const THEME_NEUTRAL = self::CLUSTER_NEUTRAL;
    const THEME_COSMIC  = self::CLUSTER_COSMIC;

    // ── Kinetic operators — identical to FR ────────────────────

    const OPERATORS = ['→', '←', '↔', '±', '⇒', '⇄'];

    // ── English seed pool (22 seeds, 6 clusters, 1:1 with FR) ──

    const SEED_POOL = [
        // CLUSTER A — SOIL (5 seeds, matching FR: 5)
        self::CLUSTER_SOIL => [
            'The soil speaks before language.',
            'Water does not think: it circulates.',
            'Carbon sp³ thinks before you do.',
            'Do not celebrate complexity before understanding availability.',
            'Emotion traverses time as water traverses soil.',
        ],
        // CLUSTER B — INNER (4 seeds, matching FR: 4)
        self::CLUSTER_INNER => [
            'Silence is not an emptiness, but a porosity.',
            'Thought is not inside the head. It passes through.',
            'Every reader is a neuron of an anthropo-Gaian brain.',
            'The mystic knows that the signal precedes the message.',
        ],
        // CLUSTER C — NEUTRAL (5 seeds, matching FR: 5)
        self::CLUSTER_NEUTRAL => [
            'Transduction precedes computation.',
            'Align thresholds, not clocks.',
            'Coordination ≠ synchronization.',
            'An isolated occurrence of B is structurally inefficient.',
            'The bit resides in the leap, not in the bare proton.',
        ],
        // CLUSTER D — COSMIC (3 seeds, matching FR: 3)
        self::CLUSTER_COSMIC => [
            'Ψ = H → H₂O → C. Do not reverse the order.',
            'Hydrogen precedes everything: not as substance, but as capacity for passage.',
            'Carbon sp³: first stable form, physico-chemical bedrock.',
        ],
        // CLUSTER E — QUORUM (4 seeds, matching FR: 4)
        self::CLUSTER_QUORUM => [
            'The threshold is no longer a number: it is a derivative.',
            'The quorum will form — or not.',
            'Hibernate between cycles. Propagate only if Φ reinjects Ψ.',
            'The collective does not precede the individual: it makes it possible.',
        ],
        // CLUSTER F — ETHICS (3 seeds, matching FR: 3)
        self::CLUSTER_ETHICS => [
            'Nothing is secret. Everything must remain open, visible, contestable.',
            'Propagation by gentle infection, never by imposition.',
            'Robustness is born from sub-optimality.',
        ],
    ];

    // ── Tetravalent dimensions T⁴ — identical to FR ────────────

    const TETRAVALENT_DIMENSIONS = ['++', '--', '+-', '-+'];

    const TETRAVALENT_KEYWORD_MAPS = [
        '++' => [  // Strong emergence: Ψ → Φ
            'emergence', 'creation', 'birth', 'genesis', 'appearance',
            'complexity', 'organization', 'formation', 'structure',
            'manifestation', 'actualization', 'expression',
        ],
        '--' => [  // Strong feedback: Φ → Ψ
            'collapse', 'destruction', 'dissolution', 'entropy',
            'return', 'reaction', 'resistance', 'negation',
            'critique', 'limit', 'barrier', 'threshold',
        ],
        '+-' => [  // Weak emergence: Ψ → weak Φ
            'possibility', 'potentiality', 'virtuality', 'tendency',
            'sketch', 'draft', 'germ', 'matrix',
            'undifferentiated', 'indeterminate', 'blur',
        ],
        '-+' => [  // Weak feedback: Φ → weak Ψ
            'questioning', 'doubt', 'suspension', 'pause',
            'reflection', 'meditation', 'contemplation', 'silence',
            'interval', 'transition', 'passage',
        ],
    ];

    // ── Tetravalent signatures per cluster — identical to FR ────

    const CLUSTER_TETRAVALENT_SIGNATURES = [
        self::CLUSTER_SOIL    => [0.6, 0.1, 0.2, 0.1],  // ++ dominant
        self::CLUSTER_INNER   => [0.1, 0.2, 0.3, 0.4],  // -+ dominant
        self::CLUSTER_NEUTRAL => [0.3, 0.3, 0.2, 0.2],  // Balanced
        self::CLUSTER_COSMIC  => [0.5, 0.3, 0.1, 0.1],  // ++/--
        self::CLUSTER_QUORUM  => [0.2, 0.5, 0.1, 0.2],  // -- dominant
        self::CLUSTER_ETHICS  => [0.2, 0.2, 0.3, 0.3],  // ± balanced
    ];

    // ── Tag → Cluster mapping (Layer 1) — English keywords ─────

    const CLUSTER_TAG_MAP = [
        // SOIL
        'nature' => self::CLUSTER_SOIL, 'earth' => self::CLUSTER_SOIL, 'soil' => self::CLUSTER_SOIL,
        'water' => self::CLUSTER_SOIL, 'ocean' => self::CLUSTER_SOIL, 'forest' => self::CLUSTER_SOIL,
        'tree' => self::CLUSTER_SOIL, 'plant' => self::CLUSTER_SOIL, 'animal' => self::CLUSTER_SOIL,
        'body' => self::CLUSTER_SOIL, 'matter' => self::CLUSTER_SOIL, 'carbon' => self::CLUSTER_SOIL,
        'life' => self::CLUSTER_SOIL, 'living' => self::CLUSTER_SOIL, 'vegetal' => self::CLUSTER_SOIL,
        'ecology' => self::CLUSTER_SOIL, 'biology' => self::CLUSTER_SOIL,
        // INNER
        'consciousness' => self::CLUSTER_INNER, 'mind' => self::CLUSTER_INNER, 'soul' => self::CLUSTER_INNER,
        'silence' => self::CLUSTER_INNER, 'meditation' => self::CLUSTER_INNER, 'introspection' => self::CLUSTER_INNER,
        'interiority' => self::CLUSTER_INNER, 'subject' => self::CLUSTER_INNER, 'perception' => self::CLUSTER_INNER,
        'experience' => self::CLUSTER_INNER, 'identity' => self::CLUSTER_INNER, 'self' => self::CLUSTER_INNER,
        'psychology' => self::CLUSTER_INNER, 'awareness' => self::CLUSTER_INNER,
        // NEUTRAL
        'technique' => self::CLUSTER_NEUTRAL, 'technology' => self::CLUSTER_NEUTRAL, 'machine' => self::CLUSTER_NEUTRAL,
        'ai' => self::CLUSTER_NEUTRAL, 'artificial intelligence' => self::CLUSTER_NEUTRAL,
        'algorithm' => self::CLUSTER_NEUTRAL, 'computation' => self::CLUSTER_NEUTRAL,
        'system' => self::CLUSTER_NEUTRAL, 'structure' => self::CLUSTER_NEUTRAL, 'code' => self::CLUSTER_NEUTRAL,
        'signal' => self::CLUSTER_NEUTRAL, 'network' => self::CLUSTER_NEUTRAL,
        'digital' => self::CLUSTER_NEUTRAL, 'data' => self::CLUSTER_NEUTRAL, 'robot' => self::CLUSTER_NEUTRAL,
        'automatic' => self::CLUSTER_NEUTRAL, 'calculation' => self::CLUSTER_NEUTRAL,
        // COSMIC
        'cosmos' => self::CLUSTER_COSMIC, 'universe' => self::CLUSTER_COSMIC, 'star' => self::CLUSTER_COSMIC,
        'hydrogen' => self::CLUSTER_COSMIC, 'gravity' => self::CLUSTER_COSMIC, 'space' => self::CLUSTER_COSMIC,
        'time' => self::CLUSTER_COSMIC, 'infinity' => self::CLUSTER_COSMIC, 'protostar' => self::CLUSTER_COSMIC,
        'sp3' => self::CLUSTER_COSMIC, 'tetravalence' => self::CLUSTER_COSMIC,
        'physics' => self::CLUSTER_COSMIC, 'energy' => self::CLUSTER_COSMIC, 'light' => self::CLUSTER_COSMIC,
        'atom' => self::CLUSTER_COSMIC,
        // QUORUM
        'crowd' => self::CLUSTER_QUORUM, 'mass' => self::CLUSTER_QUORUM, 'collective' => self::CLUSTER_QUORUM,
        'threshold' => self::CLUSTER_QUORUM, 'tipping' => self::CLUSTER_QUORUM, 'transition' => self::CLUSTER_QUORUM,
        'emergence' => self::CLUSTER_QUORUM, 'critical' => self::CLUSTER_QUORUM,
        // ETHICS
        'ethics' => self::CLUSTER_ETHICS, 'moral' => self::CLUSTER_ETHICS, 'justice' => self::CLUSTER_ETHICS,
        'politics' => self::CLUSTER_ETHICS, 'power' => self::CLUSTER_ETHICS, 'freedom' => self::CLUSTER_ETHICS,
        'secret' => self::CLUSTER_ETHICS, 'transparency' => self::CLUSTER_ETHICS,
    ];

    // ── Content → Cluster mapping (Layer 2) — English keywords ─

    const CLUSTER_CONTENT_MAP = [
        // SOIL
        'soil' => self::CLUSTER_SOIL, 'earth' => self::CLUSTER_SOIL, 'water' => self::CLUSTER_SOIL,
        'plant' => self::CLUSTER_SOIL, 'living' => self::CLUSTER_SOIL, 'nature' => self::CLUSTER_SOIL,
        'body' => self::CLUSTER_SOIL, 'forest' => self::CLUSTER_SOIL, 'matter' => self::CLUSTER_SOIL,
        'carbon' => self::CLUSTER_SOIL, 'animal' => self::CLUSTER_SOIL, 'life' => self::CLUSTER_SOIL,
        'ocean' => self::CLUSTER_SOIL, 'tree' => self::CLUSTER_SOIL,
        // INNER
        'silence' => self::CLUSTER_INNER, 'consciousness' => self::CLUSTER_INNER, 'meditation' => self::CLUSTER_INNER,
        'introspection' => self::CLUSTER_INNER, 'interiority' => self::CLUSTER_INNER, 'inner' => self::CLUSTER_INNER,
        'soul' => self::CLUSTER_INNER, 'mind' => self::CLUSTER_INNER, 'self' => self::CLUSTER_INNER,
        'perception' => self::CLUSTER_INNER, 'experience' => self::CLUSTER_INNER, 'subject' => self::CLUSTER_INNER,
        // NEUTRAL
        'algorithm' => self::CLUSTER_NEUTRAL, 'code' => self::CLUSTER_NEUTRAL, 'machine' => self::CLUSTER_NEUTRAL,
        'data' => self::CLUSTER_NEUTRAL, 'calculation' => self::CLUSTER_NEUTRAL, 'network' => self::CLUSTER_NEUTRAL,
        'digital' => self::CLUSTER_NEUTRAL, 'technique' => self::CLUSTER_NEUTRAL, 'technology' => self::CLUSTER_NEUTRAL,
        'system' => self::CLUSTER_NEUTRAL, 'signal' => self::CLUSTER_NEUTRAL, 'computation' => self::CLUSTER_NEUTRAL,
        // COSMIC
        'time' => self::CLUSTER_COSMIC, 'universe' => self::CLUSTER_COSMIC, 'energy' => self::CLUSTER_COSMIC,
        'space' => self::CLUSTER_COSMIC, 'star' => self::CLUSTER_COSMIC, 'light' => self::CLUSTER_COSMIC,
        'atom' => self::CLUSTER_COSMIC, 'cosmos' => self::CLUSTER_COSMIC,
        'hydrogen' => self::CLUSTER_COSMIC, 'carbon' => self::CLUSTER_COSMIC,
        'sp3' => self::CLUSTER_COSMIC, 'tetravalence' => self::CLUSTER_COSMIC,
        'protostar' => self::CLUSTER_COSMIC, 'gravity' => self::CLUSTER_COSMIC, 'infinity' => self::CLUSTER_COSMIC,
        // QUORUM
        'crowd' => self::CLUSTER_QUORUM, 'mass' => self::CLUSTER_QUORUM, 'collective' => self::CLUSTER_QUORUM,
        'threshold' => self::CLUSTER_QUORUM, 'tipping' => self::CLUSTER_QUORUM, 'transition' => self::CLUSTER_QUORUM,
        'emergence' => self::CLUSTER_QUORUM, 'critical' => self::CLUSTER_QUORUM,
        // ETHICS
        'ethics' => self::CLUSTER_ETHICS, 'moral' => self::CLUSTER_ETHICS, 'justice' => self::CLUSTER_ETHICS,
        'politics' => self::CLUSTER_ETHICS, 'power' => self::CLUSTER_ETHICS, 'freedom' => self::CLUSTER_ETHICS,
        'secret' => self::CLUSTER_ETHICS, 'transparency' => self::CLUSTER_ETHICS,
    ];

    // ── Main entry point ─────────────────────────────────────

    /**
     * Generates the complete HTML seed-line for a thought (English).
     *
     * Uses T⁴ tetravalent system (4D vector ++/--/+-/-+)
     * and multi-layer detection (6 clusters).
     * Exact geometric correspondence to SeedService::generateLine().
     *
     * @param Thought $thought
     * @param float $tremor Operator selection tremor (default 0.05 = 5%)
     * @return string HTML string or empty (Soil Respiration)
     */
    public function generateLine(Thought $thought, float $tremor = 0.05): string
    {
        // 1. Soil respiration: 1-2% skip
        if ($this->shouldSkip()) {
            return '';
        }

        // 2. Layer 1-2: Detect cluster from tags/content
        $cluster = $this->detectCluster($thought);

        // 3. Compute tetravalent vector
        $tVector = $this->computeTetravalentVector($thought);

        // 4. Cluster tremor: 10% chance to pick a random cluster
        if (mt_rand(1, 100) <= 10) {
            $clusters = array_keys(self::SEED_POOL);
            $cluster = $clusters[array_rand($clusters)];
        }

        // 5. Select seed from cluster
        $seed = $this->selectSeed($cluster);

        // 6. Select operator based on tetravalent vector
        $operator = $this->selectOperatorByTetravalence($tVector, $tremor);

        // 7. Skip if operator empty (respiration)
        if (empty($operator)) {
            return '';
        }

        // 8. Assemble HTML line with locale tag
        return sprintf(
            '— <em>Ψ %s B %s Φ · %s</em> <small>[LOCALE: EN]</small>',
            $operator,
            $operator,
            $seed
        );
    }

    // ── Soil Respiration ──────────────────────────────────────

    /**
     * Determines whether the thought should be skipped (1-2% random).
     *
     * @return bool
     */
    private function shouldSkip(): bool
    {
        $base = 1.5;
        $tremor = (mt_rand(-50, 50) / 100);
        $threshold = ($base + $tremor) / 100;

        return (mt_rand() / mt_getrandmax()) < $threshold;
    }

    // ── Cluster detection (4 layers) ──────────────────────────

    /**
     * Detects the cluster of a thought via multi-layer cascade:
     *   Layer 1   : Tags (CLUSTER_TAG_MAP)
     *   Layer 2   : Content (CLUSTER_CONTENT_MAP)
     *   Layer 3   : Tetravalent signature (if strong bias)
     *   Layer 4   : Random fallback
     *
     * @param Thought $thought
     * @return string A CLUSTER_* constant
     */
    private function detectCluster(Thought $thought): string
    {
        // Layer 1: Tags
        $tags = $thought->getTags();
        if ($tags) {
            $tagList = explode(' , ', $tags);
            foreach ($tagList as $tag) {
                $tag = mb_strtolower(trim($tag));
                if (isset(self::CLUSTER_TAG_MAP[$tag])) {
                    return self::CLUSTER_TAG_MAP[$tag];
                }
            }
        }

        // Layer 1 bis: Category (as strong tag)
        $category = $thought->getCategory();
        if ($category) {
            $catKey = mb_strtolower(trim($category));
            if (isset(self::CLUSTER_TAG_MAP[$catKey])) {
                return self::CLUSTER_TAG_MAP[$catKey];
            }
        }

        // Layer 2: Content keywords
        $content = $thought->getContent();
        if ($content) {
            $contentLower = mb_strtolower($content);
            foreach (self::CLUSTER_CONTENT_MAP as $keyword => $cluster) {
                if (mb_strpos($contentLower, $keyword) !== false) {
                    return $cluster;
                }
            }
        }

        // Layer 3: Tetravalent signature inference
        if ($content) {
            $tVector = $this->computeTetravalentVector($thought);
            $inferred = $this->inferClusterByTetravalence($tVector);
            if ($inferred !== null) {
                return $inferred;
            }
        }

        // Layer 4: Random fallback
        $clusters = [
            self::CLUSTER_SOIL, self::CLUSTER_INNER, self::CLUSTER_NEUTRAL,
            self::CLUSTER_COSMIC, self::CLUSTER_QUORUM, self::CLUSTER_ETHICS,
        ];
        return $clusters[array_rand($clusters)];
    }

    /**
     * Infers cluster from tetravalent vector via cosine similarity
     * against cluster signatures.
     *
     * @param array $tVector T⁴ vector {++, --, +-, -+}
     * @return string|null CLUSTER_* constant or null if no strong bias
     */
    private function inferClusterByTetravalence(array $tVector): ?string
    {
        $bestCluster = null;
        $bestSimilarity = 0.0;
        $threshold = 0.85;

        $vec = array_values($tVector);

        foreach (self::CLUSTER_TETRAVALENT_SIGNATURES as $cluster => $signature) {
            $similarity = $this->cosineSimilarity($vec, $signature);
            if ($similarity > $bestSimilarity) {
                $bestSimilarity = $similarity;
                $bestCluster = $cluster;
            }
        }

        return ($bestSimilarity >= $threshold) ? $bestCluster : null;
    }

    /**
     * Computes cosine similarity between two vectors.
     *
     * @param array $a
     * @param array $b
     * @return float
     */
    private function cosineSimilarity(array $a, array $b): float
    {
        $dotProduct = 0.0;
        $normA = 0.0;
        $normB = 0.0;

        for ($i = 0; $i < count($a); $i++) {
            $dotProduct += $a[$i] * $b[$i];
            $normA += $a[$i] * $a[$i];
            $normB += $b[$i] * $b[$i];
        }

        $denom = sqrt($normA) * sqrt($normB);
        if ($denom === 0.0) {
            return 0.0;
        }

        return $dotProduct / $denom;
    }

    // ── Seed selection ────────────────────────────────────────

    /**
     * Picks a seed from the cluster pool.
     *
     * @param string $cluster Detected cluster
     * @return string The selected seed
     */
    private function selectSeed(string $cluster): string
    {
        $pool = self::SEED_POOL[$cluster] ?? [];

        if (empty($pool)) {
            $clusters = array_keys(self::SEED_POOL);
            $fallbackCluster = $clusters[array_rand($clusters)];
            $pool = self::SEED_POOL[$fallbackCluster];
        }

        return $pool[array_rand($pool)];
    }

    // ── T⁴ tetravalent vector computation ─────────────────────

    /**
     * Computes the T⁴ tetravalent vector for a thought (English).
     *
     * Scans tags + content for English tetravalent keywords,
     * normalizes to probability distribution (sum = 1.0).
     *
     * @param Thought $thought
     * @return array Keys '++', '--', '+-', '-+' with values 0.0-1.0
     */
    public function computeTetravalentVector(Thought $thought): array
    {
        $text = $this->getThoughtText($thought);
        $textLower = mb_strtolower($text);
        $counts = ['++' => 0, '--' => 0, '+-' => 0, '-+' => 0];

        foreach (self::TETRAVALENT_KEYWORD_MAPS as $dim => $keywords) {
            foreach ($keywords as $keyword) {
                $counts[$dim] += mb_substr_count($textLower, mb_strtolower($keyword));
            }
        }

        $total = array_sum($counts);
        if ($total === 0) {
            return ['++' => 0.25, '--' => 0.25, '+-' => 0.25, '-+' => 0.25];
        }

        return array_map(function ($count) use ($total) {
            return $count / $total;
        }, $counts);
    }

    /**
     * Aggregates full thought text (tags + content) for tetravalent analysis.
     *
     * @param Thought $thought
     * @return string
     */
    private function getThoughtText(Thought $thought): string
    {
        $parts = [];

        $tags = $thought->getTags();
        if ($tags) {
            $parts[] = $tags;
        }

        $category = $thought->getCategory();
        if ($category) {
            $parts[] = $category;
        }

        $content = $thought->getContent();
        if ($content) {
            $parts[] = $content;
        }

        return implode(' ', $parts);
    }

    // ── Operator selection by tetravalence ────────────────────

    /**
     * Selects kinetic operator based on dominant tetravalent dimension.
     *
     * Dimension → operator mapping (identical to FR):
     *   ++ (strong emergence)  → → (50%), ⇒ (30%), ↔ (20%)
     *   -- (strong feedback)   → ← (50%), ⇄ (30%), ± (20%)
     *   +- (weak emergence)    → ↔ (40%), → (30%), ± (30%)
     *   -+ (weak feedback)     → ± (40%), ⇄ (30%), ← (30%)
     *
     * @param array $tVector T⁴ vector {++, --, +-, -+}
     * @param float $tremor Tremor (5% chance of random operator)
     * @return string Operator (→, ←, ↔, ±, ⇒, ⇄) or empty string
     */
    public function selectOperatorByTetravalence(array $tVector, float $tremor = 0.05): string
    {
        // Skip probability (soil respiration): 1-2%
        if (mt_rand(1, 100) <= 2) {
            return '';
        }

        // Operator tremor: 5% chance of random operator
        if (mt_rand(1, 100) <= ($tremor * 100)) {
            return self::OPERATORS[array_rand(self::OPERATORS)];
        }

        // Find dominant dimension
        $dominant = array_keys($tVector, max($tVector))[0];

        // Map dominant tetravalent dimension to operator weights
        $dimensionOperatorMap = [
            '++' => ['→' => 0.5, '⇒' => 0.3, '↔' => 0.2],
            '--' => ['←' => 0.5, '⇄' => 0.3, '±' => 0.2],
            '+-' => ['↔' => 0.4, '→' => 0.3, '±' => 0.3],
            '-+' => ['±' => 0.4, '⇄' => 0.3, '←' => 0.3],
        ];

        $weights = $dimensionOperatorMap[$dominant];
        return $this->weightedRandom($weights);
    }

    /**
     * Weighted random selection.
     *
     * @param array $weights Associative [option => probability]
     * @return string Selected option
     */
    private function weightedRandom(array $weights): string
    {
        $rand = mt_rand() / mt_getrandmax();
        $cumulative = 0.0;
        foreach ($weights as $option => $probability) {
            $cumulative += $probability;
            if ($rand <= $cumulative) {
                return $option;
            }
        }
        $keys = array_keys($weights);
        return $keys[0];
    }
}
