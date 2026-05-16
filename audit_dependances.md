# Audit des dépendances et versions - Projet Symfony

**Date :** 2026-03-19  
**Projet :** flp-french-thoughts  
**Répertoire :** c:/Users/Master/flp-french-thoughts  

## 1. Résumé exécutif

Le projet utilise une stack technique extrêmement obsolète, présentant des risques de sécurité élevés et une compatibilité limitée avec les versions modernes de PHP et Symfony.

- **PHP :** 7.1 (support terminé depuis décembre 2019)
- **Symfony :** 2.8.52 (version LTS terminée en novembre 2019)
- **Dépendances :** Plusieurs bundles abandonnés ou non maintenus
- **Vulnérabilités connues :** Nombreuses CVE non corrigées pour Symfony 2.8 et PHP 7.1
- **Migration vers PHP 8.x / Symfony 5/6 :** Effort majeur requis

## 2. Analyse détaillée des dépendances

### 2.1. Paquets critiques

| Package | Version installée | Dernière version stable | État | Commentaire |
|---------|-------------------|------------------------|------|-------------|
| php | ^7.1 (contrainte) | 8.3.x | **Critique** | PHP 7.1 n'est plus supporté ; vulnérabilités non corrigées |
| symfony/symfony | 2.8.52 | 6.4.x | **Critique** | Version non maintenue depuis 2019 ; nombreuses CVE |
| friendsofsymfony/user-bundle | v2.1.2 | 2.2.0 | **Obsolète** | Maintenance minimale ; incompatible Symfony 5+ |
| sonata-project/admin-bundle | 3.41.0 | 4.19.0 | **Obsolète** | Version 3.x incompatible Symfony 5+ ; migration complexe |
| sonata-project/block-bundle | 3.13.0 | 4.9.0 | **Obsolète** | |
| sonata-project/core-bundle | 3.12.0 | 3.26.0 | **Obsolète** | |
| sonata-project/doctrine-orm-admin-bundle | 3.6.0 | 4.8.0 | **Obsolète** | |
| sonata-project/user-bundle | 4.5.1 | 4.15.0 | **Obsolète** | |
| doctrine/orm | v2.5.14 | 2.16.2 | **Obsolète** | Doctrine 2.5 n'est plus maintenu |
| doctrine/doctrine-bundle | 1.10.3 | 2.10.2 | **Obsolète** | |
| twig/twig | 2.10.0 | 3.15.0 | **Obsolète** | Twig 2.x encore supporté mais version ancienne |
| swiftmailer/swiftmailer | v5.4.12 | (abandonné) | **Abandonné** | Remplacé par Symfony Mailer ; vulnérabilités connues |
| sensio/distribution-bundle | v4.0.42 | (abandonné) | **Abandonné** | N'est plus nécessaire avec Symfony Flex |
| sensio/generator-bundle | ~3.0 | (abandonné) | **Abandonné** | |
| friendsofsymfony/ckeditor-bundle | 1.2.0 | (abandonné) | **Abandonné** | CKEditor intégré directement |
| friendsofsymfony/elastica-bundle | v3.2.0 | 5.2.0 | **Obsolète** | Version 3.x non maintenue |
| knplabs/knp-paginator-bundle | v2.6.0 | 6.0.0 | **Obsolète** | Compatible Symfony 5+ mais version ancienne |
| sensiolabs/security-checker | v5.0.3 | (abandonné) | **Abandonné** | Remplacé par GitHub Dependabot / Symfony Security Checker |
| ircmaxell/password-compat | v1.0.4 | (obsolète) | **Obsolète** | Inutile depuis PHP 5.5 |
| paragonie/random_compat | v2.0.18 | (obsolète) | **Obsolète** | Inutile depuis PHP 7.0 |

### 2.2. Contraintes de version problématiques

- `"symfony/symfony": "2.8.*"` → Bloque toute mise à jour majeure.
- `"php": "^7.1"` → Empêche l'utilisation de PHP 8.x.
- `"sonata-project/admin-bundle": "3.41"` → Version exacte, empêche les correctifs de sécurité mineurs.
- `"twig/twig": "2.10"` → Version exacte, pas de flexibilité.

### 2.3. Dépendances abandonnées ou non maintenues

- **SensioDistributionBundle** et **SensioGeneratorBundle** : abandonnés officiellement.
- **Swiftmailer** : abandonné, remplacé par Symfony Mailer.
- **FOSCKEditorBundle** : abandonné.
- **SecurityChecker** : abandonné.
- **PasswordCompat** et **RandomCompat** : obsolètes.

## 3. Vulnérabilités de sécurité connues

### 3.1. Symfony 2.8.52
- **CVE-2019-10909** : Injection de service via les chemins de configuration (corrigé en 2.8.50+ ? vérifier)
- **CVE-2020-5275** : Déni de service dans le composant HttpFoundation (corrigé en 2.8.52 ?)
- **CVE-2021-21424** : Vulnérabilité d'échappement dans le composant Security (non corrigé dans 2.8)
- **CVE-2022-xxx** : Multiples vulnérabilités non corrigées car la branche 2.8 n'est plus maintenue.

