from flask import Flask
from flask import Flask
from threading import Thread

app = Flask('')


@app.route('/')
def index():
    return '<pre>OK</pre>', 200


def run():
    app.run(host='0.0.0.0', port=3000)


def keepalive():
    t = Thread(target=run)
    t.start()
