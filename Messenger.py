import os
import sys
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

REQUEST_TIMEOUT = 30
REMINDER_LEAD_HOURS = 24
FPL_BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"

def send_telegram_message(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        print("Error: TELEGRAM_TOKEN or TELEGRAM_CHAT_ID not found in environment variables.")
        sys.exit(1)

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }

    try:
        response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        print("Message sent successfully!")
    except requests.exceptions.Timeout:
        print("Failed to send message: request timed out")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print("Failed to send message")
        if e.response is not None:
            print(f"Telegram API returned HTTP {e.response.status_code}")
        sys.exit(1)

def parse_deadline(deadline_time):
    return datetime.strptime(deadline_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def next_future_deadline(events, now):
    # Known gap: this is whichever deadline is still ahead when the job starts,
    # not the gameweek the cron was set for. A start more than ~24 hours late
    # (after that deadline) reports the following gameweek.
    upcoming = []
    for event in events:
        deadline_time = event.get("deadline_time")
        if not deadline_time:
            continue
        deadline = parse_deadline(deadline_time)
        if deadline > now:
            upcoming.append(deadline)
    if not upcoming:
        return None
    return min(upcoming)


def fetch_events():
    response = requests.get(FPL_BOOTSTRAP_URL, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()["events"]


def format_duration(delta):
    total_minutes = int(delta.total_seconds() // 60)
    hours, minutes = divmod(total_minutes, 60)
    parts = []
    if hours:
        parts.append("1 hour" if hours == 1 else f"{hours} hours")
    if minutes:
        parts.append("1 minute" if minutes == 1 else f"{minutes} minutes")
    if not parts:
        return "less than a minute"
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return parts[0]


def build_reminder_message(deadline, now):
    remaining = format_duration(deadline - now)
    return (
        f"🚨 FPL Deadline Reminder! 🚨\n\nYou have {remaining} left "
        "until the next FPL deadline. Time to do some research! 📖📚⚽"
    )


def main():
    try:
        events = fetch_events()
    except requests.exceptions.RequestException:
        print("Failed to fetch FPL deadlines")
        sys.exit(1)

    now = datetime.now(timezone.utc)
    deadline = next_future_deadline(events, now)
    if deadline is None:
        print("No upcoming deadline found.")
        sys.exit(1)

    send_telegram_message(build_reminder_message(deadline, now))


if __name__ == "__main__":
    main()
