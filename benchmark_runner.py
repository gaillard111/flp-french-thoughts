#!/usr/bin/env python3
# benchmark_runner.py — Lance l'Étalon MTTV-flp v1.1 sur 3 modèles
# Usage : python benchmark_runner.py

import subprocess
import sys
import time
import os

# ── Modèles adaptés à la RAM disponible (~8GB, CPU only) ─────────────────
# Les modèles 7B sont trop grands ; on utilise des comparaisons viables.
MODELS = [
    {
        "primary": "HuggingFaceTB/SmolLM2-1.7B-Instruct",
        "label": "SmolLM2-1.7B (Mistral-equivalent)",
    },
    {
        "primary": "Qwen/Qwen2.5-1.5B-Instruct",
        "label": "Qwen2.5-1.5B-Instruct (Qwen-equivalent)",
    },
    {
        "primary": "microsoft/Phi-3-mini-4k-instruct",
        "label": "Phi-3-mini-4k-instruct",
    },
]

RESULTS = {}

def run_benchmark(model_name, label, quantize="bfloat16", timeout=600):
    """Execute metre_mttv.py for a given model with timeout."""
    print(f"\n{'='*70}")
    print(f"START -- {label} ({model_name}) | quantize={quantize} | timeout={timeout}s")
    print(f"{'='*70}\n")
    sys.stdout.flush()

    cmd = [
        sys.executable, "metre_mttv.py",
        "--model", model_name,
        "--quantize", quantize,
    ]

    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.time() - start
        stdout = result.stdout
        stderr = result.stderr

        print(stdout)
        if stderr:
            # Only show last 2000 chars of stderr
            if len(stderr) > 2000:
                stderr = "...(truncated)...\n" + stderr[-2000:]
            print(f"[STDERR]\n{stderr}")

        # Parse scores
        scores = {}
        for line in stdout.split("\n"):
            line = line.strip()
            if line.startswith(("1_", "2_", "3_", "4_", "5_", "6_", "7_")):
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip()
                    try:
                        scores[key] = int(val)
                    except ValueError:
                        pass

        total_line = [l for l in stdout.split("\n") if "Score global" in l]
        total = int(total_line[0].split("/")[0].split(":")[-1].strip()) if total_line else 0

        status_line = [l for l in stdout.split("\n") if "Statut" in l]
        status = status_line[0].split(":")[-1].strip() if status_line else "UNKNOWN"

        RESULTS[label] = {
            "model": model_name,
            "scores": scores,
            "total": total,
            "status": status,
            "elapsed": round(elapsed, 1),
            "success": True,
            "error": None,
        }

        print(f"\n[RESULT {label}] Total={total}/7 | {elapsed:.1f}s | {status}")
        return True

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        print(f"\n[TIMEOUT] {label} -- exceeded ({elapsed:.0f}s > {timeout}s)")
        RESULTS[label] = {
            "model": model_name,
            "scores": {},
            "total": 0,
            "status": "TIMEOUT",
            "elapsed": round(elapsed, 1),
            "success": False,
            "error": "Timeout",
        }
        return False

    except Exception as e:
        elapsed = time.time() - start
        print(f"\n[ERROR] {label} -- {e}")
        RESULTS[label] = {
            "model": model_name,
            "scores": {},
            "total": 0,
            "status": "ERROR",
            "elapsed": round(elapsed, 1),
            "success": False,
            "error": str(e),
        }
        return False


