import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Adjust PARENT_DIR to be the project root
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

import json
from typing import Type, List as TypingList

from app.backend.models import ProxyItem # Changed to absolute import
from app.backend.providers.base import ProxyProviderBase # Changed to absolute import
from app.backend.providers.freeproxylist import FreeProxyListNetProvider # Changed to absolute import
from app.backend.providers.geonode import GeoNodeProvider # Changed to absolute import
from app.backend.providers.proxyscrape import ProxyScrapeProvider # Changed to absolute import

# List of all provider classes to be tested
ALL_PROVIDER_CLASSES: TypingList[Type[ProxyProviderBase]] = [
    FreeProxyListNetProvider,
    GeoNodeProvider,
    ProxyScrapeProvider,
]

def test_single_provider(provider_class: Type[ProxyProviderBase]):
    """
    Tests a single proxy provider class.
    Instantiates the provider, fetches proxies, and checks JSON output.
    """
    provider_instance = provider_class()
    source_name = getattr(provider_instance, 'SOURCE_NAME', provider_class.__name__)
    print(f"--- Testing {source_name} ---")

    try:
        # Test fetch_proxies()
        print(f"Attempting to fetch proxies from {source_name}...")
        proxies: TypingList[ProxyItem] = provider_instance.fetch_proxies()

        if proxies:
            print(f"Successfully fetched {len(proxies)} proxies.")
        else:
            print(f"No proxies fetched from {source_name}.")

        # Test get_proxies_json()
        print(f"\nAttempting to get JSON output from {source_name}...")
        json_output_str = provider_instance.get_proxies_json()
        
        if json_output_str:
            print(f"Successfully received JSON string from {source_name}.")
            try:
                parsed_json = json.loads(json_output_str)
                if isinstance(parsed_json, list):
                    print(f"JSON output is a list with {len(parsed_json)} items.")
                    if len(parsed_json) > 0 and len(proxies) > 0:
                        if len(parsed_json) == len(proxies):
                            print("JSON item count matches fetched proxy count.")
                        else:
                            print(f"WARNING: JSON item count ({len(parsed_json)}) does not match fetched proxy count ({len(proxies)}).")
                        if all(isinstance(item, dict) for item in parsed_json):
                            print("All items in JSON list are dictionaries as expected.")
                        else:
                            print("WARNING: Not all items in JSON list are dictionaries.")
                    elif len(parsed_json) == 0 and len(proxies) == 0:
                        print("JSON output is an empty list, consistent with no proxies fetched.")
                else:
                    print("WARNING: JSON output is not a list as expected.")
            except json.JSONDecodeError as e:
                print(f"ERROR: Failed to decode JSON string from {source_name}: {e}")
        else:
            print(f"Received empty JSON string from {source_name}.")

    except Exception as e:
        print(f"!!! ERROR during test for {source_name}: {e}")
        import traceback
        traceback.print_exc() 

    finally:
        print(f"--- Finished testing {source_name} ---")
        print("-" * 40 + "\n")


def main():
    """
    Main function to run tests for all registered proxy providers.
    """
    print("=============================================")
    print("   Starting All Proxy Provider Tests")
    print("=============================================\n")

    if not ALL_PROVIDER_CLASSES:
        print("No provider classes found in ALL_PROVIDER_CLASSES. Nothing to test.")
        return

    for provider_cls in ALL_PROVIDER_CLASSES:
        test_single_provider(provider_cls)

    print("=============================================")
    print("    All Proxy Provider Tests Finished")
    print("=============================================")

if __name__ == "__main__":
    main()
