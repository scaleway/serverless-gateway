from flask import Flask

app = Flask(__name__)


@app.route("/hello")
def hello():
    return "Hello from function A"


@app.route("/goodbye")
def goodbye():
    return "Goodbye from function A"


app.run(host="0.0.0.0", port=80)
