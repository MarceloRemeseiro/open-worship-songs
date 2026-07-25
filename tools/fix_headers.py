#!/usr/bin/env python3
"""Paso 5: metadatos sueltos de cabecera -> directivas, y etiquetado del
bloque inicial que se había quedado sin {comment:}."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIRS = ["es/himnos", "es/popular", "en/hymns", "en/popular", "pt/hinos"]

# (patrón, plantilla de directiva)  -- None = eliminar la línea
META = [
    (r'^(?:BPM|Temo|Tempo)\s*:\s*(\d+)', "{tempo: %s}"),
    (r'^(?:Time|Meter)\s*:\s*(\d+\s*/\s*\d+)', "{time: %s}"),
    (r'^Original Capo\s*:\s*(\d+)', "{capo: %s}"),
    (r'^Guitar Capo\s*(\d+)', "{capo: %s}"),
    (r'^Album:\s*Capo\s*(\d+)', "{capo: %s}"),
    (r'^(?:CANT|Cant)\s*Key\s*:\s*(\S.*)$', "{meta: cant_key %s}"),
    (r'^Church\s*Key\s*:\s*(\S.*)$', "{meta: church_key %s}"),
    (r'^Origin\w*\s*Key\(?s?\)?\s*:\s*(\S.*)$', "{meta: original_key %s}"),
    (r'^Recom\w*\s*Key\(?s?\)?\s*:\s*(\S.*)$', "{meta: recommended_keys %s}"),
    (r'^Song Played\s+(\S.*)$', "{meta: original_key %s}"),
    (r'^Scripture\s*(?:Refr?e?n?ce)?\s*:\s*(\S.*)$', "{meta: scripture %s}"),
    (r'^Topic\s*:\s*(\S.*)$', "{meta: topic %s}"),
    (r'^Books?\s*:\s*(\S.*)$', "{meta: book %s}"),
    (r'^URL\s*:\s*(\S.*)$', "{meta: url %s}"),
    (r'^Writers?\(?s?\)?\s*:\s*(\S.*)$', "{artist: %s}"),
    (r'^(?:CANT|Church\s*Key|CANT\s*Key)\s*:\s*$', None),
]

# etiquetas de sección adicionales que la pasada anterior no reconocía
EXTRA_LABEL = [
    (r'^-+\s*(.+?)\s*-+\s*:?$', r'\1'),
    (r'^#\s*(.+)$', r'\1'),
    (r'^Choris\s*:?$', 'Chorus'),
    (r'^In between\s*:?$', 'Interlude'),
    (r'^Pre\s*:?$', 'Pre-Chorus'),
    (r'^Intro\s*[/\w]*\s*(?:\(|x|X)?[\w\s]*\)?\s*:$', 'Intro'),
    (r'^(.+?)\s+(Chorus|Bridge|Verse)\s*:$', r'\2 (\1)'),
    (r'^(Chorus|Bridge|Verse|Intro|Tag|Outro)\s*(\d*)\s*\(([^)]*)\)\s*:$', r'\1 \2 (\3)'),
]
LANG_LABEL = {"es": {"Chorus": "Coro", "Verse": "Verso", "Bridge": "Puente",
                     "Intro": "Intro", "Interlude": "Interludio",
                     "Pre-Chorus": "Pre-Coro", "Outro": "Final"},
              "pt": {"Chorus": "Refrão", "Verse": "Verso", "Bridge": "Ponte",
                     "Intro": "Intro", "Interlude": "Interlúdio",
                     "Pre-Chorus": "Pré-Refrão", "Outro": "Final"},
              "en": {}}


def localize(lab, lang):
    m = re.match(r'^(Chorus|Verse|Bridge|Intro|Interlude|Pre-Chorus|Outro)(\b.*)$', lab)
    if not m:
        return lab
    return LANG_LABEL[lang].get(m.group(1), m.group(1)) + m.group(2)


def process(path: Path) -> bool:
    lang = path.parts[-3]
    src = path.read_text(encoding="utf-8")
    orig = src
    lines = src.split("\n")
    has_artist = bool(re.search(r'^\{artist:', src, re.M))

    head_end = len(lines)
    for i, l in enumerate(lines):
        if l.strip().startswith("{comment:"):
            head_end = i
            break

    directives, body = [], []
    for i, line in enumerate(lines):
        s = line.strip()
        if i < head_end and s and not s.startswith("{") and "[" not in s:
            hit = False
            for pat, tpl in META:
                m = re.match(pat, s, re.I)
                if m:
                    hit = True
                    if tpl is None:
                        break
                    if tpl.startswith("{artist") and has_artist:
                        directives.append("{meta: writers %s}" % m.group(1))
                    else:
                        directives.append(tpl % m.group(1).strip())
                    break
            if hit:
                continue
            for pat, rep in EXTRA_LABEL:
                if re.match(pat, s):
                    lab = re.sub(pat, rep, s).strip()
                    if lab and len(lab) < 45:
                        body.append("{comment: %s}" % localize(lab, lang))
                        break
            else:
                body.append(line)
            continue
        body.append(line)

    # reinsertar las directivas recuperadas tras la cabecera existente
    if directives:
        pos = 0
        for i, l in enumerate(body[:12]):
            if re.match(r'^\{(title|artist|by|t|key|ccli|tempo|time|capo|meta)\s*:',
                        l.strip()):
                pos = i + 1
        body[pos:pos] = directives

    src = "\n".join(body)
    src = re.sub(r'\n{3,}', '\n\n', src).rstrip() + "\n"
    if src != orig:
        path.write_text(src, encoding="utf-8")
        return True
    return False


def label_lead(path: Path) -> bool:
    """Etiqueta el bloque de contenido que precede al primer {comment:}."""
    lang = path.parts[-3]
    src = path.read_text(encoding="utf-8")
    if "{comment:" not in src:
        return False
    head, rest = src.split("{comment:", 1)
    lead = [l for l in head.split("\n") if l.strip() and not l.strip().startswith("{")]
    if not lead:
        return False
    has_lyrics = any(re.sub(r'\[[^\]]*\]', '', l).strip() for l in lead)
    lab = ("Verse 1" if has_lyrics else "Intro")
    if has_lyrics and re.search(r'\{comment:\s*(Verse|Verso)\s*1\b', src):
        lab = "Verse"
    lab = localize(lab, lang)
    lines = head.split("\n")
    first = next(i for i, l in enumerate(lines)
                 if l.strip() and not l.strip().startswith("{"))
    lines.insert(first, "{comment: %s}" % lab)
    out = "\n".join(lines) + "{comment:" + rest
    out = re.sub(r'([^\n])\n(\{comment:)', r'\1\n\n\2', out)
    out = re.sub(r'\n{3,}', '\n\n', out)
    path.write_text(out, encoding="utf-8")
    return True


def main():
    a = b = 0
    for d in DIRS:
        for f in sorted((ROOT / d).glob("*.cho")):
            if process(f):
                a += 1
    for d in DIRS:
        for f in sorted((ROOT / d).glob("*.cho")):
            if label_lead(f):
                b += 1
    print(f"Cabeceras normalizadas: {a}")
    print(f"Bloques iniciales etiquetados: {b}")


if __name__ == "__main__":
    main()
