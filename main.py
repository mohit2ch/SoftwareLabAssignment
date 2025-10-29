import socket
from prx_scrappers import get_geonode_proxies, get_proxies_fpl, get_proxyscrape
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os
import json
import re
from tabulate import tabulate 
from collections import namedtuple

# Define a ProxyResult class to store structured data
ProxyResult = namedtuple('ProxyResult', ['proxy_url', 'country_city', 'ip', 'hostname', 'timezone', 'response_time', 'raw_response'])

def replicate_telnet_http(host, port, path, timeout=5):
    try:
        # Create a socket with timeout
        client_socket = socket.create_connection((host, port), timeout=timeout)
        
        # Construct the HTTP GET request with proper headers
        request = f"GET {path} HTTP/1.1\r\nHost: {path.split('/')[2]}\r\nUser-Agent: Mozilla/5.0\r\nAccept: */*\r\n\r\n"
        
        # Send the request
        client_socket.sendall(request.encode())

        # Receive the response
        response = b""
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                break
            try:
                client_socket.settimeout(timeout - (time.time() - start_time))
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                response += chunk
            except socket.timeout:
                break

        # Decode and return the response
        return response.decode('utf-8', errors='ignore')

    except (socket.error, socket.timeout) as e:
        return f"Error: {e}"
    finally:
        if 'client_socket' in locals() and client_socket:
            client_socket.close()

def extract_json_from_response(response):
    """Extract JSON data from HTTP response if present"""
    try:
        # Look for JSON object in the response
        json_match = re.search(r'({[\s\S]*})', response)
        if json_match:
            json_str = json_match.group(1)
            return json.loads(json_str)
        return None
    except json.JSONDecodeError:
        return None

def test_proxy(proxy):
    try:
        parts = proxy.split("://")
        if len(parts) != 2:
            return (proxy, "Invalid proxy format", False, None)
            
        protocol = parts[0]
        host_port = parts[1].split(":")
        
        if len(host_port) != 2:
            return (proxy, "Invalid host:port format", False, None)
            
        host, port = host_port
        port = int(port)
        
        if protocol == "http":
            path = "http://httpbin.org/ip"
        else:  # https, socks4, socks5, etc.
            path = "https://ipinfo.io/json"
            
        start_time = time.time()
        response = replicate_telnet_http(host, port, path)
        elapsed_time = time.time() - start_time
        
        # Extract JSON from response if possible
        json_data = extract_json_from_response(response)
        
        # Check for specific error conditions
        rate_limited = "rate limit" in response.lower() or "too many requests" in response.lower()
        
        # Determine if proxy is working
        success = (
            "Error:" not in response 
            and (json_data is not None)
            and not rate_limited
        )
        
        result = f"[{protocol}://{host}:{port}] Response in {elapsed_time:.2f}s:\n{response}"
        
        return (proxy, result, success, json_data, rate_limited)
    except Exception as e:
        return (proxy, f"Error: {str(e)}", False, None, False)

def create_proxy_result(proxy, json_data, response_time):
    """Create a structured ProxyResult object from JSON data"""
    if not json_data:
        return ProxyResult(
            proxy_url=proxy,
            country_city="None",
            ip="None",
            hostname="None",
            timezone="None",
            response_time=f"{response_time:.2f}s",
            raw_response="Error or no data"
        )
    
    # Extract data from JSON
    ip = json_data.get("ip", "None")
    hostname = json_data.get("hostname", "None")
    timezone = json_data.get("timezone", "None")
    
    # Build country_city string
    country = json_data.get("country", "")
    city = json_data.get("city", "")
    country_city = f"{country}/{city}" if country and city else country or city or "None"
    
    return ProxyResult(
        proxy_url=proxy,
        country_city=country_city,
        ip=ip,
        hostname=hostname,
        timezone=timezone,
        response_time=f"{response_time:.2f}s",
        raw_response=json.dumps(json_data, indent=2)
    )

