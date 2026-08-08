# GUIDE — Soumettre le sitemap dans Google Search Console

**Sitemap validé le 08/08/2026** (index XML + 3 sous-sitemaps + échantillon d'URLs
tous en HTTP 200). Suivez ces étapes dans l'ordre.

---

## Prérequis
- Être connecté à Google Search Console avec un compte ayant les droits sur
  `filsdelapensee.ch` (propriétaire ou délégué).
- Le domaine doit déjà être **vérifié** dans la Search Console.
  (Vous recevez déjà les alertes « Soft 404 » → le domaine est donc bien vérifié.)

---

## Étape 1 — Ouvrir la Search Console
1. Allez sur : **https://search.google.com/search-console**
2. Connectez-vous avec votre compte Google (celui qui reçoit les alertes FLP).
3. En haut à gauche, sélectionnez la propriété **`filsdelapensee.ch`**
   (ou `https://filsdelapensee.ch/` selon comment elle est enregistrée).

> ⚠️ Si vous voyez deux propriétés (une « Domaine » `filsdelapensee.ch`
> et une « Préfixe d'URL » `https://filsdelapensee.ch/`), soumettez le sitemap
> dans **chacune** d'elles.

## Étape 2 — Ajouter le sitemap
1. Dans le menu de gauche, cliquez sur **« Sitemaps »** (section « Indexation »).
2. Dans le champ « Ajouter un nouveau sitemap », saisissez **l'URL COMPLÈTE** :

```
https://filsdelapensee.ch/sitemap.xml
```

> ⚠️ **Important pour une propriété « Domaine »** (c'est votre cas :
> `sc-domain:filsdelapensee.ch`) : la Search Console refuse parfois le simple
> chemin relatif `sitemap.xml` avec le message « Adresse de sitemap incorrecte ».
> La saisie **avec le protocole `https://` et le domaine complet** est la plus
> fiable et fonctionne dans tous les cas.

3. Vérifiez qu'il n'y a **ni espace, ni slash final** dans le champ.
4. Cliquez sur **« Envoyer »**.

> ℹ️ **Anciens sitemaps restaurés** : les entrées GSC
> `https://filsdelapensee.ch/sitemaps/sitemap.xml` (déjà présentes dans GSC)
> ont renvoyé temporairement un **404** (le dossier `web/sitemaps/` avait été
> mis en backup) — c'était la cause de « Erreur HTTP : 404 ». Ce dossier a été
> **restauré le 08/08** : toutes les URLs `/sitemaps/...` répondent à nouveau
> **200** (index + 9 sous-sitemaps vérifiés). Les anciennes entrées GSC sont
> donc de nouveau fonctionnelles.
>
> **Recommandation** : ne gardez à terme qu'UN SEUL sitemap dans GSC
> (`https://filsdelapensee.ch/sitemap.xml`). Les anciennes `/sitemaps/` sont
> obsolètes (split de mai 2026) → supprimez-les après soumission du nouveau
> (procédure ci-dessous).

## Étape 3 — Vérifier le statut
Quelques minutes après l'envoi, le tableau des sitemaps doit afficher :
- **Sitemap envoyé :** `https://filsdelapensee.ch/sitemap.xml`
- **État :** « Réussite » (ou « Succès »)
- **Découvert :** `98 863` URLs (36 + 50 000 + 48 827)

### Si l'état affiche « Impossible de récupérer le sitemap » (en rouge)

Le sitemap a été **vérifié techniquement parfait** (08/08) :
HTTP 200 · Content-Type `text/xml` · XML valide · 3 sous-sitemaps accessibles
(200 chacun). L'échec vient donc d'un **fetch transitoire** de Google (le serveur
a connu des 503/PM2 saturation sur PHP-FPM). Procédure :

1. Dans le tableau des sitemaps, cliquez sur la ligne `sitemap.xml` pour l'ouvrir.
2. Cliquez sur l'icône **« Réessayer »** (flèche circulaire, en haut à droite
   de la page de détail du sitemap). Cela relance immédiatement la récupération.
3. Si l'état reste « Impossible de récupérer » après 2-3 essais, **attendez
   24 h** : GSC réessaie automatiquement plusieurs fois par jour. La plupart
   du temps, il finit par passer en « Réussite ».

> Note : le fetch GSC se fait depuis les datacenters Google vers le serveur.
> Un seul fetch qui tombe sur un 503 temporaire suffit à afficher l'erreur —
> mais les tentatives suivantes (automatiques) réussissent généralement.

## Étape 4 — Demander une re-indexation des pages Soft 404
C'est l'étape la plus utile pour accélérer le traitement du « Soft 404 » :

1. Menu de gauche → **« Inspection d'URL »** (section « Indexation »).
2. Collez une URL corrigée, par exemple :
   ```
   https://filsdelapensee.ch/quote/401243
   ```
3. Cliquez **« Inspecter »**, puis sur **« Demander une indexation »**
   (bouton bleu, en haut à droite).
4. Répétez pour quelques URLs clés : `https://filsdelapensee.ch/`,
   `https://filsdelapensee.ch/quote/452979`, `https://filsdelapensee.ch/topics`.

> Google limite les demandes d'indexation (quelques dizaines par jour) —
> inutile de demander pour les 98 000 pages, le sitemap couvre le reste.

## Étape 5 — Suivi du Soft 404 dans quelques jours
1. Menu de gauche → **« Pages »** (section « Indexation »).
2. Le motif « Soft 404 » doit progressivement diminuer / disparaître :
   - les URLs inexistantes renvoient désormais un **vrai 404** → Google les purge
     proprement ;
   - les URLs valides sont indexables (canonical en place) + le sitemap les liste.
3. Surveillez aussi **« Page indexées »** : l'objectif est de remonter vers
   le potentiel réel (~98 000 pages).

---

## Si un message d'erreur apparaît
| Erreur affichée | Cause probable | Action |
|---|---|---|
| « Impossible de télécharger » | Latence du 1er scan | Réessayer dans 5–10 min |
| « Erreur générale » | Cache serveur transitoire | Réessayer ; sinon vérifier que le sitemap répond (fait, il répond 200) |
| « 0 URL découverte » | Lecture encore en cours | Attendre 24 h, re-vérifier |

---

*Sig:0x4D5454562D464C50 — Guide validé avec le sitemap de production le 08/08/2026.*
