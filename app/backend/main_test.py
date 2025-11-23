import requests
import time
import json
from tabulate import tabulate # For pretty table printing

BASE_URL = "http://localhost:8000"

# --- Configuration for polling ---
POLL_INTERVAL_SECONDS = 5  # How often to check for proxies
MAX_WAIT_SECONDS = 180     # Maximum time to wait for the first batch before giving up

def print_api_response(response: requests.Response, action_name: str):
    """Helper function to print API response details."""
    print(f"\n--- {action_name} ---")
    print(f"Status Code: {response.status_code}")
    try:
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
    except requests.exceptions.JSONDecodeError:
        print("Response Text:")
        print(response.text)
    print("-" * (len(action_name) + 8))


def display_proxies_table(proxies: list):
    """Displays a list of proxy dictionaries in a table."""
    if not proxies:
        print("\nNo proxies to display.")
        return

    headers = [
        "IP Address", "Port", "Protocol", "Country",
        "Anonymity", "Response Time (ms)", "Valid?", "Source", "Last Checked"
    ]
    table_data = []

    for proxy in proxies:
        response_time_ms = proxy.get('response_time')
        if response_time_ms is not None:
            response_time_str = f"{response_time_ms:.2f}"
        else:
            response_time_str = "N/A"

        table_data.append([
            proxy.get('ip', 'N/A'),
            proxy.get('port', 'N/A'),
            proxy.get('protocol', 'N/A'),
            proxy.get('country', 'N/A'),
            proxy.get('anonymity', 'N/A'),
            response_time_str,
            "Yes" if proxy.get('is_valid') else "No",
            proxy.get('source', 'N/A'),
            proxy.get('last_checked', 'N/A')
        ])

    print("\n--- Proxies from First Validation Cycle ---")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print(f"Total proxies displayed: {len(proxies)}")


def wait_for_first_proxies(max_wait: int, poll_interval: int) -> list:
    """
    Polls the API until proxies are available or max_wait is reached.
    Returns the list of all proxies (valid and invalid).
    """
    start_time = time.time()
    print(f"\nWaiting for the first batch of proxies (up to {max_wait} seconds)...")
    while time.time() - start_time < max_wait:
        try:
            # Check scheduler status to see if validation is ongoing or if proxies are populated
            status_response = requests.get(f"{BASE_URL}/scheduler/status", timeout=5)
            status_response.raise_for_status()
            status_data = status_response.json()

            proxy_count = status_data.get("current_proxy_count", 0)
            is_validating = status_data.get("validation_in_progress", False)

            if proxy_count > 0 and not is_validating:
                print(f"\nProxies found ({proxy_count} total) and validation not in progress. Fetching details.")
                proxies_response = requests.get(f"{BASE_URL}/proxies?only_valid=false", timeout=10)
                proxies_response.raise_for_status()
                return proxies_response.json()
            elif proxy_count > 0 and is_validating:
                print(f"  ({time.strftime('%H:%M:%S')}) Validation in progress, {proxy_count} proxies reported so far. Waiting...")
            elif not proxy_count and is_validating:
                print(f"  ({time.strftime('%H:%M:%S')}) Validation in progress, no proxies reported yet. Waiting...")
            else: # no proxies, not validating (might have failed or not started)
                print(f"  ({time.strftime('%H:%M:%S')}) No proxies reported, validation not active. Waiting...")

        except requests.exceptions.Timeout:
            print(f"  ({time.strftime('%H:%M:%S')}) API request timed out while polling. Retrying...")
        except requests.exceptions.RequestException as e:
            print(f"  ({time.strftime('%H:%M:%S')}) Error polling for proxies: {e}. Retrying...")
        
        time.sleep(poll_interval)

    print(f"\nMax wait time of {max_wait} seconds reached. Attempting to fetch proxies one last time.")
    try:
        proxies_response = requests.get(f"{BASE_URL}/proxies?only_valid=false", timeout=10)
        proxies_response.raise_for_status()
        return proxies_response.json()
    except Exception as e:
        print(f"Failed to fetch proxies on final attempt: {e}")
        return []


def run_dynamic_first_cycle_test():
    print("Starting Test: Get Proxies from First Validation Cycle (Dynamic Wait)...")

    # 1. Check initial status (optional)
    try:
        response = requests.get(f"{BASE_URL}/scheduler/status")
        response.raise_for_status()
        print_api_response(response, "Initial Scheduler Status")
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to API or getting initial status: {e}")
        print("Please ensure the FastAPI server (main.py) is running.")
        return

    # 2. Start the scheduler
    print("\nAttempting to start the scheduler...")
    try:
        response = requests.post(f"{BASE_URL}/scheduler/start")
        response.raise_for_status()
        print_api_response(response, "Start Scheduler Request")
    except requests.exceptions.RequestException as e:
        print(f"Error starting scheduler: {e}")
        return

    # 3. Dynamically wait for the first batch of proxies
    all_proxies_list = wait_for_first_proxies(MAX_WAIT_SECONDS, POLL_INTERVAL_SECONDS)

    # 4. Display the proxies in a table
    if all_proxies_list:
        display_proxies_table(all_proxies_list)
    else:
        print("\nNo proxies were retrieved after waiting.")
        # Optionally, get final status to understand why
        try:
            response = requests.get(f"{BASE_URL}/scheduler/status")
            print_api_response(response, "Scheduler Status After Wait (No Proxies)")
        except:
            pass


    # 5. Stop the scheduler
    print("\nAttempting to stop the scheduler...")
    try:
        response = requests.post(f"{BASE_URL}/scheduler/stop")
        response.raise_for_status()
        print_api_response(response, "Stop Scheduler Request")
    except requests.exceptions.RequestException as e:
        print(f"Error stopping scheduler: {e}")

    print("\nDynamic First Cycle Proxy Test Finished.")


if __name__ == "__main__":
    run_dynamic_first_cycle_test()
