# Audit de sécurité applicative - Projet Symfony "flp-french-thoughts"

Date: 2026-03-19  
Auditeur: Roo (Debug Mode)  
Projet: c:/Users/Master/flp-french-thoughts

## Résumé exécutif

L'audit a identifié plusieurs vulnérabilités de sécurité applicative, dont certaines présentent un risque élevé. Les principales faiblesses résident dans la configuration de sécurité (hash des mots de passe faible, absence de protection CSRF sur certains formulaires, configuration de session non sécurisée), des vulnérabilités d'injection (SQL, XSS) potentielles dans les contrôleurs et repositories, des failles d'upload de fichiers non authentifié et non validé, ainsi que des erreurs de logique dans les voters de sécurité. Le niveau de risque global est **Élevé** en raison de la combinaison de vulnérabilités critiques et de la sensibilité des données (utilisateurs, contenu pédagogique).

## Détail des vulnérabilités

### 1. Configuration de sécurité (security.yml)

| Catégorie | Fichier/ligne | Description | Risque | Recommandation |
|-----------|---------------|-------------|--------|----------------|
| Hash des mots de passe faible | `app/config/security.yml:3` | L'encodeur utilise `sha512` sans coût, qui est vulnérable aux attaques par force brute (hash rapide). | Élevé | Remplacer par `bcrypt` ou `argon2i` avec un coût approprié (ex: `algorithm: bcrypt`, `cost: 12`). |
| Firewall trop permissif | `app/config/security.yml:28-36` | Le firewall `main` couvre `^/` mais ne définit pas de protection CSRF explicite pour toutes les routes. La protection CSRF est activée au niveau framework mais doit être vérifiée sur chaque formulaire. | Moyen | Vérifier que tous les formulaires utilisent `form_rest()` ou incluent manuellement le token CSRF. |
| Erreur dans les règles d'accès | `app/config/security.yml:45` | Double slash `^//teacher/` dans la règle d'access_control, pouvant entraîner un contournement de protection. | Faible | Corriger en `^/teacher/`. |
| Absence de `trusted_hosts` | `app/config/config.yml:30` | Aucune restriction sur les host headers, permettant des attaques d'injection de host. | Moyen | Définir `trusted_hosts` avec la liste des domaines autorisés (ex: `['^example\\.com$']`). |
| Absence de `trusted_proxies` | `app/config/config.yml:31` | Si l'application est derrière un reverse proxy, les headers X-Forwarded-* peuvent être falsifiés. | Moyen | Configurer `trusted_proxies` avec les IPs des proxies. |
| Secret faible par défaut | `app/config/parameters.yml.dist:19` | Le secret par défaut `ThisTokenIsNotSoSecretChangeIt` est présent dans le dépôt ; s'il n'est pas changé en production, il compromet la génération de tokens CSRF, etc. | Élevé | Remplacer par une chaîne aléatoire longue (min. 32 caractères) dans `parameters.yml` de production et ne jamais commiter ce fichier. |
| Identifiants DB par défaut | `app/config/parameters.yml.dist:5-6` | `database_user: root` et `database_password: ~` (vide) ; si les paramètres de production ne sont pas modifiés, cela expose la base de données. | Élevé | Utiliser un utilisateur dédié avec un mot de passe fort en production ; s'assurer que `parameters.yml` est exclu du dépôt. |

### 2. Vulnérabilités dans les contrôleurs

| Catégorie | Fichier/ligne | Description | Risque | Recommandation |
|-----------|---------------|-------------|--------|----------------|
| Upload de fichier non sécurisé | `src/ThoughtBundle/Controller/UtilController.php:24-28` | Aucune validation du type de fichier, pas de restriction d'extension, pas d'authentification requise. Le fichier est stocké dans un répertoire public (`web/images/ckeditor/`) avec un nom généré par `uniqid`. Risque d'exécution de code si un fichier .php est uploadé et que le serveur exécute PHP dans ce répertoire. | Élevé | 1) Exiger une authentification (ajouter `@Security("is_granted('ROLE_USER')")`). 2) Valider le type MIME (image/jpeg, image/png, etc.) avec `Assert\File` dans le formulaire. 3) Renommer avec une extension sécurisée (ex: `.jpg`). 4) Stocker hors de `web/` ou configurer le serveur web pour interdire l'exécution dans ce répertoire. |
| Injection SQL potentielle | `src/ThoughtBundle/Repository/ThoughtRepository.php:45` | Concaténation directe de `$field` et `$value` dans la clause WHERE (`'t.' . $field . $value`). Bien que ce soit du DQL, une valeur malveillante pourrait modifier la requête. | Moyen | Utiliser `->andWhere('t.' . $field . ' = :value')` avec `->setParameter('value', $value)`. |
| Exposition de données sensibles via logs | `app/config/config_dev.yml:14-23` | En environnement dev, les logs capturent tous les événements (`level: debug`), ce qui peut inclure des informations sensibles (mots de passe, tokens). | Faible | En production, utiliser `monolog.handlers.main.level: error` (déjà configuré dans `config_prod.yml`). Vérifier que les logs ne sont pas accessibles publiquement. |
| Absence de validation des entrées | Plusieurs contrôleurs utilisent `$request->get()` sans validation ni typage. Ex: `$format = $request->get('format');` (`ThoughtAdminController.php:51`). | Faible | Valider et filtrer les entrées avec les contraintes Symfony (Validation) ou utiliser `$request->query->getInt()` pour les nombres. |

