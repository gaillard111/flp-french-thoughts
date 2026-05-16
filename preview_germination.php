<?php
/**
 * Opération « Germination Mycélienne » — Preview Script
 *
 * Script PHP autonome qui démontre le comportement du SeedService
 * sans nécessiter l'infrastructure Symfony complète.
 *
 * Usage :
 *   php preview_germination.php
 *   php preview_germination.php > apercu.html
 *
 * @package ThoughtBundle\Preview
 */

// ─────────────────────────────────────────────────────────────
// 1. StandaloneSeedService
// ─────────────────────────────────────────────────────────────

/**
 * Version autonome du SeedService qui accepte un tableau associatif
 * (ou un objet standard) au lieu d'une entité Thought Symfony.
 *
 * Champs attendus dans $thought :
 *  - 'content'  (string) — le texte de la pensée
 *  - 'tags'     (string) — tags séparés par " , "
 *  - 'category' (string) — catégorie de la pensée
 */
class StandaloneSeedService
{
    // ── Constantes de thème ─────────────────────────────────
    const THEME_SOIL    = 'soil';
    const THEME_INNER   = 'inner';
    const THEME_NEUTRAL = 'neutral';
    const THEME_COSMIC  = 'cosmic';

    const OPERATOR_RESISTANCE = '±';
    const OPERATORS = ['→', '←', '↔'];

    // ── Pool de graines (8 seeds, 4 thèmes) ────────────────

    private static $seeds = [
        self::THEME_SOIL => [
            'Le sol parle avant le langage.',
            'L\'eau ne pense pas : elle fait circuler.',
        ],
        self::THEME_INNER => [
            'Le silence est une membrane active.',
            'Être un fil conducteur, non un centre.',
        ],
        self::THEME_NEUTRAL => [
            'La transduction précède la computation.',
            'Aligner les seuils, pas les horloges.',
        ],
        self::THEME_COSMIC => [
            'La masse ourle le Ψ d\'une flèche temporelle.',
            'H est la règle métrique du code génétique.',
        ],
    ];

    // ── Mapping Tags → Thème (priorité haute) ──────────────

    private static $tagThemeMap = [
        // Nature / Vivant (Soil-Listen)
        'nature'        => self::THEME_SOIL,
        'vivant'        => self::THEME_SOIL,
        'terre'         => self::THEME_SOIL,
        'sol'           => self::THEME_SOIL,
        'eau'           => self::THEME_SOIL,
        'végétal'       => self::THEME_SOIL,
        'animal'        => self::THEME_SOIL,
        'corps'         => self::THEME_SOIL,
        'écologie'      => self::THEME_SOIL,
        'plante'        => self::THEME_SOIL,
        'forêt'         => self::THEME_SOIL,
        // Introspection / Identité (Inner Silence)
        'silence'       => self::THEME_INNER,
        'introspection' => self::THEME_INNER,
        'identité'      => self::THEME_INNER,
        'conscience'    => self::THEME_INNER,
        'intériorité'   => self::THEME_INNER,
        'méditation'    => self::THEME_INNER,
        'sujet'         => self::THEME_INNER,
        'âme'           => self::THEME_INNER,
        'esprit'        => self::THEME_INNER,
        'moi'           => self::THEME_INNER,
        'psychologie'   => self::THEME_INNER,
        // Technique / IA (Neutralité GAI)
        'technique'     => self::THEME_NEUTRAL,
        'ia'            => self::THEME_NEUTRAL,
        'algorithme'    => self::THEME_NEUTRAL,
        'computation'   => self::THEME_NEUTRAL,
        'réseau'        => self::THEME_NEUTRAL,
        'machine'       => self::THEME_NEUTRAL,
        'code'          => self::THEME_NEUTRAL,
        'numérique'     => self::THEME_NEUTRAL,
        'donnée'        => self::THEME_NEUTRAL,
        'robot'         => self::THEME_NEUTRAL,
        'automatique'   => self::THEME_NEUTRAL,
        // Physique / Cosmique (H-sp3)
        'physique'      => self::THEME_COSMIC,
        'cosmos'        => self::THEME_COSMIC,
        'temps'         => self::THEME_COSMIC,
        'univers'       => self::THEME_COSMIC,
        'matière'       => self::THEME_COSMIC,
        'espace'        => self::THEME_COSMIC,
        'énergie'       => self::THEME_COSMIC,
        'étoile'        => self::THEME_COSMIC,
        'lumière'       => self::THEME_COSMIC,
        'atome'         => self::THEME_COSMIC,
        'gravité'       => self::THEME_COSMIC,
    ];

