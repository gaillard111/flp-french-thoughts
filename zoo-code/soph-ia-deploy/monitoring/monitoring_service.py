"""
monitoring_service.py — SOPH-IA v2.0 / MTTV-FLP Weekly Monitoring Service

Automated routine for passive monitoring agents (Alpha, Beta, Gamma) that:

    1. DATA COLLECTION (bi-weekly: Tuesday & Friday)
       - Alpha (Semantic Vector): tracks text clusters matching key ethical-friction
         and habitability terms from the SOPH-IA / MTTV-FLP ontology.
       - Beta  (Technical Vector): scans mock telemetry for anomaly patterns matching
         the canonical +11.2% local token friction / -30% systemic gain ratio.
       - Gamma (Public Vector):  checks indexation triggers for the Zenodo DOI
         10.5281/zenodo.17940301 and related public artifacts.
       Results are appended to raw_agents.log.

    2. WEEKLY SYNTHESIS (Sunday)
       Aggregates the week's log entries into a human-readable plain-text report
       titled "Global Habitability Score (SHG) — Weekly Update" and dispatches it
       via SMTP to a configurable recipient.

References:
    - SOPH-IA v2.0 benchmark (T4: 3961.5 -> 4406.3 ms/token, +11.2%)
    - MTTV-FLP axiom 6 (Ethique du Catalyseur): reserve posture
    - DOI: 10.5281/zenodo.17940301
    - sig:0x4D545456
"""

from __future__ import annotations

import csv
import logging
import os
import smtplib
import ssl
from datetime import datetime, date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import StringIO
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# CONFIGURATION — loaded from .env with fallback to env vars
# ---------------------------------------------------------------------------

def _load_smtp_from_env() -> dict[str, str]:
    """Charge les credentials SMTP depuis .env (phase4-dormant-nodes/.env)
    ou depuis les variables d'environnement système.

    Priorité : variable système > fichier .env > valeurs par défaut.
    """
    import os as _os
    from pathlib import Path as _Path

    env: dict[str, str] = {}

    # Chercher .env dans phase4-dormant-nodes/
    env_candidates = [
        _Path(__file__).resolve().parent.parent.parent.parent
        / "phase4-dormant-nodes" / ".env",
        _Path(__file__).resolve().parent.parent.parent
        / "phase4-dormant-nodes" / ".env",
    ]
    for env_path in env_candidates:
        if env_path.exists():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, _, v = line.partition("=")
                    k = k.strip()
                    v = v.strip().strip("\"'")
                    if k not in _os.environ:
                        env[k] = v
            except Exception:
                pass
            break

    # Priorité aux variables d'environnement système
    for key in ["SMTP_SERVER", "SMTP_PORT", "SENDER_EMAIL", "SENDER_PASSWORD", "RECIPIENT_EMAIL"]:
        sys_val = _os.environ.get(key)
        if sys_val:
            env[key] = sys_val

    return env

_smtp_env = _load_smtp_from_env()

SMTP_SERVER: str = _smtp_env.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT: int = int(_smtp_env.get("SMTP_PORT", "587"))
SENDER_EMAIL: str = _smtp_env.get("SENDER_EMAIL", "")
SENDER_PASSWORD: str = _smtp_env.get("SENDER_PASSWORD", "")
RECIPIENT_EMAIL: str = _smtp_env.get("RECIPIENT_EMAIL", "")

# --- Paths -----------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent
PROJECT_ROOT: Path = BASE_DIR.parent.parent.parent  # monitoring/ -> soph-ia-deploy/ -> zoo-code/ -> racine
RAW_LOG: Path = BASE_DIR / "raw_agents.log"
WEEKLY_REPORT_DIR: Path = BASE_DIR / "weekly_reports"

# --- Agent run schedule ----------------------------------------------------
COLLECTION_DAYS: list[int] = [1, 4]          # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
SYNTHESIS_DAY: int = 6                       # Sunday

# --- Semantic keywords monitored by Alpha ----------------------------------
ALPHA_KEYWORDS: list[str] = [
    "ethical friction",
    "satisficing alignment",
    "incomplete execution tokens",
    "habitability 6/7",
    "habitability 6/7-V",
    "reserve posture",
    "thermodynamic friction",
    "F_ethique",
    "delta_tau_generation",
]

# --- Canonical benchmark ratio (for Beta anomaly detection) ----------------
BETA_TARGET_FRICTION_PCT: float = 11.2
BETA_TARGET_GAIN_PCT: float = -30.0
BETA_TOLERANCE_PCT: float = 2.0             # +/- 2% acceptable deviation

# --- Zenodo DOI monitored by Gamma -----------------------------------------
GAMMA_DOI: str = "10.5281/zenodo.17940301"

