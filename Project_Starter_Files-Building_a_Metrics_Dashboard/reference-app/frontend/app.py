from flask import Flask, render_template, request
from prometheus_flask_exporter import PrometheusMetrics
import time
import random

app = Flask(__name__)
metrics = PrometheusMetrics(app, group_by='endpoint')
metrics.info("frontend_app_info", "Frontend App Info", version="1.0.3")


@app.route("/")
def homepage():
    return render_template("main.html")

@app.route('/test')
def test():
    time.sleep(random.random() * 0.8)
    return 'test'


@app.route('/not_found')
def sorry():
    time.sleep(random.random() * 0.9)
    return 'not found', 404


@app.route('/error')
def oooops():
    time.sleep(random.random() * 0.7)
    return 'error', 500

if __name__ == "__main__":
    app.run()
