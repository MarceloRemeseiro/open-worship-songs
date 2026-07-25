/* Cancionero — visor de canciones ChordPro
 * Vanilla JS, sin build. Habla con la API Hono del mismo origen.
 */

// ---------------------------------------------------------------------------
// Estado
// ---------------------------------------------------------------------------

const state = {
  songs: [],          // metadatos de todas las canciones
  current: null,      // canción completa seleccionada
  transpose: 0,
  showChords: true,
  fontSize: 17,
  query: "",
};

const LANGS = [
  { code: "es", name: "Español" },
  { code: "en", name: "English" },
  { code: "pt", name: "Português" },
];

const CATEGORY_NAMES = {
  himnos: "Himnos",
  hymns: "Hymns",
  hinos: "Hinos",
  popular: "Popular",
};

const META_NAMES = {
  cant_key: "Tonalidad cantada",
  church_key: "Tonalidad iglesia",
  scripture: "Pasaje",
  writers: "Autores",
  topic: "Tema",
  url: "Enlace",
};

const $ = (sel) => document.querySelector(sel);

// ---------------------------------------------------------------------------
// Acordes: parseo y transposición
// ---------------------------------------------------------------------------

const SHARP_NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const FLAT_NOTES  = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"];

const NOTE_INDEX = {
  "C": 0, "B#": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
  "E": 4, "Fb": 4, "E#": 5, "F": 5, "F#": 6, "Gb": 6, "G": 7,
  "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11, "Cb": 11,
};

function transposeNote(note, semitones, preferFlat) {
  const idx = NOTE_INDEX[note];
  if (idx === undefined) return note;
  const next = (((idx + semitones) % 12) + 12) % 12;
  return (preferFlat ? FLAT_NOTES : SHARP_NOTES)[next];
}

