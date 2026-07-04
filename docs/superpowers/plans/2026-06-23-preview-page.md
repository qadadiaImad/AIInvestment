# Preview Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Preview" page to the post-review dashboard (`review/`) that lists the pre-creation script/kit docs in `higgs/` and shows their content — `.txt` scripts as formatted text, `.md` kits rendered with a Raw toggle.

**Architecture:** A pure `scripts.list_scripts()` listing module (TDD), one new `GET /api/scripts` Flask route, and a frontend Preview view added beside the existing Posts gallery (a header nav toggle). File content is fetched from the EXISTING path-guarded `/media/` route; markdown is rendered by a small built-in vanilla-JS renderer (escape-then-format, no external library, no build step).

**Tech Stack:** Python 3.14, Flask, pytest (existing `review/` app). Vanilla HTML/CSS/JS frontend. Runs at `http://localhost:5005`.

**Spec:** `docs/superpowers/specs/2026-06-23-preview-page-design.md`

## Global Constraints

- All changes are under `review/`. Run commands from `review/` (so imports resolve top-level, e.g. `import scripts`). Additive only — do not change existing Posts/gallery/comments behavior.
- The three doc kinds (exact strings): `reels_<date>.txt` → `"reel-script"`; `posts_<date>.txt` → `"post-script"`; `reels_<date>_kit.md` → `"kit"`. `<date>` is `YYYY-MM-DD`. Every other filename is excluded.
- Script list entry shape: `{"name": str, "date": str, "kind": str, "media": "/media/higgs/<name>"}`.
- Sort: newest `date` first; within a date, kind order `kit` → `reel-script` → `post-script`, then `name` ascending.
- File content is served by the EXISTING `GET /media/<path>` route — do NOT add a new content endpoint.
- Markdown is rendered by a BUILT-IN vanilla-JS renderer: **HTML-escape the source first, then apply markdown** (security boundary). No external library, no CDN, no build step. Links open in a new tab (`target="_blank" rel="noopener noreferrer"`).
- House colors: bg `#0A0D12`, panel `#0B0E14`, text `#E8EDF2`, accent emerald `#34D399`.
- `import scripts` in `app.py` must resolve to `review/scripts.py` (the app runs with cwd `review/`, so `review/` is first on `sys.path` — note the repo-root `scripts/` dir exists but is not on the path here).

---

## Task 1: `scripts.py` listing module (pure, TDD)

**Files:**
- Create: `review/scripts.py`
- Create: `review/tests/test_scripts.py`

**Interfaces:**
- Produces: `scripts.list_scripts(higgs_files: list[str]) -> list[dict]`. Each dict: `{name, date, kind, media}` where `kind` ∈ `reel-script`/`post-script`/`kit`, `media` = `/media/higgs/<name>`. Sorted newest-date-first, then kind (kit→reel-script→post-script), then name. Non-matching filenames excluded.

- [ ] **Step 1: Write the failing test `review/tests/test_scripts.py`**

```python
from scripts import list_scripts


def test_classifies_three_kinds_and_excludes_others():
    files = ["reels_2026-06-23.txt", "reels_2026-06-23_kit.md", "posts_2026-06-03.txt",
             "reels_manifest.json", "make_reel.py", "hero_nvda.png", "reel_nvda_2026-06-22.mp4"]
    out = list_scripts(files)
    kinds = {e["name"]: e["kind"] for e in out}
    assert kinds["reels_2026-06-23.txt"] == "reel-script"
    assert kinds["reels_2026-06-23_kit.md"] == "kit"
    assert kinds["posts_2026-06-03.txt"] == "post-script"
    names = [e["name"] for e in out]
    for excluded in ("reels_manifest.json", "make_reel.py", "hero_nvda.png", "reel_nvda_2026-06-22.mp4"):
        assert excluded not in names
    e = next(e for e in out if e["name"] == "reels_2026-06-23.txt")
    assert e["date"] == "2026-06-23"
    assert e["media"] == "/media/higgs/reels_2026-06-23.txt"


def test_sorted_newest_date_first_then_kind():
    files = ["posts_2026-06-03.txt", "reels_2026-06-23.txt", "reels_2026-06-23_kit.md"]
    out = list_scripts(files)
    assert out[0]["date"] == "2026-06-23"
    assert out[-1]["date"] == "2026-06-03"
    d23 = [e["kind"] for e in out if e["date"] == "2026-06-23"]
    assert d23.index("kit") < d23.index("reel-script")


def test_empty_input():
    assert list_scripts([]) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd review && python -m pytest tests/test_scripts.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts'`