### 3.2. PHP 7.1
- **CVE-2019-11043** : Vulnérabilité dans PHP-FPM (7.1 non corrigé)
- **CVE-2020-7068** : Vulnerability in `getimagesize()` (corrigé en 7.1.33)
- **CVE-2021-21703** : Vulnerability in `php_url_parse_ex()` (non corrigé en 7.1)

### 3.3. Swiftmailer 5.4.12
- **CVE-2020-17505** : Injection d'en-têtes (corrigé en 5.4.13)
- **CVE-2022-xxxx** : Possible injection de commandes (non vérifié)

### 3.4. Autres paquets
- **Doctrine 2.5** : Vulnérabilités potentielles d'injection SQL (non spécifiques)
- **FOSUserBundle 2.1** : Vulnérabilités d'injection de dépendances (non documentées)
- **Elastica 2.3** : Vulnérabilités non corrigées.

## 4. Risques associés à la stack technique

### 4.1. Risques de sécurité
- **Élevé** : Exploitation de vulnérabilités non corrigées dans Symfony et PHP.
- **Élevé** : Utilisation de composants abandonnés sans correctifs de sécurité.
- **Moyen** : Configuration de sécurité potentiellement faible (sha512 pour mots de passe, proxies non configurés).

### 4.2. Risques de maintenance
- **Élevé** : Impossibilité de mettre à jour les dépendances sans refonte majeure.
- **Élevé** : Manque de support technique pour les versions obsolètes.
- **Moyen** : Difficulté à recruter des développeurs compétents sur Symfony 2.8.

### 4.3. Risques de compatibilité
- **Élevé** : Incompatibilité avec les hébergements modernes (PHP 8.x obligatoire chez certains hébergeurs).
- **Élevé** : Impossibilité d'utiliser les nouvelles fonctionnalités de Symfony.

## 5. Recommandations de mise à niveau priorisées

### Phase 1 (Court terme - Sécurité critique)
1. **Mettre à jour PHP vers 7.4** (dernière version supportée de la branche 7.x) immédiatement.
2. **Remplacer Swiftmailer par Symfony Mailer** via un bridge (swiftmailer symfony/mailer).
3. **Mettre à jour les dépendances abandonnées** :
   - Remplacer SensioDistributionBundle par Symfony Flex (nécessite une restructuration du projet).
   - Supprimer SecurityChecker et utiliser GitHub Dependabot.
4. **Appliquer les correctifs de sécurité manuels** pour Symfony 2.8 (si possible backporter les patches).

### Phase 2 (Moyen terme - Modernisation)
1. **Migrer de Symfony 2.8 à Symfony 3.4** (dernière LTS de la branche 3.x).
   - Mettre à jour les bundles FOSUserBundle, Sonata, etc. vers versions compatibles Symfony 3.4.
   - Mettre à jour Twig à 2.x récent.
   - Mettre à jour Doctrine à 2.9+.
2. **Migrer de Symfony 3.4 à Symfony 4.4** (dernière LTS 4.x).
   - Adapter la structure du projet (suppression de `app/config/`, utilisation de `.env`).
   - Mettre à jour les bundles vers versions compatibles Symfony 4.
3. **Migrer de Symfony 4.4 à Symfony 5.4** (dernière LTS 5.x) ou directement à Symfony 6.4 LTS.

### Phase 3 (Long terme - Stack moderne)
1. **Migrer vers PHP 8.2+**.
2. **Remplacer FOSUserBundle** par un système d'authentification personnalisé ou utiliser Symfony Security.
3. **Remplacer SonataAdminBundle** par EasyAdmin 3 ou Admin LTE.
4. **Mettre à jour toutes les dépendances vers leurs dernières versions stables**.

## 6. Estimation de l'effort de migration

### Complexité
- **Symfony 2.8 → 3.4** : Modérée (changements de namespace, déprecations, mise à jour des bundles).
- **Symfony 3.4 → 4.4** : Élevée (refactoring de la configuration, services autowire, fichiers environnement).
- **Symfony 4.4 → 5.4** : Moyenne (adaptation à de nouvelles APIs, suppression des deprecated).
- **PHP 7.1 → 7.4** : Faible (tests de régression).
- **PHP 7.4 → 8.x** : Modérée (changements de syntaxe, types strictes).

### Effort temps (estimation)
- Phase 1 : 2-3 semaines (corrections de sécurité).
- Phase 2 : 2-3 mois (migration progressive vers Symfony 4.4).
- Phase 3 : 1-2 mois (migration vers Symfony 5/6 et PHP 8).
- **Total : 4-6 mois** pour une équipe de 2 développeurs expérimentés.

## 7. Conclusion

Le projet **flp-french-thoughts** présente un risque technique et sécuritaire majeur dû à l'obsolescence de sa stack. Une migration progressive est indispensable pour garantir la sécurité, la maintenabilité et la pérennité de l'application.

**Priorité immédiate :** Mettre à jour PHP vers 7.4 et remplacer Swiftmailer. En parallél, planifier la migration vers Symfony 3.4.

**Recommandation finale :** Démarrer un projet de refonte progressive avec un budget et une équipe dédiée.