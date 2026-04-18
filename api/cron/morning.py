import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Flask, jsonify, request

from lib.ai import dzienna_analiza

app = Flask(__name__)

CRON_SECRET = os.environ.get("CRON_SECRET")


def _authorized(req):
    if not CRON_SECRET:
        return True
    auth = req.headers.get("Authorization", "")
    return auth == f"Bearer {CRON_SECRET}"


@app.route("/api/cron/morning")
def morning():
    if not _authorized(request):
        return jsonify({"error": "unauthorized"}), 401
    try:
        dzienna_analiza()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
