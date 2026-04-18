import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify

from lib.dividends import pobierz_dywidendy_portfela

app = Flask(__name__)


@app.route('/api/dividends')
def dividends():
    try:
        data = pobierz_dywidendy_portfela()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
