// Agent B's replay of a round's frozen pages (docs/plans/2026-10-31-agent-eval.md
// section 6). Playwright MCP runs this on each page it opens (--init-page).
// A11Y_FROZEN_DIR is the folder evals/agent/freeze.py wrote (index.json + HARs).
// Every recording is served; a request no recording holds is aborted, never
// fetched live. Requests that failed while recording (status -1) are failed
// again, as capture.replay_context does: Playwright's HAR replay would
// otherwise wait on them forever.
const fs = require("fs");
const path = require("path");
const zlib = require("zlib");

function harEntries(file) {
  // A .har.zip holds one .har. Read it from the zip's central directory
  // (local headers may leave sizes to a trailing descriptor); no packages.
  const buf = fs.readFileSync(file);
  let eocd = buf.length - 22;
  while (eocd >= 0 && buf.readUInt32LE(eocd) !== 0x06054b50) eocd--;
  if (eocd < 0) throw new Error("Not a zip file: " + file);
  const count = buf.readUInt16LE(eocd + 10);
  let off = buf.readUInt32LE(eocd + 16);
  for (let n = 0; n < count; n++) {
    const method = buf.readUInt16LE(off + 10);
    const csize = buf.readUInt32LE(off + 20);
    const nlen = buf.readUInt16LE(off + 28);
    const xlen = buf.readUInt16LE(off + 30);
    const clen = buf.readUInt16LE(off + 32);
    const local = buf.readUInt32LE(off + 42);
    const name = buf.toString("utf8", off + 46, off + 46 + nlen);
    if (name.endsWith(".har")) {
      const lstart =
        local + 30 + buf.readUInt16LE(local + 26) + buf.readUInt16LE(local + 28);
      const data = buf.subarray(lstart, lstart + csize);
      const text = method === 0 ? data : zlib.inflateRawSync(data);
      return JSON.parse(text.toString("utf8")).log.entries;
    }
    off += 46 + nlen + xlen + clen;
  }
  return [];
}

module.exports.default = async function ({ page }) {
  const dir = process.env.A11Y_FROZEN_DIR;
  if (!dir) throw new Error("A11Y_FROZEN_DIR is not set");
  const index = JSON.parse(fs.readFileSync(path.join(dir, "index.json"), "utf8"));
  const hars = [...new Set(Object.values(index).map((p) => path.join(dir, p.har)))];
  if (!hars.length) throw new Error("No frozen pages in " + dir);
  // Later routes run first: the first HAR aborts what none of them holds.
  for (const [i, har] of hars.entries()) {
    await page.routeFromHAR(har, { notFound: i === 0 ? "abort" : "fallback" });
  }
  const failed = new Set();
  for (const har of hars) {
    for (const e of harEntries(har)) {
      if ((e.response && e.response.status) < 0) failed.add(e.request.url);
    }
  }
  if (failed.size) {
    await page.route((url) => failed.has(url.href), (route) => route.abort("failed"));
  }
};
