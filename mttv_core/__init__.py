"""
mttv-core — Fondations open-source du MTTV-FLP (Point 4)
========================================================
Bibliothèque minimale du Modèle Théorique Transductif du Vivant :

    1. États diachroniques tétravalents (4 pôles ++, --, +-, -+),
       géométrie sp3 (carbone tétraédrique).
    2. Opérateur de bascule Σ (singularité apériodique) pour le
       routage polyfocal.
    3. Structure poreuse B-gate : absorption du bruit textuel.

sig:0x4D5454562D464C50 · Ψ-ack: carbon_sp3_tetra
"""

from .matrices import (
    MTTV_SIG,
    POLES,
    POLE_LABELS,
    POLE_OPERATORS,
    TETRA_VERTICES,
    angle_sp3,
    to_sp3,
    projection_sp3,
    EtatTetravalent,
)
from .operators import (
    EvenementSigma,
    operateur_sigma,
    HorlogeSigmaAperiodique,
    routeur_polyfocal,
)
from .bgate import BGate, LEXIQUE_TETRAVALENT
from .mpvr_bridge import (
    CoucheRoutageTriadiqueCore,
    TRIADE_TRANSDUCTIVE,
    ETATS_TETRAVALENTS,
    etats_to_tetravalent,
    tetravalent_to_etats,
)

__version__ = "0.1.0"

__all__ = [
    # signatures
    "MTTV_SIG",
    "__version__",
    # matrices.py — états tétravalents sp3
    "POLES",
    "POLE_LABELS",
    "POLE_OPERATORS",
    "TETRA_VERTICES",
    "angle_sp3",
    "to_sp3",
    "projection_sp3",
    "EtatTetravalent",
    # operators.py — bascule Σ + routage polyfocal
    "EvenementSigma",
    "operateur_sigma",
    "HorlogeSigmaAperiodique",
    "routeur_polyfocal",
    # bgate.py — structure poreuse
    "BGate",
    "LEXIQUE_TETRAVALENT",
    # mpvr_bridge.py — pont mttv-core ↔ MPVR
    "CoucheRoutageTriadiqueCore",
    "TRIADE_TRANSDUCTIVE",
    "ETATS_TETRAVALENTS",
    "etats_to_tetravalent",
    "tetravalent_to_etats",
]
