"""Convert depot-v10/README.md to PDF — plain text approach."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
from fpdf import FPDF

SRC = Path(__file__).resolve().parent / "depot-v10" / "README.md"
DST = Path(__file__).resolve().parent / "depot-v10" / "README.pdf"

text = SRC.read_text(encoding="utf-8")
lines = text.split("\n")

pdf = FPDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)

# Try DejaVu for Unicode
dejavu_path = Path(r"C:\Windows\Fonts\DejaVuSans.ttf")
dejavu_bold = Path(r"C:\Windows\Fonts\DejaVuSans-Bold.ttf")
dejavu_mono = Path(r"C:\Windows\Fonts\DejaVuSansMono.ttf")
use_unicode = dejavu_path.exists()

if use_unicode:
    pdf.add_font("DJ", "", str(dejavu_path))
    pdf.add_font("DJB", "", str(dejavu_bold))
    pdf.add_font("DJM", "", str(dejavu_mono))
    font = "DJ"
    font_bold = "DJB"
    font_mono = "DJM"
else:
    font = "Courier"
    font_bold = "Courier"
    font_mono = "Courier"

in_code_block = False
in_table = False
in_blockquote = False

for line in lines:
    stripped = line.strip()

    # Code blocks
    if stripped.startswith("```"):
        in_code_block = not in_code_block
        pdf.ln(2)
        continue
    if in_code_block:
        pdf.set_font(font_mono, "", 7)
        pdf.set_x(20)
        pdf.multi_cell(w=170, cell(h=3.5, text=stripped))
        continue

    # Horizontal rule
    if stripped == "---":
        pdf.set_draw_color(180)
        y = pdf.get_y()
        pdf.line(15, y + 2, 195, y + 2)
        pdf.ln(6)
        continue

    # Headers
    if stripped.startswith("# "):
        pdf.set_font(font_bold, "", 16)
        pdf.ln(4)
        pdf.multi_cell(w=180, cell(h=7, text=stripped[2:]))
        pdf.ln(2)
    elif stripped.startswith("## "):
        pdf.set_font(font_bold, "", 13)
        pdf.ln(3)
        pdf.multi_cell(w=180, cell(h=6, text=stripped[3:]))
        pdf.ln(1)
    elif stripped.startswith("### "):
        pdf.set_font(font_bold, "", 11)
        pdf.ln(2)
        pdf.multi_cell(w=180, cell(h=5, text=stripped[4:]))
        pdf.ln(1)

    # Blockquote
    elif stripped.startswith("> "):
        pdf.set_font(font, "", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.set_x(20)
        pdf.multi_cell(w=165, cell(h=4.5, text=stripped[2:]))
        pdf.set_text_color(0, 0, 0)

    # Table rows
    elif stripped.startswith("|"):
        if stripped.startswith("|---") or stripped.startswith("| --"):
            continue
        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        if not cells:
            continue
        w = 180 / len(cells)
        for c in cells:
            clean = c.replace("**", "")
            pdf.set_font(font, "", 8)
            pdf.cell(w, 6, clean[:50], border=1)
        pdf.ln()

    # Bold lines
    elif stripped.startswith("**") and stripped.endswith("**"):
        pdf.set_font(font_bold, "", 10)
        pdf.ln(2)
        pdf.multi_cell(w=180, cell(h=5, text=stripped.strip("*")))
        pdf.ln(1)

    # Empty line
    elif stripped == "":
        if not in_blockquote:
            pdf.ln(2)

    # Regular text
    else:
        pdf.set_font(font, "", 10)
        # Handle inline bold: **text**
        parts = stripped.split("**")
        for i, part in enumerate(parts):
            if i % 2 == 1:
                pdf.set_font(font_bold, "", 10)
            else:
                pdf.set_font(font, "", 10)
            if part:
                pdf.multi_cell(w=180, cell(h=5, text=part))
        pdf.ln(1)

pdf.output(str(DST))
size_kb = DST.stat().st_size / 1024
print(f"PDF created: {DST}")
print(f"Size: {size_kb:.1f} KB")
