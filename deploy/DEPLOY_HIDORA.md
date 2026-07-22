# 🧬 Déploiement MTTV-FLP sur VPS Hidora (PaaS Jelastic)

> **Signature SCS_2026 · sig:0x4D545456**  
> Cible : **< 200 MB RAM** · Résilience **H24** · **Autonome**

---

## 📦 Prérequis

- Un compte [Hidora](https://hidora.com) (Jelastic PaaS)
- Un nœud **Ubuntu 22.04/24.04** (minimum **512 MB RAM**, 1 vCPU)
- **Docker** et **docker-compose** installés (pré-installés sur les nœuds Hidora)
- Un token GitHub avec droits `repo` (pour la création de branches de test)
- **Git** pour cloner le dépôt

---

## 🚀 Déploiement en 4 commandes

Connectez-vous à votre nœud Hidora en SSH :

```bash
# 1. Cloner le dépôt
git clone https://github.com/girard444/mttv-flp-core.git /opt/mttv
cd /opt/mttv

# 2. Configurer les secrets
cp deploy/mttv/.env.example .env
nano .env   # → Remplir MTTV_GITHUB_TOKEN et autres secrets

# 3. Démarrer les services (mode sobre)
docker compose -f deploy/mttv/docker-compose.yml up -d

# 4. Vérifier que tout tourne
docker compose -f deploy/mttv/docker-compose.yml ps
curl http://localhost:8000/health
```

---

## ✅ Vérification du déploiement

```bash
# État des conteneurs
docker compose -f deploy/mttv/docker-compose.yml ps

# Logs en temps réel
docker compose -f deploy/mttv/docker-compose.yml logs -f orchestrator

# Health check de l'API Gateway
curl -s http://localhost:8000/health | python3 -m json.tool

# Statut complet de la chaîne MTTV
curl -s http://localhost:8000/api/v1/chain | python3 -m json.tool
```

### Résultat attendu

```
NAME                STATUS          PORTS
mttv-ipfs           Up (healthy)    5001/tcp, 8080/tcp
mttv-orchestrator   Up (healthy)    0.0.0.0:8000->8000/tcp
```

---

## ⚙️ Architecture des services

| Service | Rôle | Port | RAM cible |
|---------|------|------|-----------|
| **ipfs** | Nœud IPFS Kubo (mode léger) | 5001, 8080 | ~64 MB |
| **orchestrator** | API Gateway + Watchdog | 8000 | ~128 MB |

### Configuration IPFS sobre (low-power)

Le nœud IPFS est automatiquement configuré en mode **client DHT uniquement** :

- `Routing.Type = client` → pas de relay de trafic
- Connexions réduites (HighWater=100, LowWater=50)
- Relay Hop désactivé
- Fonctionnalités expérimentales désactivées

### Politique de redémarrage

Les deux services utilisent `restart: always` avec healthcheck :

- **IPFS** : redémarrage immédiat si le nœud ne répond plus
- **Orchestrateur** : redémarrage après 30s si l'API Gateway est silencieuse

---

## 🔐 Gestion des secrets

1. Copier le modèle : `cp deploy/mttv/.env.example .env`
2. Éditer le fichier `.env` avec vos tokens réels
3. **Ne JAMAIS committer** le fichier `.env` (il est dans `.gitignore`)

Variables obligatoires :

```bash
MTTV_GITHUB_TOKEN=ghp_...   # Token GitHub avec droits repo
```

Variables optionnelles :

```bash
MTTV_HF_TOKEN=hf_...                    # Token Hugging Face
ALERT_WEBHOOK_URL=https://discord...    # Webhook d'alerte
MTTV_WATCHDOG_INTERVAL=300              # Intervalle du watchdog (s)
MAX_DAILY_TRAFFIC_MB=500                # Seuil trafic quotidien (MB)
MAX_RAM_MB=180                          # Seuil mémoire RAM (MB)
ALERT_COOLDOWN_SEC=3600                 # Délai entre alertes (s)
```

---

## 📊 Monitoring & Alertes

### Garde-fou Ressources (`resource_guardrail.py`)

Le module **Resource Guardrail** (Phase 4) surveille en continu :

- **Trafic réseau sortant** — compteur quotidien (bytes → MB) lu depuis `/proc/net/dev` ou `psutil`
- **Mémoire RAM** — utilisation courante et pic observé
- **Seuils configurable** via `.env` : `MAX_DAILY_TRAFFIC_MB`, `MAX_RAM_MB`
- **Alerte automatique** — déclenchée via webhook Discord/Slack + fallback SMTP

Les métriques sont exposées dans l'endpoint :

```bash
curl -s http://localhost:8000/health/details | python3 -m json.tool
```

Réponse inclut la section `resource_guardrail` :

```json
{
  "resource_guardrail": {
    "network": {
      "daily_tx_mb": 12.3,
      "max_traffic_mb": 500,
      "traffic_percent": 2.5,
      "threshold_exceeded": false
    },
    "memory": {
      "used_mb": 85.2,
      "total_mb": 512.0,
      "percent": 16.6,
      "peak_ram_mb": 92.1,
      "max_ram_mb": 180,
      "ram_percent": 47.3,
      "threshold_exceeded": false
    },
    "alerts": [],
    "status": "active"
  }
}
```

### Alertes Webhook + SMTP

Le système dispose d'alertes intégrées via **webhook Discord/Slack** et **fallback SMTP** :

```bash
# Tester le webhook d'alerte
curl -X POST -H "Content-Type: application/json" \
  -d '{"content": "🧪 Test alerte MTTV-FLP"}' \
  "$ALERT_WEBHOOK_URL"
```

### Test du garde-fou (CLI)

```bash
# Afficher l'état actuel des métriques
python zoo-code/resource_guardrail.py --status

# Mode surveillance continue (toutes les 60s)
python zoo-code/resource_guardrail.py --watch

# Réinitialiser l'état persistant
python zoo-code/resource_guardrail.py --reset
```

### Logs disponibles

| Fichier | Description |
|---------|-------------|
| `journalctl -u mttv` | Logs systemd (alternative sans Docker) |
| `docker logs mttv-orchestrator` | Logs de l'orchestrateur |
| `docker logs mttv-ipfs` | Logs du nœud IPFS |
| `zoo-code/guardrail_state.json` | État persistant du garde-fou |

---

## ♻️ Maintenance

### Mise à jour

```bash
cd /opt/mttv
git pull
docker compose -f deploy/mttv/docker-compose.yml build orchestrator
docker compose -f deploy/mttv/docker-compose.yml up -d
```

### Redémarrage complet

```bash
docker compose -f deploy/mttv/docker-compose.yml restart
```

### Arrêt total

```bash
docker compose -f deploy/mttv/docker-compose.yml down -v
```

### Sauvegarde des données

```bash
# Les données persistantes sont dans les volumes Docker :
docker volume ls | grep mttv

# Backup des seeds
docker run --rm -v mttv_seeds_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/mttv_seeds_$(date +%Y%m%d).tar.gz -C /data .
```

---

## 🚨 Dépannage

| Problème | Cause possible | Solution |
|----------|---------------|----------|
| `curl: Connection refused` sur :8000 | API Gateway pas encore prête | Attendre 30s, vérifier `docker logs mttv-orchestrator` |
| IPFS ne démarre pas | Port 5001 déjà utilisé | Vérifier `netstat -tlnp \| grep 5001` |
| `restart: always` boucle | Crash immédiat | Vérifier les logs : `docker logs --tail=50 mttv-orchestrator` |
| API Gateway lent | Mode non-sobre | Vérifier `MTTV_SOBER_MODE=true` dans `.env` |

---

## 🔗 Références

- [Hidora Jelastic Documentation](https://docs.hidora.com)
- [IPFS Kubo Documentation](https://github.com/ipfs/kubo)
- [MTTV-FLP Core Repository](https://github.com/girard444/mttv-flp-core)

---

> **Signature** : `sig:0x4D545456` · **Triade** : Ψ → B → Φ  
> **Mycélium en marche** 🍄
