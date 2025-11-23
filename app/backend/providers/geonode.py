import json
from datetime import datetime
from typing import List, Optional
import requests
from app.backend.models import ProxyItem
from .base import ProxyProviderBase

class GeoNodeProvider(ProxyProviderBase):
    """
    Fetches proxies from proxylist.geonode.com API.
    """
    SOURCE_NAME = "proxylist.geonode.com"
    API_URL = "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"

    def fetch_proxies(self) -> List[ProxyItem]:
        """
        Fetches a list of proxies from Geonode.
        """
        proxies: List[ProxyItem] = []
        try:
            response = requests.get(self.API_URL, timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()

            for prx_data in data.get("data", []):
                ip = prx_data.get("ip")
                port_str = prx_data.get("port")
                
                if not ip or not port_str:
                    continue

                try:
                    port = int(port_str)
                except ValueError:
                    print(f"Skipping proxy with invalid port: {ip}:{port_str} from {self.SOURCE_NAME}")
                    continue

                country = prx_data.get("country")
                anonymity = prx_data.get("anonymityLevel")
                
                response_time_val = prx_data.get("responseTime") 
                if response_time_val is None:
                    response_time_val = prx_data.get("latency")

                last_checked_timestamp = prx_data.get("lastChecked")
                last_checked_str: Optional[str] = None
                if last_checked_timestamp:
                    try:
                        last_checked_str = datetime.fromtimestamp(last_checked_timestamp).isoformat()
                    except (TypeError, ValueError):
                        print(f"Skipping proxy with invalid lastChecked timestamp: {last_checked_timestamp} from {self.SOURCE_NAME}")
                        continue

                protocols = prx_data.get("protocols", [])
                for protocol in protocols:
                    if protocol.lower() in ["http", "https", "socks4", "socks5"]:
                        proxies.append(ProxyItem(
                            ip=ip,
                            port=port,
                            protocol=protocol.lower(),
                            country=country,
                            anonymity=anonymity,
                            source=self.SOURCE_NAME,
                            response_time=float(response_time_val) if response_time_val is not None else None,
                            last_checked=last_checked_str
                        ))
        
        except requests.RequestException as e:
            print(f"Error fetching proxies from {self.SOURCE_NAME}: {e}")
            return [] 
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {self.SOURCE_NAME}: {e}")
            return []

        return proxies