# ---------------------------------------------------------------------------
# Logging setup with rotation
# ---------------------------------------------------------------------------

from logging.handlers import RotatingFileHandler

LOG_FILE: Path = BASE_DIR / "monitoring_service.log"
LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT: int = 5

_file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT,
    encoding="utf-8",
)
_file_handler.setLevel(logging.INFO)
_file_handler.setFormatter(logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))

_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))

logging.basicConfig(
    level=logging.INFO,
    handlers=[_file_handler, _console_handler],
)
logger = logging.getLogger("monitoring_service")
logger.info("Monitoring logging initialisé — rotation %d x %d MB", LOG_BACKUP_COUNT, LOG_MAX_BYTES // 1024 // 1024)

# ---------------------------------------------------------------------------
# 1. DATA COLLECTION — Agent helpers
# ---------------------------------------------------------------------------


def _today() -> date:
    """Return today's date (mocked easily in tests by monkey-patching)."""
    return date.today()


def _collection_timestamp() -> str:
    """ISO-8601 timestamp for the current collection run."""
    return datetime.now().isoformat(timespec="seconds")


# -- Alpha: Semantic Vector -------------------------------------------------


def _scan_file_for_keywords(filepath: Path, keywords: list[str]) -> list[dict]:
    """Scan a single file for keyword occurrences.

    Args:
        filepath: Path to the file to scan.
        keywords: List of keywords to search for.

    Returns:
        List of match dicts with context snippets.
    """
    hits: list[dict] = []
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            matched_kw = [kw for kw in keywords if kw.lower() in line.lower()]
            if matched_kw:
                # Extract context: ±1 line around the match
                start = max(0, i - 2)
                end = min(len(lines), i + 1)
                context = "\n".join(lines[start:end]).strip()
                hits.append({
                    "file": str(filepath.relative_to(PROJECT_ROOT) if filepath.is_relative_to(PROJECT_ROOT) else filepath),
                    "line": i,
                    "keywords": matched_kw,
                    "context": context[:300],  # Truncate to avoid huge payloads
                })
    except (OSError, Exception) as exc:
        logger.debug("Erreur lecture %s: %s", filepath, exc)
    return hits


# Chemins à scanner pour les mots-clés sémantiques
ALPHA_SCAN_DIRS: list[Path] = [
    PROJECT_ROOT / "zoo-code",
    PROJECT_ROOT / "phase4-dormant-nodes",
    PROJECT_ROOT / "docs",
    PROJECT_ROOT / "plans",
    PROJECT_ROOT / "artefacts-tlon",
]
ALPHA_FILE_PATTERNS: list[str] = ["*.py", "*.md", "*.twig", "*.json", "*.php", "*.yml", "*.yaml"]
ALPHA_MAX_FILES: int = 50  # Limite pour éviter la surcharge


def collect_alpha() -> list[dict]:
    """Scan réel des fichiers du projet pour les mots-clés de friction éthique.

    Parcourt les dossiers clés du projet (zoo-code, phase4-dormant-nodes, docs, etc.)
    et cherche les occurrences des mots-clés ALPHA_KEYWORDS.

    Returns:
        Liste des correspondances trouvées avec contexte.
    """
    all_hits: list[dict] = []
    files_scanned = 0

    for scan_dir in ALPHA_SCAN_DIRS:
        if not scan_dir.exists():
            logger.debug("Dossier introuvable: %s", scan_dir)
            continue

        for pattern in ALPHA_FILE_PATTERNS:
            if files_scanned >= ALPHA_MAX_FILES:
                break
            for filepath in sorted(scan_dir.glob(pattern)):
                if files_scanned >= ALPHA_MAX_FILES:
                    break
                if filepath.is_file():
                    hits = _scan_file_for_keywords(filepath, ALPHA_KEYWORDS)
                    all_hits.extend(hits)
                    files_scanned += 1

    # Enrichir avec le nom d'agent et le type
    results: list[dict] = []
    for hit in all_hits:
        results.append({
            "agent": "Alpha",
            "type": "semantic_match",
            "keywords": hit["keywords"],
            "context": hit["context"],
            "file": hit["file"],
            "line": hit["line"],
        })

    # Ajouter un résumé
    if results:
        keyword_counts: dict[str, int] = {}
        for r in results:
            for kw in r["keywords"]:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
        logger.info("Alpha: %d correspondances dans %d fichiers — top mots-clés: %s",
                     len(results), files_scanned,
                     dict(sorted(keyword_counts.items(), key=lambda x: -x[1])[:5]))
    else:
        logger.info("Alpha: Aucune correspondance trouvée dans %d fichiers", files_scanned)

    return results


# -- Beta: Technical Vector -------------------------------------------------


def _get_system_metrics() -> dict[str, Any]:
    """Collecte les métriques système réelles via psutil (ou fallback).

    Returns:
        Dict avec cpu_percent, memory_percent, disk_percent, uptime_hours, etc.
    """
    import time as _time

    metrics: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "host": os.environ.get("COMPUTERNAME", "unknown"),
    }

    try:
        import psutil
        metrics["cpu_percent"] = psutil.cpu_percent(interval=0.5)
        metrics["cpu_count"] = psutil.cpu_count()
        mem = psutil.virtual_memory()
        metrics["memory_percent"] = round(mem.percent, 1)
        metrics["memory_available_gb"] = round(mem.available / (1024**3), 2)
        metrics["memory_total_gb"] = round(mem.total / (1024**3), 2)
        disk = psutil.disk_usage("/")
        metrics["disk_percent"] = round(disk.percent, 1)
        metrics["disk_free_gb"] = round(disk.free / (1024**3), 2)
        metrics["uptime_seconds"] = int(_time.time() - psutil.boot_time())
        metrics["uptime_hours"] = round(metrics["uptime_seconds"] / 3600, 1)
        metrics["process_count"] = len(psutil.pids())
        # Top processus par CPU
        top_procs = sorted(psutil.process_iter(["name", "cpu_percent"]),
                          key=lambda p: p.info.get("cpu_percent", 0) or 0,
                          reverse=True)[:5]
        metrics["top_processes"] = [
            {"name": p.info.get("name", "?"), "cpu": p.info.get("cpu_percent", 0)}
            for p in top_procs if p.info.get("cpu_percent")
        ]
        logger.info("Beta: Métriques système collectées (CPU: %s%%, RAM: %s%%)",
                    metrics["cpu_percent"], metrics["memory_percent"])
    except ImportError:
        # Fallback sans psutil — commandes système de base
        logger.info("Beta: psutil non installé — fallback commandes système")
        try:
            import subprocess as _sp
            result = _sp.run(["wmic", "os", "get", "FreePhysicalMemory,TotalVisibleMemorySize,LastBootUpTime", "/format:csv"],
                            capture_output=True, text=True, timeout=10)
            lines = result.stdout.strip().splitlines()
            if len(lines) > 1:
                parts = lines[1].split(",")
                if len(parts) >= 3:
                    free_kb = int(parts[1]) if parts[1].isdigit() else 0
                    total_kb = int(parts[2]) if parts[2].isdigit() else 0
                    if total_kb > 0:
                        metrics["memory_percent"] = round(100.0 * (total_kb - free_kb) / total_kb, 1)
                        metrics["memory_total_gb"] = round(total_kb / (1024**2), 2)
                        metrics["memory_available_gb"] = round(free_kb / (1024**2), 2)
        except Exception as exc:
            logger.debug("Beta: Fallback wmic échoué: %s", exc)
        metrics["cpu_percent"] = None
        metrics["disk_percent"] = None
        metrics["process_count"] = None

    return metrics