- [ ] **Step 3: Implement `review/scripts.py`**

```python
"""List the higgs/ pre-creation planning docs (reel scripts, post scripts, kit markdown)
for the Preview page. Pure: takes a filename list, returns sorted entries."""
from __future__ import annotations

import re

_KIND_ORDER = {"kit": 0, "reel-script": 1, "post-script": 2}


def _classify(name: str):
    m = re.match(r"^reels_(\d{4}-\d{2}-\d{2})_kit\.md$", name)
    if m:
        return m.group(1), "kit"
    m = re.match(r"^reels_(\d{4}-\d{2}-\d{2})\.txt$", name)
    if m:
        return m.group(1), "reel-script"
    m = re.match(r"^posts_(\d{4}-\d{2}-\d{2})\.txt$", name)
    if m:
        return m.group(1), "post-script"
    return None


def list_scripts(higgs_files: list[str]) -> list[dict]:
    out = []
    for name in higgs_files:
        c = _classify(name)
        if not c:
            continue
        date, kind = c
        out.append({"name": name, "date": date, "kind": kind,
                    "media": f"/media/higgs/{name}"})
    # newest date first; within a date: kit -> reel-script -> post-script, then name asc.
    out.sort(key=lambda e: e["name"])
    out.sort(key=lambda e: _KIND_ORDER.get(e["kind"], 9))
    out.sort(key=lambda e: e["date"], reverse=True)
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd review && python -m pytest tests/test_scripts.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add review/scripts.py review/tests/test_scripts.py
git commit -m "feat(review): script/kit listing module for preview page, TDD"
```

---

## Task 2: `GET /api/scripts` route

**Files:**
- Modify: `review/app.py`
- Modify: `review/tests/test_api.py`

**Interfaces:**
- Consumes: `scripts.list_scripts` (Task 1); the existing `_list_higgs()` helper in `app.py`.
- Produces: `GET /api/scripts` → JSON list from `list_scripts(<higgs filenames>)`.

- [ ] **Step 1: Add the failing API test to `review/tests/test_api.py`** (append; the `client` fixture already exists in this file)

```python
def test_scripts_endpoint_lists_kit_and_reel_script(client):
    r = client.get("/api/scripts")
    assert r.status_code == 200
    names = [e["name"] for e in r.get_json()]
    assert "reels_2026-06-23.txt" in names
    assert "reels_2026-06-23_kit.md" in names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd review && python -m pytest tests/test_api.py::test_scripts_endpoint_lists_kit_and_reel_script -v`
Expected: FAIL — 404 (route not defined yet).

- [ ] **Step 3: Add the import and route to `review/app.py`**

Add `import scripts` alongside the existing `import comments` / `import index` lines near the top:
```python
import comments
import index
import scripts
```
Add this route inside `create_app()`, right after the existing `@app.get("/api/posts")` handler:
```python
    @app.get("/api/scripts")
    def scripts_list():
        return jsonify(scripts.list_scripts(_list_higgs()))
```

- [ ] **Step 4: Run the test (and the full suite) to verify pass**

Run: `cd review && python -m pytest tests/test_api.py -v`
Expected: PASS (the new test + the existing API tests).
Run: `cd review && python -m pytest -q`
Expected: all tests pass (paths + captions + index + comments + scripts + api).

- [ ] **Step 5: Commit**

```bash
git add review/app.py review/tests/test_api.py
git commit -m "feat(review): GET /api/scripts route (content via existing /media)"
```

---

## Task 3: Preview view — nav toggle, script list, content panel, markdown renderer

**Files:**
- Modify: `review/static/index.html`
- Modify: `review/static/app.js`
- Modify: `review/static/styles.css`

**Interfaces:**
- Consumes: `GET /api/scripts`, and `GET /media/higgs/<name>` (existing) for content.
- Produces: the Preview UI. No exported JS interface (browser entry only).

