#!/usr/bin/env python3
"""envoyer_rapport.py — Envoie le rapport Mycélium par email

Utilise la config SMTP Gmail du projet.
Planification : quotidienne via Windows Task Scheduler.

Usage :
    python zoo-code/envoyer_rapport.py                    # Envoi immédiat
    python zoo-code/envoyer_rapport.py --html              # Rapport HTML complet
    python zoo-code/envoyer_rapport.py --to email@         # Destinataire personnalisé
    python zoo-code/envoyer_rapport.py --schedule          # Planifier la tâche quotidienne

sig:0x4D5454562D464C50
"""

import argparse
import json
import logging
import os
import smtplib
import subprocess
import sys
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
RAPPORT_SCRIPT = BASE_DIR / "rapport_mycelium.py"
RAPPORTS_DIR = BASE_DIR / "rapports_mycelium"
VALIDATION_SUMMARY = BASE_DIR / "validation" / "out" / "validation_summary.json"
VALIDATION_GATE = BASE_DIR / "agent-1" / "fragments" / "validation_gate.json"

# ── Configuration SMTP Gmail ─────────────────────────────────────────
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "girard444@gmail.com"
SMTP_PASS = "csjx nyyu ezdl wueu"
DEFAULT_TO = "girard444@gmail.com"

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("envoyer_rapport")

API_HEALTH_URL = "http://localhost:8000/health"


def get_api_status() -> dict:
    """Récupère le statut en direct de l'API Gateway."""
    try:
        import urllib.request
        with urllib.request.urlopen(API_HEALTH_URL, timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"status": "unreachable", "error": str(e)}


def get_process_status() -> list[dict]:
    """Liste les processus Python MTTV actifs."""
    processes = []
    try:
        import psutil
        for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time", "memory_info"]):
            try:
                cmdline = proc.info.get("cmdline") or []
                cmd = " ".join(cmdline) if cmdline else ""
                if "python" in proc.info.get("name", "").lower() or "python" in cmd:
                    # Filtrer pour ne garder que les processus du projet
                    if "zoo-code" in cmd or "mttv" in cmd.lower() or "api_gateway" in cmd:
                        mem_mb = proc.info["memory_info"].rss / 1024 / 1024 if proc.info["memory_info"] else 0
                        uptime = datetime.now().timestamp() - proc.info["create_time"]
                        processes.append({
                            "pid": proc.info["pid"],
                            "cmd": cmd[:80],
                            "mem_mb": round(mem_mb, 1),
                            "uptime_h": round(uptime / 3600, 1),
                        })
            except Exception:
                pass
    except ImportError:
        processes.append({"note": "psutil non installé"})
    except Exception as e:
        processes.append({"error": str(e)})
    return processes


def get_validation_status() -> list[str]:
    """Lit l'état de la validation MPVR (taux de passage, quarantaine)."""
    lines = []
    for label, path in [
        ("Pipeline (CLI)", VALIDATION_SUMMARY),
        ("Gate Agent 1", VALIDATION_GATE),
    ]:
        try:
            if not path.exists():
                lines.append(f"  {label}: pas encore exécuté")
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            total = data.get("total", 0)
            passed = data.get("passed", data.get("validated", 0))
            quarantined = data.get("quarantined", 0)
            pct = (passed / total * 100) if total else 0.0
            icon = "✅" if quarantined == 0 else "⚠️"
            lines.append(
                f"  {label}: {icon} {passed}/{total} validés ({pct:.0f}%), "
                f"{quarantined} en quarantaine"
            )
        except Exception as e:
            lines.append(f"  {label}: erreur lecture ({e})")
    return lines


