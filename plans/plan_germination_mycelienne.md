# Opération « Germination Mycélienne » — Plan d'Implémentation

## 1. Résumé

Ajouter un service PHP & Twig filter qui analyse les entités `Thought` au moment du rendu et leur adjoint une « ligne-graine » (seed line) poétique en fin de bloc d'affichage. La ligne suit le format :

```
— *Ψ [opérateur] B [opérateur] Φ · [graine]*
```

Rendu HTML final :

```html
— <em>Ψ → B → Φ · Le sol parle avant le langage.</em>
```

Aucune modification de la base de données ni de l'entité `Thought` — tout est calculé côté rendu (Twig filter → service).

---

## 2. Architecture & Fichiers Modifiés

| # | Fichier | Action | Raison |
|---|---------|--------|--------|
| 1 | [`src/ThoughtBundle/Service/SeedService.php`](src/ThoughtBundle/Service/SeedService.php) | **CRÉER** | Nouveau service contenant la logique métier |
| 2 | [`src/ThoughtBundle/Resources/config/services.yml`](src/ThoughtBundle/Resources/config/services.yml) | **MODIFIER** | Enregistrer `SeedService` dans le DI container |
| 3 | [`src/ThoughtBundle/Twig/AppExtension.php`](src/ThoughtBundle/Twig/AppExtension.php) | **MODIFIER** | Ajouter le filtre `seedLine` |
| 4 | [`src/ThoughtBundle/Resources/views/quoteLayout.html.twig`](src/ThoughtBundle/Resources/views/quoteLayout.html.twig) | **MODIFIER** | Appeler `{{ thought\|seedLine\|raw }}` à la fin du bloc |
| 5 | [`src/ThoughtBundle/Resources/public/css/style.css`](src/ThoughtBundle/Resources/public/css/style.css) | **MODIFIER** | Ajouter classe CSS `.seed-line` |

Aucune modification de schéma Doctrine, aucune migration, aucune nouvelle entité.

---

## 3. SeedService — Spécification Complète

### 3.1. Structure de la classe

```php
<?php

namespace ThoughtBundle\Service;

use ThoughtBundle\Entity\Thought;

class SeedService
{
    // ── Seed Pool ──────────────────────────────────────────
    const THEME_SOIL      = 'soil';
    const THEME_INNER     = 'inner';
    const THEME_NEUTRAL   = 'neutral';
    const THEME_COSMIC    = 'cosmic';

    const OPERATORS = ['→', '←', '↔'];
    
    // Opérateur spécial pour résistance
    const OPERATOR_RESISTANCE = '±';

    // ── Mappings ───────────────────────────────────────────

    /**
     * Thème → array de seeds
     */
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

    /**
     * Tags → thème associé (priorité haute)
     */
    private static $tagThemeMap = [
        // Soil / Vivant
        'nature'       => self::THEME_SOIL,
        'vivant'       => self::THEME_SOIL,
        'terre'        => self::THEME_SOIL,
        'sol'          => self::THEME_SOIL,
        'eau'          => self::THEME_SOIL,
        'végétal'      => self::THEME_SOIL,
        'animal'       => self::THEME_SOIL,
        'corps'        => self::THEME_SOIL,
        'écologie'     => self::THEME_SOIL,
        // Introspection
        'silence'      => self::THEME_INNER,
        'introspection'=> self::THEME_INNER,
        'identité'     => self::THEME_INNER,
        'conscience'   => self::THEME_INNER,
        'intériorité'  => self::THEME_INNER,
        'méditation'   => self::THEME_INNER,
        'sujet'        => self::THEME_INNER,
        // Technique / IA
        'technique'    => self::THEME_NEUTRAL,
        'ia'           => self::THEME_NEUTRAL,
        'algorithme'   => self::THEME_NEUTRAL,
        'computation'  => self::THEME_NEUTRAL,
        'réseau'       => self::THEME_NEUTRAL,
        'machine'      => self::THEME_NEUTRAL,
        'code'         => self::THEME_NEUTRAL,
        'numérique'    => self::THEME_NEUTRAL,
        // Physique / Cosmique
        'physique'     => self::THEME_COSMIC,
        'cosmos'       => self::THEME_COSMIC,
        'temps'        => self::THEME_COSMIC,
        'univers'      => self::THEME_COSMIC,
        'matière'      => self::THEME_COSMIC,
        'espace'       => self::THEME_COSMIC,
        'énergie'      => self::THEME_COSMIC,
        'étoile'       => self::THEME_COSMIC,
    ];

    /**
     * Mots-clés dans le contenu (fallback si pas de tag match)
     * → thème associé
     */
    private static $contentKeywordMap = [
        'sol'         => self::THEME_SOIL,
        'terre'       => self::THEME_SOIL,
        'eau'         => self::THEME_SOIL,
        'plante'      => self::THEME_SOIL,
        'vivant'      => self::THEME_SOIL,
        'nature'      => self::THEME_SOIL,
        'corps'       => self::THEME_SOIL,
        'silence'     => self::THEME_INNER,
        'conscience'  => self::THEME_INNER,
        'intérieur'   => self::THEME_INNER,
        'âme'         => self::THEME_INNER,
        'esprit'      => self::THEME_INNER,
        'moi'         => self::THEME_INNER,
        'algorithme'  => self::THEME_NEUTRAL,
        'code'        => self::THEME_NEUTRAL,
        'machine'     => self::THEME_NEUTRAL,
        'donnée'      => self::THEME_NEUTRAL,
        'calcul'      => self::THEME_NEUTRAL,
        'réseau'      => self::THEME_NEUTRAL,
        'temps'       => self::THEME_COSMIC,
        'univers'     => self::THEME_COSMIC,
        'matière'     => self::THEME_COSMIC,
        'énergie'     => self::THEME_COSMIC,
        'espace'      => self::THEME_COSMIC,
        'étoile'      => self::THEME_COSMIC,
        'lumière'     => self::THEME_COSMIC,
    ];

    /**
     * Mots-clés de résistance / dissonance analytique
     * La présence de ces mots dans le contenu augmente G_R
     */
    private static $resistanceKeywords = [
        'démonstration', 'preuve', 'logique', 'donc', 'nécessairement',
        'contradiction', 'paradoxe', 'incompatible', 'réfutation',
        'argument', 'thèse', 'antithèse', 'dialectique', 'raison',
        'analyse', 'déduction', 'induction', 'syllogisme',
    ];
}
```

