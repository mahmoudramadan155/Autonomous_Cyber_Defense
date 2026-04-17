from sqlalchemy.ext.asyncio import AsyncSession
from app.models.log import LogEvent as LogEventModel
from app.schemas.log import LogEventCreate

class LogCollectorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def collect_log(self, log_in: LogEventCreate) -> LogEventModel:
        """
        Collects a log event, normalizes it, and saves it to the database.
        """
        # Create the database model
        db_log = LogEventModel(**log_in.model_dump())
        self.db.add(db_log)
        await self.db.commit()
        await self.db.refresh(db_log)
        
        # Simulate pushing to Redis Stream (as per architecture diagram)
        await self._publish_to_streaming_engine({"id": db_log.id, **log_in.model_dump()})
        
        return db_log

    async def _publish_to_streaming_engine(self, payload: dict):
        from app.services.streaming import StreamingService
        await StreamingService.publish_log(payload)

    async def bulk_collect_logs(self, logs_in: list[LogEventCreate]) -> list[LogEventModel]:
        db_logs = [LogEventModel(**log.model_dump()) for log in logs_in]
        self.db.add_all(db_logs)
        await self.db.commit()
        for log, log_in in zip(db_logs, logs_in):
            await self.db.refresh(log)
            await self._publish_to_streaming_engine({"id": log.id, **log_in.model_dump()})
        return db_logs
