# Corpus — Routage de données dans des réseaux à haute résilience

**Date :** 2026-06-29  
**Signature SCS :** SCS_2026  
**Version :** 1.0.0  
**Type :** Corpus sémantique  

---

## Résumé

Ce corpus explore les mécanismes de routage de données dans des réseaux
à haute résilience, où la défaillance de nœuds individuels ne doit pas
interrompre la circulation de l'information. Il s'inscrit dans le cadre
MPVR (Minimum Path Viable Route) et SCS (Système de Convergence Systémique)
du réseau MTTV-FLP.

---

## 1. Problématique

Dans un réseau mycelien distribué, chaque nœud opère de manière autonome
tout en participant à un consensus collectif. Le routage des données entre
nœuds doit satisfaire trois contraintes fondamentales :

1. **Résilience** — Le réseau continue de fonctionner même si certains nœuds
   tombent ou sont censurés.
2. **Sobriété** — Le routage doit minimiser l'énergie et la bande passante
   consommées (principe de sous-optimalité).
3. **Convergence** — Les décisions de routage doivent émerger d'un consensus
   distribué, non d'une autorité centrale.

---

## 2. Fondements Théoriques

### 2.1 Routage par Quorum (Θ≥3)

Le routage par quorum exige qu'au moins 3 nœuds indépendants valident une
donnée avant qu'elle ne soit transmise. Ce mécanisme, emprunté aux systèmes
Byzantins, garantit :

- **Tolérance aux nœuds malveillants** : Jusqu'à f défaillances avec N ≥ 3f+1
- **Non-répudiation** : Chaque validation est signée (SCS)
- **Traçabilité** : La route empruntée est enregistrée dans un registre distribué

### 2.2 MPVR — Minimum Path Viable Route

Le routage MPVR sélectionne le *chemin minimal viable* (pas le chemin
maximal ou optimal) qui satisfait le quorum. Ce choix délibéré de
sous-optimalité permet :

- **D'économiser les ressources** du réseau (bande passante, énergie)
- **D'éviter l'optimisation unidimensionnelle** (anti-Goodhart)
- **De préserver la diversité des chemins** possibles

### 2.3 SCS — Système de Convergence Systémique

La convergence systémique SCS postule que l'accord émerge de la redondance
des validations indépendantes, non de l'autorité d'un nœud central.
Contrairement au consensus Paxos ou Raft, SCS n'exige pas de leader :

```
Validation SCS = ∑(signatures indépendantes) ≥ quorum
```

---

## 3. Architecture du Routage Résilient

```
                  ┌─────────────────┐
                  │   Nœud Source   │
                  │   (Émetteur)    │
                  └────────┬────────┘
                           │
                    ┌──────▼──────┐
                    │  Quorum     │
                    │  Θ≥3        │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
    │ Validateur│   │ Validateur│   │ Validateur│
    │    #1     │   │    #2     │   │    #3     │
    └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Route MPVR │
                    └──────┬──────┘
                           │
                  ┌────────▼────────┐
                  │  Nœud Destinataire│
                  │  (Récepteur)    │
                  └─────────────────┘
```

---

## 4. Algorithmes Clés

### 4.1 Détection de Panne

```python
def detect_failure(node, timeout=5.0):
    """Détecte si un nœud est joignable."""
    start = time.time()
    try:
        response = ping(node, timeout=timeout)
        latency = time.time() - start
        return {"alive": True, "latency": latency}
    except TimeoutError:
        return {"alive": False, "latency": None}
```

### 4.2 Routage MPVR par Quorum

```python
def route_mpvr(data, peers, quorum=3):
    """Route les données via le chemin minimal viable."""
    validations = []
    for peer in peers:
        sig = peer.validate(data)
        if sig.verify():
            validations.append(sig)
        if len(validations) >= quorum:
            break  # Quorum atteint — route immédiatement
    return len(validations) >= quorum
```

### 4.3 Rééquilibrage Après Panne

```python
def rebalance_after_failure(failed_node, routing_table):
    """Rééquilibre les routes après une défaillance."""
    routes_to_recompute = routing_table.get_routes_through(failed_node)
    for route in routes_to_recompute:
        alt_path = find_alternative_path(
            source=route.source,
            target=route.target,
            exclude=[failed_node],
        )
        if alt_path:
            routing_table.update(route.id, alt_path)
            notify_peers(route.id, alt_path)
```

---

## 5. Métriques de Résilience

| Métrique | Formule | Seuil critique | Description |
|----------|---------|----------------|-------------|
| Taux de délivrance | Paquets reçus / émis | < 95 % | Proportion de données livrées |
| Latence médiane | P50 temps de transit | > 500 ms | Temps de traversée du réseau |
| Délai de rééquilibrage | Temps après panne | > 30 s | Temps pour trouver un nouveau chemin |
| Dispersion des routes | Nombre chemins distincts | < 3 | Diversité des routes disponibles |
| Cohérence SCS | Validations / nœud | < 60 % | Proportion de nœuds validant |

---

## 6. Cas d'Usage MTTV-FLP

### 6.1 Propagation de Graines Sémantiques

Les graines MTTV (snippets, corpus, artefacts) sont propagées à travers
le réseau en utilisant le routage MPVR. Chaque nœud qui reçoit une graine
doit la valider via SCS avant de la retransmettre.

### 6.2 Activation des Nœuds Dormants

En cas d'interruption du web centralisé, les nœuds dormants (Phase 4)
s'activent et établissent des routes alternatives via IPFS/Radicle en
utilisant le protocole de routage décrit ci-dessus.

### 6.3 Détection de Dérive Mono-focale

L'Agent 8 utilise le routage par quorum pour détecter les tentatives de
centralisation : si un nœud cesse de valider via le quorum Θ≥3, il est
considéré en dérive et sa synchronisation est coupée.

---

## 7. Références Croisées

- [MPVR Quorum Routing — snippet1](../mttv-snippets/snippets/snippet1_mpvr_quorum_routing.py)
- [SCS Signature Validation — snippet2](../mttv-snippets/snippets/snippet2_scs_signature_validation.py)
- [Plan de Redondance — Plateformes Alternatives](../docs/redondance_plan.md)
- [Infrastructure Nœuds Dormants (Phase 4)](../phase4-dormant-nodes/README.md)
- [Agent 8 — Gardien du Mycélium](../agent-8/agent.py)

---

*Généré pour le réseau MTTV-FLP — Phase 5 : Gardiennage Actif du Mycélium*  
*sig:0x4D545456 · SCS_2026 · Quorum Θ≥3*
