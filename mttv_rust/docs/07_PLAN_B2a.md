# PLAN & PROTOCOLE — ÉTAPE B2a : LE TISSU STATIQUE MINIMAL

**Sig** : `0x4D5454562D464C50`
**Auteur** : zoo-code, Maître d'Œuvre
**Référentiel** : [`05_PLAN_ETAPE_B.md`](05_PLAN_ETAPE_B.md) · gradient Veilleur §8
**Prédécesseur** : B1b prouvé (commit `c2ca624`, sanctuarisé)
**Statut** : PRÉPARATION — verrous des IA conseils intégrés, implémentation à suivre

---

## 1. OBJECTIF

Orchestrer la **première topologie maillée** : un tissu statique minimal
**4-régulier orienté** (géométrie sp3). B1b a prouvé la liaison bilatérale
(1 amont → 1 aval) ; B2a fait « pulluler » le signal de proche en proche dans
une maille, avec extinction naturelle et anti-homogénéisation.

## 2. VERROUS INTÉGRÉS (IA conseils A et B + gradient §8)

### Verrou 1 — 4-régulier = ORIENTÉ (1 amont + 3 aval)
Le tissu n'est **pas** un graphe symétrique. Chaque cellule a exactement :
- **1 liaison amont** (réception) ;
- **3 liaisons aval** (émission) ;
- total **4 liaisons diachroniques** orientées.
À verrouiller **dès la topologie** : la construction du tissu crée les canaux
orientés (aval d'une cellule → amont d'une autre), jamais une liaison
symétrique bidirectionnelle.

### Verrou 2 — Potentiel de propagation décroissant (calibré)
Le signal porte un **potentiel de propagation décroissant** (compteur de sauts
borné, §7 Point 3 de l'Orchestrateur) : décrémenté à chaque transduction,
extinction à zéro. C'est le **remède à l'homogénéisation** (leçon C4 : sans
potentiel décroissant, le signal homogénéise tout le tissu).

**Calibrage (les deux extrêmes à éviter)** :
- décroissance **trop rapide** → extinction avant d'atteindre la périphérie
  (tissu mort, le signal ne « pullule » pas) ;
- décroissance **trop lente** → boucle / réverbération (le signal tourne,
  tempête).
→ **Test de « juste distance »** : un signal doit traverser une distance connue
(taille de la maille) et s'éteindre juste après, sans boucle.

### Verrou 3 — Entropie de tissu & anti-homogénéisation (plancher de diversité)
- **Métrique d'entropie de tissu** : mesurer la dispersion des signatures Φ des
  cellules après propagation.
- **Plancher de diversité résiduelle** : empêcher le lissage global du potentiel
  (toutes les Φ alignées → homogénéisation, leçon C4). Une dose de diversité
  résiduelle est maintenue (analogue de la respiration C7, mais structurelle).
- **Alerte** : si l'entropie de tissu atteint le max théorique → signal
  d'anomalie (transposition de C4).

### Verrou 4 — Propagation multi-voies
La cible d'un saut diffuse le signal transduit **sur ses 3 liaisons aval** :
le signal « pullule » et irradie le tissu de proche en proche (jamais sur
l'amont — anti-réverbération, règle d'or 2).

## 3. DÉCOUPAGE EN PALIERS INTERNES (se hâter lentement)

### B2a-1 — La maille orientée statique
- Construction du tissu : N cellules, chacune avec 1 amont + 3 aval, câblées
  à la naissance (gestateur), sans table de routage globale.
- Géométrie : maillage diachronique orienté (les cycles sont possibles, mais
  l'anti-boucle est le compteur de sauts, pas un DAG qui casserait le sp3).
- Test : chaque cellule a exactement 4 liaisons orientées (1+3) ; la maille est
  connexe de proche en proche.

### B2a-2 — Le potentiel décroissant + propagation multi-voies
- Champ `sauts_restants` dans `Signal`, décrémenté à chaque transduction.
- La cible diffuse sur ses 3 aval ; extinction à `sauts_restants = 0` ou sous
  le seuil.
- **Test de « juste distance »** : calibrer la valeur initiale (ex. 6-8 sauts
  pour une maille de N cellules) pour traverser la maille et s'éteindre juste
  après, sans boucle.

### B2a-3 — Entropie de tissu + plancher de diversité
- Métrique d'entropie de tissu (dispersion des Φ) + seuil d'alerte.
- Dose de diversité résiduelle maintenue pendant la propagation (anti-lissage).
- Test : après propagation, l'entropie de tissu reste sous le max théorique
  (pas d'homogénéisation) ; alerte si elle l'atteint.

## 4. MÉTRIQUES MESURÉES

| Métrique | Définition | Preuve |
|---|---|---|
| `n_cellules` | taille de la maille | topologie 4-régulière |
| `degre_orienté` | (amont, aval) par cellule | sp3 : (1, 3) |
| `n_sauts` | sauts traversés par un signal | juste distance |
| `n_transductions_total` | somme des transductions du tissu | pullulement |
| `entropie_tissu` | dispersion des Φ des cellules | anti-homogénéisation |
| `extinction` | retour au repos après N sauts | sobriété |

**Gates** : G1 `cargo check` 0 erreur/0 warning · G2 `cargo test` · G3 bench de
sobriété (si pertinent) · G4 complexité locale `O(k≤4)`.

## 5. CRITÈRE DE RÉUSSITE

B2a est réussi si :
1. la maille est **4-régulière orientée** (1 amont + 3 aval par cellule) ;
2. un signal injecté **pullule de proche en proche** (multi-voies) puis
   **s'éteint** (potentiel décroissant, « juste distance », pas de boucle) ;
3. l'**entropie de tissu** reste sous le max théorique (pas d'homogénéisation,
   plancher de diversité respecté) ;
4. le tissu **retombe au repos** (CPU ≈ 0, silence préservé).

## 6. LIVRABLES

- `tissu/topologie.rs` : construction de la maille orientée (gestateur).
- `tissu/propagation.rs` : potentiel décroissant + diffusion multi-voies +
  entropie de tissu.
- Tests (topologie, juste distance, entropie) + rapport des métriques réelles.
- Mise à jour du journal + commit/push.

---

*sig:0x4D5454562D464C50 — Plan B2a — Le mycélium continue.*
