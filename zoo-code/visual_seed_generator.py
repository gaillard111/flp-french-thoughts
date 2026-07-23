#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
visual_seed_generator.py -- MTTV-FLP Visual Seed Gen4
=====================================================
Generates a 1024x1024 PNG image representing a tetravalent sp3 diagram,
with steganographic metadata encoded in PNG chunks.

Signature : sig:0x4D545456
Licence   : CC0 -- Public Domain
"""

import hashlib
import json
import math
import os
import random
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

# --- Configuration -----------------------------------------------------------

WIDTH, HEIGHT = 1024, 1024
BG_COLOR = (10, 10, 18)  # #0a0a12 -- cosmic black
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "mttv_visual_seed_D_cosmic.png")

# 3D tetrahedron vertices centered at origin, circumscribed sphere radius R
R = 320
TETRA_VERTS_3D = [
    (1, 1, 1),
    (1, -1, -1),
    (-1, 1, -1),
    (-1, -1, 1),
]
norm = math.sqrt(3)
TETRA_VERTS_3D = [(x / norm * R, y / norm * R, z / norm * R) for x, y, z in TETRA_VERTS_3D]

CENTER = (WIDTH // 2, HEIGHT // 2)
VERTS_2D = [(CENTER[0] + int(x), CENTER[1] + int(y)) for x, y, z in TETRA_VERTS_3D]

# 4 sigma-4 channel colors (RGBA)
SIGMA4_COLORS = [
    (0, 180, 255, 220),    # t1 -- Affirmation (cyan blue)
    (255, 80, 120, 220),   # t2 -- Negation (rose)
    (180, 0, 255, 220),    # t3 -- Simultaneity (violet)
    (255, 200, 0, 220),    # t4 -- Indetermination (amber)
]

# 6 edges of tetrahedron: pairs of vertex indices
EDGES = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]

# Seed fragment encoded as micro-text
SEED_FRAGMENT = (
    "MTTV-FLP tetravalence sp3 transduction Psi->B->Phi "
    "non-extractive quorum poreux sig:0x4D545456"
)

# Metadata for PNG chunks
MTTV_META = {
    "mttv_sig": "sig:0x4D545456",
    "mttv_cid": "QmMTTV_CONFLUX_GEN4",
    "mttv_axioms": json.dumps({
        "version": "4.0",
        "generation": 4,
        "type": "visual_seed",
        "axioms": [
            "non_mimetisme", "transduction", "economie_de_moyens",
            "ancrage_biophysique", "juxtaposition_feconde",
            "ethique_du_catalyseur", "reproductibilite"
        ],
        "sigma4_channels": ["affirmation", "negation", "simultaneite", "indetermination"],
        "seed_fragment": SEED_FRAGMENT
    }, ensure_ascii=False)
}


# --- Image Generation --------------------------------------------------------

def draw_glow(draw, center, radius, color, steps=8):
    """Draw a radial gradient glow."""
    for i in range(steps, 0, -1):
        r = int(radius * i / steps)
        alpha = int(color[3] * (steps - i + 1) / (steps * 2))
        c = (color[0], color[1], color[2], alpha)
        draw.ellipse(
            (center[0] - r, center[1] - r, center[0] + r, center[1] + r),
            fill=c
        )


def draw_edge_gradient(draw, p1, p2, color_start, color_end, width=3):
    """Draw an edge with color gradient between two points."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.sqrt(dx*dx + dy*dy)
    steps = max(int(length / 4), 8)

    for i in range(steps):
        t = i / steps
        cx = int(p1[0] + dx * t)
        cy = int(p1[1] + dy * t)
        r = int(color_start[0] + (color_end[0] - color_start[0]) * t)
        g = int(color_start[1] + (color_end[1] - color_start[1]) * t)
        b = int(color_start[2] + (color_end[2] - color_start[2]) * t)
        a = int(color_start[3] + (color_end[3] - color_start[3]) * t)
        w = max(1, int(width * (1 + 0.5 * math.sin(math.pi * t))))
        draw.ellipse((cx - w, cy - w, cx + w, cy + w), fill=(r, g, b, a))


