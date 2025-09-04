#!/usr/bin/env python3
"""
Website Connectivity Monitor - Web Interface (SQLAlchemy version)
"""

from flask import Flask, render_template, request, jsonify
import threading
from database import init_db, db, Site, CheckHistory
from monitor import ConnectivityMonitor, SingleCheckMonitor
from utils import validate_url, normalize_url, format_timestamp, format_duration

app = Flask(__name__)
init_db(app)

# Global variables for monitoring
monitor = None
monitor_thread = None
monitor_running = False

# Exponer funciones de utils a Jinja
@app.context_processor
def utility_processor():
    return dict(format_timestamp=format_timestamp, format_duration=format_duration)


@app.route("/")
def index():
    """Main dashboard page"""
    sites = Site.query.order_by(Site.url).all()
    return render_template("index.html", sites=sites)


@app.route("/api/sites", methods=["GET"])
def get_sites():
    """API endpoint to get all sites"""
    sites = Site.query.order_by(Site.url).all()
    return jsonify({
        "sites": [
            {
                "id": s.id,
                "url": s.url,
                "added_at": format_timestamp(s.added_at),
                "last_checked": format_timestamp(s.last_checked),
                "last_status": s.last_status,
                "response_time": format_duration(s.response_time) if s.response_time else None,
                "last_error": s.last_error,
            }
            for s in sites
        ]
    })


@app.route("/api/sites", methods=["POST"])
def add_site():
    """API endpoint to add a new site"""
    data = request.get_json()
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "URL is required"}), 400

    url = normalize_url(url)
    if not validate_url(url):
        return jsonify({"error": "Invalid URL format"}), 400

    # Check if already exists
    existing = Site.query.filter_by(url=url).first()
    if existing:
        return jsonify({"error": "Site already exists"}), 409

    new_site = Site(url=url)
    db.session.add(new_site)
    db.session.commit()
    return jsonify({"message": "Site added successfully", "url": url})


@app.route("/api/sites/<path:url>", methods=["DELETE"])
def remove_site(url):
    """API endpoint to remove a site"""
    site = Site.query.filter_by(url=url).first()
    if not site:
        return jsonify({"error": "Site not found"}), 404

    db.session.delete(site)
    db.session.commit()
    return jsonify({"message": "Site removed successfully"})


@app.route("/api/check", methods=["POST"])
def check_sites():
    """API endpoint to check all sites once"""
    checker = SingleCheckMonitor(timeout=10)
    sites = Site.query.all()

    if not sites:
        return jsonify({"message": "No sites to check"})

    results = []
    for site in sites:
        status, response_time, error = checker.check_site(site.url)

        site.last_checked = db.func.now()
        site.last_status = status
        site.response_time = response_time
        site.last_error = error

        history = CheckHistory(
            site_id=site.id,
            status=status,
            response_time=response_time,
            error_message=error,
        )
        db.session.add(history)
        results.append({
            "url": site.url,
            "status": status,
            "response_time": format_duration(response_time) if response_time else None,
            "error": error,
        })

    db.session.commit()
    return jsonify({"results": results})


@app.route("/api/sites/<path:url>/history", methods=["GET"])
def get_site_history(url):
    """API endpoint to get check history for a site (JSON)"""
    site = Site.query.filter_by(url=url).first()
    if not site:
        return jsonify({"error": "Site not found"}), 404

    limit = request.args.get("limit", 50, type=int)
    history = (
        CheckHistory.query.filter_by(site_id=site.id)
        .order_by(CheckHistory.checked_at.desc())
        .limit(limit)
        .all()
    )

    return jsonify({
        "history": [
            {
                "checked_at": format_timestamp(h.checked_at),
                "status": h.status,
                "response_time": format_duration(h.response_time) if h.response_time else None,
                "error_message": h.error_message,
            }
            for h in history
        ]
    })


@app.route("/sites/<path:url>/history")
def site_history_page(url):
    """Web page to display site history (HTML)"""
    site = Site.query.filter_by(url=url).first()
    if not site:
        return "Sitio no encontrado", 404

    limit = request.args.get("limit", 50, type=int)
    history = (
        CheckHistory.query.filter_by(site_id=site.id)
        .order_by(CheckHistory.checked_at.desc())
        .limit(limit)
        .all()
    )

    return render_template("history.html", site=site, history=history)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
