from flask import Flask

app = Flask(__name__)


@app.route("/hello")
def hello():
    return "Hello from function B"


@app.route("/goodbye")
def goodbye():
    return "Goodbye from function B"

app.run(host="0.0.0.0", port=80)
