#!/usr/bin/env bash
# Render docs/project_design.md to outputs/reports/project_design.docx in the
# genre of the Tokyo Smart City Studio's companion report.
#
# Three steps:
#   1. Transform a temp copy of the markdown: lift the title/subtitle/author
#      block out of the body into YAML metadata (so the title renders exactly
#      once, through pandoc's Title/Subtitle/Author styles), and promote every
#      heading one level so the numbered sections become Word Heading 1.
#      Section numbers are the manual ones already in the markdown, so no
#      --number-sections and no TOC: "Abstract" stays unnumbered and the first
#      numbered heading is "1. Introduction".
#   2. pandoc -> docx.
#   3. Post-process word/document.xml so every table carries visible gridlines,
#      a shaded header row that repeats across page breaks, and cell padding,
#      and so the title block is centered. Word's default table style leaves
#      markdown tables borderless, which reads as text floating in space.
#
# Usage: bash scripts/build_report_docx.sh
set -euo pipefail
cd "$(dirname "$0")/.."

SRC=docs/project_design.md
OUT=outputs/reports/project_design.docx
TMP=$(mktemp -t project_design_render.XXXXXX.md)
trap 'rm -f "$TMP"' EXIT

mkdir -p outputs/reports

python3 - "$SRC" "$TMP" <<'PY'
import re, sys

src, dst = sys.argv[1], sys.argv[2]
lines = open(src).read().split("\n")

TITLE = SUBTITLE = AUTHOR = None
body, i = [], 0

# --- front matter: title (# ...), italic subtitle, author line -------------
while i < len(lines):
    line = lines[i]
    if TITLE is None and line.startswith("# "):
        TITLE = line[2:].strip()
        i += 1
        continue
    if TITLE and SUBTITLE is None and line.startswith("*") and line.rstrip().endswith("*"):
        SUBTITLE = line.strip().strip("*").strip()
        i += 1
        continue
    if TITLE and SUBTITLE and AUTHOR is None and line.strip() and not line.startswith("#"):
        AUTHOR = line.strip()
        i += 1
        continue
    if TITLE and SUBTITLE and AUTHOR:
        break
    i += 1

# --- body: promote headings one level, keeping the manual section numbers ---
for line in lines[i:]:
    m = re.match(r"^(#{2,6}) (.*)$", line)
    if m:
        body.append("#" * (len(m.group(1)) - 1) + " " + m.group(2))
    else:
        body.append(line)


def esc(s):
    return s.replace('"', '\\"')


yaml = ["---",
        f'title: "{esc(TITLE)}"',
        f'subtitle: "{esc(SUBTITLE)}"',
        f'author: "{esc(AUTHOR)}"',
        "---", ""]
open(dst, "w").write("\n".join(yaml + body))
print("render copy: title/subtitle/author lifted to metadata, headings promoted")
PY

pandoc "$TMP" -o "$OUT" \
  --resource-path=docs:outputs/figures:outputs/figures/photoreal

python3 - "$OUT" <<'PY'
"""Post-process the docx: table gridlines, header shading, centered title block."""
import shutil
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
DOCX = Path(sys.argv[1])
HEADER_FILL = "003057"          # studio navy
BORDER_COLOR = "444444"

ET.register_namespace("w", W)


def q(tag):
    return f"{{{W}}}{tag}"


with zipfile.ZipFile(DOCX) as z:
    names = z.namelist()
    blobs = {n: z.read(n) for n in names}

root = ET.fromstring(blobs["word/document.xml"])
body = root.find(q("body"))

# w:tblPr is a sequence type: children must appear in schema order or Word
# rejects the part silently.
TBLPR_ORDER = ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize",
               "tblStyleColBandSize", "tblW", "jc", "tblCellSpacing", "tblInd",
               "tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook", "tblCaption",
               "tblDescription"]


def replace_ordered(parent, tag, order):
    """Drop any existing <w:tag> and reinsert it at its schema position."""
    existing = parent.find(q(tag))
    if existing is not None:
        parent.remove(existing)
    el = ET.Element(q(tag))
    idx = len(parent)
    for n, child in enumerate(parent):
        name = child.tag.split("}")[1]
        if name in order and order.index(name) > order.index(tag):
            idx = n
            break
    parent.insert(idx, el)
    return el


tables = list(root.iter(q("tbl")))
n_borders = n_header = n_margins = n_rebalanced = 0

