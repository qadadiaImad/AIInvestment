"""Post-review dashboard — Flask app factory and routes."""
from __future__ import annotations

import datetime
import os
import pathlib

from flask import Flask, abort, jsonify, request, send_file

import comments
import index
from captions import parse_captions
from paths import CONTENT, FEEDBACK_FILE, HIGGS, REPO_ROOT


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _list_higgs() -> list[str]:
    return [p.name for p in HIGGS.iterdir() if p.is_file()] if HIGGS.exists() else []


def _list_content() -> list[str]:
    out: list[str] = []
    if CONTENT.exists():
        for p in CONTENT.rglob("*"):
            if p.is_file():
                out.append(p.relative_to(CONTENT).as_posix())
    return out


def _caption_for(post: dict) -> str | None:
    date, ticker, kind = post["date"], post["ticker"], post["kind"]
    primary = f"reels_{date}.txt" if kind == "reel" else f"posts_{date}.txt"
    fallback = f"posts_{date}.txt" if kind == "reel" else f"reels_{date}.txt"
    for name in (primary, fallback):
        f = HIGGS / name
        if f.exists():
            parsed = parse_captions(f.read_text("utf-8"))
            if ticker in parsed:
                return parsed[ticker]
    return None


def _build_posts() -> list[dict]:
    posts = index.build_index(_list_higgs(), _list_content())
    store = comments.read_store(FEEDBACK_FILE)
    for p in posts:
        cap = _caption_for(p)
        p["caption"] = cap
        p["audio_script"] = cap if p["kind"] == "reel" else None
        all_c = comments.load_for_post(store, p["post_id"], only_open=False)
        open_c = [c for c in all_c if not c["resolved"]]
        p["comment_count"] = len(all_c)
        p["open_comment_count"] = len(open_c)
    return posts


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", static_url_path="")

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

    @app.get("/api/posts")
    def posts():
        return jsonify(_build_posts())

    @app.get("/api/comments")
    def get_comments():
        store = comments.read_store(FEEDBACK_FILE)
        post_id = request.args.get("post_id")
        items = (comments.load_for_post(store, post_id, only_open=False)
                 if post_id else store["comments"])
        return jsonify(items)

    @app.post("/api/comments")
    def post_comment():
        body = request.get_json(silent=True) or {}
        try:
            store = comments.read_store(FEEDBACK_FILE)
            store, c = comments.add_comment(
                store, body.get("post_id", ""), body.get("part", ""),
                body.get("text", ""), _now())
        except (ValueError, KeyError) as e:
            abort(400, str(e))
        comments.write_store(FEEDBACK_FILE, store)
        return jsonify(c), 201

    @app.patch("/api/comments/<cid>")
    def patch_comment(cid):
        body = request.get_json(silent=True) or {}
        store = comments.read_store(FEEDBACK_FILE)
        try:
            if "resolved" in body:
                store = comments.set_resolved(store, cid, body["resolved"])
            if "text" in body:
                store = comments.edit_comment(store, cid, body["text"])
        except KeyError:
            abort(404)
        except ValueError as e:
            abort(400, str(e))
        comments.write_store(FEEDBACK_FILE, store)
        updated = next(c for c in store["comments"] if c["id"] == cid)
        return jsonify(updated)

    @app.delete("/api/comments/<cid>")
    def delete_comment(cid):
        store = comments.read_store(FEEDBACK_FILE)
        try:
            store = comments.delete_comment(store, cid)
        except KeyError:
            abort(404)
        comments.write_store(FEEDBACK_FILE, store)
        return jsonify({"ok": True})

    @app.get("/media/<path:rel>")
    def media(rel):
        root = REPO_ROOT.resolve()
        target = (root / rel).resolve()
        if target != root and root not in target.parents:
            abort(403)
        if not target.is_file():
            abort(404)
        return send_file(target, conditional=True)

    @app.get("/")
    def home():
        return app.send_static_file("index.html")

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5005, debug=True)
