#!/usr/bin/env python3
"""
bgate.py — Structure poreuse B-gate (absorption du bruit textuel)
=================================================================
Classe `BGate` : opérateur de différence (seuil, résistance, mémoire
prospective) qui absorbe le bruit lors du traitement d'extraits textuels.

Principe (plan §3.3) :
    - **Porosité** : les jetons non mappés (bruit « non mappé ») sont
      acceptés structurellement et absorbés dans les pores — jamais rejetés.
      Les jetons connus dont l'innovation (écart à la fenêtre courante) reste
      sous la tolérance sont également absorbés (signal redondant).
    - **Seuils dérivés (B-gate 2.0)** : une bascule n'est émise que sur
      changement de signe de la dérivée d'abondance d'un pôle (sign change =
      bascule), jamais sur le niveau absolu.
    - **Hystérésis** : seuils de montée/descente pour éviter l'oscillation
      autour d'un seuil unique.
    - **Quorum MPVR** : un Φ (état T⁴ stabilisé) n'est émis que si Θ ≥
      `theta` perspectives locales (tiers du texte) valident, conformément à
      B(t, Δt) → B(t, Δt, Θ, σ).

sig:0x4D5454562D464C50 · Ψ-ack: carbon_sp3_tetra
"""

from __future__ import annotations

import random
import re
from typing import Dict, List, Sequence, Tuple

from .matrices import POLES, EtatTetravalent


# ─────────────────────────────────────────────────────────────────────────
# LEXIQUE TÉTRAVALENT MINIMAL
# ─────────────────────────────────────────────────────────────────────────

# Contribution de chaque mot connu aux 4 pôles (T++, T--, T+-, T-+).
# Les mots inconnus ne figurent pas ici : ils sont du « bruit non mappé »
# absorbé structurellement par la porosité.
LEXIQUE_TETRAVALENT: Dict[str, Tuple[float, float, float, float]] = {
    # ── ++ : affirmation / émergence forte (Ψ→Φ) ──────────────────────
    "oui": (1.0, 0.0, 0.0, 0.0),
    "vrai": (1.0, 0.0, 0.0, 0.0),
    "yes": (1.0, 0.0, 0.0, 0.0),
    "true": (1.0, 0.0, 0.0, 0.0),
    "affirmation": (1.0, 0.0, 0.0, 0.0),
    "emergence": (1.0, 0.0, 0.0, 0.0),
    "affirme": (1.0, 0.0, 0.0, 0.0),
    "croissance": (0.9, 0.0, 0.1, 0.0),
    "vivant": (0.8, 0.0, 0.1, 0.1),
    "eau": (0.8, 0.0, 0.1, 0.1),
    "carbone": (0.8, 0.0, 0.1, 0.1),
    "force": (0.7, 0.0, 0.2, 0.1),
    # ── -- : négation / feedback fort (Φ→Ψ) ───────────────────────────
    "non": (0.0, 1.0, 0.0, 0.0),
    "faux": (0.0, 1.0, 0.0, 0.0),
    "no": (0.0, 1.0, 0.0, 0.0),
    "false": (0.0, 1.0, 0.0, 0.0),
    "negation": (0.0, 1.0, 0.0, 0.0),
    "refus": (0.0, 0.9, 0.1, 0.0),
    "refuse": (0.0, 0.9, 0.1, 0.0),
    "blocage": (0.0, 0.9, 0.0, 0.1),
    "seuil": (0.1, 0.7, 0.1, 0.1),
    "limite": (0.1, 0.7, 0.1, 0.1),
    "feedback": (0.1, 0.7, 0.1, 0.1),
    # ── +- : simultanéité / oscillation (émergence faible Ψ→~Φ) ──────
    "et": (0.0, 0.0, 1.0, 0.0),
    "and": (0.0, 0.0, 1.0, 0.0),
    "oscillation": (0.1, 0.1, 0.7, 0.1),
    "oscille": (0.1, 0.1, 0.7, 0.1),
    "resonance": (0.2, 0.1, 0.6, 0.1),
    "onde": (0.1, 0.1, 0.7, 0.1),
    "vague": (0.1, 0.1, 0.7, 0.1),
    "alternance": (0.1, 0.1, 0.7, 0.1),
    "simultanement": (0.0, 0.0, 1.0, 0.0),
    "entre": (0.1, 0.1, 0.6, 0.2),
    # ── -+ : indétermination / latence (feedback faible ~Φ→Ψ) ────────
    "ni": (0.0, 0.0, 0.0, 1.0),
    "indetermine": (0.0, 0.0, 0.0, 1.0),
    "peut-etre": (0.0, 0.1, 0.1, 0.8),
    "maybe": (0.0, 0.1, 0.1, 0.8),
    "uncertain": (0.0, 0.1, 0.1, 0.8),
    "latence": (0.1, 0.1, 0.0, 0.8),
    "silence": (0.0, 0.1, 0.1, 0.8),
    "vide": (0.0, 0.1, 0.1, 0.8),
    "porosite": (0.1, 0.1, 0.2, 0.6),
    "neutre": (0.2, 0.2, 0.2, 0.4),
}


