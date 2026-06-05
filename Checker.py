import json
from http.client import responses

import requests


#feature1: load servers
def load_servers():
    with open("config.json") as file:
        data = json.load(file)
    return data["servers"]

servers = load_servers()
for server in servers:
       print(f"{server}")
print("Loaded " + str(len(servers)) + " servers")

#feature2: check server and print status codes
def check_server(url):
    response = requests.get(url)
    status_code = response.status_code
    return {
        "url": url,
        "status_code": status_code
    }

for server in servers:
    results = check_server(server)
    print(results)


