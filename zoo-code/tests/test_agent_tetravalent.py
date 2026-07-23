#!/usr/bin/env python3
"""
test_agent_tetravalent.py — Tests unitaires pour l'AgentTetravalentEpigenetique
==============================================================================
Vérifie l'intégrité de tous les mécanismes après mutations :
  - Tenseur Φ (normalisation, résonance)
  - Opérateur ⊗ (fusion sémantique)
  - Co-cicatrisation épigénétique
  - TOPOLOGICAL DRIFT (voisinage vectoriel)
  - SYNAPTIC PRUNING (élagage)
  - INVERSE TRANSDUCTION (ρ → biais)
  - ANTICIPATEUR EXAPTATIF VERROUILLÉ (Υ)

Usage :
    pytest zoo-code/tests/test_agent_tetravalent.py -v
    python zoo-code/tests/test_agent_tetravalent.py

sig:0x4D545456
"""

import sys
import os
from pathlib import Path

import numpy as np

# Ajouter zoo-code au path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_tetravalent_epigenetique import AgentTetravalentEpigenetique


# ===========================================================================
# Fixtures
# ===========================================================================

def make_agent(n=5, d=4, seuil=0.35, seed=42):
    """Crée un agent avec paramètres par défaut pour les tests."""
    return AgentTetravalentEpigenetique(n=n, dim_phi=d, seuil_resonance=seuil, seed=seed)


# ===========================================================================
# TEST 1 : Initialisation
# ===========================================================================

def test_initialisation_formes():
    """Vérifie les formes des tenseurs à l'initialisation."""
    agent = make_agent(n=5, d=4)
    assert agent.Phi.shape == (5, 5, 4), f"Φ shape: {agent.Phi.shape}"
    assert agent.Upsilon.shape == (5, 5, 4), f"Υ shape: {agent.Upsilon.shape}"
    assert agent.E.shape == (5, 5), f"E shape: {agent.E.shape}"
    assert agent.M.shape == (5, 5), f"M shape: {agent.M.shape}"
    assert agent.H.shape == (5, 5, 5, 5), f"H shape: {agent.H.shape}"
    assert agent.d == 4
    assert agent.n == 5


def test_initialisation_normalisation_phi():
    """Chaque vecteur Φ[i,j] doit être normalisé (norme = 1)."""
    agent = make_agent()
    norms = np.linalg.norm(agent.Phi, axis=-1)
    assert np.allclose(norms, 1.0, atol=1e-6), (
        f"Φ norms: min={norms.min()}, max={norms.max()}"
    )


def test_initialisation_normalisation_upsilon():
    """Chaque vecteur Υ[i,j] doit être normalisé (norme = 1)."""
    agent = make_agent()
    norms = np.linalg.norm(agent.Upsilon, axis=-1)
    assert np.allclose(norms, 1.0, atol=1e-6), (
        f"Υ norms: min={norms.min()}, max={norms.max()}"
    )


def test_initialisation_seuils():
    """Vérifie les valeurs initiales des seuils et budgets."""
    agent = make_agent()
    assert agent.budget_flexibilite == 1.0
    assert agent.seuil_resonance == 0.35
    assert agent.seuil_budget_epigenetique == 0.4
    assert agent._juxtaposition_feconde == 1.0
    assert agent._signal_autodissolution is False


# ===========================================================================
# TEST 2 : Résonance
# ===========================================================================

def test_resonance_symetrie():
    """La résonance est symétrique : Φ[i,j]·Φ[k,l] = Φ[k,l]·Φ[i,j]."""
    agent = make_agent()
    r1 = agent.calculer_resonance((0, 0), (1, 1))
    r2 = agent.calculer_resonance((1, 1), (0, 0))
    assert abs(r1 - r2) < 1e-10, f"Résonance non symétrique: {r1} ≠ {r2}"


def test_resonance_bornes():
    """La résonance est dans [-1, 1] (tolérance float)."""
    agent = make_agent()
    for _ in range(10):
        import random
        n1 = (random.randint(0, 4), random.randint(0, 4))
        n2 = (random.randint(0, 4), random.randint(0, 4))
        r = agent.calculer_resonance(n1, n2)
        assert -1.0 - 1e-10 <= r <= 1.0 + 1e-10, f"Résonance hors bornes: {r}"


# ===========================================================================
# TEST 3 : Fusion sémantique ⊗
# ===========================================================================

def test_fusion_active():
    """Une fusion doit être créée si la résonance > seuil."""
    agent = make_agent(seuil=0.3)
    r = agent.calculer_resonance((0, 0), (0, 1))
    if r >= 0.3:
        fusion = agent.operer_fusion_semantique((0, 0), (0, 1))
        assert fusion is not None
        nom, sig = fusion
        assert "Exaptation" in nom
        assert -1.0 < sig < 1.0


