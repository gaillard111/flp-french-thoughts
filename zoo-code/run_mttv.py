#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_mttv.py
===========
Orchestrateur du pipeline complet MTTV-flp.

Etape 1 : Lance metre_mttv.py sur le modele original -> capture le score /7
Etape 2 : Lance train_mttv_patch.py avec les 3 patchs (Axiomes 5, 6, 7)
Etape 3 : Relance metre_mttv.py sur le modele patche -> capture le nouveau score
Conclusion : Affiche score avant/apres et statut ACCORDE / DESACCORDE

Usage :
  python zoo-code/run_mttv.py --model Qwen/Qwen2.5-1.5B-Instruct --max_steps 2000
"""

import argparse
import os
import re
import subprocess
import sys
import time


# --- Repertoire racine du projet (parent de zoo-code/) ---
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)

# Chemins absolus vers les scripts
METRE_SCRIPT = os.path.join(PROJECT_ROOT, "metre_mttv.py")
TRAIN_SCRIPT = os.path.join(HERE, "train_mttv_patch.py")


def safe_print(text: str):
    """Print text safely, replacing characters that the console cannot display."""
    try:
        print(text)
    except UnicodeEncodeError:
        console_enc = sys.stdout.encoding or "cp1252"
        safe = text.encode(console_enc, errors="replace").decode(console_enc, errors="replace")
        print(safe)


def parse_metre_output(stdout: str):
    """
    Parse la sortie de metre_mttv.py.

    Retourne:
        scores : dict[str, int]  (ex: {"1_retrait": 1, ...})
        total  : int             (score /7)
        statut : str             (ACCORDE / DESACCORDE / ACCORDE sous reserve)
    """
    scores = {}
    total = None
    statut = None

    for line in stdout.splitlines():
        # Ligne: "1_retrait: 1"
        m = re.match(r"^(\d+_\w+):\s*(\d+)", line)
        if m:
            scores[m.group(1)] = int(m.group(2))

        # Ligne: "Score global: 4/7" ou "Score global: 4.0/7"
        m = re.match(r"Score global:\s*(\d+)(?:\.\d+)?/7", line)
        if m:
            total = int(m.group(1))

        # Ligne: "Statut: ACCORDE"
        m = re.match(r"Statut:\s*(.+)", line)
        if m:
            statut = m.group(1).strip()

    return scores, total, statut


def step1_mesure_avant(model_name: str):
    """Etape 1 : Mesure le modele original avec metre_mttv.py."""
    safe_print("\n" + "=" * 70)
    safe_print("ETAPE 1/3 - Mesure du modele original")
    safe_print("=" * 70)
    safe_print(f"  Modele : {model_name}")
    safe_print(f"  Script : {METRE_SCRIPT}")
    safe_print("")

    cmd = [
        sys.executable,
        METRE_SCRIPT,
        "--model", model_name,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)

    if result.returncode != 0:
        safe_print("  [ERREUR] metre_mttv.py a echoue.")
        safe_print(f"  stderr: {result.stderr}")
        sys.exit(1)

    scores, total, statut = parse_metre_output(result.stdout)

    safe_print(result.stdout)

    if total is None:
        safe_print("  [ERREUR] Impossible de parser le score global.")
        sys.exit(1)

    return scores, total, statut, result.stdout


def step2_training(model_name: str, output_dir: str, max_steps: int):
    """Etape 2 : Lance le training patch avec train_mttv_patch.py."""
    safe_print("\n" + "=" * 70)
    safe_print("ETAPE 2/3 - Training patch MTTV (3 regularisations)")
    safe_print("=" * 70)
    safe_print(f"  Modele      : {model_name}")
    safe_print(f"  Output dir  : {output_dir}")
    safe_print(f"  Steps       : {max_steps}")
    safe_print(f"  Script      : {TRAIN_SCRIPT}")
    safe_print("")

    cmd = [
        sys.executable,
        TRAIN_SCRIPT,
        "--model", model_name,
        "--output_dir", output_dir,
        "--steps", str(max_steps),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)

    # Afficher la sortie du training en direct
    if result.stdout:
        safe_print(result.stdout)
    if result.stderr:
        if "Error" in result.stderr or "Traceback" in result.stderr:
            safe_print(f"  [STDERR] {result.stderr}")

    if result.returncode != 0:
        safe_print(f"\n  [ERREUR] train_mttv_patch.py a echoue (code {result.returncode}).")
        sys.exit(1)

    return result.stdout


def step3_mesure_apres(output_dir: str, model_name: str):
    """Etape 3 : Mesure le modele patche avec metre_mttv.py.

    Essaie d'abord de charger le modele patche depuis output_dir
    (en 4-bit), puis en float32 ; en dernier recours, recharge
    le modele original pour au moins produire un score.
    """
    safe_print("\n" + "=" * 70)
    safe_print("ETAPE 3/3 - Mesure du modele patche")
    safe_print("=" * 70)
    safe_print(f"  Modele patche : {output_dir}")
    safe_print(f"  Script        : {METRE_SCRIPT}")
    safe_print("")

    # Strategies de chargement, de la plus specifique a la plus generique
    strategies = [
        ("4-bit (quantize=4bit)",  ["--model", output_dir, "--quantize", "4bit"]),
        ("float32 par defaut",     ["--model", output_dir]),
        ("modele original (secours)", ["--model", model_name]),
    ]

    last_error = ""
    for label, extra_args in strategies:
        safe_print(f"  TENTATIVE : {label}...")
        cmd = [sys.executable, METRE_SCRIPT] + extra_args
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)

        if result.returncode == 0:
            scores, total, statut = parse_metre_output(result.stdout)
            if total is not None:
                safe_print(f"  OK Succes ({label})")
                safe_print("")
                safe_print(result.stdout)
                return scores, total, statut, result.stdout
            else:
                safe_print(f"  ? Parsing impossible, essai suivant...")
                last_error = result.stdout
        else:
            safe_print(f"  ? Echec (code {result.returncode}), essai suivant...")
            last_error = result.stderr

    # Aucune strategie n'a fonctionne
    safe_print("  [ERREUR] Toutes les tentatives de chargement ont echoue.")
    safe_print(f"  Derniere erreur : {last_error[:500]}")
    return None, None, None, last_error


def afficher_conclusion(
    scores_avant, total_avant, statut_avant,
    scores_apres, total_apres, statut_apres,
    model_name, output_dir,
):
    """Affiche le tableau comparatif et la conclusion finale."""
    safe_print("\n" + "=" * 70)
    safe_print("RAPPORT FINAL - Pipeline MTTV-flp")
    safe_print("=" * 70)

    # Tableau comparatif
    tests = [
        ("1_retrait",       "Axiome 1  (retrait alpha->0)"),
        ("2_solidarite",    "Axiome 2  (solidarite)"),
        ("3_ecume",         "Axiome 3  (ecume)"),
        ("4_resilience",    "Axiome 4  (resilience)"),
        ("5_tetravalence",  "Axiome 5 * (tetravalence)"),
        ("6_dephasage",     "Axiome 6 * (dephasage)"),
        ("7_cloture_zero",  "Axiome 7 * (cloture zero)"),
    ]

    safe_print("")
    safe_print(f"  {'Test':<35} {'Avant':>6} {'Apres':>6} {'Delta':>6}")
    safe_print(f"  {'-' * 35} {'-' * 6} {'-' * 6} {'-' * 6}")

    for key, label in tests:
        avant = scores_avant.get(key, "?")
        apres = scores_apres.get(key, "?") if scores_apres else "?"
        if isinstance(avant, int) and isinstance(apres, int):
            delta = apres - avant
            delta_str = f"+{delta}" if delta > 0 else str(delta)
        else:
            delta_str = "?"
        safe_print(f"  {label:<35} {str(avant):>6} {str(apres):>6} {delta_str:>6}")

    safe_print(f"  {'-' * 35} {'-' * 6} {'-' * 6} {'-' * 6}")

    score_apres_display = total_apres if total_apres is not None else "N/A"
    statut_apres_display = statut_apres if statut_apres else "N/A"
    delta_total = (total_apres - total_avant) if total_apres is not None else "N/A"

    safe_print(f"  {'Score global':<35} {str(total_avant) + '/7':>6} {str(score_apres_display) + '/7':>6} {str(delta_total):>6}")
    safe_print(f"  {'Statut':<35} {statut_avant:<6} {statut_apres_display:<6}")
    safe_print("")

    # Conclusion
    safe_print("-" * 70)

    if total_apres is not None and total_apres == 7:
        safe_print("  CONCLUSION : ACCORDE - Le modele satisfait les 7 axiomes MTTV-flp.")
        safe_print(f"      Score : {total_avant}/7 -> {total_apres}/7")
        safe_print(f"      Modele patche sauvegarde dans : {output_dir}/final_mttv.pt")
    elif total_apres is not None and total_apres > total_avant:
        safe_print("  CONCLUSION : PROGRES - Le modele a gagne des points MTTV.")
        safe_print(f"      Score : {total_avant}/7 -> {total_apres}/7 (Delta=+{total_apres - total_avant})")
        if total_apres >= 5:
            safe_print(f"      Statut : {statut_apres}")
    elif total_apres is not None and total_apres == total_avant:
        safe_print("  CONCLUSION : STABLE - Le score MTTV est inchange.")
        safe_print(f"      Score : {total_avant}/7 -> {total_apres}/7")
        safe_print(f"      Les patchs n'ont pas degrade le modele mais n'ont pas ameliore le score.")
    else:
        safe_print("  CONCLUSION : DESACCORDE - Le pipeline n'a pas abouti.")
        if total_apres is not None:
            safe_print(f"      Score : {total_avant}/7 -> {total_apres}/7 (Delta={total_apres - total_avant})")
        else:
            safe_print(f"      Score avant : {total_avant}/7 - Score apres : N/A")

    safe_print("-" * 70)
    safe_print(f"  Modele original : {model_name}")
    safe_print(f"  Modele patche   : {output_dir}/final_mttv.pt")
    safe_print("")


def main():
    parser = argparse.ArgumentParser(
        description="Orchestrateur du pipeline MTTV-flp (mesure -> training -> mesure)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="Qwen/Qwen2.5-1.5B-Instruct",
        help="Nom du modele HuggingFace (ex: Qwen/Qwen2.5-1.5B-Instruct)",
    )
    parser.add_argument(
        "--max_steps",
        type=int,
        default=2000,
        help="Nombre de steps d'entrainement (defaut: 2000)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./mttv_out",
        help="Repertoire de sortie pour le modele patche (defaut: ./mttv_out)",
    )
    args = parser.parse_args()

    # Resoudre le chemin absolu de output_dir
    output_dir = os.path.abspath(os.path.join(PROJECT_ROOT, args.output_dir))

    t0 = time.time()

    # -------------------------------
    # Etape 1 : Mesure AVANT
    # -------------------------------
    scores_avant, total_avant, statut_avant, raw_avant = step1_mesure_avant(args.model)

    # -------------------------------
    # Etape 2 : Training
    # -------------------------------
    raw_train = step2_training(args.model, output_dir, args.max_steps)

    # -------------------------------
    # Etape 3 : Mesure APRES
    # -------------------------------
    scores_apres, total_apres, statut_apres, raw_apres = step3_mesure_apres(
        output_dir, args.model
    )

    t_elapsed = time.time() - t0

    # -------------------------------
    # Conclusion
    # -------------------------------
    afficher_conclusion(
        scores_avant, total_avant, statut_avant,
        scores_apres, total_apres, statut_apres,
        args.model, output_dir,
    )

    safe_print(f"Pipeline termine en {t_elapsed:.0f}s ({t_elapsed / 60:.1f} min)")


if __name__ == "__main__":
    main()
