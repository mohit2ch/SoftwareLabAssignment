# app/backend/proxy_validator.py
import requests
import time
from datetime import datetime
from typing import List, Optional, Dict, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import pycountry # Import pycountry

from .models import ProxyItem
from app.backend.providers import get_all_proxies

# Constants
DEFAULT_THREADS = 50
REQUEST_TIMEOUT = 12  # Main connectivity test timeout (increased slightly)
ANONYMITY_REQUEST_TIMEOUT = 10 # Anonymity check timeout (increased)
DEFAULT_TEST_URL = "https://ipinfo.io/json"
ANONYMITY_TEST_URL = "https://httpbin.org/get?show_env=1"

# Common browser user agent
COMMON_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
REQUEST_HEADERS = {"User-Agent": COMMON_USER_AGENT}

def get_my_real_ip(timeout=7) -> Optional[str]:
    urls_to_try = ["https://ipinfo.io/json", "https://httpbin.org/ip", "https://api.ipify.org?format=json"]
    for url in urls_to_try:
        try:
            response = requests.get(url, timeout=timeout, headers=REQUEST_HEADERS) # Add headers
            response.raise_for_status()
            data = response.json()
            ip = data.get("ip") or data.get("origin")
            if ip: return ip.split(',')[0].strip()
        except Exception: continue
    print("[VALIDATOR_WARNING] Could not fetch real IP from any source.")
    return None

REAL_IP = get_my_real_ip()
if REAL_IP: print(f"[VALIDATOR_INFO] Real IP detected: {REAL_IP}")
else: print("[VALIDATOR_WARNING] Real IP could not be determined. Anonymity checks will be affected.")


def get_country_name_from_code(country_code: Optional[str]) -> Optional[str]:
    if not country_code:
        return None
    try:
        country = pycountry.countries.get(alpha_2=country_code.upper())
        return country.name.upper() if country else None # Return full name in uppercase
    except Exception: # Handles LookupError if code is invalid, or other issues
        return None # Or return the original code if preferred: country_code.upper()

def test_single_proxy(proxy_item: ProxyItem, timeout: int, test_url: str, anonymity_test_url: str, check_anonymity: bool) -> ProxyItem:
    proxy_dict = {"http": proxy_item.proxy_string(), "https": proxy_item.proxy_string()}
    
    proxy_item.is_valid = False
    proxy_item.response_time = None
    proxy_item.anonymity = "N/A"
    proxy_item.last_checked = datetime.now().isoformat()
    # Country will be set/updated later

    start_time_main_test = time.perf_counter()
    try:
        response = requests.get(test_url, proxies=proxy_dict, timeout=timeout, headers=REQUEST_HEADERS, allow_redirects=True)
        response.raise_for_status()
        
        proxy_item.response_time = round((time.perf_counter() - start_time_main_test) * 1000, 2)
        proxy_item.is_valid = True

        try:
            data = response.json()
            country_code_from_ipinfo = data.get("country")
            if country_code_from_ipinfo:
                full_country_name = get_country_name_from_code(country_code_from_ipinfo)
                proxy_item.country = full_country_name if full_country_name else country_code_from_ipinfo.upper()
            # If provider already set a full name and ipinfo gives a code, this will update it.
            # If provider had nothing, and ipinfo gives nothing, it remains None.
        except json.JSONDecodeError:
            print(f"[VALIDATOR_WARNING] Proxy {proxy_item.proxy_string()} - {test_url} response not JSON. Country not updated from test.")
        except Exception as e_ipinfo_parse:
            print(f"[VALIDATOR_WARNING] Proxy {proxy_item.proxy_string()} - Error parsing ipinfo response: {e_ipinfo_parse}")

        if check_anonymity:
            if not REAL_IP: proxy_item.anonymity = "Unknown (No Real IP)"
            else:
                try:
                    anon_response = requests.get(anonymity_test_url, proxies=proxy_dict, timeout=ANONYMITY_REQUEST_TIMEOUT, headers=REQUEST_HEADERS)
                    anon_response.raise_for_status()
                    data_anon = anon_response.json()
                    headers_from_proxy = {k.lower(): v for k, v in data_anon.get("headers", {}).items()}
                    origin_ip_via_proxy = data_anon.get("origin", "").split(',')[0].strip()

                    if origin_ip_via_proxy == REAL_IP: proxy_item.anonymity = "Transparent"
                    else:
                        is_elite = True
                        proxy_revealing_headers = [
                            "x-forwarded-for", "x-real-ip", "via", "proxy-connection", "xroxy-connection",
                            "forwarded-for", "x-proxy-id", "client-ip", "x-client-ip", "forwarded", "from",
                            "http-x-forwarded-for", "http-client-ip", "http-via", "xproxy-connection",
                        ]
                        for header_key in proxy_revealing_headers:
                            if header_key in headers_from_proxy: is_elite = False; break
                        proxy_item.anonymity = "Elite" if is_elite else "Anonymous"
                
                except requests.exceptions.Timeout: proxy_item.anonymity = "Error (Anonymity Timeout)"
                except requests.exceptions.RequestException: proxy_item.anonymity = "Error (Anonymity Network)"
                except json.JSONDecodeError: proxy_item.anonymity = "Error (Anonymity Format)"
                except Exception: proxy_item.anonymity = "Error (Anonymity Unknown)"
        else: proxy_item.anonymity = "Not Checked"

    except requests.exceptions.Timeout: proxy_item.is_valid = False
    except requests.exceptions.ConnectionError: proxy_item.is_valid = False
    except requests.exceptions.HTTPError: proxy_item.is_valid = False
    except requests.exceptions.RequestException: proxy_item.is_valid = False

    if not proxy_item.is_valid:
        proxy_item.response_time = None
        if not proxy_item.anonymity.startswith("Error"): proxy_item.anonymity = "N/A"
    
    # If country was not set by provider and ipinfo also failed or didn't provide it,
    # proxy_item.country would remain None. The UI handles None as "N/A".
    return proxy_item


