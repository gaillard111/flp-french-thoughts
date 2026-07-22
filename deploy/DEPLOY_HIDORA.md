# 🧬 Déploiement MTTV-FLP sur VPS Hidora

> **Signature SCS_2026 · sig:0x4D545456**
> Cible : **< 200 MB RAM** · Résilience **H24** · **Autonome**
> Environnement : **VPS Hidora** → `/home/flp/app/mttv`

---

## 📦 Prérequis

- Un compte [Hidora](https://hidora.com) (Jelastic PaaS)
- Un nœud **Ubuntu 22.04/24.04** (minimum **512 MB RAM**, 1 vCPU)
- **Docker** et **docker-compose** installés (pré-installés sur les nœuds Hidora)
- **Git** pour cloner le dépôt
- Clé SSH privée : `C:\Users\Master\.ssh\hidora`

---

## 🔌 Connexion SSH au VPS Hidora

```bash
ssh -i C:\Users\Master\.ssh\hidora -p 3022 136579-5464@gate.hidora.com
```

> **Note** : Le port **3022** et l'utilisateur **136579-5464** sont spécifiques au nœud Hidora.
> La clé privée se trouve sur la machine locale à `C:\Users\Master\.ssh\hidora`.

---

## 🚀 Déploiement en 4 commandes

Une fois connecté au VPS :

```bash
# 1. Aller dans le répertoire d'installation et cloner le dépôt
cd /home/flp/app
git clone https://github.com/girard444/mttv-flp-core.git mttv
cd mttv

# 2. Copier et configurer les secrets
cp deploy/mttv/.env.example .env
nano .env   # → Vérifier/modifier SMTP_HOST, SMTP_USER, MYSQL_PASSWORD, etc.

# 3. Démarrer les services (mode sobre)
docker compose -f deploy/mttv/docker-compose.yml up -d

# 4. Vérifier que tout tourne (healthcheck détaillé)
curl http://localhost:8000/health/details
```

> **Structure finale** :
> - Dépôt : `/home/flp/app/mttv/`
> - `.env` : `/home/flp/app/mttv/.env`
> - Compose : `/home/flp/app/mttv/deploy/mttv/docker-compose.yml`

---

## ✅ Vérification du déploiement

```bash
# État des conteneurs
docker compose -f deploy/mttv/docker-compose.yml ps

# Logs en temps réel
docker compose -f deploy/mttv/docker-compose.yml logs -f orchestrator

# Health check complet (inclut resource_guardrail)
curl -s http://localhost:8000/health/details | python3 -m json.tool

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

### Variables obligatoires

```bash
MTTV_GITHUB_TOKEN=ghp_...   # Token GitHub avec droits repo
```

### SMTP — Alertes Email (Gmail — pré-configuré)

Le `.env.example` contient déjà les paramètres SMTP Gmail.
**Aucune modification nécessaire** pour utiliser le compte `girard444@gmail.com`.

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=girard444@gmail.com
SMTP_PASS=csjx nyyu ezdl wueu
```

> ⚠️ **Sécurité** : Le mot de passe SMTP (`SMTP_PASS`) est un **mot de passe d'application** Gmail,
> pas le mot de passe principal. Il est stocké dans `.env.example` par commodité,
> mais vous pouvez le modifier si vous souhaitez utiliser un autre compte.

### Base de données MySQL (Hidora locale)

Le VPS Hidora dispose d'une base MySQL locale. Les paramètres sont pré-remplis dans `.env.example` :

```bash
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=flp
MYSQL_PASSWORD=NBui4!fnD32
MYSQL_DATABASE=mttv_flp
```

> **Note** : Si l'orchestrateur tourne dans Docker et que MySQL est sur l'hôte,
> utilisez `host.docker.internal` ou l'IP `172.17.0.1` comme `MYSQL_HOST`.

### Autres variables optionnelles

```bash
MTTV_HF_TOKEN=hf_...                    # Token Hugging Face
ALERT_WEBHOOK_URL=https://discord...    # Webhook d'alerte (canal primaire)
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
- **Seuils configurables** via `.env` : `MAX_DAILY_TRAFFIC_MB`, `MAX_RAM_MB`
- **Alerte automatique** — déclenchée via SMTP (Gmail pré-configuré) + webhook Discord/Slack

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

### Alertes SMTP (Gmail)

Les alertes sont envoyées par email via le serveur SMTP Gmail pré-configuré :

```bash
# Test d'envoi d'alerte depuis le VPS
curl -X POST http://localhost:8000/api/v1/alert/test \
  -H "Content-Type: application/json" \
  -d '{"channel": "smtp", "message": "🧪 Test alerte SMTP MTTV-FLP"}'
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

| Fichier / Commande | Description |
|---------------------|-------------|
| `journalctl -u mttv` | Logs systemd (alternative sans Docker) |
| `docker logs mttv-orchestrator` | Logs de l'orchestrateur |
| `docker logs mttv-ipfs` | Logs du nœud IPFS |
| `zoo-code/guardrail_state.json` | État persistant du garde-fou |

---

## ♻️ Maintenance

### Mise à jour

```bash
cd /home/flp/app/mttv
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
| Connexion MySQL refusée | MYSQL_HOST incorrect dans Docker | Essayer `host.docker.internal` au lieu de `127.0.0.1` |
| SMTP : échec d'envoi | Mot de passe d'application invalide | Régénérer un mot de passe d'application Gmail |

---

## 🔗 Références

- [Hidora Jelastic Documentation](https://docs.hidora.com)
- [IPFS Kubo Documentation](https://github.com/ipfs/kubo)
- [MTTV-FLP Core Repository](https://github.com/girard444/mttv-flp-core)

---

> **Signature** : `sig:0x4D545456` · **Triade** : Ψ → B → Φ
> **Chemin d'installation** : `/home/flp/app/mttv`
> **Mycélium en marche** 🍄
