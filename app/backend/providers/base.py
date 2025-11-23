import json
from abc import ABC, abstractmethod
from typing import List
from app.backend.models import ProxyItem 


class ProxyProviderBase(ABC):
    """
    Abstract base class for proxy providers.
    Subclasses must implement the `fetch_proxies` method.
    """

    @abstractmethod
    def fetch_proxies(self) -> List[ProxyItem]:
        """
        Fetches a list of proxies from the specific provider.
        This method must be implemented by subclasses.

        Returns:
            List[ProxyItem]: A list of ProxyItem objects.
        """

    def get_proxies_json(self) -> str:
        """
        Fetches proxies and returns them as a JSON string.

        Returns:
            str: A JSON string representing the list of proxies.
        """
        proxies = self.fetch_proxies()
        return json.dumps([proxy.model_dump() for proxy in proxies], indent=2)
