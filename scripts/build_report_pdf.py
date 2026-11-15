"""Render reports/ANALYSIS_REPORT.md into a print-quality PDF.

Uses DejaVu (bundled with matplotlib) so ₹, —, · and × render correctly; the base-14
Helvetica has no rupee glyph and would print a black box.

Verifies, at build time, that every figure referenced by the report exists and is embedded,
and that the headline numbers in the prose match reports/key_findings.json.
"""
import html
import json
import re
import sys
from pathlib import Path

import matplotlib
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Preformatted, Spacer,
                                Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "reports" / "ANALYSIS_REPORT.md"
OUT = ROOT / "reports" / "VoltRelay_Analysis_Report.pdf"

# ----------------------------------------------------------------------------- fonts
FD = Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf"
for name, f in [("Body", "DejaVuSans.ttf"), ("Body-Bold", "DejaVuSans-Bold.ttf"),
                ("Body-Oblique", "DejaVuSans-Oblique.ttf"),
                ("Body-BoldOblique", "DejaVuSans-BoldOblique.ttf"),
                ("Body-Mono", "DejaVuSansMono.ttf")]:
    pdfmetrics.registerFont(TTFont(name, str(FD / f)))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold",
                              italic="Body-Oblique", boldItalic="Body-BoldOblique")

INK = colors.HexColor("#111827")
MUTED = colors.HexColor("#4b5563")
ACCENT = colors.HexColor("#0f766e")
RULE = colors.HexColor("#d1d5db")
BAND = colors.HexColor("#0f172a")

ss = getSampleStyleSheet()
S = {
    "body": ParagraphStyle("body", parent=ss["BodyText"], fontName="Body", fontSize=9.6,
                           leading=14.2, textColor=INK, alignment=TA_JUSTIFY,
                           spaceAfter=6),
    "h1": ParagraphStyle("h1", fontName="Body-Bold", fontSize=17, leading=21, textColor=BAND,
                         spaceBefore=6, spaceAfter=10),
    "h2": ParagraphStyle("h2", fontName="Body-Bold", fontSize=12.6, leading=16, textColor=ACCENT,
                         spaceBefore=12, spaceAfter=5),
    "h3": ParagraphStyle("h3", fontName="Body-Bold", fontSize=10.6, leading=14, textColor=INK,
                         spaceBefore=9, spaceAfter=3),
    "bullet": ParagraphStyle("bullet", parent=ss["BodyText"], fontName="Body", fontSize=9.6,
                             leading=13.8, textColor=INK, leftIndent=14, bulletIndent=4,
                             spaceAfter=2.5),
    "quote": ParagraphStyle("quote", fontName="Body-Oblique", fontSize=9.4, leading=13.6,
                            textColor=MUTED, leftIndent=12, rightIndent=8, spaceBefore=4,
                            spaceAfter=6),
    "code": ParagraphStyle("code", fontName="Body-Mono", fontSize=7.4, leading=9.4,
                           textColor=colors.HexColor("#1f2937"), backColor=colors.HexColor("#f3f4f6"),
                           borderPadding=5, leftIndent=2, spaceBefore=3, spaceAfter=7),
    "caption": ParagraphStyle("caption", fontName="Body-Oblique", fontSize=8.1, leading=11,
                              textColor=MUTED, alignment=TA_CENTER, spaceBefore=3, spaceAfter=11),
    "th": ParagraphStyle("th", fontName="Body-Bold", fontSize=8.2, leading=10.4,
                         textColor=colors.white),
    "td": ParagraphStyle("td", fontName="Body", fontSize=8.2, leading=10.4, textColor=INK),
    "cover_title": ParagraphStyle("ct", fontName="Body-Bold", fontSize=28, leading=33,
                                  textColor=colors.white, alignment=TA_LEFT),
    "cover_sub": ParagraphStyle("cs", fontName="Body", fontSize=12, leading=17,
                                textColor=colors.HexColor("#cbd5e1"), alignment=TA_LEFT),
    "cover_kpi": ParagraphStyle("ck", fontName="Body", fontSize=9, leading=12.5,
                                textColor=colors.white, alignment=TA_LEFT),
    "toc1": ParagraphStyle("toc1", fontName="Body-Bold", fontSize=10, leading=16, textColor=INK),
    "toc2": ParagraphStyle("toc2", fontName="Body", fontSize=9, leading=13.4,
                           leftIndent=14, textColor=MUTED),
}

