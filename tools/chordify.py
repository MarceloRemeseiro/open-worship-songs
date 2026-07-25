#!/usr/bin/env python3
"""Inserta acordes en un .cho existente SIN reescribir la letra.

Se declara, por sección y por línea, una lista de (ancla, acorde). El acorde
se coloca justo delante de la primera aparición del texto ancla en esa línea.
Anclas especiales: "^" = principio de línea, "$" = final de línea.

    apply_chords("es/himnos/x.cho", {
        "Verso 1": [
            [("^", "Eb"), ("mundo", "Bb")],   # 1ª línea con letra
            [("^", "Bb7")],                   # 2ª línea
        ],
    })

Los acordes que la línea ya tuviera se eliminan antes de insertar los nuevos.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _place(line: str, pairs):
    plain = re.sub(r"\[[^\]]*\]", "", line)
    inserts = []          # (posición, acorde)
    for anchor, chord in pairs:
        if anchor == "^":
            pos = len(plain) - len(plain.lstrip())
        elif anchor == "$":
            pos = len(plain.rstrip())
        else:
            i = plain.find(anchor)
            if i < 0:
                raise ValueError(f"ancla {anchor!r} no encontrada en {plain!r}")
            pos = i
        inserts.append((pos, chord))
    inserts.sort(key=lambda x: x[0])
    out, prev = [], 0
    for pos, chord in inserts:
        out.append(plain[prev:pos])
        out.append(f"[{chord}]")
        prev = pos
    out.append(plain[prev:])
    return "".join(out)


def apply_chords(rel_path: str, spec: dict, verbose=True):
    path = ROOT / rel_path
    lines = path.read_text(encoding="utf-8").split("\n")
    # índice: etiqueta de sección -> posiciones de sus líneas con letra
    sections, cur = {}, None
    for i, line in enumerate(lines):
        s = line.strip()
        m = re.match(r"^\{comment:\s*(.*?)\}$", s)
        if m:
            cur = m.group(1)
            sections.setdefault(cur, [])
            continue
        if not s or s.startswith("{"):
            continue
        if cur is not None and re.sub(r"\[[^\]]*\]", "", s).strip():
            sections[cur].append(i)

    for label, per_line in spec.items():
        if label not in sections:
            raise KeyError(f"{rel_path}: sección {label!r} no existe "
                           f"(hay: {list(sections)})")
        idxs = sections[label]
        if len(per_line) > len(idxs):
            raise ValueError(f"{rel_path}/{label}: {len(per_line)} líneas "
                             f"declaradas pero la sección tiene {len(idxs)}")
        for pairs, i in zip(per_line, idxs):
            if pairs:
                lines[i] = _place(lines[i], pairs)
    path.write_text("\n".join(lines), encoding="utf-8")
    if verbose:
        print("acordes aplicados:", rel_path)


def repeat_spec(spec_lines, labels):
    """Mismo patrón de acordes para varias secciones (estrofas isométricas)."""
    return {l: spec_lines for l in labels}


# --- esqueleto armónico por posición de frase -------------------------------
NOTES_S = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
NOTES_F = ["C","Db","D","Eb","E","F","Gb","G","Ab","A","Bb","B"]
PCS = {"C":0,"C#":1,"Db":1,"D":2,"D#":3,"Eb":3,"E":4,"F":5,"F#":6,"Gb":6,
       "G":7,"G#":8,"Ab":8,"A":9,"A#":10,"Bb":10,"B":11}
# grado -> (semitonos sobre la tónica, sufijo)
DEG = {"I":(0,""), "I7":(0,"7"), "ii":(2,"m"), "iii":(4,"m"), "IV":(5,""),
       "IV7":(5,"7"), "V":(7,""), "V7":(7,"7"), "vi":(9,"m"), "iv":(5,"m"),
       "II7":(2,"7"), "VI7":(9,"7"), "III7":(4,"7")}


def chord_of(key: str, degree: str) -> str:
    import re as _re
    m = _re.match(r"^([A-G][#b]?)(m?)$", key.strip())
    tonic, minor = m.group(1), m.group(2)
    flat = "b" in key or key.strip() in ("F", "Fm")
    semis, suf = DEG[degree]
    pc = (PCS[tonic] + semis) % 12
    return (NOTES_F if flat else NOTES_S)[pc] + suf


def skeleton(rel_path: str, key: str, patterns: dict, verbose=True):
    """patterns: etiqueta -> lista por línea de [(fracción 0..1, grado), ...].
    El acorde se ancla al comienzo de la palabra más cercana a esa fracción."""
    import re as _re
    path = ROOT / rel_path
    lines = path.read_text(encoding="utf-8").split("\n")
    sections, cur = {}, None
    for i, line in enumerate(lines):
        s = line.strip()
        m = _re.match(r"^\{comment:\s*(.*?)\}$", s)
        if m:
            cur = m.group(1); sections.setdefault(cur, []); continue
        if not s or s.startswith("{"):
            continue
        if cur is not None and _re.sub(r"\[[^\]]*\]", "", s).strip():
            sections[cur].append(i)

    for label, per_line in patterns.items():
        if label not in sections:
            raise KeyError(f"{rel_path}: sección {label!r} no existe (hay: {list(sections)})")
        for spec, i in zip(per_line, sections[label]):
            plain = _re.sub(r"\[[^\]]*\]", "", lines[i])
            starts = [m.start() for m in _re.finditer(r"\S+", plain)]
            if not starts or not spec:
                continue
            placed, used = [], set()
            for frac, deg in spec:
                target = frac * len(plain.rstrip())
                cand = sorted(starts, key=lambda p: (abs(p - target), p))
                pos = next((p for p in cand if p not in used), None)
                if pos is None:      # no quedan palabras libres: mejor omitir
                    continue         # que duplicar el acorde
                used.add(pos)
                placed.append((pos, chord_of(key, deg)))
            placed.sort()
            out, prev = [], 0
            for pos, ch in placed:
                out.append(plain[prev:pos]); out.append(f"[{ch}]"); prev = pos
            out.append(plain[prev:])
            lines[i] = "".join(out)
    path.write_text("\n".join(lines), encoding="utf-8")
    if verbose:
        print("esqueleto aplicado:", rel_path)


# patrones habituales de himno
P4 = [[(0,"I"),(.5,"IV"),(.8,"I")], [(0,"V7"),(.65,"I")],
      [(0,"I"),(.5,"IV"),(.8,"I")], [(0,"I"),(.45,"V7"),(.8,"I")]]
P4b = [[(0,"I"),(.55,"IV"),(.85,"I")], [(0,"I"),(.6,"V7")],
       [(0,"I"),(.5,"IV"),(.8,"I")], [(0,"IV"),(.4,"I"),(.7,"V7"),(.9,"I")]]
P6 = [[(0,"I")], [(0,"IV"),(.6,"I")], [(0,"V7"),(.7,"I")],
      [(0,"I")], [(0,"IV"),(.6,"I")], [(0,"I"),(.5,"V7"),(.85,"I")]]
