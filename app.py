import requests
from flask import Flask, jsonify

from freeproxylist import get_proxies_fpl

app = Flask(__name__)

TEST_URL = "http://httpbin.org/ip"
REQUEST_TIMEOUT = 3


def check_proxy_status(proxy_url):
    print(f"Checking proxy: {proxy_url}...")

    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }

    try:
        response = requests.get(TEST_URL, proxies=proxies, timeout=REQUEST_TIMEOUT)

        if 200 <= response.status_code < 300:
            print(f"SUCCESS: {proxy_url}")
            return "Working", response.elapsed.total_seconds()
        else:
            print(f"FAIL: {proxy_url} (Status {response.status_code})")
            return f"Error: {response.status_code}", 0

    except requests.exceptions.RequestException:
        print(f"FAIL: {proxy_url} (Connection Error)")
        return "Failed to connect", 0


@app.route("/")
def index():
    print("Scraping proxies from free-proxy-list.net...")
    all_proxies = get_proxies_fpl()

    proxy_subset = all_proxies

    results = []

    for proxy in proxy_subset:
        status, time_taken = check_proxy_status(proxy)
        results.append(
            {"proxy": proxy, "status": status, "response_time_seconds": time_taken}
        )

    return jsonify(
        {
            "total_scraped": len(all_proxies),
            "checked_count": len(proxy_subset),
            "results": results,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
