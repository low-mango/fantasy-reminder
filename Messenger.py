import os
import requests
import sys

from dotenv import load_dotenv
load_dotenv()

REQUEST_TIMEOUT = 30

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

if __name__ == "__main__":
    message = "🚨 FPL Deadline Reminder! 🚨\n\nYou have 3 hours left until the next FPL deadline. Time to do some research! 📖📚⚽"
    send_telegram_message(message)