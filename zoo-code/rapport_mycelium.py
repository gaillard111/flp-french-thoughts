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
import math
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

    [M7] Agrége aussi les causes racines par agent : flexibilité moyenne
    (degrés de liberté), désaturations Tremor cumulées et cycles ρ bas.
    """
    etat = data.get("essaim", data.get("etat_essaim", data.get("etat", {})))
    if isinstance(etat, dict) and isinstance(etat.get("etat_courant"), dict):
        etat = etat["etat_courant"]
    agents = etat.get("agents", {}) if isinstance(etat, dict) else {}
    flex_values: list[float] = [
        float(a.get("taux_occupation_flexible") or 0.0)
        for a in agents.values() if isinstance(a, dict)
    ]
    desat_values: list[int] = [
        int(a.get("n_desatures_tremor") or 0)
        for a in agents.values() if isinstance(a, dict)
    ]
    # n_grille : présent dans meta du snapshot (essaim.meta.n_grille) ou à plat
    n_grille = None
    meta = data.get("meta") if isinstance(data, dict) else None
    if isinstance(meta, dict):
        n_grille = meta.get("n_grille")
    if n_grille is None and isinstance(etat, dict):
        n_grille = etat.get("n_grille")
    if n_grille is None and isinstance(data, dict):
        essaim_raw = data.get("essaim")
        if isinstance(essaim_raw, dict):
            n_grille = essaim_raw.get("n_grille")

    return {
        "resonance_globale": etat.get("resonance_globale", "N/A"),
        "n_grille": int(n_grille) if n_grille else 5,
        "entropie_collective": etat.get("entropie_collective", "N/A"),
        "couplage_moyen": etat.get("couplage_moyen", "N/A"),
        "fusions_total": etat.get("n_fusions_total", "N/A"),
        "budget_flexibilite": etat.get("budget_flexibilite_collectif", "N/A"),
        "tremor_moyen": etat.get("tremor_moyen", "N/A"),
        "mode_tremor": etat.get("mode_tremor", "N/A"),
        "n_spawns": etat.get("n_spawns", 0),
        "n_agents": len(agents),
        "cycles_resonance_basse": etat.get("cycles_resonance_basse", 0),
        "taux_occupation_flexible": (
            round(sum(flex_values) / len(flex_values), 4)
            if flex_values else 0.0
        ),
        "n_desatures_tremor": sum(desat_values) if desat_values else 0,
        "timestamp": data.get("timestamp", etat.get("timestamp", "N/A")),
    }


def diagnostiquer_homogeneisation(m: dict) -> dict:
    """[C4] Détecte l'homogénéisation de l'essaim.

    L'entropie structurelle de Φ atteint son maximum théorique
    (≈ log(n_grille²·(n_grille²−1)) ≈ 6.3969 pour une grille 5×5) quand TOUS
    les vecteurs Φ sont identiques (distribution de similarité uniforme).
    Combiné à un couplage moyen ≈ 1.0, c'est un signe d'HOMOGÉNÉISATION
    (perte de diversité) — et non de « diversité saine » comme l'ancien
    docstring le suggérait.

    Retourne un dict avec : niveau ("ok" | "attention" | "alerte"), message,
    entropie_max (théorique) et marge.
    """
    entropie = m.get("entropie_collective", "N/A")
    couplage = m.get("couplage_moyen", "N/A")
    n_grille = int(m.get("n_grille", 5) or 5)   # grille de l'essaim (5 par défaut)

    # Maximum théorique : N = n_grille² vecteurs Φ → distribution de similarité
    # uniforme sur N(N-1) paires → entropie max = log(N(N-1)).
    # Pour grille 5×5 : N=25 → log(25·24) = log(600) ≈ 6.3969.
    try:
        n_grille = max(2, int(n_grille))
        n_vecteurs: int = n_grille * n_grille
        entropie_max: float = float(
            math.log(n_vecteurs * (n_vecteurs - 1))
        )
    except Exception:
        entropie_max = 6.3969  # valeur de référence pour grille 5×5

    if not isinstance(entropie, (int, float)) or not isinstance(couplage, (int, float)):
        return {"niveau": "ok", "message": "", "entropie_max": round(entropie_max, 4), "marge": None}

    marge = entropie_max - entropie
    couplage_haut = couplage >= 0.98
    entropie_max_atteinte = marge <= 0.05

    if entropie_max_atteinte and couplage_haut:
        return {
            "niveau": "alerte",
            "message": (
                f"[C4] ALERTE HOMOGÉNÉISATION : entropie={entropie:.4f} ≈ max "
                f"théorique ({entropie_max:.4f}) ET couplage={couplage:.3f} ≈ 1.0. "
                "Tous les Φ sont alignés → perte de diversité (à ne pas lire "
                "comme une diversité saine)."
            ),
            "entropie_max": round(entropie_max, 4),
            "marge": round(marge, 4),
        }
    if entropie_max_atteinte:
        return {
            "niveau": "attention",
            "message": (
                f"[C4] Attention : entropie={entropie:.4f} au voisinage du max "
                f"théorique ({entropie_max:.4f}) — surveiller l'homogénéisation."
            ),
            "entropie_max": round(entropie_max, 4),
            "marge": round(marge, 4),
        }
    return {
        "niveau": "ok",
        "message": f"[C4] Diversité OK : entropie={entropie:.4f} sous le max "
                   f"({entropie_max:.4f}), marge={marge:.4f}.",
        "entropie_max": round(entropie_max, 4),
        "marge": round(marge, 4),
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
        lignes.append(f"  Tremor moyen      : {m['tremor_moyen']} "
                      f"({m['mode_tremor']})")
        lignes.append(f"  Auto-suture spawns: {m['n_spawns']}")
        lignes.append(f"  Agents actifs     : {m['n_agents']}")
        lignes.append(f"  Flexibilite moy.  : {m['taux_occupation_flexible']}")
        lignes.append(f"  Desat. tremor     : {m['n_desatures_tremor']}")
        lignes.append(f"  Cycles rho bas    : {m['cycles_resonance_basse']}")
        # [C4] Diagnostic d'homogénéisation (entropie au max théorique + couplage ~1)
        c4 = diagnostiquer_homogeneisation(m)
        lignes.append(f"  Entropie max th.  : {c4['entropie_max']}")
        if c4["niveau"] != "ok":
            lignes.append(f"  ⚠️ {c4['message']}")
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
            # [M7] Durée du plateau terminal : cycles consécutifs (en fin de
            # liste) à résonance nulle — mesure directe de la pétrification.
            try:
                seq_trend = [
                    extraire_metriques(lire_fichier(c)) for c in cycles
                ]
                plat: int = 0
                for m in reversed(seq_trend):
                    r = m['resonance_globale']
                    if isinstance(r, (int, float)) and r == 0:
                        plat += 1
                    else:
                        break
                if plat >= 1:
                    lignes.append(
                        f"  Plateau (rho=0)    : {plat} cycle(s) consecutif(s)"
                    )
            except (ValueError, TypeError):
                pass
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
                dernier_m = seq[-1]
                flex = dernier_m.get('taux_occupation_flexible', 'N/A')
                entro = dernier_m.get('entropie_collective', 'N/A')
                cyc = dernier_m.get('cycles_resonance_basse', 'N/A')
                rho_dernier = dernier_m.get('resonance_globale', 'N/A')
                budget = dernier_m.get('budget_flexibilite', 'N/A')
                lignes.append("  [!DIAGNOSTIC] Plateau de résonance détecté :")
                lignes.append(f"    {zeros}/{len(seq)} cycles récents ont une résonance nulle malgré des fusions.")
                lignes.append(f"    Flexibilité moyenne (degrés liberté) : {flex}")
                lignes.append(f"    Budget flexibilité collective        : {budget}")
                lignes.append(f"    Cycles consécutifs ρ bas            : {cyc}")
                lignes.append(f"    Entropie collective                 : {entro} (seuil spawn ≈ 6.0)")
                if isinstance(rho_dernier, (int, float)) and rho_dernier == 0:
                    # Distinguer les deux attracteurs de dormance :
                    #  - métabolique : budget épuisé à 0 + tout flexible → ρ=0 par construction
                    #  - rigide      : trop de nœuds rigides, trop peu de flexibilité
                    budget_ok = isinstance(budget, (int, float)) and budget <= 0.05
                    flex_ok = isinstance(flex, (int, float)) and flex >= 0.9
                    if budget_ok and flex_ok:
                        lignes.append("    [M7] ALERTE dormance MÉTABOLIQUE ACTIVE :")
                        lignes.append("      budget de flexibilité épuisé alors que TOUS les nœuds")
                        lignes.append("      sont flexibles → ρ = 0 par construction (plus aucun nœud")
                        lignes.append("      rigide pour régénérer le budget).")
                        lignes.append("      Correction intégrée : re-rigidification homéostatique (M7)")
                        lignes.append("      active automatiquement (plancher métabolique + 0.25 des")
                        lignes.append("      nœuds les plus centraux repassent en rigide).")
                    elif budget_ok:
                        lignes.append("    [M7] ALERTE dormance métabolique : budget épuisé (0.0)")
                        lignes.append("      mais flexibilité partielle — re-rigidification homéostatique")
                        lignes.append("      (M7) requise / active.")
                    else:
                        lignes.append("    [M7] ALERTE dormance RIGIDE :")
                        lignes.append("      injecter de la flexibilité (M1/M2) ou activer --auto-reseed")
                else:
                    lignes.append(f"    Résonance du dernier cycle : {rho_dernier} →")
                    lignes.append("      plateau historique, en cours de résolution")
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

    # [C4] Diagnostic d'homogénéisation pour le rapport HTML
    c4 = diagnostiquer_homogeneisation(m_rapport) if m_rapport else {
        "niveau": "ok", "message": "", "entropie_max": "N/A", "marge": None
    }
    c4_couleur = {
        "alerte": "#ff6b6b", "attention": "#ffb84d", "ok": "#81c784"
    }.get(c4["niveau"], "#81c784")
    c4_bandeau = (
        f'<div style="background:#1b1b1b;border:1px solid {c4_couleur};'
        f'border-radius:8px;padding:10px 16px;margin-top:12px;color:{c4_couleur};">'
        f'{c4["message"] if c4["message"] else "Diversité OK."}</div>'
    )

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
{c4_bandeau}
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
