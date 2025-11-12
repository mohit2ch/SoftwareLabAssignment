import requests
import json

def get_proxyscrape():
    # Get proxies from Proxyscrape API in format protocol://ip:port list
    url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json"
    response = requests.get(url)
    if response.status_code == 200:
        prxlist = []
        for prx in response.json()["proxies"]:
            prxlist.append(prx['proxy'])
        return prxlist
    return []

# proxies = get_proxyscrape()
# print(proxies)
