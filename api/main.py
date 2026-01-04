from flask import Flask
from middleware.logging import WSGILogging
from werkzeug.serving import run_simple
app = Flask(__name__)

app.wsgi_app = WSGILogging(app.wsgi_app)

SERVER_NAME="0.0.0.0"
SERVER_PORT=8443

@app.route("/")
def index():
    return {"status": 200}

run_simple(
    hostname=SERVER_NAME,
    port=SERVER_PORT,
    application=app
    )
