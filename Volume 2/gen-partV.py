#!/usr/bin/env python3
"""Part V generator, v2: derive the policy reference from the canonical
schema/policy.toml.schema (itself derived from the parser structs). Single
source of truth: this tool reads the schema, it does not re-parse Rust."""
import json, re, pathlib, subprocess
REPO = pathlib.Path("/home/claude/kennel")
SCHEMA = json.load(open(REPO/"schema/policy.toml.schema"))
DEFS = SCHEMA["definitions"]
CORPUS = REPO/"toml"
DECORATION = {"reason", "threats"}
CROSSCUT_DEFS = {"threats"}   # documented once in Common forms

def defname(ref): return ref.split("/")[-1]

def classify(v):
    """(kind, target_def|None, enum|None) for a property schema node."""
    if "allOf" in v and len(v["allOf"]) == 1 and "$ref" in v["allOf"][0]:
        return ("table", defname(v["allOf"][0]["$ref"]), None)
    if "$ref" in v:
        return ("table", defname(v["$ref"]), None)
    if "oneOf" in v:
        for b in v["oneOf"]:
            if b.get("type") == "array":
                it = b.get("items", {})
                if "$ref" in it: return ("list_delta_table", defname(it["$ref"]), None)
                return ("list_delta_str", None, None)
        return ("list_delta_str", None, None)
    if "enum" in v: return ("enum", None, v["enum"])
    if v.get("type") == "array":
        it = v.get("items", {})
        if "$ref" in it: return ("array_table", defname(it["$ref"]), None)
        return ("array_str", None, None)
    if "$ref" in v.get("items", {}) if "items" in v else False:
        return ("array_table", defname(v["items"]["$ref"]), None)
    return ("scalar", v.get("type", "string"), None)

def placeholder(kind, enum, tgt):
    if enum: return " | ".join(f'"{e}"' for e in enum)
    if kind in ("array_str", "list_delta_str"): return '["..."]'
    if kind == "scalar" and tgt == "boolean": return "true"
    if kind == "scalar" and tgt == "integer": return "0"
    return '"..."' 

def fields_of(defn):
    props = DEFS[defn].get("properties", {})
    req = set(DEFS[defn].get("required", []))
    out = []
    for k, v in props.items():
        kind, tgt, enum = classify(v)
        cls = "decoration" if k in DECORATION else ("required" if k in req else "optional")
        out.append(dict(key=k, kind=kind, tgt=tgt, enum=enum, cls=cls,
                        type_node=v, desc=v.get("description", "").strip()))
    return out

def corpus_example(toml_path, header):
    """pull a real block from the corpus; header like '[[provides]]' or '[fs.tmp]'."""
    for f in CORPUS.rglob("policy.toml"):
        t = f.read_text()
        if header in t:
            lines = t.splitlines()
            for i, ln in enumerate(lines):
                if ln.strip() == header:
                    blk = [ln]
                    for nxt in lines[i+1:]:
                        if nxt.strip() == "" or nxt.lstrip().startswith("[") and nxt.strip() != header:
                            break
                        blk.append(nxt)
                    return "\n".join(blk).rstrip(), f.relative_to(REPO)
    return None, None

OUT, emitted = [], set()

def toml_header(path, arr): return f"[[{path}]]" if arr else f"[{path}]"

def emit_block(defn, path, arr, level, desc_override=None):
    if defn in emitted: return
    emitted.add(defn)
    flds = [f for f in fields_of(defn) if f["tgt"] not in CROSSCUT_DEFS or f["key"] != f["tgt"]]
    hdr = toml_header(path, arr)
    OUT.append(f"\n{'#'*min(level,4)} `{hdr}`\n")
    desc = desc_override or DEFS[defn].get("description", "")
    if desc: OUT.append(desc + "\n")

    own = [f for f in flds if f["kind"] in ("scalar","enum","array_str","list_delta_str")]
    subtables = [f for f in flds if f["kind"] == "table"]
    entries = [f for f in flds if f["kind"] in ("array_table","list_delta_table")]

    # options block: header + own fields grouped req/opt/decoration
    if own:
        OUT.append("```")
        OUT.append(hdr)
        for cls in ("required","optional","decoration"):
            grp = [f for f in own if f["cls"] == cls]
            if grp:
                OUT.append(f"# {cls}")
                for f in grp:
                    OUT.append(f"{f['key']:<8} = {placeholder(f['kind'], f['enum'], f['tgt'])}")
        OUT.append("```")

    # breadcrumb
    kids = [toml_header((path+'.'+f['key']), False) for f in subtables] + \
           [toml_header((path+'.'+f['key']), True) for f in entries]
    if kids: OUT.append("Contains: " + ", ".join(f"`{k}`" for k in kids) + ".\n")

    # field list for own fields -> definition list (no bullet dots)
    if own:
        OUT.append("")
    for f in own:
        ev = f" One of {', '.join('`'+e+'`' for e in f['enum'])}." if f['enum'] else ""
        OUT.append(f"`{f['key']}`")
        OUT.append(f":   {f['cls']}.{(' '+f['desc']) if f['desc'] else ''}{ev}")
        OUT.append("")

    # entry sub-blocks: their own fields as a definition list
    for f in entries:
        sub = toml_header(path+'.'+f['key'], True)
        note = "entries (or `{ add, remove }` increment)" if f["kind"]=="list_delta_table" else "entries"
        OUT.append(f"\n**`{sub}`** {note}, {f['cls']}:\n")
        for ef in fields_of(f["tgt"]):
            ev = f" One of {', '.join('`'+e+'`' for e in ef['enum'])}." if ef['enum'] else ""
            OUT.append(f"`{ef['key']}`")
            OUT.append(f":   {ef['cls']}.{(' '+ef['desc']) if ef['desc'] else ''}{ev}")
            OUT.append("")

    # worked example
    ex, src = corpus_example(None, hdr)
    if ex:
        OUT.append(f"\nExample, from `{src.parent}`:\n")
        OUT.append("```\n" + ex + "\n```")

    # recurse into container sub-tables
    for f in subtables:
        emit_block(f["tgt"], path+'.'+f["key"], False, level+1, desc_override=f["desc"])

# driver: top-level
top_props = SCHEMA["properties"]
top_req = set(SCHEMA.get("required", []))
ver = re.search(r'^version\s*=\s*"([^"]+)"', (REPO/"Cargo.toml").read_text(), re.M).group(1)
OUT.append(f"# 20. The policy language\n\n*Generated from `schema/policy.toml.schema`. Current as of {ver}.*\n")
# classify top-level props into sections (tables) and header scalars
for k, v in top_props.items():
    kind, tgt, enum = classify(v)
    if kind == "table":
        emit_block(tgt, k, False, 2)
    elif kind in ("array_table","list_delta_table"):
        emit_block(tgt, k, True, 2)

# Common forms
OUT.append("\n## Common forms\n")
th = DEFS.get("threats", {})
OUT.append("**Threat tags**: carried inline on any grant that can widen surface, as `threats = { exposed = [...], mitigated = [...] }`.")
OUT.append("\n**The increment**: any list field also accepts `[[<list>.add]]` / `[[<list>.remove]]`, folded over the inherited list at compile.")

md = "\n".join(OUT)
pathlib.Path("/mnt/user-data/outputs/vol2-ch20-policy-language.md").write_text(md)
print(f"blocks: {len(emitted)} | words: {len(md.split())} | em-dashes: {md.count(chr(8212))} | enums rendered: {md.count('One of')}")
