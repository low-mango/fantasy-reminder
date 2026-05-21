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