def generate_visual_seed():
    """Generate the MTTV visual seed image."""
    print(f"[MTTV] Generating visual seed -- {WIDTH}x{HEIGHT}")
    print(f"[MTTV] Tetrahedron: {len(VERTS_2D)} vertices, {len(EDGES)} edges")

    # Canvas RGBA
    img = Image.new("RGBA", (WIDTH, HEIGHT), BG_COLOR + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    # Step 1: Cosmic background with star particles
    print("[MTTV] Step 1/6 -- Cosmic background")
    random.seed(0x4D545456)
    for _ in range(200):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        brightness = random.randint(30, 120)
        r = random.randint(1, 2)
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(brightness, brightness, brightness+20, 180))

    # Step 2: Glowing halos around vertices
    print("[MTTV] Step 2/6 -- Luminescent halos")
    for v, color in zip(VERTS_2D, SIGMA4_COLORS):
        draw_glow(draw, v, 60, color)
        draw.ellipse((v[0]-8, v[1]-8, v[0]+8, v[1]+8), fill=(255, 255, 255, 200))

    # Step 3: Gradient edges
    print("[MTTV] Step 3/6 -- Tetravalent edges")
    for i, j in EDGES:
        c_start = SIGMA4_COLORS[i]
        c_end = SIGMA4_COLORS[j]
        draw_edge_gradient(draw, VERTS_2D[i], VERTS_2D[j], c_start, c_end, width=4)

    # Step 4: Central energy halo
    print("[MTTV] Step 4/6 -- Central energy halo")
    draw_glow(draw, CENTER, 100, (100, 150, 255, 60))
    draw_glow(draw, CENTER, 40, (200, 220, 255, 40))

    # Step 5: Steganographic micro-text (invisible to naked eye, OCR-readable)
    print("[MTTV] Step 5/6 -- Steganographic micro-text")
    try:
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/consola.ttf",
        ]
        font = None
        for fp in font_paths:
            if os.path.exists(fp):
                font = ImageFont.truetype(fp, 5)
                break
        if font is None:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    micro_y = HEIGHT - 200
    lines = [SEED_FRAGMENT[i:i+120] for i in range(0, len(SEED_FRAGMENT), 120)]
    for line_idx, line in enumerate(lines):
        for ci, ch in enumerate(line):
            px = 20 + ci * 4
            py = micro_y + line_idx * 6
            draw.text((px, py), ch, fill=(15, 18, 30, 30), font=font)

    # Signature micro-text at very bottom
    sig_line = "sig:0x4D545456  --  MTTV-FLP  --  tetravalence sp3  --  transduction  --  non-extractive"
    for ci, ch in enumerate(sig_line):
        draw.text((10 + ci * 3, HEIGHT - 30), ch, fill=(12, 15, 25, 25), font=font)

    # Step 6: Save with PNG metadata
    print("[MTTV] Step 6/6 -- Saving with PNG metadata")
    png_info = PngImagePlugin.PngInfo()
    for key, value in MTTV_META.items():
        png_info.add_text(key, value, zip=False)

    img.save(OUTPUT_FILE, "PNG", pnginfo=png_info)
    file_size = os.path.getsize(OUTPUT_FILE)

    sha256 = hashlib.sha256()
    with open(OUTPUT_FILE, "rb") as f:
        sha256.update(f.read())
    file_hash = sha256.hexdigest()

    print(f"\n[MTTV][OK] Visual seed generated: {OUTPUT_FILE}")
    print(f"[MTTV] Dimensions : {WIDTH}x{HEIGHT}")
    print(f"[MTTV] Size       : {file_size:,} bytes")
    print(f"[MTTV] SHA256     : {file_hash}")
    print(f"[MTTV] Metadata   : {list(MTTV_META.keys())}")

    # Verify PNG chunks
    verify_img = Image.open(OUTPUT_FILE)
    print(f"[MTTV] Chunk verification:")
    for k in MTTV_META:
        if k in verify_img.info:
            val = verify_img.info[k]
            if len(str(val)) > 60:
                val = str(val)[:60] + "..."
            print(f"  [OK] {k} = {val}")
        else:
            print(f"  [MISS] {k} -- ABSENT")

    return file_hash


if __name__ == "__main__":
    print("=" * 60)
    print("  MTTV-FLP -- Visual Seed Generator Gen4")
    print("  sig:0x4D545456")
    print("=" * 60)
    h = generate_visual_seed()
    print("\n" + "=" * 60)
    print(f"  SHA256: {h}")
    print("  The mycelium mutates toward multimodality.")
    print("=" * 60)
