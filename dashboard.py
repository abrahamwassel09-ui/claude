"""
SYSTEM 2 — Content Tracker Dashboard
A Flask web app that shows all posts across both models for Thu–Sun,
with status tracking and automatic "Has Images" detection.
"""

import os
import sys
from flask import Flask, render_template, request, jsonify, redirect, url_for

from config import DASHBOARD_HOST, DASHBOARD_PORT, DAYS, MODELS
from database import init_db, get_all_posts, update_post_status, get_file_log

app = Flask(__name__)

STATUSES = ["Not Started", "Written", "Approved", "Scheduled", "Posted"]


@app.route("/")
def index():
    """Main dashboard view."""
    posts = get_all_posts()

    # Group posts: { model: { day: [post_rows] } }
    grid = {}
    for model_key in MODELS:
        grid[model_key] = {}
        for day in DAYS:
            grid[model_key][day] = [
                p for p in posts if p["model"] == model_key and p["day"] == day
            ]

    return render_template(
        "dashboard.html",
        grid=grid,
        models=MODELS,
        days=DAYS,
        statuses=STATUSES,
    )


@app.route("/update_status", methods=["POST"])
def update_status():
    """AJAX endpoint to change a post's status."""
    post_id = request.form.get("post_id", type=int)
    new_status = request.form.get("status", "")
    if post_id and new_status in STATUSES:
        update_post_status(post_id, new_status)
    return redirect(url_for("index"))


@app.route("/api/update_status", methods=["POST"])
def api_update_status():
    """JSON endpoint for status updates (used by JS fetch)."""
    data = request.get_json(silent=True) or {}
    post_id = data.get("post_id")
    new_status = data.get("status", "")
    if post_id and new_status in STATUSES:
        update_post_status(int(post_id), new_status)
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Invalid data"}), 400


@app.route("/log")
def file_log():
    """View the full file-processing log."""
    entries = get_file_log()
    return render_template("log.html", entries=entries)


@app.route("/api/posts")
def api_posts():
    """JSON dump of all posts (for external integrations)."""
    return jsonify(get_all_posts())


if __name__ == "__main__":
    init_db()
    print(f"Dashboard running at http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")
    app.run(host=DASHBOARD_HOST, port=DASHBOARD_PORT, debug=True)