- [ ] **Step 1: Replace `review/static/index.html` with the nav toggle + two view sections**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Post Review</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <header>
      <span class="brand">POST REVIEW</span>
      <nav class="views">
        <button id="nav-posts" class="active">Posts</button>
        <button id="nav-preview">Preview</button>
      </nav>
      <span class="filters">
        <select id="filter-date"></select>
        <select id="filter-ticker"></select>
        <button id="refresh">Refresh</button>
      </span>
    </header>
    <main>
      <section id="posts-view">
        <section id="gallery"></section>
        <aside id="detail" hidden></aside>
      </section>
      <section id="preview-view" hidden>
        <section id="script-list"></section>
        <aside id="script-content"><div class="empty">Select a script to preview.</div></aside>
      </section>
    </main>
    <footer>Educational / market-commentary only — not financial advice.</footer>
    <script src="app.js"></script>
  </body>
</html>
```

- [ ] **Step 2: Append the Preview logic + markdown renderer + nav wiring to `review/static/app.js`**

Append this to the END of `review/static/app.js` (it reuses the existing `$` and `escapeHtml` helpers already defined in that file):

```javascript
// ---- Preview view (script/kit monitoring) ----
let scriptsLoaded = false;

function showView(v) {
  document.getElementById("posts-view").hidden = v !== "posts";
  document.getElementById("preview-view").hidden = v !== "preview";
  $("#nav-posts").classList.toggle("active", v === "posts");
  $("#nav-preview").classList.toggle("active", v === "preview");
  if (v === "preview" && !scriptsLoaded) { scriptsLoaded = true; loadScripts(); }
}

async function loadScripts() {
  const items = await (await fetch("/api/scripts")).json();
  const groups = {};
  for (const e of items) (groups[e.date] ??= []).push(e);
  const dates = Object.keys(groups).sort().reverse();
  $("#script-list").innerHTML = dates.map((date) => `
    <div class="sdate">${date}</div>
    ${groups[date].map((e) => `
      <button class="script-row" data-name="${e.name}" data-media="${e.media}" data-kind="${e.kind}">
        <span class="sname">${e.name}</span>
        <span class="kind-chip ${e.kind === "kit" ? "kit" : ""}">${e.kind}</span>
      </button>`).join("")}`).join("");
  for (const b of document.querySelectorAll(".script-row"))
    b.onclick = () => showScript(b);
}

async function showScript(btn) {
  for (const b of document.querySelectorAll(".script-row")) b.classList.remove("active");
  btn.classList.add("active");
  const { name, media, kind } = btn.dataset;
  const text = await (await fetch(media)).text();
  const isMd = name.endsWith(".md");
  const el = $("#script-content");
  el.dataset.text = text;       // stash for the Raw/Rendered toggle
  el.dataset.md = isMd ? "1" : "";
  renderScript(el, name, kind, text, isMd, /*raw=*/false);
}

function renderScript(el, name, kind, text, isMd, raw) {
  const toggle = isMd
    ? `<button class="sc-toggle" id="md-toggle">${raw ? "Rendered" : "Raw"}</button>` : "";
  const body = (isMd && !raw)
    ? `<div class="md-body">${renderMarkdown(text)}</div>`
    : `<pre class="${isMd ? "raw-content" : "txt-content"}">${escapeHtml(text)}</pre>`;
  el.innerHTML = `<div class="sc-head"><span class="sc-title">${name} · ${kind}</span>${toggle}</div>${body}`;
  if (isMd) $("#md-toggle").onclick = () =>
    renderScript(el, name, kind, text, true, !raw);
}

function renderInline(s) {
  // s is already HTML-escaped. Apply inline markdown.
  return s
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>")
    .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
}

