import os
import json
import logging
from threading import Thread
from datetime import datetime
from flask import Flask, jsonify, request

os.environ['FLASK_ENV'] = 'production'

app = Flask('')

log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)


@app.route('/')
def index():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ping from {request.remote_addr}")
    return '<pre>OK</pre>', 200


@app.route('/tracker')
def tracker():
    try:
        data = json.load(open('tracker.json'))
        data['total'] = data['good'] + data['bad']
        return jsonify(data), 200
    except Exception as err:
        print(err)
        return f'<pre>{err}</pre>', 500


def run():
    app.run(host='0.0.0.0', port=3000)


def keepalive():
    t = Thread(target=run)
    t.start()
