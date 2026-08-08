#!/usr/bin/env python3
"""Test C6 — Non-homogénéisation de l'essaim.

Vérifie que, sur un essaim frais (état non homogénéisé) avec la respiration
C7 active et la contrainte environnementale réelle C5 :
1. L'entropie collective reste SOUS le maximum théorique
   (H_max = log(n_grille²·(n_grille²−1)) ≈ 6.3969 pour grille 5×5) après N cycles.
2. Le couplage moyen ne s'écrase PAS à 1.0 (diversité préservée entre agents).
3. La respiration C7 se déclenche bien (n_respirations > 0).
4. La contrainte environnementale réelle C5 produit un champ spatial cohérent
   (dérivé des Φ, pas un simple bruit indépendant).

Le but : empêcher la régression vers l'homogénéisation totale observée en
production (entropie = max théorique, couplage = 1.0) — voir JOURNAL 3bis/2septies.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from essaim_tetravalent import EssaimTetravalent  # noqa: E402


def entropie_max_grille(n_grille: int) -> float:
    """Maximum théorique de l'entropie structurelle de Φ pour une grille."""
    n_vecteurs = n_grille * n_grille
    return math.log(n_vecteurs * (n_vecteurs - 1))


def test_non_homogeneite():
    N_CYCLES = 30
    GRILLE = 5
    H_MAX = entropie_max_grille(GRILLE)

    essaim = EssaimTetravalent(
        n_agents=4,
        n_grille=GRILLE,
        dim_phi=4,
        seed=7,
        respiration_intervalle=4,   # respiration C7 active
        respiration_dose=0.10,
    )

    # 1. La respiration est configurée
    assert essaim.respiration_intervalle > 0, "Respiration C7 doit être active"
    assert essaim.respiration_dose >= 0.05, "Dose C7 renforcée attendue"

    # 2. La contrainte réelle C5 produit un champ spatial cohérent
    champ = essaim.construire_contrainte_reelle()
    assert champ.shape == (GRILLE, GRILLE), "Champ C5 doit être (n_grille, n_grille)"
    assert champ.min() >= 0.0 and champ.max() <= 1.0, "Champ C5 dans [0,1]"
    # Le champ dérivé des Φ doit varier spatialement (pas constant) sur un essaim
    # frais avec des tenseurs initialisés aléatoirement.
    assert np.std(champ) > 1e-6, "Champ C5 doit être spatialement non trivial"

    # 3. Évolution sur N cycles
    entropies = []
    couplages = []
    for _ in range(N_CYCLES):
        etat = essaim.evoluer()
        entropies.append(etat.entropie_collective)
        couplages.append(etat.couplage_moyen)

    # 4. La respiration s'est déclenchée
    assert essaim.n_respirations > 0, (
        f"Respiration non déclenchée (n_respirations={essaim.n_respirations})"
    )

    # 5. L'entropie reste SOUS le maximum théorique (avec marge)
    entropie_finale = float(entropies[-1])
    marge = H_MAX - entropie_finale
    print(f"Entropie finale : {entropie_finale:.4f} | max théorique : {H_MAX:.4f} "
          f"| marge : {marge:.4f} | resp : {essaim.n_respirations}")
    assert marge > 0.05, (
        f"Homogénéisation : entropie={entropie_finale:.4f} au max théorique "
        f"{H_MAX:.4f} (marge={marge:.4f})"
    )

    # 6. Le couplage moyen ne s'écrase pas à 1.0 en fin de parcours
    couplage_final = float(couplages[-1])
    print(f"Couplage final : {couplage_final:.4f}")
    assert couplage_final < 0.99, (
        f"Couplage écrasé à {couplage_final:.4f} ≈ 1.0 (homogénéisation)"
    )

    # 7. Au moins un couplage moyen intermédiaire est resté sous 0.5 (diversité)
    assert any(c < 0.5 for c in couplages), "Aucune diversité pendant l'évolution"

    print(f"\n[OK] C6 VALIDE : {N_CYCLES} cycles, entropie sous le max, "
          f"couplage diversifie, respiration C7 active ({essaim.n_respirations}).")


if __name__ == "__main__":
    test_non_homogeneite()
    print("TEST C6 OK")
