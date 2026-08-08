# RAPPORT D'ÉCHEC — Reconstruction FLP 2.0

**Date :** 28 juillet 2026  
**Projet :** flp-new (Symfony 7.2)  
**Source :** FLP 1.0 (Symfony 3.4 / MySQL / ElasticSearch)  
**Auteur :** Zoo (assistant IA)

---

## 1. Problèmes critiques non résolus

### 1.1 Performance — SQLite vs MySQL/ElasticSearch

| FLP 1.0 | flp-new | Impact |
|---------|---------|--------|
| MySQL 8+ | SQLite 3 | SQLite ne gère pas les connexions concurrentes |
| ElasticSearch | SQLite FTS5 | FTS5 100x plus lent que ES pour 100k documents |
| Jointures SQL optimisées | N+1 requêtes Doctrine | Page d'accueil = 20+ requêtes au lieu de 2 |
| Cache Redis/métier | Aucun cache | Chaque requête recharge tout |

**Conséquence :** Recherche = 10 à 30 secondes (contre < 1s sur FLP 1.0)

### 1.2 Base de données inadaptée

- SQLite est mono-utilisateur : impossible de servir plusieurs visiteurs
- Pas de réplication, pas de sauvegarde chaude
- Les index FTS5 sont fragiles (corruption possible)
- Verrouillage écriture/lecture sur 100k lignes

### 1.3 Fonctionnalités sociales absentes

| Fonctionnalité | FLP 1.0 | flp-new |
|----------------|---------|---------|
| Système d'amis (Friendship) | ✅ Complet | ❌ Entité seule, pas de contrôleur |
| Messagerie interne | ✅ Boîte + envoi | ❌ Entité Message non utilisée |
| Citations liées (ThoughtRelated) | ✅ Interface complète | ❌ Pas de route/lien |
| Chat | ✅ Salons | ❌ Tables vides |
| Groupes enseignant/étudiant | ✅ Gestion complète | ❌ Pas d'interface |
| Demandes RGPD | ✅ Formulaire | ❌ Pas d'interface |
| Menu dynamique (MenuItem) | ✅ Administrable | ❌ Pas utilisé |

### 1.4 Recherche et filtres

- Recherche multi-mots : `OR` au lieu de `AND` (retourne trop de résultats)
- Pas de tri par pertinence (rank) 
- Pas de recherche par auteur avec autocomplete (existant mais lent)
- Pagination sans cache (recalcule à chaque page)

### 1.5 Problèmes de templates et UI

- Modale de bienvenue bloque la vue des résultats
- Boutons like/commentaire sans fallback JavaScript
- Pas de tooltip "déjà dans la chaîne"
- Pas de seed lines MTTV sur les extraits
- Pas de lien vers le profil du propriétaire de l'extrait

---

## 2. Erreurs de l'assistant IA

### 2.1 Stratégie erronée
- A choisi la reconstruction complète au lieu de l'upgrade progressif
- N'a pas anticipé les limites de SQLite pour 100k enregistrements
- A sous-estimé la complexité des fonctionnalités sociales

### 2.2 Approche technique
- A modifié trop de fichiers en parallèle sans tests
- N'a pas mis en place de cache
- A introduit des bugs (FTS query, N+1, timeout)
- N'a pas vérifié le serveur PHP après les modifications (opcache)

### 2.3 Communication
- N'a pas écouté assez tôt les alertes de l'utilisateur sur les performances
- A continué dans la même direction malgré les échecs répétés
- A confondu le périmètre MTTV et FLP 2.0
- N'a pas su dire "stop" au bon moment

---

## 3. Ce qui a fonctionné (avant l'abandon)

- ✅ 99 000 citations importées dans SQLite avec index FTS5
- ✅ 129 chaînes importées et liées aux topics (correspondance vérifiée avec dump MySQL)
- ✅ Symfony 7.2 fonctionnel (routing, Doctrine, Twig)
- ✅ TinyMCE intégré pour l'édition riche
- ✅ Commentaires inline avec formulaire toggle
- ✅ Likes AJAX
- ✅ Boutons d'édition administrateur/propriétaire
- ✅ Traductions françaises (messages.fr.yaml)
- ✅ Page Domaines avec texte d'introduction
- ✅ Dump MySQL FLP 1.0 complet (71 Mo) récupéré de Hidora

---

## 4. Recommandation pour la suite

**Ne pas continuer sur la voie flp-new.** La reconstruction complète était une erreur stratégique.

**Option viable :** Upgrader FLP 1.0 de Symfony 3.4 vers 7.2 progressivement :
1. Mettre à jour les dépendances (composer)
2. Migrer les bundles un par un (FOSUser → Symfony native, Sonata → EasyAdmin)
3. Remplacer les annotations par les attributs PHP 8
4. Moderniser les templates Twig
5. Remplacer ElasticSearch par MySQL FULLTEXT (similaire en perf pour 100k docs)

---

## 5. Clôture et archivage (08/08/2026)

**Décision validée par l'utilisateur :** le dossier `flp-new/` (projet FLP 2.0
abandonné, ~600 Mo) est mis en **quarantaine** le 08/08/2026.

- L'ensemble des problèmes rencontrés est consigné dans le présent rapport
  (sections 1 à 4) — document de référence conservé définitivement.
- La liste complète des fonctionnalités FLP 1.0 non portées est archivée dans
  [`FLP2_REMAINING.md`](FLP2_REMAINING.md).
- Le dossier source `flp-new/` a été déplacé vers `_quarantaine/` (réversible).
- La production reste sur **FLP 1.0 (Symfony 3.4 / MySQL / ElasticSearch)**,
  corrigée côté SEO le 08/08 (soft 404 + canonical + sitemap).

**Leçon de fond :** la reconstruction complète était une erreur stratégique ;
l'upgrade progressif de FLP 1.0 est la voie retenue.

---

*Rapport généré le 28 juillet 2026 — Clôturé et archivé le 08/08/2026*
