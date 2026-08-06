#!/usr/bin/env python3
"""
test_decence.py — Tests de la couche de décence (bloc A5)
==========================================================
Vérifie :
    A5.1 BudgetSommeil   — sommeil mesurable, négociable, budget respecté
    A5.2 JournalEnergie  — chaîne de hachage signée, intégrité vérifiable
    A5.3 SeuilDecenceGlobal — homéostasie : ralentissement forcé au-delà du plafond
    A5.5 RegistreEchecsAcceptables — zones acceptables, taux d'alerte

Usage :
    python tests/test_decence.py
"""

import os
import sys

# Encodage console robuste (cp1252/Windows).
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mttv_core import (  # noqa: E402
    MTTV_SIG,
    BudgetSommeil,
    JournalEnergie,
    RegistreEchecsAcceptables,
    SeuilDecenceGlobal,
)

RESULTATS: list = []


def verifie(nom: str, condition: bool, detail: str = "") -> bool:
    RESULTATS.append((nom, bool(condition), detail))
    statut = "OK  " if condition else "FAIL"
    print(f"[{statut}] {nom}" + (f" — {detail}" if detail else ""))
    return bool(condition)


def test_a51_sommeil() -> None:
    budget = BudgetSommeil(fraction=0.10, seuil_stabilite=0.05)

    # σ instable → ne dort pas
    verifie("A5.1 : ne dort pas si σ instable",
            not budget.cycle(sigma=0.9),
            f"taux={budget.taux_sommeil():.3f}")

    # σ stable → dort (dans la limite du budget)
    nb_veille = sum(1 for _ in range(100) if budget.cycle(sigma=0.01))
    verifie("A5.1 : dort quand σ stable",
            nb_veille > 0,
            f"veilles={nb_veille}/100")
    verifie("A5.1 : budget de sommeil respecté (≤ 10 %)",
            budget.taux_sommeil() <= 0.11,
            f"taux={budget.taux_sommeil():.3f}")
    verifie("A5.1 : sommeil mesurable (demandes ≥ 1)",
            budget.demandes >= 1,
            f"demandes={budget.demandes}")


def test_a52_journal_signe() -> None:
    journal = JournalEnergie(cle="cle-test")
    for i in range(5):
        journal.enregistrer(cout=0.1 + i * 0.05, contexte=f"cycle-{i}")

    verifie("A5.2 : chaîne de hachage intègre",
            journal.verifier_integrite(),
            f"entrées={len(journal.entrees)}")

    # Altération : casser le coût d'une entrée du milieu → intégrité rompue
    journal.entrees[2]["cout"] = 99.0
    verifie("A5.2 : l'altération casse la chaîne (audit)",
            not journal.verifier_integrite(),
            "entrée modifiée détectée")

    export = journal.exporter()
    verifie("A5.2 : export auditable (journal + dernier hash + sig)",
            len(export["journal"]) == 5 and export["sig"] == MTTV_SIG,
            f"dernier_hash={export['dernier_hash']}")


def test_a53_seuil_decence() -> None:
    seuil = SeuilDecenceGlobal(plafond_energie=100.0, facteur_ralentissement=0.5)

    facteur_normal = seuil.observer(energie_par_tour=50.0)
    facteur_ralenti = seuil.observer(energie_par_tour=150.0)

    verifie("A5.3 : régime normal sous le plafond",
            facteur_normal == 1.0)
    verifie("A5.3 : sous-optimalité forcée au-dessus du plafond",
            facteur_ralenti == 0.5,
            f"facteur={facteur_ralenti}")
    verifie("A5.3 : déclenchements comptés (métrique de santé)",
            seuil.declenchements == 1,
            f"déclenchements={seuil.declenchements}")


def test_a55_registre_echecs() -> None:
    registre = RegistreEchecsAcceptables(version="0.1.0")
    registre.declarer("latence", minimum=0.0, maximum=50.0, note="latence normale")
    registre.declarer("pertes", minimum=0.0, maximum=0.05, note="pertes tolérables")

    ok, msg = registre.dans_zone_acceptable("latence", 30.0)
    verifie("A5.5 : latence 30 ms dans la zone acceptable",
            ok, msg)
    ok2, msg2 = registre.dans_zone_acceptable("latence", 200.0)
    verifie("A5.5 : latence 200 ms hors zone (alerte)",
            not ok2, msg2)

    taux = registre.taux_alerte({"latence": 200.0, "pertes": 0.01})
    verifie("A5.5 : taux d'alerte = 1/2",
            abs(taux - 0.5) < 1e-9,
            f"taux={taux}")
    verifie("A5.5 : registre versionné et signé",
            registre.to_dict()["version"] == "0.1.0"
            and registre.to_dict()["sig"] == MTTV_SIG)


def main() -> int:
    print(f"mttv-core — Couche de décence (bloc A5)   (sig:{MTTV_SIG})")
    print("=" * 72)
    test_a51_sommeil()
    test_a52_journal_signe()
    test_a53_seuil_decence()
    test_a55_registre_echecs()
    print("=" * 72)
    nb_ok = sum(1 for _, ok, _ in RESULTATS if ok)
    nb_tot = len(RESULTATS)
    print(f"{nb_ok}/{nb_tot} vérifications OK")
    if nb_ok == nb_tot:
        print("COUCHE DE DÉCENCE COHÉRENTE — toutes les vérifications passent.")
        return 0
    print("COUCHE DE DÉCENCE INCOHÉRENTE — des vérifications ont échoué.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