### 3. Vulnérabilités dans les templates Twig

| Catégorie | Fichier/ligne | Description | Risque | Recommandation |
|-----------|---------------|-------------|--------|----------------|
| Sortie non échappée (raw) | `src/ThoughtBundle/Resources/views/content.html.twig:7`<br>`src/ThoughtBundle/Resources/views/dynamicPage.html.twig:7`<br>`src/ThoughtBundle/Resources/views/instruction.html.twig:7` | Utilisation de `|raw` sur du contenu stocké en base de données (`content.content`, `text`). Si un attaquant peut injecter du HTML (via édition administrateur ou injection SQL), cela conduit à du XSS stocké. | Moyen | Si le contenu est censé être du HTML enrichi (éditeur WYSIWYG), s'assurer qu'il est assaini avant stockage (ex: avec `htmlpurifier`). Sinon, retirer `|raw` et échapper automatiquement. |
| Sortie non échappée dans les messages flash | `src/ThoughtBundle/Resources/views/layout.html.twig:65,73` | `{{ msg|raw }}` sur les messages flash. Si un message contient des données utilisateur non échappées, XSS possible. | Faible | Éviter `|raw` sur les messages flash ; utiliser `|trans` ou échapper par défaut. |
| Filtre customTag non sécurisé | `src/ThoughtBundle/Twig/AppExtension.php:134-154` | Le filtre `customTag` transforme `[a url]text[/a]` en `<a href="url">text</a>` sans échappement des attributs `url` et `text`. Combiné à `|raw` dans les templates (`quoteLayout.html.twig:52`), cela peut permettre du XSS. | Moyen | Échapper les attributs `url` et `text` avec `htmlspecialchars` dans le filtre, ou utiliser `Twig_SimpleFilter` avec `['is_safe' => ['html']]` et assurer que l'entrée est sûre. |
| JSON non échappé | `src/ThoughtBundle/Resources/views/teacherGroups/search.json.twig:4` | `|json_encode|raw` peut exposer à du XSS si le contenu contient des caractères HTML et que la réponse est interprétée comme HTML. Comme c'est une réponse JSON avec Content-Type approprié, le risque est faible. | Faible | S'assurer que l'entête `Content-Type: application/json` est bien défini. |

### 4. Voters de sécurité défectueux

| Catégorie | Fichier/ligne | Description | Risque | Recommandation |
|-----------|---------------|-------------|--------|----------------|
| Logique erronée dans ChainVoter | `src/ThoughtBundle/Security/ChainVoter.php:67` | `$security->isGranted($owner, $user)` utilise l'utilisateur propriétaire comme attribut, ce qui est incorrect. La condition `$owner !== $user` combinée peut bloquer l'accès même au propriétaire. | Moyen | Corriger la logique : vérifier si l'utilisateur courant est le propriétaire (`$owner === $user`) ou a un rôle administrateur. Utiliser `$security->isGranted('ROLE_ADMIN')`. |
| Bug dans StudentVoter.supports | `src/ThoughtBundle/Security/StudentVoter.php:26` | `if (!$attribute instanceof User)` alors que `$attribute` est une chaîne (ex: 'view'), donc le voter ne supporte jamais aucune action, rendant la protection inefficace. | Élevé | Corriger `supports` pour vérifier l'attribut attendu (ex: `in_array($attribute, ['view', 'edit'])`) et le sujet. |
| Logique confuse dans ProfileVoter | `src/ThoughtBundle/Security/ProfileVoter.php:64-66` | La condition compare un booléen (rôle de l'utilisateur) avec un booléen (rôle du profil). La règle peut autoriser ou refuser incorrectement l'accès. | Moyen | Réécrire la logique d'autorisation selon les besoins métier (ex: les enseignants peuvent voir les profils étudiants, mais pas l'inverse). |

### 5. Configuration des sessions

| Catégorie | Fichier/ligne | Description | Risque | Recommandation |
|-----------|---------------|-------------|--------|----------------|
| Absence de cookie_secure | `app/config/config.yml:32-34` | Pas de configuration `cookie_secure: true`, donc le cookie de session est transmis en HTTP même si l'application utilise HTTPS, exposant au vol de session par MITM. | Moyen | Ajouter `cookie_secure: true` dans `config_prod.yml` (sous `framework.session`). |
| Absence de cookie_httponly explicite | Idem | Bien que `cookie_httponly` soit true par défaut, il est recommandé de le définir explicitement. | Faible | Ajouter `cookie_httponly: true`. |
| Durée de session par défaut (1440s) | - | La session PHP expire après 24 minutes d'inactivité, ce qui peut être trop long pour une application sensible. | Faible | Régler `gc_maxlifetime` à une valeur appropriée (ex: 3600) et utiliser `session.cookie_lifetime`. |

