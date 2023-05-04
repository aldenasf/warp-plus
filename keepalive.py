import os
import json
import yaml
import logging
from threading import Thread
from datetime import datetime
from flask import Flask, jsonify, request

config = yaml.safe_load(open('config.yml'))

if config['hide-flask-development-server-warn']:
    os.environ['FLASK_ENV'] = 'production'

app = Flask('')

log = logging.getLogger('werkzeug')

log_level = logging.WARNING

match config['flask-log-level']:
    case 'DEBUG':
        log_level = logging.DEBUG

    case 'INFO':
        log_level = logging.INFO

    case 'WARNING':
        log_level = logging.WARNING

    case 'ERROR':
        log_level = logging.ERROR

    case 'CRITICAL':
        log_level = logging.CRITICAL

log.setLevel(log_level)


@app.route('/')
def index():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ping from {request.remote_addr}")
    return '<pre>OK</pre>', 200


if config['keep-alive-tracker']:
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
    app.run(host='0.0.0.0', port=config['flask-server-port'])


def keepalive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
