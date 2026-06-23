const $ = (s, el = document) => el.querySelector(s);
let POSTS = [];
let SELECTED = null;

async function load() {
  POSTS = await (await fetch("/api/posts")).json();
  buildFilters();
  renderGallery();
}

function buildFilters() {
  const dates = ["all", ...new Set(POSTS.map((p) => p.date))];
  const tks = ["all", ...new Set(POSTS.map((p) => p.ticker))];
  $("#filter-date").innerHTML = dates.map((d) => `<option>${d}</option>`).join("");
  $("#filter-ticker").innerHTML = tks.map((t) => `<option>${t}</option>`).join("");
}

function shown() {
  const d = $("#filter-date").value, t = $("#filter-ticker").value;
  return POSTS.filter((p) => (d === "all" || p.date === d) && (t === "all" || p.ticker === t));
}

function thumb(p) {
  const mp4 = p.media.find((m) => m.endsWith(".mp4"));
  const png = p.media.find((m) => m.endsWith(".png"));
  if (mp4) return `<video src="${mp4}" muted preload="metadata"></video>`;
  if (png) return `<img src="${png}" alt="${p.ticker}" />`;
  return `<span>${p.kind}</span>`;
}

function renderGallery() {
  const groups = {};
  for (const p of shown()) (groups[p.date] ??= []).push(p);
  const dates = Object.keys(groups).sort().reverse();
  $("#gallery").innerHTML = dates.map((date) => `
    <div class="daygroup"><h2>${date}</h2><div class="grid">
      ${groups[date].map((p) => `
        <button class="tile" data-id="${p.post_id}">
          <div class="thumb">${thumb(p)}</div>
          <div class="meta"><b>${p.ticker}</b><span>${p.kind}${
            p.open_comment_count ? ` <span class="badge">${p.open_comment_count}</span>` : ""
          }</span></div>
        </button>`).join("")}
    </div></div>`).join("");
  for (const b of document.querySelectorAll(".tile"))
    b.onclick = () => select(b.dataset.id);
}

async function select(postId) {
  SELECTED = POSTS.find((p) => p.post_id === postId);
  await renderDetail();
}

async function renderDetail() {
  const p = SELECTED;
  const det = $("#detail");
  det.hidden = false;
  const mp4 = p.media.find((m) => m.endsWith(".mp4"));
  const slides = p.media.filter((m) => m.endsWith(".png"));
  const cs = await (await fetch(`/api/comments?post_id=${encodeURIComponent(p.post_id)}`)).json();
  det.innerHTML = `
    <h3>${p.ticker} · ${p.kind} <span style="color:#888">${p.date}</span></h3>
    ${mp4 ? `<video src="${mp4}" controls></video>`
          : slides.map((s) => `<img class="slide" src="${s}" />`).join("")}
    <div class="label">CAPTION</div>
    <div class="block">${escapeHtml(p.caption || "(none)")}</div>
    ${p.kind === "reel"
      ? `<div class="label">AUDIO SCRIPT (pushed to Higgsfield)</div>
         <div class="block">${escapeHtml(p.audio_script || "(none)")}</div>`
      : `<div class="label">AUDIO SCRIPT</div><div class="block">no audio for this post</div>`}
    <div class="label">COMMENTS</div>
    <div id="comment-list">${cs.map(commentHtml).join("") || '<div class="block">No comments yet.</div>'}</div>
    <form class="add" id="add-form">
      <select id="add-part">
        <option value="general">general</option>
        <option value="caption">caption</option>
        <option value="audio">audio</option>
        <option value="visual">visual</option>
      </select>
      <textarea id="add-text" placeholder="Add a comment for regeneration…"></textarea>
      <button type="submit">Add comment</button>
    </form>`;
  $("#add-form").onsubmit = addComment;
  for (const el of det.querySelectorAll("[data-resolve]"))
    el.onclick = () => patchComment(el.dataset.resolve, { resolved: el.dataset.next === "true" });
  for (const el of det.querySelectorAll("[data-del]"))
    el.onclick = () => delComment(el.dataset.del);
}

function commentHtml(c) {
  return `<div class="comment ${c.resolved ? "resolved" : ""}">
    <div class="row"><span class="chip">${c.part}</span><span>${c.created_at}</span>
      <span style="margin-left:auto">
        <a href="#" data-resolve="${c.id}" data-next="${!c.resolved}">${c.resolved ? "reopen" : "resolve"}</a>
        · <a href="#" data-del="${c.id}">delete</a></span></div>
    <div>${escapeHtml(c.text)}</div></div>`;
}

async function addComment(e) {
  e.preventDefault();
  const text = $("#add-text").value.trim();
  if (!text) return;
  await fetch("/api/comments", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ post_id: SELECTED.post_id, part: $("#add-part").value, text }),
  });
  await refreshCounts();
  await renderDetail();
}

async function patchComment(id, body) {
  await fetch(`/api/comments/${id}`, {
    method: "PATCH", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  await refreshCounts();
  await renderDetail();
}

async function delComment(id) {
  await fetch(`/api/comments/${id}`, { method: "DELETE" });
  await refreshCounts();
  await renderDetail();
}

async function refreshCounts() {
  POSTS = await (await fetch("/api/posts")).json();
  SELECTED = POSTS.find((p) => p.post_id === SELECTED.post_id) || SELECTED;
  renderGallery();
}

function escapeHtml(s) {
  return (s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

$("#refresh").onclick = load;
$("#filter-date").onchange = renderGallery;
$("#filter-ticker").onchange = renderGallery;
load();

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
      <button class="script-row" data-name="${escapeHtml(e.name)}" data-media="${escapeHtml(e.media)}" data-kind="${escapeHtml(e.kind)}">
        <span class="sname">${escapeHtml(e.name)}</span>
        <span class="kind-chip ${e.kind === "kit" ? "kit" : ""}">${escapeHtml(e.kind)}</span>
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
  renderScript(el, name, kind, text, isMd, /*raw=*/false);
}

function renderScript(el, name, kind, text, isMd, raw) {
  const toggle = isMd
    ? `<button class="sc-toggle" id="md-toggle">${raw ? "Rendered" : "Raw"}</button>` : "";
  const body = (isMd && !raw)
    ? `<div class="md-body">${renderMarkdown(text)}</div>`
    : `<pre class="${isMd ? "raw-content" : "txt-content"}">${escapeHtml(text)}</pre>`;
  el.innerHTML = `<div class="sc-head"><span class="sc-title">${escapeHtml(name)} · ${escapeHtml(kind)}</span>${toggle}</div>${body}`;
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