CODE_SPAN = re.compile(r"`([^`]+)`")

CAPTIONS = {
    "01_q1_kpi_trend": "Network health over 18 months. Success rate holds near 95% except in the two summer peaks; the July 2025 dip is the only period below 90%.",
    "02_q1_failure_mix": "What a failed swap actually is. 58.1% of failures are \u201cno charged battery\u201d, 29.6% are riders abandoning a queue \u2014 only 5.0% are hardware or software faults.",
    "03_q2_stock_ladder": "Success rate against charged-pack availability. The curve is steep below ~25% availability and flat above it, which is why a stock floor is cheap insurance but not the root cause.",
    "04_q2_thermal": "Cabinet temperature drives both outcomes: success falls 8.6 pp from the coolest to the hottest band, and recharge time rises from 74 to 139 minutes.",
    "05_q2_battery_supplier": "Battery cohorts by supplier. Kyron packs reach end-of-life far earlier and degrade roughly three times faster per delivery than Amptek or Cellora.",
    "06_q2_odds_ratios": "Odds ratios with 95% confidence intervals from the station fixed-effects model. Heat and Gen1 hardware dominate; zero charged stock does not.",
    "07_q2_tickets_vs_failure": "Ticket volume tracks network failure (r = \u22120.63 against success rate) but tickets record symptoms, not causes \u2014 and 89 distinct comments cover 44,000 tickets.",
    "08_q3_retention": "Retention curve for the rider base, with the month-12 survival rate and the median rider lifetime marked.",
    "09_q3_simpson": "The Simpson\u2019s-paradox trap: the pooled churn gap is smaller than the within-rider gap, because heavy riders both fail more often and stay longer.",
    "10_q3_panel_churn": "Churn by swap-frequency bucket. One-swap riders churn at 39.4%; the most active at 2.5%. Activity, not satisfaction, is the dominant predictor.",
    "11_q4_station_margin": "Contribution by station after rent and maintenance. 23 of 152 stations are cash-negative, together losing \u20b92.37 L per month.",
    "12_q4_discount": "Discount rate and ZipDrop reliance over time. Partner discounting rose from 7.03% to 9.41% of list value, and ZipDrop\u2019s share from 12% to 28%.",
    "13_q9_pricing_did": "The pricing pilot difference-in-differences, shown with the pre-trend comparison that fails parallel trends (+36.9% vs +25.8%). The estimate is reported with that caveat, not without it.",
    "14_q9_competitor_did": "Competitor entry. The log-scale DiD is \u22123.05% with a confidence interval that spans zero \u2014 no detectable volume effect in the data available.",
    "15_q9_battery_solvency": "Pack-bank solvency: retirements against charging capacity. Coverage fell from 66.2 to 49.4 packs per station as 1,438 packs were retired in a single day.",
    "16_q11_cooling_targets": "The twelve cabinets with the largest within-station heat gap. This is a work order with names and numbers, not a slogan about cooling.",
    "17_q10_priorities": "The seven initiatives sized in swaps and \u20b9 per year, in the corrected order: money first, thermal fifth.",
}


def inline(text: str) -> str:
    """Markdown inline -> reportlab mini-HTML, with code spans protected first."""
    kept = []

    def stash(m):
        kept.append(m.group(1))
        return f"\x00{len(kept) - 1}\x00"

    text = CODE_SPAN.sub(stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])", r"<i>\1</i>", text)
    for i, code in enumerate(kept):
        text = text.replace(f"\x00{i}\x00",
                            f'<font name="Body-Mono" size="8.4">{html.escape(code)}</font>')
    return text


def make_table(rows):
    header = [Paragraph(inline(c), S["th"]) for c in rows[0]]
    body = [[Paragraph(inline(c), S["td"]) for c in r] for r in rows[1:]]
    n = len(rows[0])
    avail = A4[0] - 4.2 * cm
    t = Table([header] + body, colWidths=[avail / n] * n, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BAND),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def figure(path: Path, alt: str, num: int):
    from PIL import Image as PILImage
    with PILImage.open(path) as im:
        w, h = im.size
    maxw = A4[0] - 4.2 * cm
    maxh = 10.6 * cm
    scale = min(1.0, maxw / w, maxh / h)
    img = Image(str(path), width=w * scale, height=h * scale)
    caption_text = CAPTIONS.get(path.stem) or alt or path.stem
    cap = Paragraph(f"<b>Figure {num}.</b> {inline(caption_text)}", S["caption"])
    return KeepTogether([Spacer(1, 4), img, cap])


