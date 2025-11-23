from typing import List
from .base import ProxyProviderBase # ProxyItem is no longer imported from base
from app.backend.models import ProxyItem # Import ProxyItem from models
from .freeproxylist import FreeProxyListNetProvider
from .geonode import GeoNodeProvider
from .proxyscrape import ProxyScrapeProvider

__all__ = [
    "ProxyItem",
    "ProxyProviderBase",
    "FreeProxyListNetProvider",
    "GeoNodeProvider",
    "ProxyScrapeProvider",
]

def get_all_proxies() -> List[ProxyItem]:
    """Fetches proxies from all available providers and returns a single list."""
    all_proxies: List[ProxyItem] = []
    providers = [
        FreeProxyListNetProvider(),
        GeoNodeProvider(),
        ProxyScrapeProvider(),
    ]

    for provider in providers:
        try:
            proxies = provider.fetch_proxies()
            all_proxies.extend(proxies)
            print(f"Successfully fetched {len(proxies)} proxies from {provider.SOURCE_NAME}")
        except (IOError, ValueError, RuntimeError) as e:
            print(f"Error fetching proxies from {provider.SOURCE_NAME}: {e}")
            continue
    
    return all_proxies
