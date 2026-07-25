#!/usr/bin/env python3
"""Paso 2: corrige la posición de los acordes.

Dos reglas, ambas conservadoras:

A) Acorde pegado al final de una palabra y seguido de espacio  ("the[C] Lord")
   -> se mueve delante de la palabra siguiente  ("the [C]Lord").
   Es equivalente musicalmente (el cambio cae en el mismo punto) pero se
   renderiza correctamente.

B) Acorde dentro de una palabra ("Gr[G7]ace") -> se lleva al inicio de la
   palabra SOLO si es el primer acorde de esa palabra. Si la palabra ya
   tiene un acorde antes, el segundo se considera un cambio intencionado
   dentro de la palabra y se deja intacto ("[D7]majest[G]ad").

Nunca se toca una palabra con marcas de melisma (- o _), donde la posición
intermedia sí es deliberada ("fore--[G]ver", "Gl[C]ó__[G/B]ria").
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIRS = ["es/himnos", "es/popular", "en/hymns", "en/popular", "pt/hinos"]
WORD = re.compile(r"[^\W\d_]", re.UNICODE)   # letra (unicode), no dígito ni _


def parse(line):
    """-> (texto plano, [(idx_plano, texto_del_acorde), ...])"""
    plain, marks, i = [], [], 0
    while i < len(line):
        if line[i] == "[":
            j = line.find("]", i)
            if j == -1:
                plain.append(line[i]); i += 1; continue
            marks.append([len(plain), line[i:j + 1]])
            i = j + 1
        else:
            plain.append(line[i]); i += 1
    return "".join(plain), marks


def render(plain, marks):
    buckets = {}
    for idx, txt in marks:
        buckets.setdefault(idx, []).append(txt)
    out = []
    for i, ch in enumerate(plain):
        if i in buckets:
            out.extend(buckets[i])
        out.append(ch)
    if len(plain) in buckets:
        out.extend(buckets[len(plain)])
    return "".join(out)


def word_bounds(s, pos):
    a = pos
    while a > 0 and WORD.match(s[a - 1]):
        a -= 1
    b = pos
    while b < len(s) and WORD.match(s[b]):
        b += 1
    return a, b


def fix_line(line, stats):
    if not line.strip() or line.strip().startswith("{"):
        return line
    plain, marks = parse(line)
    if not marks:
        return line
    # línea sin letra (sólo acordes/compases): no tocar
    if not WORD.search(re.sub(r"\[[^\]]*\]", "", line)):
        return line

    def rule_a():
        """Acorde justo antes de un espacio -> delante de la palabra siguiente."""
        for m in marks:
            p = m[0]
            if 0 < p < len(plain) and plain[p] in " \t" and WORD.match(plain[p - 1]):
                q = p
                while q < len(plain) and plain[q] in " \t":
                    q += 1
                # sólo si detrás hay letra (no final de línea ni otro acorde suelto)
                if q < len(plain) and WORD.match(plain[q]):
                    m[0] = q
                    stats["A"] += 1

    rule_a()

    # --- Regla B: acorde dentro de palabra -> inicio de palabra ---
    occupied = sorted(m[0] for m in marks)
    for m in marks:
        p = m[0]
        if p == 0 or p >= len(plain):
            continue
        if not (WORD.match(plain[p - 1]) and WORD.match(plain[p])):
            continue
        a, b = word_bounds(plain, p)
        # palabra con marca de melisma pegada: posición intencionada
        tail = plain[b:b + 2]
        if "-" in plain[a:b] or "_" in plain[a:b] or tail[:1] in ("-", "_"):
            continue
        # ¿ya hay otro acorde en esta palabra antes de este?
        if any(a <= o < p for o in occupied):
            continue
        m[0] = a
        occupied = sorted(x[0] for x in marks)
        stats["B"] += 1

    # --- Regla C: acorde a un carácter del final de palabra -> final de palabra ---
    # Un cambio de acorde nunca cae sobre la última letra de una palabra: es
    # deriva. Sólo se aplica a los que la regla B dejó (2º acorde de la palabra).
    for m in marks:
        p = m[0]
        if p == 0 or p >= len(plain):
            continue
        if not (WORD.match(plain[p - 1]) and WORD.match(plain[p])):
            continue
        a, b = word_bounds(plain, p)
        if "-" in plain[a:b] or "_" in plain[a:b] or plain[b:b + 1] in ("-", "_"):
            continue
        if b - p == 1:
            m[0] = b
            stats["C"] += 1

    rule_a()   # los que C dejó al final de palabra pasan a la palabra siguiente
    return render(plain, marks)


def main(dry=False):
    stats = {"A": 0, "B": 0, "C": 0}
    changed = 0
    for d in DIRS:
        for f in sorted((ROOT / d).glob("*.cho")):
            src = f.read_text(encoding="utf-8")
            new = "\n".join(fix_line(l, stats) for l in src.split("\n"))
            if new != src:
                changed += 1
                if not dry:
                    f.write_text(new, encoding="utf-8")
    print(f"Ficheros modificados: {changed}")
    print(f"  Regla A (antes de espacio): {stats['A']}")
    print(f"  Regla B (dentro de palabra): {stats['B']}")
    print(f"  Regla C (final de palabra):  {stats['C']}")


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
