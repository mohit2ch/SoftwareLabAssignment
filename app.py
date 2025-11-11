from flask import Flask

# Initialize the Flask application
app = Flask(__name__)

PROXY_LIST = [
    "http://192.168.1.1:8080",
    "http://10.0.0.1:3128",
    "http://user:pass@example.com:8000",
    "http://203.0.113.1:80"
]

@app.route('/')
def index():
    """
    Main entry point for the web application.
    Currently just a placeholder.
    """
    return "Proxy Checker"

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True)
