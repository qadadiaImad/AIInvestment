"""Post-review dashboard — Flask app factory and routes."""
from __future__ import annotations

from flask import Flask, jsonify


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", static_url_path="")

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5005, debug=True)
