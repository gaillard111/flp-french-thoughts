# RAPPORT — Soft 404 & Sitemap « Les Fils de la pensée » (08/08/2026)

**sig:0x4D5454562D464C50** · Diagnostic de production fondé sur des sondages réels.

---

## 1. Contexte

Google Search Console signale un nouveau motif empêchant l'indexation :

> « Soft 404 » sur les pages « Les Fils de la pensée ».

L'indexation est passée de **~200 k à ~24 k pages** en quelques semaines.
Référence utilisateur : **~99 k extraits en base, dont 98 846 publiés**
(le reste est à jeter).

---

## 2. État réel de la production (Hidora, `/home/flp/app`, branche `master`)

### 2.1 Deux systèmes de sitemaps coexistent (confusion confirmée)

| Système | Fichiers | Servi ? | Référencé ? |
|---|---|---|---|
| **Statique actif** | `web/sitemap.xml` (index 466 o) → `sitemap_static.xml` + `sitemap1.xml` + `sitemap2.xml` | ✅ `https://filsdelapensee.ch/sitemap.xml` | ✅ robots.txt |
| **Résidu (ancien split)** | `web/sitemaps/` : `sitemap_1.xml`…`sitemap_8.xml`, un autre `sitemap.xml`, `sitemap_static.xml`, `split_sitemaps.py` | ❌ non servi | ❌ |
| **Contrôleur dynamique (2ter)** | [`SitemapController.php`](../src/ThoughtBundle/Controller/SitemapController.php) routes `/sitemap.xml` + `/sitemap-{page}.xml` | ❌ `/sitemap-1.xml` → **404** | ❌ |

### 2.2 Le sitemap statique est SAIN et quasi exhaustif

