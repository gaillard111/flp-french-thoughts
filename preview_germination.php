<?php
/**
 * Opération « Germination Mycélienne » — Preview Script (Phase 2A)
 *
 * Script PHP autonome qui démontre le comportement du SeedService v2
 * sans nécessiter l'infrastructure Symfony complète.
 *
 * Usage :
 *   php preview_germination.php
 *   php preview_germination.php > apercu.html
 *
 * @package ThoughtBundle\Preview
 */

// ─────────────────────────────────────────────────────────────
// 1. StandaloneSeedService (Phase 2A)
// ─────────────────────────────────────────────────────────────

/**
 * Version autonome du SeedService Phase 2A qui accepte un tableau
 * associatif au lieu d'une entité Thought Symfony.
 *
 * Phase 2A introduit :
 *   - 6 clusters thématiques (SOIL, INNER, NEUTRAL, COSMIC, QUORUM, ETHICS)
 *   - 22 seeds réparties dans ces 6 clusters
 *   - Logique tétravalente T⁴ (vecteur 4D ++/--/+-/-+) remplaçant G_R scalaire
 *   - Détection multi-couche (tags → catégorie → contenu → T⁴ → fallback)
 *   - Sélection d'opérateur pilotée par la dimension tétravalente dominante
 *   - 6 opérateurs (→, ←, ↔, ±, ⇒, ⇄)
 *
 * Champs attendus dans $thought :
 *  - 'content'  (string) — le texte de la pensée
 *  - 'tags'     (string) — tags séparés par " , "
 *  - 'category' (string) — catégorie de la pensée
 */
class StandaloneSeedService
{
    // ── Constantes de cluster (6 pôles) ─────────────────────

    const CLUSTER_SOIL    = 'soil';
    const CLUSTER_INNER   = 'inner';
    const CLUSTER_NEUTRAL = 'neutral';
    const CLUSTER_COSMIC  = 'cosmic';
    const CLUSTER_QUORUM  = 'quorum';
    const CLUSTER_ETHICS  = 'ethics';

    // ── Alias rétrocompatibles ───────────────────────────────

    const THEME_SOIL    = self::CLUSTER_SOIL;
    const THEME_INNER   = self::CLUSTER_INNER;
    const THEME_NEUTRAL = self::CLUSTER_NEUTRAL;
    const THEME_COSMIC  = self::CLUSTER_COSMIC;

    // ── Opérateurs cinétiques (6) ────────────────────────────

    const OPERATORS = ['→', '←', '↔', '±', '⇒', '⇄'];

    // ── Pool de graines (22 seeds, 6 clusters) ───────────────