if __name__ == "__main__":
    # Collect proxies from all sources
    print("Collecting proxies from multiple sources...")
    proxies = []
    
    try:
        proxies.extend(get_proxyscrape())
        print(f"Got {len(proxies)} proxies from proxyscrape")
    except Exception as e:
        print(f"Failed to get proxyscrape proxies: {e}")
    
    try:
        fpl_proxies = get_proxies_fpl()
        proxies.extend(fpl_proxies)
        print(f"Got {len(fpl_proxies)} proxies from fpl")
    except Exception as e:
        print(f"Failed to get fpl proxies: {e}")
    
    try:
        geonode_proxies = get_geonode_proxies()
        proxies.extend(geonode_proxies)
        print(f"Got {len(geonode_proxies)} proxies from geonode")
    except Exception as e:
        print(f"Failed to get geonode proxies: {e}")
    
    print(f"Total proxies to test: {len(proxies)}")
    
    # Use ThreadPoolExecutor for better control
    max_workers = 50
    working_proxies = []
    rate_limited_proxies = []
    failed_proxies = []
    
    # Function to process a batch of proxies
    def process_proxy_batch(proxy_batch, is_retry=False):
        batch_working = []
        batch_rate_limited = []
        batch_failed = []
        
        print(f"Testing {'retry batch' if is_retry else 'initial batch'} of {len(proxy_batch)} proxies with {max_workers} workers...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_proxy = {executor.submit(test_proxy, proxy): proxy for proxy in proxy_batch}
            
            for future in as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    result = future.result()
                    if len(result) >= 3:
                        proxy_str, response_text, success, json_data, rate_limited = result
                        
                        if success:
                            # Extract response time from the text
                            response_time = float(re.search(r'Response in (\d+\.\d+)s', response_text).group(1))
                            proxy_result = create_proxy_result(proxy, json_data, response_time)
                            batch_working.append(proxy_result)
                            print(f"✓ Working: {proxy}")
                        elif rate_limited:
                            batch_rate_limited.append(proxy)
                            print(f"⟳ Rate limited: {proxy}")
                        else:
                            batch_failed.append((proxy, response_text))
                            print(f"✗ Failed: {proxy}")
                    else:
                        batch_failed.append((proxy, "Incomplete result"))
                        print(f"✗ Failed (incomplete result): {proxy}")
                except Exception as e:
                    batch_failed.append((proxy, f"Error: {str(e)}"))
                    print(f"Error testing {proxy}: {e}")
        
        return batch_working, batch_rate_limited, batch_failed
    
    # Process initial batch
    new_working, new_rate_limited, new_failed = process_proxy_batch(proxies)
    working_proxies.extend(new_working)
    rate_limited_proxies.extend(new_rate_limited)
    failed_proxies.extend(new_failed)
    
    # Process rate-limited proxies with a delay
    if rate_limited_proxies:
        print(f"\nWaiting 30 seconds before retrying {len(rate_limited_proxies)} rate-limited proxies...")
        time.sleep(30)
        retry_working, retry_rate_limited, retry_failed = process_proxy_batch(rate_limited_proxies, True)
        working_proxies.extend(retry_working)
        failed_proxies.extend(retry_failed)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Proxy Testing Complete. Working: {len(working_proxies)}/{len(proxies)}")
    print("=" * 50)
    
    # Create a results directory if it doesn't exist
    results_dir = os.path.join(os.path.dirname(__file__), "proxy_results")
    os.makedirs(results_dir, exist_ok=True)
    
    # Save results to a file for better viewing
    results_file = os.path.join(results_dir, f"working_proxies.txt")
    json_results_file = os.path.join(results_dir, f"working_proxies.json")
    
    # Prepare table data for display
    table_data = [
        [p.proxy_url, p.country_city, p.ip, p.hostname, p.timezone, p.response_time]
        for p in working_proxies
    ]
    
    # Display results in table format
    headers = ["Proxy URL", "Country/City", "IP", "Hostname", "Timezone", "Response Time"]
    table = tabulate(table_data, headers=headers, tablefmt="grid")
    
    print("\nWORKING PROXIES TABLE:")
    print(table)
    
    # Save detailed results
    with open(results_file, 'w') as f:
        f.write(f"WORKING PROXIES ({len(working_proxies)} found)\n")
        f.write("=" * 80 + "\n\n")
        f.write(table + "\n\n")
        
        f.write("DETAILED RESULTS:\n")
        f.write("=" * 80 + "\n\n")
        
        for proxy_result in working_proxies:
            f.write(f"\n{proxy_result.proxy_url}\n")
            f.write("-" * 75 + "\n")
            f.write(proxy_result.raw_response + "\n")
            f.write("-" * 75 + "\n")
    
    # Save JSON results for programmatic use
    with open(json_results_file, 'w') as f:
        json.dump([{
            "proxy_url": p.proxy_url,
            "country_city": p.country_city,
            "ip": p.ip,
            "hostname": p.hostname,
            "timezone": p.timezone,
            "response_time": p.response_time
        } for p in working_proxies], f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    print(f"JSON results saved to: {json_results_file}")



