from scw_serverless import Serverless

app = Serverless("function-int-tests")

@app.func()
def hello():
    return "Hello from function"

@app.func()
def goodbye():
    return "Goodbye from function"