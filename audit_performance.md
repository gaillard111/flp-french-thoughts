# Audit de Performance - Projet Symfony (flp-french-thoughts)

**Date de l'audit** : 19 mars 2026  
**Auditeur** : Roo (Assistant IA)  
**Objectif** : Identifier les goulots d'étranglement potentiels, les optimisations possibles pour améliorer les temps de réponse, la scalabilité, et l'expérience utilisateur.

---

## 1. Méthodologie

L'audit a été réalisé par analyse statique des fichiers de configuration, du code source (contrôleurs, services, commandes) et des assets. Les points examinés sont :

- Configuration des caches (Symfony, Doctrine, Twig)
- Gestion des assets (CSS, JS, images)
- Performances des contrôleurs et services (requêtes N+1, boucles, appels externes)
- Configuration Elasticsearch (mappings, analyzers)
- Configuration des logs (Monolog)
- Gestion des sessions
- Performances des commandes CLI

Aucun profiling en temps réel ni benchmark de charge n'a été effectué ; les conclusions sont basées sur les bonnes pratiques Symfony et les antipatterns détectés.

---

## 2. Résultats détaillés par catégorie

### 2.1 Cache

**Fichiers analysés** : [`app/config/config.yml`](app/config/config.yml), [`app/config/config_prod.yml`](app/config/config_prod.yml)

**État actuel** :
- Cache Doctrine : `auto_generate_proxy_classes` dépend de `%kernel.debug%` (OK).
- **Aucun cache de métadonnées, de requêtes ou de résultats n'est activé** en production (les lignes correspondantes dans `config_prod.yml` sont commentées).
- Cache de validation et de serializer non configurés.
- Twig : `debug` et `strict_variables` dépendent de `%kernel.debug%` ; le cache de template est géré automatiquement par Symfony (OK).

**Impact** :
- Augmentation du temps de réponse à chaque requête (compilation des métadonnées Doctrine, compilation des templates).
- Charge CPU supplémentaire sur le serveur.

**Recommandation** :
- Décommenter et configurer les caches APC/APCu (ou Redis) dans `config_prod.yml` :
```yaml
doctrine:
    orm:
        metadata_cache_driver: apc
        result_cache_driver: apc
        query_cache_driver: apc
framework:
    validation:
        cache: validator.mapping.cache.doctrine.apc
    serializer:
        cache: serializer.mapping.cache.apc
```

### 2.2 Assets (CSS, JS, images)

**Fichiers analysés** : [`src/ThoughtBundle/Resources/public/`](src/ThoughtBundle/Resources/public/), [`src/ThoughtBundle/Resources/views/layout.html.twig`](src/ThoughtBundle/Resources/views/layout.html.twig)

**État actuel** :
- Bootstrap, jQuery, Select2 chargés depuis CDN (bonne pratique).
- Fichiers CSS/JS propres au projet **non minifiés ni concaténés** (ex: `style.css`, `script.js`).
- **Double inclusion de jQuery** (ligne 29 et ligne 82 du layout) → risque de conflits et temps de chargement inutile.
- Aucune optimisation d'images (pas de compression, pas de lazy‑loading).
- Pas de mécanisme de versionning (hash) pour invalidation du cache navigateur.

**Impact** :
- Augmentation du temps de chargement des pages.
- Consommation de bande passante supérieure.

**Recommandation** :
- Activer Assetic (ou Webpack Encore) pour la concaténation et la minification.
- Supprimer la duplication de jQuery (conserver uniquement la version de Google CDN).
- Compresser les images existantes (outils comme `jpegoptim`, `pngquant`).
- Implémenter un système de cache‑bursting (versionnement des assets).

### 2.3 Contrôleurs et services

**Fichiers analysés** : plusieurs contrôleurs, notamment [`HomepageController.php`](src/ThoughtBundle/Controller/HomepageController.php), [`ThoughtPageController.php`](src/ThoughtBundle/Controller/ThoughtPageController.php), [`ChainController.php`](src/ThoughtBundle/Controller/ChainController.php)

**Problèmes identifiés** :

#### a) Requêtes N+1
- Dans `HomepageController::indexAction()` : boucle sur les pensées paginées, appel à `$em->getRepository(Comment::class)->getLastComments($thought)` pour chaque pensée → génère une requête supplémentaire par élément.
- Même pattern dans `ChainController::showAction()`.

