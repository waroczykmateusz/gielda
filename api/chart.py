import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request

from lib.chart_data import dane_wykresu

app = Flask(__name__)


@app.route('/api/chart')
def chart():
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({'error': 'missing symbol'}), 400
    try:
        data = dane_wykresu(symbol)
        if data is None:
            return jsonify({'error': 'no data'}), 404
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
