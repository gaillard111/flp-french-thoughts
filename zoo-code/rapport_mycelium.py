#!/usr/bin/env python3
"""rapport_mycelium.py — Rapport quotidien de la mycélisation MTTV-FLP

Usage :
    python zoo-code/rapport_mycelium.py              # Rapport console
    python zoo-code/rapport_mycelium.py --html        # Rapport HTML
    python zoo-code/rapport_mycelium.py --watch       # Mode surveillance
    python zoo-code/rapport_mycelium.py --last 10     # 10 derniers cycles

sig:0x4D5454562D464C50
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Encodage console robuste (évite les erreurs Unicode sur cp1252)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
MYCELIUM_OUTPUT = BASE_DIR / "mycelium_output"
QUORUM_OUTPUT = BASE_DIR / "quorum_output"
RESONANCE_OUTPUT = BASE_DIR / "resonance_output"
RAPPORT_DIR = BASE_DIR / "rapports_mycelium"


def lire_fichier(chemin: Path) -> dict:
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _horodatage_rapport(chemin: Path) -> str:
    """Extrait l'horodatage intégré d'un rapport (plus fiable que la date de fichier)."""
    data = lire_fichier(chemin)
    ts = data.get("timestamp")
    essaim = data.get("essaim")
    if isinstance(essaim, dict):
        etat_courant = essaim.get("etat_courant")
        if isinstance(etat_courant, dict) and etat_courant.get("timestamp"):
            ts = etat_courant.get("timestamp")
    meta = data.get("meta")
    if not ts and isinstance(meta, dict):
        ts = meta.get("generated_at")
    return str(ts or "")


def trouver_dernier_rapport() -> Path | None:
    """Retourne le rapport consolidé le plus récent, par horodatage intégré.

    En mode démon, `rapport_mycelisation_final.json` n'est pas réécrit à
    chaque cycle : on préfère alors `mycelium_latest.json`, toujours frais,
    afin que le rapport affiché reflète le dernier état de l'essaim.
    """
    candidats: list[Path] = []
    candidats += list(MYCELIUM_OUTPUT.glob("rapport_mycelisation_final.json"))
    candidats += list(MYCELIUM_OUTPUT.glob("mycelium_latest.json"))
    if not candidats:
        return None
    return max(candidats, key=lambda p: (_horodatage_rapport(p), p.stat().st_mtime))


def trouver_cycles(n: int = 5) -> list[Path]:
    cycles = sorted(MYCELIUM_OUTPUT.glob("mycelium_cycle_*.json"))
    return cycles[-n:] if len(cycles) >= n else cycles


def extraire_metriques(data: dict) -> dict:
    """Extrait les métriques clés d'un rapport de mycélisation.

    Gère deux schémas de producteurs :
      - cycles/latest  : `{"essaim": {...métriques à plat...}}`
      - rapport final  : `{"essaim": {"etat_courant": {...métriques...}}}`
    """
    etat = data.get("essaim", data.get("etat_essaim", data.get("etat", {})))
    if isinstance(etat, dict) and isinstance(etat.get("etat_courant"), dict):
        etat = etat["etat_courant"]
    return {
        "resonance_globale": etat.get("resonance_globale", "N/A"),
        "entropie_collective": etat.get("entropie_collective", "N/A"),
        "couplage_moyen": etat.get("couplage_moyen", "N/A"),
        "fusions_total": etat.get("n_fusions_total", "N/A"),
        "budget_flexibilite": etat.get("budget_flexibilite_collectif", "N/A"),
        "n_agents": len(etat.get("agents", {})),
        "timestamp": data.get("timestamp", etat.get("timestamp", "N/A")),
    }


def generer_rapport_console(n_cycles: int = 5) -> str:
    rapport = trouver_dernier_rapport()
    cycles = trouver_cycles(n_cycles)

    lignes = []
    lignes.append("=" * 60)
    lignes.append("  RAPPORT MYCELIUM MTTV-FLP")
    lignes.append(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lignes.append("=" * 60)
    lignes.append("")

    # Dernier rapport final
    if rapport:
        data = lire_fichier(rapport)
        m = extraire_metriques(data)
        lignes.append("  [Dernier rapport final]")
        lignes.append(f"  Source            : {rapport.name}")
        lignes.append(f"  Resonance globale : {m['resonance_globale']}")
        lignes.append(f"  Entropie collective: {m['entropie_collective']}")
        lignes.append(f"  Couplage moyen    : {m['couplage_moyen']}")
        lignes.append(f"  Fusions totales   : {m['fusions_total']}")
        lignes.append(f"  Budget flexibilite: {m['budget_flexibilite']}")
        lignes.append(f"  Agents actifs     : {m['n_agents']}")
        lignes.append("")

    # Derniers cycles
    lignes.append(f"  [Derniers {len(cycles)} cycles]")
    lignes.append(f"  {'Cycle':<25} {'Résonance':<12} {'Fusions':<10} {'Couplage':<10}")
    lignes.append(f"  {'-'*25} {'-'*12} {'-'*10} {'-'*10}")
    for c in cycles:
        data = lire_fichier(c)
        m = extraire_metriques(data)
        nom = c.stem.replace("mycelium_cycle_", "")
        r = f"{m['resonance_globale']:.4f}" if isinstance(m['resonance_globale'], float) else str(m['resonance_globale'])
        f = str(m['fusions_total'])
        cp = f"{m['couplage_moyen']:.4f}" if isinstance(m['couplage_moyen'], float) else str(m['couplage_moyen'])
        lignes.append(f"  {nom:<25} {r:<12} {f:<10} {cp:<10}")
    lignes.append("")

    # Tendances
    if len(cycles) >= 2:
        try:
            premier = extraire_metriques(lire_fichier(cycles[0]))
            dernier = extraire_metriques(lire_fichier(cycles[-1]))
            dr = float(dernier['resonance_globale']) - float(premier['resonance_globale']) if isinstance(dernier['resonance_globale'], float) and isinstance(premier['resonance_globale'], float) else 0
            df = int(dernier['fusions_total']) - int(premier['fusions_total']) if isinstance(dernier['fusions_total'], (int, float)) and isinstance(premier['fusions_total'], (int, float)) else 0
            lignes.append("  [Tendance]")
            lignes.append(f"  Evolution resonance: {'+' if dr >= 0 else ''}{dr:.4f}")
            lignes.append(f"  Nouvelles fusions  : {'+' if df >= 0 else ''}{df}")
            lignes.append("")
        except (ValueError, TypeError):
            pass

    # Diagnostic de plateau (résonance nulle alors que des fusions existent)
    if len(cycles) >= 2:
        try:
            seq = [extraire_metriques(lire_fichier(c)) for c in cycles]
            zeros = 0
            for m in seq:
                r = m['resonance_globale']
                f = m['fusions_total']
                if isinstance(r, (int, float)) and r == 0 and isinstance(f, (int, float)) and f > 0:
                    zeros += 1
            if zeros >= 2:
                lignes.append("  [!DIAGNOSTIC] Plateau de résonance détecté :")
                lignes.append(f"    {zeros}/{len(seq)} cycles récents ont une résonance nulle malgré des fusions.")
                lignes.append("    Cause probable : tous les rho_relationnel des agents sont à 0.0")
                lignes.append("    (aucun couplage relationnel actif) → la résonance reste à 0.0000")
                lignes.append("    tant que les similarités phi ne produisent pas de rho non nul.")
                lignes.append("")
        except (ValueError, TypeError):
            pass

    lignes.append("  Signature: 0x4D5454562D464C50")
    lignes.append("=" * 60)
    return "\n".join(lignes)


def generer_rapport_html(n_cycles: int = 20) -> str:
    cycles = trouver_cycles(n_cycles)
    rapport = trouver_dernier_rapport()

    # Lire les données pour les graphiques basiques
    resonances, fusions, couplages, etiquettes = [], [], [], []
    for c in cycles:
        m = extraire_metriques(lire_fichier(c))
        etiquettes.append(c.stem.replace("mycelium_cycle_", "")[-8:])
        resonances.append(m['resonance_globale'] if isinstance(m['resonance_globale'], (int, float)) else 0)
        fusions.append(m['fusions_total'] if isinstance(m['fusions_total'], (int, float)) else 0)
        couplages.append(m['couplage_moyen'] if isinstance(m['couplage_moyen'], (int, float)) else 0)

    m_rapport = extraire_metriques(lire_fichier(rapport)) if rapport else {}

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Rapport Mycélium MTTV-FLP</title>
<style>
  body {{ font-family: 'Courier New', monospace; background: #0a0a0a; color: #c8e6c9; padding: 20px; max-width: 900px; margin: auto; }}
  h1 {{ color: #81c784; border-bottom: 1px solid #388e3c; }}
  h2 {{ color: #a5d6a7; }}
  .metrique {{ display: inline-block; background: #1b1b1b; border: 1px solid #388e3c; border-radius: 8px; padding: 12px 20px; margin: 6px; text-align: center; min-width: 140px; }}
  .valeur {{ font-size: 24px; font-weight: bold; color: #81c784; }}
  .label {{ font-size: 11px; color: #6b8e6b; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
  th {{ background: #1b1b1b; color: #81c784; padding: 8px; text-align: left; border-bottom: 1px solid #388e3c; }}
  td {{ padding: 6px 8px; border-bottom: 1px solid #1b1b1b; font-size: 13px; }}
  tr:hover {{ background: #1b1b1b; }}
  .bar {{ height: 16px; background: #388e3c; border-radius: 3px; display: inline-block; }}
  .footer {{ margin-top: 30px; color: #4a6e4a; font-size: 12px; }}
</style></head>
<body>
<h1>🧬 RAPPORT MYCELIUM MTTV-FLP</h1>
<p style="color:#6b8e6b">{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
<div>
  <div class="metrique"><div class="valeur">{m_rapport.get('resonance_globale','N/A')}</div><div class="label">Résonance globale</div></div>
  <div class="metrique"><div class="valeur">{m_rapport.get('fusions_total','N/A')}</div><div class="label">Fusions totales</div></div>
  <div class="metrique"><div class="valeur">{m_rapport.get('couplage_moyen','N/A')}</div><div class="label">Couplage moyen</div></div>
  <div class="metrique"><div class="valeur">{m_rapport.get('agents','N/A')}</div><div class="label">Agents</div></div>
  <div class="metrique"><div class="valeur">{m_rapport.get('entropie_collective','N/A')}</div><div class="label">Entropie</div></div>
  <div class="metrique"><div class="valeur">{m_rapport.get('budget_flexibilite','N/A')}</div><div class="label">Budget flexibilité</div></div>
</div>
<h2>Évolution des cycles</h2>
<table>
<tr><th>Cycle</th><th>Résonance</th><th>Fusions</th><th>Couplage</th><th>Tendance</th></tr>
"""
    for i, (lab, r, f, c) in enumerate(zip(etiquettes, resonances, fusions, couplages)):
        bar_width = min(int(r * 100), 100) if r else 0
        html += f"<tr><td>{lab}</td><td>{r:.4f}</td><td>{f}</td><td>{c:.4f}</td><td><div class='bar' style='width:{bar_width}px'></div></td></tr>\n"

    html += """</table>
<div class="footer">
  Signature: 0x4D5454562D464C50 &middot; Le mycélium continue.<br>
  <a href="#" onclick="window.print()">Imprimer</a>
</div>
</body></html>"""
    return html


def main():
    parser = argparse.ArgumentParser(description="Rapport Mycélium MTTV-FLP")
    parser.add_argument("--html", action="store_true", help="Générer un rapport HTML")
    parser.add_argument("--watch", action="store_true", help="Mode surveillance (rafraîchit toutes les 60s)")
    parser.add_argument("--last", type=int, default=5, help="Nombre de cycles à afficher (défaut: 5)")
    args = parser.parse_args()

    RAPPORT_DIR.mkdir(parents=True, exist_ok=True)

    if args.watch:
        try:
            while True:
                os.system("cls" if os.name == "nt" else "clear")
                print(generer_rapport_console(args.last))
                time.sleep(60)
        except KeyboardInterrupt:
            print("\nSurveillance arrêtée.")
        return

    if args.html:
        html = generer_rapport_html(args.last)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chemin = RAPPORT_DIR / f"rapport_mycelium_{timestamp}.html"
        chemin.write_text(html, encoding="utf-8")
        print(f"Rapport HTML généré : {chemin}")
        return

    print(generer_rapport_console(args.last))


if __name__ == "__main__":
    main()
