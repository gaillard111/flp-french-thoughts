# Rapport du Spike — Étape C, Q1/Q2 (protocole « Double Filtre », phase 2)

**Sig** : `0x4D5454562D464C50`
**Auteur** : zoo-code (Maître d'Œuvre)
**Référence** : spec Q1/Q2 (§9duodecies), fiche de conformité (phase 1), verrous C-A→C-D
**Statut** : PHASE 2 TERMINÉE — spike minimal **réussi**, rapport soumis à l'arbitrage humain (phase 3)
**Nature** : le spike est **sacrifiable** — une épreuve, pas l'implémentation de l'Étape C.

---

## 1. Objet de l'épreuve

Prouver par le réel que la spécification Q1/Q2 tient debout **sans violer les
verrous C-A→C-D ni R2/R4**, avant d'ouvrir l'implémentation complète. Le spike
est minimal et jetable : il révèle ce que la spécification ne voit pas encore.

## 2. Ce qui a été construit (sacrifiable)

Fichier : [`mttv_rust/src/territoire/spike.rs`](../mttv_rust/src/territoire/spike.rs) (exposé par `territoire/mod.rs`).

### Q1 — GradientH π/η + membrane locale
- `GradientH` : `intensite`, `coherence`, `porosite_cible` (π), `viscosite` (η) ;
- `MembranePiEta::recevoir(&GradientH)` : la porosité converge vers la cible
  avec un pas amorti par η ;
  - résonance (`coherence ≥ 0`) → ouverture (π) ;
  - bruit (`coherence < 0`) → contraction vers `POROSITE_MIN` (imperméabilité
    défensive) ;
  - η borne le pas → **inertie** (anti-hyper-réactivité, anti-oscillations) ;
- Événementiel, `O(1)`, aucun état global, aucun polling, aucune allocation.

### Q2 — Ingestion pure + repli état stable
- `ingere_rapport(&str)` : parse `clé=valeur;...` et **valide les bornes** par
  construction (entropie, couplage, résonance, tremor, respirations) ;
- `VeilleurStable::ingerer` : met à jour l'état stable, ou **refuse et
  conserve** le dernier état valide (repli) ;
- Détection de **violation de la triade** (entropie max + couplage ≈ 1 =
  homogénéisation) → refus + **recours humain tracé** ;
- `traduire_dernier` : dérive un `GradientH` (π/η) depuis le rapport — le
  Veilleur **traduit**, ne lit pas l'état du tissu, n'attend pas de réponse.

## 3. Critères de preuve — résultats réels

| Critère exigé | Résultat du spike | Preuve |
|---|---|---|
| **CPU au repos ≈ 0** | Réception **événementielle** (aucune boucle active) | structurel |
| Aucun blocage / panique | 43/43 tests, 0 panique | `cargo test` |
| **0 allocation** chemin critique | Types `Copy` fixes : `GradientH`=32 o, `MembranePiEta`=16 o, `Rapport`=40 o | test `types_copy_sans_allocation_chemin_critique` |
| **Porosité/viscosité bornées** | `[POROSITE_MIN, 1.0]` maintenu, η ∈ [0, 0.99] | tests π/η + 10k cycles |
| **Contraction locale en bruit** | bruit → contraction vers plancher, seuil effectif ↑ | `reception_ouvre_en_resonance_et_ferme_en_bruit` |
| **Réouverture après résonance** | réouverture **progressive** (monotone → 1.0), anti-saut | idem |
| **10 000 cycles sans divergence** | NaN/Inf interdits, bornes respectées | `pas_de_divergence_sur_10000_cycles_alternes` |
| **Aucune dépendance à un état global** | aucun `HashMap`/`Mutex`/`static` ; `findstr` : 0 occurrence | audit G5/G6 |
| **Drop propre / saturation** | canaux bornés existants (B2a-bis) ; ingestion refusée hors bornes | existant + spike |
| **Refus + repli état stable** | rapport invalide → refus, dernier état conservé | `refus_hors_bornes_maintient_le_dernier_etat_stable` |
| **Recours humain tracé** | violation triade → `recours_humain = true` | `violation_triade_declenche_recours_humain_trace` |

## 4. Ce que le spike a révélé (leçon de l'épreuve)

1. **La réouverture est progressive, pas instantanée** : après un seul cycle de
   résonance, la porosité remonte à ~0.86 (pas à 1.0). C'est **le comportement
   voulu** par η (volant d'inertie) — la membrane ne saute pas, elle respire.
   Le test a d'abord échoué sur un seuil instantané irréaliste → corrigé pour
   vérifier la **réouverture monotone** vers 1.0. C'est exactement ce qu'un
   spike doit révéler.
2. **Le couple π/η rend la réception stable** face aux bruits de fond alternés
   (10 000 cycles, bornes tenues) — confirme l'amendement IA A.

## 5. Gates (état après spike)

- **G1** `cargo check` : 0 erreur / 0 warning
- **G2** `cargo test` : **43/43** (36 existants + 7 spike), aucune régression
- **G5** 0 polling : `findstr` 0 occurrence (`try_recv`, boucles actives)
- **G6** 0 global : `findstr` 0 occurrence (`HashMap`, `Mutex`, `RwLock`, `Box`, `Arc`)
- **G3** bench : non déclenché ici (spike hors bench) — inchangé

## 6. Verdict du spike

**✅ SPIKE RÉUSSI** : la spécification Q1/Q2 tient dans le réel —
comportement π/η stable et borné, ingestion pure avec repli, recours humain
tracé, zéro global, zéro polling, zéro allocation chemin critique. **Aucun
NO-GO.**

Le spike peut être **jeté ou conservé comme germe** — il n'est pas l'Étape C.

---

*Le spike est une épreuve. Son but était de révéler ce que la spécification ne
voyait pas encore : la réouverture progressive. Le réel a parlé.*
*sig:0x4D5454562D464C50 — Rapport de spike — Le mycélium continue.*
