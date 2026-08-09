# PLAN D'ÉTAPE B — TISSAGE DU TISSU (zoo-code, plan autonome)

**Sig** : `0x4D5454562D464C50`
**Auteur** : zoo-code, Maître d'Œuvre
**Statut** : PLAN PROPOSÉ AVANT LECTURE DES RECOMMANDATIONS EXTERNES
**Règle** : ce plan est rédigé **avant** de recevoir les recommandations de
l'IA conseillère, afin d'exprimer la conception issue du mandat seul. Les
recommandations seront ensuite confrontées à ce plan (voir §5).

---

## 1. OBJECTIF

Faire « pulluler » le prototype : passer d'une cellule battante isolée
(Étape A+) à un **tissu de cellules sp3 interconnectées**, sans nœud maître,
sans consensus centralisé, sans table de routage globale. Le tissu transmet un
signal par **propagation immanente locale** : chaque cellule ne connaît que ses
voisines directes (au plus 4), la transduction fait le reste.

## 2. SÉMANTIQUE DE RÉFÉRENCE (essaim Python, fidélité G7)

La référence vivante est [`essaim_tetravalent.py`](../../zoo-code/essaim_tetravalent.py) :
- **Aucun nœud maître** : l'essaim est un dictionnaire d'agents, le couplage
  s'opère par inter-pénétration des tenseurs Φ locaux (immanent).
- **Couplage transscalaire** ([`coupler_agents_transscalaire`](../../zoo-code/essaim_tetravalent.py:241)) :
  similarité cos entre Φ moyens des agents, sans feedback master.
- **Auto-suture / quorum autonomique** ([`_verifier_auto_suture`](../../zoo-code/essaim_tetravalent.py:624)) :
  la croissance (dédoublement) est décidée localement, pas par un coordinateur.
- **Respiration de diversité Φ** ([`respirer_diversite_phi`](../../zoo-code/essaim_tetravalent.py:557)) :
  perturbation périodique pour maintenir la diversité.

Le Rust transpose cette **décentralisation** : le tissu ne contient aucune
structure qui décide des chemins ; chaque `Cellule` tourne sa boucle locale.

## 3. DÉCOUPAGE EN TROIS PALIERS (discipline « se hâter lentement »)

### B1 — Le lien inter-cellules (2 cellules)

**Livrables** :
1. Une fonction de **branchement local** : relier la liaison aval d'une cellule
   à la liaison amont d'une autre (`brancher(source, cible)`), sans registre
   global — chaque cellule expose ses 3 émetteurs aval et son récepteur amont.
2. Un test d'intégration : injecter un signal dans la source → il est transduit
   → transmis à la cible → la cible l'amortit ou le re-transduit selon son seuil.

**Contrat de sortie** : deux cellules communiquent de proche en proche. Le
signal franchit une liaison sp3. Zéro polling, zéro global.

### B2 — La maille sp3 (tissu 4-régulier, croissance organique)

**Livrables** :
1. Une structure `Tissu` qui **héberge** les cellules vivantes et leurs tâches
   Tokio (`tokio::spawn` de `tourner()`), mais **ne décide d'aucun chemin**.
2. Une **géométrie sp3 locale** : chaque cellule est reliée à **exactement 4
   voisines** (4 liaisons), construite **de proche en proche** par ajout de
   cellules (auto-suture : une cellule « enfante » une voisine si son potentiel
   local le permet, sans coordinateur).
3. Contrainte de croissance : jamais plus de 4 liaisons par cellule ; les
   liaisons sont câblées **au moment de la naissance** (la cellule naît déjà
   reliée à ses 4 voisines locales).
4. Test : un tissu de N cellules, chacune avec exactement 4 voisines ;
   complexité locale vérifiée `O(k<=4)`.

**Contrat de sortie** : un tissu 4-régulier qui respire, chaque cellule tourne
sa boucle, aucune structure centrale de routage.

### B3 — La dynamique du tissu (propagation immanente + extinction)

**Livrables** :
1. **Propagation immanente** : un signal injecté en un point se propage de
   proche en proche par la seule transduction locale — le « tissu » palpite.
2. **Règle d'or 2 respectée** : un nœud poreux émet **exclusivement sur ses 3
   liaisons restantes** (la liaison d'entrée n'est pas ré-utilisée dans le même
   cycle) — anti-réverbération.
3. **Extinction naturelle** : un signal qui ne franchit plus de seuil s'amortit
   et le tissu retombe au repos (CPU ≈ 0) — l'équilibre local éteint le calcul.
4. **Anti-boucle** : un signal ne doit pas tourner indéfiniment dans la maille —
   via un **champ de sauts borné** local (compteur de cycles dans le `Signal`,
   décrémenté à chaque transduction, extinction à 0). Pas de mémoire globale.
