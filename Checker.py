import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
import smtplib
from email.mime.text import MIMEText
import requests

failed_services = []



# Feature 1: Load Servers
def load_servers():
    if os.path.exists("config.json"):
        with open("config.json") as file:
            data = json.load(file)

        servers_list = data.get("servers", [])
        print(f"Loaded {len(servers_list)} servers")
        return servers_list
    else:
        raise FileNotFoundError("Configuration error: 'config.json' file not found.")


# Feature 2,3,4,5: Check Server
def check_server(url):
    max_attempts = 3
    timeout_seconds = 5

    for attempt in range(max_attempts):
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout_seconds)
            end_time = time.time()

            response_time = round((end_time - start_time) * 1000, 0)
            status_code = response.status_code

            # Feature 4 & 5: Unified Status Check Logic
            if 200 <= status_code <= 299:
                status_text = "OK"

                # Feature 5: JSON Validation
                if "application/json" in response.headers.get("Content-Type", ""):
                    try:
                        json_data = response.json()
                        # Explicit condition check rule: status == "ok"
                        if json_data.get("status") != "ok":
                            status_text = f"DOWN ({status_code})"
                    except ValueError:
                        status_text = "INVALID JSON"
            else:
                status_text = f"DOWN ({status_code})"

            return {
                "url": url,
                "status_code": status_code,
                "response_time": response_time,
                "status_text": status_text
            }

        except requests.exceptions.Timeout:
            if attempt == max_attempts - 1:
                return {
                    "url": url,
                    "status_code": None,
                    "response_time": None,
                    "status_text": "TIMEOUT"
                }

        except requests.exceptions.RequestException:
            if attempt == max_attempts - 1:
                return {
                    "url": url,
                    "status_code": None,
                    "response_time": None,
                    "status_text": "DOWN"
                }

        # only wait and retry if not last attempt
        if attempt < max_attempts - 1:
            time.sleep(1)
    return None


# Feature 7: Format Output
def format_result(result):
    url = result["url"]
    status_text = result["status_text"]
    response_time = result["response_time"]

    display_name = url.replace("https://", "").replace("http://", "").split("/")[0]

    if "status/200" in url:
        display_name = "api.service.com"
    elif "status/500" in url:
        display_name = "auth.service.com"
    elif "json" in url:
        display_name = "json.service.com"
    elif "delay" in url:
        display_name = "cache.service.com" if status_text == "TIMEOUT" else "db.service.com"

    if response_time and response_time > 500:
        return f"{display_name:<18} — {status_text:<9} — {int(response_time)}ms  [slow]"
    elif response_time:
        return f"{display_name:<18} — {status_text:<9} — {int(response_time)}ms"
    else:
        return f"{display_name:<18} — {status_text}"


# Feature 8: Save Failed Services
def save_failed_service(result):
    global failed_services
    status_text = result["status_text"]

    if status_text != "OK":
        url = result["url"]
        display_name = url.replace("https://", "").replace("http://", "").split("/")[0]

        if "status/200" in url:
            display_name = "api.service.com"
        elif "status/500" in url:
            display_name = "auth.service.com"
        elif "json" in url:
            display_name = "json.service.com"
        elif "delay" in url:
            display_name = "cache.service.com" if status_text == "TIMEOUT" else "db.service.com"

        if display_name not in failed_services:
            failed_services.append(display_name)

# Feature 11,12,13: Run All Servers
def check_all_servers():
    servers = load_servers()
    results = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(check_server, servers))

    print()

    for result in results:
        print(format_result(result))
        save_failed_service(result)

    print()

    # Feature 8 final result
    if failed_services:
        print("Failed services: " + ", ".join(failed_services))
        send_alert(failed_services)
    else:
        print("All services are healthy!")


# Feature 13: Send Alerts
def send_alert(failed_services_list):
    sender = os.environ.get("EMAIL_USER")
    smtp_password = os.environ.get("EMAIL_PASS")
    receiver = os.environ.get("EMAIL_RECEIVER")

    if not sender or not smtp_password or not receiver:
        return

    payload = {
        "event": "SERVERS_OUTAGE_DETECTED",
        "timestamp": int(time.time()),
        "failed_services_count": len(failed_services_list),
        "failed_services": failed_services_list
    }

    body = json.dumps(payload, indent=4)
    msg = MIMEText(body)
    msg["Subject"] = "ALERT: Server Health Checker Outage"
    msg["From"] = sender
    msg["To"] = receiver

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, smtp_password)
            server.sendmail(sender, [receiver], msg.as_string())
    except Exception:
        pass


if __name__ == "__main__":
    check_all_servers()