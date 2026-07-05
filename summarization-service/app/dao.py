import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from app.database import async_session_maker
from app.models import ProcessedRequest


logger = logging.getLogger("summarization-service.dao")


class ProcessedRequestDAO:
    @staticmethod
    async def find_by_correlation_id(correlation_id: str) -> Optional[str]:
        async with async_session_maker() as session:
            cached = await session.get(ProcessedRequest, correlation_id)
            return cached.report_text if cached else None

    @staticmethod
    async def save_to_cache(correlation_id: str, report_text: str) -> str:
        async with async_session_maker() as session:
            try:
                new_entry = ProcessedRequest(correlation_id=correlation_id, report_text=report_text)
                session.add(new_entry)
                await session.commit()
                return report_text
            except IntegrityError:
                await session.rollback()
                logger.warning("Race condition caught for correlation_id: %s. Reading alternative cache.", correlation_id)
                
                async with async_session_maker() as clean_session:
                    cached_entry = await clean_session.get(
                        ProcessedRequest, 
                        correlation_id, 
                        execution_options={"read_only": True}
                    )
                    return cached_entry.report_text if cached_entry else report_text

    @staticmethod
    async def delete_old_cache(days: int) -> int:
        limit_time = datetime.now(timezone.utc) - timedelta(days=days)
        async with async_session_maker() as session:
            stmt = delete(ProcessedRequest).where(ProcessedRequest.created_at < limit_time)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount
