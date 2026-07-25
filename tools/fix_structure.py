#!/usr/bin/env python3
"""Paso 4: limpieza estructural.

- etiquetas de sección escritas como texto plano -> {comment: ...}
- restos de OpenSong: líneas de acordes con prefijo '.'  -> acordes entre []
- basura de conversión: <<>>, <<<>>>, ~~~~
- 'Tempo: 73' / 'Scripture Reference(s): ...' -> directivas de cabecera
- ficheros sin ninguna sección -> se etiquetan los bloques
"""
import re, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIRS = ["es/himnos", "es/popular", "en/hymns", "en/popular", "pt/hinos"]

LABEL = re.compile(
    r'^(chorus|verse|bridge|refrain|intro|outro|ending|tag|pre.?chorus|interlude'
    r'|instrumental|vamp|coro|verso|estrofa|puente|pre.?coro|final|estribillo'
    r'|refr[aã]o|ponte)\s*[:.]?\s*(\d+)?\s*[:.]?\s*(\(?\s*\d+\s*x\s*\)?)?$', re.I)
JUNK = re.compile(r'^\s*(<<+>>+|~{3,}|-{3,}|={3,})\s*$')
OPENSONG_CHORDS = re.compile(r'^\.\s+(.*)$')
CHORDISH = re.compile(r'^[A-G](#|b)?[A-Za-z0-9#/+()°.]*$')


# etiqueta canónica por idioma de la carpeta
L10N = {
    "chorus":   {"en": "Chorus", "es": "Coro", "pt": "Refrão"},
    "verse":    {"en": "Verse", "es": "Verso", "pt": "Verso"},
    "bridge":   {"en": "Bridge", "es": "Puente", "pt": "Ponte"},
    "refrain":  {"en": "Chorus", "es": "Coro", "pt": "Refrão"},
    "intro":    {"en": "Intro", "es": "Intro", "pt": "Intro"},
    "outro":    {"en": "Outro", "es": "Final", "pt": "Final"},
    "ending":   {"en": "Ending", "es": "Final", "pt": "Final"},
    "tag":      {"en": "Tag", "es": "Tag", "pt": "Tag"},
    "prechorus": {"en": "Pre-Chorus", "es": "Pre-Coro", "pt": "Pré-Refrão"},
    "interlude": {"en": "Interlude", "es": "Interludio", "pt": "Interlúdio"},
    "instrumental": {"en": "Instrumental", "es": "Instrumental", "pt": "Instrumental"},
    "vamp":     {"en": "Vamp", "es": "Vamp", "pt": "Vamp"},
    "coro":     {"en": "Chorus", "es": "Coro", "pt": "Refrão"},
    "verso":    {"en": "Verse", "es": "Verso", "pt": "Verso"},
    "estrofa":  {"en": "Verse", "es": "Verso", "pt": "Verso"},
    "puente":   {"en": "Bridge", "es": "Puente", "pt": "Ponte"},
    "precoro":  {"en": "Pre-Chorus", "es": "Pre-Coro", "pt": "Pré-Refrão"},
    "final":    {"en": "Outro", "es": "Final", "pt": "Final"},
    "estribillo": {"en": "Chorus", "es": "Coro", "pt": "Refrão"},
    "refrao":   {"en": "Chorus", "es": "Coro", "pt": "Refrão"},
    "refrão":   {"en": "Chorus", "es": "Coro", "pt": "Refrão"},
    "ponte":    {"en": "Bridge", "es": "Puente", "pt": "Ponte"},
}


def canon_label(s: str, lang: str = "en") -> str:
    m = LABEL.match(s)
    word, num, rep = m.group(1), m.group(2), m.group(3)
    slug = re.sub(r'[^a-zãâ]', '', word.lower())
    word = L10N.get(slug, {}).get(lang, word.capitalize())
    out = word
    if num:
        out += " " + num
    if rep:
        out += " (" + re.sub(r'\s+', '', rep).strip("()") + ")"
    return out


def norm(s: str) -> str:
    s = re.sub(r'\[[^\]]*\]', '', s)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r'[^a-z0-9 ]', '', s.lower()).strip()