function renderMarkdown(src) {
  const lines = escapeHtml(src).split("\n");   // ESCAPE FIRST, then format
  const html = [];
  let i = 0, inList = false;
  const closeList = () => { if (inList) { html.push("</ul>"); inList = false; } };
  while (i < lines.length) {
    const line = lines[i];
    if (/^```/.test(line)) {
      closeList();
      const buf = []; i++;
      while (i < lines.length && !/^```/.test(lines[i])) { buf.push(lines[i]); i++; }
      i++;
      html.push("<pre class='md-code'><code>" + buf.join("\n") + "</code></pre>");
      continue;
    }
    if (/^\s*\|.*\|\s*$/.test(line) && i + 1 < lines.length && /^\s*\|[\s:|-]+\|\s*$/.test(lines[i + 1])) {
      closeList();
      const head = line.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
      i += 2;
      const rows = [];
      while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) {
        rows.push(lines[i].trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim())); i++;
      }
      html.push("<table class='md-table'><thead><tr>" +
        head.map((c) => "<th>" + renderInline(c) + "</th>").join("") + "</tr></thead><tbody>" +
        rows.map((r) => "<tr>" + r.map((c) => "<td>" + renderInline(c) + "</td>").join("") + "</tr>").join("") +
        "</tbody></table>");
      continue;
    }
    let m = line.match(/^(#{1,3})\s+(.*)$/);
    if (m) { closeList(); html.push(`<h${m[1].length}>` + renderInline(m[2]) + `</h${m[1].length}>`); i++; continue; }
    if (/^---+\s*$/.test(line)) { closeList(); html.push("<hr/>"); i++; continue; }
    if (/^>\s?/.test(line)) { closeList(); html.push("<blockquote>" + renderInline(line.replace(/^>\s?/, "")) + "</blockquote>"); i++; continue; }
    if (/^\s*[-*]\s+/.test(line)) {
      if (!inList) { html.push("<ul>"); inList = true; }
      html.push("<li>" + renderInline(line.replace(/^\s*[-*]\s+/, "")) + "</li>"); i++; continue;
    }
    if (/^\s*$/.test(line)) { closeList(); i++; continue; }
    closeList();
    html.push("<p>" + renderInline(line) + "</p>"); i++;
  }
  closeList();
  return html.join("\n");
}

$("#nav-posts").onclick = () => showView("posts");
$("#nav-preview").onclick = () => showView("preview");
```

- [ ] **Step 3: Update `review/static/styles.css` — change the `main` rule and append Preview styles**

Find the existing `main { ... }` rule (it currently is `main { display: flex; height: calc(100vh - 56px - 32px); }`) and REPLACE it with (drop `display:flex` so the view sections own layout):
```css
main { height: calc(100vh - 56px - 32px); }
#posts-view, #preview-view { display: flex; height: 100%; overflow: hidden; }
```
Then APPEND this block to the end of the file:
```css
/* view nav */
nav.views { display: flex; gap: 6px; }
nav.views button { background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.12);
  color: #E8EDF2; border-radius: 6px; padding: 6px 12px; font: inherit; cursor: pointer; }
nav.views button.active { background: rgba(52,211,153,.18); color: #34D399; border-color: rgba(52,211,153,.4); }

/* preview: list + content */
#script-list { width: 320px; border-right: 1px solid rgba(255,255,255,.1); overflow: auto; padding: 12px; }
#script-list .sdate { font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: .18em;
  color: #34D399; margin: 14px 4px 6px; }
.script-row { display: flex; justify-content: space-between; align-items: center; gap: 8px; width: 100%;
  text-align: left; background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.1);
  border-radius: 8px; padding: 8px 10px; margin-bottom: 6px; color: inherit; cursor: pointer; font: inherit; }
