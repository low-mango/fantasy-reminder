# fantasy-reminder

Telegram reminders for Fantasy Premier League deadlines — sent **24 hours before** each gameweek locks.

## How it works

1. **Scheduler** reads the next FPL deadline from the official API and updates the messenger workflow’s cron schedule.
2. **Messenger** sends a Telegram message when that cron fires, then triggers the scheduler again for the following gameweek.

Runs on GitHub Actions (no server needed).

## Setup

Add these repository secrets:

- `TELEGRAM_TOKEN` — from the Telegram Bot
- `TELEGRAM_CHAT_ID` — your chat or group ID
- `WORKFLOW_PUSH_TOKEN` — classic personal access token the scheduler uses to push cron updates

To update `WORKFLOW_PUSH_TOKEN`: regenerate the classic token (GitHub → **Settings → Developer settings → Personal access tokens → Tokens (classic)**), then replace the value under the repo’s **Settings → Secrets and variables → Actions**.

Enable the workflows under **Actions**. The messenger cron is overwritten automatically after the first run.