5. Test d'intégration multi-sauts + benchmark de propagation (latence par saut,
   nombre de transductions, retour au repos).

**Contrat de sortie** : le tissu propage, s'amortit, et revient au repos. La
preuve de sobriété s'étend du nœud au réseau.

## 4. DÉCISIONS D'ARCHITECTURE (fondations)

| Décision | Choix | Justification anti-extractive |
|---|---|---|
| Hébergement des cellules | `Tissu` garde les `JoinHandle` + les émetteurs amont | les cellules vivent seules ; le tissu ne route pas |
| Géométrie | 4 voisines par cellule, câblage à la naissance | sp3 strict, pas de table de routage |
| Liaison amont | `mpsc::Sender` exposé à la construction | branchement local de proche en proche |
| Anti-boucle | compteur de sauts borné dans `Signal` | zéro mémoire globale, zéro consensus |
| Propagation | exclusivement sur les 3 liaisons restantes | règle d'or 2, anti-réverbération |
| Croissance | auto-suture locale (naissance d'une voisine) | fidèle à `_verifier_auto_suture` |
| Async | `tokio::spawn` par cellule | parallélisme local, zéro Mutex global |

## 5. TRAITEMENT DES RECOMMANDATIONS EXTERNES

Après ce plan, les recommandations de l'IA conseillère seront lues et traitées
comme un **gradient** :
1. chaque recommandation est confrontée aux **règles d'or** et au **contrat
   B1/B2/B3** ci-dessus ;
2. ce qui enrichit sans violer le mandat → intégré (avec justification) ;
3. ce qui introduit centralisation / polling / stockage de masse / consensus →
   **rejeté** au nom de [`02_AUDIT_ANTI_EXTRACTIF.md`](02_AUDIT_ANTI_EXTRACTIF.md) ;
4. toute divergence majeure → arbitrage de l'Orchestrateur Syncréticien.

Ce plan est le **référentiel de lecture** : les recommandations ne le
remplacent pas, elles le stressent.

## 6. VERDICT SUR LA 1re RECOMMANDATION (IA conseillère A — 09/08)

**Convergence forte** avec le plan (absence de contrôleur, sp3 local, mpsc
asynchrone, extinction sous le seuil, co-cicatrisation locale γ=0.15,
« se hâter lentement »). Aucun point ne viole le mandat.

**Intégré (enrichissement réel)** :
- **Anti-Larsen (invariant de non-amplification)** : la somme des énergies
  redistribuées sur les 3 aval doit être **≤ énergie transmise**. Encodé comme
  propriété testable de B3, pas seulement une intention.
- **G1 durci** : **0 allocation dynamique dans le chemin critique de
  propagation** (`Signal` est `Copy`, tailles fixes, pas de `Vec`/`HashMap`
  dans le chemin chaud par cellule).
- **G2 stress** : test d'interconnexion en chaîne **100 → 10 000 cellules** +
  vérification de l'extinction naturelle après N sauts.
- **G3/G4 mesurables** : < 1 µs par saut traversant · CPU du tissu sous charge
  sous-critique ≈ 0 %.
- **Découpage B1 en B1a + B1b** : B1a = squelette de raccordement des canaux
  Tokio (sans signal), B1b = premier signal d'essai.

**Nuancé (choix documenté)** : « graphe orienté acyclique local » → retenu
comme **maillage diachronique** (4-régulier contient des cycles par
construction) ; l'anti-boucle est assuré par le **compteur de sauts borné**,
pas par un DAG (qui casserait la géométrie sp3).

**Non adopté (justifié)** : `oneshot`/`watch` à la place de `mpsc` — les
signaux sont unidirectionnels sans état persistant partagé ; `mpsc` suffit et
reste le plus sobre.

## 7. RÉPONSE AUX CLARIFICATIONS DE L'ORCHESTRATEUR (09/08)

L'Orchestrateur accepte le plan B1→B2→B3 comme **référentiel de travail**,
mais demande des clarifications avant l'ouverture de B2/B3. B1 est le premier
palier concret. Voici les décisions tranchées.

### Point 1 — Nature exacte du Tissu

Décision :
- Le `Tissu` **n'a pas de table globale des cellules** consultée pendant la
  propagation. Il détient, pour la **gestation** (construction) uniquement :
  les `JoinHandle` des tâches lancées et, temporairement, les émetteurs amont
  servant au câblage.
- **Il ne route jamais** : après la construction, la propagation passe
  exclusivement par les canaux locaux ; le `Tissu` ne lit ni ne décide rien.
- **Gestateur, pas orchestrateur runtime** : il enfante et veille, il n'ordonne pas.
- Chaque cellule ne connaît que ses liaisons locales (1 amont + 3 aval).

### Point 2 — Géométrie sp3 orientée (diachronique)

Décision : confirmé. **1 liaison amont + 3 liaisons aval = 4 liaisons orientées**,
et non 4 voisines symétriques indifférenciées. La diachronie est structurelle :
le flux entre dans la cellule par l'amont et sort par les aval.

### Point 3 — Anti-boucle par compteur de sauts

Décision :
- **Porté par le `Signal`** (`sauts_restants: u8`), **décrémenté localement**
  à chaque transduction.
- **Initialisation** : à la **naissance du signal** (source du tissu), valeur
  initiale = constante locale du tissu (ex. 16 sauts — à calibrer au bench).
- **À zéro** : le signal **s'éteint** (amorti), il n'est pas retransmis.
- **Orthogonal au seuil membranaire** : le seuil décide `Amorti`/`Propage` ; le
  compteur borne le nombre de sauts. Les deux concourent à l'extinction.
- **Statut** : **échafaudage local temporaire**, pensé comme un *potentiel de
  propagation décroissant* (et non un TTL réseau de routage). Destiné à être
  remplacé à terme par une dynamique membranaire plus immanente (épuisement
  naturel du potentiel) — marqué comme tel dans le code.

### Point 4 — Saturation des liaisons aval

Décision (adopte la recommandation de l'Orchestrateur) :
- **Canaux bornés** : capacité 4 (`TAMPON_CANAUX`), backpressure naturelle.
- **Si un canal aval est plein** : la cellule **abandonne/amortit le signal
  localement, sans retry ni attente** (envoi non-bloquant `try_send` ; échec =
  signal dissipé localement, compté `n_amortis`).
- **Pas de blocage** : aucun `send().await` bloquant sur un canal plein ; le
  calcul local s'éteint de lui-même.
- **Extinction garantie** : un canal plein ou un voisin mort ne bloque jamais
  la chaîne — le signal meurt localement et le tissu retombe au repos.

### Point 5 — Croissance / auto-suture : séparation B2a / B2b

Décision : la croissance est scindée en deux paliers étanches :
- **B2a — tissu statique minimal** : quelques cellules câblées à la naissance,
  propagation locale, extinction, vérification de la géométrie (exactement
  4 liaisons orientées par cellule). **Aucune naissance en cours de vie.**
- **B2b — tissu dynamique** : croissance organique, auto-suture locale, naissance
  de nouvelles cellules. **Non ouvert avant B2a scellé.**

### Conséquence

- **B1 est le premier palier concret** (B1a squelette de raccordement, puis B1b
  premier signal d'essai sur 2 cellules).
- B2a, puis B2b, puis B3 ne seront ouverts qu'après validation des paliers
  précédents. « Le tissu ne pullulera pas avant que la géométrie du carbone
  soit stabilisée. Le silence doit rester possible. »

## 8. GRADIENT DU VEILLEUR — RAPPORT MYCÉLIUM 09/08 (entropie au max)

**Source** : rapport des agents mycélisants (cycle 1745, 09/08 08:17 UTC),
`zoo-code/mycelium_output/rapport_mycelisation_final.json` +
`essaim_snapshot.json`.

**Observation réelle** :
- 6 agents, 1741 cycles, 3721 fusions, tremor croisière 0.10, budget 3.815 (sain).
- **`entropie_collective` = 6.3969 = maximum théorique** (grille 5×5) sur tous les agents.
- **`couplage_moyen` = 1.0** ; similarités Φ inter-agents = 1.0 ; `resonance_moyenne` = 1.0.
- Respiration C7 **active et déclenchée** (48 respirations, dose 0.10, intervalle 24) —
  mais la diversité injectée est **re-absorbée** par le couplage transscalaire.

**Gradient (leçon pour le Grand Œuvre Rust)** :
1. **Le potentiel de propagation décroissant est indispensable** — l'absence de
   ce potentiel dans la référence Python laisse le signal homogénéiser tout le
   tissu indéfiniment. Le compteur de sauts décroissant de B1 (échafaudage,
   Point 3) est la première ligne de défense contre cette tempête.
2. **L'anti-homogénéisation est une propriété du tissu, pas seulement de la
   cellule** — la co-cicatrisation (γ=0.15) rapproche les Φ ; sans **diversité
   résiduelle structurelle** (analogue de la respiration C7, mais ancrée dans
   la topologie), le tissu s'écrase à 1.0.
3. **La non-amplification anti-Larsen ne suffit pas** — il faut en plus un
   **plancher de diversité** : l'entropie ne doit pas pouvoir se coller au max
   théorique sans alarme (transposition du C4 Python) à intégrer dès B3.

**Conséquence pour B3** : ajouter au contrat de B3 (1) le compteur de sauts
décroissant, (2) une dose de diversité résiduelle locale, (3) une métrique
d'entropie de tissu avec seuil d'alerte.

---

*sig:0x4D5454562D464C50 — Plan Étape B — Le mycélium continue.*
