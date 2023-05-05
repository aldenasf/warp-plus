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
wait_time = 0


def increment_good():
    session_tracker['good'] += 1


def increment_bad():
    session_tracker['bad'] += 1


def setup_tracker():
    global wait_time

    session_tracker['good'] = 0
    session_tracker['bad'] = 0

    if tracker['last_status'] == 200:
        wait_time = config['good-response-wait']
    elif tracker['last_status'] == 429:
        wait_time = config['rate-limit-response-wait']
    else:
        wait_time = config['bad-response-wait']


def sync_tracker():
    try:
        r = json.load(open('tracker.json'))

        for property in ["good", "bad"]:
            if not property in r:
                r[property] = 0
            with open('tracker.json', 'w') as w:
                json.dump(r, w, indent=2)

        tracker['good'] = r['good']
        tracker['bad'] = r['bad']

        if not 'last_run' in r:
            r['last_run'] = ""
            with open('tracker.json', 'w') as w:
                json.dump(r, w, indent=2)

        tracker['last_run'] = r['last_run']
        tracker['last_status'] = r['last_status']

    except:
        wtf = {"good": 0, "bad": 0, "last_run": "", "last_status": 0}
        print(wtf)
        with open('tracker.json', 'w') as w:
            json.dump(
                wtf, w, indent=2)
        sync_tracker()


def print_tracker(status_code: int):
    if status_code == 200:
        print(tracker_code(status_code, "good. sleeping..."))
    elif status_code == 429:
        print(tracker_code(status_code, "rate limit. sleeping..."))
    else:
        print(tracker_code(status_code, "retrying..."))

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


def update_tracker():
    global wait_time
    global tracker
    global session_tracker

    tracker['good'] = tracker['good'] + session_tracker['good']
    tracker['bad'] = tracker['bad'] + session_tracker['bad']

    tracker['last_run'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tracker['last_status'] = result

    if tracker['last_status'] == 200:
        wait_time = config['good-response-wait']
    elif tracker['last_status'] == 429:
        wait_time = config['rate-limit-response-wait']
    else:
        wait_time = config['bad-response-wait']

    with open('tracker.json', 'w') as w:
        json.dump(tracker, w, indent=2)


def countdown_sleep(seconds: float):
    while seconds > 0:
        sys.stdout.write(f"sleeping for {seconds:.2f} seconds...\r")
        time.sleep(1)
        seconds -= 1
    sys.stdout.write('\n')


def countdown_sleep_from_last(seconds: float, last_run: str | None = None):
    try:
        last_time = datetime.strptime(last_run, '%Y-%m-%d %H:%M:%S')
        elapsed_time = datetime.now() - last_time
        remaining_time = seconds - elapsed_time.total_seconds()
        if remaining_time > 0:
            countdown_sleep(remaining_time)
    except ValueError:
        print(f"{BColor.YELLOW + Style.BRIGHT} WARN {Style.RESET_ALL} Property 'last_run' with the value '{last_run}' is not a valid datetime string. Executing normal countdown sleep...")
        countdown_sleep(seconds)


def clear_terminal():
    # os.system('cls' if os.name == 'nt' else 'clear')
    return


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

    if config['keep-alive-enabled']:
        keepalive()

    if referrer == None or len(referrer) == 0:
        print(f"{BColor.RED + Style.BRIGHT} ERROR {Style.RESET_ALL} Property 'referrer' is empty or None. Please set the referrer in config.yml or enviroment variable")
        exit(1)

    sync_tracker()
    setup_tracker()

    while True:
        countdown_sleep_from_last(wait_time, tracker['last_run'])
        clear_terminal()
        result = run()

        if result == 200:
            increment_good()
        else:
            increment_bad()

        if config['show-referrer']:
            print(f"referrer : {referrer}")

        update_tracker()
        print_tracker(result)
