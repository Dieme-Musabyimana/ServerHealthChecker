import json
import time
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

#feature2&3: check server print status codes
def check_server(url):
    start_time = time.time()
    response = requests.get(url)
    status_code = response.status_code
    end_time = time.time()
    response_time = round((end_time-start_time)*1000,0)
    if 200 <= status_code <= 299:
        healthy = True
    else: healthy = False
    return {
        "url": url,
        "status_code": status_code,
        "response_time": response_time,
        "healthy": healthy
    }

for server in servers:
    results = check_server(server)
    print(results)


