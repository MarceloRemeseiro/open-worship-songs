import { Hono } from "hono";
import { cors } from "hono/cors";
import { serve } from "@hono/node-server";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { readFileSync, existsSync, statSync } from "node:fs";
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

// ---------------------------------------------------------------------------
// Static frontend (web/) — served straight from disk so edits are picked up
// without a build step or a second dev server.
// ---------------------------------------------------------------------------
const WEB_ROOT = path.join(REPO_ROOT, "web");

const MIME: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".png": "image/png",
  ".woff2": "font/woff2",
};

function serveFile(c: any, relPath: string) {
  const target = path.resolve(WEB_ROOT, "." + path.posix.resolve("/", relPath));
  if (!target.startsWith(WEB_ROOT)) return c.text("Forbidden", 403);
  if (!existsSync(target) || !statSync(target).isFile()) return null;
  const ext = path.extname(target).toLowerCase();
  return c.body(readFileSync(target), 200, {
    "Content-Type": MIME[ext] ?? "application/octet-stream",
    "Cache-Control": "no-cache",
  });
}

app.get("/", (c) => serveFile(c, "index.html") ?? c.text("web/index.html not found", 404));

app.get("/*", (c) => {
  const res = serveFile(c, new URL(c.req.url).pathname);
  return res ?? c.text("Not found", 404);
});

const port = Number(process.env.PORT) || 3001;
const hostname = process.env.HOST || "0.0.0.0";
console.log(`Server starting on ${hostname}:${port}...`);
serve({ fetch: app.fetch, port, hostname });
console.log(`Open Worship Songs running at http://localhost:${port}`);
