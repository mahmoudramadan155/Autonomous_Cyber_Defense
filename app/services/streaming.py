import json
import logging
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)

# Shared Redis client
redis_client = redis.from_url(settings.redis_url, decode_responses=True)

class StreamingService:
    @staticmethod
    async def publish_log(log_dict: dict):
        """Publish a normalized log to the raw logs stream."""
        try:
            # Redis streams expect string key-value pairs
            payload = {k: str(v) if v is not None else "" for k, v in log_dict.items()}
            await redis_client.xadd("logs_raw", payload)
            logger.debug(f"Published log to logs_raw stream: log_id={log_dict.get('id')}")
        except Exception as e:
            logger.error(f"Failed to publish to stream logs_raw: {e}")

    @staticmethod
    async def publish_alert(alert_dict: dict):
        """Publish a detected alert to the alerts stream."""
        try:
            payload = {k: str(v) if v is not None else "" for k, v in alert_dict.items()}
            await redis_client.xadd("alerts", payload)
            logger.debug(f"Published alert to alerts stream: alert_id={alert_dict.get('id')}")
        except Exception as e:
            logger.error(f"Failed to publish alert to stream alerts: {e}")

    @staticmethod
    async def publish_incident(incident_dict: dict):
        """Publish a correlated incident to the incidents stream."""
        try:
            payload = {k: str(v) if v is not None else "" for k, v in incident_dict.items()}
            await redis_client.xadd("incidents", payload)
            logger.debug(f"Published incident to incidents stream: incident_id={incident_dict.get('id')}")
        except Exception as e:
            logger.error(f"Failed to publish incident to stream incidents: {e}")
