import requests
import concurrent.futures
from flask import Flask, jsonify

from freeproxylist import get_proxies_fpl

app = Flask(__name__)

TEST_URL = "http://httpbin.org/ip"
REQUEST_TIMEOUT = 3
MAX_WORKERS = 50  

def check_proxy_status(proxy_url):

    print(f"Checking proxy: {proxy_url}...")

    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }

    try:
        # We use the proxy for both http and https requests
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


def check_proxy_wrapper(proxy):

    status, time_taken = check_proxy_status(proxy)
    return {
        "proxy": proxy, 
        "status": status, 
        "response_time_seconds": time_taken
    }


@app.route("/")
def index():
    print("Scraping proxies from free-proxy-list.net...")
    all_proxies = get_proxies_fpl()
    
    proxy_subset = all_proxies
    
    results = []

    print(f"Starting execution with {MAX_WORKERS} threads for {len(proxy_subset)} proxies...")

    # Context Manager for the ThreadPool
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_proxy = {executor.submit(check_proxy_wrapper, proxy): proxy for proxy in proxy_subset}
        
        for future in concurrent.futures.as_completed(future_to_proxy):
            try:
                data = future.result()
                results.append(data)
            except Exception as exc:
                # Catch any unexpected errors inside the thread
                proxy = future_to_proxy[future]
                print(f'{proxy} generated an exception: {exc}')

    return jsonify(
        {
            "total_scraped": len(all_proxies),
            "checked_count": len(results),
            "results": results,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
