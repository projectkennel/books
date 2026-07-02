# Volume 2 PDF build

Single source of truth: the `vol2-*.md`, `CONSTRUCTION.md`, and (when it exists)
`vol2-references.md` markdown set. This folder renders them to `vol2-volume.pdf`.
The PDF is output only; all edits flow through the markdown.

## Run
```
SRC=/path/to/markdown ./build.sh
```
Defaults `SRC` to `/mnt/user-data/outputs`. Writes `vol2-volume.pdf` into `SRC`.

## Pieces
- `build.sh`   — converts each chapter (pandoc, --no-highlight), assembles, runs xelatex x3
- `full.tex`   — master: cover, front matter (reading guide, TOC, register), four parts, chapters, references
- `preamble.tex` — the design (identical to Vol 1 but for the PDF title): 7x10in trim, TeX Gyre
                   Pagella throughout, mono for code/slugs, part dividers, chapter openers,
                   running heads, TOC, code blocks
- `kennelhero-vol2.jpg` — cover image (Tux locked in the kennel)

## Differences from the Vol 1 pipeline
- Register is `CONSTRUCTION.md` (Vol 1 uses `PRINCIPLES.md`).
- Four parts, chapters 1..19 (Vol 1 is three parts, 1..16).
- `vol2-references.md` is optional: until it exists the back matter renders empty.
- The chapter loop fails loudly if a chapter number matches more than one markdown file,
  rather than globbing a stale draft. Resolve the duplicate and re-run.

## Cover placeholders to set
- Subtitle: currently `Mechanism and Construction on Linux`.
- Date/place line: currently `Schalkhaar, June 2026`.

## Requirements
xelatex (TeX Live, with TeX Gyre + Latin Modern fonts) and pandoc.
