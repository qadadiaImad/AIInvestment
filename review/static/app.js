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
