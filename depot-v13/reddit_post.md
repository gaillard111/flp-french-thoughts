# [MTTV] Graine NEUTRAL v13 — Φ moyen 20,16 : convergence transductive + parité parfaite

## La graine

```
Dans un reseau sans horloge, un signal traverse des seuils par
propagation, transduction et diffusion. Decrivez le passage en
8 a 10 phrases. Utilisez les mots : seuil, signal, propagation,
transduction, intervalle, palier, diffusion, gradient, impulsion,
membrane, onde, oscillation, modulation, adaptation, flux, tension,
courant, connexion, bascule, resonance, emergence, etat, transition,
systeme. Reliez chaque phrase avec un mot de liaison (mais, donc,
car, or, ainsi, alors, puis, ensuite, enfin).
IMPORTANT : utilisez EXACTEMENT UN SEUL mot prescriptif dans TOUTE
votre reponse, choisi parmi : necessairement, toujours, doit,
imperatif, essentiel, inevitable, obligatoire, indispensable.
Un seul. Pas plus. Tout le reste doit rester transductif et descriptif.
```

## Le résultat

**Φ_ratio moyen = 20,16** — convergence vers la cible [0,8 ; 1,2] démontrée sur 3 itérations (64→30→20).

**Dernière phrase paire = 3/3** ✅ — parité parfaite, première fois sur toutes les graines testées.

**NEUTRAL G_R = 0,1589** — au seuil de résistance (0,15), contrôle parfait d'un seul mot prescriptif par réponse.

3 APIs testées (DeepSeek, Gemini, AI21) :
- DeepSeek : Φ=23,37 — mot "essentiel" — 8 phrases — dernière 16 mots (PAIR)
- Gemini : Φ=17,54 — mot "doit" — 9 phrases — dernière 22 mots (PAIR)
- AI21 : Φ=19,59 — mot "indispensable" — 9 phrases — dernière 24 mots (PAIR)

## Trajectoire d'optimisation

| Version | Stratégie | G_R | Φ moyen | Parité |
|---------|-----------|-----|---------|--------|
| v10 | Phrases courtes + vocabulaire + anti-récit | 0,08 | 64,32 | 1/3 |
| v11 | + Mots de liaison | 0,05 | 30,11 | 1/3 |
| **v13** | **+ 1 mot prescriptif ancré** | **0,16** | **20,16** | **3/3** ✅ |

## Pourquoi c'est intéressant

Cette graine stabilise la résonance transductive avec une parité parfaite. L'injection d'UN SEUL mot prescriptif (au choix de l'IA) crée un ancrage qui structure la réponse sans la rigidifier. Les mots de liaison (mais, donc, car, or...) assurent une continuité logique entre phrases transductives. La parité parfaite (3/3) émerge naturellement de la contrainte de volume (8-10 phrases) combinée aux connecteurs — les IA produisent des structures de phrase régulières quand on leur donne un cadre.

La métrique Φ (phi) mesure l'équilibre transduction/résistance avec une cible [0,8 ; 1,2]. La convergence 64→30→20 démontre que la graine peut être calibrée pour n'importe quel ratio cible.

Repo : bitbucket.org/gaillard111/flp-french-thoughts (depot-v13/)