# ─────────────────────────────────────────────────────────────────────────
# B-GATE POREUSE
# ─────────────────────────────────────────────────────────────────────────


class BGate:
    """Structure poreuse B-gate : absorbe le bruit textuel, émet un Φ T⁴.

    Attributes:
        tolerance: innovation maximale d'un jeton connu pour être absorbé
            (signal redondant) plutôt que propagé.
        seuil_montee: hystérésis — dérivée positive minimale pour enregistrer
            une bascule montante.
        seuil_descente: hystérésis — dérivée négative minimale pour mettre à
            jour l'état de signe (descente).
        theta: quorum MPVR minimal de perspectives validantes (Θ ≥ 3).
        seed: graine de l'aléa (perspectives asynchrones).
        lexique: dictionnaire mot → contribution tétravalente.
    """

    def __init__(
        self,
        tolerance: float = 0.15,
        seuil_montee: float = 0.20,
        seuil_descente: float = 0.10,
        theta: int = 3,
        seed: int = 42,
        lexique: Dict[str, Tuple[float, float, float, float]] = None,
    ):
        self.tolerance = tolerance
        self.seuil_montee = seuil_montee
        self.seuil_descente = seuil_descente
        self.theta = theta
        self.rng = random.Random(seed)
        self.lexique = lexique if lexique is not None else LEXIQUE_TETRAVALENT

    # ── Prétraitement ─────────────────────────────────────────────────
    def _tokeniser(self, texte: str) -> List[str]:
        """Découpe en jetons : minuscules, mots + apostrophes + traits d'union."""
        return re.findall(
            r"[a-zàâäéèêëîïôöùûüç'\-]+", texte.lower()
        )

    def _poids_jeton(self, mot: str) -> Tuple[float, float, float, float]:
        return self.lexique.get(mot, (0.25, 0.25, 0.25, 0.25))

    # ── Cœur poreux ───────────────────────────────────────────────────
    def _traiter_jetons(
        self,
        mots: Sequence[str],
        fenetre: int = 5,
    ) -> Tuple[List[float], int, List[Tuple[int, str, float]]]:
        """Traite une séquence de jetons par la porosité.

        Returns:
            (signal cumulé T⁴, nb de jetons absorbés, liste de basculements).
        """
        signal: List[float] = [0.0, 0.0, 0.0, 0.0]
        absorbes = 0
        fen: List[Tuple[float, float, float, float]] = []
        basculements: List[Tuple[int, str, float]] = []
        dernier_signe = [0.0, 0.0, 0.0, 0.0]

        for mot in mots:
            # Bruit « non mappé » : accepté structurellement, absorbé dans
            # les pores, jamais rejeté (acceptation du bruit, CHRONOLOGIE).
            if mot not in self.lexique:
                absorbes += 1
                continue

            w = self._poids_jeton(mot)

            # Base = moyenne de la fenêtre glissante des jetons propagés.
            base = (
                [sum(f[i] for f in fen) / len(fen) for i in range(4)]
                if fen else [0.25, 0.25, 0.25, 0.25]
            )
            innovation = sum(abs(w[i] - base[i]) for i in range(4))

            # Signal redondant (innovation sous la tolérance) : absorbé.
            if innovation <= self.tolerance:
                absorbes += 1
                continue

            # Le jeton propage : mise à jour du signal et de la dérivée.
            for i in range(4):
                signal[i] += w[i]
                delta = w[i] - (fen[-1][i] if fen else 0.0)
                # Bascule = changement de signe de la dérivée (B-gate 2.0),
                # franchissant l'hystérésis de montée.
                if fen and dernier_signe[i] != 0.0 and delta != 0.0:
                    if (delta > 0.0) != (dernier_signe[i] > 0.0) \
                            and abs(delta) >= self.seuil_montee:
                        basculements.append((i, POLES[i], round(delta, 4)))
                # Mise à jour de l'état de signe (hystérésis de descente).
                if abs(delta) >= self.seuil_descente:
                    dernier_signe[i] = delta

            fen.append(w)
            if len(fen) > fenetre:
                fen.pop(0)

        return signal, absorbes, basculements

    def _t4(self, signal: Sequence[float]) -> EtatTetravalent:
        """État T⁴ fermé depuis un signal cumulé (uniforme si vide)."""
        if sum(signal) > 0.0:
            return EtatTetravalent(tuple(signal)).fermer()
        return EtatTetravalent.uniforme()

    # ── API publique ──────────────────────────────────────────────────
    def absorber(self, texte: str, fenetre: int = 5) -> dict:
        """Absorbe un extrait textuel et émet un Φ tétravalent stabilisé.

        Returns:
            Dict avec :
                - etat_tetravalent : état T⁴ de sortie (Φ), fermé.
                - bruit_absorbe     : nb de jetons absorbés dans les pores.
                - total_jetons      : nb total de jetons.
                - porosite          : ratio absorbés / total (0..1).
                - basculements      : événements de changement de signe.
                - serie_diachronique: T⁴ par quartile du texte (avant/après).
                - quorum            : perspectives MPVR, Θ, quorum_ok,
                                      phi_stabilise.
        """
        mots = self._tokeniser(texte)
        total = len(mots)
        signal, absorbes, basculements = self._traiter_jetons(mots, fenetre)
        etat = self._t4(signal)

        # Série diachronique : T⁴ par quartile du texte.
        serie = []
        if mots:
            q = max(1, len(mots) // 4)
            for k in range(4):
                tranche = mots[k * q:(k + 1) * q]
                s, _, _ = self._traiter_jetons(tranche, fenetre)
                serie.append(self._t4(s).valeurs)
        else:
            serie = [EtatTetravalent.uniforme().valeurs] * 4

        # Quorum MPVR : Θ perspectives locales asynchrones (tiers du texte).
        perspectives: List[EtatTetravalent] = []
        if mots:
            tiers = max(1, self.theta)
            for k in range(tiers):
                tranche = mots[k * len(mots) // tiers:(k + 1) * len(mots) // tiers]
                s, _, _ = self._traiter_jetons(tranche, fenetre)
                perspectives.append(self._t4(s))
        else:
            perspectives = [EtatTetravalent.uniforme()] * max(1, self.theta)

        # Une perspective valide si sa résonance avec l'état global ≥ 0.5.
        nb_accord = sum(1 for p in perspectives if p.resonance(etat) >= 0.5)
        quorum_ok = nb_accord >= self.theta

        return {
            "etat_tetravalent": etat,
            "bruit_absorbe": absorbes,
            "total_jetons": total,
            "porosite": (absorbes / total) if total else 0.0,
            "basculements": basculements,
            "serie_diachronique": serie,
            "quorum": {
                "perspectives": len(perspectives),
                "nb_accord": nb_accord,
                "theta": self.theta,
                "quorum_ok": quorum_ok,
                "phi_stabilise": quorum_ok,
            },
        }