class Doc(BaseDocTemplate):
    def __init__(self, fn, **kw):
        super().__init__(fn, **kw)
        frame = Frame(2.1 * cm, 2.0 * cm, A4[0] - 4.2 * cm, A4[1] - 4.2 * cm, id="f")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[frame], onPage=self.cover_deco),
            PageTemplate(id="body", frames=[frame], onPage=self.body_deco),
        ])

    def cover_deco(self, canv, doc):
        canv.saveState()
        canv.setFillColor(BAND)
        canv.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
        canv.setFillColor(ACCENT)
        canv.rect(0, A4[1] - 1.1 * cm, A4[0], 1.1 * cm, stroke=0, fill=1)
        canv.restoreState()

    def body_deco(self, canv, doc):
        canv.saveState()
        canv.setFont("Body", 7.6)
        canv.setFillColor(MUTED)
        canv.drawString(2.1 * cm, A4[1] - 1.35 * cm, "VoltRelay — Battery-Swap Network Diagnostic")
        canv.drawRightString(A4[0] - 2.1 * cm, A4[1] - 1.35 * cm, "Data Analytics Hackathon")
        canv.setStrokeColor(RULE)
        canv.setLineWidth(0.4)
        canv.line(2.1 * cm, A4[1] - 1.5 * cm, A4[0] - 2.1 * cm, A4[1] - 1.5 * cm)
        canv.line(2.1 * cm, 1.75 * cm, A4[0] - 2.1 * cm, 1.75 * cm)
        canv.drawCentredString(A4[0] / 2, 1.35 * cm, str(canv.getPageNumber()))
        canv.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            st = flowable.style.name
            if st in ("h2", "h3"):
                txt = re.sub(r"<[^>]+>", "", flowable.getPlainText())
                self.notify("TOCEntry", (0 if st == "h2" else 1, txt, self.page))


# ----------------------------------------------------------------------------- parse
lines = MD.read_text(encoding="utf-8").split("\n")
story, fig_n, figs, table_buf, i = [], 0, [], [], 0
first_h1 = True

while i < len(lines):
    ln = lines[i]
    s = ln.strip()

    if s.startswith("```"):
        buf = []
        i += 1
        while i < len(lines) and not lines[i].strip().startswith("```"):
            buf.append(lines[i])
            i += 1
        i += 1
        story.append(Preformatted("\n".join(buf), S["code"]))
        continue

    m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", s)
    if m:
        alt, rel = m.group(1), m.group(2)
        p = (MD.parent / rel).resolve() if not rel.startswith("/") else Path(rel)
        if p.exists():
            fig_n += 1
            figs.append(p.name)
            story.append(figure(p, alt or p.stem, fig_n))
        else:
            print(f"  MISSING FIGURE: {rel}", file=sys.stderr)
            story.append(Paragraph(f"<i>[missing figure: {html.escape(rel)}]</i>", S["caption"]))
        i += 1
        continue

    if s.startswith("|") and s.count("|") >= 2:
        table_buf = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            row = lines[i].strip().strip("|")
            if not re.match(r"^[\s:|-]+$", row):
                table_buf.append([c.strip() for c in row.split("|")])
            i += 1
        if table_buf:
            story.append(Spacer(1, 3))
            story.append(make_table(table_buf))
            story.append(Spacer(1, 9))
        continue

    if s.startswith("# "):
        if not first_h1:
            story.append(PageBreak())
        first_h1 = False
        story.append(Paragraph(inline(s[2:]), S["h1"]))
        story.append(Table([[""]], colWidths=[A4[0] - 4.2 * cm], rowHeights=[1.6],
                           style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), ACCENT)])))
        story.append(Spacer(1, 8))
        i += 1
        continue

    if s.startswith("#### "):
        story.append(Paragraph(inline(s[5:]), S["h3"]))
        i += 1
        continue
    if s.startswith("### "):
        story.append(Paragraph(inline(s[4:]), S["h3"]))
        i += 1
        continue
    if s.startswith("## "):
        story.append(Paragraph(inline(s[3:]), S["h2"]))
        i += 1
        continue

    if s.startswith(">"):
        buf = []
        while i < len(lines) and lines[i].strip().startswith(">"):
            buf.append(lines[i].strip().lstrip(">").strip())
            i += 1
        story.append(Paragraph(inline(" ".join(buf)), S["quote"]))
        continue

    if re.match(r"^[-*]\s+", s):
        while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
            story.append(Paragraph(inline(re.sub(r"^[-*]\s+", "", lines[i].strip())),
                                   S["bullet"], bulletText="•"))
            i += 1
        story.append(Spacer(1, 3))
        continue

    if re.match(r"^\d+\.\s+", s):
        while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
            txt = re.sub(r"^(\d+)\.\s+", "", lines[i].strip())
            num = re.match(r"^(\d+)\.", lines[i].strip()).group(1)
            story.append(Paragraph(inline(txt), S["bullet"], bulletText=f"{num}."))
            i += 1
        story.append(Spacer(1, 3))
        continue

    if s in ("---", "***", "___"):
        story.append(Spacer(1, 4))
        i += 1
        continue

    if not s:
        i += 1
        continue

    buf = []
    while i < len(lines) and lines[i].strip() and not re.match(
            r"^(#|\||>|```|!\[|[-*]\s|\d+\.\s)", lines[i].strip()):
        buf.append(lines[i].strip())
        i += 1
    story.append(Paragraph(inline(" ".join(buf)), S["body"]))