def validate_all_proxies(
    proxy_list_input: Optional[List[ProxyItem]] = None,
    num_threads: int = DEFAULT_THREADS,
    timeout: int = REQUEST_TIMEOUT,
    test_url: str = DEFAULT_TEST_URL, 
    anonymity_test_url: str = ANONYMITY_TEST_URL,
    check_anonymity: bool = True,
) -> List[ProxyItem]:
    
    source_proxies = get_all_proxies() if proxy_list_input is None else proxy_list_input
    
    # De-duplicate based on (ip, port, protocol) AND pre-populate country from providers if possible
    # The ProxyItem __hash__ and __eq__ methods will handle uniqueness.
    # If providers give country names, they might be overwritten by ipinfo's code-to-name conversion later.
    unique_proxies_map: Dict[ProxyItem, ProxyItem] = {} # Use ProxyItem as key
    for p_item in source_proxies:
        if p_item not in unique_proxies_map: # First time seeing this (ip,port,protocol)
            unique_proxies_map[p_item] = p_item
        else: # Duplicate (ip,port,protocol) found
            existing_p = unique_proxies_map[p_item]
            # Merge/prioritize info if needed, e.g., prefer if one has country and other doesn't
            if not existing_p.country and p_item.country:
                existing_p.country = p_item.country
            # Could also merge sources: existing_p.source += f", {p_item.source}" 
            # For now, simple first-seen keeps its data, potentially updated if new one has more info.


    proxies_to_validate: List[ProxyItem] = list(unique_proxies_map.values())
    total_to_validate = len(proxies_to_validate)
    
    if total_to_validate > 0:
        print(f"[VALIDATOR] Validating {total_to_validate} unique proxies (source: {len(source_proxies)}) with {num_threads} threads. Test URL: {test_url}")
    else:
        print("[VALIDATOR] No unique proxies to validate."); return []

    if not REAL_IP and check_anonymity: print("[VALIDATOR_WARNING] Real IP not available, anonymity accuracy will be low.")

    results: List[ProxyItem] = []
    processed_count = 0
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_proxy = {
            executor.submit(test_single_proxy, proxy_item, timeout, test_url, anonymity_test_url, check_anonymity): proxy_item
            for proxy_item in proxies_to_validate
        }
        for future in as_completed(future_to_proxy):
            original_proxy_item = future_to_proxy[future]
            try:
                updated_proxy_item = future.result()
                results.append(updated_proxy_item)
            except Exception as exc:
                print(f"[VALIDATOR_ERROR] Proxy {original_proxy_item.proxy_string()} task failed: {exc}")
                original_proxy_item.is_valid = False; original_proxy_item.response_time = None
                original_proxy_item.anonymity = "Error (Task Failed)"; original_proxy_item.last_checked = datetime.now().isoformat()
                results.append(original_proxy_item)
            
            processed_count += 1
            if total_to_validate > 0: print(f"[VALIDATOR] Progress: {processed_count}/{total_to_validate} ({((processed_count/total_to_validate)*100):.1f}%)", end='\r', flush=True)

    if total_to_validate > 0: print()
    valid_count_final = sum(1 for p in results if p.is_valid)
    print(f"[VALIDATOR] Validation complete. Results: {len(results)} processed, {valid_count_final} valid.")
    return results