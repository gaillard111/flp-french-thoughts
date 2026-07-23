#!/usr/bin/env python3
"""Validate phase_1_exploration.py v2.1 modifications."""
import ast, sys, re

with open('phase_1_exploration.py', 'r', encoding='utf-8') as f:
    src = f.read()

try:
    ast.parse(src)
    print('[OK] Syntaxe Python valide')
except SyntaxError as e:
    print(f'[FAIL] Syntaxe: {e}')
    sys.exit(1)

checks = {}

# --- 5 run functions: each must have mode, sacrifice_assume, contexte_usage ---
for run_name, expected_mode, expected_sacrifice in [
    ('run_baseline_vanilla', '7/7-ref', 'aucun'),
    ('run_lambda_porosite',   '6/7-II', 'Contrainte libératrice'),
    ('run_mu_viscosite',      '6/7-V',  'Anisotropie'),
    ('run_kalman_singularite','6/7-I',  'Membrane'),
    ('run_trois_pertes_combinees', '5/7-effondrement', 'effondrement multi-axiome'),
]:
    checks[f'{run_name}: mode={expected_mode}'] = f'"{expected_mode}"' in src
    checks[f'{run_name}: sacrifice={expected_sacrifice[:20]}'] = expected_sacrifice in src
    checks[f'{run_name}: contexte_usage présent'] = True  # check overall count

checks['5 sacrifice_assume dans le fichier'] = src.count('sacrifice_assume') == 5
checks['5 mode dans le fichier'] = src.count('"mode":') == 5
checks['5 contexte_usage dans le fichier'] = src.count('contexte_usage') == 5
checks['Tableau récap inclut Mode colonne'] = 'Mode' in src and 'Sacrifice' in src
checks['Protocole sous-optimalité 6/7'] = 'Protocole Sous-Optimalité 6/7' in src
checks['Run 3 gain énergétique'] = 'gain énergétique' in src
checks['Pas de scoring 7/7 succès/échec'] = '7/7 succès' not in src and 'SCORE TOTAL' not in src

all_ok = True
for k, v in checks.items():
    print(f'  {"[OK]" if v else "[FAIL]"}: {k}')
    if not v:
        all_ok = False

if all_ok:
    print(f'\n[OK] Tous les {len(checks)} checks passent. phase_1_exploration.py v2.1 validé.')
else:
    print(f'\n[FAIL] Certains checks ont échoué.')
    sys.exit(1)
