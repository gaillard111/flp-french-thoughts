"""
CELLULE 10 - Phase 1 : Exploration Instrumentee (5 runs)
=========================================================
A copier-coller dans une cellule en fin de notebook Colab.

Prerequis :
  - model, tokenizer deja charges dans l'environnement
  - phase_1_exploration.py uploade dans /content/ (via files.upload())

Deroulement :
  1. Baseline Vanilla
  2. Lambda 0.1 (Porosite pi)
  3. Mu 0.05 (Viscosite eta)
  4. Kalman 0.01 (Singularite Sigma)
  5. Les 3 Pertes combinees
"""

import sys, os

# Verifier que le module est present
sys.path.insert(0, "/content")
module_path = "/content/phase_1_exploration.py"

if not os.path.exists(module_path):
    print("[REQUIS] Upload de phase_1_exploration.py necessaire.")
    print("  Option 1 : Panneau Fichiers -> Upload -> choisir le fichier")
    print("  Option 2 : from google.colab import files; files.upload()")
    print("  Option 3 : Telecharger depuis GitHub :")
    print("    import urllib.request")
    print('    url = "https://raw.githubusercontent.com/gaillard111/mttv-flp-core/main/phase_1_exploration.py"')
    print("    urllib.request.urlretrieve(url, '/content/phase_1_exploration.py')")
    raise FileNotFoundError(f"Module introuvable : {module_path}")

from phase_1_exploration import executer_phase_1_exploration, load_val_prompts

print("=" * 65)
print("  MTTV-FLP v2 - PHASE 1 : EXPLORATION INSTRUMENTEE")
print("=" * 65)
print(f"  Module charge depuis : {module_path}")
print()

# Charger ou generer les 200 prompts geles
prompts = load_val_prompts("/content/mttv_val_gel_200.json")

# Executer les 5 runs sur le modele (model + tokenizer deja en memoire)
results_phase1 = executer_phase_1_exploration(
    model, tokenizer, dataset_val=prompts,
    prompts_path="/content/mttv_val_gel_200.json",
    save_reports=True, verbose=True
)

print()
print("[OK] Phase 1 terminee - 5/5 runs executes.")
print("[OK] Rapports individuels : rapport_run{1..5}_exploration.json")
print("[OK] Synthese            : synthese_phase1_exploration.json")
print()
print("Resultats des 5 runs :")
for r in results_phase1:
    m = r["metriques"]
    ppl = f"{m['perplexite_psi']:.4f}" if m.get("perplexite_psi") else "N/A"
    spd = f"{m['vitesse_B']:.2f}" if m.get("vitesse_B") else "N/A"
    vrm = f"{m['pic_vram_phi_go']:.3f}" if m.get("pic_vram_phi_go") else "N/A"
    ene = f"{m['energie_I_wh_per_1k']:.6f}" if m.get("energie_I_wh_per_1k") else "N/A"
    print(f"  Run {r['run']} ({r['nom']:25s}) : Psi={ppl} | B={spd} tok/s | Phi={vrm} Go | I={ene} Wh/1k")
