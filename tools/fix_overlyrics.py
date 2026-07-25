#!/usr/bin/env python3
"""Paso 6: convierte los restos de formato 'acordes sobre la letra' a ChordPro
inline, y pone entre corchetes las líneas de acordes sueltas."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_N = r"[A-G](?:#|b)?"
_M = (r"(?:m|min|maj|M|aug|dim|\+|°|sus[24]?|add[#b]?\d+|no3|alt"
      r"|b5|#5|b9|#9|#11|b13|\d+|\([^)]*\))")
CH = re.compile(rf'^{_N}{_M}*(?:/{_N})?$')
SEP = {'/', '//', '///', '-', '|'}


def expand_tabs(s, width=8):
    out = []
    for c in s:
        if c == "\t":
            out.append(" " * (width - len(out) % width))
        else:
            out.append(c)
    return "".join(out)


def is_chord_line(s):
    if not s.strip() or "[" in s or s.strip().startswith("{"):
        return False
    toks = [t for t in re.split(r'\s+', s.strip()) if t]
    if not toks or len(toks) > 14:
        return False
    return all(CH.match(t) or t in SEP for t in toks) and any(CH.match(t) for t in toks)


def merge(chord_line, lyric_line):
    """Inserta los acordes en la letra según su columna."""
    cl = expand_tabs(chord_line)
    ly = expand_tabs(lyric_line)
    marks = [(m.start(), m.group(0)) for m in re.finditer(r'\S+', cl)
             if CH.match(m.group(0))]
    out, prev = [], 0
    for col, ch in marks:
        col = min(col, len(ly))
        out.append(ly[prev:col])
        out.append(f"[{ch}]")
        prev = col
    out.append(ly[prev:])
    return "".join(out).rstrip()


def bracket_line(s):
    toks = [t for t in re.split(r'(\s+)', expand_tabs(s)) if t]
    return "".join(f"[{t}]" if CH.match(t.strip()) and t.strip() else t
                   for t in toks).rstrip()


def process(path: Path) -> bool:
    src = path.read_text(encoding="utf-8")
    lines = src.split("\n")
    out, i, changed = [], 0, False
    while i < len(lines):
        cur = lines[i]
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if is_chord_line(cur):
            has_lyric = (nxt.strip() and not nxt.strip().startswith("{")
                         and "[" not in nxt and not is_chord_line(nxt))
            if has_lyric:
                out.append(merge(cur, nxt))
                i += 2
            else:
                out.append(bracket_line(cur))
                i += 1
            changed = True
            continue
        out.append(cur)
        i += 1
    if changed:
        path.write_text("\n".join(out), encoding="utf-8")
    return changed


if __name__ == "__main__":
    n = 0
    for d in ["es/himnos", "es/popular", "en/hymns", "en/popular", "pt/hinos"]:
        for f in sorted((ROOT / d).glob("*.cho")):
            if process(f):
                n += 1
                print("  ", f.relative_to(ROOT))
    print(f"Ficheros convertidos: {n}")