def generer_rapport_etendu() -> tuple[str, str]:
    """Génère un rapport enrichi avec statut live + historique."""
    # 1. Statut API
    api = get_api_status()
    api_ok = api.get("status") == "healthy"

    # 2. Processus
    procs = get_process_status()

    # 3. Rapport mycélium standard
    try:
        result = subprocess.run(
            [sys.executable, str(RAPPORT_SCRIPT), "--last", "15"],
            capture_output=True, text=True, cwd=str(BASE_DIR), timeout=30
        )
        mycelium_report = result.stdout if result.returncode == 0 else "Erreur: " + result.stderr
    except Exception as e:
        mycelium_report = f"Erreur génération rapport: {e}"

    # 4. Assemblage texte
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = []
    lines.append("=" * 60)
    lines.append("  RAPPORT QUOTIDIEN MTTV-FLP — MYCELIUM")
    lines.append(f"  {now}")
    lines.append("  Signature: 0x4D5454562D464C50")
    lines.append("=" * 60)
    lines.append("")

    # Status
    lines.append("─── ÉTAT DE L'INFRASTRUCTURE ───")
    lines.append(f"  API Gateway : {'✅ ACTIVE' if api_ok else '❌ INACTIVE'}")
    if api_ok and "chain" in api:
        for axe, status in api["chain"].items():
            s = status.get("status", "?")
            under = status.get("underlying", "")
            if s == "active":
                icon = "✅"
            elif s == "supervised":
                # Supervisé (artefact présent) mais infrastructure peut être hors-ligne
                icon = "🟡" if under == "online" else "🟠"
            else:
                icon = "❌"
            suffix = f" [infra: {under}]" if under else ""
            lines.append(f"    {axe} : {icon} {s}{suffix}")
    lines.append("")

    # Résonance — clarification des deux métriques distinctes
    lines.append("─── RÉSONANCE (2 métriques distinctes) ───")
    if api_ok and "chain" in api:
        axe1 = api["chain"].get("axe_1_dashboard", {})
        lines.append(f"  • resonance_score (dashboard signaux) : {axe1.get('resonance_score', 'N/A')}")
        lines.append(f"    source: resonance_output/resonance_latest.json")
    mycelium_rho = ""
    try:
        import re as _re
        mm = _re.search(r"Resonance globale\s*:\s*(\S+)", mycelium_report)
        if mm:
            mycelium_rho = mm.group(1)
    except Exception:
        pass
    lines.append(f"  • resonance_globale (essaim phi) : {mycelium_rho or 'N/A'}")
    lines.append(f"    source: mycelium_output/mycelium_latest.json (rapport mycélium)")
    lines.append("")
    lines.append("  NB: le rapport mycélium affiche la résonance PHI de l'essaim ;")
    lines.append("      le dashboard calcule un SCORE de signaux (autre métrique).")
    lines.append("      Le fichier zoo-code/zoo-code/resonance_output/ est un doublon périmé (07-20), non utilisé.")
    lines.append("")

    # Processus
    lines.append("─── PROCESSUS ACTIFS ───")
    if procs:
        for p in procs:
            lines.append(f"  PID {p.get('pid', '?'):>6} | {p.get('mem_mb', '?'):>6} MB | {p.get('uptime_h', '?'):>5}h | {p.get('cmd', '?')}")
    else:
        lines.append("  Aucun processus MTTV détecté.")
    lines.append("")

    # Validation MPVR (P6 — boucle de feedback)
    lines.append("─── VALIDATION MPVR ───")
    lines.extend(get_validation_status())
    lines.append("")

    # Rapport mycélium
    lines.append("─── RAPPORT MYCELIUM ───")
    lines.append(mycelium_report)

    # Pied de page
    lines.append("")
    lines.append("=" * 60)
    lines.append("  Prochain rapport : automatique (tâche planifiée)")
    lines.append("  Pour vous désabonner : supprimer la tâche Windows")
    lines.append("=" * 60)

    corps_texte = "\n".join(lines)

    # Version HTML
    html_status = "✅ ACTIVE" if api_ok else "❌ INACTIVE"
    chain_html = ""
    if api_ok and "chain" in api:
        for axe, status in api["chain"].items():
            s = status.get("status", "?")
            under = status.get("underlying", "")
            if s == "active":
                icon = "✅"
            elif s == "supervised":
                icon = "🟢" if under == "online" else "🟠"
            else:
                icon = "❌"
            infra = f" <span style='color:#a5d6a7'>[infra: {under}]</span>" if under else ""
            chain_html += f"<tr><td>{axe}</td><td>{icon} {s}{infra}</td></tr>\n"

    procs_html = ""
    for p in procs:
        procs_html += f"<tr><td>{p.get('pid', '?')}</td><td>{p.get('mem_mb', '?')} MB</td><td>{p.get('uptime_h', '?')}h</td><td style='font-size:11px'>{p.get('cmd', '?')}</td></tr>\n"

    corps_html = f"""<html><body style="font-family:monospace;background:#0a0a0a;color:#c8e6c9;padding:20px">
<h2 style="color:#81c784">🧬 MTTV-FLP — Rapport Quotidien</h2>
<p style="color:#a5d6a7">{now}</p>
<hr style="border-color:#2e7d32">

<h3 style="color:#81c784">📊 Infrastructure</h3>
<table border="1" cellpadding="6" cellspacing="0" style="border-color:#2e7d32;color:#c8e6c9">
<tr><th>Endpoint</th><th>Statut</th></tr>
<tr><td>API Gateway (:8000)</td><td>{html_status}</td></tr>
{chain_html}
</table>

<h3 style="color:#81c784">⚙️ Processus</h3>
<table border="1" cellpadding="6" cellspacing="0" style="border-color:#2e7d32;color:#c8e6c9">
<tr><th>PID</th><th>RAM</th><th>Uptime</th><th>Commande</th></tr>
{procs_html if procs_html else "<tr><td colspan='4'>Aucun processus MTTV</td></tr>"}
</table>

<h3 style="color:#81c784">🍄 Rapport Mycélium</h3>
<pre style="background:#1b1b1b;padding:10px;border-left:3px solid #2e7d32;color:#c8e6c9;overflow-x:auto">{mycelium_report[:3000]}</pre>

<hr style="border-color:#2e7d32">
<p style="color:#558b2f;font-size:11px">sig:0x4D5454562D464C50 — Prochain rapport : automatique</p>
</body></html>"""

    return corps_texte, corps_html


