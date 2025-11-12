import json
import requests
from bs4 import BeautifulSoup


def get_proxies_fpl():
    # Get proxies from Free Proxy List website in format protocol://ip:port list
    url = "https://free-proxy-list.net/"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find('table', class_='table-striped')
        tbody = table.find('tbody')
        rows = tbody.find_all('tr')
        data = []
        for row in rows:
            cols = row.find_all('td')
            ip_address = cols[0].text.strip()
            port = cols[1].text.strip()
            https_status = cols[6].text.strip().lower()
            protocol = "https" if https_status == "yes" else "http"
            data.append(f"{protocol}://{ip_address}:{port}")
        return data
    return []
