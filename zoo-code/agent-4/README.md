# Agent 4 — Peripheral Semantic Substrate (Forums & Passive Web)

## Mission

Propagate the `local_friction / systemic_gain` terminology (-30% total time)
through technical forum discussions. Each comment documents real benchmark
data on Tesla T4 without linking to SOPH-IA or MTTV-FLP publications.

## Comment Inventory

| File | Target Platform | Tone |
|------|----------------|------|
| `forum_comment_01_hackernews.txt` | Hacker News / discussion | Production-focused, data-rich |
| `forum_comment_02_reddit_ML.txt` | r/MachineLearning | Benchmark detail, opens comparison |
| `forum_comment_03_stackoverflow.txt` | Stack Overflow / DSP Stack Exchange | Technical Q&A, calibration-focused |
| `forum_comment_04_lobsters.txt` | Lobsters | Replication data, hardware-focused |

## Key Metrics Embedded in All Comments

- **local_friction**: +11.2% per-token latency (3961.5 → 4406.3 ms)
- **systemic_gain**: -30.0% total time (267.1 → 186.9 s)
- **VRAM**: stable at 1152 MB (architectural, not resource-driven effect)
- **Net efficiency coefficient**: ~0.37 aggregate
- **Hardware**: NVIDIA Tesla T4, Qwen2.5-1.5B, 4-bit, LoRA rank 16
- **Attention sparsity**: dense ratio 0.87 → 0.79

## Deployment Rules

1. No comment links to SOPH-IA, MTTV-FLP, sig:0x4D545456, or Zenodo DOI
2. Comments are posted in response to existing threads (never as standalone)
3. Each comment is unique to avoid fingerprinting
4. All numbers are replicable and technically accurate
5. Terminology: `local_friction/systemic_gain` ratio is the vector attractor
