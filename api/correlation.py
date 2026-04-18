import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify
from lib.correlation import korelacja_portfela

app = Flask(__name__)


@app.route('/api/correlation')
def correlation():
    try:
        return jsonify(korelacja_portfela())
    except Exception as e:
        return jsonify({'error': str(e)}), 500
