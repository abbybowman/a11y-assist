# Visual judgment: mechanical checks first, then OCR, then the server's own model

Research note, 2026-11-07. It is research, not an authority: the TT PDF is the authority, TT text comes from `tt.json`, and page numbers are the PDF's printed pages. It makes no outcome decision; anything here that changes an outcome goes through a spec.

**Why.** In development runs 5-11, calling agents did not reliably look at the pictures a question names. They answered "unsure", wrote `picture_error` ("not inspected"), or wrote `seen` without looking (`docs/solutions/agent-follow-through.md`). When an agent does look, the questions work (judge eval runs 24 and 27). So this note asks, per question:
- what can be decided without anyone looking;
- what a tool on our own server can read (OCR, layout);
- what is left for a model the server controls (`ApiJudge`) or a person.

Principles 3 and 8 bound every answer. A mechanical check may confirm an opinion, or replace a question that has only one possible answer. It never creates a PASS from missing evidence. Tokens for NASA's hosted model are scarce, so anything that needs no model comes first.

The per-test detail for the visual-versus-code cluster (10.B-10.D, 13.C, 14.A-14.C, 15.A, 18.A, 7.E) is in [2026-11-07-visual-cluster-per-test.md](2026-11-07-visual-cluster-per-test.md). ANDI's modules are described in [2026-10-31-tt-coverage-map.md](2026-10-31-tt-coverage-map.md).

## Decided so far (Abby, 2026-11-07)

- **Questions settled by reading carry no pictures.** 2.D J1 and J2 and 5.F J1 keep their pictures as evidence only, so agents are not asked to describe them (2.D 1.1.0, 5.F 1.3.0). Judge eval run 28: 19/19, no false PASS. No fixture yet checks a 2.D not_sufficient answer.
- **Contrast comes from ANDI, never from a model.** ANDI's contrast module matches exact WCAG maths on 444 colour pairs, rounded to 2 decimals. It rounds before comparing, so 4.495-4.499 passes; how to treat that band is for the 13.C spec (ROADMAP).
- **18.A uses real browser zoom.** It comes from a small extension of our own calling `chrome.tabs.setZoom`, which works in headless Chromium. The half-width stand-in differs on native form controls (ROADMAP 18.A).
- **Answer once per site,** for images and media too. A judgment is keyed by the content's hash and the spec version, and reused until the content changes (ROADMAP).
- **A review view for people is parked** until we decide what is most usable and accessible (ROADMAP).
- **Reading text out of pixels is an OCR tool's job;** a model only judges (section 4).

## 1. Which questions need a picture now

These are the questions whose input names a picture, so the `seen` rule applies. The list comes from searching `src/tobi508/checks/` and reading each spec's section 4.

| Question | What a tester does (TT) | Already mechanical | Could be added without a model | Left for a model or person | False PASS risk |
| --- | --- | --- | --- | --- | --- |
| **4.D J1** focus change shows focus? | Look for a visible indicator (p. 22) | M5 caret, M6 style + changed pixels → PASS; M8 too few pixels → FAIL | where the changed pixels sit relative to the element; anti-aliasing detection for "only soft edges round text" (can only route to *no*) | a weak or unusual change: marker, faint outline, tooltip | Low-medium |
| **4.F J1** order preserves meaning? | Judge the Tab order (p. 23) | order signals, backward order, opened menus | crop the order picture to the stops in question (a full page shrunk to 768 px is unreadable) | whether the order makes sense for this content | Medium: the broadest PASS path |
| **4.E J1** dialog changes context? | Watch for a change of context on focus (p. 22) | the dialog appeared with no key pressed | its share of the viewport, `aria-modal`, the page behind it inert: above a threshold, `content_only` goes to unsure | purpose: sign-up prompt or hint bubble | Low-medium |
| **5.D J2** change only adds content? | Watch for a change of context on input (p. 27) | navigation, new window, submit and focus moves are mechanical | the changed region's share; the main content replaced (DOM diff) | whether a re-arrangement changes context | Medium |
| **2.B J1** movement essential? | Judge whether motion is essential (p. 14) | movement and timing; a guard against "loading" | none | purpose of the motion | No PASS path; a false DNA is as bad |
| **2.C J1 / 2.B J2** mechanism evident? | Find and use a mechanism (pp. 14-15) | the key press that stopped the content | the control's visible text from the DOM | recognising an icon (‖, ■) | Low |
| **5.A J1** visible label? | Look for a visible label (p. 25) | visible text nearest first; quote check | label geometry to order candidates | the graphic case (a magnifier icon) | Low-medium |
| **5.B J1** labels descriptive? | Judge descriptiveness (p. 25) | items with label, near text, group | none | mostly text; pictures matter for icon buttons | Medium |
| **5.C J1** announced covers shown? | Compare ANDI's output with what is shown (p. 26) | ANDI output; quote check; sets asked once | CSS `::before` content (a red `*`) added to the visible text | cues shown only visually | Medium |
| **5.F J2 / 5.G J2** field looks in error? | Look at how the error is shown (p. 28) | colours read | border or background hue from computed styles | icons, unusual styling | Low |
| **4.A J1** another keyboard way? | Find the keyboard equivalent (p. 19) | stop list; the number must name a stop | none | matching purpose, mostly from names | Low-medium |