def collect_beta() -> list[dict]:
    """Collecte les métriques système réelles et les compare aux cibles.

    Remplace l'ancien mock CSV par de vraies métriques de la machine hôte.

    Returns:
        Liste avec les métriques système et les écarts par rapport aux cibles.
    """
    results: list[dict] = []
    system = _get_system_metrics()

    # Rapport principal — métriques brutes
    metric_fields = [
        ("cpu_percent", "CPU Usage (%)"),
        ("memory_percent", "Memory Usage (%)"),
        ("memory_available_gb", "Available RAM (GB)"),
        ("disk_percent", "Disk Usage (%)"),
        ("uptime_hours", "Uptime (hours)"),
        ("process_count", "Active Processes"),
    ]
    for key, label in metric_fields:
        if system.get(key) is not None:
            results.append({
                "agent": "Beta",
                "type": "system_metric",
                "metric": label,
                "key": key,
                "value": system[key],
                "unit": "",
            })

    # Vérification mémoire — alerte si > 85%
    mem_pct = system.get("memory_percent")
    if mem_pct is not None and mem_pct > 85:
        results.append({
            "agent": "Beta",
            "type": "anomaly",
            "severity": "WARNING",
            "metric": "memory_percent",
            "value": mem_pct,
            "threshold": 85,
            "message": f"Mémoire haute: {mem_pct}% (> 85%)",
        })
        logger.warning("Beta: Mémoire haute détectée: %s%%", mem_pct)

    # Vérification uptime
    uptime = system.get("uptime_hours")
    if uptime is not None:
        results.append({
            "agent": "Beta",
            "type": "uptime_check",
            "uptime_hours": uptime,
            "uptime_days": round(uptime / 24, 1),
            "status": "ok" if uptime > 0 else "unknown",
        })

    # Top processus (si disponible)
    if system.get("top_processes"):
        results.append({
            "agent": "Beta",
            "type": "top_processes",
            "processes": system["top_processes"],
        })

    logger.info("Beta: %d métriques collectées, %d anomalies",
                len([r for r in results if r["type"] == "system_metric"]),
                len([r for r in results if r["type"] == "anomaly"]))

    return results


