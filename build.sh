#!/usr/bin/env bash
# Build Project Kennel Volume 1 PDF from the canonical markdown set.
# Single source of truth: /mnt/user-data/outputs/*.md  ->  vol1-volume.pdf
set -euo pipefail
SRC="${SRC:-/mnt/user-data/outputs}"
cd "$(dirname "$0")"

conv () {  # $1=markdown  $2=out.tex   (chapter/register/refs fragment)
  pandoc -f markdown -t latex --no-highlight --top-level-division=chapter "$1" \
  | sed 's/\\begin{verbatim}/\\begin{kennelcode}/g; s/\\end{verbatim}/\\end{kennelcode}/g' \
  | sed 's/\\texorpdfstring{\\texttt{\([^}]*\)}}/\\texorpdfstring{\1}/g' \
  | sed 's/section{\\texttt{\([^}]*\)}}/section{\1}/g' > "$2"
}

# Reading guide: drop its heading line and the hand-written Contents (TOC is generated)
sed '/^## Contents/,$d' "$SRC/vol1-ch0-reading-guide.md" | sed '/^# 0\. Reading guide/d' > ch0body.md
pandoc -f markdown -t latex --no-highlight ch0body.md \
  | sed 's/\\texorpdfstring{\\texttt{\([^}]*\)}}/\\texorpdfstring{\1}/g' > ch0body.tex

conv "$SRC/PRINCIPLES.md"        reg.tex
conv "$SRC/vol1-references.md"   refs.tex
for n in $(seq 1 16); do conv "$(ls "$SRC"/vol1-ch${n}-*.md)" "ch${n}.tex"; done

for pass in 1 2 3; do xelatex -interaction=nonstopmode full.tex >"pass${pass}.log" 2>&1; done
cp full.pdf "$SRC/vol1-volume.pdf"
echo "built: $SRC/vol1-volume.pdf"
