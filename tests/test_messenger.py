from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests

import Messenger


@patch.dict("os.environ", {"TELEGRAM_TOKEN": "test-token", "TELEGRAM_CHAT_ID": "12345"})
@patch("Messenger.requests.post")
def test_send_telegram_message_success(mock_post, capsys):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    Messenger.send_telegram_message("hello")

    mock_post.assert_called_once_with(
        "https://api.telegram.org/bottest-token/sendMessage",
        json={"chat_id": "12345", "text": "hello"},
        timeout=Messenger.REQUEST_TIMEOUT,
    )
    assert "Message sent successfully!" in capsys.readouterr().out


@patch.dict("os.environ", {}, clear=True)
def test_send_telegram_message_missing_credentials(capsys):
    with pytest.raises(SystemExit) as exc_info:
        Messenger.send_telegram_message("hello")

    assert exc_info.value.code == 1
    assert "TELEGRAM_TOKEN or TELEGRAM_CHAT_ID not found" in capsys.readouterr().out


@patch.dict("os.environ", {"TELEGRAM_TOKEN": "test-token", "TELEGRAM_CHAT_ID": "12345"})
@patch("Messenger.requests.post", side_effect=requests.exceptions.Timeout)
def test_send_telegram_message_timeout(mock_post, capsys):
    with pytest.raises(SystemExit) as exc_info:
        Messenger.send_telegram_message("hello")

    assert exc_info.value.code == 1
    assert "request timed out" in capsys.readouterr().out


@patch.dict("os.environ", {"TELEGRAM_TOKEN": "test-token", "TELEGRAM_CHAT_ID": "12345"})
@patch("Messenger.requests.post")
def test_send_telegram_message_http_error(mock_post, capsys):
    mock_response = MagicMock()
    mock_response.status_code = 400
    error = requests.exceptions.HTTPError(response=mock_response)
    mock_post.return_value.raise_for_status.side_effect = error

    with pytest.raises(SystemExit) as exc_info:
        Messenger.send_telegram_message("hello")

    assert exc_info.value.code == 1
    captured = capsys.readouterr().out
    assert "Failed to send message" in captured
    assert "HTTP 400" in captured


@patch.dict("os.environ", {"TELEGRAM_TOKEN": "test-token", "TELEGRAM_CHAT_ID": "12345"})
@patch("Messenger.requests.post")
def test_send_telegram_message_connection_error(mock_post, capsys):
    mock_post.side_effect = requests.exceptions.ConnectionError("network down")

    with pytest.raises(SystemExit) as exc_info:
        Messenger.send_telegram_message("hello")

    assert exc_info.value.code == 1
    captured = capsys.readouterr().out
    assert "Failed to send message" in captured
    assert "HTTP" not in captured


def test_format_duration_hours_and_minutes():
    assert Messenger.format_duration(timedelta(hours=23, minutes=40)) == "23 hours and 40 minutes"


def test_format_duration_singular_units():
    assert Messenger.format_duration(timedelta(hours=1, minutes=1)) == "1 hour and 1 minute"


def test_format_duration_exact_hours():
    assert Messenger.format_duration(timedelta(hours=24)) == "24 hours"


def test_format_duration_minutes_only():
    assert Messenger.format_duration(timedelta(minutes=45)) == "45 minutes"


def test_format_duration_under_one_minute():
    assert Messenger.format_duration(timedelta(seconds=30)) == "less than a minute"


def test_next_future_deadline_picks_earliest_upcoming():
    now = datetime(2026, 5, 20, 18, 50, tzinfo=timezone.utc)
    events = [
        {"deadline_time": "2026-05-19T18:30:00Z"},
        {"deadline_time": "2026-05-28T18:30:00Z"},
        {"deadline_time": "2026-05-21T18:30:00Z"},
        {"name": "blank"},
    ]

    result = Messenger.next_future_deadline(events, now)

    assert result == datetime(2026, 5, 21, 18, 30, tzinfo=timezone.utc)


def test_next_future_deadline_none_when_all_passed():
    now = datetime(2026, 6, 1, tzinfo=timezone.utc)
    events = [{"deadline_time": "2026-05-21T18:30:00Z"}]

    assert Messenger.next_future_deadline(events, now) is None


def test_build_reminder_message_uses_time_until_deadline():
    deadline = datetime(2026, 5, 21, 18, 30, tzinfo=timezone.utc)
    now = datetime(2026, 5, 20, 18, 50, tzinfo=timezone.utc)

    message = Messenger.build_reminder_message(deadline, now)

    assert "You have 23 hours and 40 minutes left" in message
    assert str(Messenger.REMINDER_LEAD_HOURS) not in message


@patch.dict("os.environ", {"TELEGRAM_TOKEN": "test-token", "TELEGRAM_CHAT_ID": "12345"})
@patch("Messenger.send_telegram_message")
@patch("Messenger.requests.get")
def test_main_sends_time_remaining_until_next_deadline(mock_get, mock_send):
    now = datetime(2026, 5, 20, 18, 50, tzinfo=timezone.utc)
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "events": [
            {"deadline_time": "2026-05-19T18:30:00Z"},
            {"deadline_time": "2026-05-21T18:30:00Z"},
        ]
    }
    mock_get.return_value = mock_response

    with patch("Messenger.datetime") as mock_datetime:
        mock_datetime.now.return_value = now
        mock_datetime.strptime = datetime.strptime
        Messenger.main()

    mock_get.assert_called_once_with(Messenger.FPL_BOOTSTRAP_URL, timeout=Messenger.REQUEST_TIMEOUT)
    text = mock_send.call_args[0][0]
    assert "23 hours and 40 minutes" in text


@patch("Messenger.requests.get")
def test_main_no_upcoming_deadline(mock_get, capsys):
    now = datetime(2026, 6, 1, tzinfo=timezone.utc)
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "events": [{"deadline_time": "2026-05-21T18:30:00Z"}]
    }
    mock_get.return_value = mock_response

    with patch("Messenger.datetime") as mock_datetime:
        mock_datetime.now.return_value = now
        mock_datetime.strptime = datetime.strptime
        with pytest.raises(SystemExit) as exc_info:
            Messenger.main()

    assert exc_info.value.code == 1
    assert "No upcoming deadline found." in capsys.readouterr().out


@patch("Messenger.requests.get", side_effect=requests.exceptions.Timeout)
def test_main_fetch_failure(mock_get, capsys):
    with pytest.raises(SystemExit) as exc_info:
        Messenger.main()

    assert exc_info.value.code == 1
    assert "Failed to fetch FPL deadlines" in capsys.readouterr().out
