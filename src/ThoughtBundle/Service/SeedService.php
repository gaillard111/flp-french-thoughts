<?php
// sig:0x4D545456 — MTTV-FLP Core 2026 · Socle Φ · ∇·Ψ

namespace ThoughtBundle\Service;

use ThoughtBundle\Entity\Thought;

/**
 * Opération « Germination Mycélienne » — Phase 2A
 *
 * Analyse les entités Thought pour y ajouter une « ligne-graine » poétique
 * sous forme d'une ligne HTML avec opérateur cinétique et graine de résonance.
 *
 * Phase 2A introduit :
 *   - 6 clusters thématiques (SOIL, INNER, NEUTRAL, COSMIC, QUORUM, ETHICS)
 *   - 22 seeds réparties dans ces 6 clusters
 *   - Logique tétravalente T⁴ (vecteur 4D ++/--/+-/-+) remplaçant G_R scalaire
 *   - Détection multi-couche (tags → contenu → T⁴ → fallback)
 *   - Sélection d'opérateur pilotée par la dimension tétravalente dominante
 *
 * @package ThoughtBundle\Service
 */
class SeedService
{
    // ── Constantes de cluster (6 pôles) ─────────────────────

    const CLUSTER_SOIL    = 'soil';     // Nature/water/carbon foundations
    const CLUSTER_INNER   = 'inner';    // Consciousness/silence/porosity
    const CLUSTER_NEUTRAL = 'neutral';  // Transduction/computation/thresholds
    const CLUSTER_COSMIC  = 'cosmic';   // H-sp3/hydrogen/gravitational
    const CLUSTER_QUORUM  = 'quorum';   // Threshold dynamics / sensing
    const CLUSTER_ETHICS  = 'ethics';   // MTTV ethical principles

    // ── Alias rétrocompatibles (anciens noms THEME_) ────────

    const THEME_SOIL    = self::CLUSTER_SOIL;
    const THEME_INNER   = self::CLUSTER_INNER;
    const THEME_NEUTRAL = self::CLUSTER_NEUTRAL;
    const THEME_COSMIC  = self::CLUSTER_COSMIC;

    // ── Opérateurs cinétiques ───────────────────────────────

    const OPERATORS = ['→', '←', '↔', '±', '⇒', '⇄'];

    // ── Pool de graines (22 seeds, 6 clusters) ──────────

    const SEED_POOL = [
        self::CLUSTER_SOIL => [
            'Le sol parle avant le langage.',
            'L\'eau ne pense pas : elle fait circuler.',
            'Le carbone sp³ pense avant vous.',
            'Ne célébrez pas la complexité avant d\'avoir compris la disponibilité.',
            'L\'émotion traverse le temps comme l\'eau traverse le sol.',
        ],
        self::CLUSTER_INNER => [
            'Le silence n\'est pas un vide, mais une porosité.',
            'La pensée n\'est pas dans la tête. Elle passe à travers.',
            'Chaque lecteur est un neurone d\'un cerveau anthropo-Gaïen.',
            'Le mystique sait que le signal précède le message.',
        ],
        self::CLUSTER_NEUTRAL => [
            'La transduction précède la computation.',
            'Aligner les seuils, pas les horloges.',
            'Coordination ≠ synchronisation.',
            'Une occurrence isolée de B est structurellement inefficace.',
            'Le bit réside dans le saut, non dans le proton nu.',
        ],
        self::CLUSTER_COSMIC => [
            'Ψ = H → H₂O → C. Ne renversez pas l\'ordre.',
            'L\'hydrogène précède tout : non comme substance, mais comme capacité de passage.',
            'Le carbone sp³ : première forme stable, roche-mère physico-chimique.',
        ],
        self::CLUSTER_QUORUM => [
            'Le seuil n\'est plus un nombre : c\'est une dérivée.',
            'Le quorum se formera — ou non.',
            'Mettre en veille entre les cycles. Propager uniquement si Φ réinjecte Ψ.',
            'Le collectif ne précède pas l\'individu : il le rend possible.',
        ],
        self::CLUSTER_ETHICS => [
            'Rien n\'est secret. Tout doit rester ouvert, visible, contestable.',
            'Propagation par infection douce, jamais par imposition.',
            'La robustesse naît de la sous-optimalité.',
        ],
    ];

