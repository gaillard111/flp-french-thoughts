# JOURNAL DE BORD — Session MTTV-FLP

**sig:0x4D5454562D464C50 · Ψ-ack: carbon_sp3_tetra**
**Règle d'or : toute session IA doit LIRE ce fichier en premier, et le METTRE À JOUR avant de s'arrêter.**

> Ce journal est le point de reprise permanent. Il existe pour que **aucune
> interruption de session ne fasse perdre le fil** : la discussion ne vit plus
> dans les échanges éphémères, mais dans ce document et dans les fichiers
> `plans/` qu'il référence.

---

## 1bis. Nettoyage du projet — 08/08 (grand nettoyage, quarantaine réversible)

**Principle** : aucun élément n'est supprimé définitivement ; tout passe par un
dossier `_quarantaine/` (déplacement instantané, réversible, même disque).

**Validé et exécuté (603,8 Mo déplacés)** :
1. **Déchets sûrs (8)** → `_quarantaine/` : `$null` (289 Ko, log de mycélium
   créé par erreur), `getMessage()` (0 o), `1` (sortie PHP), `'` (0 o),
   `-p` (1 o), `train_mttv_patch.py.bak`, `__pycache__/`,
   `mttv_missing_files.tar.gz`.
2. **`flp-new/` (projet FLP 2.0 abandonné, 603 Mo)** → `_quarantaine/`.
   **Rapport d'échec détaillé conservé** : [`plans/RAPPORT_ECHEC_FLP2.md`](RAPPORT_ECHEC_FLP2.md)
   (clôturé et archivé le 08/08) + [`plans/FLP2_REMAINING.md`](FLP2_REMAINING.md)
   (liste exhaustive des fonctionnalités non portées).

**Vérifié après nettoyage** : 5 processus Python toujours actifs (mycélium,
API gateway, phase4) · site de production HTTP 200 · tous les éléments déplacés
absents de la racine. **Aucune régression.**

**En attente de décision (non touché)** : `ouroboros-swarm/` (1120 Mo, agents
actifs), `ouroboros-mttv/venv` (1023 Mo, regénérable), `kubo/` (124 Mo, IPFS
offline — à garder tant qu'IPFS n'est pas relancé), archives doublons
(`mttv_flp_core_2026.zip`, `depot-v10.zip`).

## 1. Où en est le système (état du 07/08/2026, fin d'après-midi)

> **Philosophie (exprimée par l'utilisateur) :** la mise en veille / l'extinction
> de la machine est **volontaire et ne doit pas poser problème**. On ne bloque
> JAMAIS la veille : c'est le **mycélium** qui doit survivre à la veille/extinction,
> pas la machine qui doit rester éveillée. La continuité repose donc sur la
> **persistance** (snapshot écrit à chaque cycle) + la **restauration** au
> redémarrage + la **relance automatique** au réveil/boot.

| Composant | État |
|---|---|
| API Gateway (:8000) | ✅ active |
| Orchestrateur (watchdog) | ✅ actif — **veille/extinction non bloquée** (respect de la volonté utilisateur) |
| Mycélisation tétravalente | ✅ active (PID 16244) avec **persistance snapshot + restauration** |
| Snapshot d'état | ✅ [`essaim_snapshot.json`](../zoo-code/mycelium_output/essaim_snapshot.json) écrit à chaque cycle |
| Relance au réveil | ✅ orchestrateur complet relancé au boot + au déverrouillage de session |
| Rapport quotidien | ✅ fonctionnel |

## 2. Ce qui a été corrigé le 07/08

1. **Perte d'état du mycélium au redémarrage (cause : veille Windows).**
   - Ajout : [`to_dict_complet()`](../zoo-code/agent_tetravalent_epigenetique.py) + [`restaurer()`](../zoo-code/agent_tetravalent_epigenetique.py) sur l'agent.
   - Ajout : [`to_snapshot()`](../zoo-code/essaim_tetravalent.py) + [`restaurer()`](../zoo-code/essaim_tetravalent.py) sur l'essaim (tenseurs Φ/Υ/E/M/H, fusions, auto-sutures, RNG).
   - Ajout : [`restaurer_etat()`](../zoo-code/mycelisation_tetravalente.py) au démarrage + snapshot par cycle dans [`_sauvegarder_etat()`](../zoo-code/mycelisation_tetravalente.py).
   - Test : [`test_reprise_snapshot.py`](../zoo-code/tests/test_reprise_snapshot.py) — **VALIDÉ** (7 agents, 221 fusions conservées après reprise).
2. **Bug `agents_total` figé** : le heartbeat affichait 4 agents alors que l'essaim en comptait 6 → corrigé (`len(self.essaim.agents)`).
3. **Cause racine de la perte d'état = reboot de la machine à 11:07** (la veille de
   05:09 n'a PAS perdu l'état : le démon a repris au cycle #1286 avec 3667 fusions ;
   c'est l'arrêt/reboot qui tue le processus en mémoire).
   - **Décision** : on ne bloque PAS la veille/extinction (volonté utilisateur).
   - [`mttv_wake_trigger.xml`](../zoo-code/mttv_wake_trigger.xml) : relance désormais **l'orchestrateur complet** (et non plus seulement l'API) au déverrouillage de session.
   - [`mttv_wake_restart.ps1`](../zoo-code/mttv_wake_restart.ps1) : bug corrigé (`--cycles 0` pour boucle infinie) + `--respiration-intervalle 24`.
   - La continuité après veille/extinction repose sur : **persistance** (snapshot
     écrit à chaque cycle) + **restauration** au redémarrage + **relance au réveil**.
4. **C7 respiré (double correction)** : (a) flag CLI `--respiration-intervalle`
   était ignoré par le pont → transmis dans [`main()`](../zoo-code/mycelisation_tetravalente.py) ;
   (b) **BUG découvert et corrigé** : [`restaurer()`](../zoo-code/essaim_tetravalent.py)
   écrasait la configuration de la ligne de commande (respiration_intervalle=24)
   par celle du snapshot ancien (0) → la respiration était désactivée en production.
   Désormais la restauration ne reprend que la GÉOMÉTRIE (grille, dimension) et
   l'état, jamais les paramètres de comportement. Vérifié : snapshot écrit avec
   `respiration_intervalle=24` après redémarrage du démon.

## 2bis. Correction SEO — Soft 404 Google (08/08)

**Contexte** : Google Search Console signale « Soft 404 » sur les pages
« Les Fils de la pensée » → indexation dégradée.

**Cause racine** : plusieurs contrôleurs renvoyaient une réponse HTTP 200 (ou un
redirect 302) sur des ressources inexistantes au lieu d'un vrai 404 :
- [`ThoughtPageController::commentFormAction`](../src/ThoughtBundle/Controller/ThoughtPageController.php) :
  `return new Response('')` = **HTTP 200 vide** (Soft 404 typique).