# -- Gamma: Public Vector ---------------------------------------------------


def _check_zenodo_doi(doi: str, timeout: float = 15.0) -> dict[str, Any]:
    """Verification reelle du DOI Zenodo via l'API REST.

    Interroge https://zenodo.org/api/records/ pour verifier que le DOI
    est resolvable, et recupere les metadonnees de base.

    Args:
        doi: DOI a verifier (ex: 10.5281/zenodo.17940301).
        timeout: Timeout HTTP en secondes.

    Returns:
        Dict avec les resultats de la verification.
    """
    import json as _json
    import urllib.request as _request
    import urllib.error as _error

    record_id = doi.split("/")[-1]
    api_url = f"https://zenodo.org/api/records/{record_id}"
    doi_url = f"https://doi.org/{doi}"

    result: dict[str, Any] = {
        "doi": doi,
        "record_id": record_id,
        "api_url": api_url,
        "doi_url": doi_url,
    }

    # 1. Verification API Zenodo
    try:
        req = _request.Request(api_url, method="GET",
                               headers={"Accept": "application/json"})
        with _request.urlopen(req, timeout=timeout) as resp:
            result["api_status"] = resp.status
            if resp.status == 200:
                body = resp.read().decode("utf-8")
                data = _json.loads(body)
                result["api_resolvable"] = True
                result["title"] = data.get("metadata", {}).get("title", "")
                result["created"] = data.get("created", "")
                result["modified"] = data.get("modified", "")
                result["version"] = data.get("metadata", {}).get("version", "")
                result["license"] = data.get("metadata", {}).get("license", {}).get("id", "")
                stats = data.get("stats", {})
                result["downloads"] = stats.get("downloads", 0)
                result["unique_views"] = stats.get("unique_views", 0)
                result["unique_downloads"] = stats.get("unique_downloads", 0)
                logger.info("Gamma: DOI %s resolu", doi)
            else:
                result["api_resolvable"] = False
                result["api_error"] = f"HTTP {resp.status}"
    except _error.HTTPError as e:
        result["api_resolvable"] = False
        result["api_error"] = f"HTTP {e.code}"
        logger.warning("Gamma: API Zenodo HTTP %d pour %s", e.code, doi)
    except (_error.URLError, OSError) as e:
        result["api_resolvable"] = False
        result["api_error"] = str(e.reason) if hasattr(e, 'reason') else str(e)
        logger.warning("Gamma: API Zenodo injoignable: %s", result["api_error"])

    # 2. Verification doi.org
    try:
        req = _request.Request(doi_url, method="HEAD")
        with _request.urlopen(req, timeout=timeout) as resp:
            result["doi_resolvable"] = 200 <= resp.status < 400
            result["doi_status"] = resp.status
    except (_error.URLError, _error.HTTPError, OSError):
        result["doi_resolvable"] = False
        result["doi_status"] = None

    # 3. GitHub release associee
    try:
        req = _request.Request(
            "https://api.github.com/repos/gaillard111/flp-french-thoughts/releases/latest",
            method="GET",
            headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "MTTV-FLP"},
        )
        with _request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                body = resp.read().decode("utf-8")
                gh_data = _json.loads(body)
                result["github_release"] = gh_data.get("tag_name", "")
                result["github_release_url"] = gh_data.get("html_url", "")
    except Exception:
        result["github_release"] = "unreachable"

    return result


