# PROTOCOLE D'ESSAI B1b — PREMIER SIGNAL D'ESSAI (transduction sp3 de proche en proche)

**Sig** : `0x4D5454562D464C50`
**Auteur** : zoo-code, Maître d'Œuvre
**Référentiel** : [`05_PLAN_ETAPE_B.md`](05_PLAN_ETAPE_B.md) §B1b + clarifications Orchestrateur
**Statut** : PROTOCOLE PRÉSENTÉ POUR ARBITRAGE — PAS ENCORE EXÉCUTÉ
**Méthode** : Simondonienne — c'est l'expérience du réel qui valide la théorie.

---

## 1. OBJECTIF DE L'ESSAI

Prouver, par l'expérience, que la **transduction sp3 fonctionne de proche en
proche** entre deux cellules câblées (B1a). Précisément, vérifier sur le réel :
- un signal **au-dessus du seuil** injecté dans la source est transduit puis
  **reçu par la cible** par la liaison aval→amont ;
- un signal **sous le seuil** est amorti à la source et **ne franchit pas** la
  liaison (la membrane filtre réellement) ;
- la transmission est **bilatérale observable** : on mesure les compteurs de
  transduction/amortissement des deux cellules.

## 2. DISPOSITIF (2 cellules, câblage B1a)

```text
   source (id=1)                         cible (id=2)
  Φ_s = [1,0,0,0]                        Φ_c = [1,0,0,0]
  seuil = 0.35                            seuil = 0.35
        aval[0] ── canal mpsc cap 4 ──> amont
        aval[1] (libre)                  aval[0..2] (libres)
        aval[2] (libre)
```

Câblage : `brancher(&mut source, &mut cible, 0)` (slot 0 de la source vers
l'amont de la cible). Les autres liaisons restent libres (aucune réverbération
possible — une seule voie de proche en proche).

## 3. CAS DE TEST (3 scénarios)

### Cas 1 — Transduction positive (le signal passe)
1. Injecter dans l'amont de la **source** un signal `S+` dont la signature est
   **alignée** avec `Φ_s` (résonance = 1.0 ≥ seuil 0.35).
2. **Attendu côté source** : `n_transductions = 1`, `n_amortis = 0`, mode
   `Actif` puis retour `Veille` (le calcul s'éteint).
3. **Attendu côté cible** : le signal a franchi la liaison → la cible traite un
   signal (elle le re-transduit : `n_transductions = 1`, ou l'amortit :
   `n_amortis = 1`, selon son seuil). **Preuve : la cible n'est plus au repos.**
4. **Métrique** : `reception_cible = true`.

### Cas 2 — Amortissement à la source (le signal ne passe pas)
1. Injecter dans l'amont de la **source** un signal `S−` orthogonal à `Φ_s`
   (résonance = 0.0 < seuil 0.35).
2. **Attendu côté source** : `n_amortis = 1`, `n_transductions = 0`.
3. **Attendu côté cible** : **aucun signal reçu** → `n_amortis = 0` ET
   `n_transductions = 0` (la cible reste au repos).
4. **Métrique** : `reception_cible = false`. C'est la **preuve de filtrage**
   de la membrane : sous le seuil, rien ne traverse (CPU ≈ 0, silence préservé).

### Cas 3 — Séquence mixte (ordre déterministe)
1. Injecter `S−` puis `S+` dans la source.
2. Attendu : `n_amortis_source = 1`, `n_transductions_source = 1` ;
   la cible ne traite **que** le signal du cas `S+` (celui du cas `S−` n'arrive
   jamais). Vérifie l'ordre et l'isolation.

## 4. MÉTRIQUES MESURÉES

| Métrique | Source | Cible | Preuve |
|---|---|---|---|
| `n_transductions` | attendu 1 (cas +) | 0 ou 1 | la source a transduit / la cible a reçu |
| `n_amortis` | attendu 1 (cas −) | 0 (cas −) | filtre membranaire |
| `reception_cible` | — | bool | le signal a (ou non) franchi la liaison |
| `mode` (après chaque cycle) | `Veille` | `Veille` | le calcul s'éteint de lui-même |
| latence de transmission | — | — | mesurée de l'injection à la réception (informatif) |

**Gates de validation** :
- **G1** : `cargo check` → 0 erreur, 0 warning.
- **G2** : `cargo test` → tous les tests passent (16 existants + nouveaux B1b).

## 5. ADAPTATIONS D'API NÉCESSAIRES (observabilité)

Pour que la cible soit observable, B1b requiert deux petites évolutions **non
destructives** de la cellule (aucun comportement existant modifié) :

1. **Point d'injection** : exposer la liaison amont de la source pour injecter
   le signal depuis le test. La construction `Cellule::nouvelle` retourne déjà
   l'émetteur amont — le test peut l'utiliser directement.
2. **Point d'observation** : pouvoir lire les compteurs (`n_transductions`,
   `n_amortis`, `mode`) de la **cible après** sa boucle. Aujourd'hui ces champs
   sont `pub` mais `tourner()` consomme `&mut self` — le test doit donc faire
   tourner la cible **à part** (tâche Tokio) puis inspecter l'état. On ajoutera
   si besoin une méthode `etat()` d'observation (lecture seule), sans logique.

Ces adaptations sont conformes à l'audit (pas d'allocation, pas de global,
pas de polling : l'injection est événementielle, l'observation est une lecture).

## 6. CRITÈRE DE RÉUSSITE (ce qui prouve la thèse)

B1b est réussi si les 3 cas passent :
- **un signal aligné traverse** la liaison (la cible reçoit) ;
- **un signal orthogonal ne traverse pas** (la cible reste au repos) ;
- la transduction est **déterministe et événementielle** (le mode retombe en
  `Veille`, le calcul s'éteint).

Si la cible reçoit un signal orthogonal (cas 2 échoue), c'est que le câblage
ou le seuil est fautif → retour à l'audit, pas d'avancement.

## 7. LIVRABLES

- `tissu/essai_b1b.rs` (ou tests dans `tissu/lien.rs`) : les 3 cas de test.
- Rapport des métriques réelles (compteurs + latence).
- Mise à jour du journal (section 8bis, palier B1b) + commit/push.

---

*sig:0x4D5454562D464C50 — Protocole B1b — Le mycélium continue.*