.script-row:hover { border-color: rgba(52,211,153,.5); }
.script-row.active { border-color: #34D399; }
.script-row .sname { font-size: 12px; word-break: break-all; }
.kind-chip { font-family: 'JetBrains Mono', monospace; font-size: 10px; padding: 1px 6px; border-radius: 4px;
  background: rgba(255,255,255,.1); white-space: nowrap; }
.kind-chip.kit { background: rgba(52,211,153,.2); color: #34D399; }
#script-content { flex: 1; overflow: auto; padding: 18px; background: #0B0E14; }
#script-content .empty { color: rgba(255,255,255,.3); font-size: 13px; }
.sc-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.sc-title { font-family: 'JetBrains Mono', monospace; font-size: 13px; }
.sc-toggle { font-family: 'JetBrains Mono', monospace; font-size: 11px; background: rgba(255,255,255,.05);
  border: 1px solid rgba(255,255,255,.12); color: #E8EDF2; border-radius: 6px; padding: 4px 10px; cursor: pointer; }
pre.txt-content, pre.raw-content { white-space: pre-wrap; word-break: break-word;
  font-family: 'JetBrains Mono', monospace; font-size: 12px; line-height: 1.5;
  background: rgba(255,255,255,.04); border-radius: 8px; padding: 14px; }

/* rendered markdown */
.md-body { font-size: 14px; line-height: 1.55; }
.md-body h1 { font-size: 22px; } .md-body h2 { font-size: 18px; color: #34D399; } .md-body h3 { font-size: 15px; }
.md-body code { background: rgba(255,255,255,.1); padding: 1px 5px; border-radius: 4px;
  font-family: 'JetBrains Mono', monospace; font-size: .9em; }
.md-body pre.md-code { background: #06080c; border: 1px solid rgba(255,255,255,.1); border-radius: 8px;
  padding: 12px; overflow: auto; }
.md-body pre.md-code code { background: none; padding: 0; }
.md-body blockquote { border-left: 3px solid #34D399; margin: 8px 0; padding: 4px 12px;
  color: #cdd6e0; background: rgba(255,255,255,.03); }
.md-body table.md-table { border-collapse: collapse; margin: 10px 0; font-size: 13px; }
.md-body .md-table th, .md-body .md-table td { border: 1px solid rgba(255,255,255,.15); padding: 6px 10px; text-align: left; }
.md-body hr { border: none; border-top: 1px solid rgba(255,255,255,.12); margin: 14px 0; }
.md-body a { color: #34D399; }
```

- [ ] **Step 4: Smoke test — Preview renders the real kit**

Run (background): `cd review && python app.py`, then in another shell:
- `curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5005/api/scripts` → `200`
- `curl -s http://127.0.0.1:5005/api/scripts | python -c "import sys,json; d=json.load(sys.stdin); print([e['name'] for e in d])"` → includes `reels_2026-06-23.txt` and `reels_2026-06-23_kit.md`
- `curl -s -o /dev/null -w "%{http_code}\n" "http://127.0.0.1:5005/media/higgs/reels_2026-06-23_kit.md"` → `200`
- `curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5005/` and `/app.js` → `200` each
Then kill the server. (Visual confirmation — clicking Preview shows the list; the `.md` renders formatted; the Raw toggle works; a `.txt` shows the formatted sheet — is reserved for the owner at the live browser; state that.)

- [ ] **Step 5: Commit**

```bash
git add review/static
git commit -m "feat(review): Preview page — script/kit list + content + markdown renderer"
```

---

## Self-Review

**Spec coverage:**
- §3/§4 listing module (kinds, date, media, sort) → Task 1.
- §5 `/api/scripts` route + content via existing `/media` → Task 2.
- §6 frontend (nav toggle, list grouped by date, content panel, `.txt` formatted / `.md` rendered + Raw toggle, built-in escape-then-format renderer with links-in-new-tab) → Task 3.
- §7 data flow (open Preview → /api/scripts → click → fetch /media → render) → Task 3.
- §8 testing (pytest list_scripts + /api/scripts; manual md smoke) → Tasks 1,2,3.
- §9 decisions (3 kinds, reuse /media, built-in renderer, read-only) → honored across tasks.

**Placeholder scan:** All steps contain concrete code/commands. No TBD/TODO.

**Type consistency:** `list_scripts` return shape `{name,date,kind,media}` (Task 1) matches the `/api/scripts` consumer (Task 2) and the frontend's `e.name/e.date/e.kind/e.media` + `.script-row data-*` usage (Task 3). Kind strings `reel-script`/`post-script`/`kit` identical across Global Constraints, Task 1, and the Task 3 chip rendering. The `escapeHtml`/`$` helpers used in Task 3's appended code are the ones already defined in the existing `app.js` (from the prior build).

**Known follow-ups (acceptable):** the markdown renderer is intentionally minimal (covers the kit's elements: headings, bold/italic, inline+fenced code, lists, GitHub tables, blockquote, hr, links); exotic markdown (nested lists, setext headings, reference links) falls through as escaped text — acceptable per spec §6. Client-side renderer verified by manual smoke (the project's automated tests are pytest).
