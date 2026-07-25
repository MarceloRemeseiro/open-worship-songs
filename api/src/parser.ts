import type { MetaEntry, SongSection } from "./types.js";

function detectSectionType(label: string): SongSection["type"] {
  const lower = label.toLowerCase();
  if (/^(intro|introducción|introduction)/.test(lower)) return "intro";
  if (/^(outro|final|coda|ending)/.test(lower)) return "outro";
  if (/^(coro|chorus|estribillo|tornada|refrão)/.test(lower)) return "chorus";
  if (/^(pre.?coro|pre.?chorus)/.test(lower)) return "pre_chorus";
  if (/^(puente|bridge|pont)/.test(lower)) return "bridge";
  if (/^(interl|instrumental)/.test(lower)) return "interlude";
  if (/^(tag|ending)/.test(lower)) return "tag";
  if (/^(verso|verse|estrofa|v\d)/.test(lower)) return "verse";
  return "other";
}

function isInstrumental(content: string): boolean {
  // Remove chord brackets and whitespace — if nothing remains, it's instrumental
  const withoutChords = content.replace(/\[.*?\]/g, "").replace(/\s+/g, "").trim();
  return withoutChords.length === 0;
}

function filenameToTitle(filename: string): string {
  const name = filename.replace(/\.cho$/, "");
  return name
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export interface ParsedSong {
  title: string;
  artist: string | null;
  key: string;
  tempo: number | null;
  capo: number | null;
  ccli: string | null;
  time: string | null;
  meta: MetaEntry[];
  sections: SongSection[];
}

export function parseChoFile(content: string, filename: string): ParsedSong {
  const lines = content.split("\n");

  let title: string | null = null;
  let artist: string | null = null;
  let key: string | null = null;
  let tempo: number | null = null;
  let capo: number | null = null;
  let ccli: string | null = null;
  let time: string | null = null;
  const meta: MetaEntry[] = [];

  const sections: SongSection[] = [];
  let currentLabel: string | null = null;
  let currentLines: string[] = [];
  let sectionIndex = 0;

  function flushSection() {
    const text = currentLines.join("\n").trim();
    if (!text && !currentLabel) return;

    const label = currentLabel || `Section ${sectionIndex + 1}`;
    sections.push({
      type: detectSectionType(label),
      label,
      content: text,
      position: sectionIndex,
      isInstrumental: isInstrumental(text),
    });
    sectionIndex++;
    currentLines = [];
  }

  for (const line of lines) {
    const trimmed = line.trim();

    // Parse directives
    const directiveMatch = trimmed.match(/^\{(\w+):\s*(.*?)\}$/);
    if (directiveMatch) {
      const [, directive, value] = directiveMatch;
      const dir = directive.toLowerCase();

      if (dir === "title" || dir === "t") {
        title = value.trim();
      } else if (dir === "artist" || dir === "by") {
        artist = value.trim();
      } else if (dir === "key") {
        key = value.trim();
      } else if (dir === "tempo") {
        const parsed = parseInt(value.trim(), 10);
        if (!isNaN(parsed)) tempo = parsed;
      } else if (dir === "capo") {
        const parsed = parseInt(value.trim(), 10);
        if (!isNaN(parsed)) capo = parsed;
      } else if (dir === "ccli") {
        ccli = value.trim() || null;
      } else if (dir === "time") {
        time = value.trim() || null;
      } else if (dir === "meta") {
        // "{meta: scripture Psalm 19:1}" -> { name: "scripture", value: "Psalm 19:1" }
        const raw = value.trim();
        const spaceIdx = raw.indexOf(" ");
        if (spaceIdx > 0) {
          meta.push({ name: raw.slice(0, spaceIdx), value: raw.slice(spaceIdx + 1).trim() });
        } else if (raw) {
          meta.push({ name: raw, value: "" });
        }
      } else if (dir === "comment" || dir === "c") {
        // New section starts
        flushSection();
        currentLabel = value.trim();
      }
      // Ignore other unknown directives
      continue;
    }

    // Check for non-directive tempo line (e.g. "Tempo: 73")
    const tempoLineMatch = trimmed.match(/^Tempo:\s*(\d+)/i);
    if (tempoLineMatch && tempo === null) {
      tempo = parseInt(tempoLineMatch[1], 10);
      continue;
    }

    // Skip other metadata-like lines (e.g. "Scripture Reference(s): ...")
    if (/^Scripture Reference/i.test(trimmed)) {
      continue;
    }

    // Regular content line
    currentLines.push(line);
  }

  // Flush last section
  flushSection();

  return {
    title: title || filenameToTitle(filename),
    artist: artist || null,
    key: key || "C",
    tempo,
    capo,
    ccli,
    time,
    meta,
    sections,
  };
}