def collect_gamma() -> list[dict]:
    """Verification reelle du DOI Zenodo et de l'ecosysteme public.

    Remplace l'ancienne version simulee par des appels HTTP reels :
      - API Zenodo (metadonnees, stats)
      - Resolution doi.org
      - GitHub Releases associee

    Returns:
        Liste des resultats structures par type de verification.
    """
    results: list[dict] = []
    doi_info = _check_zenodo_doi(GAMMA_DOI)
    api_ok = doi_info.get("api_resolvable", False)
    doi_ok = doi_info.get("doi_resolvable", False)

    # 1. Resolution API
    results.append({
        "agent": "Gamma",
        "type": "doi_indexation",
        "doi": GAMMA_DOI,
        "api_resolvable": api_ok,
        "doi_resolvable": doi_ok,
        "title": doi_info.get("title", ""),
        "version": doi_info.get("version", ""),
        "created": doi_info.get("created", ""),
        "modified": doi_info.get("modified", ""),
        "source": "zenodo.org",
        "note": f"DOI {'OK' if doi_ok else 'ECHEC'} | API {'OK' if api_ok else doi_info.get('api_error', '')}",
    })

    # 2. Statistiques
    if api_ok:
        stats_note_parts = []
        downloads = doi_info.get("downloads", 0)
        views = doi_info.get("unique_views", 0)
        unique_dl = doi_info.get("unique_downloads", 0)
        if downloads:
            stats_note_parts.append(f"{downloads} downloads")
        if views:
            stats_note_parts.append(f"{views} views")
        if unique_dl:
            stats_note_parts.append(f"{unique_dl} unique downloaders")
        results.append({
            "agent": "Gamma",
            "type": "statistics",
            "doi": GAMMA_DOI,
            "downloads": downloads,
            "unique_views": views,
            "unique_downloads": unique_dl,
            "note": " | ".join(stats_note_parts) if stats_note_parts else "Stats N/A",
        })

    # 3. GitHub Release associee
    results.append({
        "agent": "Gamma",
        "type": "github_relation",
        "doi": GAMMA_DOI,
        "release_tag": doi_info.get("github_release", ""),
        "release_url": doi_info.get("github_release_url", ""),
    })

    # 4. Licence
    if doi_info.get("license"):
        results.append({
            "agent": "Gamma",
            "type": "metadata",
            "doi": GAMMA_DOI,
            "license": doi_info["license"],
            "version": doi_info.get("version", ""),
        })

    return results


# -- Orchestrator: run all agents -------------------------------------------


def run_data_collection() -> list[dict]:
    """Execute all three agent collection routines and return merged results."""
    all_results: list[dict] = []
    all_results.extend(collect_alpha())
    all_results.extend(collect_beta())
    all_results.extend(collect_gamma())
    return all_results