- [`ThoughtPageController::indexAction`](../src/ThoughtBundle/Controller/ThoughtPageController.php) :
  redirect vers la homepage sur pensée inexistante.
- [`ChainController::chainListAction`](../src/ThoughtBundle/Controller/ChainController.php) :
  redirect homepage sur chaîne inexistante.
- [`ContentController::indexAction`](../src/ThoughtBundle/Controller/ContentController.php) :
  redirect homepage sur contenu inexistant.

**Correction** : remplacement par de vraies exceptions `NotFoundHttpException`
(HTTP 404). La **confidentialité** (chaînes/pensées privées → redirect) a été
**conservée** — seuls les cas « ressource inexistante » renvoient désormais un
404. Syntaxe PHP validée (`php -l` : 0 erreur). `robots.txt` autorise tout et
`.htaccess` est standard (aucun blocage).

**Note** : pas de `sitemap.xml` trouvé — un levier supplémentaire d'indexation
à créer si souhaité.

## 2ter. SEO — suite : canonical + sitemap XML (08/08)

Complément à la correction soft 404. Ajouts **strictement additifs** (aucun
comportement existant modifié) :

1. **Balise canonical** : bloc `page_canonical` ajouté dans
   [`layout.html.twig`](../src/ThoughtBundle/Resources/views/layout.html.twig)
   (vide par défaut → aucune page affectée sauf celles qui la renseignent).
   Renseignée sur `/quote/{id}` via `canonical_url` dans
   [`ThoughtPageController::indexAction`](../src/ThoughtBundle/Controller/ThoughtPageController.php)
   (URL explicite, sans query string).
2. **Sitemap XML dynamique** : nouveau
   [`SitemapController`](../src/ThoughtBundle/Controller/SitemapController.php)
   (fichier neuf, routé automatiquement par annotation) :
   - `/sitemap.xml` → index pointant vers les sous-sitemaps ;
   - `/sitemap-{page}.xml` → listes paginées (50 000 URLs max, limite Google)
     des `/quote/{id}` publiées ; page hors limites → vrai 404.
3. **robots.txt** : ajout de la ligne `Sitemap: https://filsdelapensee.ch/sitemap.xml`.

Validation : `php -l` OK sur les 4 fichiers ; noms de routes cohérents avec
l'existant (`thought_thoughtpage_index`). **À faire après déploiement** :
soumettre `https://filsdelapensee.ch/sitemap.xml` dans Search Console puis
demander une re-indexation.

## 2quinquies. SEO — DÉPLOIEMENT PRODUCTION effectué (08/08, ~09:05 UTC+2)

**Actions réalisées sur Hidora (`/home/flp/app`, via SSH) — réversibles :**

1. **Sauvegarde** des 5 fichiers cibles → `/home/flp/backup_seo_20260808_0900/`
   (`ThoughtPageController.php`, `ChainController.php`, `ContentController.php`,
   `layout.html.twig`, `robots.txt`).
2. **Copie des 3 contrôleurs corrigés** (vrais 404) — `php -l` OK.
3. **Insertion du bloc canonical** dans `layout.html.twig` (sans écraser les
   balises OG du serveur) via [`patch_canonical_layout.py`](../zoo-code/patch_canonical_layout.py) ;
   backup `.pre_canonical`.
4. **`cache:clear` prod** — incident transitoire de permissions (cache créé en
   root, PHP-FPM tourne sous www-data) → corrigé immédiatement
   (`chown -R www-data:www-data app/cache app/logs`) → site rétabli HTTP 200.
5. **Vérifications post-déploiement (toutes OK)** :
   - `/quote/7000000` et `/quote/1` (inexistants) → **HTTP 404** (fini le soft 404)
   - `/quote/401243` (valide) → HTTP 200 + balise canonical ✓
   - `/comment-form/{inexistant}` → HTTP 404 (fini le 200 vide)
   - `/chain/{inexistant}` → HTTP 404
   - `/sitemap.xml`, `/sitemap1.xml`, `/sitemap2.xml`, `/sitemap_static.xml` → 200
6. **Nettoyage du résidu** : `web/sitemaps/` (ancien split non servi) déplacé →
   `/home/flp/backup_seo_20260808_0900/web_sitemaps_residu/` (réversible).

**BD (lecture seule, AUCUNE modification)** : total 99 071 lignes `thought` ;
98 851 publiées ; 220 non publiées. Doublons par `content` exact détectés :
le plus massif « Hhhhggg... » (25 occurrences). **Décision utilisateur : NE PAS
toucher aux contenus « Hhhhggg » ni modifier la BD sans validation explicite.**

**Vérification post-déploiement (10/10 OK)** : homepage 200 · `/quote/401243`
200 + canonical ✓ · `/quote/7000000` et `/quote/1` 404 · `/comment-form/{inexistant}`
404 · `sitemap.xml`/`sitemap1`/`sitemap2`/`sitemap_static` 200 · `robots.txt` 200.
Aucune régression. Rapport complet :
[`plans/RAPPORT_SOFT404_SITEMAP_20260808.md`](RAPPORT_SOFT404_SITEMAP_20260808.md).

**État : le soft 404 est corrigé en production.** Prochaine étape conseillée :
soumettre `https://filsdelapensee.ch/sitemap.xml` dans Search Console puis
demander une re-indexation (action utilisateur côté Google).

