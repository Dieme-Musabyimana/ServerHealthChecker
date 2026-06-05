import json


def load_servers():
    with open("config.json") as file:
        data = json.load(file)
    return data["servers"]

servers = load_servers()
for server in servers:
       print(f"{server}")
print("Loaded " + str(len(servers)) + " servers")


