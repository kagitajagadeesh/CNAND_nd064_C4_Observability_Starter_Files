from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from flask_cors import CORS
import time
import random
import pymongo
import logging
from flask_pymongo import PyMongo


from jaeger_client import Config
from flask_opentracing import FlaskTracing

from prometheus_flask_exporter import PrometheusMetrics
logging.basicConfig(level=logging.INFO)
logging.info("Setting LOGLEVEL to INFO")
app = Flask(__name__)
app.config['MONGO_DBNAME'] = 'example-mongodb'
app.config['MONGO_URI'] = 'mongodb://example-mongodb-svc.default.svc.cluster.local:27017/example-mongodb'

mongo = PyMongo(app)
CORS(app)

metrics = PrometheusMetrics(app, group_by='endpoint')
metrics.info("backend_app_info", "Backend App Info", version="1.0.3")


config = Config(
    config={
        'sampler':
        {'type': 'const',
         'param': 1},
                        'logging': True,
                        'reporter_batch_size': 1,},
                        service_name="backend")
jaeger_tracer = config.initialize_tracer()
tracing = FlaskTracing(jaeger_tracer, True, app)

@app.route('/healthz')
def healthcheck():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
        )
    return response

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
    parent_span = tracing.get_span("error-span")
    with jaeger_tracer.start_span('ErrorSpan', child_of=parent_span) as span:
        span.set_tag("http.url", '/error')
        span.set_tag("http.status_code", 500)
    return 'error', 500

@app.route("/")
def homepage():
    with jaeger_tracer.start_span('TestSpan') as span:
        span.log_kv({'event': 'welcome to the backend!', 'life': 42})
        with jaeger_tracer.start_span('ChildSpan', child_of=span) as child_span:
            child_span.log_kv({'event': 'Welcome again!! in case you missed the first time.'})
    return "Hello World"


@app.route("/api")
def my_api():
    parent_span = tracing.get_span("api-span")
    with jaeger_tracer.start_span('TestSpan', child_of=parent_span) as span:
        span.set_tag("url: ", '/api"')
    answer = "something"
    return jsonify(repsonse=answer)
        
@app.route("/star", methods=["POST"])
def add_star():
    star = mongo.db.stars
    name = request.json["name"]
    distance = request.json["distance"]
    star_id = star.insert({"name": name, "distance": distance})
    new_star = star.find_one({"_id": star_id})
    output = {"name": new_star["name"], "distance": new_star["distance"]}
    return jsonify({"result": output})


if __name__ == "__main__":
    app.run()