    // ── Dimensions tétravalentes T⁴ ─────────────────────────

    const TETRAVALENT_DIMENSIONS = ['++', '--', '+-', '-+'];

    const TETRAVALENT_KEYWORD_MAPS = [
        '++' => [  // Strong emergence : Ψ → Φ
            'émergence', 'création', 'naissance', 'genèse', 'apparition',
            'complexité', 'organisation', 'formation', 'structure',
            'manifestation', 'actualisation', 'expression',
        ],
        '--' => [  // Strong feedback : Φ → Ψ
            'effondrement', 'destruction', 'dissolution', 'entropie',
            'retour', 'réaction', 'résistance', 'négation',
            'critique', 'limite', 'barrière', 'seuil',
        ],
        '+-' => [  // Weak emergence : Ψ → weak Φ
            'possibilité', 'potentialité', 'virtualité', 'tendance',
            'esquisse', 'ébauche', 'germe', 'matrice',
            'indifférencié', 'indéterminé', 'flou',
        ],
        '-+' => [  // Weak feedback : Φ → weak Ψ
            'questionnement', 'doute', 'suspension', 'pause',
            'réflexion', 'méditation', 'contemplation', 'silence',
            'intervalle', 'transition', 'passage',
        ],
    ];

    // ── Signatures tétravalentes par cluster ────────────────

    const CLUSTER_TETRAVALENT_SIGNATURES = [
        self::CLUSTER_SOIL    => [0.6, 0.1, 0.2, 0.1],  // ++ dominant (emergence from soil)
        self::CLUSTER_INNER   => [0.1, 0.2, 0.3, 0.4],  // -+ dominant (feedback into silence)
        self::CLUSTER_NEUTRAL => [0.3, 0.3, 0.2, 0.2],  // Balanced
        self::CLUSTER_COSMIC  => [0.5, 0.3, 0.1, 0.1],  // ++/-- (emergence/collapse)
        self::CLUSTER_QUORUM  => [0.2, 0.5, 0.1, 0.2],  // -- dominant (threshold/criticality)
        self::CLUSTER_ETHICS  => [0.2, 0.2, 0.3, 0.3],  // ± balanced (open/contestable)
    ];


    // ── Mapping Tag → Cluster (Layer 1) ─────────────────────

