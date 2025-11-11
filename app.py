from flask import Flask
import requests

# Initialize the Flask application
app = Flask(__name__)

# temp list
PROXY_LIST = [
    "http://192.168.1.1:8080",
    "http://8.212.151.166:80"
]


TEST_URL = 'http://httpbin.org/ip'
REQUEST_TIMEOUT = 5

def check_proxy_status(proxy_url):
    print(f"Checking proxy: {proxy_url}...")
    
    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }

    try:
        response = requests.get(TEST_URL, proxies=proxies, timeout=REQUEST_TIMEOUT)
        
        if response.status_code >= 200 and response.status_code < 300:
            print(f"Proxy {proxy_url} is working.")
            return True
        else:
            print(f"Proxy {proxy_url} returned status code: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Proxy {proxy_url} failed to connect.")
        return False

@app.route('/')
def index():

    results = {}
    for proxy in PROXY_LIST:
        status = check_proxy_status(proxy)
        results[proxy] = status
    
    print("\n")

    return "Proxy checker"

if __name__ == '__main__':
    # Run the Flask app
    # We set debug=True for development
    app.run(debug=True)