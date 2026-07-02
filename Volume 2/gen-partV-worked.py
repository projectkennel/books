#!/usr/bin/env python3
"""Part V chapter 2: the lineage walkthrough. Renders the real shipped
base-confined -> interactive(template) -> interactive(policy) chain, fragments
expanded at their include points. Prose is the files' own comments (single
source); signatures masked; nothing authored. Honors the author's comment
vocabulary: === banner (tier intro), # --- divider (### heading), flush-left #
prose (leading) or in-section doc, # then indented text (commented-out example),
indented # (inside a code block), inline trailing # (stays on the line)."""
import re, pathlib, textwrap
REPO = pathlib.Path("/home/claude/kennel")
T = REPO / "toml"
def frag(name): return T / "fragments" / name / "policy.toml"

CHAIN = [
    ("base-confined", T/"templates/base-confined/policy.toml", "the floor every kennel stands on"),
    ("interactive (template)", T/"templates/interactive/policy.toml", "the floor made into a usable human shell"),
    ("interactive (policy)", T/"policies/interactive/policy.toml", "the thin leaf that pins a workload"),
]

def split_banner(text):
    lines = text.splitlines(); i = 0; banner = []
    while i < len(lines) and (lines[i].lstrip().startswith("#") or lines[i].strip() == ""):
        banner.append(lines[i]); i += 1
    return banner, "\n".join(lines[i:]).strip()

def banner_prose(banner):
    out, run, kind = [], [], None
    def flush():
        nonlocal run, kind
        if not run: return
        if kind == "prose":
            p = " ".join(run)
            if p: out.append(p)
        elif kind == "commentcode":
            code = textwrap.dedent("\n".join(run)).strip("\n")
            out.append("```\n" + code + "\n```")
        run, kind = [], None
    for l in banner:
        s = l.strip()
        if not s.startswith("#"):
            flush(); continue
        inner = s[1:]                       # after the leading '#'
        body = inner.strip()
        if not body or set(body) <= set("="):   # rule / blank-comment
            flush(); continue
        if inner.startswith("  "):          # '#' then indented = commented-out example
            if kind and kind != "commentcode": flush()
            kind = "commentcode"; run.append(inner)
        else:
            if kind and kind != "prose": flush()
            kind = "prose"; run.append(body)
    flush()
    return "\n\n".join(out)

def mask_sig(body):
    return re.sub(r'signature = "[^"]*"', 'signature = "...envelope elided in print..."', body)

def _classify(line):
    if line.strip() == "": return "blank"
    if not line.startswith("#"):                 # not flush-left: TOML, or indented # inside code
        return "toml"
    inner = line[1:]                             # flush-left (column 0) standalone comment
    body = inner.strip()
    if set(body) <= set("="): return "banner"
    if re.match(r"^-{2,}", body): return "heading"
    if inner.startswith("  "): return "commentcode"
    return "prose"

def _clean_prose(run):
    out = []
    for l in run:
        s = l.strip().lstrip("#").strip()
        if set(s) <= set("-= "): continue
        out.append(s)
    return " ".join(out)

def render_body(body):
    out, run, kind = [], [], None
    mode = "leading"
    def flush():
        nonlocal run, kind
        if not run: return
        if kind == "prose":
            p = _clean_prose(run)
            if p: out.append("\n" + p)
        elif kind == "toml":
            out.append("\n```\n" + mask_sig("\n".join(run)) + "\n```")
        elif kind == "commentcode":
            code = textwrap.dedent("\n".join(l[1:] for l in run)).strip("\n")
            out.append("\n```\n" + code + "\n```")
        run, kind = [], None
    for l in body.splitlines():
        k = _classify(l)
        if k in ("blank", "banner"):
            flush(); continue
        if k == "heading":
            flush()
            t = l.strip().lstrip("#").strip()
            t = re.sub(r"^-+\s*", "", t); t = re.sub(r"\s*-+$", "", t)
            out.append(f"\n### {t}\n"); mode = "leading"; continue
        if k == "commentcode":
            flush(); kind = "commentcode"; run.append(l); flush(); continue
        if k == "toml":
            if l.lstrip().startswith("["): mode = "inside"
            if kind and kind != "toml": flush()
            kind = "toml"; run.append(l); continue
        # prose
        if mode == "inside":
            if kind and kind != "toml": flush()
            kind = "toml"; run.append(l)
        else:
            if kind and kind != "prose": flush()
            kind = "prose"; run.append(l)
    flush()
    return out

def includes(body):
    m = re.search(r'include = \[([^\]]*)\]', body)
    return re.findall(r'"([^"]+)"', m.group(1)) if m else []

def grants_of(fragtext):
    pairs = re.findall(r'path = "([^"]+)"\s*\n\s*(?:#[^\n]*\n\s*)*reason = "([^"]+)"', fragtext)
    if pairs:
        return pairs
    return [(p, None) for p in re.findall(r'path = "([^"]+)"', fragtext)]

OUT = ["# 21. Worked examples\n"]
OUT.append("A single confined thing, followed from the floor to a running shell. Each tier is a real "
           "shipped file; the prose is the file's own. Read top to bottom and you watch confinement "
           "accrete: the floor denies, the template widens it four different ways, the leaf pins it.\n")

for label, path, role in CHAIN:
    banner, body = split_banner(path.read_text())
    OUT.append(f"\n## `{label}` — {role}\n")
    OUT.append(banner_prose(banner))
    OUT.extend(render_body(body))
    for fr in includes(body):
        fp = frag(fr)
        if not fp.exists():
            OUT.append(f"\n*Fragment `{fr}` not found in corpus.*"); continue
        fb, _ = split_banner(fp.read_text())
        OUT.append(f"\n### `include = \"{fr}\"`\n")
        OUT.append(banner_prose(fb))
        g = grants_of(fp.read_text())
        if g:
            OUT.append("\nAdds to the exec floor:\n")
            for p, r in g[:12]:
                OUT.append(f"- `{p}` ({r})" if r else f"- `{p}`")
            if len(g) > 12: OUT.append(f"- ...and {len(g)-12} more")
            OUT.append("")

md = "\n".join(OUT)
pathlib.Path("/mnt/user-data/outputs/vol2-ch21-worked-examples.md").write_text(md)
print(f"tiers: {len(CHAIN)} | words: {len(md.split())} | em-dashes: {md.count(chr(8212))} | "
      f"sig bytes leaked: {md.count('BEGIN SSH SIGNATURE')} | fragments: {md.count('### `include')}")