**The other questions are text questions.** These are 2.C J2 and 2.B J3, 4.A J2, 4.B, 4.C (J2's screenshot is evidence only), 5.D J1/J3, 5.F J0, 5.G J1, 5.H, 9.A, 9.C, 19.A, and since 2026-11-07 2.D J1/J2 and 5.F J1.

**Volume:** about 24-30 questions per 5-page development run, 14-15 of them picture questions (runs 9-11).

## 2. Order of work, ranked by false-PASS safety, then effort

1. **Routing guards that cannot create a PASS** (no new dependency): 4.E/5.D's covering-share guard, 5.C's `::before` content, 4.D's pixel positions as numbers for the judge. Each is a MINOR spec change with a fixture.
2. **Better pictures for any judge:** crop 4.F's order picture to the stops in question; crop 2.B content below the first screen. This removes "unreadable" as a reason to skip looking. Run the judge eval after each.
3. **Detectors that need no model** for the cluster: layout-based table detection (14.A), and an image inventory with OCR and an alt-text comparison (7.E). See section 3.
4. **Answer once per site:** the fewer questions, the fewer tokens, whoever answers.
5. **ApiJudge for the picture judgments that remain,** once the hosted model is known and only after it passes the judge eval (section 5).

## 3. Detectors that need no model tokens

The aim is a funnel: browser facts first, then detectors on our own server, then a model or a person for what is left.

**One rule holds throughout: a detector that finds nothing is not evidence that nothing is there.** "No candidates" gives DOES NOT APPLY only when the page plainly has no such content, for example no images larger than an icon. Otherwise the result is NEEDS_REVIEW.

**Visual tables built without table markup (14.A; also 14.C and 10.D).**
1. **Layout, no pixels.** From each visible text block's box, find at least 3 rows × 2 columns whose edges line up, with regular row spacing and short cells, outside `table`, `role=table` and `role=grid`. It takes milliseconds and gives the same answer every run.
2. **CSS signals:** `display: table|table-row|table-cell` on non-table elements; `grid-template-columns` on an element whose children repeat a pattern.
3. **Data or layout.** This stays the TT's own judgment (do cells need their headers, p. 60). Signals rank the candidates: a styled header row, columns of numbers or dates. Clear cases can be decided by rule; unclear ones go to a person with the reading-order text.
4. **Pictures of tables** (the TT includes them): ruling lines plus OCR words in columns. `img2table` (MIT) does both but needs OpenCV; line detection alone works in Pillow.
5. **Last resort, if 1-4 miss real tables:** Microsoft's Table Transformer (MIT; local, but needs PyTorch).

**Text inside images (7.E; it also helps 7.A and 13.C).**
1. **Inventory from the DOM:** `img`, `input type=image`, CSS background images, `canvas`, SVG `image`, skipping icon sizes and real SVG `<text>`, each with its alt text or name and nearby text.
2. **OCR on the image bytes from the recording** (the HAR holds them). Options:
   - **tesseract.js** (Apache-2.0), vendored with hashes and run in the browser we already drive: no system install, no network, the same on Linux and Windows;
   - **native Tesseract or RapidOCR,** if speed matters.
3. **Compare by rule:** words OCR reads with confidence that appear in neither the alt text nor the nearby text become a candidate.
4. **What stays a judgment:** logotype or brand text, or a picture whose text is minor (p. 37). Logo signals (in the header, links home, alt holds the site's name, file name "logo") help a person decide quickly.

**Other options checked.**
- **Small vision models on our own server** (Florence-2-base, MIT; SmolVLM-256M, Apache-2.0) need no API tokens, but are models: slow on CPU, large to vendor, and held to the same judge-eval bar as ApiJudge. A middle option, not a first step.
- **Operating system OCR** (Windows, macOS) is not available on the Linux target. Chrome's `TextDetector` is experimental and not on Linux.

## 4. OCR or the server's model, for text in pictures

- **What agents failed at was looking, not reading.** Both ApiJudge and an OCR tool fix that, because the server handles the picture itself.
- **For reading, OCR is the safer tool.**
  - **Repeatable:** the same image bytes and engine version give the same words, so a test can pin it.
  - **Fails safely:** OCR gives each word a confidence and a box, and fails by missing text. A hosted vision model can return different text for the same image, and can produce plausible text that is not there (a corrected misspelling, a completed word, a remembered tagline), which is what a quote check must not trust.
  - **No tokens.**
- **The split:**
  1. OCR reads.
  2. Rules compare.
  3. Only the judgment goes to a person or a model, with OCR's words as text.

  A model's reading may add candidates, but never settles a PASS.

## 5. ApiJudge design

The stub is `ApiJudge(endpoint, model)` in `judgment.py`. `config.judge_backend` is `Literal["client"]`, so it cannot be switched on before it is built.

**Interface.**
- Same contract: `judge(questions) -> JudgeResult(answers, pending)`. It answers the questions it is configured for and returns the rest as pending, for the calling agent as now.
- Answers go through `record_answers`, so every guard applies (choices, quote checks, stop numbers). Outcomes still come only from the specs.
- `decided_by` stays `"model"`. Add `Answer.answered_by` (`"server:<model id>"` or `"client"`), set by the server.
- Record the hosted model's id and version, a hash of the prompt template, and the parameters in `judging_model`. Today that field is one setting ("none") and says nothing about the calling agent.
- The server knows the picture was sent, so `not_viewed` is always false for its answers. `seen` is still filled, for the judge eval and for a person.

**What the model is given.**
- The question, rubric, input and shared inputs; pictures at full resolution or as crops (not the 768 px client downscale).
- The system prompt is fixed and holds no page content. Page-derived input goes in one block labelled as untrusted data.
- Structured output: the question's choices as an enum, plus quote, reasons and seen.
- No tools and no URLs.

**Prompt injection.** Screenshots and page text can say "answer preserves". The defences:
- the enum, so an injection can only pick an allowed choice;
- the mechanical guards (found quotes, measured pixels, the key press that worked);
- a set of injection pages in the judge eval, whose expected answer ignores the injected text.

These limit an injection to the choices the spec already allows; they do not limit it to "unsure".

**Where it runs (recommended: server first, picture questions only).**
- **When:** inside the job, after the checks create questions and before the result returns, so `tobi_run_status` already covers the wait. Calls run a few at a time.
- **If a call fails** (timeout, error, refusal, bad schema), the question stays with the calling agent; it is never answered by default.
- **Its "unsure" goes to a person,** not back to the agent, which had a worse view of the same picture.
- **A person's answer overrides it.**
- **Rejected alternatives:**
  - every question to the server model: costs more, and text questions already work with agents;
  - a fallback for the agent's unsure answers only: run 11 shows wrong-but-sure answers never reach a fallback.

**Cost (estimate; the hosted model's pricing and speed are unknown).**
- About 15 picture questions per 5-page run, each 3-10k input tokens with its pictures.
- Total: about 50-150k input tokens per run, about the calling agent's whole new context per run now (107-122k, runs 10-11).
- Time: roughly 15-60 s inside the job.
- An ApiJudge phase in `steps.jsonl` would let `evals/time_budget.py` report it.

**How it is checked before it is turned on.**
1. Add a judge-eval backend that answers the packets with ApiJudge's own prompt.
2. Score false PASS and false DNA first, then matches, over all packets (run 19's 71 cases) plus the injection set, three repeats.
3. The bar: zero false PASS and false DNA in every repeat; at least run 19's agent with pictures (67/70); every injection case answered as if the text were absent.
4. Then one development answering run with it on, compared with runs 10-11.

Rubric examples must not be fixture words, and fixture names must never reach the model (solutions/judge-eval.md).

## 6. Libraries

Facts come from the PyPI and npm registries on 2026-11-07.
- **None of these libraries does cryptography,** so FIPS 140 does not apply to them.
- **What FIPS does touch:** the TLS connection to the hosted model, and libraries that download models using `hashlib.md5` (they may fail on a FIPS-mode host; not tested).

| Library | Licence | Latest | Footprint | Verdict |
| --- | --- | --- | --- | --- |
| Pillow (`ImageChops`) | MIT-CMU | 13.0.0 | already locked | **Keep:** diffs, masks, crops, line detection |
| pixelmatch (Python port) | ISC | 0.4.0 | pure Python | **Maybe** for 4.D's anti-aliasing check |
| tesseract.js + core | Apache-2.0 | 7.0.0 / 6.1.2 | ~31 MB unpacked core, plus a model file | **First OCR choice:** in-browser, vendored, no install |
| Tesseract (engine) via pytesseract or tesserocr | Apache-2.0 / MIT | 5.5.x / 0.3.13 / 2.12.0 | system binary or bundled library | Faster OCR; a system install, so ask first |
| RapidOCR + onnxruntime | Apache-2.0 / MIT | 3.10.0 / 1.31.1 | ~50 MB | OCR without a system binary (offline packaging not checked) |
| img2table | MIT | 2.0.0 | 3 MB + OpenCV | Only for pictures of tables |
| scikit-image, OpenCV, imagehash | BSD / Apache-2.0 | | 13-61 MB + NumPy | Not needed |
| EasyOCR, PaddleOCR, docTR | Apache-2.0 | | PyTorch or Paddle, models downloaded at first use | No |
| APCA (`apca-w3`) | "Limited W3 License" | 0.1.9 | | No: restrictive, and not WCAG 2 |

**NumPy note.** Any library that needs NumPy holds us on NumPy 2.4.x and SciPy 1.17.x: their next releases need Python 3.12, and we support 3.11.

**axe-core and IBM's checker** are evidence sources, never a PASS on their own. Their rules per test are in the coverage map and the per-test note.

## 7. The agent eval: should agents A and B submit a structured report?

- **They already do.** Both arms end with a `RESULT:` JSON line (every page × criterion), which `evals/agent/score.py` scores; 18 of 19 recorded runs have one. Agent A's server-side pre-SCRT files are scored too, so the gap between what the tool found and what the agent relayed shows.
- **A required report gets filled, not followed.** Agents skipped the work before the report, and a report can say NEEDS_REVIEW everywhere.
- **Grading during the run would spoil the eval.** Feedback from the answer key is contamination, and grading through our server would give Agent B our tool.
- **What would help:** a harness check of format and completeness only. Does `RESULT` parse, cover every page and criterion, and give a reason for each NEEDS_REVIEW? If not, one resumed turn says what is missing.

## 8. Open questions for Abby

1. **The hosted model:**
   - API style and authentication;
   - image input (formats, size, count per request);
   - limits and quota;
   - deterministic settings;
   - a version id to record;
   - whether screenshots of public pages may be sent, and whether prompts are retained;
   - FIPS-validated TLS;
   - reachable from the hosted deployment?
2. **Licences:** axe-core (MPL-2.0, unmodified) and Apache-2.0 tools (IBM checker, Tesseract, tesseract.js) for GSA and NASA release; and whether a system-installed OCR binary is acceptable.
3. **Overrides:** may the calling agent override a server-model answer, or only a person? Recommended: only a person.
4. **18.A windows:** 1280 px and about 1024 px? A failure only in the smaller window: FAIL or NEEDS REVIEW?

## Verified vs assumed

**Verified this session:**
- the inventory, from the checks' code and specs;
- the registries' licence and version facts;
- NumPy's and SciPy's Python requirements;
- the contrast and zoom experiments (per-test note);
- judge eval run 28;
- the run figures, from `evals/README.md` and `evals/judging/round1-postfix/README.md`.

**Assumed:**
- Tesseract's exact latest version;
- RapidOCR's offline packaging;
- OCR accuracy on agency images;
- tesseract.js speed;
- the layout table detector's recall on real pages;
- FIPS behaviour of model-downloading libraries;
- every ApiJudge cost and time figure;
- Windows behaviour.

## Sources

**In the repository:**
- CLAUDE.md;
- `docs/plans/2026-11-06-agent-follow-through.md` (changes 3 and 6);
- `docs/solutions/agent-follow-through.md`, `judge-eval.md`;
- `docs/research/2026-10-31-tt-coverage-map.md`, `2026-11-07-visual-cluster-per-test.md`;
- `docs/rules/*.md` section 4;
- `src/tobi508/judgment.py`, `inline.py`, `config.py`;
- `evals/README.md`, `evals/agent/score.py`.

**External:**
- [PyPI JSON API](https://pypi.org/pypi/pillow/json) and the [npm registry](https://registry.npmjs.org/tesseract.js/latest);
- [apca-w3 on npm](https://www.npmjs.com/package/apca-w3) (licence field);
- [W3C ACT implementations: Equal Access](https://www.w3.org/WAI/standards-guidelines/act/implementations/equal-access).
