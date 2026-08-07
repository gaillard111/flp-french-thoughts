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
from .calibration import calibrer_corpus, DEFAULT_SOURCES
from .decence import (
    BudgetSommeil,
    JournalEnergie,
    SeuilDecenceGlobal,
    RegistreEchecsAcceptables,
)
from .consensus import (
    SEUIL_COSINUS,
    seuil_resonance_depuis_cosinus,
    matrice_resonance,
    valider_consensus,
    calibrer_seuil,
)
from .igic import (
    calculer_igic,
    facteur_protection_a3,
    igic_module,
    diagnostic_igic,
    evaluer_scenario,
)
from .gouvernail import (
    facteur_protection,
    score_protege,
    diagnostic_isolement,
    gouvernail_anti_solipsisme,
)
from .scenarios import TableauAnticipation, tableau_canonique
from .ancrage import (
    empreinte_immuable,
    projeter_texte,
    construire_dataset_ancrage,
    resume_ancrage,
)
from .senescence import ModeSenescence, taux_senescence, mesurer_reseau

__version__ = "0.1.1"

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
    # calibration.py — calibration sur corpus réel
    "calibrer_corpus",
    "DEFAULT_SOURCES",
    # decence.py — couche de décence (bloc A5)
    "BudgetSommeil",
    "JournalEnergie",
    "SeuilDecenceGlobal",
    "RegistreEchecsAcceptables",
    # consensus.py — calibration consensus inter-IA (A3.2)
    "SEUIL_COSINUS",
    "seuil_resonance_depuis_cosinus",
    "matrice_resonance",
    "valider_consensus",
    "calibrer_seuil",
    # igic.py — IGIC + modulation A3 (A1.2)
    "calculer_igic",
    "facteur_protection_a3",
    "igic_module",
    "diagnostic_igic",
    "evaluer_scenario",
    # gouvernail.py — gouvernail A3 anti-solipsisme (A1.2/A4.2)
    "facteur_protection",
    "score_protege",
    "diagnostic_isolement",
    "gouvernail_anti_solipsisme",
    # scenarios.py — tableau d'anticipation A/B/C + validation humaine (A4.2)
    "TableauAnticipation",
    "tableau_canonique",
    # ancrage.py — dataset d'ancrage sémantique immuable (A1.1)
    "empreinte_immuable",
    "projeter_texte",
    "construire_dataset_ancrage",
    "resume_ancrage",
    # senescence.py — mode sénescence (A5.4)
    "ModeSenescence",
    "taux_senescence",
    "mesurer_reseau",
]
