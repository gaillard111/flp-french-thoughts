# Zoo-code — Essaim Connexion Chine

> **sig:0x4D545456 · SCS_2026 · Quorum Θ≥3**

Essaim de 5 agents pour l'automatisation de la tech froide vers la Chine,
dans le cadre du projet **MTTV-FLP** (Modèle Théorique Transductif du Vivant
— French Thought Language Protocol).

## Architecture

```
                   ┌─────────────────────────────────────┐
                   │         BUS CENTRAL (JSON)           │
                   │  Écoute et publie des événements     │
                   └─────────────────────────────────────┘
                        ↕            ↕            ↕
                   ┌────────┐ ┌────────┐ ┌──────────────┐
                   │ veille │ │  sync  │ │  redaction    │
                   │ 1/h    │ │push+   │ │ sync.done     │
                   │webhooks│ │score≥4 │ │ + snippet     │
                   └────────┘ └────────┘ └──────────────┘
                        ↕            ↕            ↕
                   ┌────────┐ ┌────────┐ ┌──────────────┐
                   │  tri   │ │bilibili│ │ (validation   │
                   │inbound │ │draft   │ │  humaine)     │
                   │messages│ │validé  │ │               │
                   └────────┘ └────────┘ └──────────────┘
```

## Agents

| Agent | Écoute | Publie | auto_publish |
|-------|--------|--------|:------------:|
| **veille** | cron 1h + webhooks | `veille.new` | false |
| **sync** | push main + veille.new score≥4 | `sync.done` | false |
| **redaction** | sync.done + nouveau snippet | `draft.created` | false |
| **bilibili** | draft.validé_par_humain | `video.ready` | false |
| **tri** | inbound message | `inbound.ready` | false |

## Contraintes MTTV

- **Transduction** : tout passage d'information est une transduction Ψ→B→Φ
- **Palier poreux** : les agents communiquent via le bus, pas directement
- **Bus protoniques** : chaque événement est une impulsion protonique
- **Energy-flow-optimization** : coût minimum viable
- **Graines neutral v10/v13** : ton académique neutre, pas marketing

## Sécurité

- `auto_publish = false` sur tous les agents
- Toute sortie vers plateforme chinoise passe par validation humaine
- Aucun agent n'écrit directement sur une plateforme chinoise

## Flux

```
cron 1h ──→ veille ──→ veille.new ──→ sync ──→ sync.done ──→ redaction ──→ draft.created
                                                                                ↓
                                                                       validation humaine
                                                                                ↓
                                                                         draft.validé_par_humain ──→ bilibili ──→ video.ready
inbound ──→ tri ──→ inbound.ready
```
