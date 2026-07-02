# Volume 1 PDF build

Single source of truth: the `vol1-*.md`, `PRINCIPLES.md`, and `vol1-references.md`
markdown set. This folder renders them to `vol1-volume.pdf`. The PDF is output only;
all edits flow through the markdown.

## Run
```
SRC=/path/to/markdown ./build.sh
```
Defaults `SRC` to `/mnt/user-data/outputs`. Writes `vol1-volume.pdf` into `SRC`.

## Pieces
- `build.sh`   — converts each chapter (pandoc, --no-highlight), assembles, runs xelatex x3
- `full.tex`   — master: cover, front matter (reading guide, TOC, register), parts, chapters, references
- `preamble.tex` — the design: 7x10in trim, TeX Gyre Pagella throughout, mono for code/slugs,
                   part dividers, chapter openers, running heads, TOC, code blocks
- `kennelhero.png` — cover image

## Requirements
xelatex (TeX Live, with TeX Gyre + Latin Modern fonts) and pandoc.
