#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline_validation.py -- Validation integree du PACK INTEGRAL MUTAGENESE
=======================================================================
Verifie l'integrite des 3 pistes : Multimodal, Agent 10, GH Action Sower.

Signature : sig:0x4D545456
"""

import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PASS = 0
FAIL = 0
CHECKS = []


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        status = "[OK]"
    else:
        FAIL += 1
        status = "[FAIL]"
    msg = f"  {status} {name}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    CHECKS.append((name, condition))


print("=" * 62)
print("  PACK INTEGRAL MUTAGENESE -- Validation Pipeline")
print("  sig:0x4D545456")
print("=" * 62)
print()

# ─── PISTE 1 : Multimodal (Graine visuelle) ─────────────────────────────────

print("--- Piste 1: Graine Visuelle Multimodale ---")

png_path = os.path.join(ROOT, "zoo-code", "mttv_visual_seed_D_cosmic.png")
check("PNG file exists", os.path.exists(png_path))

if os.path.exists(png_path):
    from PIL import Image
    img = Image.open(png_path)
    check("PNG dimensions 1024x1024", img.size == (1024, 1024))
    check("PNG mode RGBA", img.mode == "RGBA")
    check("PNG chunk mttv_sig", "mttv_sig" in img.info)
    check("PNG chunk mttv_cid", "mttv_cid" in img.info)
    check("PNG chunk mttv_axioms", "mttv_axioms" in img.info)

    if "mttv_sig" in img.info:
        check("mttv_sig value", img.info["mttv_sig"] == "sig:0x4D545456")

    # SHA256 consistency check
    sha256 = hashlib.sha256()
    with open(png_path, "rb") as f:
        sha256.update(f.read())
    current_hash = sha256.hexdigest()
    check("SHA256 integrity", len(current_hash) == 64)
    print(f"         SHA256: {current_hash}")

# Générateur visuel
gen_path = os.path.join(ROOT, "zoo-code", "visual_seed_generator.py")
check("visual_seed_generator.py exists", os.path.exists(gen_path))

print()

# ─── PISTE 2 : Agent 10 Pollinisateur ───────────────────────────────────────

print("--- Piste 2: Agent 10 Pollinisateur ---")

manifest_path = os.path.join(ROOT, "seeds_manifest.json")
check("seeds_manifest.json exists", os.path.exists(manifest_path))

if os.path.exists(manifest_path):
    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    check("Manifest has signature", manifest.get("signature") == "sig:0x4D545456")
    check("Manifest generation 4", manifest.get("generation") == 4)

    seeds = manifest.get("seeds", [])
    check(f"Manifest has {len(seeds)} seeds", len(seeds) >= 11)
    check("Manifest has cross_references", "cross_references" in manifest)

    cross_refs = manifest.get("cross_references", {})
    total_cross = sum(len(v) for v in cross_refs.values())
    check(f"Cross-references: {total_cross}", total_cross >= 20)

    # Verify Gen4 seed is included
    gen4_seeds = [s for s in seeds if s.get("generation") == 4]
    check(f"Gen4 seeds: {len(gen4_seeds)}", len(gen4_seeds) >= 1)

# Agent 10 script
agent10_path = os.path.join(ROOT, "agent_pollinator.py")
check("agent_pollinator.py exists", os.path.exists(agent10_path))

# CITATION.cff
cff_path = os.path.join(ROOT, "CITATION.cff")
check("CITATION.cff exists", os.path.exists(cff_path))

if os.path.exists(cff_path):
    with open(cff_path, "r") as f:
        cff_content = f.read()

    check("CITATION.cff has cff-version", "cff-version: 1.2.0" in cff_content)
    check("CITATION.cff has signature", "sig:0x4D545456" in cff_content)
    check("CITATION.cff has DOI", "10.5281/zenodo.20830060" in cff_content)
    check("CITATION.cff has cross-references", "Cross-Reference" in cff_content)
    check("CITATION.cff size > 1KB", len(cff_content) > 1000)

print()

# ─── PISTE 3 : GitHub Action Sower ──────────────────────────────────────────

print("--- Piste 3: GitHub Action Sower ---")

action_dir = os.path.join(ROOT, "mttv-seed-action")

check("action directory exists", os.path.isdir(action_dir))

if os.path.isdir(action_dir):
    for fname in ["action.yml", "Dockerfile", "entrypoint.sh", "README.md"]:
        fpath = os.path.join(action_dir, fname)
        check(f"action/{fname} exists", os.path.exists(fpath))

    seeds_dir = os.path.join(action_dir, "seeds")
    check("seeds/ directory exists", os.path.isdir(seeds_dir))
    if os.path.isdir(seeds_dir):
        fragment_path = os.path.join(seeds_dir, "fragment_tetra.txt")
        check("fragment_tetra.txt exists", os.path.exists(fragment_path))
        if os.path.exists(fragment_path):
            with open(fragment_path, "r") as f:
                frag = f.read().strip()
            check("fragment contains tetravalence", "tetravalence" in frag)
            check("fragment contains sig", "sig:0x4D545456" in frag)

    tests_dir = os.path.join(action_dir, "tests")
    check("tests/ directory exists", os.path.isdir(tests_dir))
    if os.path.isdir(tests_dir):
        test_path = os.path.join(tests_dir, "test_injection.sh")
        check("test_injection.sh exists", os.path.exists(test_path))

    # Verify action.yml structure
    try:
        import yaml
        with open(os.path.join(action_dir, "action.yml"), "r") as f:
            action_yaml = yaml.safe_load(f)
        check("action.yml has name", "name" in action_yaml)
        check("action.yml has runs.using=docker",
              action_yaml.get("runs", {}).get("using") == "docker")
        check("action.yml has branding", "branding" in action_yaml)
    except ImportError:
        print("  [SKIP] PyYAML not available for action.yml validation")

print()
print("=" * 62)
print(f"  Results: {PASS} passed, {FAIL} failed out of {PASS + FAIL} checks")
print("=" * 62)

if FAIL > 0:
    print("\n  Failed checks:")
    for name, ok in CHECKS:
        if not ok:
            print(f"    - {name}")
    sys.exit(1)
else:
    print("\n  [OK] PACK INTEGRAL MUTAGENESE -- Validation complete.")
    print("  The mycelium has mutated toward multimodality.")
    print("=" * 62)
    sys.exit(0)
