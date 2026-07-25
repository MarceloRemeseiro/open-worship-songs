#!/usr/bin/env python3
"""Paso 3: deduce la tonalidad a partir de los acordes y la escribe en {key:}.

Puntúa las 24 tonalidades (12 mayores + 12 menores) según cuántos acordes de
la canción son diatónicos, con bonus para el acorde final y el inicial (que
en la práctica casi siempre son la tónica).
"""
import re, sys, json, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIRS = ["es/himnos", "es/popular", "en/hymns", "en/popular", "pt/hinos"]

PC = {"C":0,"C#":1,"Db":1,"D":2,"D#":3,"Eb":3,"E":4,"Fb":4,"E#":5,"F":5,
      "F#":6,"Gb":6,"G":7,"G#":8,"Ab":8,"A":9,"A#":10,"Bb":10,"B":11,"Cb":11}
SHARP = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
FLAT  = ["C","Db","D","Eb","E","F","Gb","G","Ab","A","Bb","B"]
MAJOR = [0,2,4,5,7,9,11]
MINOR = [0,2,3,5,7,8,10]
# calidad esperada de la tríada sobre cada grado
MAJ_Q = {0:"",2:"m",4:"m",5:"",7:"",9:"m",11:"dim"}
MIN_Q = {0:"m",2:"dim",3:"",5:"m",7:"m",8:"",10:""}

ROOT_RE = re.compile(r"^([A-G](?:#|b)?)(.*)$")


def parse_chord(tok):
    """-> (pitch class raíz, 'm' | '' | 'dim') o None"""
    t = tok.strip().split("/")[0]
    m = ROOT_RE.match(t)
    if not m:
        return None
    root, rest = m.group(1), m.group(2)
    if root not in PC:
        return None
    if rest.startswith("dim") or rest.startswith("°") or rest.startswith("o"):
        q = "dim"
    elif re.match(r"^(m|min)(?!aj)", rest):
        q = "m"
    else:
        q = ""
    return PC[root], q


def song_chords(text):
    out = []
    for line in text.split("\n"):
        if line.strip().startswith("{"):
            continue
        for tok in re.findall(r"\[([^\]]*)\]", line):
            c = parse_chord(tok)
            if c:
                out.append(c)
    return out


def detect(chords, prefer_flat):
    if not chords:
        return None, 0
    counts = collections.Counter(chords)
    first, last = chords[0], chords[-1]
    best, best_score = None, -1e9
    for tonic in range(12):
        for mode in ("maj", "min"):
            scale = [(tonic + i) % 12 for i in (MAJOR if mode == "maj" else MINOR)]
            qmap = {(tonic + d) % 12: q for d, q in
                    ((MAJ_Q if mode == "maj" else MIN_Q).items())}
            score = 0
            for (pcv, q), n in counts.items():
                if pcv in scale:
                    score += 3 * n if qmap.get(pcv) == q else 1.5 * n
                elif (pcv - tonic) % 12 == 10:      # bVII, muy común en worship
                    score += 1.0 * n
                elif mode == "min" and (pcv - tonic) % 12 == 7 and q == "":
                    score += 2.0 * n                # V mayor en menor armónica
                else:
                    score -= 2.5 * n
            tq = "m" if mode == "min" else ""
            if last == (tonic, tq):
                score += 8
            if first == (tonic, tq):
                score += 5
            if mode == "min":
                score -= 0.5           # desempate hacia el relativo mayor
            if score > best_score:
                best_score, best = score, (tonic, mode)
    tonic, mode = best
    name = (FLAT if prefer_flat else SHARP)[tonic]
    return name + ("m" if mode == "min" else ""), best_score


def main(apply=False):
    added, mismatch = [], []
    for d in DIRS:
        for f in sorted((ROOT / d).glob("*.cho")):
            text = f.read_text(encoding="utf-8")
            chords = song_chords(text)
            raw = re.findall(r"\[([^\]]*)\]", text)
            prefer_flat = sum("b" in c for c in raw) > sum("#" in c for c in raw)
            key, _ = detect(chords, prefer_flat)
            if not key:
                continue
            m = re.search(r"^\{key:\s*(.*?)\}\s*$", text, re.M)
            if m:
                cur = m.group(1).strip()
                if not cur or cur == key:
                    continue
                # Sólo se corrige una tonalidad declarada cuando es demostrablemente
                # incompatible: su tónica no aparece nunca como acorde de la canción.
                cm = ROOT_RE.match(cur)
                cur_pc = PC.get(cm.group(1)) if cm else None
                roots = {c[0] for c in chords}
                if cur_pc is not None and cur_pc not in roots and len(chords) >= 6:
                    mismatch.append((str(f.relative_to(ROOT)), cur, key, "CORREGIDA"))
                    if apply:
                        f.write_text(re.sub(r"^\{key:.*\}\s*$", "{key: %s}" % key,
                                            text, count=1, flags=re.M), encoding="utf-8")
                else:
                    mismatch.append((str(f.relative_to(ROOT)), cur, key, "respetada"))
                continue
            added.append((str(f.relative_to(ROOT)), key))
            if apply:
                lines = text.split("\n")
                # insertar tras {artist:} si existe, si no tras {title:}
                idx = 0
                for i, l in enumerate(lines[:8]):
                    if re.match(r"^\{(title|artist|by|t)\s*:", l.strip()):
                        idx = i + 1
                lines.insert(idx, "{key: %s}" % key)
                f.write_text("\n".join(lines), encoding="utf-8")
    print(f"Tonalidades añadidas: {len(added)}")
    print(f"Discrepancias con {{key:}} existente: {len(mismatch)}")
    Path(ROOT / "tools/keys_report.json").write_text(
        json.dumps({"added": added, "mismatch": mismatch}, ensure_ascii=False, indent=1))
    corr = [x for x in mismatch if x[3] == "CORREGIDA"]
    print(f"  de ellas corregidas: {len(corr)}")
    for x in corr[:25]:
        print("   ", x[0], x[1], "->", x[2])


if __name__ == "__main__":
    main(apply="--apply" in sys.argv)
