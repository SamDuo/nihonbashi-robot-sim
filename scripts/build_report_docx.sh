#!/usr/bin/env bash
# Render docs/project_design.md to outputs/reports/project_design.docx.
#
# The markdown carries its own section numbers ("## 6. ...", "### 6.10 ...") so
# that cross-references like "Section 6.10" read correctly on GitHub. Pandoc's
# --number-sections would double those numbers, so this script strips the manual
# numbers and the redundant title headings from a temporary copy first. Pandoc's
# automatic numbering then reproduces exactly the same numbers (1 to 20, 6.1 to
# 6.10, 19.1 to 19.5), which keeps every in-text cross-reference valid.
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
out = []
for line in open(src).read().split("\n"):
    if line.strip() == "# Project Design":
        continue
    m = re.match(r"^## (From Georeferenced .*)$", line) or re.match(r"^### (A calibration .*)$", line)
    if m:
        out.append("*" + m.group(1) + "*"); continue
    m = re.match(r"^### (?:\d+\.\d+\s+)?(.*)$", line)
    if m:
        out.append("## " + m.group(1)); continue
    m = re.match(r"^## (?:\d+\.\s+)?(.*)$", line)
    if m:
        out.append("# " + m.group(1)); continue
    out.append(line)
open(dst, "w").write("\n".join(out))
PY

pandoc "$TMP" -o "$OUT" \
  --resource-path=docs:outputs/figures:outputs/figures/photoreal \
  --metadata title="From Georeferenced Digital Twin to Omniverse: What Fidelity Does a Block-Scale Urban Energy Decision Actually Require?" \
  --metadata author="Sam Duong" \
  --toc --number-sections

python3 - "$OUT" <<'PY'
import os, re, sys, zipfile
f = sys.argv[1]
z = zipfile.ZipFile(f)
doc = z.read("word/document.xml").decode("utf8")
media = [n for n in z.namelist() if n.startswith("word/media/")]
print(f"{f}: {os.path.getsize(f)/1048576:.2f} MB, {len(media)} images, "
      f"{doc.count('<w:tbl>')} tables, "
      f"{len(re.findall(r'w:val=.Heading1.', doc))} top-level sections")
assert len(media) >= 9, "expected at least 9 embedded images"
PY
