# fantasy-reminder

Telegram bot that reminds a Fantasy Premier League mini-league about the upcoming
gameweek deadline. `Messenger.py` sends the message; `Scheduler.py` rewrites the
cron in `.github/workflows/messenger.yml` so the next run lands before the next
deadline.

## Change workflow

Never commit directly to `main`. Steps 4 and 5 need an explicit request: unless
the instructions ask you to commit, push, or open a PR, stop after step 3 and
report what changed, leaving the work uncommitted in the working tree.

1. `git fetch origin && git switch -c <branch> origin/main` — always branch from
   fresh `origin/main`, never from a stale local `main` (see "Automated commits").
2. Make the change.
3. `python -m pytest` — must pass before pushing.
4. Commit and `git push -u origin <branch>`.
5. Open a PR against `main` (see "Opening PRs").

Report the PR URL whenever you open one.

Branch names are short, descriptive, kebab-case, with no prefix — matching the
existing history: `fix-scheduler`, `notify-rescheduling`, `pip-tools`.

## Pushing

The remote URL uses an SSH host alias, so pushing depends on `~/.ssh/config` being
applied. A push rejected with `Permission to ... denied` means it authenticated as
the wrong account; retry it in an environment where that config is honoured. This
repo is public, so `git fetch` works regardless of identity and the problem only
ever surfaces at push time.

Do not work around it by pinning a key with `core.sshCommand`. Overriding how git
invokes `ssh` can cut off git's network access in restricted environments, which
breaks `git fetch` as well.

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
