import requests
from bs4 import BeautifulSoup
from typing import List

from app.backend.models import ProxyItem
from .base import ProxyProviderBase 

class FreeProxyListNetProvider(ProxyProviderBase):
    """
    Fetches proxies from free-proxy-list.net.
    """
    SOURCE_NAME = "free-proxy-list.net"

    def fetch_proxies(self) -> List[ProxyItem]:
        """
        Fetches a list of proxies from free-proxy-list.net.
        """
        url = "https://free-proxy-list.net/"
        proxies: List[ProxyItem] = []
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                table = soup.find('table', class_='table-striped')
                if table:
                    tbody = table.find('tbody')
                    if tbody:
                        rows = tbody.find_all('tr')
                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) >= 8:
                                ip_address = cols[0].text.strip()
                                port_str = cols[1].text.strip()
                                country = cols[3].text.strip()
                                anonymity = cols[4].text.strip()
                                https_status = cols[6].text.strip().lower()
                                last_checked = cols[7].text.strip()
                                
                                protocol = "https" if https_status == "yes" else "http"
                                
                                try:
                                    port = int(port_str)
                                    proxies.append(ProxyItem(
                                        ip=ip_address,
                                        port=port,
                                        protocol=protocol,
                                        country=country,
                                        anonymity=anonymity,
                                        source=self.SOURCE_NAME,
                                        last_checked=last_checked
                                    ))
                                except ValueError:
                                    print(f"Skipping proxy with invalid port: {ip_address}:{port_str}")
                                    continue
        except requests.RequestException as e:
            print(f"Error fetching proxies from {self.SOURCE_NAME}: {e}")
            return [] 
        
        return proxies