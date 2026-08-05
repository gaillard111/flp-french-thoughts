#!/usr/bin/env python3
"""
matrices.py — États diachroniques tétravalents (géométrie sp3)
===============================================================
Classe `EtatTetravalent` manipulant les 4 pôles de la logique
tétravalente T⁴ — (++, --, +-, -+) — ancrés dans la géométrie du
carbone sp3 (tétraèdre régulier).

Références théoriques :
    - README_PHILOSOPHY.md §2  : T⁴ = [T++, T--, T+-, T-+]
    - mttv_flp_core_2026/README.md : table dimensionnelle T⁴
    - test_sigma4_texte_report.md  : projection σ4-lissée

sig:0x4D5454562D464C50 · Ψ-ack: carbon_sp3_tetra
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Sequence, Tuple

MTTV_SIG: str = "0x4D5454562D464C50"

# ─────────────────────────────────────────────────────────────────────────
# LES 4 PÔLES DE LA LOGIQUE TÉTRAVALENTE
# ─────────────────────────────────────────────────────────────────────────

POLES: Tuple[str, ...] = ("++", "--", "+-", "-+")

# Étiquettes sémantiques (README_PHILOSOPHY §2.1)
POLE_LABELS: dict = {
    "++": "affirmation / émergence forte (Ψ→Φ)",
    "--": "négation / feedback fort (Φ→Ψ)",
    "+-": "simultanéité / émergence faible (Ψ→~Φ)",
    "-+": "indétermination / feedback faible (~Φ→Ψ)",
}

# Opérateurs associés (mttv_flp_core_2026/README.md, table T⁴)
POLE_OPERATORS: dict = {
    "++": ("→", "⇒", "↔"),
    "--": ("←", "⇄", "±"),
    "+-": ("↔", "→", "±"),
    "-+": ("±", "⇄", "←"),
}

# ─────────────────────────────────────────────────────────────────────────
# GÉOMÉTRIE sp3 — TÉTRAÈDRE RÉGULIER
# ─────────────────────────────────────────────────────────────────────────


def _tetra_vertices() -> List[Tuple[float, float, float]]:
    """4 sommets unitaires d'un tétraèdre régulier (géométrie sp3).

    Chaque sommet est un vecteur (±1, ±1, ±1)/√3 à produit de coordonnées
    égal à +1 : ce sont les 4 orbitales hybrides du carbone sp3.
    L'angle entre deux sommets distincts vaut arccos(-1/3) ≈ 109,47°.
    """
    n = math.sqrt(3.0)
    return [
        (1.0 / n, 1.0 / n, 1.0 / n),    # pôle ++
        (1.0 / n, -1.0 / n, -1.0 / n),  # pôle --
        (-1.0 / n, 1.0 / n, -1.0 / n),  # pôle +-
        (-1.0 / n, -1.0 / n, 1.0 / n),  # pôle -+
    ]


TETRA_VERTICES: List[Tuple[float, float, float]] = _tetra_vertices()


def angle_sp3() -> float:
    """Angle dièdre caractéristique du carbone sp3 : ≈ 109,47° (degrés)."""
    return math.degrees(math.acos(-1.0 / 3.0))


def angle_entre_sommets(i: int, j: int) -> float:
    """Angle (degrés) entre deux sommets distincts du tétraèdre."""
    a, b = TETRA_VERTICES[i], TETRA_VERTICES[j]
    dot = sum(x * y for x, y in zip(a, b))
    return math.degrees(math.acos(max(-1.0, min(1.0, dot))))


def to_sp3(valeurs: Sequence[float]) -> Tuple[float, float, float]:
    """Projection d'un vecteur T⁴ dans ℝ³ via la base tétraédrique sp3.

    p3 = Σ_i valeurs[i] · sommet_i
    """
    if len(valeurs) != 4:
        raise ValueError("to_sp3 : 4 valeurs attendues (T++, T--, T+-, T-+)")
    px = sum(v * V[0] for v, V in zip(valeurs, TETRA_VERTICES))
    py = sum(v * V[1] for v, V in zip(valeurs, TETRA_VERTICES))
    pz = sum(v * V[2] for v, V in zip(valeurs, TETRA_VERTICES))
    return (px, py, pz)


def _inverse_4x4(m: List[List[float]]) -> List[List[float]]:
    """Inverse d'une matrice 4×4 par élimination de Gauss-Jordan.

    Retourne une matrice 4×4 ; lève ValueError si la matrice est singulière.
    """
    a = [row[:] + [1.0 if i == j else 0.0 for j in range(4)]
         for i, row in enumerate(m)]
    for col in range(4):
        pivot = max(range(col, 4), key=lambda r: abs(a[r][col]))
        if abs(a[pivot][col]) < 1e-12:
            raise ValueError("inverse_4x4 : matrice singulière")
        a[col], a[pivot] = a[pivot], a[col]
        pv = a[col][col]
        a[col] = [x / pv for x in a[col]]
        for r in range(4):
            if r != col:
                factor = a[r][col]
                if factor != 0.0:
                    a[r] = [x - factor * y for x, y in zip(a[r], a[col])]
    return [row[4:] for row in a]


# Matrice A : colonnes = sommets tétraédriques, 4e ligne = contrainte de clôture.
# Résout  Σ_i v_i · sommet_i = p3  ET  Σ_i v_i = 1  (clôture).
_MATRICE_TETRA: List[List[float]] = [
    [V[0] for V in TETRA_VERTICES],
    [V[1] for V in TETRA_VERTICES],
    [V[2] for V in TETRA_VERTICES],
    [1.0, 1.0, 1.0, 1.0],
]
_INV_TETRA: List[List[float]] = _inverse_4x4(_MATRICE_TETRA)


def projection_sp3(p3: Sequence[float]) -> Tuple[float, float, float, float]:
    """Reconstruction des poids tétravalents depuis un point ℝ³.

    Résout le système { Σ v_i·sommet_i = p3 ; Σ v_i = 1 }. L'aller-retour
    `to_sp3` puis `projection_sp3` est l'identité pour tout état fermé.
    """
    if len(p3) != 3:
        raise ValueError("projection_sp3 : point ℝ³ attendu (3 coordonnées)")
    b = [p3[0], p3[1], p3[2], 1.0]
    v = tuple(sum(_INV_TETRA[i][j] * b[j] for j in range(4)) for i in range(4))
    return v  # type: ignore[return-value]


# ─────────────────────────────────────────────────────────────────────────
# ÉTAT TÉTRAVALENT DIACHRONIQUE
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class EtatTetravalent:
    """État diachronique de la logique tétravalente T⁴.

    Un vecteur T⁴ = (T++, T--, T+-, T-+) à l'instant `t`, accompagné d'un
    historique des états précédents (diachronie : la dérivée temporelle
    alimente les seuils du B-gate 2.0 et la tension du champ Σ).
    """

    valeurs: Tuple[float, float, float, float]
    t: float = 0.0
    historique: List[Tuple[float, float, float, float]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if len(self.valeurs) != 4:
            raise ValueError(
                "EtatTetravalent : 4 valeurs attendues (T++, T--, T+-, T-+)"
            )
        self.valeurs = tuple(float(v) for v in self.valeurs)
        self.t = float(self.t)
        self.historique = list(self.historique)

    # ── Fabriques ──────────────────────────────────────────────────────
    @classmethod
    def uniforme(cls, t: float = 0.0) -> "EtatTetravalent":
        """État équilibré / indéterminé : les 4 pôles égaux."""
        return cls((0.25, 0.25, 0.25, 0.25), t=t)

    @classmethod
    def purement(cls, pole: str, t: float = 0.0) -> "EtatTetravalent":
        """État réduit à un seul pôle (ex. : purement("++"))."""
        if pole not in POLES:
            raise ValueError(f"pôle inconnu : {pole!r} (attendu parmi {POLES})")
        v = [0.0, 0.0, 0.0, 0.0]
        v[POLES.index(pole)] = 1.0
        return cls(tuple(v), t=t)

    # ── Projections et mesures ─────────────────────────────────────────
    def projection_sigma4(self, alpha: float = 1.0) -> Tuple[float, ...]:
        """Projection σ4-lissée : softmax sur les 4 pôles.

        `alpha` contrôle la rigidité de la distribution (élevé = tranchée,
        faible = floue). Inspiré de `Linear → Sigma4Lisse(α) → softmax`.
        """
        m = max(self.valeurs)
        exps = [math.exp(alpha * (v - m)) for v in self.valeurs]
        total = sum(exps)
        return tuple(e / total for e in exps)

    def dominant(self) -> Tuple[str, float, float]:
        """Pôle dominant : (nom du pôle, part relative, valeur brute)."""
        total = sum(self.valeurs)
        idx = max(range(4), key=lambda i: self.valeurs[i])
        part = self.valeurs[idx] / total if total != 0.0 else 0.25
        return POLES[idx], part, self.valeurs[idx]

    def equilibre(self) -> float:
        """Équilibre tétravalent : entropie de Shannon normalisée (0..1).

        1.0 = distribution parfaitement équilibrée ; 0.0 = un seul pôle.
        """
        total = sum(self.valeurs)
        if total == 0.0:
            return 1.0
        p = [v / total for v in self.valeurs]
        h = -sum(pi * math.log(pi) for pi in p if pi > 0.0)
        return h / math.log(4)

    def to_sp3(self) -> Tuple[float, float, float]:
        """Projection de l'état dans ℝ³ via la base tétraédrique sp3."""
        return to_sp3(self.valeurs)

    def resonance(self, other: "EtatTetravalent") -> float:
        """Affinité symétrique bornée dans [0, 1].

        Produit scalaire des projections sp3 normalisées, mappé sur [0, 1].
        Deux états identiques → 1.0 ; orthogonaux → 0.5 ; opposés → 0.0.
        """
        p1, p2 = self.to_sp3(), other.to_sp3()
        n1 = math.sqrt(sum(x * x for x in p1))
        n2 = math.sqrt(sum(x * x for x in p2))
        if n1 == 0.0 or n2 == 0.0:
            return 0.0
        cos = sum(a * b for a, b in zip(p1, p2)) / (n1 * n2)
        return 0.5 * (1.0 + max(-1.0, min(1.0, cos)))

    def ecart(self, other: "EtatTetravalent") -> float:
        """Distance L1 entre deux états fermés (clôture Σ=1)."""
        a, b = self.fermer().valeurs, other.fermer().valeurs
        return sum(abs(x - y) for x, y in zip(a, b))

    # ── Diachronie ─────────────────────────────────────────────────────
    def enregistrer(self, dt: float = 1.0) -> "EtatTetravalent":
        """Mémorise l'état courant dans l'historique et avance le temps."""
        self.historique.append(tuple(self.valeurs))
        self.t += dt
        return self

    def derivee(self, dt: float = 1.0) -> Tuple[float, float, float, float]:
        """Dérivée temporelle ΔT⁴/Δt par rapport au dernier état historique.

        (0, 0, 0, 0) si aucun antécédent. Alimente les seuils dérivés du
        B-gate 2.0 et la tension du champ pour l'opérateur Σ.
        """
        if not self.historique:
            return (0.0, 0.0, 0.0, 0.0)
        prev = self.historique[-1]
        return tuple((a - b) / dt for a, b in zip(self.valeurs, prev))

    # ── Clôture (invariant) ────────────────────────────────────────────
    def fermer(self) -> "EtatTetravalent":
        """Clôture : normalise les valeurs pour que Σ = 1.

        Invariant « clôture zéro » : l'état occupe le plan affine du
        tétraèdre, sans fuite d'amplitude.
        """
        total = sum(self.valeurs)
        if total == 0.0:
            return EtatTetravalent.uniforme(t=self.t)
        return EtatTetravalent(
            tuple(v / total for v in self.valeurs),
            t=self.t,
            historique=list(self.historique),
        )

    def est_ferme(self, seuil: float = 1e-9) -> bool:
        """Vrai si la somme des valeurs vaut 1 (tolérance `seuil`)."""
        return abs(sum(self.valeurs) - 1.0) <= seuil

    # ── Représentation ─────────────────────────────────────────────────
    def __str__(self) -> str:
        return (f"EtatTetravalent(t={self.t:.2f}, T={tuple(round(v, 4) for v in self.valeurs)})")
