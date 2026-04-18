import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Flask, jsonify, request
from lib.report import dzienny_raport

app = Flask(__name__)
CRON_SECRET = os.environ.get("CRON_SECRET")


def _authorized(req):
    if not CRON_SECRET:
        return True
    return req.headers.get("Authorization", "") == f"Bearer {CRON_SECRET}"


@app.route("/api/cron/report")
def report():
    if not _authorized(request):
        return jsonify({"error": "unauthorized"}), 401
    try:
        dzienny_raport()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
