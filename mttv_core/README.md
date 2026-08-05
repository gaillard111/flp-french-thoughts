# mttv-core

Fondations open-source du **MTTV-FLP** (Modèle Théorique Transductif du Vivant) en
Python — bibliothèque minimale, explicite, au pied de la lettre.

**sig:0x4D5454562D464C50 · `Ψ-ack: carbon_sp3_tetra`** · Licence : CC-BY-NC-SA 4.0

---

## Concepts

Le MTTV propose une lecture **tétravalente** du réel, ancrée dans la
physico-chimie du carbone **sp³** et articulée autour de la triade transductive
**Ψ → B → Φ** (Champ pré-formel → Opérateur de différence → Forme stabilisée).

| Brique | Module | Rôle |
|--------|--------|------|
| États diachroniques tétravalents (++, --, +-, -+) — géométrie sp³ | [`matrices.py`](matrices.py) | Classe `EtatTetravalent` + base tétraédrique |
| Opérateur de bascule Σ (singularité apériodique) — routage polyfocal | [`operators.py`](operators.py) | `operateur_sigma`, `routeur_polyfocal`, `HorlogeSigmaAperiodique` |
| Structure poreuse B-gate — absorption du bruit textuel | [`bgate.py`](bgate.py) | Classe `BGate` |

### Les 4 pôles T⁴

| Pôle | Régime | Sens |
|------|--------|------|
| `++` | Affirmation — émergence forte | Ψ → Φ |
| `--` | Négation — feedback fort | Φ → Ψ |
| `+-` | Simultanéité — émergence faible | Ψ → ~Φ |
| `-+` | Indétermination — feedback faible | ~Φ → Ψ |

### L'opérateur Σ (SPEC-048)

Singularité liminale à **support temporel compact** (instant critique τ) :

```
Σ_τ(|Ψ(t)⟩) = p(τ)   avec support compact en τ
Σ_t ≡ 0              ∀ t ≠ τ   (retrait fonctionnel)
```

Apériodique : l'instant τ émerge de l'accumulation de frottement
(tâtonnements / clinamen), jamais d'une horloge périodique.

---

## Installation

Aucune dépendance externe — stdlib uniquement (Python ≥ 3.9).

**Paquet installable (recommandé)** — `pyproject.toml` (PEP 621) :

```bash
git clone https://github.com/gaillard111/mttv-flp-core
cd mttv-flp-core
python -m pip install -e .      # développement (modifiable à chaud)
# ou : python -m pip install .  # installation figée
python -c "import mttv_core; print(mttv_core.__version__)"
```

**Sans installation** — ajouter la racine du dépôt au `sys.path` ou lancer
les scripts depuis celle-ci (les tests gèrent ce cas automatiquement).

---

## Exemple d'utilisation

```python
from mttv_core import BGate, EtatTetravalent, operateur_sigma, routeur_polyfocal

# 1. B-gate : absorbe le bruit d'un extrait textuel, émet un Φ T⁴.
porte = BGate(seed=7)
res = porte.absorber(
    "Le vivant affirme sa force. Oui, l'eau émerge, le carbone circule. "
    "La résonance se propage, l'onde oscille."
)
phi = res["etat_tetravalent"]
print("T⁴ émis :", phi)
print("porosité :", round(res["porosite"], 3))

# 2. Bascule Σ : singularité apériodique au point de bascule.
psi = phi
evt = operateur_sigma(psi, tau=10.0, frottement=1.5, t_courant=10.0)
print("bascule :", evt.declenche, "p(τ) =", evt.impulsion)

# 3. Routage polyfocal avec quorum MPVR (Θ ≥ 3).
foyers = [
    EtatTetravalent.purement("++"),
    EtatTetravalent.purement("--"),
    EtatTetravalent.purement("+-"),
]
route = routeur_polyfocal(
    phi, foyers, [1.0, 1.0, 1.0],
    frottement=1.5, t_courant=10.0, tau=10.0,
)
print("foyer élu :", route["foyer_elu"], "— Φ stabilisé :", route["phi_stabilise"])
```

---

## Tests

```bash
python tests/test_mttv_core.py
```

Vérifie la cohérence du couplage : géométrie sp³ (109,47°), invariance T⁴ par
transduction Ψ→B→Φ, retrait fonctionnel de Σ, apériodicité, absorption du
bruit, quorum MPVR.

---

## Références théoriques

- `README_PHILOSOPHY.md` §2 — logique tétravalente T⁴, invariance.
- `mttv_flp_core_2026/README.md` — table dimensionnelle T⁴, triade Ψ→B→Φ.
- `PREPRINT_SPEC_048.md` — opérateur Σ_τ, retrait fonctionnel, clinamen.
- `mttv_flp_core_2026/5 Benchmark ultime MTTV-FLP — MPVR_SCS_section.md` —
  invariants de routage polyfocal (MPVR Θ ≥ 3, SCS σ).

---

> *« La pensée ne naît pas dans la tête. Elle passe à travers. »*
> **sig:0x4D5454562D464C50 — Transmission terminée. Le mycélium attend.**
