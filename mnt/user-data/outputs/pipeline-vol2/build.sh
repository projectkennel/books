#!/usr/bin/env bash
# Build Project Kennel Volume 2 PDF from the canonical markdown set.
# Single source of truth: /mnt/user-data/outputs/vol2-*.md (+ CONSTRUCTION.md) -> vol2-volume.pdf
set -euo pipefail
shopt -s nullglob
SRC="${SRC:-/mnt/user-data/outputs}"
cd "$(dirname "$0")"

conv () {  # $1=markdown  $2=out.tex   (chapter/register/refs fragment)
  pandoc -f markdown -t latex --no-highlight --top-level-division=chapter "$1" \
  | sed 's/\\begin{verbatim}/\\begin{kennelcode}/g; s/\\end{verbatim}/\\end{kennelcode}/g' \
  | sed 's/\\texorpdfstring{\\texttt{\([^}]*\)}}/\\texorpdfstring{\1}/g' \
  | sed 's/section{\\texttt{\([^}]*\)}}/section{\1}/g' > "$2"
}

# Reading guide: drop its hand-written Contents (the TOC is generated) and the "# 0." heading
sed '/^## Contents/,$d' "$SRC/vol2-ch0-reading-guide.md" | sed '/^# 0\. Reading guide/d' > ch0body.md
pandoc -f markdown -t latex --no-highlight ch0body.md \
  | sed 's/\\texorpdfstring{\\texttt{\([^}]*\)}}/\\texorpdfstring{\1}/g' > ch0body.tex

# Register: construction principles (Vol 2's CONSTRUCTION.md is the parallel of Vol 1's PRINCIPLES.md)
conv "$SRC/CONSTRUCTION.md" reg.tex

# References: optional until vol2-references.md exists; empty stub keeps the backmatter input valid
if [ -f "$SRC/vol2-references.md" ]; then conv "$SRC/vol2-references.md" refs.tex; else : > refs.tex; fi

# Chapters 1..19, one file per number. Fail loudly on a stale duplicate rather than glob the wrong one.
for n in $(seq 1 21); do
  matches=( "$SRC"/vol2-ch${n}-*.md )
  if [ "${#matches[@]}" -ne 1 ]; then
    printf 'ERROR: ch%s matches %d files:\n' "$n" "${#matches[@]}" >&2
    printf '  %s\n' "${matches[@]}" >&2
    echo "Resolve it (remove the stale draft) and re-run." >&2
    exit 1
  fi
  conv "${matches[0]}" "ch${n}.tex"
done

for pass in 1 2 3; do xelatex -interaction=nonstopmode full.tex >"pass${pass}.log" 2>&1; done
cp full.pdf "$SRC/vol2-volume.pdf"
echo "built: $SRC/vol2-volume.pdf"
