import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Flask, jsonify, request

from lib.alerts import sprawdz_alerty
from lib.report import dzienny_raport
from lib.signals import sprawdz_sygnaly

app = Flask(__name__)

CRON_SECRET = os.environ.get("CRON_SECRET")


def _authorized(req):
    if not CRON_SECRET:
        return True
    auth = req.headers.get("Authorization", "")
    return auth == f"Bearer {CRON_SECRET}"


@app.route("/api/cron/evening")
def evening():
    if not _authorized(request):
        return jsonify({"error": "unauthorized"}), 401
    errors = []
    for name, fn in (("signals", sprawdz_sygnaly), ("alerts", sprawdz_alerty), ("report", dzienny_raport)):
        try:
            fn()
        except Exception as e:
            errors.append(f"{name}: {e}")
    if errors:
        return jsonify({"ok": False, "errors": errors}), 500
    return jsonify({"ok": True})