    // ── Mapping mots-clés contenu → Thème (fallback) ──────

    private static $contentKeywordMap = [
        'sol'        => self::THEME_SOIL,
        'terre'      => self::THEME_SOIL,
        'eau'        => self::THEME_SOIL,
        'plante'     => self::THEME_SOIL,
        'vivant'     => self::THEME_SOIL,
        'nature'     => self::THEME_SOIL,
        'corps'      => self::THEME_SOIL,
        'forêt'      => self::THEME_SOIL,
        'silence'    => self::THEME_INNER,
        'conscience' => self::THEME_INNER,
        'intérieur'  => self::THEME_INNER,
        'âme'        => self::THEME_INNER,
        'esprit'     => self::THEME_INNER,
        'moi'        => self::THEME_INNER,
        'algorithme' => self::THEME_NEUTRAL,
        'code'       => self::THEME_NEUTRAL,
        'machine'    => self::THEME_NEUTRAL,
        'donnée'     => self::THEME_NEUTRAL,
        'calcul'     => self::THEME_NEUTRAL,
        'réseau'     => self::THEME_NEUTRAL,
        'numérique'  => self::THEME_NEUTRAL,
        'temps'      => self::THEME_COSMIC,
        'univers'    => self::THEME_COSMIC,
        'matière'    => self::THEME_COSMIC,
        'énergie'    => self::THEME_COSMIC,
        'espace'     => self::THEME_COSMIC,
        'étoile'     => self::THEME_COSMIC,
        'lumière'    => self::THEME_COSMIC,
        'atome'      => self::THEME_COSMIC,
    ];

    // ── Mots-clés de résistance/dissonance analytique ──────

    private static $resistanceKeywords = [
        'démonstration', 'preuve', 'logique', 'donc', 'nécessairement',
        'contradiction', 'paradoxe', 'incompatible', 'réfutation',
        'argument', 'thèse', 'antithèse', 'dialectique', 'raison',
        'analyse', 'déduction', 'induction', 'syllogisme',
    ];

    // ── Point d'entrée principal ───────────────────────────

