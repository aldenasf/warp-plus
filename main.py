import os
import sys
import yaml
import json
import time
import random
import string
import requests
from datetime import datetime
from dotenv import load_dotenv
from keepalive import keepalive
from colorama import init, Fore as Color, Back as BColor, Style

init(convert=True)
config = yaml.safe_load(open('config.yml'))


def generate_str(length: int):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))


def generate_int(length: int):
    digit = string.digits
    return ''.join((random.choice(digit) for i in range(length)))


if config['referrer-type'] == 'env':
    load_dotenv()
    referrer = os.environ.get("REFERRER")
elif config['referrer-type'] == 'yml':
    referrer = config['referrer']
else:
    print(
        f"{BColor.RED} ERROR {BColor.RESET} Invalid referrer type. Possible values are 'env' and 'yml'\nSpecified value: {config['referrer']}")
    exit(1)

url = f'https://api.cloudflareclient.com/v0a{generate_int(3)}/reg'
tracker = {}
session_tracker = {}


def increment_good():
    session_tracker['good'] += 1

    if config['tracker-save']:
        r = json.load(open('tracker.json'))
        r['good'] += 1
        tracker['good'] = r['good']
        with open('tracker.json', 'w') as w:
            json.dump(r, w)


def increment_bad():
    session_tracker['bad'] += 1

    if config['tracker-save']:
        r = json.load(open('tracker.json'))
        r['bad'] += 1
        tracker['bad'] = r['bad']
        with open('tracker.json', 'w') as w:
            json.dump(r, w)


def setup_tracker():
    session_tracker['good'] = 0
    session_tracker['bad'] = 0


def sync_tracker():
    try:
        r = json.load(open('tracker.json'))

        for property in ["good", "bad"]:
            if not property in r:
                r[property] = 0
            with open('tracker.json', 'w') as w:
                json.dump(r, w)

        tracker['good'] = r['good']
        tracker['bad'] = r['bad']
    except json.decoder.JSONDecodeError:
        with open('tracker.json', 'w') as w:
            json.dump({"good": 0, "bad": 0}, w)
        sync_tracker()


def print_tracker(status_code: int):
    if status_code == 200:
        print(tracker_code(status_code, "good. sleeping..."))
    elif status_code == 429:
        print(tracker_code(status_code, "rate limit. sleeping..."))
    else:
        print(tracker_code(status_code, "retrying..."))

    if config['tracker-save']:
        print(
            f"total    :{Color.GREEN + Style.BRIGHT} {str(tracker['good']):>5} good {Color.RESET}|{Color.RED} {tracker['bad']:>5} bad {Color.RESET}|{Color.CYAN} {tracker['good'] + tracker['bad']:>5} total {Style.RESET_ALL}")

    print(
        f"session  :{Color.GREEN + Style.BRIGHT} {session_tracker['good']:>5} good {Color.RESET}|{Color.RED} {session_tracker['bad']:>5} bad {Color.RESET}|{Color.CYAN} {session_tracker['good'] + session_tracker['bad']:>5} total {Style.RESET_ALL}")


def tracker_code(status_code, message):
    if status_code == 200:
        color = Color.GREEN + Style.BRIGHT
    else:
        color = Color.RED + Style.BRIGHT

    return f"code     :{Style.BRIGHT + color} {str(status_code):>10} {Color.RESET}|{color} {message}{Style.RESET_ALL}"


def countdown_sleep(seconds: int):
    for i in range(seconds, 0, -1):
        sys.stdout.write(f"sleeping for {i} seconds...\r")
        time.sleep(1)
    sys.stdout.write("\n")


def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')


def run():
    time.sleep(0.5)
    return 200

    try:
        install_id = generate_str(22)
        body = {
            "key": f"{generate_str(43)}=",
            "install_id": install_id,
            "fcm_token": f"{install_id}:APA91b{generate_str(134)}",
            "referrer": referrer,
            "warp_enabled": False,
            "tos": datetime.now().isoformat()[:-3] + "-07:00",
            "type": "Android",
            "locale": "en_US"
        }

        headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'Host': 'api.cloudflareclient.com',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            'User-Agent': 'okhttp/3.12.1'
        }

        with requests.Session() as session:
            session.headers.update(headers)
            data = json.dumps(body).encode('utf8')
            response = session.post(url, data=data)
            status_code = response.status_code

        return status_code
    except Exception as err:
        print(err)
        exit


if __name__ == '__main__':
    if config['keep-alive-enabled']:
        keepalive()

    if referrer == None or len(referrer) == 0:
        print(f"{BColor.RED + Style.BRIGHT} ERROR {Style.RESET_ALL} Property 'referrer' is empty or None. Please set the referrer in config.yml or enviroment variable")
        exit(1)

    if config['tracker-save']:
        sync_tracker()

    setup_tracker()

    while True:
        result = run()

        if config['show-referrer']:
            print(f"referrer : {referrer}")

        if result == 200:
            increment_good()
            print_tracker(result)
            countdown_sleep(config['good-response-wait'])
        elif result == 429:
            increment_bad()
            print_tracker(result)
            countdown_sleep(config['rate-limit-response-wait'])
        else:
            increment_bad()
            print_tracker(result)
            countdown_sleep(config['bad-response-wait'])

        clear_terminal()