**Impact** : Multiplication des requêtes SQL, dégradation significative lorsque le nombre d'éléments affichés augmente.

**Recommandation** : Utiliser des jointures DQL ou des requêtes optimisées avec `LEFT JOIN` pour récupérer les commentaires en une seule requête.

#### b) Boucles coûteuses dans les templates
- Plusieurs templates Twig incluent des boucles sur des collections sans pagination (ex: liste d'utilisateurs). Aucun problème critique détecté, mais vigilance recommandée.

#### c) Appels réseau synchrones
- **Aucun appel API externe** n'a été repéré dans le flux principal des contrôleurs (bon).

#### d) Opérations de calcul intensif
- Aucune opération CPU lourde détectée dans les contrôleurs audités.

### 2.4 Elasticsearch (FOSElastica)

**Fichier analysé** : [`app/config/fos_elastica.yml`](app/config/fos_elastica.yml)

**État actuel** :
- Mappings détaillés avec champs `multi_field` pour la recherche floue.
- Analysers personnalisés (`ngram_analyzer`, `without_preposition_analyzer`, etc.).
- Paramètres `edgeNGram` avec `min_gram:1`, `max_gram:40` (très large) → index potentiellement volumineux.

**Impact** :
- Taille d'index élevée, consommation mémoire accrue.
- Performances de recherche toujours correctes, mais peut être optimisée.

**Recommandation** :
- Réduire `max_gram` à 20 ou 25 pour limiter la taille des termes indexés.
- Vérifier que les analyzers correspondent bien aux besoins linguistiques (français).
- Surveiller la taille des indexes et les performances via Kibana/Elasticsearch monitoring.

### 2.5 Logs (Monolog)

**Fichier analysé** : [`app/config/config_prod.yml`](app/config/config_prod.yml) (lignes 16‑27)

**État actuel** :
- Handler `fingers_crossed` avec `action_level: error` (bon).
- Handler `nested` écrit dans un fichier avec **level: debug** → en production, tous les messages de niveau debug sont enregistrés.

**Impact** :
- Fichiers de logs très volumineux, I/O disque accru, risque de saturation de l'espace disque.

**Recommandation** :
- Changer le niveau du handler `nested` de `debug` à `error` (ou `warning`) :
```yaml
nested:
    type: stream
    path: '%kernel.logs_dir%/%kernel.environment%.log'
    level: error
```

### 2.6 Sessions

**Fichier analysé** : [`app/config/config.yml`](app/config/config.yml) (lignes 32‑34)

**État actuel** :
- `handler_id: ~` (utilisation du handler par défaut de PHP, généralement `files`).
- Aucune configuration de durée de vie personnalisée, pas de stockage externalisé.

**Impact** :
- En cas de montée en charge, le stockage fichier peut devenir un goulot d'étranglement (I/O disque).
- Pas de partage de sessions entre plusieurs serveurs (scalabilité horizontale impossible).

**Recommandation** :
- Migrer vers un stockage Redis ou base de données (Doctrine).
- Ajouter une durée de vie adaptée à l'utilisation :
```yaml
framework:
    session:
        handler_id: ~
        cookie_lifetime: 86400
        gc_maxlifetime: 86400
        save_path: '%kernel.project_dir%/var/sessions/%kernel.environment%'
```
- Pour Redis, installer `snc/redis-bundle` et configurer le handler `snc_redis.session.handler`.

### 2.7 Commandes CLI

**Fichiers analysés** : [`MailCommand.php`](src/ThoughtBundle/Command/MailCommand.php), [`RecommendThoughtCommand.php`](src/ThoughtBundle/Command/RecommendThoughtCommand.php)

**Problèmes identifiés** :
- **Chargement en mémoire de tous les utilisateurs** via `findAll()` → risque d'épuisement de la mémoire avec un grand nombre d'utilisateurs.
- Aucune pagination, pas de traitement par lots (batch).

**Impact** :
- Commande `throught:mail_command` peut planter si la table User dépasse la mémoire disponible.
- Temps d'exécution long et consommation mémoire élevée.

**Recommandation** :
- Utiliser la pagination Doctrine (`$repository->findBy([], [], $limit, $offset)`) ou un `BatchIterator`.
- Pour l'envoi d'emails massifs, envisager l'utilisation de la queue (RabbitMQ, Redis) avec découpage en jobs individuels.

---

## 3. Tableau synthétique des problèmes

| Catégorie | Problème | Impact | Priorité |
|-----------|---------|--------|----------|
| Cache | Caches Doctrine/validation/serializer désactivés | Temps de réponse accru, charge CPU | Haute |
| Assets | Fichiers CSS/JS non minifiés, double jQuery | Temps de chargement page | Moyenne |
| Assets | Images non compressées | Bande passante | Faible |
| Contrôleurs | Requêtes N+1 (commentaires) | Nombre de requêtes SQL multiplié | Haute |
| Elasticsearch | Taille des ngrams (max_gram:40) | Index volumineux | Moyenne |
| Logs | Niveau debug en production | Fichiers logs volumineux | Moyenne |
| Sessions | Stockage fichier par défaut | Scalabilité limitée | Moyenne |
| CLI | `findAll()` sur toute la table User | Risque mémoire | Haute |

**Priorité** : Haute = impact direct sur les performances perçues ; Moyenne = impact à moyen terme ; Faible = optimisation mineure.

---

## 4. Mesures d'optimisation prioritaires

1. **Activer les caches de production** (Doctrine, validation, serializer) – gain immédiat sur le temps de réponse.
2. **Corriger les requêtes N+1** dans `HomepageController` et `ChainController` – réduit le nombre de requêtes SQL.
3. **Modifier le niveau des logs** en production de `debug` à `error` – réduit l'I/O disque.
4. **Paginer les commandes CLI** (`MailCommand`, `RecommendThoughtCommand`) – évite les dépassements mémoire.
5. **Supprimer la double inclusion de jQuery** et minifier les assets propres.

---

## 5. Suggestions pour l'optimisation avancée

### Cache HTTP (Varnish / Reverse Proxy)
- Installer Varnish devant l'application pour mettre en cache les pages publiques (homepage, pages de contenu statique).
- Configurer les en‑têtes `Cache‑Control` et `Expires` dans les réponses Symfony.
- Utiliser `FOSHttpCacheBundle` pour une invalidation fine.

### Optimisation des bases de données
- Analyser les requêtes lentes avec un outil de profiling (Blackfire, New Relic).
- Ajouter des indexes sur les colonnes fréquemment filtrées (`thought.author`, `comment.thought_id`, etc.).
- Envisager la réplication en lecture (master‑slave) si la charge le justifie.

### Mise en cache des résultats Elasticsearch
- Cache des résultats de recherche fréquents (ex: suggestions, autocomplete) via Redis.
- Ajuster les paramètres de refresh d'Elasticsearch pour améliorer le débit d'indexation.

### Async & Queue
- Déporter l'envoi d'emails, la génération de PDF, les appels API externes dans une queue (RabbitMQ, Redis).
- Utiliser `RabbitMQBundle` ou `EnqueueBundle` pour gérer les jobs asynchrones.

---

## 6. Évaluation globale de la performance

**Note qualitative** : **Moyenne**

**Points forts** :
- Architecture Symfony propre, séparation des couches.
- Utilisation de bundles standard (FOSUser, SonataAdmin, KnpPaginator).
- Elasticsearch correctement intégré pour la recherche.
- CDN pour les bibliothèques front‑end.

**Points faibles** :
- Absence de cache de production (doctrine, validation, serializer).
- Requêtes N+1 non optimisées.
- Gestion des assets non optimisée.
- Logs trop verbeux en production.

**Potentiel d'amélioration** : **Élevé**. La mise en œuvre des recommandations prioritaires pourrait réduire les temps de réponse de 30 à 50 % et améliorer significativement la scalabilité.

---

## 7. Conclusion

L'audit a révélé plusieurs axes d'optimisation, certains simples à mettre en œuvre (activation de caches, correction de logs), d'autres demandant un peu plus de développement (correction des N+1, pagination des commandes).  
Il est recommandé de procéder par étapes, en commençant par les correctifs à fort impact et faible coût (cache, logs), puis d'attaquer les modifications de code (requêtes, assets).  
Une surveillance continue (APM, logs) permettra de valider les gains après chaque amélioration.

--- 

*Document généré automatiquement – pour toute question ou précision, contacter l'équipe technique.*