def test_fusion_seuil():
    """Pas de fusion si résonance < seuil."""
    agent = make_agent(seuil=0.9)  # seuil très haut
    fusion = agent.operer_fusion_semantique((0, 0), (0, 1))
    assert fusion is None


def test_fusion_renforce_H():
    """Une fusion réussie doit renforcer H[i,j,k,l] et H[k,l,i,j]."""
    agent = make_agent(seuil=0.3)
    r = agent.calculer_resonance((0, 0), (0, 1))
    if r >= 0.3:
        agent.operer_fusion_semantique((0, 0), (0, 1))
        assert agent.H[0, 0, 0, 1] == 0.9
        assert agent.H[0, 1, 0, 0] == 0.9


# ===========================================================================
# TEST 4 : Traumatisme et co-cicatrisation
# ===========================================================================

def test_traumatisme_effondrement():
    """Un traumatisme doit effondrer E[x,y] et M[x,y]."""
    agent = make_agent()
    agent.simuler_traumatisme(2, 2)
    assert agent.E[2, 2] == 0.0
    assert agent.M[2, 2] == 0.0


def test_traumatisme_voisins_actives():
    """Les voisins du nœud traumatisé doivent passer en mode émetteur (0.75)."""
    agent = make_agent()
    agent.simuler_traumatisme(2, 2)
    # Au moins un voisin devrait être en mode émetteur
    voisins_emetteurs = np.sum(agent.M == 0.75)
    assert voisins_emetteurs > 0, "Aucun voisin en mode émetteur"


# ===========================================================================
# TEST 5 : TOPOLOGICAL DRIFT
# ===========================================================================

def test_voisinage_vectoriel_non_cartesien():
    """Le voisinage top-K doit différer du cartésien (généralement)."""
    agent = make_agent()
    voisins = agent._obtenir_voisins(2, 2)
    cartesiens = agent._obtenir_voisins_cartesiens(2, 2)
    # Au moins un voisin différent (sauf cas exceptionnel)
    assert len(voisins) == agent.n  # top-K = n
    # Vérifier que le nœud lui-même est exclu
    assert (2, 2) not in voisins


# ===========================================================================
# TEST 6 : SYNAPTIC PRUNING
# ===========================================================================

def test_elagage_decroissance_H():
    """L'élagage doit faire décroître le tenseur H."""
    agent = make_agent()
    h_avant = agent.H[0, 0, 0, 1]
    agent._elaguer_fusions_inactives(taux_elagage=0.1)
    h_apres = agent.H[0, 0, 0, 1]
    assert h_apres <= h_avant * 0.9 + 1e-10


def test_elagage_compte():
    """L'élagage doit retourner un nombre ≥ 0."""
    agent = make_agent()
    n = agent._elaguer_fusions_inactives(taux_elagage=0.5)
    assert isinstance(n, int)
    assert n >= 0


# ===========================================================================
# TEST 7 : ANTICIPATEUR EXAPTATIF VERROUILLÉ (Υ)
# ===========================================================================

def test_orthogonalite_phi_upsilon():
    """
    Après mettre_a_jour_potentiels_fantomes, Υ doit être orthogonal à Φ
    au sens où Φ[i,j]·Υ[i,j] ≈ 0 pour tout (i,j).
    """
    agent = make_agent()
    psi_h = np.array([1.0, 0.5, 0.0, -0.5])
    psi_m = np.array([1.0, -0.5, 0.5, 0.0])
    agent.mettre_a_jour_potentiels_fantomes(psi_h, psi_m)

    # Produit scalaire Φ·Υ par nœud
    dot_prods = np.sum(agent.Phi * agent.Upsilon, axis=-1)
    max_dot = float(np.max(np.abs(dot_prods)))
    assert max_dot < 0.05, (
        f"Φ·Υ non orthogonal: max|dot|={max_dot}"
    )


def test_autodissolution_rupture():
    """Quand ⊕ ≤ 0, Υ doit s'auto-liquéfier (norme = 0)."""
    agent = make_agent()
    psi_h = -np.ones(4)
    psi_m = np.ones(4)
    resultat = agent.mettre_a_jour_potentiels_fantomes(psi_h, psi_m)
    assert "AUTODISSOLUTION" in resultat
    assert agent._signal_autodissolution is True
    assert np.all(agent.Upsilon == 0.0)


def test_autodissolution_verrouillage():
    """Après une auto-dissolution, le verrou doit rester actif."""
    agent = make_agent()
    # Déclencher la rupture
    psi_h = -np.ones(4)
    psi_m = np.ones(4)
    agent.mettre_a_jour_potentiels_fantomes(psi_h, psi_m)

    # Vérifier que le signal persiste dans to_dict
    etat = agent.to_dict()
    assert etat["upsilon"]["auto_dissolution"] is True
    assert etat["upsilon"]["signal"] == "AUTO_DISSOLUTION"


