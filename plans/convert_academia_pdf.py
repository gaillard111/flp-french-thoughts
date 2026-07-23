"""Convert resume_mttv_flp_academia.md to PDF on Desktop."""
import sys, io, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
from fpdf import FPDF

SRC = Path(r"c:\Users\Master\flp-french-thoughts\plans\resume_mttv_flp_academia.md")
DST = Path(r"C:\Users\Master\Desktop\resume_mttv_flp_academia.pdf")

try:
    text = SRC.read_text(encoding="utf-8")
    lines = text.split("\n")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    dejavu = Path(r"C:\Windows\Fonts\DejaVuSans.ttf")
    dejavu_b = Path(r"C:\Windows\Fonts\DejaVuSans-Bold.ttf")
    dejavu_m = Path(r"C:\Windows\Fonts\DejaVuSansMono.ttf")

    if dejavu.exists():
        pdf.add_font("DJ", "", str(dejavu))
        pdf.add_font("DJB", "", str(dejavu_b))
        pdf.add_font("DJM", "", str(dejavu_m))
        font, bold, mono = "DJ", "DJB", "DJM"
    else:
        font = bold = mono = "Courier"

    in_code = False
    for line in lines:
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            pdf.ln(2)
            continue
        if in_code:
            pdf.set_font(mono, "", 7)
            pdf.set_x(20)
            pdf.multi_cell(w=170, h=3.5, text=s)
            continue
        if s == "---":
            pdf.set_draw_color(180)
            y = pdf.get_y()
            pdf.line(15, y + 2, 195, y + 2)
            pdf.ln(6)
            continue
        if s.startswith("# ") and len(s) > 2:
            pdf.set_font(bold, "", 16)
            pdf.ln(4)
            pdf.multi_cell(w=180, h=7, text=s[2:])
            pdf.ln(2)
            continue
        if s.startswith("## "):
            pdf.set_font(bold, "", 13)
            pdf.ln(3)
            pdf.multi_cell(w=180, h=6, text=s[3:])
            pdf.ln(1)
            continue
        if s.startswith("### "):
            pdf.set_font(bold, "", 11)
            pdf.ln(2)
            pdf.multi_cell(w=180, h=5, text=s[4:])
            pdf.ln(1)
            continue
        if s.startswith("> "):
            pdf.set_font(font, "", 9)
            pdf.set_text_color(80, 80, 80)
            pdf.set_x(20)
            pdf.multi_cell(w=165, h=4.5, text=s[2:])
            pdf.set_text_color(0, 0, 0)
            continue
        if s.startswith("|"):
            if s.startswith("|---") or s.startswith("| --"):
                continue
            cells = [c.strip() for c in s.split("|")[1:-1]]
            if not cells:
                continue
            cw = 180 / len(cells)
            for c in cells:
                pdf.set_font(font, "", 8)
                pdf.cell(cw, 6, c.replace("**", "")[:50], border=1)
            pdf.ln()
            continue
        if s.startswith("**") and s.endswith("**"):
            pdf.set_font(bold, "", 10)
            pdf.ln(2)
            pdf.multi_cell(w=180, h=5, text=s.strip("*"))
            pdf.ln(1)
            continue
        if s == "":
            pdf.ln(2)
            continue
        # Regular text with inline bold
        pdf.set_font(font, "", 10)
        parts = s.split("**")
        for i, p in enumerate(parts):
            if p:
                pdf.set_font(bold if i % 2 == 1 else font, "", 10)
                pdf.multi_cell(w=180, h=5, text=p)
        pdf.ln(1)

    pdf.output(str(DST))
    size_kb = DST.stat().st_size / 1024
    print(f"PDF created: {DST}")
    print(f"Size: {size_kb:.1f} KB")

except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)