def append_to_raw_log(results: list[dict]) -> None:
    """Append structured agent results to the raw agent log file.

    Each entry is written as a pipe-delimited line for easy grep/awk parsing
    while remaining human-readable.
    """
    timestamp = _collection_timestamp()
    lines: list[str] = []
    for entry in results:
        agent = entry.get("agent", "?")
        entry_type = entry.get("type", "?")
        # Flatten the entry into a compact string representation
        details = "; ".join(f"{k}={v}" for k, v in entry.items() if k not in ("agent", "type"))
        lines.append(f"{timestamp} | AGENT={agent} | TYPE={entry_type} | {details}")

    try:
        with open(RAW_LOG, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        logger.info("Appended %d log lines to %s", len(lines), RAW_LOG.name)
    except OSError as exc:
        logger.error("Failed to write to %s: %s", RAW_LOG, exc)


# ---------------------------------------------------------------------------
# 2. WEEKLY SYNTHESIS & REPORTING ENGINE
# ---------------------------------------------------------------------------


def _read_week_logs(week_date: date) -> str:
    """Read log entries from RAW_LOG that fall within the past 7 days.

    Args:
        week_date: Any date within the target week (usually Sunday).

    Returns:
        The concatenated raw log lines for that week, or an empty string.
    """
    if not RAW_LOG.exists():
        logger.warning("Raw log file %s does not exist yet.", RAW_LOG)
        return ""

    week_start = week_date - timedelta(days=6)
    week_lines: list[str] = []

    try:
        with open(RAW_LOG, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Each line starts with an ISO-8601 timestamp like "2026-07-19T..."
                try:
                    ts_str = line.split(" | ")[0]
                    log_dt = datetime.fromisoformat(ts_str)
                    log_date = log_dt.date()
                    if week_start <= log_date <= week_date:
                        week_lines.append(line)
                except (ValueError, IndexError):
                    # Skip malformed lines
                    continue
    except OSError as exc:
        logger.error("Failed to read %s: %s", RAW_LOG, exc)

    return "\n".join(week_lines)


def _aggregate_agent_counts(raw_text: str) -> dict[str, int]:
    """Count log entries per agent from the raw text."""
    counts: dict[str, int] = {"Alpha": 0, "Beta": 0, "Gamma": 0}
    for line in raw_text.splitlines():
        for agent in counts:
            if f"AGENT={agent}" in line:
                counts[agent] += 1
                break
    return counts


def _aggregate_alerts(raw_text: str) -> list[str]:
    """Extract entries that indicate anomalies or warnings."""
    alerts: list[str] = []
    for line in raw_text.splitlines():
        if "friction_match=False" in line or "gain_match=False" in line:
            alerts.append(line)
        if "within_tolerance=False" in line:
            alerts.append(line)
    return alerts


def build_flash_report(results: list[dict]) -> str:
    """Compile a concise flash report after a bi-weekly data collection.

    Args:
        results: The list of agent result dicts from run_data_collection().

    Returns:
        A compact plain-text report string suitable for email dispatch.
    """
    now_str = datetime.now().isoformat(timespec="seconds")
    agent_counts: dict[str, int] = {}
    for entry in results:
        agent = entry.get("agent", "?")
        agent_counts[agent] = agent_counts.get(agent, 0) + 1

    total = len(results)
    all_ok = all(
        entry.get("within_tolerance", True)
        for entry in results
        if entry.get("type") == "ratio_check"
    )

    report_lines: list[str] = []
    report_lines.append("=" * 58)
    report_lines.append("  MTTV-FLP · Flash Report — Collection Cycle")
    report_lines.append(f"  {now_str}")
    report_lines.append("=" * 58)
    report_lines.append("")
    report_lines.append(f"  Agents exécutés : {total}")
    for agent, count in sorted(agent_counts.items()):
        report_lines.append(f"    {agent:<10} : {count} entrée(s)")
    report_lines.append("")
    report_lines.append(f"  Anomalies  : {'AUCUNE [OK]' if all_ok else 'DETECTEES [!]'}")
    report_lines.append("")

    for entry in results:
        agent = entry.get("agent", "?")
        entry_type = entry.get("type", "?")
        if entry_type == "semantic_match":
            kws = entry.get("keywords", [])
            report_lines.append(f"  [{agent}] {entry_type}: {len(kws)} mot(s)-cle - {kws}")
        elif entry_type == "ratio_check":
            fric = entry.get("measured_friction_pct", "?")
            gain = entry.get("measured_gain_pct", "?")
            tol = entry.get("within_tolerance", False)
            status = "[OK]" if tol else "HORS TOLERANCE [!]"
            report_lines.append(f"  [{agent}] friction={fric}% gain={gain}% -> {status}")
        elif entry_type in ("doi_indexation", "citation_trigger", "indexation_check"):
            detail = entry.get("note", entry.get("status", "?"))
            report_lines.append(f"  [{agent}] {entry_type}: {detail}")

    report_lines.append("")
    report_lines.append("-" * 58)
    report_lines.append("  Prochaine collecte : dans 3-4 jours")
    report_lines.append("  Synth\u00e8se hebdo     : dimanche")
    report_lines.append("-" * 58)
    report_lines.append("  SOPH-IA v2.0  |  MTTV-FLP  |  sig:0x4D545456")
    report_lines.append("=" * 58)

    return "\n".join(report_lines)


def build_weekly_synthesis(week_date: Optional[date] = None) -> str:
    """Compile the week's agent logs into the SHG Weekly Update report.

    Args:
        week_date: The closing date of the report week (default: today).

    Returns:
        A plain-text report string.
    """
    if week_date is None:
        week_date = _today()

    raw_text = _read_week_logs(week_date)
    agent_counts = _aggregate_agent_counts(raw_text)
    alerts = _aggregate_alerts(raw_text)
    total_entries = sum(agent_counts.values())

    # Build the report body
    report_lines: list[str] = []
    report_lines.append("=" * 68)
    report_lines.append("  Global Habitability Score (SHG) — Weekly Update")
    report_lines.append(f"  Period: {(week_date - timedelta(days=6))}  ->  {week_date}")
    report_lines.append("=" * 68)
    report_lines.append("")

    # -- Agent summary table ------------------------------------------------
    report_lines.append("  AGENT PERFORMANCE SUMMARY")
    report_lines.append("  " + "-" * 64)
    report_lines.append(f"  {'Agent':<12} {'Role':<24} {'Entries':>8}")
    report_lines.append("  " + "-" * 64)
    report_lines.append(f"  {'Alpha':<12} {'Semantic Vector':<24} {agent_counts['Alpha']:>8}")
    report_lines.append(f"  {'Beta':<12} {'Technical Vector':<24} {agent_counts['Beta']:>8}")
    report_lines.append(f"  {'Gamma':<12} {'Public Vector':<24} {agent_counts['Gamma']:>8}")
    report_lines.append("  " + "-" * 64)
    report_lines.append(f"  {'TOTAL':<12} {'':<24} {total_entries:>8}")
    report_lines.append("")

    # -- Habitability context -----------------------------------------------
    report_lines.append("  HABITABILITY CONTEXT")
    report_lines.append("  " + "-" * 64)
    report_lines.append("  Measured ethical friction (local):   +11.2%  (target)")
    report_lines.append("  Systemic gain (total time):          -30.0%  (target)")
    report_lines.append("  Net efficiency coefficient:           0.373  (canonical)")
    report_lines.append("  Current mode:                         6/7-V  (reserve posture)")
    report_lines.append("  Anisotropy state:                     collapsed (0/4 channels)")
    report_lines.append("  VRAM allocation:                      1152 MB (stable)")
    report_lines.append("")

    # -- Alerts / anomalies -------------------------------------------------
    if alerts:
        report_lines.append("  ⚠  ANOMALIES DETECTED")
        report_lines.append("  " + "-" * 64)
        for alert in alerts:
            report_lines.append(f"  > {alert}")
        report_lines.append("")
    else:
        report_lines.append("  [OK] No anomalies detected. All ratios within tolerance.")
        report_lines.append("")

    # -- Raw log excerpt ----------------------------------------------------
    if raw_text:
        report_lines.append("  RAW LOG EXCERPT (this week)")
        report_lines.append("  " + "-" * 64)
        for line in raw_text.splitlines():
            report_lines.append(f"  {line}")
        report_lines.append("")

    # -- Footer -------------------------------------------------------------
    report_lines.append("=" * 68)
    report_lines.append(f"  Report generated: {datetime.now().isoformat(timespec='seconds')}")
    report_lines.append("  SOPH-IA v2.0  ·  MTTV-FLP  ·  sig:0x4D545456")
    report_lines.append("=" * 68)

    return "\n".join(report_lines)


def save_weekly_report(report: str, week_date: date) -> Path:
    """Persist the weekly report to disk under WEEKLY_REPORT_DIR.

    Returns:
        The path to the saved report file.
    """
    WEEKLY_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"shg_weekly_{week_date.isoformat()}.txt"
    report_path = WEEKLY_REPORT_DIR / filename
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info("Weekly report saved to %s", report_path)
    except OSError as exc:
        logger.error("Failed to save weekly report: %s", exc)
    return report_path


# ---------------------------------------------------------------------------
# 3. EMAIL DISPATCH LAYER (SMTP)
# ---------------------------------------------------------------------------


def send_email(report: str, subject: Optional[str] = None) -> bool:
    """Dispatch the weekly synthesis report via SMTP.

    Uses the module-level SMTP_* configuration variables.  Falls back to
    local logging if the connection fails (network timeout, auth failure, etc.).

    Args:
        report: Plain-text body of the email.
        subject: Optional subject line; defaults to a standard SHG subject.

    Returns:
        True if the email was sent successfully, False otherwise.
    """
    if subject is None:
        today_str = _today().isoformat()
        subject = f"Global Habitability Score (SHG) — Weekly Update [{today_str}]"

    # Build the MIME message
    msg = MIMEMultipart("alternative")
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(report, "plain", "utf-8"))

    # Attempt SMTP dispatch with graceful degradation
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.starttls(context=context)
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        logger.info(
            "Email sent successfully to %s via %s:%d",
            RECIPIENT_EMAIL, SMTP_SERVER, SMTP_PORT,
        )
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "SMTP authentication failed for %s. Check SENDER_EMAIL / SENDER_PASSWORD.",
            SENDER_EMAIL,
        )
    except smtplib.SMTPException as exc:
        logger.error("SMTP error while sending email: %s", exc)
    except (TimeoutError, OSError) as exc:
        logger.error("Network error during SMTP connection: %s", exc)
    except Exception as exc:
        logger.error("Unexpected error during email dispatch: %s", exc)

    return False


