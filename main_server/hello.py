from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'hello world'

if __name__ == '__main__':
    app.run(host='localhost', port=8080)
    print("Server is running on http://localhost:8080")