/** Transpone un token de acorde tipo "F#m7/A#" respetando el sufijo. */
function transposeChord(chord, semitones, preferFlat) {
  if (!semitones || !chord) return chord;
  return chord
    .split("/")
    .map((part) => {
      const m = part.match(/^([A-G][#b]?)(.*)$/);
      if (!m) return part;
      return transposeNote(m[1], semitones, preferFlat) + m[2];
    })
    .join("/");
}

/** ¿Usamos bemoles al transponer? Depende de la tonalidad destino. */
function preferFlats(key, semitones) {
  const FLAT_KEYS = new Set(["F", "Bb", "Eb", "Ab", "Db", "Gb", "Cb", "Dm", "Gm", "Cm", "Fm", "Bbm", "Ebm"]);
  const base = (key || "C").trim();
  const target = transposeChord(base, semitones, false);
  // Si el destino "en sostenidos" es raro (A#, D#, G#) preferimos bemoles.
  if (/^(A#|D#|G#|C#|F#)/.test(target) && !/^(F#|C#)/.test(target)) return true;
  return FLAT_KEYS.has(base) || base.includes("b");
}

/**
 * Divide una línea ChordPro en segmentos { chord, text }.
 * "[C]A Cristo [F]coronad" -> [{C,"A Cristo "},{F,"coronad"}]
 */
function parseChordLine(line) {
  const segments = [];
  const parts = line.split(/(\[[^\]]*\])/g);
  let pending = null;
  let started = false;

  for (const part of parts) {
    if (part === "") continue;
    if (part.startsWith("[") && part.endsWith("]")) {
      if (started && pending !== null) segments.push({ chord: pending, text: "" });
      pending = part.slice(1, -1).trim();
      started = true;
    } else {
      segments.push({ chord: pending, text: part });
      pending = null;
      started = true;
    }
  }
  if (pending !== null) segments.push({ chord: pending, text: "" });
  return segments;
}

/** Un "trocito": acorde arriba, texto abajo, en columna. */
function makeWord(chord, text, semitones, flat) {
  const span = document.createElement("span");
  span.className = "w";

  const ch = document.createElement("span");
  ch.className = "ch";
  ch.textContent = chord ? transposeChord(chord, semitones, flat) : "";

  const lx = document.createElement("span");
  lx.className = "lx";
  lx.textContent = text;

  span.append(ch, lx);
  return span;
}

/**
 * Renderiza una línea. Cada palabra va en su propio contenedor en columna,
 * de forma que el acorde queda justo encima de la sílaba y la línea puede
 * partirse por espacios sin romper la alineación.
 */
function renderLine(line, semitones, flat) {
  const div = document.createElement("div");
  div.className = "line";

  if (line.trim() === "") {
    div.classList.add("blank");
    return div;
  }

  for (const seg of parseChordLine(line)) {
    let chordPending = seg.chord || null;
    const tokens = seg.text === "" ? [] : seg.text.split(/(\s+)/).filter((t) => t !== "");

    if (tokens.length === 0) {
      div.appendChild(makeWord(chordPending, "", semitones, flat));
      continue;
    }

    for (const token of tokens) {
      if (/^\s+$/.test(token)) {
        // El acorde no puede colgar de un espacio: le damos su propia casilla.
        if (chordPending) {
          div.appendChild(makeWord(chordPending, "", semitones, flat));
          chordPending = null;
        }
        div.appendChild(document.createTextNode(" "));
      } else {
        div.appendChild(makeWord(chordPending, token, semitones, flat));
        chordPending = null;
      }
    }
  }
  return div;
}

// ---------------------------------------------------------------------------
// Render de la canción
// ---------------------------------------------------------------------------

function chip(label, value, extraClass) {
  const el = document.createElement("span");
  el.className = "chip" + (extraClass ? " " + extraClass : "");
  const b = document.createElement("b");
  b.textContent = label;
  el.append(b, document.createTextNode(value));
  return el;
}

function renderSong() {
  const song = state.current;
  const content = $("#content");
  content.innerHTML = "";
  if (!song) return;

  const flat = preferFlats(song.key, state.transpose);
  const wrap = document.createElement("article");
  wrap.className = "song";

  // Cabecera
  const head = document.createElement("header");
  head.className = "song-head";

  const h2 = document.createElement("h2");
  h2.textContent = song.title;
  head.appendChild(h2);

  if (song.artist) {
    const p = document.createElement("p");
    p.className = "artist";
    p.textContent = song.artist;
    head.appendChild(p);
  }

  const metaRow = document.createElement("div");
  metaRow.className = "meta-row";

  if (song.key) {
    const shown = transposeChord(song.key, state.transpose, flat);
    const suffix = state.transpose ? ` (orig. ${song.key})` : "";
    metaRow.appendChild(chip("Tono", shown + suffix, "key-chip"));
  }
  if (song.tempo) metaRow.appendChild(chip("Tempo", song.tempo + " bpm"));
  if (song.capo !== null && song.capo !== undefined) metaRow.appendChild(chip("Capo", String(song.capo)));
  if (song.time) metaRow.appendChild(chip("Compás", song.time));
  if (song.ccli) metaRow.appendChild(chip("CCLI", song.ccli));
  for (const m of song.meta || []) {
    metaRow.appendChild(chip(META_NAMES[m.name] || m.name.replace(/_/g, " "), m.value));
  }
  const langName = (LANGS.find((l) => l.code === song.lang) || {}).name || song.lang;
  metaRow.appendChild(chip("Idioma", langName));
  metaRow.appendChild(chip("Categoría", CATEGORY_NAMES[song.category] || song.category));
  head.appendChild(metaRow);
  wrap.appendChild(head);

  // Secciones
  for (const section of song.sections) {
    if (!section.content.trim() && !section.label) continue;

    const sec = document.createElement("section");
    sec.className = "section" + (section.isInstrumental ? " instrumental" : "");

    const label = document.createElement("div");
    label.className = "section-label";
    label.textContent = section.isInstrumental ? `${section.label} · instrumental` : section.label;
    sec.appendChild(label);

    const body = document.createElement("div");
    body.className = "section-body";

    const lines = section.content.replace(/\s+$/, "").split("\n");
    // Quita líneas en blanco iniciales
    while (lines.length && lines[0].trim() === "") lines.shift();

    for (const line of lines) {
      body.appendChild(renderLine(line, state.transpose, flat));
    }

    sec.appendChild(body);
    wrap.appendChild(sec);
  }

  content.appendChild(wrap);
  content.scrollTop = 0;
  document.title = `${song.title} — Cancionero`;
}

// ---------------------------------------------------------------------------
// Sidebar
// ---------------------------------------------------------------------------

function matches(song, q) {
  if (!q) return true;
  return (
    song.title.toLowerCase().includes(q) ||
    (song.artist || "").toLowerCase().includes(q)
  );
}

function songButton(song) {
  const btn = document.createElement("button");
  btn.className = "song-item";
  btn.dataset.id = song.id;
  btn.title = song.artist ? `${song.title} — ${song.artist}` : song.title;
  btn.textContent = song.title;
  if (song.artist) {
    const sub = document.createElement("span");
    sub.className = "sub";
    sub.textContent = " · " + song.artist;
    btn.appendChild(sub);
  }
  if (state.current && state.current.id === song.id) btn.classList.add("active");
  btn.addEventListener("click", () => selectSong(song.id));
  return btn;
}

function renderTree() {
  const tree = $("#tree");
  tree.innerHTML = "";
  const q = state.query.trim().toLowerCase();

  // Buscando: lista plana de resultados
  if (q) {
    const found = state.songs.filter((s) => matches(s, q)).slice(0, 400);
    const info = document.createElement("p");
    info.className = "muted pad";
    info.textContent = found.length ? `${found.length} resultado(s)` : "Sin resultados";
    tree.appendChild(info);
    const list = document.createElement("div");
    list.className = "flat";
    found.forEach((s) => list.appendChild(songButton(s)));
    tree.appendChild(list);
    return;
  }

  for (const lang of LANGS) {
    const langSongs = state.songs.filter((s) => s.lang === lang.code);
    if (!langSongs.length) continue;

    const group = document.createElement("div");
    group.className = "group open";

    const gBtn = document.createElement("button");
    gBtn.className = "grp-btn";
    gBtn.innerHTML = `<span class="caret">▶</span><span>${lang.name}</span>`;
    const gCount = document.createElement("span");
    gCount.className = "count";
    gCount.textContent = langSongs.length;
    gBtn.appendChild(gCount);
    gBtn.addEventListener("click", () => group.classList.toggle("open"));
    group.appendChild(gBtn);

    const cats = document.createElement("div");
    cats.className = "songs";

    const categories = [...new Set(langSongs.map((s) => s.category))].sort();
    for (const cat of categories) {
      const catSongs = langSongs
        .filter((s) => s.category === cat)
        .sort((a, b) => a.title.localeCompare(b.title, lang.code));

      const catEl = document.createElement("div");
      catEl.className = "cat";

      const cBtn = document.createElement("button");
      cBtn.className = "cat-btn";
      cBtn.innerHTML = `<span class="caret">▶</span><span>${CATEGORY_NAMES[cat] || cat}</span>`;
      const cCount = document.createElement("span");
      cCount.className = "count";
      cCount.textContent = catSongs.length;
      cBtn.appendChild(cCount);
      cBtn.addEventListener("click", () => catEl.classList.toggle("open"));
      catEl.appendChild(cBtn);

      const list = document.createElement("div");
      list.className = "songs";
      catSongs.forEach((s) => list.appendChild(songButton(s)));
      catEl.appendChild(list);
      cats.appendChild(catEl);
    }

    group.appendChild(cats);
    tree.appendChild(group);
  }
}

function markActive(id) {
  document.querySelectorAll(".song-item.active").forEach((el) => el.classList.remove("active"));
  const el = document.querySelector(`.song-item[data-id="${id}"]`);
  if (el) {
    el.classList.add("active");
    // Abre los grupos que lo contienen
    let p = el.parentElement;
    while (p && p !== document.body) {
      if (p.classList.contains("group") || p.classList.contains("cat")) p.classList.add("open");
      p = p.parentElement;
    }
    el.scrollIntoView({ block: "nearest" });
  }
}

// ---------------------------------------------------------------------------
// Carga y eventos
// ---------------------------------------------------------------------------

async function selectSong(id, skipHash) {
  try {
    const res = await fetch(`/songs/${id}`);
    if (!res.ok) throw new Error("HTTP " + res.status);
    state.current = await res.json();
    state.transpose = state.pendingTranspose || 0;
    state.pendingTranspose = 0;
    updateTransposeLabel();
    renderSong();
    markActive(id);
    if (!skipHash) location.hash = "#" + id;
    document.body.classList.remove("nav-open");
  } catch (err) {
    $("#content").innerHTML = `<div class="empty"><div class="empty-inner"><h2>Error</h2><p class="muted">No se pudo cargar la canción (${err.message}).</p></div></div>`;
  }
}

function updateTransposeLabel() {
  const el = $("#transposeLabel");
  el.textContent = state.transpose > 0 ? "+" + state.transpose : String(state.transpose);
  el.classList.toggle("on", state.transpose !== 0);
}

function setTranspose(delta) {
  if (delta === 0) state.transpose = 0;
  else state.transpose = Math.max(-11, Math.min(11, state.transpose + delta));
  updateTransposeLabel();
  renderSong();
}

function toggleChords() {
  state.showChords = !state.showChords;
  document.body.classList.toggle("no-chords", !state.showChords);
  $("#chordsBtn").textContent = "Acordes: " + (state.showChords ? "ON" : "OFF");
}

function setFontSize(delta) {
  state.fontSize = Math.max(12, Math.min(34, state.fontSize + delta));
  document.documentElement.style.setProperty("--lyric-size", state.fontSize + "px");
}

async function init() {
  // Estado inicial vía querystring: /?t=2&chords=0#<id>
  const params = new URLSearchParams(location.search);
  if (params.has("t")) state.pendingTranspose = parseInt(params.get("t"), 10) || 0;
  if (params.get("chords") === "0") toggleChords();

  // Toolbar
  $("#chordsBtn").addEventListener("click", toggleChords);
  $("#upBtn").addEventListener("click", () => setTranspose(1));
  $("#downBtn").addEventListener("click", () => setTranspose(-1));
  $("#transposeLabel").addEventListener("click", () => setTranspose(0));
  $("#fontUpBtn").addEventListener("click", () => setFontSize(1));
  $("#fontDownBtn").addEventListener("click", () => setFontSize(-1));
  $("#printBtn").addEventListener("click", () => window.print());
  $("#menuBtn").addEventListener("click", () => document.body.classList.toggle("nav-open"));
  $("#overlay").addEventListener("click", () => document.body.classList.remove("nav-open"));

  let debounce;
  $("#search").addEventListener("input", (e) => {
    clearTimeout(debounce);
    const value = e.target.value;
    debounce = setTimeout(() => {
      state.query = value;
      renderTree();
      if (state.current) markActive(state.current.id);
    }, 120);
  });

  window.addEventListener("hashchange", () => {
    const id = location.hash.slice(1);
    if (id && (!state.current || state.current.id !== id)) selectSong(id, true);
  });

  // Catálogo
  try {
    const res = await fetch("/songs");
    state.songs = await res.json();
  } catch (err) {
    $("#tree").innerHTML = `<p class="muted pad">No se pudo cargar el catálogo: ${err.message}</p>`;
    return;
  }

  $("#totalCount").textContent = `${state.songs.length} canciones`;
  renderTree();

  const hashId = location.hash.slice(1);
  if (hashId) selectSong(hashId, true);
}

init();