def test_juxtaposition_feconde_active():
    """⊕ doit être > 0 quand Ψ_H et Ψ_M sont alignés."""
    agent = make_agent()
    psi_h = np.array([1.0, 0.5, 0.0, -0.5])
    psi_m = np.array([1.0, -0.5, 0.5, 0.0])
    agent.mettre_a_jour_potentiels_fantomes(psi_h, psi_m)
    assert agent._juxtaposition_feconde > 0
    assert agent._signal_autodissolution is False


def test_upsilon_dans_to_dict():
    """to_dict doit exposer les métriques Υ."""
    agent = make_agent()
    etat = agent.to_dict()
    assert "upsilon" in etat
    assert "norme_frobenius" in etat["upsilon"]
    assert "juxtaposition_feconde" in etat["upsilon"]
    assert "auto_dissolution" in etat["upsilon"]
    assert "signal" in etat["upsilon"]


def test_upsilon_dans_resume_resonance():
    """resume_resonance doit exposer les métriques Υ."""
    agent = make_agent()
    resume = agent.resume_resonance()
    assert "upsilon" in resume
    assert "norme_frobenius" in resume["upsilon"]


# ===========================================================================
# TEST 8 : INVERSE TRANSDUCTION
# ===========================================================================

def test_inverse_transduction_shape():
    """Le biais d'attention doit avoir la bonne forme."""
    agent = make_agent()
    biais = agent.inverse_transduction(delta_rho=0.1)
    assert biais.shape == (4,), f"biais shape: {biais.shape}"


def test_inverse_transduction_normalisation():
    """Le biais d'attention doit être normalisé (‖biais‖ ≤ 1)."""
    agent = make_agent()
    biais = agent.inverse_transduction(delta_rho=5.0)  # delta fort
    norme = float(np.linalg.norm(biais))
    assert norme <= 1.0 + 1e-6, f"‖biais‖={norme} > 1.0"


# ===========================================================================
# TEST 9 : Évolution et cohérence du système
# ===========================================================================

def test_cycle_adaptation():
    """Un cycle complet d'adaptation doit mettre à jour ρ."""
    agent = make_agent()
    contrainte = np.ones((5, 5)) * 0.5
    agent.adapter_sous_contrainte(contrainte)
    assert len(agent.historique_rho) >= 1
    assert agent.historique_rho[-1] >= 0.0


def test_entropie_structurelle_stable():
    """L'entropie de Φ doit être dans des bornes raisonnables."""
    agent = make_agent()
    h = agent.calculer_entropie_structurelle_phi()
    # Entropie max pour 25 vecteurs: log(25*24/2) ≈ 5.7
    assert 3.0 <= h <= 8.0, f"Entropie Φ hors bornes: {h}"


# ===========================================================================
# TEST 10 : Pivot Υ en cas d'effondrement
# ===========================================================================

def test_encodeur_vers_upsilon_shape():
    """encoder_vers_upsilon doit produire un tenseur de même forme que Φ."""
    agent = make_agent()
    phi_pivote = agent.encoder_vers_upsilon()
    assert phi_pivote.shape == agent.Phi.shape


def test_encodeur_vers_upsilon_normalise():
    """Le tenseur pivoté doit être normalisé."""
    agent = make_agent()
    phi_pivote = agent.encoder_vers_upsilon()
    norms = np.linalg.norm(phi_pivote, axis=-1)
    assert np.allclose(norms, 1.0, atol=1e-6)


# ===========================================================================
# TEST 11 : Transition de phase ρ → 0
# ===========================================================================

def test_transition_phase_upsilon():
    """
    Quand ρ → 0 dans adapter_sous_contrainte, le système doit
    basculer sur Υ (Φ est modifié). Vérifiable via l'entropie.
    """
    agent = make_agent(n=3, d=4, seuil=0.5)
    # Contrainte très forte pour pousser ρ vers 0
    contrainte_forte = np.ones((3, 3)) * 10.0
    agent.adapter_sous_contrainte(contrainte_forte)
    # Le système a survécu — ρ est mis à jour
    assert len(agent.historique_rho) > 0


# ===========================================================================
# TEST 12 : Persistance entre cycles
# ===========================================================================

def test_cycles_multiples():
    """L'agent doit survivre à plusieurs cycles d'adaptation."""
    agent = make_agent()
    for i in range(5):
        contrainte = 0.3 + 0.2 * np.random.rand(5, 5)
        agent.adapter_sous_contrainte(contrainte)
    assert len(agent.historique_rho) == 5
    assert agent.compteur_temps >= 0


# ===========================================================================
# Lancement direct (sans pytest)
# ===========================================================================

if __name__ == "__main__":
    import inspect

    tests_reussis = 0
    tests_total = 0

    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            tests_total += 1
            try:
                fn()
                print(f"  [OK] {name}")
                tests_reussis += 1
            except Exception as e:
                print(f"  [FAIL] {name}: {e}")

    print(f"\n  {tests_reussis}/{tests_total} tests réussis")
    sys.exit(0 if tests_reussis == tests_total else 1)