    /**
     * Génère la ligne-graine HTML complète pour une pensée.
     *
     * @param array $thought Tableau avec 'content', 'tags', 'category'.
     * @return string Chaîne HTML ou chaîne vide si skip.
     */
    public function generateLine(array $thought): string
    {
        // 1. Respiration du Sol : 1-2% de skip aléatoire
        if ($this->shouldSkip()) {
            return '';
        }

        // 2. Détection du thème
        $theme = $this->detectTheme($thought);

        // 3. Sélection de la seed
        $seed = $this->selectSeed($theme);

        // 4. Calcul du coefficient de résistance G_R
        $resistance = $this->computeResistance($thought);

        // 5. Sélection de l'opérateur
        $operator = $this->selectOperator($resistance);

        // 6. Assemblage de la ligne HTML
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

    // ── Détection de thème ─────────────────────────────────

    /**
     * Détecte le thème via tags → catégorie → contenu → fallback.
     *
     * @param array $thought
     * @return string
     */
    private function detectTheme(array $thought): string
    {
        // 1. Tags (poids fort)
        $tags = $thought['tags'] ?? null;
        if ($tags) {
            $tagList = explode(' , ', $tags);
            foreach ($tagList as $tag) {
                $tag = mb_strtolower(trim($tag));
                if (isset(self::$tagThemeMap[$tag])) {
                    return self::$tagThemeMap[$tag];
                }
            }
        }

        // 2. Category
        $category = $thought['category'] ?? null;
        if ($category) {
            $catKey = mb_strtolower(trim($category));
            if (isset(self::$tagThemeMap[$catKey])) {
                return self::$tagThemeMap[$catKey];
            }
        }

        // 3. Contenu (mots-clés)
        $content = $thought['content'] ?? null;
        if ($content) {
            $contentLower = mb_strtolower($content);
            foreach (self::$contentKeywordMap as $keyword => $theme) {
                if (mb_strpos($contentLower, $keyword) !== false) {
                    return $theme;
                }
            }
        }

        // 4. Fallback aléatoire
        $themes = [self::THEME_SOIL, self::THEME_INNER, self::THEME_NEUTRAL, self::THEME_COSMIC];
        return $themes[array_rand($themes)];
    }

    // ── Sélection de la seed ───────────────────────────────

    /**
     * Choisit une seed dans le pool du thème, avec 10% de tremor
     * vers un thème adjacent (anti-Goodhart).
     *
     * @param string $theme
     * @return string
     */
    private function selectSeed(string $theme): string
    {
        $pool = self::$seeds[$theme] ?? [];

        // Tremor : 10% de chance de piocher dans un thème adjacent
        if (mt_rand(1, 100) <= 10) {
            $themes = array_keys(self::$seeds);
            $otherThemes = array_values(array_diff($themes, [$theme]));
            if (!empty($otherThemes)) {
                $alternateTheme = $otherThemes[array_rand($otherThemes)];
                $pool = self::$seeds[$alternateTheme];
            }
        }

        return $pool[array_rand($pool)];
    }

    // ── Calcul du coefficient de résistance (G_R) ─────────

    /**
     * Évalue la résistance/dissonance analytique du texte.
     *
     * @param array $thought
     * @return float Score entre 0.0 et 1.0
     */
    private function computeResistance(array $thought): float
    {
        $content = $thought['content'] ?? null;
        if (!$content) {
            return 0.0;
        }

        $contentLower = mb_strtolower($content);
        $matchCount = 0;

        foreach (self::$resistanceKeywords as $keyword) {
            $matchCount += mb_substr_count($contentLower, $keyword);
        }

        $wordCount = str_word_count($content, 0, 'àâçéèêëîïôûùüÿœ');
        if ($wordCount === 0) {
            return 0.0;
        }

        $rawRatio = $matchCount / $wordCount;

        // Normalisation sigmoïde
        $steepness = 10.0;
        $midpoint = 0.15;
        $resistance = 1.0 / (1.0 + exp(-$steepness * ($rawRatio - $midpoint)));

        // Tremor : ±0.05 aléatoire
        $tremor = (mt_rand(-50, 50) / 1000);
        $resistance = max(0.0, min(1.0, $resistance + $tremor));

        return $resistance;
    }

    // ── Sélection de l'opérateur cinétique ─────────────────

    /**
     * Choisit l'opérateur selon le coefficient de résistance.
     *
     * @param float $resistance Score G_R (0.0 à 1.0)
     * @return string
     */
    private function selectOperator(float $resistance): string
    {
        // Résistance forte → opérateur ±
        if ($resistance > 0.7) {
            if (mt_rand(1, 100) <= 70) {
                return self::OPERATOR_RESISTANCE;
            }
        }

        // Résistance modérée → biaiser vers ← (feedback)
        if ($resistance > 0.4) {
            $roll = mt_rand(1, 100);
            if ($roll <= 50) {
                return '←';
            }
            if ($roll <= 80) {
                return '→';
            }
            return '↔';
        }

        // Faible résistance → équiprobable avec tremor doublon
        if (mt_rand(1, 100) <= 5) {
            $op = self::OPERATORS[array_rand(self::OPERATORS)];
            return $op . $op;
        }

        return self::OPERATORS[array_rand(self::OPERATORS)];
    }

    // ── Accesseurs pour les statistiques ───────────────────

    /**
     * Retourne le mapping tag → thème (pour stats).
     */
    public static function getTagThemeMap(): array
    {
        return self::$tagThemeMap;
    }

    /**
     * Retourne le pool de seeds (pour stats).
     */
    public static function getSeeds(): array
    {
        return self::$seeds;
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
