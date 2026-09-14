# fantasy-reminder

Telegram bot that reminds a Fantasy Premier League mini-league about the upcoming
gameweek deadline. `Messenger.py` sends the message; `Scheduler.py` rewrites the
cron in `.github/workflows/messenger.yml` so the next run lands before the next
deadline.

## Change workflow

Never commit directly to `main`. For every change:

1. `git fetch origin && git switch -c <branch> origin/main` — always branch from
   fresh `origin/main`, never from a stale local `main` (see "Automated commits").
2. Make the change.
3. `python -m pytest` — must pass before pushing.
4. Commit and `git push -u origin <branch>`.
5. Open a PR against `main` (see "Opening PRs").

Report the PR URL when done.

Branch names are short, descriptive, kebab-case, with no prefix — matching the
existing history: `fix-scheduler`, `notify-rescheduling`, `pip-tools`.

## Opening PRs

```bash
gh pr create --base main --title "<summary>" --body "<what changed and why>"
```

Write a real body rather than using `--fill`: PRs here are reviewed
asynchronously, often days later, so the description has to stand on its own.

## Automated commits

The `Scheduler` workflow pushes to `main` on its own, with the message
`Scheduler: Rescheduled messenger for next gameweek`. Two consequences:

- `main` moves without human action, so always re-fetch before branching.
- Do not edit the `cron:` line in `.github/workflows/messenger.yml`. It carries a
  `DYNAMIC_SCHEDULE` marker and is owned by `Scheduler.py`; editing it by hand
  creates conflicts with the bot. Change the scheduling logic in `Scheduler.py`
  instead.

## Secrets

`.env` holds `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` and is gitignored. Never
commit it, never read its values into a commit, log, or PR description. In CI
these come from repository secrets.

Tests must not need real credentials — mock them with
`@patch.dict("os.environ", ...)`, as `tests/test_messenger.py` already does.

## Dependencies

Managed with pip-tools. Edit the `.in` files, never the `.txt` files:

```bash
pip-compile requirements.in
pip-compile requirements-dev.in
pip-sync requirements-dev.txt
```