### 6. Informations sensibles exposées

| Catégorie | Fichier/ligne | Description | Risque | Recommandation |
|-----------|---------------|-------------|--------|----------------|
| Fichier parameters.yml.dist avec valeurs par défaut | `app/config/parameters.yml.dist` | Contient des secrets faibles et des identifiants par défaut. Si le fichier `parameters.yml` n'est pas personnalisé en production, l'application est vulnérable. | Élevé | Supprimer les valeurs par défaut ou les remplacer par des placeholders explicites. S'assurer que `parameters.yml` est généré avec des valeurs fortes lors du déploiement. |
| Clés API éventuelles | Non détecté | Aucune clé API trouvée dans le dépôt (bonne pratique). | - | Continuer à ne jamais commiter de clés. |

## Évaluation du niveau de risque global

- **Risque Élevé** : 4 vulnérabilités (hash faible, upload non sécurisé, secret faible, voter défectueux).
- **Risque Moyen** : 7 vulnérabilités (CSRF, trusted_hosts, injection SQL, XSS via raw, configuration session, logique voters).
- **Risque Faible** : 5 vulnérabilités (logs, validation, double slash, cookie_httponly, durée session).

L'application présente des failles critiques qui pourraient permettre à un attaquant de prendre le contrôle du serveur (via upload de shell), de voler des sessions, de contourner l'authentification, ou d'exfiltrer la base de données. Une correction prioritaire est nécessaire avant la mise en production.

## Recommandations prioritaires de correction

1. **Corriger l'upload de fichier** (Élevé) : Ajouter l'authentification, validation stricte des types MIME, renommage avec extension sécurisée, désactivation de l'exécution dans le répertoire public.
2. **Renforcer le hash des mots de passe** (Élevé) : Passer à bcrypt avec coût 12 dans `security.yml`.
3. **Changer le secret** (Élevé) : Générer un secret fort et unique pour chaque environnement ; ne pas commiter `parameters.yml`.
4. **Réparer les voters** (Élevé) : Corriger `StudentVoter.supports` et `ChainVoter.canEdit` pour qu'ils fonctionnent comme attendu.
5. **Activer trusted_hosts et trusted_proxies** (Moyen) : Configurer selon l'infrastructure.
6. **Échapper les sorties raw** (Moyen) : Supprimer `|raw` des contenus non fiables ou implémenter un filtre de purification HTML.
7. **Configurer la session sécurisée** (Moyen) : Ajouter `cookie_secure: true` et `cookie_httponly: true` en production.
8. **Valider les entrées utilisateur** (Moyen) : Utiliser les contraintes de validation Symfony sur tous les formulaires et paramètres de requête.
9. **Corriger l'injection SQL potentielle** (Moyen) : Remplacer la concaténation dans `ThoughtRepository::getFilterThoughts` par des paramètres nommés.
10. **Vérifier la protection CSRF** (Moyen) : S'assurer que tous les formulaires incluent un token CSRF (vérifier les formulaires personnalisés).

## Bonnes pratiques à mettre en œuvre

- **Validation des entrées** : Utiliser les composants `Validator` et `Form` de Symfony pour toutes les données externes.
- **Échappement des sorties** : Toujours utiliser l'auto-escape de Twig ; ne jamais utiliser `|raw` sur des données non fiables.
- **Journalisation sécurisée** : Éviter de logger des informations sensibles (mots de passe, tokens, données personnelles). Configurer les niveaux de log appropriés.
- **Gestion des erreurs** : En production, désactiver l'affichage des erreurs (`kernel.debug: false`) et configurer une page d'erreur générique.
- **Authentification forte** : Implémenter la vérification en deux étapes (2FA) pour les comptes administrateur.
- **Revue des dépendances** : Mettre à jour régulièrement les bundles (voir audit de dépendances séparé).
- **Tests de sécurité** : Intégrer des tests automatisés de sécurité (ex: avec `symfony/security-checker`, `nikic/php-parser`).
- **Configuration HTTPS** : Forcer HTTPS sur toutes les pages (redirection HTTP → HTTPS) et activer HSTS.

## Conclusion

L'application Symfony présente des vulnérabilités significatives qui nécessitent une attention immédiate. Les correctifs prioritaires doivent être appliqués avant tout déploiement en environnement de production. Une fois ces correctifs mis en place, il est recommandé de réaliser un test de pénétration complémentaire pour s'assurer de la robustesse de l'application.

---
*Audit réalisé avec une analyse statique du code. Certaines vulnérabilités peuvent nécessiter une validation dynamique.*