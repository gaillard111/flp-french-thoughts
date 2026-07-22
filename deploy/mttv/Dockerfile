# syntax=docker/dockerfile:1
# ──────────────────────────────────────────────────────────────────────────────
# MTTV-FLP — Image Docker Légère pour l'Orchestrateur
# Cible : VPS Hidora (PaaS Jelastic) — < 200 MB RAM
# Signature SCS_2026 · sig:0x4D545456
# ──────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim-bookworm AS base

LABEL org.opencontainers.image.title="MTTV-FLP Orchestrator"
LABEL org.opencontainers.image.description="Orchestrateur sobre du réseau MTTV-FLP pour VPS Hidora"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="girard444@gmail.com"
LABEL org.opencontainers.image.licenses="MIT"
LABEL sig="0x4D545456"

# ── Éviter les warnings pip et l'interactivité ──────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# ── Installation des dépendances système minimales ───────────────────────────
RUN set -eux; \
    apt-get update -qq; \
    apt-get install -y -qq --no-install-recommends \
        curl \
        ca-certificates \
        gosu \
        tini \
    ; \
    # Nettoyage agressif pour image minimale
    apt-get clean; \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# ── Application des dépendances Python ───────────────────────────────────────
WORKDIR /app
COPY deploy/mttv/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copie du code métier (uniquement ce qui est nécessaire au runtime) ──────
# On copie les modules Python essentiels (orchestrateur, gateway, pinner)
COPY zoo-code/mttv_orchestrator.py      /app/zoo-code/mttv_orchestrator.py
COPY zoo-code/api_gateway.py            /app/zoo-code/api_gateway.py
COPY zoo-code/quorum_orchestrator.py    /app/zoo-code/quorum_orchestrator.py
COPY zoo-code/quorum_state.json         /app/zoo-code/quorum_state.json
COPY zoo-code/evolutionary_seeder.py    /app/zoo-code/evolutionary_seeder.py
COPY zoo-code/deploy_seeds_ipfs.py      /app/zoo-code/deploy_seeds_ipfs.py
COPY zoo-code/agent_pollinator.py       /app/zoo-code/agent_pollinator.py
COPY zoo-code/resource_guardrail.py     /app/zoo-code/resource_guardrail.py

# Scripts de l'Axe dormant
COPY phase4-dormant-nodes/              /app/phase4-dormant-nodes/

# Scripts de monitoring SOPH-IA
COPY zoo-code/soph-ia-deploy/monitoring/ /app/zoo-code/soph-ia-deploy/monitoring/

# Entrypoint et scripts de déploiement
COPY deploy/mttv/entrypoint.sh          /app/entrypoint.sh
COPY deploy/mttv/healthcheck.py         /app/healthcheck.py

RUN chmod +x /app/entrypoint.sh /app/healthcheck.py

# ── Création des répertoires de données persistantes ────────────────────────
RUN mkdir -p /data/ipfs /data/logs /data/seeds && \
    chmod 755 /data/ipfs /data/logs /data/seeds

# ── Utilisateur non-root pour la sécurité ────────────────────────────────────
RUN groupadd -r mttv -g 1999 && \
    useradd -r -g mttv -u 1999 -d /app -s /sbin/nologin mttv && \
    chown -R mttv:mttv /app /data

# ── Healthcheck par défaut ───────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=15s \
    CMD python /app/healthcheck.py

# ── Point d'entrée ──────────────────────────────────────────────────────────
ENTRYPOINT ["/usr/bin/tini", "--", "/app/entrypoint.sh"]
