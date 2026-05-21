from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, mock_open, patch

import pytest

import Scheduler


def test_parse_deadline():
    gw = {"deadline_time": "2026-05-21T18:30:00Z"}

    result = Scheduler.parse_deadline(gw)

    assert result == datetime(2026, 5, 21, 18, 30, tzinfo=timezone.utc)


@patch("Scheduler.requests.get")
def test_get_next_deadline_returns_upcoming_deadline(mock_get, capsys):
    now = datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc)
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "events": [
            {"name": "GW38", "is_next": True, "deadline_time": "2026-05-21T18:30:00Z"},
        ]
    }
    mock_get.return_value = mock_response

    with patch("Scheduler.datetime") as mock_datetime:
        mock_datetime.now.return_value = now
        mock_datetime.strptime = datetime.strptime
        result = Scheduler.get_next_deadline()

    assert result == datetime(2026, 5, 21, 18, 30, tzinfo=timezone.utc)
    assert "GW38" in capsys.readouterr().out


@patch("Scheduler.requests.get")
def test_get_next_deadline_skips_past_reminders(mock_get):
    now = datetime(2026, 5, 21, 16, 0, tzinfo=timezone.utc)
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "events": [
            {"name": "GW37", "is_next": True, "deadline_time": "2026-05-21T18:30:00Z"},
            {"name": "GW38", "deadline_time": "2026-05-28T18:30:00Z"},
        ]
    }
    mock_get.return_value = mock_response

    with patch("Scheduler.datetime") as mock_datetime:
        mock_datetime.now.return_value = now
        mock_datetime.strptime = datetime.strptime
        result = Scheduler.get_next_deadline()

    assert result == datetime(2026, 5, 28, 18, 30, tzinfo=timezone.utc)


@patch("Scheduler.requests.get")
def test_get_next_deadline_no_is_next_gameweek(mock_get, capsys):
    now = datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc)
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "events": [{"name": "GW38", "is_next": False, "deadline_time": "2026-05-21T18:30:00Z"}]
    }
    mock_get.return_value = mock_response

    with patch("Scheduler.datetime") as mock_datetime:
        mock_datetime.now.return_value = now
        mock_datetime.strptime = datetime.strptime
        result = Scheduler.get_next_deadline()

    assert result is None
    assert "No gameweek with is_next found" in capsys.readouterr().out


@patch("Scheduler.requests.get")
def test_get_next_deadline_all_reminders_passed(mock_get):
    now = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "events": [
            {"name": "GW38", "is_next": True, "deadline_time": "2026-05-21T18:30:00Z"},
        ]
    }
    mock_get.return_value = mock_response

    with patch("Scheduler.datetime") as mock_datetime:
        mock_datetime.now.return_value = now
        mock_datetime.strptime = datetime.strptime
        result = Scheduler.get_next_deadline()

    assert result is None


def test_update_messenger_workflow_writes_new_cron(capsys):
    deadline = datetime(2026, 5, 21, 15, 0, tzinfo=timezone.utc)
    reminder = deadline - timedelta(hours=3)
    expected_cron = f"{reminder.minute} {reminder.hour} {reminder.day} {reminder.month} *"
    original = "- cron: '0 0 1 1 *' # DYNAMIC_SCHEDULE\nother: line\n"
    mock_file = mock_open(read_data=original)

    with patch("builtins.open", mock_file):
        Scheduler.update_messenger_workflow(deadline)

    written = mock_file().write.call_args[0][0]
    assert f"- cron: '{expected_cron}' # DYNAMIC_SCHEDULE" in written
    assert f"New cron: {expected_cron}" in capsys.readouterr().out


def test_update_messenger_workflow_missing_cron_line(capsys):
    deadline = datetime(2026, 5, 21, 15, 0, tzinfo=timezone.utc)

    with patch("builtins.open", mock_open(read_data="schedule:\n  - cron: '0 0 * * *'\n")):
        with pytest.raises(SystemExit) as exc_info:
            Scheduler.update_messenger_workflow(deadline)

    assert exc_info.value.code == 1
    assert "DYNAMIC_SCHEDULE cron line not found" in capsys.readouterr().out