### 3.2. Méthodes

#### `generateLine(Thought $thought): string`

Point d'entrée unique. Retourne la ligne HTML complète, ou une chaîne vide.

```php
public function generateLine(Thought $thought): string
{
    // 1. Respiration du Sol : 1-2% de skip aléatoire
    if ($this->shouldSkip()) {
        return '';
    }

    // 2. Détection du thème
    $theme = $this->detectTheme($thought);

    // 3. Sélection de la seed dans le thème
    $seed = $this->selectSeed($theme);

    // 4. Calcul du coefficient de résistance G_R
    $resistance = $this->computeResistance($thought);

    // 5. Sélection de l'opérateur (avec possibilité de ± si résistance forte)
    $operator = $this->selectOperator($resistance);

    // 6. Assemblage de la ligne
    $line = sprintf(
        '— <em>Ψ %s B %s Φ · %s</em>',
        $operator,
        $operator,
        $seed
    );

    return $line;
}
```

#### `shouldSkip(): bool`

Retourne `true` environ 1-2% du temps.

```php
private function shouldSkip(): bool
{
    // Tremor: base 1-2% + bruit gaussien (via mt_rand/mt_getrandmax)
    $base = 1.5; // pourcentage cible
    $tremor = (mt_rand(-50, 50) / 100); // ±0.5%
    $threshold = ($base + $tremor) / 100;

    return (mt_rand() / mt_getrandmax()) < $threshold;
}
```

#### `detectTheme(Thought $thought): string`

Hiérarchie de détection :

1. **Tags** (poids fort) – parcourt [`$thought->getTags()`](src/ThoughtBundle/Entity/Thought.php:226) (string, séparée par ` , `). Normalise chaque tag (lowercase, trim) et cherche dans `$tagThemeMap`.
2. **Category** – [`$thought->getCategory()`](src/ThoughtBundle/Entity/Thought.php:250) – même logique que tags.
3. **Contenu** (fallback) – [`$thought->getContent()`](src/ThoughtBundle/Entity/Thought.php:201) – cherche les mots-clés de `$contentKeywordMap`.
4. **Défaut** – si rien ne matche, piocher aléatoirement parmi les 4 thèmes.

