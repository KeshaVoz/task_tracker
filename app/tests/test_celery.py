import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timezone
from app.tasks.email import send_daily_report, process_user_report, send_welcome_email


pytestmark = pytest.mark.anyio


async def test_send_daily_report_chunks(monkeypatch):
    mock_user_ids = [101, 102, 103]
    mock_find_all = MagicMock(side_effect=[mock_user_ids, []])
    monkeypatch.setattr("app.tasks.email.UserDAO.find_all_ids_chunk", mock_find_all)
    
    mock_delay = MagicMock()
    monkeypatch.setattr("app.tasks.email.process_user_report.delay", mock_delay)
    
    send_daily_report()
    
    mock_find_all.assert_has_calls([
        call(limit=500, offset=0),
        call(limit=500, offset=500)
    ])
    
    assert mock_delay.call_count == 3
    mock_delay.assert_has_calls([call(101), call(102), call(103)])


async def test_process_user_report_safeguard(monkeypatch):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "empty@example.com"
    monkeypatch.setattr("app.tasks.email.UserDAO.find_one_or_none_sync", MagicMock(return_value=mock_user))
    
    mock_analytics = MagicMock()
    mock_analytics.total_pending = 0
    mock_analytics.completed_count = 0
    monkeypatch.setattr("app.tasks.email.TaskService.get_user_daily_analytics", MagicMock(return_value=mock_analytics))
    
    from app.tasks.email import kafka_producer
    kafka_producer.send = MagicMock()
    
    process_user_report(user_id=1)
    
    kafka_producer.send.assert_not_called()


async def test_process_user_report_success(monkeypatch):
    mock_user = MagicMock()
    mock_user.id = 42
    mock_user.email = "active@example.com"
    monkeypatch.setattr("app.tasks.email.UserDAO.find_one_or_none_sync", MagicMock(return_value=mock_user))
    
    mock_analytics = MagicMock()
    mock_analytics.total_pending = 2
    mock_analytics.pending_titles = ["Task 1", "Task 2"]
    mock_analytics.completed_count = 1
    mock_analytics.completed_titles = ["Done Task"]
    monkeypatch.setattr("app.tasks.email.TaskService.get_user_daily_analytics", MagicMock(return_value=mock_analytics))
    
    from app.tasks.email import kafka_producer
    kafka_producer.send = MagicMock()
    kafka_producer.flush = MagicMock()
    
    test_now = datetime(2026, 7, 4, 12, 0, 0, tzinfo=timezone.utc)
    
    with patch("app.tasks.email.current_task") as mock_current_task:
        mock_current_task.request.time_start = test_now
        
        process_user_report(user_id=42)
    
    kafka_producer.send.assert_called_once()
    
    called_args, called_kwargs = kafka_producer.send.call_args

    assert called_args[0] == "summary_requests"

    assert called_kwargs["headers"] == [("correlation_id", b"report-42-2026-07-04")]

    payload = called_kwargs["value"]
    assert payload["user_id"] == 42
    assert payload["user_email"] == "active@example.com"
    assert payload["total_pending"] == 2
    assert payload["completed_count"] == 1
    assert payload["pending_titles"] == ["Task 1", "Task 2"]
    
    kafka_producer.flush.assert_called_once()

async def test_send_welcome_email_success(monkeypatch):
    mock_send = MagicMock(return_value=None)
    monkeypatch.setattr("app.tasks.email.EmailService.send_welcome_email", mock_send)

    result = send_welcome_email("newuser@example.com")

    assert result is True
    mock_send.assert_called_once_with(user_email="newuser@example.com")


async def test_send_welcome_email_failure(monkeypatch):
    mock_send = MagicMock(side_effect=Exception("SMTP Connection Timeout"))
    monkeypatch.setattr("app.tasks.email.EmailService.send_welcome_email", mock_send)

    result = send_welcome_email("fail@example.com")

    assert result is False
    mock_send.assert_called_once()


async def test_process_user_report_retry_on_kafka_error(monkeypatch):
    mock_user = MagicMock(id=77, email="retry@example.com")
    monkeypatch.setattr("app.tasks.email.UserDAO.find_one_or_none_sync", MagicMock(return_value=mock_user))

    mock_analytics = MagicMock(total_pending=5, completed_count=0)
    monkeypatch.setattr("app.tasks.email.TaskService.get_user_daily_analytics", MagicMock(return_value=mock_analytics))

    from app.tasks.email import kafka_producer
    kafka_producer.send = MagicMock(side_effect=Exception("Kafka broker disconnected"))

    with pytest.raises(Exception) as exc_info:
        process_user_report(user_id=77)
        
    assert "Kafka broker disconnected" in str(exc_info.value)

