#!/usr/bin/env python3
"""
Convert resume_mttv_flp_hal.md to PDF using fpdf2 (Unicode-capable).
Output: plans/resume_mttv_flp_hal.pdf
"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
from fpdf import FPDF

SRC = Path(__file__).resolve().parent / "resume_mttv_flp_hal.md"
DST = Path(__file__).resolve().parent / "resume_mttv_flp_hal.pdf"

text = SRC.read_text(encoding="utf-8")
lines = text.split("\n")

pdf = FPDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)

# Check for DejaVu fonts (needed for Unicode / French characters)
dejavu_path = Path(r"C:\Windows\Fonts\DejaVuSans.ttf")
dejavu_bold = Path(r"C:\Windows\Fonts\DejaVuSans-Bold.ttf")
dejavu_mono = Path(r"C:\Windows\Fonts\DejaVuSansMono.ttf")

if dejavu_path.exists():
    pdf.add_font("DJ", "", str(dejavu_path))
    pdf.add_font("DJB", "", str(dejavu_bold))
    pdf.add_font("DJM", "", str(dejavu_mono))
    FONT = "DJ"
    FONT_BOLD = "DJB"
    FONT_MONO = "DJM"
else:
    # Fallback — may not render French accents correctly
    FONT = "Courier"
    FONT_BOLD = "Courier"
    FONT_MONO = "Courier"

in_code_block = False
in_table = False

def write_text(text, font_style="", size=10, x=None, w=180, color=None):
    """Write multi-cell text with optional formatting."""
    if color:
        pdf.set_text_color(*color)
    if x:
        pdf.set_x(x)
    pdf.set_font(font_style, "", size)
    pdf.multi_cell(w=w, text=text)
    if color:
        pdf.set_text_color(0, 0, 0)

def write_cell(text, font_style="", size=8, w=None):
    """Write a single table cell."""
    pdf.set_font(font_style, "", size)
    clean = text.replace("**", "").replace("*", "").replace("`", "")
    pdf.cell(w or (180 / max(1, len(text))), 6, clean[:60], border=1)

for line in lines:
    stripped = line.strip()

    # ── Code blocks ──
    if stripped.startswith("```"):
        in_code_block = not in_code_block
        pdf.ln(2)
        continue
    if in_code_block:
        pdf.set_font(FONT_MONO, "", 7)
        pdf.set_x(20)
        pdf.multi_cell(w=170, text=stripped)
        continue

    # ── Horizontal rule ──
    if stripped == "---":
        pdf.set_draw_color(150)
        y = pdf.get_y()
        if y > 270:
            pdf.add_page()
            y = pdf.get_y()
        pdf.line(15, y + 2, 195, y + 2)
        pdf.ln(5)
        continue

    # ── Headers ──
    if stripped.startswith("# "):
        pdf.set_font(FONT_BOLD, "", 15)
        pdf.ln(3)
        pdf.multi_cell(w=180, text=stripped[2:])
        pdf.ln(2)
    elif stripped.startswith("## "):
        pdf.set_font(FONT_BOLD, "", 12)
        pdf.ln(2)
        pdf.multi_cell(w=180, text=stripped[3:])
        pdf.ln(1)
    elif stripped.startswith("### "):
        pdf.set_font(FONT_BOLD, "", 10.5)
        pdf.ln(1)
        pdf.multi_cell(w=180, text=stripped[4:])
        pdf.ln(1)
    elif stripped.startswith("#### "):
        pdf.set_font(FONT_BOLD, "", 10)
        pdf.ln(1)
        pdf.multi_cell(w=180, text=stripped[5:])
        pdf.ln(0.5)

    # ── Blockquote ──
    elif stripped.startswith("> "):
        write_text(stripped[2:], size=9, x=20, w=165, color=(80, 80, 80))
        pdf.ln(1)

    # ── Table rows ──
    elif stripped.startswith("|"):
        if re.match(r"^\|[\s\-:]+\|", stripped):
            continue  # separator row
        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        if not cells:
            continue
        col_w = 180 / len(cells)
        # Check if it's a header (bold markers)
        is_header = any("**" in c for c in cells)
        for c in cells:
            clean = c.replace("**", "").replace("`", "")
            font_st = FONT_BOLD if is_header else FONT
            pdf.set_font(font_st, "", 7.5)
            pdf.cell(col_w, 5.5, clean[:50], border=1)
        pdf.ln()

    # ── Bold standalone lines ──
    elif re.match(r"^\*\*.+\*\*$", stripped):
        pdf.set_font(FONT_BOLD, "", 10)
        pdf.ln(1)
        pdf.multi_cell(w=180, text=stripped.strip("*"))
        pdf.ln(0.5)

    # ── Empty line ──
    elif stripped == "":
        pdf.ln(2)

    # ── Regular text (handles inline bold, italic, code) ──
    else:
        pdf.set_font(FONT, "", 9.5)
        # Process inline formatting for display
        # Remove bold markers for clean text
        text_clean = stripped
        pdf.multi_cell(w=180, text=text_clean)
        pdf.ln(0.8)

pdf.output(str(DST))
size_kb = DST.stat().st_size / 1024
print(f"✅ PDF created: {DST}")
print(f"   Size: {size_kb:.1f} KB")
print(f"   Pages: {pdf.pages_count}")
