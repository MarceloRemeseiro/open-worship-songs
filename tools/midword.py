#!/usr/bin/env python3
"""Mide la distribución de acordes dentro de palabra: cuántos caracteres
dentro de la palabra cae el acorde, y cuántos quedan hasta el final."""
import re, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIRS = ["es/himnos", "es/popular", "en/hymns", "en/popular", "pt/hinos"]
CH = re.compile(r"\[[^\]]*\]")

into = collections.Counter()
rest = collections.Counter()
samples = collections.defaultdict(list)
WORD = re.compile(r"[^\W\d_]", re.UNICODE)

for d in DIRS:
    for f in sorted((ROOT / d).glob("*.cho")):
        for line in f.read_text(encoding="utf-8").split("\n"):
            t = line.strip()
            if not t or t.startswith("{"):
                continue
            # recorre y calcula posición en la letra "plana"
            plain = []
            marks = []  # (índice en plain)
            i = 0
            while i < len(t):
                if t[i] == "[":
                    j = t.find("]", i)
                    if j == -1:
                        break
                    marks.append(len(plain))
                    i = j + 1
                else:
                    plain.append(t[i])
                    i += 1
            s = "".join(plain)
            for pos in marks:
                if pos == 0 or pos >= len(s):
                    continue
                if not (WORD.match(s[pos - 1]) and WORD.match(s[pos])):
                    continue  # no está en medio de palabra
                # cuántos caracteres desde el inicio de la palabra
                k = pos
                while k > 0 and WORD.match(s[k - 1]):
                    k -= 1
                depth = pos - k
                e = pos
                while e < len(s) and WORD.match(s[e]):
                    e += 1
                into[depth] += 1
                rest[e - pos] += 1
                if len(samples[depth]) < 4:
                    samples[depth].append(s[k:e] + "  <<  " + t[:70])

tot = sum(into.values())
print(f"Acordes en medio de palabra: {tot}\n")
print("Profundidad (chars desde inicio de palabra):")
acc = 0
for k in sorted(into):
    acc += into[k]
    print(f"  {k:3d} -> {into[k]:6d}  ({into[k]*100/tot:5.1f}%)  acum {acc*100/tot:5.1f}%")
print("\nChars restantes hasta fin de palabra:")
for k in sorted(rest):
    print(f"  {k:3d} -> {rest[k]:6d}  ({rest[k]*100/tot:5.1f}%)")
print("\nEjemplos por profundidad:")
for k in sorted(samples):
    if k > 6: break
    print(f" depth={k}")
    for s in samples[k]:
        print("   ", s)
