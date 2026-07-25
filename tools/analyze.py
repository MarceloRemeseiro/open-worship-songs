#!/usr/bin/env python3
"""Analiza el catálogo ChordPro y reporta problemas por categoría."""
import re, sys, json, collections, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIRS = ["es/himnos", "es/popular", "en/hymns", "en/popular", "pt/hinos"]

NOTE = r"[A-G](?:#|b)?"
MOD = (r"(?:m|min|maj|Maj|M|aug|dim|\+|°|o|sus[24]?|add[#b]?\d+|no3|alt"
       r"|b5|#5|b9|#9|#11|b13|6/9|\d+|\([^)]*\))")
CHORD_RE = re.compile(rf"^{NOTE}{MOD}*(?:/{NOTE})?$")
BRACKET_RE = re.compile(r"\[([^\]]*)\]")
DIRECTIVE_RE = re.compile(r"^\{(\w+)\s*:\s*(.*?)\}$")


def is_chord(tok: str) -> bool:
    t = tok.strip()
    if not t:
        return False
    if t in ("N.C.", "NC", "-", "%", "|"):
        return True
    return bool(CHORD_RE.match(t))


def analyze(path: Path):
    raw = path.read_text(encoding="utf-8")
    lines = raw.split("\n")
    info = {
        "path": str(path.relative_to(ROOT)),
        "title": None, "artist": None, "key": None,
        "sections": 0, "lyric_lines": 0, "chords": 0,
        "issues": [], "bad_tokens": [], "chord_set": [],
    }
    chord_counter = collections.Counter()
    for ln in lines:
        t = ln.strip()
        m = DIRECTIVE_RE.match(t)
        if m:
            d, v = m.group(1).lower(), m.group(2).strip()
            if d in ("title", "t"): info["title"] = v
            elif d in ("artist", "by"): info["artist"] = v
            elif d == "key": info["key"] = v
            elif d in ("comment", "c"): info["sections"] += 1
            continue
        if t.startswith("{"):
            info["issues"].append(f"directiva-malformada:{t[:40]}")
            continue
        if not t:
            continue
        if t.count("[") != t.count("]"):
            info["issues"].append("corchete-desbalanceado")
        for tok in BRACKET_RE.findall(t):
            info["chords"] += 1
            if is_chord(tok):
                chord_counter[tok.strip()] += 1
            else:
                info["bad_tokens"].append(tok)
        stripped = BRACKET_RE.sub("", t).strip()
        if stripped:
            info["lyric_lines"] += 1

    info["chord_set"] = sorted(chord_counter)
    # --- categorías de problemas ---
    if not info["title"]: info["issues"].append("sin-titulo")
    if not info["key"]: info["issues"].append("sin-key")
    if not info["artist"]: info["issues"].append("sin-artist")
    if info["sections"] == 0: info["issues"].append("sin-secciones")
    if info["chords"] == 0: info["issues"].append("sin-acordes")
    if info["bad_tokens"]: info["issues"].append("acorde-invalido")
    if info["lyric_lines"] == 0: info["issues"].append("sin-letra")

    # chord pegado al final de palabra seguido de espacio: "the[C] Lord"
    glued = len(re.findall(r"\w\[[^\]]+\]\s", raw))
    if glued: info["issues"].append("acorde-antes-de-espacio")
    info["glued"] = glued

    # chord en medio de palabra: "coron[F]ad"
    midword = len(re.findall(r"\w\[[^\]]+\]\w", raw))
    if midword: info["issues"].append("acorde-en-medio-de-palabra")
    info["midword"] = midword

    # metadatos sueltos en el cuerpo
    if re.search(r"^(Tempo|Scripture Reference|CCLI|Copyright|Key of)\s*[:#]", raw, re.M):
        info["issues"].append("metadata-en-cuerpo")

    # densidad: muy pocos acordes para muchas líneas
    if info["lyric_lines"] > 6 and info["chords"] < info["lyric_lines"] * 0.5:
        info["issues"].append("pocos-acordes")
    return info


def main():
    all_info = []
    for d in DIRS:
        for f in sorted((ROOT / d).glob("*.cho")):
            all_info.append(analyze(f))
    counts = collections.Counter()
    for i in all_info:
        for iss in set(i["issues"]):
            counts[iss] += 1
    print(f"Total canciones: {len(all_info)}\n")
    print("--- Problemas (nº de ficheros) ---")
    for k, v in counts.most_common():
        print(f"{v:5d}  {k}")
    print(f"\nTotal acordes 'pegados antes de espacio': {sum(i['glued'] for i in all_info)}")
    print(f"Total acordes en medio de palabra:        {sum(i['midword'] for i in all_info)}")
    bad = collections.Counter()
    for i in all_info:
        for t in i["bad_tokens"]:
            bad[t] += 1
    print(f"\n--- Tokens no reconocidos como acorde ({len(bad)} distintos) ---")
    for k, v in bad.most_common(60):
        print(f"{v:5d}  {k!r}")
    (ROOT / "tools/report.json").write_text(json.dumps(all_info, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
