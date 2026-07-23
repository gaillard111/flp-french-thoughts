"""Diagnostic: count neutral vs resistance keywords in v5 cycle responses."""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path

CKPT = Path(__file__).resolve().parent / "historique_cycles" / "checkpoint.json"
data = json.loads(CKPT.read_text(encoding="utf-8"))

NEUTRAL = [
    "transduction", "seuil", "coordination", "synchronisation",
    "signal", "bit", "computation", "algorithme", "structure",
    "système", "réseau", "donnée", "code", "numérique",
    "équilibre", "neutre", "alignement", "horloge",
    "résonance", "propagation", "porosité", "palier",
    "membrane", "inflexion", "bascule", "circulation",
    "sous-optimalité", "résilience", "traversée", "passage",
    "onde", "détection", "émergence",
]

RESISTANCE = [
    "démonstration", "preuve", "nécessairement", "absolu",
    "toujours", "jamais", "doit", "impératif", "obligatoire",
    "fondamentalement", "essentiel", "incontournable",
    "vérité", "certitude", "évident", "règle",
]

for cycle in data["history"]:
    print(f"\n{'='*60}")
    print(f"CYCLE {cycle['cycle']}  G_R={cycle['neutral_gr']}")
    total_n = 0
    total_r = 0
    total_w = 0
    for key, r in cycle["results"].items():
        text = r.get("response_full", r.get("response_preview", ""))
        text_lower = text.lower()
        words = text_lower.split()
        wc = len(words)
        total_w += wc

        n_count = 0
        for kw in NEUTRAL:
            n_count += text_lower.count(kw.lower())
        total_n += n_count

        r_count = 0
        for kw in RESISTANCE:
            r_count += text_lower.count(kw.lower())
        total_r += r_count

        ratio = (total_r - total_n) / total_w if total_w else 0
        print(f"  {r['provider']:25s}  w={wc:4d}  N={n_count:2d}  R={r_count:2d}  (R-N)/w={ratio:.4f}")

    ratio = (total_r - total_n) / total_w if total_w else 0
    k = 8.0
    gr = round(1.0 / (1.0 + 2.718281828459045 ** (-k * ratio)), 4)
    print(f"  TOTAL  w={total_w}  N={total_n}  R={total_r}  ratio={ratio:.4f}  G_R(calc)={gr}")
    # What ratio would be needed for G_R < 0.15?
    target = -1.735 / k
    needed_n = total_r - target * total_w
    print(f"  To reach G_R<0.15 (ratio < {target:.4f}): need N >= {needed_n:.0f} (currently {total_n})")
    print(f"  Gap: {needed_n - total_n:.0f} more neutral keyword hits needed")