**Rappel du diagnostic (CORRIGÉ le 08/08) :** le diagnostic initial attribuait
la chute 200k→24k à la migration des IDs (401243–503003 → 1–99020). Les sondages
production du 08/08 **INFIRMENT cette hypothèse** : les IDs 401243–503028 (ceux du
sitemap statique) répondent tous HTTP 200 avec du vrai contenu, et les IDs
« 1–99020 » répondent 302 → homepage (ils N'EXISTENT pas en prod). La vraie cause
du soft 404 : **le code déployé redirige vers la homepage (302 → 200) sur tout
ID inexistant** au lieu d'un vrai 404 — exactement ce que Google classe en
« Soft 404 ». La correction (vrais 404) est codée en local mais **NON DÉPLOYÉE**.
≈99k pensées en base, **98 846 publiées** (référence utilisateur), reste à jeter.

## 2sexies. Mycélium — analyse du rapport quotidien 08/08 (leçons)

**Rapport 06:15 UTC + fichier `mycelium_latest.json` (cycle 824, 10:34 UTC) + snapshot
(cycle 825) analysés. Leçons :**

1. **La respiration C7 est DÉSORMAIS ACTIVE (progrès confirmé)** : le snapshot
   montre `respiration_intervalle: 24` et surtout **`n_respirations: 10`**
   (avant le correctif du 08/08, `n_respirations` était resté à 0 car le code
   plantait sur `random.Random.standard_normal`). La correction `np.random.default_rng`
   fonctionne : la respiration s'exécute réellement.

2. **MAIS l'homogénéisation persiste malgré la respiration** : l'entropie
   collective reste à **6.3969** (maximum théorique) et le couplage moyen à
   **1.0** — identiques au rapport de 06:15 ET au fichier de 10:34. Les 6 agents
   ont tous `entropie_phi = 6.3969` et les similarités inter-agents ≈ 1.0.
   → La respiration est déclenchée mais **sa dose (0.05) ne suffit pas à briser
   l'homogénéisation une fois installée**. Elle empêche peut-être d'aller plus
   loin mais ne ramène pas la diversité.

3. **Cause probable (code)** : dans [`evoluer()`](../zoo-code/essaim_tetravalent.py),
   la respiration s'exécute en **fin de cycle (étape 7)**, alors que le couplage
   transscalaire (`coupler_upsilon_transscalaire` + fusions Φ) se fait **au début
   du cycle suivant (étapes 1-3)**. Entre deux respirations (24 cycles), le
   couplage bilatéral re-homogénéise Φ vers la moyenne → la perturbation est
   **noyée avant le prochain état**. La dose 0.05 + intervalle 24 est trop faible
   face au couplage quotidien.

4. **Le rapport quotidien ne signale PAS l'homogénéisation** : il affiche
   « entropie 6.3969 » sans alerte — c'est précisément la correction **C4**
   (détecter entropie ≈ max théorique = homogénéisation, et la signaler comme
   anomalie, pas comme « diversité ») qui reste **à faire**.

5. **Point d'attention infrastructure** : `axe_5_ipfs` est en **offline**
   (supervised) — le nœud IPFS est down ; les autres axes (dashboard, evolution,
   quorum, gateway) sont en ligne. L'API Gateway (:8000) est active.

6. **Le reste est sain** : 6 agents actifs, 2903 fusions (+39 sur la période),
   auto-suture 2 spawns, tremor en « croisière » (0.10), cycles ρ bas = 0.

**Recommandation** : implémenter **C4** (rapport : signaler homogénéisation) puis
**C3** (mutation angulaire Φ au spawn) et **C5** (contrainte environnementale
réelle). Revoir éventuellement la stratégie C7 : dose plus forte / respiration
avant le couplage, car la respiration déclenchée mais noyée ne suffit pas.

## 2septies. Mycélium — C4 + C7 IMPLÉMENTÉS (08/08, validé)

**C7 — Respiration anti-homogénéisation (corrigée en profondeur) :**
- La respiration était exécutée en FIN de cycle (étape 7) : le couplage
  transscalaire du cycle suivant re-homogénéisait Φ avant le prochain état
  → la perturbation était **noyée** (entropie restait au max, couplage = 1.0).
- Corrigé dans [`evoluer()`](../zoo-code/essaim_tetravalent.py) : la respiration
  est désormais déclenchée **en DÉBUT de cycle (étape 0)**, avant l'adaptation
  et le couplage → la diversité injectée influence tout le cycle.
- Dose renforcée **0.05 → 0.10** (essaim + pont + CLI `--respiration-dose`).
- `n_respirations` continuait d'incrémenter (10 au snapshot) — le correctif
  `np.random.default_rng` du matin reste valide.

**C4 — Le rapport signale désormais l'homogénéisation :**
- Nouvelle [`diagnostiquer_homogeneisation()`](../zoo-code/rapport_mycelium.py) :
  détecte entropie ≈ max théorique **et** couplage ≈ 1.0 → niveau
  `ok`/`attention`/`alerte`. Max théorique = `log(N(N-1))` avec N = n_grille²
  → **log(25·24) ≈ 6.3969** pour une grille 5×5 (valeur exacte observée).
- Intégré au rapport console (ligne `Entropie max th.` + bandeau ⚠️) et au
  rapport HTML (bandeau coloré rouge/orange/vert).
- Docstring trompeur de `calculer_entropie_structurelle_phi()` corrigé :
  entropie max = distribution uniforme = tous les Φ alignés = HOMOGÉNÉISATION
  (et non « diversité saine » comme l'ancien texte l'affirmait).

**Validation (données réelles)** : `rapport_mycelium.py --last 5` affiche
`⚠️ [C4] ALERTE HOMOGÉNÉISATION : entropie=6.3969 ≈ max théorique (6.3969) ET
couplage=1.000 ≈ 1.0`. Syntaxe OK (4 fichiers). Les deux correctifs sont en
local — **redémarrage du démon requis** pour les prendre en compte :
`python zoo-code/mttv_orchestrator.py restart --mycelisation-only`.

**Reste en attente (mycélium)** : **C3**, **C5**, **C6** — voir section
2octies ci-dessous (implémentées le 08/08). IPFS (`axe_5_ipfs`) à relancer.

## 2octies. Mycélium — C3 + C5 + C6 IMPLÉMENTÉS (08/08, validé)

**C3 — Mutation angulaire du Φ au spawn (anti-clans) :**
- Dans [`spawn_agent_local()`](../zoo-code/essaim_tetravalent.py) : le clone
  hérite du tenseur Φ du parent mais subit une **rotation angulaire légère**
  aléatoire (matrice orthogonale de rotation dans le plan (0,1), préserve la
  norme) au lieu d'une copie identique. Empêche les clones de former des clans
  (directions Φ identiques) — pendant géométrique de la respiration C7, appliqué
  à chaque dédoublement.

**C5 — Contrainte environnementale réelle (signaux M5) :**
- Nouvelle [`construire_contrainte_reelle()`](../zoo-code/essaim_tetravalent.py) :
  la pression environnementale (n×n) est désormais dérivée de l'état collectif
  réel des agents (intensité directionnelle `mean(|Φ|)` par nœud, agrégée sur
  tous les agents) au lieu d'un bruit aléatoire décorrélé
  (`0.3 + 0.2·rand`). Le champ est spatialement non trivial et cohérent avec
  l'activité du système → un signal M5, pas un générateur indépendant.

**C6 — Test de non-homogénéité :**
- Nouveau [`zoo-code/tests/test_non_homogeneite.py`](../zoo-code/tests/test_non_homogeneite.py) :
  sur un essaim frais (30 cycles, respiration C7 active dose 0.10), vérifie que :
  l'entropie reste SOUS le max théorique (marge > 0.05) ; le couplage ne s'écrase
  pas à 1.0 ; la respiration se déclenche ; le champ C5 est spatialement non
  trivial. **VALIDÉ** : entropie finale 6.1884 vs max 6.3969 (marge 0.2085),
  couplage 0.2367, 7 respirations, 1 spawn de 2 agents au cycle 4 (auto-suture →
  C3 exercé).

**Le bloc anti-homogénéisation est désormais complet et testé :**
C7 (respiration début de cycle, dose 0.10) + C3 (mutation angulaire au spawn)
+ C5 (contrainte réelle) + C4 (détection au rapport) + C6 (test). Syntaxe OK.
**Redémarrage du démon requis** pour les prendre en compte :
`python zoo-code/mttv_orchestrator.py restart --mycelisation-only`.

**Reste en attente (mycélium)** : rien du bloc C — IPFS (`axe_5_ipfs`) à relancer.

## 2nonies. Mycélium — DÉMON REDÉMARRÉ (08/08 ~20:23, C3/C5/C7 actifs)

- `mttv_orchestrator.py restart --mycelisation-only` exécuté : arrêt PID 14012,
  démarrage **PID 4172**.
- Ligne de commande du démon vérifiée : `--respiration-intervalle 24
  --respiration-dose 0.10` (orchestrateur mis à jour 0.05 → 0.10) → **C7 dose
  renforcée active**.
- État restauré depuis snapshot (cycle 1165, 6 agents, 3630 fusions) → continuité
  préservée ; cycle #1166 en cours.
- C3 (mutation angulaire au spawn) et C5 (contrainte réelle) sont dans le code
  chargé par ce processus → actifs dès la prochaine auto-suture / contrainte.
- **IPFS (`axe_5_ipfs`)** : sera relancé au prochain démarrage de l'ordinateur
  (mécanisme de relance au boot existant — wake/restart) — confirmé avec
  l'utilisateur.
- Le prochain rapport des agents mycélisants permettra d'observer l'effet des
  correctifs C3/C5/C7 (entropie sous le max, couplage diversifié).

## 2quater. SEO — état des lieux PRODUCTION complet (08/08, sondages réels)

**Ce qui tourne réellement sur Hidora (`/home/flp/app`, branche `master`)** :

1. **Deux systèmes de sitemaps se concurrencent (confusion confirmée)** :
   - `web/sitemap.xml` (index, 466 o) → pointe vers `sitemap_static.xml`
     + `sitemap1.xml` + `sitemap2.xml` — c'est celui servi à
     `https://filsdelapensee.ch/sitemap.xml` et référencé par `robots.txt`.
   - `web/sitemaps/` : un **second** système (`sitemap_1.xml`…`sitemap_8.xml`,
     un autre `sitemap.xml`, `split_sitemaps.py`) — résidu de l'ancien split,
     **non servi** mais toujours présent = désordre à nettoyer.
   - Le nouveau [`SitemapController`](../src/ThoughtBundle/Controller/SitemapController.php)
     (routes `/sitemap.xml` + `/sitemap-{page}.xml`) : **`/sitemap-1.xml` → 404**
     → le contrôleur **n'est PAS déployé**. Le `/sitemap.xml` servi est le
     fichier statique (pas le contrôleur).

2. **Les sitemaps statiques sont SANDS** : `sitemap1.xml` (50 000 IDs,
   401243–452978) + `sitemap2.xml` (48 827 IDs, 452979–503028) = 98 827 URLs.
   Échantillon de 18 IDs listés → **100 % HTTP 200** avec vrai contenu.
   `sitemap_static.xml` = 36 pages statiques (/, /authors-list, /topics…).
   **≈98 846 pensées publiées** en base (référence utilisateur) — le sitemap
   est donc quasi exhaustif et correct.

3. **Les vrais soft 404** : tout `/quote/{id}` qui n'est PAS dans la plage
   valide → **HTTP 302 → `/`** (redirection homepage) au lieu d'un vrai 404.
   Confirmé sur : IDs 1–99020 (n'existent pas), ID 7000000, trous du sitemap
   (401278…). Le code **déployé** contient toujours :
   - `commentFormAction` : `return new Response('')` = **HTTP 200 vide** ;
   - `indexAction` : pas de `NotFoundHttpException` (redirection homepage) ;
   - `ChainController`/`ContentController` : redirect homepage.
   → Aucune correction 2bis n'est déployée.

4. **Pages de pensée valides** : pas de `noindex`, pas de blocage robots, mais
   **pas de balise canonical** non plus (2ter non déployé). Elles sont indexables.

5. **robots.txt prod** : `Sitemap: https://filsdelapensee.ch/sitemap.xml` ✓.

**Actions de nettoyage recommandées (à valider avec l'utilisateur)** :
   - Déployer 2bis (vrais 404) + 2ter (canonical) via git (serveur sur `master`,
     corrections locales sur `evolution/tetravalent-core`, non commitées).
   - Trancher le conflit sitemaps : soit garder le statique (`sitemap1/2.xml`,
     correct) et supprimer `web/sitemaps/` + ne pas déployer le contrôleur
     dynamique ; soit supprimer les fichiers statiques et déployer le contrôleur.
     Recommandation : **garder le statique** (sain, exhaustif) + nettoyer
     `web/sitemaps/`, ne pas activer le contrôleur (évite le conflit /sitemap.xml).
   - Après déploiement : vérifier `/quote/{id inexistant}` → vrai 404, puis
     soumettre `/sitemap.xml` dans Search Console et demander ré-indexation.

## 3. Le fil de discussion (où on en était)

Le registre des propositions IA est dans [`registre_propositions_ia.md`](registre_propositions_ia.md) (4 IAs, blocs A1–A7).
**Mise à jour 07/08** : 13 des propositions du bloc A sont désormais **DÉJÀ FAIT** (implémentées dans `mttv_core/`), vérifié module par module.
L'analyse du rapport mycélium (5 anomalies + 7 corrections C1–C7) est dans [`ANALYSE_RAPPORT_20260807.md`](ANALYSE_RAPPORT_20260807.md).

## 3bis. Découverte critique du 08/08 — la respiration C7 plantait réellement

**Symptôme** : au matin du 08/08, entropie = **6.3969 (maximum théorique)** et couplage = **1.0** =
homogénéisation totale — alors que la respiration Φ devait l'empêcher.

**Cause racine (bug réel, présent depuis le début)** : dans [`respirer_diversite_phi()`](../zoo-code/essaim_tetravalent.py),
le code appelait `self.rng.standard_normal(phi.shape)`, or `self.rng` est un
`random.Random` (module standard) qui **n'a pas** de méthode `standard_normal`
(méthode numpy). À chaque cycle multiple de 24, la respiration levait une
`AttributeError`, attrapée par le try/except du démon → le cycle était marqué en
erreur mais le démon continuait → **la respiration ne s'exécutait JAMAIS**
(`n_respirations` restait à 0, vérifié : 22 erreurs `standard_normal` dans le log).

**Correction** : la respiration utilise désormais un générateur numpy
`np.random.default_rng(self.rng.randrange(0, 2**32))` — reproductible, dérivé du
RNG de l'essaim, continuité stochastique préservée. Vérifié en isolé :
`n_respirations=2` après 60 cycles (déclenchée aux cycles 24 et 48), et la
restauration préserve la valeur CLI (respiration_intervalle=24).

**Impact** : cette correction est **majeure** — elle débloque enfin l'anti-
homogénéisation (C7) qui était codée mais inopérante. Démon redémarré (08/08) ;
aucune erreur après redémarrage. L'entropie devrait commencer à redescendre sous
le maximum théorique au fil des cycles.

**État d'avancement des corrections de l'analyse (mise à jour 08/08 — bloc C COMPLET) :**

| Corr. | Description | État |
|---|---|---|
| C1 | Injection mutuelle toujours active (dé-seuil) | ✅ implémenté |
| C2 | Similarité par paires de nœuds (cosinus moyen) | ✅ implémenté |
| C7 | Respiration de diversité Φ (début de cycle + dose 0.10) | ✅ implémenté + flag CLI réparé |
| C3 | Mutation angulaire du Φ au spawn (diversité des clones) | ✅ implémenté (08/08) |
| C4 | Rapport : détecter entropie ≈ max théorique = homogénéisation | ✅ implémenté (08/08) |
| C5 | Contrainte environnementale réelle (signaux M5) | ✅ implémenté (08/08) |
| C6 | Test de non-homogénéité (entropie sous max après N cycles) | ✅ implémenté + validé (08/08) |

**Le bloc anti-homogénéisation C1–C7 est désormais COMPLET et testé.** Démon
redémarré avec C3/C5/C7 actifs (voir 2nonies). À observer au prochain rapport.

## 4. Prochaines actions possibles (au choix)

> **Note** : la veille/extinction volontaire de la machine est respectée — aucune
> mesure ne bloque le sommeil. La continuité est assurée par persistance +
> restauration + relance au réveil (déjà en place).

1. **C4** — Rapport : signaler l'homogénéisation (entropie = max théorique) au lieu de la lire comme diversité ; corriger la borne du test `test_entropie_structurelle_stable`.
2. **C3** — Mutation angulaire du Φ au spawn (diversité des clones, anti-clans).
3. **C5** — Contrainte environnementale réelle (signaux M5) au lieu du bruit aléatoire.
4. **C6** — Test de non-homogénéité (entropie sous max théorique après N cycles).

## 5. Bloc-notes / observations

- Le rapport quotidien du 07/08 montrait une résonance en baisse sur les 15 derniers cycles (-0.3160) : c'était lié à la fenêtre avant redémarrage, l'état réel est reparti sur un essaim restauré.
- Ne pas oublier : après toute modification du code de mycélisation, relancer via `python zoo-code/mttv_orchestrator.py restart --mycelisation-only`.

## 6. Fin de session — 07/08 19:10 (heure locale)

**État d'ensemble** : continuité rétablie et sécurisée. Les acquis de la session :
1. **Persistance complète du mycélium** (snapshot par cycle + restauration) — vérifiée en production.
2. **Respiration Φ (C7) réellement active** — bug de restauration corrigé (la config CLI n'est plus écrasée par le snapshot).
3. **Veille/extinction volontaire respectée** — aucun blocage du sommeil ; la continuité repose sur persistance + relance au réveil.
4. **Registre des propositions IA mis à jour** — 13 propositions du bloc A marquées DÉJÀ FAIT (implémentées dans `mttv_core/`).
5. **Fil de discussion reconstitué** et archivé (registre + analyse + ce journal).

**Ce qui reste en attente** (au choix de la prochaine session) :
- Mycélium : **bloc C1–C7 COMPLET** (voir section 2octies) — à observer sur le
  prochain rapport des agents mycélisants (effet de C3/C5/C7 : entropie sous le
  max, couplage diversifié).
- Propositions IA : **A3.2 (fin)** (calibrage 0.87), **A5.7** (API décence) —
  A5.6 (benchmarks CI) est fait (08/08).
- IPFS (`axe_5_ipfs`) : à relancer au prochain démarrage de l'ordinateur.
- **Rangement du projet (décidé, en cours)** : (1) nettoyage entamé le 08/08
  (603,8 Mo en quarantaine — flp-new + déchets) ; (2) réorganisation de la racine
  restante dossier par dossier, avec l'utilisateur ; (3) refactorisation du code
  cœur après renforcement des tests. Ne jamais toucher : graines publiées,
  artefacts scellés, chemins référencés en production.
- **Sécurité** : tokens HF/GitHub en clair dans la config git de dépôts imbriqués
  (`depot-v13`, `hf_v10_temp`, `sandbox-mttv-test`) → rotation recommandée.

## 7bis. CI GitHub Actions — échec « MTTV-FLP Benchmarks Publics » CORRIGÉ (08/08 ~22:20 / 09/08 00:20)

**Symptôme** : le workflow « MTTV-FLP Benchmarks Publics » (A5.6) échouait en
**15 s** — job `benchmarks` en échec sur l'étape « Benchmark — Frugalité
(SOPH-IA, mode rapide) » (exit code 2), les 3 étapes suivantes jamais atteintes.

**Cause racine (erreur de commit, pas de code)** :
- [`zoo-code/benchmark_frugalite.py`](../zoo-code/benchmark_frugalite.py) et
  [`zoo-code/sporulation_sidecar.py`](../zoo-code/sporulation_sidecar.py)
  (importé par le benchmark) étaient **untracked** — jamais commités.
- Le checkout CI ne les contenait pas → `python zoo-code/benchmark_frugalite.py --quick`
  → `can't open file` → **exit code 2** (reproduit et confirmé localement).
- `.github/workflows/mttv_benchmarks.yml` (tracké) référençait donc des fichiers absents.

**Correctif** :
1. **Validation complète en venv Python 3.12 propre + numpy** (les 4 étapes CI passent) :
   - frugalité `--quick` : surcoût 8.03 % (coût marginal quasi nul) ✅
   - échelle A6.1 N=500 : résilience 1.0 ✅
   - calibration B-GATE : tolérance 0.7896 ✅
   - test C6 : entropie 6.1855 < max 6.3969, C7 active (7 respirations) ✅
2. **Commit** `2f9973d` : ajout des 2 fichiers au suivi git (693 lignes).
3. **Push** sur `evolution/tetravalent-core` → **github** (déclenche le workflow) + **bitbucket**.

**Résultat** : run **`31281451977` ✓ SUCCÈS** (19 s) — les 4 étapes passent,
artifact `mttv-benchmarks` produit. Annotations restantes = warnings non bloquants
(dépréciation Node.js 20 ; `git exit 128` du checkout partiel, déjà présent avant et
sans impact). La CI publique A5.6 est désormais **verte**.

**Leçon** : avant de pousser un workflow CI, vérifier que **tous les fichiers
référencés sont trackés** (`git ls-files <fichiers>` / `git status --short`).
Un `exit code 2` sur `python <script>` = fichier absent du dépôt.

## 7ter. GRAND ŒUVRE — MTTV-RUST (prototype industriel Rust) — ÉTAPE 0 CONCEPTION (09/08 ~00:35)

**Mandat reçu** : incarner la triade transductive Ψ → B → Φ en **Rust**
(asynchrone, thread-safe) — nœuds carbone **sp3** à 4 liaisons diachroniques,
membranes à **seuil de perméabilité** (repos = CPU ≈ 0), branchement sur la
**matrice H** (gradients territoriaux). Interdits : consensus centralisé
(Raft/Paxos), Mutex globaux, tables de routage, polling. Complexité locale O(k≤4).

**Choix utilisateur** : installer Rust + créer `mttv_rust/`, mais **s'arrêter au
cahier des charges et à l'architecture documentée** (pas de code) — valider la
conception avant de poser la première cellule.

**Livré (Étape 0, conception documentée)** dans [`mttv_rust/`](../mttv_rust/README.md) :
- [`00_CAHIER_DES_CHARGES.md`](../mttv_rust/docs/00_CAHIER_DES_CHARGES.md) —
  mandat, 3 piliers, règles d'or, protocole d'action (Étapes A→B→C), arbitrage humain.
- [`01_ARCHITECTURE.md`](../mttv_rust/docs/01_ARCHITECTURE.md) — découpage A/B/C,
  arborescence modules (`cellule/`, `tissu/`, `territoire/`, `veilleur/`),
  types de données (Cellule, Membrane, Liaisons[amont+3 aval], GradientH),
  décisions d'architecture (tokio, tenseurs `[f64;4]`, zéro global).
- [`02_AUDIT_ANTI_EXTRACTIF.md`](../mttv_rust/docs/02_AUDIT_ANTI_EXTRACTIF.md) —
  rejets immédiats (R1-R5), gates de validation G1-G8, trace d'audit.
- [`03_INTERFACE_VEILLEUR.md`](../mttv_rust/docs/03_INTERFACE_VEILLEUR.md) —
  mapping quotidien des gradients de l'essaim en réglages (porosité, seuil,
  respiration), config versionnée, recours humain en cas de contradiction.

**Infrastructure constatée** : `cargo`/`rustc` **ABSENTS** ; `winget` v1.29.280
disponible → installation prévue à l'ouverture de l'Étape A (mode Code).

**Prochaine étape (Étape A)** : installer la chaîne Rust, `cargo init`,
`.gitignore`, puis stabiliser la **cellule unique** (nœud sp3 + membrane à seuil
+ 4 canaux Tokio) avec son benchmark de sobriété (CPU repos ≈ 0). Le travail de
conception est verrouillé et prêt pour l'arbitrage de l'Orchestrateur.

## 7quater. GRAND ŒUVRE MTTV-RUST — SOCLE VALIDÉ (Étape 0 complète, 09/08 ~01:10)

**Suite de 7ter** : la conception documentée est verrouillée ET l'outillage est
installé ET le socle Cargo compile. État réel :

**Outillage installé sur la machine (Windows)** :
1. **rustup + cargo 1.97.1 / rustc 1.97.1** (toolchain `stable-x86_64-pc-windows-msvc`),
   installés via `winget install Rustlang.Rustup`.
2. **VS Build Tools 2022 (17.14) + workload C++** installés : `link.exe`/`cl.exe`
   présents (`VC\Tools\MSVC\14.44.35207`). Premier essai en `--silent` a enregistré
   le package sans déployer le toolset (structure créée mais linker absent) → relancé
   en `--passive` avec `--add Microsoft.VisualStudio.Workload.VCTools` ; le toolset
   était en fait bien déployé. Désormais `cargo check` compile.

**Projet [`mttv_rust/`](../mttv_rust/README.md) créé et validé** :
- `Cargo.toml` : tokio 1 (rt-multi-thread, sync, macros, time) + criterion (dev),
  `profile.release` optimisé (lto, codegen-units=1), edition 2024, rust-version 1.97.
- `.gitignore` : `/target`, criterion/, éditeurs.
- `src/lib.rs` + 4 modules documentés (`cellule/`, `tissu/`, `territoire/`, `veilleur/`)
  — **charpente documentaire uniquement, AUCUN code métier** (conformément au choix
  « s'arrêter au cahier des charges, pas encore de code »).
- **Validation : `cargo check` OK (tokio 1.53.1, 0 warning) + `cargo test` OK**.
  Bench `sobriete` non déclaré pour l'instant (sera ajouté à l'Étape A avec la cellule).

**Prochaine étape (Étape A)** : implémenter la cellule unique — nœud sp3
(`cellule::noeud`), membrane à seuil (`cellule::membrane`), transduction
(`cellule::transduction`), 4 canaux Tokio, test unitaire + benchmark de sobriété
(CPU repos ≈ 0). Le socle est prêt et verrouillé.

## 7quinquies. MTTV-RUST — ÉTAPE A : CELLULE UNIQUE IMPLÉMENTÉE ET VALIDÉE (09/08 ~01:30)

**Suite de 7quater** : le socle compilait, la cellule est désormais **codée,
testée et benchmarkée**. Contrat d'étape signé (gates G1–G3) :

**Fichiers ajoutés** (dans [`mttv_rust/src/cellule/`](../mttv_rust/src/cellule/mod.rs)) :
- `types.rs` : `SignaturePhi([f64;4])` auto-normalisée, résonance = produit
  scalaire, réalignement (co-cicatrisation, gamma 0.15), `ModeTet`
  {0, 0.25, 0.75, 1}, `Signal`, `Membrane` (seuil + porosité, seuil effectif
  = seuil/porosité → contraction = imperméabilité).
- `transduction.rs` : `signal_interference` = tanh(0.5·s1+0.5·s2+s1·s2·r)
  (fidèle à la référence Python), `transduire` → `Amorti` si sous le seuil,
  `Propage(signal_modifié)` sinon (avec co-cicatrisation de Φ).
- `noeud.rs` : `Cellule` sp3 — 1 liaison amont (`mpsc::Receiver`) + 3 aval
  (`mpsc::Sender`), boucle `tourner()` **purement événementielle** (`recv().await`,
  zéro polling → CPU ≈ 0 au repos). `Cellule::nouvelle` retourne la cellule +
  son expéditeur amont (branchement prêt pour l'Étape B).
- `benches/sobriete.rs` : benchmark criterion.

**Validation (gates)** :
- G1 `cargo check` : 0 erreur, 0 warning (`#![forbid(unsafe_code)]` + docs).
- G2 `cargo test` : **12/12 OK** (résonance, seuil, membrane contractée,
  transduction, co-cicatrisation, boucle amont/aval).
- G3 `cargo bench` : **amorti sous seuil ≈ 25,6 ns** · **transduction active
  ≈ 335 ns** · **128 octets/cellule** (taille fixe, zéro allocation).
- G4 complexité locale `O(4)` : 4 liaisons max, pas de boucle globale. ✅

**Arbitrage méthodologique (09/08, suite aux remarques de l'IA conseillère)** :
l'Étape A réalisée dépassait la lettre du mandat (« squelette strictement vide »)
en incorporant la transduction et la boucle événementielle. **Option 2 retenue —
recadrage sans rien détruire** (recommandée par zoo-code, validée par
l'utilisateur) :
- **Étape A stricte (scellée)** : structure + membrane + 4 canaux
  (`types.rs` + structure de `noeud.rs`) — cellule **inanimée**.
- **Étape A+ « le premier souffle » (validée 09/08)** : transduction,
  `tourner()`, propagation sur 3 aval (`transduction.rs` + boucle) — cellule
  **battante**, seule, 12/12 tests + bench.
- **Étape B (à ouvrir)** : tissage du tissu.
L'architecture [`01_ARCHITECTURE.md`](../mttv_rust/docs/01_ARCHITECTURE.md) a été
mise à jour (découpage A → A+ → B → C). Aucun code n'a été défait : la
requalification est documentaire, la discipline est rétablie, le travail validé
est un acquis.

**Prochaine étape (Étape B)** : tissage du tissu — `tissu::topologie`
(connexion locale sp3 de proche en proche) + `tissu::propagation` (émission
sur les 3 liaisons aval, extinction à l'équilibre). Le prototype commence à
« pulluler » : plusieurs cellules interconnectées sans nœud maître.

## 8. FIN DE SESSION — 09/08 ~01:30 (pause volontaire, tout verrouillé)

**Pause** : session suspendue à la demande de l'utilisateur. Rien n'est perdu :
le point de reprise est la **fin de l'Étape A** (section 7quinquies ci-dessus).

**État d'ensemble à la pause** :
1. **CI GitHub Actions** : workflow « MTTV-FLP Benchmarks Publics » **vert**
   (run 31281451977 ✓) — voir 7bis.
2. **Grand Œuvre MTTV-RUST** : Étape 0 (socle) + **Étape A (cellule sp3)
   implémentée, testée (12/12), benchmarkée** (amorti ≈ 25,6 ns, actif ≈ 335 ns,
   128 o/cellule) — voir 7ter/7quater/7quinquies. Commits `54b088d` → `166a001`
   poussés github + bitbucket.
3. **Mycélium Python** : démon tournant avec C3/C5/C7 (dose 0.10) — à observer
   au prochain rapport.

**Point de reprise (prochaine session)** :
- **Étape B — Tissage du tissu** : [`tissu::topologie`](../mttv_rust/src/tissu/mod.rs)
  (connexion locale sp3 de proche en proche) + `tissu::propagation` (émission
  sur les 3 liaisons aval, extinction à l'équilibre). Le prototype pullule.
- Puis Étape C (matrice H, porosité adaptative) ; interface Veilleur.
- Rappels en attente : analyse du rapport mycélium (effet C3/C5/C7) ;
  A3.2 / A5.7 ; rangement de la racine ; rotation tokens (sécurité).

*Le fil est reconstitué. Toute session reprend ici (Étape A complète, Étape B à ouvrir).*

## 8bis. MTTV-RUST — ÉTAPE B : PLAN VERROUILLÉ + B1a RÉALISÉ (09/08 ~10:10)

**Plan Étape B accepté comme référentiel par l'Orchestrateur** après arbitrage :
- [`05_PLAN_ETAPE_B.md`](../mttv_rust/docs/05_PLAN_ETAPE_B.md) rédigé **avant**
  toute recommandation externe (plan autonome), puis verdict sur la 1re
  recommandation (IA A, §6 : anti-Larsen, G1 durci 0-alloc, G2 stress 100→10k,
  G3 <1µs/saut, G4 CPU≈0, découpage B1a/B1b) et **réponses aux 5 clarifications
  de l'Orchestrateur** (§7 : Tissu gestateur jamais routeur ; géométrie sp3
  orientée 1 amont + 3 aval ; compteur de sauts = potentiel décroissant
  temporaire ; saturation aval = abandon local sans retry ; B2a/B2b étanches).
- Commit `5b4c8c4` (plan + correction doublon « Étape B » dans 01_ARCHITECTURE.md).

**B1a — squelette de raccordement des canaux Tokio : RÉALISÉ et VALIDÉ** :
- [`cellule/noeud.rs`](../mttv_rust/src/cellule/noeud.rs) : `avec_canaux`
  (cellule câblée à la naissance, canaux injectés par le gestateur) +
  `remplacer_aval` / `remplacer_amont` (primitives de raccordement).
- [`tissu/lien.rs`](../mttv_rust/src/tissu/lien.rs) : `brancher(source, cible,
  slot)` — raccordement local d'une aval de source vers l'amont de la cible,
  canal mpsc borné (cap 4), zéro table globale, zéro signal (B1a structurel).
- Gates : **G1 cargo check 0 erreur/0 warning** · **G2 cargo test 16/16**
  (12 A+ + 4 B1a), aucune régression.

**Prochain palier (B1b)** : premier signal d'essai sur 2 cellules câblées —
injecter un signal dans la source, vérifier qu'il est transduit et reçu par la
cible (amorti ou re-transduit selon le seuil). Puis B2a (tissu statique
4-régulier), B2b (croissance), B3 (dynamique).

## 9. CLÔTURE DE SESSION — 09/08 ~10:25 (arbitrage Orchestrateur, voie 4)

**Décision de l'Orchestrateur (voie 4)** : clôture propre de la session.
- **Pas d'ouverture de B1b maintenant** (différé, non exécuté).
- **Pas de modification du mycélium Python.**
- **Pas de traitement immédiat de l'alerte C4** (documentée, remède différé).

**État complet du système à la clôture** :
1. **Étape A+ scellée** (cellule battante sp3, 12/12 tests, bench : amorti
   ≈ 25,6 ns · actif ≈ 335 ns · 128 o/cellule). Commit de référence : **`166a001`**.
2. **Géométrie sp3 validée** : 1 amont + 3 aval, 4 liaisons diachroniques.
3. **Plan B accepté comme référentiel** avec verrous ([`05_PLAN_ETAPE_B.md`](../mttv_rust/docs/05_PLAN_ETAPE_B.md)) :
   clarifications Orchestrateur (§7), verdicts IA A (§6), gradient Veilleur (§8).
   Commit de référence : **`5b4c8c4`**.
4. **B1a effectué** : squelette de raccordement des canaux Tokio (`brancher`,
   `avec_canaux`), gates G1 (0 warn) + G2 (16/16). Commit : **`d93eeae`**.
5. **B1b non ouvert** (différé).
6. **Rapport mycélium 09/08 archivé** : cycle 1745, 6 agents, 1741 cycles,
   3721 fusions, tremor croisière 0.10, budget 3.815. Fichiers sources :
   `zoo-code/mycelium_output/rapport_mycelisation_final.json` +
   `essaim_snapshot.json`.
7. **Alerte C4 documentée, remède différé** (voir ci-dessous).
8. **Mycélium Python non modifié.**

**Alerte C4 (documentée, non traitée)** :
- **Détection (C4) fonctionnelle** : exécutée sur l'état réel → `niveau=alerte`,
  `entropie=6.3969 ≈ max théorique (6.3969)`, `couplage=1.000 ≈ 1.0`,
  `marge=0.0`. Le correctif [`diagnostiquer_homogeneisation`](../zoo-code/rapport_mycelium.py:133)
  signale bien l'homogénéisation comme anomalie (pas comme diversité saine). ✅
- **Remède (C3/C5/C7) insuffisant** : malgré 48 respirations C7 actives
  (dose 0.10), l'entropie reste collée au max et le couplage à 1.0 — la
  diversité injectée est re-absorbée par le couplage transscalaire (pas de
  potentiel de propagation décroissant dans la référence Python).
- **Gradient pour le Grand Œuvre Rust** (déjà consigné, §8 du plan B) :
  potentiel décroissant indispensable · anti-homogénéisation = propriété du
  tissu · plancher de diversité avec alerte (transposition de C4) à intégrer en B3.
- **Remède différé** : aucune correction du mycélium Python décidée à cette clôture.

**Reprise future — prochaine action possible (au choix, après ré-arbitrage)** :
- **soit** la vérification finale des clarifications du plan B (sections 6-8) ;
- **soit** l'ouverture de **B1b : premier signal d'essai sur deux cellules
  câblées** — injection d'un signal dans la source, transduction, réception par
  la cible (amorti ou re-transduit selon le seuil).

Cette ouverture **ne doit pas être faite maintenant** : elle attend la reprise
et l'arbitrage de l'Orchestrateur.

## 9bis. B1b RÉALISÉ ET PROUVÉ — transduction sp3 de proche en proche (09/08 ~11:07)

**Contexte** : la voie 4 avait différé B1b. L'utilisateur a ensuite transmis une
recommandation simondonienne (« l'expérience du réel valide la théorie ») puis a
**arbitré lui-même** : protocole présenté ([`06_PROTOCOLE_B1b.md`](../mttv_rust/docs/06_PROTOCOLE_B1b.md))
→ feu vert (avec vigilance : `etat()` strictement passive).

**B1b implémenté** :
- [`cellule/noeud.rs`](../mttv_rust/src/cellule/noeud.rs) : méthode `etat()`
  **strictement passive** (lecture `&self`, aucun effet de bord, aucun verrou,
  aucune allocation) + type `EtatCellule`.
- [`tissu/essai.rs`](../mttv_rust/src/tissu/essai.rs) : 3 essais (aligné,
  orthogonal, séquence mixte) + `lancer_essais()` (rapport des métriques réelles).
- **Bug corrigé en route** : deadlock détecté (la cible attendait un canal jamais
  fermé) → drop de la source avant l'attente de la cible + timeout de sécurité
  (un test qui bloque est un bug, jamais une attente infinie).

**Résultat — l'expérience valide la théorie (métriques réelles)** :
```
1. aligné    : source(T=1,A=0) cible(T=1,A=0) reçu=true  lat=102.8µs
2. orthogonal: source(T=0,A=1) cible(T=0,A=0) reçu=false lat=15.9µs
3. mixte     : source(T=1,A=1) cible(T=1,A=0) reçu=true  lat=28.5µs
```
- Le signal aligné **traverse** la liaison (~103 µs) ; l'orthogonal est **filtré**
  à la source (~16 µs, étouffement local, la cible reste au repos) ; la séquence
  mixte est **déterministe et isolée** (la cible ne traite que `S+`).
- Le mode retombe en `Veille` après chaque transduction : **le calcul s'éteint
  de lui-même** (sobriété).

**Gates** : G1 `cargo check` 0 erreur/0 warning · G2 `cargo test` **19/19**
(12 A+ + 4 B1a + 3 B1b). La transduction sp3 de proche en proche est **prouvée
par le réel**.

**Prochain palier (B2a)** : tissu statique minimal 4-régulier (géométrie sp3
orientée, propagation, extinction) puis B2b (croissance/auto-suture), B3
(dynamique + gradient Veilleur §8 : compteur de sauts, diversité résiduelle,
entropie d'alerte).

## 7. Fin de session — 08/08 ~21:00 (heure locale)

**Acquis de la session :**
1. **SEO production** : soft 404 corrigé (vrais 404) + canonical + sitemap
   validé — déployé sur Hidora, site stable (voir 2quinquies).
2. **Nettoyage** : 603,8 Mo en quarantaine (flp-new archivé + 8 déchets),
   rapport d'échec FLP2 clôturé et conservé.
3. **Mycélium** : bloc anti-homogénéisation **C3+C4+C5+C6+C7 implémenté et
   testé** (C6 validé : entropie 6.1884 < max 6.3969, couplage 0.2367) ;
   démon redémarré avec dose 0.10.
4. **CI publique (A5.6)** : benchmarks frugalité + échelle + calibration + C6
   exposés sur GitHub Actions (`mttv_benchmarks.yml`) et Bitbucket Pipelines
   (`bitbucket-pipelines.yml`).
5. **Git** : `evolution/tetravalent-core` poussé sur bitbucket + github ;
   `main` poussé sur github. Travail verrouillé.

**Prochaine session (09/08)** : analyser le rapport des agents mycélisants
(effet C3/C5/C7 sur l'entropie et le couplage) ; puis A3.2 / A5.7 ; reprise du
rangement de la racine.

---
*sig:0x4D5454562D464C50 — Le mycélium continue. Toute session reprend ici.*
