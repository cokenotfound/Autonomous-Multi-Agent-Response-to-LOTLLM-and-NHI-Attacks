from typing import Dict, List, Any
import redis

from .config import STREAMS, REDIS_CONFIG

class RedisStreamReader:
    """Batch reader for Module 1's six Redis telemetry streams."""

    def __init__(self, url: str = REDIS_CONFIG.url):
        self.client = redis.Redis.from_url(url, decode_responses=True)

    def read_batch(self, stream: str, count: int = REDIS_CONFIG.batch_size, last_id: str = "0-0"):
        """
        Read one batch using XREAD.

        The caller should retain returned Redis message IDs and use the last
        processed ID on the next call in a continuous implementation.
        """
        return self.client.xread({stream: last_id}, count=count, block=1000)

    def read_all_once(self, count: int = REDIS_CONFIG.batch_size):
        result = {}
        for source, stream in STREAMS.items():
            result[source] = self.client.xread({stream: "0-0"}, count=count, block=1000)
        return result