    private static $seeds = [
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

    private static $tetravalentKeywords = [
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

    // ── Signatures T⁴ par cluster ────────────────────────────

    private static $clusterTetravalentSignatures = [
        self::CLUSTER_SOIL    => [0.6, 0.1, 0.2, 0.1],
        self::CLUSTER_INNER   => [0.1, 0.2, 0.3, 0.4],
        self::CLUSTER_NEUTRAL => [0.3, 0.3, 0.2, 0.2],
        self::CLUSTER_COSMIC  => [0.5, 0.3, 0.1, 0.1],
        self::CLUSTER_QUORUM  => [0.2, 0.5, 0.1, 0.2],
        self::CLUSTER_ETHICS  => [0.2, 0.2, 0.3, 0.3],
    ];

    // ── Mapping Tag → Cluster (Layer 1) ─────────────────────

    private static $tagClusterMap = [
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
        'ia' => self::CLUSTER_NEUTRAL, 'algorithme' => self::CLUSTER_NEUTRAL, 'computation' => self::CLUSTER_NEUTRAL,
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

    private static $contentClusterMap = [
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
     * @param array $thought Tableau avec 'content', 'tags', 'category'.
     * @return string Chaîne HTML ou chaîne vide si skip.
     */
    public function generateLine(array $thought): string
    {
        // 1. Respiration du sol: 1-2% skip
        if ($this->shouldSkip()) {
            return '';
        }

        // 2. Détection du cluster (tags → catégorie → contenu → T⁴ → fallback)
        $cluster = $this->detectCluster($thought);

        // 3. Calcul du vecteur tétravalent
        $tVector = $this->computeTetravalentVector($thought);

        // 4. Cluster tremor: 10% de chance de cluster aléatoire (anti-Goodhart)
        if (mt_rand(1, 100) <= 10) {
            $clusters = array_keys(self::$seeds);
            $cluster = $clusters[array_rand($clusters)];
        }

        // 5. Sélection de la seed
        $seed = $this->selectSeed($cluster);

        // 6. Sélection de l'opérateur par dominance tétravalente
        $operator = $this->selectOperatorByTetravalence($tVector);

        // 7. Skip si opérateur vide (respiration)
        if (empty($operator)) {
            return '';
        }

        // 8. Assemblage de la ligne HTML
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
        $base = 1.5;
        $tremor = (mt_rand(-50, 50) / 100);
        $threshold = ($base + $tremor) / 100;
        return (mt_rand() / mt_getrandmax()) < $threshold;
    }

    // ── Détection de cluster (4 couches) ───────────────────

    /**
     * Détecte le cluster via cascade multi-couche :
     *   Layer 1 : Tags
     *   Layer 2 : Catégorie + Contenu
     *   Layer 3 : Signature tétravalente (si biais fort)
     *   Layer 4 : Fallback aléatoire
     *
     * @param array $thought
     * @return string Une constante CLUSTER_*
     */
    private function detectCluster(array $thought): string
    {
        // Layer 1: Tags
        $tags = $thought['tags'] ?? null;
        if ($tags) {
            $tagList = explode(' , ', $tags);
            foreach ($tagList as $tag) {
                $tag = mb_strtolower(trim($tag));
                if (isset(self::$tagClusterMap[$tag])) {
                    return self::$tagClusterMap[$tag];
                }
            }
        }

        // Layer 1 bis: Category
        $category = $thought['category'] ?? null;
        if ($category) {
            $catKey = mb_strtolower(trim($category));
            if (isset(self::$tagClusterMap[$catKey])) {
                return self::$tagClusterMap[$catKey];
            }
        }

        // Layer 2: Content keywords
        $content = $thought['content'] ?? null;
        if ($content) {
            $contentLower = mb_strtolower($content);
            foreach (self::$contentClusterMap as $keyword => $cluster) {
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
     * Infère le cluster à partir du vecteur tétravalent.
     *
     * @param array $tVector [++, --, +-, -+]
     * @return string|null Constante CLUSTER_* ou null
     */
    private function inferClusterByTetravalence(array $tVector): ?string
    {
        $bestCluster = null;
        $bestSimilarity = 0.0;
        $threshold = 0.85;

        $vec = array_values($tVector);

        foreach (self::$clusterTetravalentSignatures as $cluster => $signature) {
            $similarity = $this->cosineSimilarity($vec, $signature);
            if ($similarity > $bestSimilarity) {
                $bestSimilarity = $similarity;
                $bestCluster = $cluster;
            }
        }

        return ($bestSimilarity >= $threshold) ? $bestCluster : null;
    }

    /**
     * Similarité cosinus entre deux vecteurs.
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
     * @param string $cluster
     * @return string
     */
    private function selectSeed(string $cluster): string
    {
        $pool = self::$seeds[$cluster] ?? [];

        if (empty($pool)) {
            $clusters = array_keys(self::$seeds);
            $fallbackCluster = $clusters[array_rand($clusters)];
            $pool = self::$seeds[$fallbackCluster];
        }

        return $pool[array_rand($pool)];
    }

    // ── Calcul du vecteur tétravalent T⁴ ───────────────────

    /**
     * Calcule le vecteur tétravalent T⁴ d'une pensée.
     *
     * @param array $thought
     * @return array Clés '++', '--', '+-', '-+' (somme = 1.0)
     */
    public function computeTetravalentVector(array $thought): array
    {
        $parts = [];
        if (!empty($thought['tags'])) $parts[] = $thought['tags'];
        if (!empty($thought['category'])) $parts[] = $thought['category'];
        if (!empty($thought['content'])) $parts[] = $thought['content'];
        $text = implode(' ', $parts);
        $textLower = mb_strtolower($text);

        $counts = ['++' => 0, '--' => 0, '+-' => 0, '-+' => 0];

        foreach (self::$tetravalentKeywords as $dim => $keywords) {
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

    // ── Sélection de l'opérateur par tétravalence ──────────

    /**
     * Sélectionne l'opérateur cinétique selon le vecteur T⁴ dominant.
     *
     * Mapping dimension → opérateur :
     *   ++ → → (50%), ⇒ (30%), ↔ (20%)
     *   -- → ← (50%), ⇄ (30%), ± (20%)
     *   +- → ↔ (40%), → (30%), ± (30%)
     *   -+ → ± (40%), ⇄ (30%), ← (30%)
     *
     * @param array $tVector [++, --, +-, -+]
     * @return string Opérateur ou chaîne vide
     */
    public function selectOperatorByTetravalence(array $tVector): string
    {
        // Skip probabiliste (respiration)
        if (mt_rand(1, 100) <= 2) {
            return '';
        }

        // Tremor: 5% opérateur aléatoire
        if (mt_rand(1, 100) <= 5) {
            return self::OPERATORS[array_rand(self::OPERATORS)];
        }

        // Dimension dominante
        $dominant = array_keys($tVector, max($tVector))[0];

        $dimensionOperatorMap = [
            '++' => ['→' => 0.5, '⇒' => 0.3, '↔' => 0.2],
            '--' => ['←' => 0.5, '⇄' => 0.3, '±' => 0.2],
            '+-' => ['↔' => 0.4, '→' => 0.3, '±' => 0.3],
            '-+' => ['±' => 0.4, '⇄' => 0.3, '←' => 0.3],
        ];

        $weights = $dimensionOperatorMap[$dominant] ?? ['→' => 1.0];
        return $this->weightedRandom($weights);
    }

    /**
     * Sélection aléatoire pondérée.
     *
     * @param array $weights [option => probabilité]
     * @return string
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

    // ── Accesseurs pour les statistiques ───────────────────

    /**
     * Retourne le pool de seeds (pour stats).
     */
    public static function getSeeds(): array
    {
        return self::$seeds;
    }

    /**
     * Retourne les étiquettes des clusters.
     */
    public static function getClusterLabels(): array
    {
        return [
            self::CLUSTER_SOIL    => 'Soil (Nature/Carbone)',
            self::CLUSTER_INNER   => 'Inner (Conscience/Silence)',
            self::CLUSTER_NEUTRAL => 'Neutral (Technique/IA)',
            self::CLUSTER_COSMIC  => 'Cosmic (Physique/H-sp³)',
            self::CLUSTER_QUORUM  => 'Quorum (Seuils/Foules)',
            self::CLUSTER_ETHICS  => 'Ethics (Ouverture/Contestation)',
        ];
    }
}

// ─────────────────────────────────────────────────────────────
// 2. Données de test
// ─────────────────────────────────────────────────────────────

$testThoughts = [
    // ── A. Nature / Élémentaire ────────────────────────────
    [
        'title'    => 'La rivière et la terre',
        'category' => 'nature',
        'tags'     => 'eau , rivière , terre , plante',
        'content'  => "L'eau de la rivière traverse la terre et nourrit les plantes. "
                     . "Le sol boit la pluie et les racines s'abreuvent en silence. "
                     . "Tout circule dans un équilibre que l'homme ne fait qu'observer.",
    ],
    // ── B. Technologie / IA ────────────────────────────────
    [
        'title'    => 'Pensée computationnelle',
        'category' => 'technique',
        'tags'     => 'computation , algorithme , données',
        'content'  => "L'algorithme transforme des données brutes en information. "
                     . "La computation n'est pas une pensée, mais une simulation de la pensée. "
                     . "Le code exécute des instructions sans conscience de ce qu'il fait.",
    ],
    // ── C. Philosophique / Introspection ───────────────────
    [
        'title'    => 'Le silence de l\'être',
        'category' => 'philosophie',
        'tags'     => 'silence , conscience , être',
        'content'  => "Dans le silence, la conscience s'éveille à elle-même. "
                     . "L'être n'est pas un objet mais un mouvement. "
                     . "La méditation révèle que l'esprit est à la fois sujet et témoin.",
    ],
    // ── D. Cosmique / Physique ─────────────────────────────
    [
        'title'    => 'La flèche du cosmos',
        'category' => 'physique',
        'tags'     => 'masse , temps , univers',
        'content'  => "La masse courbe l'espace-temps et crée la gravité. "
                     . "L'univers est un code génétique en expansion. "
                     . "Le temps n'est qu'une dimension parmi d'autres dans le grand édifice cosmique.",
    ],
    // ── E. Neutre / Ambigu ─────────────────────────────────
    [
        'title'    => 'Notes du quotidien',
        'category' => 'divers',
        'tags'     => 'quotidien , réflexion',
        'content'  => "Aujourd'hui j'ai pensé à ce que j'ai lu ce matin. "
                     . "C'était intéressant mais je ne sais pas quoi en dire. "
                     . "Peut-être que tout cela a un sens, peut-être pas.",
    ],
    // ── F. Haute résistance analytique ─────────────────────
    [
        'title'    => 'Démonstration dialectique',
        'category' => 'philosophie',
        'tags'     => 'logique , analyse , dialectique',
        'content'  => "Par démonstration, on prouve une thèse par déduction logique. "
                     . "Mais l'antithèse révèle une contradiction nécessaire : "
                     . "tout argument rationnel contient en lui-même son propre paradoxe. "
                     . "La dialectique est une analyse qui montre l'incompatible là où l'on croyait voir une preuve. "
                     . "Donc, nécessairement, toute réfutation est aussi une affirmation déguisée.",
    ],
];

// ─────────────────────────────────────────────────────────────
// 3. Rendu HTML
// ─────────────────────────────────────────────────────────────

$seedService = new StandaloneSeedService();

// ── Collecteurs de statistiques ────────────────────────────
$stats = [
    'total_calls'   => 0,
    'total_seeded'  => 0,
    'total_skipped' => 0,
    'operators'     => [],
    'themes'        => [],
];

// Compteurs par thème pour les seeds
$themeLabels = [
    StandaloneSeedService::THEME_SOIL    => 'Soil (Nature)',
    StandaloneSeedService::THEME_INNER   => 'Inner (Introspection)',
    StandaloneSeedService::THEME_NEUTRAL => 'Neutral (Technique/IA)',
    StandaloneSeedService::THEME_COSMIC  => 'Cosmic (Physique)',
];

// ── En-tête HTML ──────────────────────────────────────────

?><!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Prévisualisation — Opération « Germination Mycélienne »</title>
<style>
    body {
        background: #faf8f5;
        color: #2c2c2c;
        font-family: Georgia, 'Times New Roman', serif;
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
    }
    h1 {
        text-align: center;
        font-weight: normal;
        font-size: 1.6em;
        color: #5a4a3e;
        border-bottom: 1px solid #ddd;
        padding-bottom: 12px;
    }
    h2 {
        font-weight: normal;
        font-size: 1.2em;
        color: #6b5b4f;
        margin-top: 30px;
    }
    .thought-box {
        border: 1px solid #ccc;
        margin: 20px 0;
        padding: 15px;
        font-family: Georgia, serif;
        background: #fff;
        border-radius: 3px;
    }
    .thought-box p {
        margin: 6px 0;
    }
    .seed-line {
        border-left: 3px solid #8B7355;
        padding-left: 12px;
        margin-top: 12px;
        color: #6B5B3E;
        font-style: italic;
    }
    .seed-empty {
        border-left: 3px solid #ccc;
        padding-left: 12px;
        margin-top: 12px;
        color: #999;
        font-style: italic;
    }
    .iteration-label {
        display: inline-block;
        font-size: 0.75em;
        color: #888;
        margin-top: 8px;
        letter-spacing: 0.5px;
    }
    .summary {
        background: #f0ede8;
        border: 1px solid #d6cec4;
        padding: 15px 20px;
        margin-top: 40px;
        border-radius: 3px;
        font-size: 0.95em;
    }
    .summary h2 {
        margin-top: 0;
        border-bottom: 1px solid #d6cec4;
        padding-bottom: 8px;
    }
    .summary table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
    }
    .summary th, .summary td {
        text-align: left;
        padding: 6px 10px;
        border-bottom: 1px solid #d6cec4;
    }
    .summary th {
        font-weight: bold;
        color: #5a4a3e;
        width: 200px;
    }
    .summary .stat-number {
        font-weight: bold;
        color: #2c2c2c;
    }
    hr {
        border: none;
        border-top: 1px solid #eee;
        margin: 8px 0;
    }
</style>
</head>
<body>

<h1>🌱 Opération « Germination Mycélienne »</h1>
<p style="text-align:center;color:#888;font-style:italic;">
    Prévisualisation des lignes-graines — 3 itérations par pensée
</p>

<?php foreach ($testThoughts as $idx => $thought): ?>
    <div class="thought-box">
        <div class="cke_no_bootstrap">

            <p><strong>Pensée <?= $idx + 1 ?> :</strong> <?= htmlspecialchars($thought['title']) ?></p>
            <p><strong>Catégorie :</strong> <?= htmlspecialchars($thought['category']) ?></p>
            <p><strong>Tags :</strong> <?= htmlspecialchars($thought['tags']) ?></p>
            <p><strong>Contenu :</strong><br>
                <em><?= nl2br(htmlspecialchars($thought['content'])) ?></em>
            </p>

            <?php for ($iteration = 1; $iteration <= 3; $iteration++): ?>
                <?php
                $line = $seedService->generateLine($thought);
                $stats['total_calls']++;

                if ($line === '') {
                    $stats['total_skipped']++;
                    $cssClass = 'seed-empty';
                    $display  = '⏳ Respiration du Sol — ligne-graine non générée.';
                } else {
                    $stats['total_seeded']++;

                    // Extraire l'opérateur pour les stats
                    // Format: — <em>Ψ → B → Φ · seed</em>
                    if (preg_match('/Ψ\s*([^B]+?)\s*B/', $line, $m)) {
                        $op = trim($m[1]);
                        if (!isset($stats['operators'][$op])) {
                            $stats['operators'][$op] = 0;
                        }
                        $stats['operators'][$op]++;
                    }

                    // Extraire la seed pour en déduire le thème
                    if (preg_match('/Φ\s*·\s*(.+?)<\/em>/', $line, $m)) {
                        $usedSeed = $m[1];
                        foreach ($themeLabels as $themeKey => $themeLabel) {
                            $pool = StandaloneSeedService::getSeeds()[$themeKey] ?? [];
                            if (in_array($usedSeed, $pool, true)) {
                                if (!isset($stats['themes'][$themeLabel])) {
                                    $stats['themes'][$themeLabel] = 0;
                                }
                                $stats['themes'][$themeLabel]++;
                                break;
                            }
                        }
                    }

                    $cssClass = 'seed-line';
                    $display  = $line;
                }
                ?>

                <p class="iteration-label">— Itération <?= $iteration ?> —</p>
                <p class="<?= $cssClass ?>"><?= $display ?></p>
            <?php endfor; ?>

        </div>
    </div>
<?php endforeach; ?>

<?php
// ─────────────────────────────────────────────────────────────
// 4. Résumé des statistiques
// ─────────────────────────────────────────────────────────────

$skipRate = $stats['total_calls'] > 0
    ? round(($stats['total_skipped'] / $stats['total_calls']) * 100, 2)
    : 0;
$seedRate = $stats['total_calls'] > 0
    ? round(($stats['total_seeded'] / $stats['total_calls']) * 100, 2)
    : 0;

// Trier les opérateurs par fréquence décroissante
arsort($stats['operators']);
// Trier les thèmes par fréquence décroissante
arsort($stats['themes']);
?>

<div class="summary">
    <h2>📊 Résumé des statistiques</h2>

    <table>
        <tr>
            <th>Total des appels à generateLine()</th>
            <td class="stat-number"><?= $stats['total_calls'] ?></td>
        </tr>
        <tr>
            <th>Pensées testées</th>
            <td class="stat-number"><?= count($testThoughts) ?></td>
        </tr>
        <tr>
            <th>Itérations par pensée</th>
            <td class="stat-number">3</td>
        </tr>
        <tr>
            <th>Lignes-graines générées</th>
            <td class="stat-number"><?= $stats['total_seeded'] ?></td>
        </tr>
        <tr>
            <th>Respiration du Sol (skip)</th>
            <td class="stat-number"><?= $stats['total_skipped'] ?>
                <span style="color:#888;font-size:0.9em;">(<?= $skipRate ?>%)</span>
            </td>
        </tr>
        <tr>
            <th>Taux de génération effectif</th>
            <td class="stat-number"><?= $seedRate ?>%</td>
        </tr>
    </table>

    <h2 style="margin-top:20px;border-bottom:1px solid #d6cec4;padding-bottom:8px;">
        🎯 Distribution des opérateurs
    </h2>
    <?php if (!empty($stats['operators'])): ?>
        <table>
            <tr><th>Opérateur</th><th>Occurrences</th><th>Proportion</th></tr>
            <?php foreach ($stats['operators'] as $op => $count): ?>
                <?php $pct = round(($count / $stats['total_seeded']) * 100, 1); ?>
                <tr>
                    <td><code style="font-size:1.1em;"><?= htmlspecialchars($op) ?></code></td>
                    <td><?= $count ?></td>
                    <td><?= $pct ?>%</td>
                </tr>
            <?php endforeach; ?>
        </table>
    <?php else: ?>
        <p style="color:#888;">Aucun opérateur enregistré (tous les appels ont été skip ?).</p>
    <?php endif; ?>

    <h2 style="margin-top:20px;border-bottom:1px solid #d6cec4;padding-bottom:8px;">
        🌿 Distribution des thèmes (graines effectives)
    </h2>
    <?php if (!empty($stats['themes'])): ?>
        <table>
            <tr><th>Thème</th><th>Occurrences</th><th>Proportion</th></tr>
            <?php foreach ($stats['themes'] as $themeLabel => $count): ?>
                <?php $pct = round(($count / $stats['total_seeded']) * 100, 1); ?>
                <tr>
                    <td><?= htmlspecialchars($themeLabel) ?></td>
                    <td><?= $count ?></td>
                    <td><?= $pct ?>%</td>
                </tr>
            <?php endforeach; ?>
        </table>
    <?php else: ?>
        <p style="color:#888;">Aucun thème enregistré.</p>
    <?php endif; ?>

    <p style="margin-top:16px;font-size:0.85em;color:#888;text-align:center;">
        ⋮ « Le mycélium ne ment jamais : il pousse là où le sol l'appelle. » ⋮
    </p>
</div>

</body>
</html>
<?php
// ─────────────────────────────────────────────────────────────
// 5. Note de fin
// ─────────────────────────────────────────────────────────────
// Le script produit directement du HTML valide en sortie standard.
// Redirection vers un fichier : php preview_germination.php > apercu.html