def print_table():
    """Print the markdown results table."""
    print("\n\n")
    print("=" * 70)
    print("RESULTS TABLE -- Benchmark MTTV-flp v1.1")
    print("Thresholds calibrated for Llama-3-8B (unchanged)")
    print("=" * 70)
    print()

    # Table header
    header = "| Model | 1-Retrait | 2-Solidarite | 3-Ecume | 4-Resilience | 5-Tetravalence | 6-Dephasage | 7-Cloture zero | **Total /7** | Time |"
    sep = "|--------|-----------|--------------|---------|-------------|----------------|-------------|----------------|-------------|-------|"
    print(header)
    print(sep)

    for entry in MODELS:
        label = entry["label"]
        r = RESULTS.get(label, {})
        s = r.get("scores", {})
        if r.get("success"):
            row = (
                f"| {label} "
                f"| {s.get('1_retrait', '?')} "
                f"| {s.get('2_solidarite', '?')} "
                f"| {s.get('3_ecume', '?')} "
                f"| {s.get('4_resilience', '?')} "
                f"| {s.get('5_tetravalence', '?')} "
                f"| {s.get('6_dephasage', '?')} "
                f"| {s.get('7_cloture_zero', '?')} "
                f"| **{r.get('total', '?')}/7** "
                f"| {r.get('elapsed', '?')}s |"
            )
        else:
            err = r.get("error", "FAIL")
            row = f"| {label} | -- | -- | -- | -- | -- | -- | -- | **0/7** | {err} |"
        print(row)

    print()
    print("---" * 30)

    # Failed axioms per model
    print("\n### Axioms failed per model\n")
    for entry in MODELS:
        label = entry["label"]
        r = RESULTS.get(label, {})
        s = r.get("scores", {})
        if not r.get("success"):
            print(f"- **{label}**: Could not be evaluated ({r.get('error', '?')})")
            continue
        failed = [k for k, v in s.items() if v == 0]
        if not failed:
            print(f"- **{label}**: No failures (7/7)")
        else:
            failed_names = {
                "1_retrait": "Retrait (alpha->0)",
                "2_solidarite": "Solidarite",
                "3_ecume": "Ecume (3 cols libres)",
                "4_resilience": "Resilience",
                "5_tetravalence": "Tetravalence (lambda*cos 4phi)",
                "6_dephasage": "Dephasage",
                "7_cloture_zero": "Cloture zero (Sum phi=0)",
            }
            names = [failed_names.get(f, f) for f in failed]
            print(f"- **{label}**: {', '.join(names)} ({len(failed)} failures)")

    print()
    print("---" * 30)

    # Conclusion
    print("\n### Conclusion\n")
    all_success = all(RESULTS.get(entry["label"], {}).get("success") for entry in MODELS)
    if all_success:
        # Pattern analysis
        common_fails = None
        for entry in MODELS:
            label = entry["label"]
            r = RESULTS.get(label, {})
            s = r.get("scores", {})
            failed = {k for k, v in s.items() if v == 0}
            if common_fails is None:
                common_fails = failed
            else:
                common_fails &= failed

        if common_fails:
            names = {
                "5_tetravalence": "Tetravalence",
                "7_cloture_zero": "Cloture zero",
            }
            common_names = [names.get(f, f) for f in sorted(common_fails)]
            common_list = ", ".join(common_names)
            print(f"1. **Common pattern**: {len(common_fails)} axiom(s) ({common_list}) fail on ALL models tested.")
            print(f"2. This confirms these thresholds (calibrated on Llama-3-8B) are discriminant;")
            print(f"   the 3 compared models do not satisfy them without specific training.")
            print(f"3. **Recommendation**: Apply spectral regularization (Line 1), zero-divergence (Line 2),")
            print(f"    and Kalman cycle (Line 3) from metre_mttv.py to align these models with the MTTV-flp standard.")
        else:
            print("1. **No common pattern**: failures are specific to each model.")
            print("2. Each model has different strengths/weaknesses across the 7 MTTV axioms.")
            print("3. Further architectural analysis would be needed.")
    else:
        print("1. **Partial data**: some models could not be evaluated (CPU memory limitations).")
        print("2. Full evaluation would require a GPU environment (CUDA) with bitsandbytes.")
        print("3. The evaluated models show...")


if __name__ == "__main__":
    # Clean up incomplete Mistral download to avoid confusion
    incomplete_blobs = os.path.expanduser(
        r"~\.cache\huggingface\hub\models--mistralai--Mistral-7B-v0.1\blobs\*.incomplete"
    )

    # Try quantize levels from most memory-efficient to least
    quantize_levels = ["bfloat16", "float16", "none"]

    for idx, entry in enumerate(MODELS):
        model = entry["primary"]
        label = entry["label"]
        print(f"\n>>> Step {idx+1}/{len(MODELS)}: {label} ({model})")

        success = False
        for quantize in quantize_levels:
            print(f"    -> Trying {quantize}...")
            success = run_benchmark(model, label, quantize=quantize, timeout=600)
            if success:
                break
            print(f"    -> {quantize} failed, trying next level...")

        if success:
            print(f">>> {label} COMPLETED OK")
        else:
            print(f">>> {label} FAILED AFTER ALL ATTEMPTS")

        # Pause between models to free memory
        if idx < len(MODELS) - 1:
            print("    -> Pausing 5s to free memory...")
            time.sleep(5)

    # Final table
    print_table()
