import re
import sys
from datetime import datetime, timezone, timedelta

import requests
from dotenv import load_dotenv

from Messenger import send_telegram_message

load_dotenv()

REQUEST_TIMEOUT = 30

def parse_deadline(gw):
    return datetime.strptime(gw['deadline_time'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

def get_next_deadline():
    r = requests.get(
        'https://fantasy.premierleague.com/api/bootstrap-static/',
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    events = r.json()['events']


    now = datetime.now(timezone.utc)
    print(f"Current UTC datetime (now): {now}")

    next_gw = next((gw for gw in events if gw.get('is_next')), None)
    if not next_gw:
        print("No gameweek with is_next found.")
        return None

    start_idx = events.index(next_gw)
    print(f"Start index: {start_idx}")
    for gw in events[start_idx:]:
        deadline_dt = parse_deadline(gw)
        reminder = deadline_dt - timedelta(hours=3)
        if reminder > now:
            print(f"Next deadline: {deadline_dt} ({gw['name']})")
            return deadline_dt

    return None

def update_messenger_workflow(deadline_dt):
    reminder = deadline_dt - timedelta(hours=3)
    new_cron = f"{reminder.minute} {reminder.hour} {reminder.day} {reminder.month} *"
    print(f"New cron: {new_cron}")

    path = ".github/workflows/messenger.yml"
    with open(path, "r") as f:
        content = f.read()

    updated_content, count = re.subn(
        r"- cron: '.*' # DYNAMIC_SCHEDULE",
        f"- cron: '{new_cron}' # DYNAMIC_SCHEDULE",
        content,
    )

    if count == 0:
        print("Error: DYNAMIC_SCHEDULE cron line not found in messenger.yml")
        sys.exit(1)

    with open(path, "w") as f:
        f.write(updated_content)


def reschedule_and_notify(deadline_dt):
    reminder = deadline_dt - timedelta(hours=3)
    update_messenger_workflow(deadline_dt)
    print(f"Rescheduled for: {reminder}")
    when = reminder.strftime("%Y-%m-%d %H:%M UTC")
    send_telegram_message(
        f"✅ FPL reminder re-scheduled for {when} "
        f"(3 hours before the next deadline)."
    )


if __name__ == "__main__":
    next_dt = get_next_deadline()
    if next_dt:
        reschedule_and_notify(next_dt)
    else:
        print("No upcoming reminder to schedule.")
        sys.exit(1)
