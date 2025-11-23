import json
from typing import List
from urllib.parse import urlparse

import requests

from app.backend.models import ProxyItem

from .base import ProxyProviderBase


class ProxyScrapeProvider(ProxyProviderBase):
    """
    Fetches proxies from proxyscrape.com API.
    """
    SOURCE_NAME = "proxyscrape.com"
    API_URL = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json"

    def fetch_proxies(self) -> List[ProxyItem]:
        """
        Fetches a list of proxies from Proxyscrape.
        """
        proxies: List[ProxyItem] = []
        try:
            response = requests.get(self.API_URL, timeout=20) # Increased timeout slightly
            response.raise_for_status()  
            data = response.json()

            # The "proxies" key contains a list of dictionaries,
            # each dictionary has a "proxy" key with the actual proxy string.
            raw_proxy_entries = data.get("proxies", [])
            if not isinstance(raw_proxy_entries, list):
                print(f"Expected a list of proxies from {self.SOURCE_NAME}, but got {type(raw_proxy_entries)}")
                return []

            for proxy_entry in raw_proxy_entries:
                if not isinstance(proxy_entry, dict):
                    print(f"Skipping non-dictionary proxy entry: {proxy_entry} from {self.SOURCE_NAME}")
                    continue
                
                proxy_str = proxy_entry.get("proxy")

                if not isinstance(proxy_str, str):
                    print(f"Skipping entry with missing or non-string 'proxy' field: {proxy_entry} from {self.SOURCE_NAME}")
                    continue
                
                try:
                    # Example: "http://123.45.67.89:8080"
                    parsed_url = urlparse(proxy_str)
                    protocol = parsed_url.scheme
                    ip = parsed_url.hostname
                    port_val = parsed_url.port # This is an int or None

                    if not protocol or not ip or port_val is None:
                        print(f"Skipping malformed proxy string (missing protocol, IP, or port): {proxy_str} from {self.SOURCE_NAME}")
                        continue
                    
                    port = port_val

                    if protocol.lower() in ["http", "https", "socks4", "socks5"]:
                        # Extract additional details if available and desired
                        country = proxy_entry.get("country")
                        anonymity = proxy_entry.get("anonymity")
                        # last_checked = proxy_entry.get("last_seen") # Consider date format if used
                        # response_time = proxy_entry.get("timeout") # or "average_timeout"

                        proxies.append(ProxyItem(
                            ip=ip,
                            port=port, 
                            protocol=protocol.lower(),
                            source=self.SOURCE_NAME,
                            country=country if isinstance(country, str) else None,
                            anonymity=anonymity if isinstance(anonymity, str) else None,
                            # response_time=float(response_time) if response_time is not None else None,
                            # last_checked=str(last_checked) if last_checked is not None else None,
                        ))
                except Exception as e: 
                    print(f"Error parsing proxy string '{proxy_str}' from {self.SOURCE_NAME}: {e}")
                    continue
        
        except requests.RequestException as e:
            print(f"Error fetching proxies from {self.SOURCE_NAME}: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {self.SOURCE_NAME}: {e}")
            return []

        return proxies
