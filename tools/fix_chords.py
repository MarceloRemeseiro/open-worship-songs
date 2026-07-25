#!/usr/bin/env python3
"""Paso 1: normaliza tokens de acorde inválidos y estructuras rotas."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --- sustituciones literales por fichero (ambigüedades resueltas a mano) ---
PER_FILE = {
    "en/popular/spirit-move.cho": [("[[Cm]]", "[Cm]")],
    "en/popular/runnin.cho": [("every []G#mtime", "every [G#m]time")],
    "en/popular/forever-reign.cho": [("You are hoG/Bpe", "You are ho[G/B]pe")],
    "en/hymns/it-is-well.cho": [("(It is wel[t]l)", "(It is well)")],
    "en/popular/when-the-cold-wind-blows.cho": [
        ("[F]Takes so long [D/F#G]to learn", "[F]Takes so long [D/F#]to [G]learn")],
    "en/popular/new-wine.cho": [
        ("[Eb / Bb5]", "[Eb]   [Bb5]"),
        ("out of me[Bb     F/A]", "out of me[Bb]   [F/A]")],
    "en/popular/seek-ye-first.cho": [
        ("[G/B]door shall be [M]opened", "[G/B]door shall be [Am]opened")],
    "es/popular/asi-como-david-danzaba.cho": [("[¡Gózate!]", "(¡Gózate!)")],
    "en/popular/heal-our-land-come-and-move.cho": [("[/]", " / "), ("[|]", " | ")],
    "en/popular/what-child-is-this.cho": [
        ("The silent Word is pleading.[Chorus]", "The silent Word is pleading.")],
}

# --- normalización global de tokens de acorde ---
TOKEN_MAP = {
    # notación maj7 con acento circunflejo / erratas
    "C^7": "Cmaj7", "F^7add2": "Fmaj7add2", "F^7 add2": "Fmaj7add2",
    "Cma7": "Cmaj7", "Camj7": "Cmaj7", "Ema7/D#": "Emaj7/D#",
    # shift no pulsado: '3' en vez de '#'
    "C3m": "C#m", "C3m7": "C#m7", "G37": "G#7", "F3maj7": "F#maj7",
    # bajos imposibles (tríada menor como bajo)
    "G/Dm": "G/D", "A/C#m": "A/C#", "E/F#m": "E/F#", "E/G#m": "E/G#",
    "Db/Fm": "Db/F", "E/Bsus": "E/B", "A/Bsus": "A/B",
    # separadores y erratas varias
    "DF#": "D/F#", "D.F#": "D/F#", "D2F#": "D2/F#", "E,G#": "E/G#",
    "D/2": "D2", "Dd": "D", "Ebs": "Eb2", "Fm#7": "F#m7", "C#/7": "C#m7",
    "(A2)": "A2", "A7Sus4": "A7sus4", "asus2": "Asus2", "em7": "Em7",
    "gm7": "Gm7", "c7sus": "C7sus",
}
# etiquetas de sección escritas como si fueran acordes
SECTION_TOKENS = {"Intro", "Outro", "Bridge", "Chorus", "Verse", "Verse 2",
                  "Instrumental", "Pre-Chorus", "Tag"}

SPACED_SLASH = re.compile(r"^([A-G](?:#|b)?[^\s/]*)\s*/\s*([A-G](?:#|b)?[^\s/]*)$")
# cadena de compases: contiene '|' o varios acordes separados por espacios
MEASURE = re.compile(r"^[|\s/]*[A-G].*[|/].*$")
CHORD_TOK = re.compile(r"^[A-G](#|b)?[a-zA-Z0-9#()/+°.]*$")


def split_measure(inner: str) -> str:
    """'| Bb /// | Gm /// |' -> '| [Bb] /// | [Gm] /// |'"""
    out = []
    for tok in re.split(r"(\s+)", inner):
        if tok.strip() and CHORD_TOK.match(tok.strip()):
            out.append(f"[{tok.strip()}]")
        else:
            out.append(tok)
    return "".join(out)


def fix_file(path: Path) -> bool:
    rel = str(path.relative_to(ROOT))
    src = path.read_text(encoding="utf-8")
    orig = src

    for a, b in PER_FILE.get(rel, []):
        src = src.replace(a, b)

    lines = src.split("\n")
    out = []
    for line in lines:
        if line.strip().startswith("{"):
            out.append(line)
            continue
        # bracket externo envolviendo una línea de compases: [| [F2] / / |]
        m = re.match(r"^\s*\[(\|.*\|)\]\s*$", line)
        if m and "[" in m.group(1):
            line = m.group(1)

        def repl(mo):
            tok = mo.group(1)
            t = tok.strip()
            if t in TOKEN_MAP:
                return f"[{TOKEN_MAP[t]}]"
            if t in SECTION_TOKENS:
                return f"\x00SECTION:{t}\x00"
            sm = SPACED_SLASH.match(t)
            if sm:
                return f"[{sm.group(1)}/{sm.group(2)}]"
            if ("|" in t or "/" in t) and MEASURE.match(t) and " " in t:
                return split_measure(t)
            return mo.group(0)

        line = re.sub(r"\[([^\]]*)\]", repl, line)
        out.append(line)

    src = "\n".join(out)
    # etiquetas de sección -> directiva {comment:} en su propia línea
    src = re.sub(r"^\s*\x00SECTION:([^\x00]+)\x00\s*$", r"{comment: \1}", src, flags=re.M)
    src = re.sub(r"\x00SECTION:([^\x00]+)\x00", r"", src)
    # limpieza de brackets vacíos residuales
    src = re.sub(r"\[\s*\]", "", src)

    if src != orig:
        path.write_text(src, encoding="utf-8")
        return True
    return False


def main():
    n = 0
    for d in ["es/himnos", "es/popular", "en/hymns", "en/popular", "pt/hinos"]:
        for f in sorted((ROOT / d).glob("*.cho")):
            if fix_file(f):
                n += 1
    print(f"Ficheros modificados: {n}")


if __name__ == "__main__":
    main()
