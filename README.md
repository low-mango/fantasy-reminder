# fantasy-reminder

Telegram reminders for Fantasy Premier League deadlines — sent **3 hours before** each gameweek locks.

## How it works

1. **Scheduler** reads the next FPL deadline from the official API and updates the messenger workflow’s cron schedule.
2. **Messenger** sends a Telegram message when that cron fires, then triggers the scheduler again for the following gameweek.

Runs on GitHub Actions (no server needed).

## Setup

Add these repository secrets:

- `TELEGRAM_TOKEN` — from the Telegram Bot
- `TELEGRAM_CHAT_ID` — your chat or group ID

Enable the workflows under **Actions**. The messenger cron is overwritten automatically after the first run.