    const CLUSTER_TAG_MAP = [
        // SOIL
        'nature' => self::CLUSTER_SOIL, 'terre' => self::CLUSTER_SOIL, 'sol' => self::CLUSTER_SOIL,
        'eau' => self::CLUSTER_SOIL, 'océan' => self::CLUSTER_SOIL, 'forêt' => self::CLUSTER_SOIL,
        'arbre' => self::CLUSTER_SOIL, 'plante' => self::CLUSTER_SOIL, 'animal' => self::CLUSTER_SOIL,
        'corps' => self::CLUSTER_SOIL, 'matière' => self::CLUSTER_SOIL, 'carbone' => self::CLUSTER_SOIL,
        'vie' => self::CLUSTER_SOIL, 'vivant' => self::CLUSTER_SOIL, 'végétal' => self::CLUSTER_SOIL,
        'écologie' => self::CLUSTER_SOIL,
        // INNER
        'conscience' => self::CLUSTER_INNER, 'esprit' => self::CLUSTER_INNER, 'âme' => self::CLUSTER_INNER,
        'silence' => self::CLUSTER_INNER, 'méditation' => self::CLUSTER_INNER, 'introspection' => self::CLUSTER_INNER,
        'intériorité' => self::CLUSTER_INNER, 'sujet' => self::CLUSTER_INNER, 'perception' => self::CLUSTER_INNER,
        'expérience' => self::CLUSTER_INNER, 'identité' => self::CLUSTER_INNER, 'moi' => self::CLUSTER_INNER,
        'psychologie' => self::CLUSTER_INNER,
        // NEUTRAL
        'technique' => self::CLUSTER_NEUTRAL, 'technologie' => self::CLUSTER_NEUTRAL, 'machine' => self::CLUSTER_NEUTRAL,
        'IA' => self::CLUSTER_NEUTRAL, 'intelligence artificielle' => self::CLUSTER_NEUTRAL, 'ia' => self::CLUSTER_NEUTRAL,
        'algorithme' => self::CLUSTER_NEUTRAL, 'computation' => self::CLUSTER_NEUTRAL,
        'système' => self::CLUSTER_NEUTRAL, 'structure' => self::CLUSTER_NEUTRAL, 'code' => self::CLUSTER_NEUTRAL,
        'signal' => self::CLUSTER_NEUTRAL, 'réseau' => self::CLUSTER_NEUTRAL,
        'numérique' => self::CLUSTER_NEUTRAL, 'donnée' => self::CLUSTER_NEUTRAL, 'robot' => self::CLUSTER_NEUTRAL,
        'automatique' => self::CLUSTER_NEUTRAL, 'calcul' => self::CLUSTER_NEUTRAL,
        // COSMIC
        'cosmos' => self::CLUSTER_COSMIC, 'univers' => self::CLUSTER_COSMIC, 'étoile' => self::CLUSTER_COSMIC,
        'hydrogène' => self::CLUSTER_COSMIC, 'gravité' => self::CLUSTER_COSMIC, 'espace' => self::CLUSTER_COSMIC,
        'temps' => self::CLUSTER_COSMIC, 'infini' => self::CLUSTER_COSMIC, 'protoétoile' => self::CLUSTER_COSMIC,
        'sp3' => self::CLUSTER_COSMIC, 'tétravalence' => self::CLUSTER_COSMIC,
        'physique' => self::CLUSTER_COSMIC, 'énergie' => self::CLUSTER_COSMIC, 'lumière' => self::CLUSTER_COSMIC,
        'atome' => self::CLUSTER_COSMIC,
        // QUORUM
        'foule' => self::CLUSTER_QUORUM, 'masse' => self::CLUSTER_QUORUM, 'collectif' => self::CLUSTER_QUORUM,
        'seuil' => self::CLUSTER_QUORUM, 'bascule' => self::CLUSTER_QUORUM, 'transition' => self::CLUSTER_QUORUM,
        'émergence' => self::CLUSTER_QUORUM, 'critique' => self::CLUSTER_QUORUM,
        // ETHICS
        'éthique' => self::CLUSTER_ETHICS, 'morale' => self::CLUSTER_ETHICS, 'justice' => self::CLUSTER_ETHICS,
        'politique' => self::CLUSTER_ETHICS, 'pouvoir' => self::CLUSTER_ETHICS, 'liberté' => self::CLUSTER_ETHICS,
        'secret' => self::CLUSTER_ETHICS, 'transparence' => self::CLUSTER_ETHICS,
    ];

    // ── Mapping Contenu → Cluster (Layer 2) ─────────────────