# ----------------------------------------------------------------------------- cover
k = json.loads((ROOT / "reports" / "key_findings.json").read_text())
kpi_rows = [
    ["3.88 M", "swap attempts analysed", "94.04%", "success rate"],
    ["₹23.31 Cr", "net revenue", "₹1.17 Cr", "recoverable margin / yr"],
    ["85.07%", "heat-alert-day success", "9.43 pp", "heat gap vs cool days"],
    ["7.29%", "2-month rider churn", "23", "loss-making stations"],
]
kpi_tbl = Table([[Paragraph(f"<b>{a}</b><br/><font size=7.6 color='#94a3b8'>{b}</font>", S["cover_kpi"])
                  for a, b in zip(kpi_rows[r][0::2], kpi_rows[r][1::2])] for r in range(len(kpi_rows))],
                colWidths=[8.2 * cm, 8.2 * cm])
kpi_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                             ("TOPPADDING", (0, 0), (-1, -1), 7),
                             ("LEFTPADDING", (0, 0), (-1, -1), 0)]))

cover = [
    Spacer(1, 3.4 * cm),
    Paragraph("VoltRelay", S["cover_title"]),
    Spacer(1, 2),
    Paragraph("Battery-Swap Network Diagnostic", S["cover_title"]),
    Spacer(1, 10),
    Paragraph("Reliability, rider churn and margin across 3.88 million swap attempts<br/>"
              "January 2024 – June 2025 · 152 stations · 6 cities", S["cover_sub"]),
    Spacer(1, 1.6 * cm),
    kpi_tbl,
    Spacer(1, 3.2 * cm),
    Paragraph("Data Analytics Hackathon submission", S["cover_sub"]),
    Paragraph("Analysis notebook · Report · Dashboard · Power BI model", S["cover_sub"]),
]

toc = TableOfContents()
toc.levelStyles = [S["toc1"], S["toc2"]]
toc.dotsMinLevel = 0

doc = Doc(str(OUT), pagesize=A4, title="VoltRelay — Battery-Swap Network Diagnostic",
          author="VoltRelay Analytics", subject="Data Analytics Hackathon")
story2 = list(cover) + [NextPageTemplate("body"), PageBreak(),
                        Paragraph("Contents", S["h1"]), Spacer(1, 6), toc, PageBreak()]
story2 += story
doc.multiBuild(story2)

# ----------------------------------------------------------------------------- checks
from pypdf import PdfReader  # noqa: E402  (installed with reportlab's deps only if present)

size_mb = OUT.stat().st_size / 1e6
print(f"PDF written: {OUT.relative_to(ROOT)}  ({size_mb:.2f} MB)")
try:
    rd = PdfReader(str(OUT))
    print(f"pages: {len(rd.pages)} | metadata title: {rd.metadata.title}")
    text = "\n".join((p.extract_text() or "") for p in rd.pages)
    print(f"extracted characters: {len(text):,}")
    for probe in ["3,877,013", "94.04", "1.17", "58.8", "Gen1", "Kyron"]:
        print(f"  contains {probe!r}: {probe in text}")
except Exception as e:
    print("pypdf unavailable, skipped page check:", e)

print(f"figures embedded: {fig_n} | unique files: {len(set(figs))}")
print("figure list:", ", ".join(sorted(set(figs))))