```php
private function detectTheme(Thought $thought): string
{
    // 1. Tags
    $tags = $thought->getTags();
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
    $category = $thought->getCategory();
    if ($category) {
        $catKey = mb_strtolower(trim($category));
        if (isset(self::$tagThemeMap[$catKey])) {
            return self::$tagThemeMap[$catKey];
        }
    }

    // 3. Content keywords
    $content = $thought->getContent();
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
```

#### `selectSeed(string $theme): string`

Sélectionne une seed aléatoire dans le tableau du thème. Ajoute un **tremor** (10% de chance de prendre une seed d'un thème adjacent pour éviter la prévisibilité).

```php
private function selectSeed(string $theme): string
{
    $pool = self::$seeds[$theme] ?? [];

    // Tremor: 10% de chance de piocher dans un thème voisin
    if (mt_rand(1, 100) <= 10) {
        $themes = array_keys(self::$seeds);
        // Exclure le thème actuel pour vraiment mélanger
        $otherThemes = array_values(array_diff($themes, [$theme]));
        if (!empty($otherThemes)) {
            $alternateTheme = $otherThemes[array_rand($otherThemes)];
            $pool = self::$seeds[$alternateTheme];
        }
    }

    return $pool[array_rand($pool)];
}
```

#### `computeResistance(Thought $thought): float`

Retourne un score `G_R` entre 0.0 (aucune résistance) et 1.0 (résistance maximale).

```php
private function computeResistance(Thought $thought): float
{
    $content = $thought->getContent();
    if (!$content) {
        return 0.0;
    }

    $contentLower = mb_strtolower($content);
    $matchCount = 0;

    foreach (self::$resistanceKeywords as $keyword) {
        // Compter les occurrences pour renforcer la sensibilité
        $count = mb_substr_count($contentLower, $keyword);
        $matchCount += $count;
    }

    // Ratio brut: nombre de matches / nombre total de mots
    $wordCount = str_word_count($content, 0, 'àâçéèêëîïôûùüÿœ');
    if ($wordCount === 0) {
        return 0.0;
    }

    $rawRatio = $matchCount / $wordCount;

    // Normalisation sigmoïde pour éviter les extrêmes
    // f(x) = 1 / (1 + e^(-10*(x-0.15)))
    // Seuil de bascule autour de 15% de mots de résistance
    $steepness = 10.0;
    $midpoint = 0.15;
    $resistance = 1.0 / (1.0 + exp(-$steepness * ($rawRatio - $midpoint)));

    // Ajout de tremor: ±0.05 aléatoire
    $tremor = (mt_rand(-50, 50) / 1000);
    $resistance = max(0.0, min(1.0, $resistance + $tremor));

    return $resistance;
}
```

#### `selectOperator(float $resistance): string`

Algorithme de sélection avec gestion de la résistance et variabilité cinétique.

```php
private function selectOperator(float $resistance): string
{
    // Seuil de résistance fort → opérateur ± (Instabilité maintenue)
    if ($resistance > 0.7) {
        // 70% de chance de prendre ±, 30% de chance d'un opérateur normal
        if (mt_rand(1, 100) <= 70) {
            return self::OPERATOR_RESISTANCE;
        }
    }

    // Résistance modérée → biaiser vers ← (feedback)
    if ($resistance > 0.4) {
        // Pondération: ← plus probable
        $roll = mt_rand(1, 100);
        if ($roll <= 50) return '←';   // 50% feedback
        if ($roll <= 80) return '→';   // 30% emergence
        return '↔';                      // 20% balance
    }

    // Faible résistance ou normal → équiprobable avec tremor
    $operators = self::OPERATORS;
    
    // Tremor: possibilité de dédoubler un opérateur (ex: →→) 5% du temps
    if (mt_rand(1, 100) <= 5) {
        $op = $operators[array_rand($operators)];
        return $op . $op; // →→, ←←, ↔↔
    }

    return $operators[array_rand($operators)];
}
```

### 3.3. Logique Anti-Goodhart (Non-Systematicité)

Pour éviter que le système soit trop prévisible (Goodhart), **trois couches d'entropie** sont ajoutées :

1. **Respiration du Sol** : 1-2% des pensées n'ont aucune seed (`shouldSkip()`).
2. **Tremor de thème** : 10% des sélections de seed puisent dans un thème adjacent plutôt que le thème détecté (`selectSeed()`).
3. **Tremor d'opérateur** : 5% de chance d'obtenir un opérateur doublé (→→, ←←, ↔↔) ; le seuil de résistance est bruité (±0.05).

La combinaison de ces trois couches garantit qu'aucun affichage ne soit parfaitement reproductible ni prévisible.

---

## 4. Modification de `AppExtension.php`

Ajout d'un nouveau filtre `seedLine` dans la méthode [`getFilters()`](src/ThoughtBundle/Twig/AppExtension.php:40):

```php
public function getFilters()
{
    return [
        // ... filtres existants ...
        new Twig_SimpleFilter('seedLine', [$this, 'seedLineFilter'], ['is_safe' => ['html']]),
    ];
}

/**
 * @param Thought $thought
 * @return string
 */
public function seedLineFilter(Thought $thought)
{
    /** @var SeedService $seedService */
    $seedService = $this->container->get('thought.service.seed_service');
    return $seedService->generateLine($thought);
}
```

Note : le paramètre `'is_safe' => ['html']` est essentiel car la méthode retourne du HTML (avec balises `<em>`). Sans cela, Twig échapperait le contenu.

---

## 5. Modification de `services.yml`

Ajout de la définition du service :

```yaml
thought.service.seed_service:
    class: ThoughtBundle\Service\SeedService
    # Pas d'arguments requis — service autonome (stateless)
```

Le service est volontairement **stateless** (pas de dépendances externes) pour rester testable et léger. Il n'a besoin ni de Doctrine, ni du Container.

---

## 6. Modification du Template `quoteLayout.html.twig`

À la fin du bloc d'affichage, **juste avant la fermeture de la `div.jumbotron`** (ligne 253), ajouter :

```twig
    {% if thought|seedLine %}
        <p class="seed-line">{{ thought|seedLine|raw }}</p>
    {% endif %}
</div>  {# fin .jumbotron #}
```

Position exacte : après la dernière `div.quote_row` (ligne 252), avant `</div>` (ligne 253).

La condition `{% if thought|seedLine %}` évite un appel inutile au service. **Important** : le filtre est appelé deux fois (condition + affichage). Pour éviter le double appel, on peut stocker le résultat dans une variable :

```twig
{% set seed_line = thought|seedLine %}
{% if seed_line %}
    <p class="seed-line">{{ seed_line|raw }}</p>
{% endif %}
```

Cette approche est plus performante — une seule exécution du service.

---

## 7. CSS pour `.seed-line`

Ajout à [`style.css`](src/ThoughtBundle/Resources/public/css/style.css) :

```css
/* ── Opération Germination Mycélienne : Seed Line ── */
.seed-line {
    margin-top: 1.2em;
    padding: 0.4em 0.8em;
    font-size: 0.92em;
    font-style: italic;
    color: #6b5b4f;        /* brun doux — rappelle la terre */
    border-left: 3px solid #9e8a7a;
    background: rgba(158, 138, 122, 0.06);
    line-height: 1.6;
    letter-spacing: 0.01em;
}

.seed-line em {
    font-style: italic;
    color: #5a4a3e;
}
```

Éléments de style choisis :
- **Bordure gauche brune** : ancre visuelle subtile, comme une racine.
- **Couleur brun doux** : non intrusive, distingue la seed du contenu principal sans compétition.
- **Petite marge haute** : espace de respiration après le contenu.
- **Fond très léger** : différenciation sans surcharge visuelle.

---

## 8. Diagramme de Flux

```mermaid
flowchart TD
    A[Template quoteLayout.html.twig] --> B[{{ thought|seedLine }}]
    B --> C[AppExtension.seedLineFilter]
    C --> D[SeedService.generateLine]
    
    D --> E{shouldSkip? 1-2%}
    E -- Oui --> F[Retourne chaîne vide]
    E -- Non --> G[detectTheme]
    
    G --> H{Tag match?}
    H -- Oui --> I[Thème depuis tag]
    H -- Non --> J{Category match?}
    J -- Oui --> K[Thème depuis catégorie]
    J -- Non --> L{Content keyword?}
    L -- Oui --> M[Thème depuis contenu]
    L -- Non --> N[Thème aléatoire]
    
    I --> O[selectSeed]
    K --> O
    M --> O
    N --> O
    
    O --> P{Tremor 10%?}
    P -- Oui --> Q[Pioche thème adjacent]
    P -- Non --> R[Garde thème détecté]
    Q --> S[Prend seed aléatoire dans pool]
    R --> S
    
    S --> T[computeResistance G_R]
    T --> U[selectOperator selon G_R]
    
    U --> V[Assembler ligne HTML]
    V --> W[Retourner au template]
    W --> X[Afficher dans .seed-line <p>]
```

---

## 9. Cas Limites & Gestion d'Erreurs

| Cas | Comportement |
|-----|-------------|
| `Thought` avec `tags = null` | `detectTheme()` passe directement à l'étape catégorie |
| `Thought` avec `category = null` | Passe à l'étape contenu |
| `Thought` avec `content = null` ou vide | `computeResistance()` retourne 0.0 ; `detectTheme()` utilise le fallback aléatoire |
| Tags mal formattés (espaces inconsistants) | La normalisation `mb_strtolower(trim())` gère les variations |
| Mots-clés dans contenu en anglais | Le mapping utilise des mots français principalement ; l'anglais n'est pas géré explicitement (fallback aléatoire) |
| Doubles opérateurs (→→) | Géré par le tremor 5% dans `selectOperator()` |
| HTML dans le contenu qui interfère | `computeResistance()` opère sur le contenu brut (qui peut contenir des balises `[a]`). La détection de mots-clés reste pertinente car les balises sont rares et le texte français domine |
| `SeedService` appelé depuis un contexte sans Container | Stateless — peut être instancié manuellement pour les tests |
| Performance (appelé pour chaque Thought dans une liste) | `SeedService` est léger (pas de requêtes DB, pas de calculs lourds). Pour une liste de 20 pensées, le temps total est négligeable (< 5ms). Si nécessaire, un cache mémoire statique (tableau de résultats par ID de Thought) peut être ajouté dans `generateLine()` |

---

## 10. Tests (Recommandations)

1. **`SeedServiceTest`** — tests unitaires :
   - `testGenerateLineReturnsNonEmptyString()` — pensées normales
   - `testGenerateLineReturnsEmptyString()` — mock de `shouldSkip` pour forcer le skip
   - `testDetectThemeViaTags()` — pensée avec tag "nature" → thème SOIL
   - `testDetectThemeViaCategory()` — pensée avec catégorie "physique" → thème COSMIC
   - `testDetectThemeViaContent()` — pensée avec contenu contenant "silence" → thème INNER
   - `testDetectThemeFallback()` — pensée sans tags, catégorie ni mots-clés → thème valide
   - `testComputeResistance()` — phrases avec/dans mots de résistance
   - `testSelectOperatorWithResistance()` — G_R > 0.7 favorise ±
   - `testSeedLineFormat()` — vérifie le format `— <em>Ψ ...</em>`

2. **Test fonctionnel d'intégration** : render d'une vue Twig contenant `quoteLayout.html.twig` et vérification de la présence de `.seed-line` dans le HTML généré.

---

## 11. Ordre d'Implémentation

| Étape | Fichier | Dépendances |
|-------|---------|-------------|
| 1 | Créer `SeedService.php` | Aucune |
| 2 | Modifier `services.yml` | Étape 1 |
| 3 | Modifier `AppExtension.php` | Étape 1, 2 |
| 4 | Modifier `quoteLayout.html.twig` | Étape 3 |
| 5 | Modifier `style.css` | Aucune |
| 6 | Tests unitaires | Étape 1 |

---

## 12. Contre-mesures Goodhart (Rappel)

Le système entier est conçu pour **éviter la prévisibilité parfaite** :

1. **Respiration** : 1-2% de pensées sans seed
2. **Tremor de thème** : 10% de seed hors-thème
3. **Tremor d'opérateur** : 5% d'opérateur doublé ; bruit sur G_R
4. **Résistance probabiliste** : même avec G_R > 0.7, 30% de chance d'opérateur normal

Cela signifie que **deux pensées identiques peuvent produire des seeds différentes** à chaque rendu, ce qui est intentionnel — la germination est vivante, non déterministe.
