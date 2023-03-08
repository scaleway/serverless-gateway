from scw_serverless import Serverless

app = Serverless("function-int-tests")

@app.func()
def handle(_event, _content):    
    return "Hello from function"


@app.func()
def goodbye(_event, _content):
    return "Goodbye from function"
