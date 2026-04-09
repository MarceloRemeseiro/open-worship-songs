import { createHash } from "node:crypto";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import type { SongFull, SongMeta } from "./types.js";
import { parseChoFile } from "./parser.js";

function generateId(relativePath: string): string {
  return createHash("sha256").update(relativePath).digest("hex").slice(0, 12);
}

function walkDir(dir: string): string[] {
  const files: string[] = [];
  try {
    const entries = readdirSync(dir);
    for (const entry of entries) {
      const full = join(dir, entry);
      const stat = statSync(full);
      if (stat.isDirectory()) {
        files.push(...walkDir(full));
      } else if (entry.endsWith(".cho")) {
        files.push(full);
      }
    }
  } catch {
    // Directory doesn't exist, skip
  }
  return files;
}

const LANG_DIRS: Record<string, string> = {
  en: "en",
  es: "es",
  pt: "pt",
};

export function loadCatalog(repoRoot: string): Map<string, SongFull> {
  const catalog = new Map<string, SongFull>();
  const counts: Record<string, number> = {};

  for (const [lang, dir] of Object.entries(LANG_DIRS)) {
    const langDir = join(repoRoot, dir);
    const choFiles = walkDir(langDir);

    for (const filePath of choFiles) {
      const relPath = relative(repoRoot, filePath);
      const id = generateId(relPath);
      const content = readFileSync(filePath, "utf-8");
      const filename = filePath.split("/").pop()!;

      // Extract category from path: en/popular/file.cho -> "popular"
      const parts = relPath.split("/");
      const category = parts.length >= 2 ? parts[1] : "unknown";

      const parsed = parseChoFile(content, filename);

      catalog.set(id, {
        id,
        title: parsed.title,
        artist: parsed.artist,
        key: parsed.key,
        tempo: parsed.tempo,
        lang,
        category,
        filename,
        sections: parsed.sections,
      });
    }

    counts[lang] = choFiles.length;
  }

  console.log(`Catalog loaded: ${catalog.size} songs total`);
  for (const [lang, count] of Object.entries(counts)) {
    console.log(`  ${lang}: ${count} songs`);
  }

  return catalog;
}

export interface SearchParams {
  lang?: string;
  category?: string;
  q?: string;
}

export function searchSongs(catalog: Map<string, SongFull>, params: SearchParams): SongMeta[] {
  const results: SongMeta[] = [];

  for (const song of catalog.values()) {
    if (params.lang && song.lang !== params.lang) continue;
    if (params.category && song.category !== params.category) continue;

    if (params.q) {
      const query = params.q.toLowerCase();
      const matchTitle = song.title.toLowerCase().includes(query);
      const matchArtist = song.artist?.toLowerCase().includes(query) ?? false;
      if (!matchTitle && !matchArtist) continue;
    }

    // Return metadata only (no sections)
    const { sections: _, ...meta } = song;
    results.push(meta);
  }

  return results;
}

export function getSong(catalog: Map<string, SongFull>, id: string): SongFull | null {
  return catalog.get(id) ?? null;
}