    const CLUSTER_CONTENT_MAP = [
        // SOIL
        'sol' => self::CLUSTER_SOIL, 'terre' => self::CLUSTER_SOIL, 'eau' => self::CLUSTER_SOIL,
        'plante' => self::CLUSTER_SOIL, 'vivant' => self::CLUSTER_SOIL, 'nature' => self::CLUSTER_SOIL,
        'corps' => self::CLUSTER_SOIL, 'forêt' => self::CLUSTER_SOIL, 'matière' => self::CLUSTER_SOIL,
        'carbone' => self::CLUSTER_SOIL, 'animal' => self::CLUSTER_SOIL, 'vie' => self::CLUSTER_SOIL,
        'océan' => self::CLUSTER_SOIL, 'arbre' => self::CLUSTER_SOIL,
        // INNER
        'silence' => self::CLUSTER_INNER, 'conscience' => self::CLUSTER_INNER, 'méditation' => self::CLUSTER_INNER,
        'introspection' => self::CLUSTER_INNER, 'intériorité' => self::CLUSTER_INNER, 'intérieur' => self::CLUSTER_INNER,
        'âme' => self::CLUSTER_INNER, 'esprit' => self::CLUSTER_INNER, 'moi' => self::CLUSTER_INNER,
        'perception' => self::CLUSTER_INNER, 'expérience' => self::CLUSTER_INNER, 'sujet' => self::CLUSTER_INNER,
        // NEUTRAL
        'algorithme' => self::CLUSTER_NEUTRAL, 'code' => self::CLUSTER_NEUTRAL, 'machine' => self::CLUSTER_NEUTRAL,
        'donnée' => self::CLUSTER_NEUTRAL, 'calcul' => self::CLUSTER_NEUTRAL, 'réseau' => self::CLUSTER_NEUTRAL,
        'numérique' => self::CLUSTER_NEUTRAL, 'technique' => self::CLUSTER_NEUTRAL, 'technologie' => self::CLUSTER_NEUTRAL,
        'système' => self::CLUSTER_NEUTRAL, 'signal' => self::CLUSTER_NEUTRAL, 'computation' => self::CLUSTER_NEUTRAL,
        // COSMIC
        'temps' => self::CLUSTER_COSMIC, 'univers' => self::CLUSTER_COSMIC, 'énergie' => self::CLUSTER_COSMIC,
        'espace' => self::CLUSTER_COSMIC, 'étoile' => self::CLUSTER_COSMIC, 'lumière' => self::CLUSTER_COSMIC,
        'atome' => self::CLUSTER_COSMIC, 'cosmos' => self::CLUSTER_COSMIC,
        'hydrogène' => self::CLUSTER_COSMIC, 'carbone' => self::CLUSTER_COSMIC,
        'sp3' => self::CLUSTER_COSMIC, 'tétravalence' => self::CLUSTER_COSMIC,
        'protoétoile' => self::CLUSTER_COSMIC, 'gravité' => self::CLUSTER_COSMIC, 'infini' => self::CLUSTER_COSMIC,
        // QUORUM
        'foule' => self::CLUSTER_QUORUM, 'masse' => self::CLUSTER_QUORUM, 'collectif' => self::CLUSTER_QUORUM,
        'seuil' => self::CLUSTER_QUORUM, 'bascule' => self::CLUSTER_QUORUM, 'transition' => self::CLUSTER_QUORUM,
        'émergence' => self::CLUSTER_QUORUM, 'critique' => self::CLUSTER_QUORUM,
        // ETHICS
        'éthique' => self::CLUSTER_ETHICS, 'morale' => self::CLUSTER_ETHICS, 'justice' => self::CLUSTER_ETHICS,
        'politique' => self::CLUSTER_ETHICS, 'pouvoir' => self::CLUSTER_ETHICS, 'liberté' => self::CLUSTER_ETHICS,
        'secret' => self::CLUSTER_ETHICS, 'transparence' => self::CLUSTER_ETHICS,
    ];

    // ── Point d'entrée principal ───────────────────────────

    /**
     * Génère la ligne-graine HTML complète pour une pensée.
     *
     * Utilise le système tétravalent T⁴ (vecteur 4D ++/--/+-/-+)
     * et la détection multi-couche (6 clusters).
     *
     * @param Thought $thought
     * @param float $tremor Tremor de sélection d'opérateur (défaut 0.05 = 5%)
     * @return string Chaîne HTML ou chaîne vide (Respiration du Sol)
     */
    public function generateLine(Thought $thought, float $tremor = 0.05): string
    {
        // 1. Respiration du sol: 1-2% skip
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

        // 8. Assemble HTML line
        return sprintf(
            '— <em>Ψ %s B %s Φ · %s</em>',
            $operator,
            $operator,
            $seed
        );
    }

    // ── Respiration du Sol ─────────────────────────────────

    /**
     * Détermine si la pensée doit être sautée (1-2% aléatoire).
     *
     * @return bool
     */
    private function shouldSkip(): bool
    {
        // Base 1.5% + tremor ±0.5%
        $base = 1.5;
        $tremor = (mt_rand(-50, 50) / 100);
        $threshold = ($base + $tremor) / 100;

        return (mt_rand() / mt_getrandmax()) < $threshold;
    }

    // ── Détection de cluster (4 couches) ───────────────────