def envoyer_email(sujet: str, corps_html: str, corps_texte: str, destinataire: str) -> bool:
    """Envoie l'email via SMTP Gmail."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = sujet
    msg["From"] = f"MTTV-FLP Mycelium <{SMTP_USER}>"
    msg["To"] = destinataire
    msg.attach(MIMEText(corps_texte, "plain", "utf-8"))
    msg.attach(MIMEText(corps_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        logger.info(f"Email envoyé à {destinataire}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Authentification SMTP échouée. Vérifier le mot de passe d'application Gmail.")
        return False
    except Exception as e:
        logger.error(f"Erreur envoi email: {e}")
        return False


def schedule_task():
    """Planifie la tâche quotidienne dans Windows Task Scheduler."""
    python_exe = sys.executable
    script_path = str(BASE_DIR / "envoyer_rapport.py")
    project_dir = str(PROJECT_ROOT)

    task_name = "MTTV-FLP Rapport Quotidien"
    xml_path = str(BASE_DIR / "mttv_rapport_task.xml")

    # Créer le XML de la tâche
    import xml.etree.ElementTree as ET
    from xml.dom import minidom

    task = ET.Element("Task", xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task")
    reg = ET.SubElement(task, "RegistrationInfo")
    ET.SubElement(reg, "Description").text = "Envoi quotidien du rapport MTTV-FLP par email"

    trig = ET.SubElement(task, "Triggers")
    cal = ET.SubElement(trig, "CalendarTrigger")
    ET.SubElement(cal, "StartBoundary").text = "2026-07-30T08:00:00"
    ET.SubElement(cal, "Enabled").text = "true"
    sched = ET.SubElement(cal, "ScheduleByDay")
    ET.SubElement(sched, "DaysInterval").text = "1"

    actions = ET.SubElement(task, "Actions")
    exec_action = ET.SubElement(actions, "Exec")
    ET.SubElement(exec_action, "Command").text = python_exe
    ET.SubElement(exec_action, "Arguments").text = f'"{script_path}" --html'
    ET.SubElement(exec_action, "WorkingDirectory").text = project_dir

    # Settings
    settings = ET.SubElement(task, "Settings")
    ET.SubElement(settings, "Enabled").text = "true"
    ET.SubElement(settings, "StartWhenAvailable").text = "true"
    ET.SubElement(settings, "RunOnlyIfNetworkAvailable").text = "true"

    # Écrire le XML
    rough = ET.tostring(task, encoding="utf-8")
    reparsed = minidom.parseString(rough)
    xml_content = reparsed.toprettyxml(indent="  ")
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    logger.info(f"XML de tâche créé: {xml_path}")

    # Importer via schtasks.exe
    cmd = [
        "schtasks.exe", "/Create", "/XML", str(xml_path),
        "/TN", task_name, "/F"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            logger.info(f"Tâche planifiée créée : {task_name}")
            logger.info("Le rapport sera envoyé automatiquement chaque jour à 08:00")
            return True
        else:
            logger.error(f"Erreur schtasks: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Erreur création tâche: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Envoi rapport Mycelium par email")
    parser.add_argument("--to", default=DEFAULT_TO, help="Destinataire email")
    parser.add_argument("--html", action="store_true", help="Rapport HTML enrichi")
    parser.add_argument("--schedule", action="store_true", help="Planifier la tâche quotidienne")
    args = parser.parse_args()

    if args.schedule:
        schedule_task()
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    sujet = f"[MTTV-FLP] Rapport Mycelium — {timestamp}"

    logger.info("Génération du rapport étendu...")
    corps_texte, corps_html = generer_rapport_etendu()

    if args.html:
        pass  # corps_html est déjà enrichi
    else:
        corps_html = f"""<html><body style="font-family:monospace;background:#0a0a0a;color:#c8e6c9;padding:20px">
<pre>{corps_texte}</pre>
</body></html>"""

    logger.info(f"Envoi de l'email à {args.to}...")
    succes = envoyer_email(sujet, corps_html, corps_texte, args.to)

    if succes:
        logger.info("Rapport envoyé avec succès.")
    else:
        logger.error("Échec de l'envoi.")
        sys.exit(1)


if __name__ == "__main__":
    main()