def process(path: Path) -> bool:
    lang = path.parts[-3]
    src = path.read_text(encoding="utf-8")
    orig = src
    src = src.replace("ʖ", "¿")

    lines = src.split("\n")
    out, tempo, scripture = [], None, []
    for line in lines:
        s = line.strip()
        if JUNK.match(s):
            continue
        m = re.match(r'^Tempo:\s*(\d+)\s*$', s, re.I)
        if m:
            tempo = m.group(1); continue
        m = re.match(r'^Scripture References?\(?s?\)?:\s*(.+)$', s, re.I)
        if m:
            scripture.append(m.group(1).strip()); continue
        # línea de acordes estilo OpenSong:  ". C9 D"
        m = OPENSONG_CHORDS.match(line)
        if m and m.group(1).strip():
            toks = m.group(1).split()
            if toks and all(CHORDISH.match(t) or t in ("|", "/", "->") for t in toks):
                out.append("  ".join(f"[{t}]" for t in toks if CHORDISH.match(t)))
                continue
        # etiqueta de sección como texto plano
        if s and not s.startswith("{") and "[" not in s and LABEL.match(s):
            lab = canon_label(s, lang)
            # si justo antes hay un {comment:}, la etiqueta explícita lo sustituye
            j = len(out) - 1
            while j >= 0 and not out[j].strip():
                j -= 1
            if j >= 0 and re.match(r'^\{comment:', out[j].strip()):
                out[j] = "{comment: %s}" % lab
            else:
                out.append("{comment: %s}" % lab)
            continue
        out.append(line)

    # cabecera: tempo y referencia bíblica
    if tempo or scripture:
        hdr = 0
        for i, l in enumerate(out[:10]):
            if re.match(r'^\{(title|artist|by|t|key|ccli)\s*:', l.strip()):
                hdr = i + 1
        extra = []
        if tempo:
            extra.append("{tempo: %s}" % tempo)
        for sc in scripture:
            extra.append("{meta: scripture %s}" % sc)
        out[hdr:hdr] = extra

    src = "\n".join(out)
    src = re.sub(r'([^\n])\n(\{comment:)', r'\1\n\n\2', src)
    src = re.sub(r'(^\{(?!comment[:\s])[a-z_]+:[^\n]*\})\n(?=[^{\n])', r'\1\n\n',
                 src, flags=re.M)
    src = re.sub(r'\n{3,}', '\n\n', src).rstrip() + "\n"

    if src != orig:
        path.write_text(src, encoding="utf-8")
        return True
    return False


def add_sections(path: Path) -> bool:
    lang = path.parts[-3]
    src = path.read_text(encoding="utf-8")
    if re.search(r'^\{comment:', src, re.M):
        return False
    m = re.search(r'^\{title:\s*(.*?)\}', src, re.M)
    title = norm(m.group(1)) if m else ""
    head, body = [], []
    for line in src.split("\n"):
        (head if (line.strip().startswith("{") and not body) else body).append(line)
    blocks = re.split(r'\n\s*\n', "\n".join(body).strip())
    blocks = [b for b in blocks if b.strip()]
    if not blocks:
        return False
    keys = [norm(b) for b in blocks]
    seen = {}
    labels, vn = [], 0
    for i, (b, k) in enumerate(zip(blocks, keys)):
        if k in seen:
            labels.append(labels[seen[k]])
            continue
        seen[k] = i
        repeated = keys.count(k) > 1
        is_chorus = repeated or (i > 0 and title and title in k)
        cho = L10N["chorus"][lang]
        ver = L10N["verse"][lang]
        if is_chorus and not any(l.startswith(cho) for l in labels):
            labels.append(cho)
        else:
            vn += 1
            labels.append(f"{ver} {vn}")
    parts = [f"{{comment: {l}}}\n{b}" for l, b in zip(labels, blocks)]
    new = "\n".join(head).rstrip() + "\n\n" + "\n\n".join(parts) + "\n"
    path.write_text(new, encoding="utf-8")
    return True


def main():
    a = b = 0
    for d in DIRS:
        for f in sorted((ROOT / d).glob("*.cho")):
            if process(f):
                a += 1
    for d in DIRS:
        for f in sorted((ROOT / d).glob("*.cho")):
            if add_sections(f):
                b += 1
    print(f"Ficheros limpiados: {a}")
    print(f"Ficheros con secciones añadidas: {b}")


if __name__ == "__main__":
    main()
