"""
preprocessing/redis_reader.py

Reads raw events in batches from multiple Redis streams.
Responsibilities:
- Connect to Redis
- Read multiple streams using XREAD
- Preserve stream name, message ID, and envelope
- Support stateful block reading or batch polling
"""

import logging
from typing import Dict, List, Tuple, Any

import redis

from config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_STREAMS, BATCH_SIZE

logger = logging.getLogger(__name__)

class RedisBatchReader:
    def __init__(self, host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, streams=None, batch_size=BATCH_SIZE):
        self.host = host
        self.port = port
        self.db = db
        self.streams = streams or REDIS_STREAMS
        self.batch_size = batch_size
        
        # Track the last read ID for each stream (start at "0-0" for beginning, or "$" for new)
        # Using "0-0" since we want to process the generated test data.
        self.stream_state = {stream: "0-0" for stream in self.streams}
        self.client = None

    def connect(self) -> bool:
        """Connects to Redis. Returns True if successful, False otherwise."""
        try:
            # Native Redis 5.0 on Windows requires RESP2
            self.client = redis.Redis(
                host=self.host, 
                port=self.port, 
                db=self.db, 
                decode_responses=True,
                protocol=2
            )
            self.client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
            return True
        except redis.RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.client = None
            return False

    def read_batch(self, block_ms: int = 1000) -> List[Tuple[str, str, Dict[str, Any]]]:
        """
        Reads a batch of events from all configured streams.
        Returns a list of tuples: (stream_name, message_id, raw_envelope)
        """
        if not self.client:
            raise RuntimeError("Redis client not connected. Call connect() first.")

        batch_results = []
        try:
            # xread returns a list of tuples: [(stream_name, [(msg_id, payload), ...]), ...]
            results = self.client.xread(
                streams=self.stream_state,
                count=self.batch_size,
                block=block_ms
            )

            if not results:
                return []

            for stream_name, messages in results:
                for msg_id, payload in messages:
                    # Append exactly as requested: stream, id, envelope(payload)
                    batch_results.append((stream_name, msg_id, payload))
                    # Update state to the last read message ID for this stream
                    self.stream_state[stream_name] = msg_id

        except redis.RedisError as e:
            logger.error(f"Error reading from Redis streams: {e}")
            
        return batch_results