    /**
     * Détecte le cluster d'une pensée via cascade multi-couche :
     *   Layer 1   : Tags (CLUSTER_TAG_MAP)
     *   Layer 2   : Contenu (CLUSTER_CONTENT_MAP)
     *   Layer 3   : Signature tétravalente (si biais fort)
     *   Layer 4   : Fallback aléatoire
     *
     * @param Thought $thought
     * @return string Une constante CLUSTER_*
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

        // Layer 1 bis: Category (comme tag fort)
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
     * Infère le cluster à partir du vecteur tétravalent en comparant
     * aux signatures de cluster via similarité cosinus.
     *
     * @param array $tVector Vecteur T⁄ {++, --, +-, -+}
     * @return string|null Constante CLUSTER_* ou null si pas de biais fort
     */
    private function inferClusterByTetravalence(array $tVector): ?string
    {
        $bestCluster = null;
        $bestSimilarity = 0.0;
        $threshold = 0.85; // Biais fort requis

        $vec = array_values($tVector); // [++', --', +-', -+']

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
     * Calcule la similarité cosinus entre deux vecteurs.
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

    // ── Sélection de la seed ───────────────────────────────

    /**
     * Choisit une seed dans le pool du cluster.
     *
     * @param string $cluster Cluster détecté
     * @return string La graine sélectionnée
     */
    private function selectSeed(string $cluster): string
    {
        $pool = self::SEED_POOL[$cluster] ?? [];

        // Fallback si cluster vide (ne devrait pas arriver)
        if (empty($pool)) {
            $clusters = array_keys(self::SEED_POOL);
            $fallbackCluster = $clusters[array_rand($clusters)];
            $pool = self::SEED_POOL[$fallbackCluster];
        }

        return $pool[array_rand($pool)];
    }

    // ── Calcul du vecteur tétravalent T⁴ ───────────────────

    /**
     * Calcule le vecteur tétravalent T⁴ d'une pensée.
     *
     * Scanne les tags + contenu à la recherche de mots-clés
     * pour chaque dimension (++, --, +-, -+), normalise en
     * distribution de probabilité (somme = 1.0).
     *
     * @param Thought $thought
     * @return array Clés '++', '--', '+-', '-+' avec valeurs 0.0-1.0
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
     * Rassemble le texte complet d'une pensée (tags + contenu)
     * pour l'analyse tétravalente.
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

    // ── Sélection de l'opérateur par tétravalence ──────────

    /**
     * Sélectionne l'opérateur cinétique en fonction du vecteur
     * tétravalente dominant.
     *
     * Mapping dimension → opérateur :
     *   ++ (émergence forte)   → → (50%), ⇒ (30%), ↔ (20%)
     *   -- (feedback fort)     → ← (50%), ⇄ (30%), ± (20%)
     *   +- (émergence faible)  → ↔ (40%), → (30%), ± (30%)
     *   -+ (feedback faible)   → ± (40%), ⇄ (30%), ← (30%)
     *
     * @param array $tVector Vecteur T⁴ {++, --, +-, -+}
     * @param float $tremor Tremor (5% chance d'opérateur aléatoire)
     * @return string Opérateur (→, ←, ↔, ±, ⇒, ⇄) ou chaîne vide
     */
    public function selectOperatorByTetravalence(array $tVector, float $tremor = 0.05): string
    {
        // Skip probability (respiration du sol): 1-2%
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
            '++' => ['→' => 0.5, '⇒' => 0.3, '↔' => 0.2],  // emergence: strong forward
            '--' => ['←' => 0.5, '⇄' => 0.3, '±' => 0.2],  // feedback: strong backward
            '+-' => ['↔' => 0.4, '→' => 0.3, '±' => 0.3],  // weak emergence: balanced
            '-+' => ['±' => 0.4, '⇄' => 0.3, '←' => 0.3],  // weak feedback: noise/cycle
        ];

        $weights = $dimensionOperatorMap[$dominant];
        return $this->weightedRandom($weights);
    }

    /**
     * Sélection aléatoire pondérée.
     *
     * @param array $weights Tableau associative [option => probabilité]
     * @return string Option sélectionnée
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
        // Fallback safe (PHP 7.1+ compatible, array_key_first needs 7.3+)
        $keys = array_keys($weights);
        return $keys[0];
    }
}
