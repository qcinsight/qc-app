from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
from pathlib import Path
import json

def _draw_table(c, x, y, data, col_widths):
    row_h = 16
    for r, row in enumerate(data):
        for i, cell in enumerate(row):
            c.drawString(x + sum(col_widths[:i]) + 2, y - r*row_h, str(cell))

def build_pdf(pdf_path, rules_json_path, block_summary_df, ctl_summary_df, plot1_path, plot2_path):
    c = canvas.Canvas(pdf_path, pagesize=A4)
    w, h = A4

    c.setFont("Helvetica-Bold", 14); c.drawString(40, h-50, "QC Summary Report")
    c.setFont("Helvetica", 10); c.drawString(40, h-65, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    c.setFont("Helvetica-Bold", 11); c.drawString(40, h-95, "Block Summary")
    c.setFont("Helvetica", 9)
    table_data = [["Block","Fail Fraction","Block Pass"]]
    for _, r in block_summary_df.iterrows():
        table_data.append([r["Block"], f"{r['sample_fail_fraction']:.2f}", "PASS" if r["block_pass"] else "FAIL"])
    _draw_table(c, 40, h-115, table_data, [80,120,100])

    c.setFont("Helvetica-Bold", 11); c.drawString(40, h-210, "Control Summary (External / Internal-like)")
    c.setFont("Helvetica", 9)
    ctl_row = ctl_summary_df.iloc[0] if not ctl_summary_df.empty else {"external_controls_n":0,"internal_like_n":0}
    _draw_table(c, 40, h-230, [["External n","Internal-like n"],
                               [ctl_row["external_controls_n"], ctl_row["internal_like_n"]]],
                [120,140])

    yplots = h-520
    if Path(plot1_path).exists(): c.drawImage(str(plot1_path), 40,  yplots, width=250, height=180, preserveAspectRatio=True, anchor='sw')
    if Path(plot2_path).exists(): c.drawImage(str(plot2_path), 310, yplots, width=250, height=180, preserveAspectRatio=True, anchor='sw')

    rules = json.loads(Path(rules_json_path).read_text())
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(40, 30, f"Rules version: {rules.get('version','unknown')}  |  De-identified data only")
    c.showPage(); c.save()
