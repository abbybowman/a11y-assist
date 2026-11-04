// Agent B's browser for a round (docs/plans/2026-10-31-agent-eval.md
// section 6). Playwright MCP runs this on each page it opens (--init-page).
//
// - The round's tested pages come only from their frozen copies
//   (A11Y_FROZEN_DIR: index.json + HARs), never live, as for Agent A.
// - Other pages of the tested site's hosts load live, as Agent A's server
//   loads other pages and 19.A's search live. Each live page is logged to
//   A11Y_LIVE_LOG (JSON lines), so the round stays auditable.
// - A page on any other host is refused. A live page's own images and
//   scripts load from wherever they come from; the browser's connections
//   go through the harness's egress proxy (--proxy-server), which refuses
//   private, loopback and metadata addresses, as for Agent A.
// - A frozen page's requests that are not in its recording are aborted, and
//   requests that failed while recording (status -1) fail again, as
//   capture.replay_context does: Playwright's HAR replay would otherwise wait
//   on them forever.
const fs = require("fs");
const path = require("path");
const zlib = require("zlib");

function zipFiles(file) {
  // Every file in a .har.zip, read from the zip's central directory (local
  // headers may leave sizes to a trailing descriptor); no packages.
  const buf = fs.readFileSync(file);
  let eocd = buf.length - 22;
  while (eocd >= 0 && buf.readUInt32LE(eocd) !== 0x06054b50) eocd--;
  if (eocd < 0) throw new Error("Not a zip file: " + file);
  const count = buf.readUInt16LE(eocd + 10);
  let off = buf.readUInt32LE(eocd + 16);
  const out = {};
  for (let n = 0; n < count; n++) {
    const method = buf.readUInt16LE(off + 10);
    const csize = buf.readUInt32LE(off + 20);
    const nlen = buf.readUInt16LE(off + 28);
    const xlen = buf.readUInt16LE(off + 30);
    const clen = buf.readUInt16LE(off + 32);
    const local = buf.readUInt32LE(off + 42);
    const name = buf.toString("utf8", off + 46, off + 46 + nlen);
    const lstart =
      local + 30 + buf.readUInt16LE(local + 26) + buf.readUInt16LE(local + 28);
    const data = buf.subarray(lstart, lstart + csize);
    out[name] = method === 0 ? Buffer.from(data) : zlib.inflateRawSync(data);
    off += 46 + nlen + xlen + clen;
  }
  return out;
}

// Each recording, unpacked once per process into a temporary folder, with
// its failed entries (status -1) removed: Playwright consults the newest
// route first, so a recording's failed copy of a file the site's pages share
// would otherwise be served instead of another recording's good one (round
// 1, 2026-11-04). Returns [{har, failed}] in index order.
let prepared = null;
function prepare(dir, pages) {
  if (prepared) return prepared;
  const tmp = fs.mkdtempSync(path.join(require("os").tmpdir(), "a11y-frozen-"));
  const seen = new Set();
  prepared = [];
  for (const p of pages) {
    if (seen.has(p.har)) continue;
    seen.add(p.har);
    const files = zipFiles(path.join(dir, p.har));
    const sub = path.join(tmp, String(prepared.length));
    fs.mkdirSync(sub);
    let harName = null;
    for (const [name, data] of Object.entries(files)) {
      if (name.endsWith(".har")) harName = name;
      else fs.writeFileSync(path.join(sub, name), data);
    }
    const log = JSON.parse(files[harName].toString("utf8"));
    const failed = [];
    log.log.entries = log.log.entries.filter((e) => {
      const bad = (e.response && e.response.status) < 0;
      if (bad) failed.push(e.request.url);
      return !bad;
    });
    const har = path.join(sub, "page.har");
    fs.writeFileSync(har, JSON.stringify(log));
    prepared.push({ har, failed });
  }
  return prepared;
}

function key(u) {
  try {
    const x = new URL(u);
    x.hash = "";
    return x.href;
  } catch {
    return u;
  }
}

function host(u) {
  try {
    return new URL(u).hostname.toLowerCase();
  } catch {
    return "";
  }
}

module.exports.default = async function ({ page }) {
  const dir = process.env.A11Y_FROZEN_DIR;
  if (!dir) throw new Error("A11Y_FROZEN_DIR is not set");
  const index = JSON.parse(fs.readFileSync(path.join(dir, "index.json"), "utf8"));
  const pages = Object.values(index);
  if (!pages.length) throw new Error("No frozen pages in " + dir);
  const tested = new Set(pages.flatMap((p) => [key(p.url), key(p.final_url)]));
  const hosts = new Set(pages.flatMap((p) => [host(p.url), host(p.final_url)]));
  const liveLog = process.env.A11Y_LIVE_LOG;
  const note = (row) => {
    if (liveLog) {
      fs.appendFileSync(liveLog, JSON.stringify({ ts: new Date().toISOString(), ...row }) + "\n");
    }
  };
  // Registered first, so it runs last: what no recording answered.
  await page.route("**", async (route) => {
    const req = route.request();
    const url = req.url();
    let frame = null;
    try {
      frame = req.frame();
    } catch {}
    const topLevel = req.isNavigationRequest() && frame && !frame.parentFrame();
    if (topLevel) {
      if (tested.has(key(url))) return route.abort("blockedbyclient"); // frozen only
      if (hosts.has(host(url))) {
        note({ url, live: true });
        return route.continue();
      }
      note({ url, refused: "not the tested site" });
      return route.abort("blockedbyclient");
    }
    if (tested.has(key(page.url()))) return route.abort("failed"); // as the replay
    return route.continue();
  });
  const recs = prepare(dir, pages);
  for (const r of recs) {
    await page.routeFromHAR(r.har, { notFound: "fallback" });
  }
  // Fail again what failed while recording and no recording holds.
  const ok = new Set();
  const failed = new Set();
  for (const r of recs) for (const u of r.failed) failed.add(u);
  for (const r of recs) {
    for (const e of JSON.parse(fs.readFileSync(r.har, "utf8")).log.entries) {
      ok.add(e.request.url);
    }
  }
  for (const u of ok) failed.delete(u);
  if (failed.size) {
    await page.route((u) => failed.has(u.href), (route) => route.abort("failed"));
  }
};
