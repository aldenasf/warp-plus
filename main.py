import os
import sys
import time
import json
import random
import string
import requests
from keepalive import keepalive
from datetime import datetime
from dotenv import load_dotenv

# env  : Loads referrer from .env with the property name REFERRER (default)
# json : Loads referrer from json with the property name Referrer
REFERRER_TYPE = 'env'


def generate_str(length: int):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))


def generate_int(length: int):
    digit = string.digits
    return ''.join((random.choice(digit) for i in range(length)))


if REFERRER_TYPE == 'env':
    load_dotenv()
    referrer = os.environ.get("REFERRER")
elif REFERRER_TYPE == 'json':
    config = json.load(open('config.json'))
    referrer = config['referrer']
else:
    print("[ERROR] Invalid referrer type. Possible values are 'env' and 'json'")
    exit(1)

show_referrer = False
url = f'https://api.cloudflareclient.com/v0a{generate_int(3)}/reg'
tracker = {}
session_tracker = {}


def increment_good():
    r = json.load(open('tracker.json'))

    r['good'] += 1
    session_tracker['good'] += 1
    tracker['good'] = r['good']

    with open('tracker.json', 'w') as w:
        json.dump(r, w)


def increment_bad():
    r = json.load(open('tracker.json'))

    r['bad'] += 1
    session_tracker['bad'] += 1
    tracker['bad'] = r['bad']

    with open('tracker.json', 'w') as w:
        json.dump(r, w)


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
        session_tracker['good'] = 0
        session_tracker['bad'] = 0
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

    print(
        f"total    : {str(tracker['good']):>5} good | {tracker['bad']:>5} bad | {tracker['good'] + tracker['bad']:>5} total ")
    print(
        f"session  : {session_tracker['good']:>5} good | {session_tracker['bad']:>5} bad | {session_tracker['good'] + session_tracker['bad']:>5} total ")


def tracker_code(status_code, message):
    return f"code     : {str(status_code):>10} | {message}"


def countdown_sleep(seconds: int):
    for i in range(seconds, 0, -1):
        sys.stdout.write(f"sleeping for {i} seconds...\r")
        time.sleep(1)
    sys.stdout.write("\n")


def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')


def run():
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
    keepalive()
    if referrer == None or len(referrer) == 0:
        print("[ERROR] Property 'referrer' is empty or None. Please create a .env file and define REFERRER")
        exit(1)
    sync_tracker()
    while True:
        result = run()

        if show_referrer:
            print(f"referrer : {referrer}")

        if result == 200:
            increment_good()
            print_tracker(result)
            countdown_sleep(18)
        elif result == 429:
            increment_bad()
            print_tracker(result)
            countdown_sleep(18)
        else:
            increment_bad()
            print_tracker(result)
            countdown_sleep(1)

        clear_terminal()
