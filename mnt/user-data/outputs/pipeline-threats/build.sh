#!/usr/bin/env bash
# Build the standalone Threat Catalogue PDF from the neutralised markdown.
set -euo pipefail
SRC="${SRC:-/mnt/user-data/outputs}"
cd "$(dirname "$0")"

conv () {  # $1=markdown  $2=out.tex
  pandoc -f markdown -t latex --no-highlight --top-level-division=chapter "$1" \
  | sed 's/\\begin{verbatim}/\\begin{kennelcode}/g; s/\\end{verbatim}/\\end{kennelcode}/g' \
  | sed 's/\\texorpdfstring{\\texttt{\([^}]*\)}}/\\texorpdfstring{\1}/g' \
  | sed 's/section{\\texttt{\([^}]*\)}}/section{\1}/g' > "$2"
}

# front matter (title-page prose) and body
pandoc -f markdown -t latex --no-highlight "$SRC/threats-frontmatter.md" \
  | sed 's/\\texorpdfstring{\\texttt{\([^}]*\)}}/\\texorpdfstring{\1}/g' > frontbody.tex
# Split the body at the Part 2 marker so each part gets a real divider.
# body1 = in-scope families; body2 = X-series; body3 = appendices + versioning.
awk '/^# Part 2 —/{exit} {print}' "$SRC/threats-body.md" > _body1.md
awk '/^# Part 2 —/{f=1} f && /^# Appendix A/{exit} f{print}' "$SRC/threats-body.md" > _body2.md
awk '/^# Appendix A/{f=1} f{print}' "$SRC/threats-body.md" > _body3.md
# strip the now-redundant "# Part 2 — Out of scope (...)" H1 from body2 (the divider carries it)
sed -i '0,/^# Part 2 —.*/{/^# Part 2 —.*/d}' _body2.md
conv _body1.md body1.tex
conv _body2.md body2.tex
conv _body3.md body3.tex

for pass in 1 2 3; do xelatex -interaction=nonstopmode full.tex >"pass${pass}.log" 2>&1; done
cp full.pdf "$SRC/threat-catalogue.pdf"
echo "built: $SRC/threat-catalogue.pdf"