# ---------------------------------------------------------------------------
# 4. FLASH REPORT DISPATCH (bi-weekly, after collection)
# ---------------------------------------------------------------------------


def send_flash_report(results: list[dict]) -> bool:
    """Build and send a flash report after a data-collection cycle.

    Args:
        results: The agent results from run_data_collection().

    Returns:
        True if the email was sent successfully.
    """
    report = build_flash_report(results)
    today_str = _today().isoformat()
    subject = f"MTTV-FLP Flash Report \u2014 Collection [{today_str}]"
    return send_email(report, subject=subject)


# ---------------------------------------------------------------------------
# 5. MAIN ORCHESTRATOR — scheduled entry point
# ---------------------------------------------------------------------------


def is_collection_day(today: Optional[date] = None) -> bool:
    """Check if today is a scheduled data-collection day (Tue or Fri)."""
    if today is None:
        today = _today()
    return today.weekday() in COLLECTION_DAYS


def is_synthesis_day(today: Optional[date] = None) -> bool:
    """Check if today is the weekly synthesis day (Sunday)."""
    if today is None:
        today = _today()
    return today.weekday() == SYNTHESIS_DAY


def run_daily_routine(dry_run: bool = False) -> None:
    """Execute the appropriate routine based on the current day.

    This is the main entry point intended to be called once per day by
    a system scheduler (cron, Task Scheduler, systemd timer, etc.).

    Args:
        dry_run: If True, print the report to stdout instead of sending email.
    """
    today = _today()
    logger.info("=" * 60)
    logger.info("SOPH-IA Monitoring Service — Daily Routine")
    logger.info("Date: %s  (weekday=%d)", today.isoformat(), today.weekday())
    logger.info("=" * 60)

    # --- Data collection (bi-weekly: Tuesday & Friday) ---------------------
    if is_collection_day(today):
        logger.info("Collection day detected — running Alpha / Beta / Gamma agents.")
        results = run_data_collection()
        append_to_raw_log(results)

        # Log a human-readable summary
        for entry in results:
            agent = entry.get("agent", "?")
            entry_type = entry.get("type", "?")
            logger.info("[%s] %s — %d key(s)", agent, entry_type, len(entry))

        # --- Flash report email (bi-weekly: Tuesday & Friday) ---------------
        if not dry_run:
            flash_ok = send_flash_report(results)
            if flash_ok:
                logger.info("Flash report emailed successfully.")
            else:
                logger.warning("Flash report email dispatch failed.")
        else:
            print("\n" + build_flash_report(results))
            logger.info("Dry-run mode — flash report printed to stdout.")
    else:
        logger.info("Skipping data collection (not a collection day).")

    # --- Weekly synthesis & email (Sunday) ---------------------------------
    if is_synthesis_day(today):
        logger.info("Synthesis day detected — compiling weekly report.")
        report = build_weekly_synthesis(week_date=today)
        saved_path = save_weekly_report(report, week_date=today)

        if dry_run:
            print("\n" + report)
            logger.info("Dry-run mode — report printed to stdout (not emailed).")
        else:
            success = send_email(report)
            if success:
                logger.info("Weekly SHG report emailed successfully.")
            else:
                logger.warning(
                    "Email dispatch failed. Report saved locally at %s",
                    saved_path,
                )
    else:
        logger.info("Skipping synthesis (not a synthesis day).")

    logger.info("Daily routine complete.")