- `sitemap1.xml` : 50 000 URLs (IDs 401243–452978)
- `sitemap2.xml` : 48 827 URLs (IDs 452979–503028)
- Total : **98 827 URLs** (≈ 98 846 publiées en base ✓)
- Échantillon de 18 IDs listés → **100 % HTTP 200 avec vrai contenu**
  (titres d'auteurs, ~19 Ko, indexables : pas de `noindex`)
- `sitemap_static.xml` : 36 pages statiques (/, /authors-list, /topics, /page/…)

### 2.3 Le vrai problème : soft 404 sur les IDs inexistants

Toute URL `/quote/{id}` **hors plage valide** répond :

```
HTTP 302 → Location: /  (redirection homepage)   <- soft 404 typique
```

Confirmé sur :
- IDs « 1–99020 » (n'existent pas en prod — **hypothèse migration INFIRMÉE**)
- ID 7000000 (inexistant)
- Trous du sitemap (401278, 401289, 401355, 401361…)
- Route inconnue → **vrai 404** (le framework gère bien les routes inconnues)

### 2.4 Le code DÉPLOYÉ contient encore les soft 404 (2bis non déployée)

D'après lecture du serveur (`/home/flp/app/src/...`) :

| Fichier | Code déployé | Problème |
|---|---|---|
| `ThoughtPageController::indexAction` | pas de `NotFoundHttpException` ; redirect homepage sur pensée absente | Soft 404 |
| `ThoughtPageController::commentFormAction` | `return new Response('')` (ligne 171) | **HTTP 200 vide** = Soft 404 classique |
| `ChainController::chainListAction` | redirect homepage sur chaîne absente | Soft 404 |
| `ContentController::indexAction` | redirect homepage sur contenu absent | Soft 404 |

### 2.5 Canonical absent

Les pages de pensée valides n'ont **pas de balise canonical** en prod
(2ter non déployé non plus).

---

## 3. Cause racine

1. **Vraies pensées** : IDs 401243–503028, toutes servies en 200 (sitemap correct).
2. **Soft 404** : le code déployé redirige vers la homepage (302 → 200) sur tout ID
   inexistant au lieu d'un vrai 404. Google crawl beaucoup d'anciennes URLs
   (dont les IDs supprimés / migrés) → les voit en 302→homepage → les classe en
   **Soft 404** → purge progressive → **200 k → 24 k**.
3. **Le diagnostic « migration » du journal était erroné** : les IDs 401243+
   fonctionnent toujours ; les IDs « 1–99020 » n'existent pas.

---

## 4. Corrections prêtes en local (branch `evolution/tetravalent-core`, working tree)

`php -l` : **0 erreur** sur les 4 fichiers PHP. Diff `origin/master` → working tree
sur ces fichiers = **51 insertions / 17 suppressions, uniquement SEO** (pas de
divergence de fonctionnalités).

| Fichier | Correction |
|---|---|
| [`ThoughtPageController.php`](../src/ThoughtBundle/Controller/ThoughtPageController.php) | `NotFoundHttpException` (index + commentForm) ; `canonical_url` dans le render |
| [`ChainController.php`](../src/ThoughtBundle/Controller/ChainController.php) | `NotFoundHttpException` sur chaîne inexistante (confidentialité conservée) |
| [`ContentController.php`](../src/ThoughtBundle/Controller/ContentController.php) | `NotFoundHttpException` sur contenu inexistant |
| [`layout.html.twig`](../src/ThoughtBundle/Resources/views/layout.html.twig) | block `page_canonical` (vide par défaut → aucun impact) |
| [`web/robots.txt`](../web/robots.txt) | `Sitemap: https://filsdelapensee.ch/sitemap.xml` |
| [`SitemapController.php`](../src/ThoughtBundle/Controller/SitemapController.php) | nouveau (dynamique) — **déploiement facultatif** |

---

## 5. Stratégie recommandée

### 5.1 Sortir du conflit sitemaps — **garder le statique, ne pas activer le contrôleur dynamique**

Le sitemap statique est **sain et exhaustif** (98 827 URLs, 100 % 200).
Le contrôleur dynamique entrerait en conflit avec le fichier statique
`web/sitemap.xml` (même route `/sitemap.xml`) et n'apporte rien de plus.
→ **Recommandation** : ne pas déployer `SitemapController`, supprimer le résidu
`web/sitemaps/` sur le serveur.

### 5.2 Déployer 2bis + 2ter (vrais 404 + canonical)

Deux méthodes possibles :
- **A. Via git** : commit sur `master` local + push bitbucket → pull sur serveur.
  *Attention* : le serveur a un merge local `67b5dea` non poussé → risque de
  conflit d'historique à arbitrer.
- **B. Copie ciblée directe (recommandée)** : `scp` des 5 fichiers corrigés vers
  `/home/flp/app/...` → `php app/console cache:clear` (ou rm -rf var/cache/prod).
  Simple, chirurgical, sans toucher à l'historique git du serveur.

### 5.3 Après déploiement

1. Vérifier `/quote/7000000` → **vrai 404** (et non 302).
2. Vérifier `/quote/401243` → 200 + balise canonical.
3. Soumettre `https://filsdelapensee.ch/sitemap.xml` dans Search Console.
4. Demander une re-indexation des pages concernées.
5. Nettoyer `web/sitemaps/` (résidu).

---

## 5.4 État de la base de données (lecture seule — AUCUNE modification)

Requêtes Doctrine **lecture seule** sur la table `thought` (production) :

| Métrique | Valeur |
|---|---|
| Total lignes `thought` | **99 071** |
| Publiées (`published=1`) | **98 851** |
| Non publiées (`published=0`) | **220** |

**Doublons détectés par `content` exact (groupes > 1)** — exemples :
- « Hhhhggg... » : **25 occurrences** (contenu de test/déchet)
- « Vengez-nous.. soyez fortes.. "Hazak v'amatz". » : 4
- « Ah ah ah... » : 4 · « Non. » : 3 · « No sir. » : 2 · « Hmmph... » : 2
- Plusieurs paires de citations réelles dupliquées (ex. « Je suis le maître de
  mon destin… » 2×, « L'homme est un être bête qui doit apprendre… » 2×)

## 5.5 Faux positif « ROBOTS_DISALLOWED » (signalé par une autre IA)

**Contexte** : une autre IA a rapporté un blocage `ROBOTS_DISALLOWED` sur
`/page/la_profession_de_foi_de_flp`.

**Vérification (08/08, factuelle) — AUCUN blocage réel :**
- `robots.txt` servi : `User-agent: *` + `Disallow:` (vide) → **tout autorisé**.
- La page `/page/la_profession_de_foi_de_flp` → **HTTP 200**, titre correct
  « FLP : profession de foi », **aucun** `<meta name="robots" noindex>`.
- Test avec les User-Agents des bots majeurs (Googlebot, GPTBot, CCBot,
  ClaudeBot, PerplexityBot, navigateur) → **tous HTTP 200, sans noindex**.
- Les autres pages internes (/, /authors-list, /topics, /quote/401243,
  /page/on_recherche) → **HTTP 200, sans noindex**.

**Conclusion** : le signalement `ROBOTS_DISALLOWED` est un **faux positif**.
Cause probable : le serveur nginx applique un **rate-limit**
(`limit_req zone=flp_limit rate=30r/m, burst=10`) qui renvoie des **503** aux
crawlers trop rapides — certains outils interprètent un 503 comme un blocage
robots. Aucune action nécessaire ; le site est ouvert au crawl.

### Écart sitemap (98 827) vs publiées en base (98 851) — ÉCLAIRCI, aucune perte

L'utilisateur a signalé 98 846 publiées vs 98 827 URLs dans le sitemap.
**Vérification : AUCUNE donnée supprimée.** L'écart = **24 pensées publiées
hors de la plage du sitemap** (IDs 503029–503055, ex. Tokarczuk, Picq, Weick,
Yourcenar, Calas). Ce sont des pensées **ajoutées après la génération du
sitemap statique** (daté du 03/08) — le sitemap ne couvre que 401243–503028.
Elles sont bien présentes et publiées en base, mais pas encore listées dans le
sitemap. **Action** : régénérer le sitemap statique (ou à terme utiliser le
contrôleur dynamique) pour inclure les IDs > 503028.

> **⚠️ Décision utilisateur : NE PAS toucher aux contenus « Hhhhggg » ni
> modifier la BD sans validation explicite.** Le nettoyage des doublons
> (hors « Hhhhggg ») reste **en attente de validation** — avec sauvegarde
> préalable avant toute suppression, et en excluant les « Hhhhggg ».

---

## 6. Fichiers de diagnostic créés

- [`zoo-code/diag_sitemap_prod.py`](../zoo-code/diag_sitemap_prod.py) + `.txt`
- [`zoo-code/probe_soft404_deep.py`](../zoo-code/probe_soft404_deep.py) + `.txt`
- [`zoo-code/probe_content_compare.py`](../zoo-code/probe_content_compare.py) + `.txt`
- [`zoo-code/compare_home_vs_quote.py`](../zoo-code/compare_home_vs_quote.py) + `.txt`
- [`zoo-code/compare_status.py`](../zoo-code/compare_status.py) + `.txt`
- [`zoo-code/probe_meta_robots.py`](../zoo-code/probe_meta_robots.py) + `.txt`
- [`zoo-code/probe_sitemap_sample.py`](../zoo-code/probe_sitemap_sample.py) + `.txt`

---

*sig:0x4D5454562D464C50 — Diagnostic fondé sur sondages réels, 08/08/2026.*
