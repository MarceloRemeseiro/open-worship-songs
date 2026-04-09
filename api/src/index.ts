import { Hono } from "hono";
import { cors } from "hono/cors";
import { serve } from "@hono/node-server";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { loadCatalog, searchSongs, getSong } from "./catalog.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = new Hono();
app.use("*", cors());

// Resolve repo root: from api/src/ go up two levels
const REPO_ROOT = path.resolve(__dirname, "../../");
console.log(`Loading catalog from: ${REPO_ROOT}`);
const catalog = loadCatalog(REPO_ROOT);

app.get("/songs", (c) => {
  const lang = c.req.query("lang");
  const category = c.req.query("category");
  const q = c.req.query("q");
  const results = searchSongs(catalog, { lang, category, q });
  return c.json(results);
});

app.get("/songs/:id", (c) => {
  const song = getSong(catalog, c.req.param("id"));
  if (!song) return c.json({ error: "Not found" }, 404);
  return c.json(song);
});

app.get("/stats", (c) => {
  const stats: Record<string, Record<string, number>> = {};
  for (const song of catalog.values()) {
    if (!stats[song.lang]) stats[song.lang] = {};
    stats[song.lang][song.category] = (stats[song.lang][song.category] || 0) + 1;
  }
  return c.json({ total: catalog.size, byLanguage: stats });
});

const port = Number(process.env.PORT) || 3001;
console.log(`Server starting on port ${port}...`);
serve({ fetch: app.fetch, port });
console.log(`Open Worship Songs API running at http://localhost:${port}`);