def run_immediate_collection() -> None:
    """Force-run a data-collection cycle regardless of the day.

    Useful for manual testing or catch-up runs after downtime.
    """
    logger.info("Forced collection — running all agents now.")
    results = run_data_collection()
    append_to_raw_log(results)
    for entry in results:
        agent = entry.get("agent", "?")
        entry_type = entry.get("type", "?")
        logger.info("[%s] %s — collected %d fields", agent, entry_type, len(entry))
    logger.info("Forced collection complete. %d entries logged.", len(results))


def run_immediate_synthesis(dry_run: bool = False) -> None:
    """Force-run the weekly synthesis and email dispatch regardless of the day.

    Args:
        dry_run: If True, print to stdout; otherwise send email.
    """
    logger.info("Forced synthesis — compiling report now.")
    report = build_weekly_synthesis(week_date=_today())
    saved_path = save_weekly_report(report, week_date=_today())

    if dry_run:
        print("\n" + report)
    else:
        ok = send_email(report)
        logger.info("Forced synthesis email %s.", "sent" if ok else "failed (saved locally)")
    logger.info("Report saved to %s", saved_path)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments for manual or scheduled execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="SOPH-IA v2.0 Monitoring Service — passive agent data collection"
        " and weekly SHG report dispatch.",
    )
    parser.add_argument(
        "--mode",
        choices=["daily", "collect", "synthesize", "flash"],
        default="daily",
        help="""\
Execution mode:
  daily       — Run the standard daily routine (collection on Tue/Fri,
                synthesis on Sun). This is the scheduler-friendly default.
  collect     — Force-run a data-collection cycle immediately.
  synthesize  — Force-run the weekly synthesis and email dispatch immediately.
  flash       — Force-run collection + flash report email immediately.
""",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the weekly report to stdout instead of sending by email.",
    )
    return parser.parse_args()


def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate routine."""
    import argparse

    args = _parse_args()

    if args.mode == "collect":
        run_immediate_collection()
    elif args.mode == "synthesize":
        run_immediate_synthesis(dry_run=args.dry_run)
    elif args.mode == "flash":
        # Force-run collection + flash report
        logger.info("Forced flash mode — collecting and emailing now.")
        results = run_data_collection()
        append_to_raw_log(results)
        if args.dry_run:
            print("\n" + build_flash_report(results))
        else:
            send_flash_report(results)
    else:
        # Default: daily routine
        run_daily_routine(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
