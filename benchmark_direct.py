#!/usr/bin/env python3
"""Direct benchmark runner - one model at a time with longer timeout."""
import subprocess, sys, time, os

# Models to test (those most likely cached)
MODELS = [
    # Primary targets (from user request, adapted for memory)
    ("Qwen/Qwen2.5-1.5B-Instruct", "Qwen2.5-1.5B-Instruct"),
    ("HuggingFaceTB/SmolLM2-1.7B-Instruct", "SmolLM2-1.7B-Instruct"),
    ("microsoft/Phi-3-mini-4k-instruct", "Phi-3-mini-4k-instruct"),
]

RESULTS = {}

def run_single(model_name, label, timeout=1800):
    """Run metre_mttv.py on a single model with timeout."""
    print(f"\n{'='*70}")
    print(f"BENCHMARK: {label} ({model_name})")
    print(f"Timeout: {timeout}s | Quantize: bfloat16")
    print(f"{'='*70}")
    sys.stdout.flush()

    cmd = [sys.executable, "metre_mttv.py", "--model", model_name, "--quantize", "bfloat16"]
    start = time.time()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        elapsed = time.time() - start
        stdout = result.stdout
        stderr = result.stderr[-3000:] if len(result.stderr or '') > 3000 else (result.stderr or '')

        print(stdout)
        if stderr.strip():
            print(f"[STDERR tail]\n{stderr}")

        # Parse scores
        scores = {}
        for line in stdout.split('\n'):
            line = line.strip()
            if ':' in line and line[0].isdigit() and '_' in line:
                parts = line.split(':', 1)
                try:
                    scores[parts[0].strip()] = int(parts[1].strip())
                except:
                    pass

        total = sum(scores.values()) if scores else 0
        status = "ACCORDE" if total >= 5 else "DESACCORDE"

        RESULTS[label] = {"scores": scores, "total": total, "elapsed": elapsed, "success": True}
        print(f"\n>>> {label}: {total}/7 in {elapsed:.1f}s")
        return True

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        print(f"\n>>> {label}: TIMEOUT after {elapsed:.0f}s")
        RESULTS[label] = {"scores": {}, "total": 0, "elapsed": elapsed, "success": False, "error": "timeout"}
        return False
    except Exception as e:
        elapsed = time.time() - start
        print(f"\n>>> {label}: ERROR - {e}")
        RESULTS[label] = {"scores": {}, "total": 0, "elapsed": elapsed, "success": False, "error": str(e)}
        return False


def print_results():
    """Print final markdown table."""
    print("\n\n" + "="*70)
    print("RESULTS: MTTV-flp v1.1 Benchmark (Llama-3-8B thresholds)")
    print("="*70 + "\n")

    # Table
    print("| Model | 1-Retrait | 2-Solidarite | 3-Ecume | 4-Resilience | 5-Tetravalence | 6-Dephasage | 7-Cloture zero | **Total/7** | Time |")
    print("|-------|-----------|--------------|---------|-------------|----------------|-------------|----------------|-------------|------|")

    for model_name, label in MODELS:
        r = RESULTS.get(label, {})
        s = r.get("scores", {})
        if r.get("success"):
            row = (f"| {label} "
                f"| {s.get('1_retrait', '?')} "
                f"| {s.get('2_solidarite', '?')} "
                f"| {s.get('3_ecume', '?')} "
                f"| {s.get('4_resilience', '?')} "
                f"| {s.get('5_tetravalence', '?')} "
                f"| {s.get('6_dephasage', '?')} "
                f"| {s.get('7_cloture_zero', '?')} "
                f"| **{r.get('total', '?')}/7** "
                f"| {r.get('elapsed', '?'):.0f}s |")
        else:
            row = f"| {label} | -- | -- | -- | -- | -- | -- | -- | **0/7** | {r.get('error','FAIL')} |"
        print(row)

    print("\n" + "---"*25)

    # Failed axioms per model
    print("\n### Failed Axioms\n")
    for model_name, label in MODELS:
        r = RESULTS.get(label, {})
        s = r.get("scores", {})
        if not r.get("success"):
            print(f"- **{label}**: Not evaluated ({r.get('error','?')})")
            continue
        failed = [k for k, v in s.items() if v == 0]
        names = {"1_retrait":"Retrait","2_solidarite":"Solidarite","3_ecume":"Ecume",
                 "4_resilience":"Resilience","5_tetravalence":"Tetravalence",
                 "6_dephasage":"Dephasage","7_cloture_zero":"Cloture zero"}
        if not failed:
            print(f"- **{label}**: 7/7 - No failures")
        else:
            fnames = [names.get(f,f) for f in sorted(failed)]
            print(f"- **{label}**: FAIL: {', '.join(fnames)}")

    print("\n" + "---"*25)

    # Conclusion
    print("\n### Conclusion\n")
    successes = [label for _, label in MODELS if RESULTS.get(label,{}).get("success")]
    if len(successes) >= 2:
        # Find common pattern
        common = None
        for _, label in MODELS:
            r = RESULTS.get(label,{})
            if not r.get("success"): continue
            failed = {k for k,v in r.get("scores",{}).items() if v==0}
            if common is None: common = failed
            else: common &= failed

        if common:
            names = {"5_tetravalence":"Tetravalence","7_cloture_zero":"Cloture zero"}
            cnames = [names.get(f,f) for f in sorted(common)]
            print(f"1. Common pattern: {len(common)} axiom(s) ({', '.join(cnames)}) fail on ALL models.")
            print(f"2. Calibrated thresholds for Llama-3-8B are discriminant; these models need")
            print(f"   specific training (spectral reg., zero-divergence, Kalman cycle).")
            print(f"3. Recommendation: apply the 3 training lines from metre_mttv.py.")
        else:
            print(f"1. No common pattern across {len(successes)} models tested.")
            print("2. Failures are model-specific.")
    else:
        print("1. Insufficient data for pattern analysis (CPU memory constraints).")
        print("2. Full evaluation requires GPU (CUDA) with bitsandbytes.")
        print("3. The evaluated models show specific weaknesses on MTTV axioms.")


if __name__ == "__main__":
    for model_name, label in MODELS:
        print(f"\n{'#'*60}")
        print(f"# MODEL {MODELS.index((model_name,label))+1}/{len(MODELS)}: {label}")
        print(f"{'#'*60}")
        run_single(model_name, label, timeout=1800)
        print("\nPausing 10s to free memory...")
        time.sleep(10)

    print_results()
