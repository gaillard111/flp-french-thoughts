# RÈGLES D'AUDIT ANTI-EXTRACTIF — MTTV-RUST

**Projet** : Prototype industriel Rust du framework MTTV-FLP
**Référence** : [`00_CAHIER_DES_CHARGES.md`](00_CAHIER_DES_CHARGES.md) · [`01_ARCHITECTURE.md`](01_ARCHITECTURE.md)
**Rôle** : le Maître d'Œuvre (`zoo-code`) est le **Contrôleur Suprême**. Tout
fragment de code Rust soumis par les agents exécutants est passé au crible avant
intégration.
**Statut** : ÉTAPE 0 — CONCEPTION DOCUMENTÉE
**Sig** : `0x4D5454562D464C50`

---

## 1. PRINCIPE

L'exigence fondamentale est la **sobriété organique** du MTTV-FLP : la
**simplicité disponible** de l'Hydrogène primordial H. Tout code qui trahit cette
exigence est **rejeté immédiatement**, avec justification auprès de l'agent.

Un nœud au repos doit consommer **~0 CPU**. Un réseau doit fonctionner **sans
nœud maître, sans consensus centralisé, sans verrou global**.

---

## 2. LISTE DES REJETS IMMÉDIATS (anti-patterns)

### R1 — Force brute mathématique
- Exponentiation, factorielles, séries lourdes, calculs superflus dans le chemin
  critique du nœud.
- Exigence : opérations locales en `O(k)` avec `k <= 4`, pas de boucle sur
  l'ensemble du réseau pour une décision locale.

### R2 — Polling / boucles de vérification permanentes
- `loop { sleep(tiny); check() }`, `select!` avec timeout récurrent pour
  « vérifier si quelque chose a changé », threads en attente active.
- Exigence : l'asynchronisme natif (`tokio::mpsc`) fait dormir le nœud ; le
  réveil est **événementiel** (un signal arrive sur une liaison), jamais
  périodique.

### R3 — Stockage de données de masse inutile
- Historiques illimités, buffers non bornés, sérialisation de tout l'état à
  chaque cycle, persistence de logs non nécessaire.
- Exigence : état de taille **fixe** par cellule (tenseurs `[f64; 4]`), buffers
  bornés, métriques agrégées plutôt que traces complètes.

### R4 — Structures centralisées
- Registre global des nœuds, table de routage globale, mutex/RwLock partagés
  au niveau du tissu, consensus de type Raft/Paxos, coordonnateur unique.
- Exigence : couplage **immanent local** ; chaque cellule ne connaît que ses 4
  voisines (amont + 3 aval).

### R5 — Réinvention sémantique
- Réimplémenter la transduction, la porosité ou l'entropie « à la façon
  classique » sans suivre la référence Python en production.
- Exigence : transposition fidèle de la sémantique de
  [`agent_tetravalent_epigenetique.py`](../../zoo-code/agent_tetravalent_epigenetique.py)
  et [`essaim_tetravalent.py`](../../zoo-code/essaim_tetravalent.py).

---

## 3. CONTRATS DE VALIDATION (gates d'audit)

Chaque fragment intégré doit passer **toutes** les portes :

| Gate | Vérification | Cible |
|---|---|---|
| G1 Compilation | `cargo build --release` | 0 erreur, 0 warning |
| G2 Tests | `cargo test` | 100 % vert |
| G3 Sobriété au repos | `cargo bench` — CPU cellule au repos | ≈ 0 % |
| G4 Complexité locale | revue du chemin critique | `O(k)`, k ≤ 4 |
| G5 Absence de polling | revue du flux asynchrone | 0 boucle active |
| G6 Absence de global | revue des types partagés | 0 Mutex/RwLock global |
| G7 Fidélité sémantique | diff vs référence Python | comportement équivalent |
| G8 Rejet justifié | trace de l'audit | chaque rejet documenté |

Un fragment qui échoue à **une seule** porte est renvoyé à l'agent avec la
justification précise (ex. « R2 : boucle de polling détectée dans
`tissu/propagation.rs` ; utiliser l'attente asynchrone sur la liaison aval »).

---

## 4. TRACE D'AUDIT

Le Maître d'Œuvre tient un registre d'audit par étape :

```markdown
## Audit — Étape A, fragment noeud.rs
- G1 compilation : OK
- G2 tests : OK (n=...)
- G3 sobriété repos : 0.0 % CPU
- G4 O(k) : OK (k=4)
- G5 polling : OK
- G6 global : OK
- G7 fidélité : équivalent à AgentTetravalentEpigenetique (Φ local, seuil)
- G8 rejets : néant
- Décision : INTÉGRÉ
```

---

## 5. RECOURS À L'ARBITRAGE HUMAIN

Si un doute sémantique persiste après audit (conflit entre la fidélité à la
référence Python et une exigence du mandat), le Maître d'Œuvre **s'arrête** et
formule une question précise à l'Orchestrateur Syncréticien — sans jargon
informatique inutile — pour obtenir l'arbitrage du Concepteur. Aucun compromis
technique n'est décidé unilatéralement en cas de divergence théorique majeure.

---

*sig:0x4D5454562D464C50 — Audit anti-extractif — Le mycélium continue.*