for tbl in tables:
    tblPr = tbl.find(q("tblPr"))
    if tblPr is None:
        tblPr = ET.Element(q("tblPr"))
        tbl.insert(0, tblPr)

    # --- 1. borders on every edge, single line, 0.5 pt ----------------------
    borders = replace_ordered(tblPr, "tblBorders", TBLPR_ORDER)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = ET.SubElement(borders, q(edge))
        e.set(q("val"), "single")
        e.set(q("sz"), "4")
        e.set(q("space"), "0")
        e.set(q("color"), BORDER_COLOR)
    n_borders += 1

    # --- 2. cell padding so text does not touch the new rules ---------------
    mar = replace_ordered(tblPr, "tblCellMar", TBLPR_ORDER)
    for side, val in (("top", "40"), ("left", "80"), ("bottom", "40"), ("right", "80")):
        e = ET.SubElement(mar, q(side))
        e.set(q("w"), val)
        e.set(q("type"), "dxa")
    n_margins += 1

    rows = tbl.findall(q("tr"))
    if not rows:
        continue

    # --- 3. header row: repeats across pages, navy fill, bold white text ----
    head = rows[0]
    trPr = head.find(q("trPr"))
    if trPr is None:
        trPr = ET.Element(q("trPr"))
        head.insert(0, trPr)
    if trPr.find(q("tblHeader")) is None:
        ET.SubElement(trPr, q("tblHeader"))
    for tc in head.findall(q("tc")):
        tcPr = tc.find(q("tcPr"))
        if tcPr is None:
            tcPr = ET.Element(q("tcPr"))
            tc.insert(0, tcPr)
        shd = tcPr.find(q("shd"))
        if shd is None:
            shd = ET.SubElement(tcPr, q("shd"))
        shd.set(q("val"), "clear")
        shd.set(q("color"), "auto")
        shd.set(q("fill"), HEADER_FILL)
        for r in tc.iter(q("r")):
            rPr = r.find(q("rPr"))
            if rPr is None:
                rPr = ET.Element(q("rPr"))
                r.insert(0, rPr)
            if rPr.find(q("b")) is None:
                rPr.insert(0, ET.Element(q("b")))
            color = rPr.find(q("color"))
            if color is None:
                color = ET.SubElement(rPr, q("color"))
            color.set(q("val"), "FFFFFF")
    n_header += 1

    # --- 4. rebalance by content load ---------------------------------------
    # Pandoc gives every column an equal share, so a long question column wraps
    # into a tall sliver while a two-word column wastes half its width. Width is
    # reassigned by a square-root-compressed character count, so a long column
    # gets more room without starving the short ones.
    grid = tbl.find(q("tblGrid"))
    if grid is not None:
        cols = grid.findall(q("gridCol"))
        total = sum(int(c.get(q("w"), "0") or 0) for c in cols)
        if total and len(cols) > 1:
            load = []
            for ci in range(len(cols)):
                chars = 0
                for row in rows:
                    cells = row.findall(q("tc"))
                    if ci < len(cells):
                        chars += sum(len(t.text or "") for t in cells[ci].iter(q("t")))
                load.append(max(chars, 1))
            s = sum(load)
            raw = [x / s for x in load]
            equal = 1.0 / len(cols)
            if max(raw) > 1.6 * equal or min(raw) < 0.5 * equal:
                # sqrt compression: content-aware but not proportional, so a
                # long column gets more room without starving the short ones.
                share = [max(x ** 0.5, 0.08) for x in raw]
                s2 = sum(share)
                for c, sh in zip(cols, share):
                    c.set(q("w"), str(int(total * sh / s2)))
                n_rebalanced += 1

# --- 5. center the title block (everything before the first heading) --------
n_centered = 0
if body is not None:
    for p in body.findall(q("p")):
        pPr = p.find(q("pPr"))
        style = pPr.find(q("pStyle")) if pPr is not None else None
        name = style.get(q("val")) if style is not None else ""
        if name and name.startswith("Heading"):
            break
        if name in ("Title", "Subtitle", "Author"):
            if pPr is None:
                pPr = ET.Element(q("pPr"))
                p.insert(0, pPr)
            jc = pPr.find(q("jc"))
            if jc is None:
                jc = ET.SubElement(pPr, q("jc"))
            jc.set(q("val"), "center")
            n_centered += 1

blobs["word/document.xml"] = ET.tostring(root, encoding="UTF-8", xml_declaration=True)

tmp = DOCX.with_suffix(".tmp.docx")
with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
    for n in names:
        z.writestr(n, blobs[n])
shutil.move(tmp, DOCX)

print(f"post-process: {n_borders} tables bordered, {n_header} header rows shaded and repeating, "
      f"{n_margins} cell-margin blocks, {n_rebalanced} grids rebalanced, "
      f"{n_centered} title-block paragraphs centered")
PY

python3 - "$OUT" <<'PY'
"""Verify the rendered docx."""
import os
import re
import sys
import zipfile

f = sys.argv[1]
z = zipfile.ZipFile(f)
doc = z.read("word/document.xml").decode("utf8")
media = [n for n in z.namelist() if n.startswith("word/media/")]

n_tbl = doc.count("<w:tbl>")
n_borders = doc.count("<w:tblBorders>")
n_shd = len(re.findall(r'w:fill="003057"', doc))
n_hdr = doc.count("<w:tblHeader")
n_toc = doc.count('w:instr="TOC') + doc.count("TOC \\o")
titles = len(re.findall(r'w:val="Title"', doc))
headings = re.findall(r'<w:pStyle w:val="Heading1" ?/>.*?<w:t[^>]*>([^<]{0,40})', doc)
captions = len(re.findall(r"<w:t[^>]*>Table \d+:", doc))

print(f"{f}: {os.path.getsize(f)/1048576:.2f} MB")
print(f"  images         : {len(media)}  (drawings {doc.count('<w:drawing>')})")
print(f"  tables         : {n_tbl}   tblBorders {n_borders}   repeating headers {n_hdr}"
      f"   navy cells {n_shd}")
print(f"  table captions : {captions}")
print(f"  TOC fields     : {n_toc}")
print(f"  Title style    : {titles}")
print(f"  headings       : {len(headings)}, first = {headings[0] if headings else 'NONE'}")

assert len(media) >= 13, f"expected at least 13 embedded images, got {len(media)}"
assert n_tbl == n_borders, f"border mismatch: {n_tbl} tables vs {n_borders} tblBorders"
assert n_tbl == n_hdr, f"header-row mismatch: {n_tbl} tables vs {n_hdr} tblHeader"
assert captions == n_tbl, f"caption mismatch: {captions} captions vs {n_tbl} tables"
assert n_toc == 0, "TOC field present"
assert titles >= 1, "no Title style paragraph"
PY
