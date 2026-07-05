import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, AsyncMock, patch

from sqlalchemy.exc import IntegrityError

from app.schemas import SSummaryReportRequest, SClearCacheCommand
from app.services import summarizer, LLMSummarizer
from app.models import ProcessedRequest
from app.database import async_session_maker


pytestmark = pytest.mark.anyio


@pytest.fixture
def sample_request_data() -> SSummaryReportRequest:
    return SSummaryReportRequest(
        total_pending=2,
        pending_titles=["Fix bugs", "Write tests"],
        completed_count=1,
        completed_titles=["Deploy backend"],
        user_email="developer@test.com",
        target_date="2026-07-04",
        user_id=123
    )


async def test_build_prompt_security_tags(sample_request_data: SSummaryReportRequest) -> None:
    prompt = summarizer._build_prompt(sample_request_data)
    
    assert "<completed_tasks_data>" in prompt
    assert "- Deploy backend" in prompt
    assert "Remaining pending tasks count: 2" in prompt
    assert "The final response MUST be written in English language." in prompt


async def test_generate_summary_success_and_caching(
    sample_request_data: SSummaryReportRequest, 
    mock_gigachat_network_lock: AsyncMock
) -> None:
    correlation_id = "rpc-unique-key-111"
    
    mock_ai_response = MagicMock()
    mock_ai_response.text = "Super beautiful markdown text from mocked AI."
    mock_gigachat_network_lock.return_value = mock_ai_response

    result = await summarizer.generate_summary(sample_request_data, correlation_id)
    
    assert result == "Super beautiful markdown text from mocked AI."
    mock_gigachat_network_lock.assert_awaited_once()

    async with async_session_maker() as session:
        db_entry = await session.get(ProcessedRequest, correlation_id)
        assert db_entry is not None
        assert db_entry.report_text == "Super beautiful markdown text from mocked AI."


async def test_generate_summary_idempotency_hit(
    sample_request_data: SSummaryReportRequest, 
    mock_gigachat_network_lock: AsyncMock
) -> None:
    correlation_id = "rpc-cached-key-222"
    
    async with async_session_maker() as session:
        session.add(ProcessedRequest(correlation_id=correlation_id, report_text="Old cached report data."))
        await session.commit()

    result = await summarizer.generate_summary(sample_request_data, correlation_id)
    
    assert result == "Old cached report data."
    mock_gigachat_network_lock.assert_not_called()


async def test_generate_summary_race_condition_handling(
    sample_request_data: SSummaryReportRequest, 
    mock_gigachat_network_lock: AsyncMock
) -> None:
    correlation_id = "rpc-race-condition-333"
    
    mock_ai_response = MagicMock()
    mock_ai_response.text = "My fresh response text."
    mock_gigachat_network_lock.return_value = mock_ai_response

    async with async_session_maker() as session:
        session.add(ProcessedRequest(correlation_id=correlation_id, report_text="Winner competitor text."))
        await session.commit()

    with patch("sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=IntegrityError(None, None, None)):
        result = await summarizer.generate_summary(sample_request_data, correlation_id)
        
        assert result == "Winner competitor text."


async def test_generate_summary_gigachat_exception_masking(
    sample_request_data: SSummaryReportRequest, 
    mock_gigachat_network_lock: AsyncMock
) -> None:
    class GigaChatAPIError(Exception):
        pass
        
    mock_gigachat_network_lock.side_effect = GigaChatAPIError("Secret Token XYZ Expired!")

    result = await summarizer.generate_summary(sample_request_data, "rpc-fail-key")
    
    assert "Failed to generate AI report" in result


async def test_clear_old_cache_logic() -> None:
    now = datetime.now(timezone.utc)
    
    async with async_session_maker() as session:
        session.add(ProcessedRequest(correlation_id="fresh-1", report_text="text", created_at=now))
        session.add(ProcessedRequest(correlation_id="old-2", report_text="text", created_at=now - timedelta(days=35)))
        await session.commit()

    command = SClearCacheCommand(retention_days=30)
    deleted_count = await LLMSummarizer.clear_old_cache(command)
    
    assert deleted_count == 1
