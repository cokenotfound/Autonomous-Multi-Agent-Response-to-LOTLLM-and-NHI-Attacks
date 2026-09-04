"""
preprocessing/windows/session_windows.py

Groups events into sessions based on continuous activity.
A session breaks if the inactivity gap exceeds the threshold.
Maintains state across batches.
"""
import polars as pl
from datetime import datetime, timezone
from config import SESSION_GAP_THRESHOLD
import uuid

class SessionWindowBuilder:
    def __init__(self, gap_seconds: int = SESSION_GAP_THRESHOLD):
        self.gap_seconds = gap_seconds
        # State tracker: correlation_key -> (last_timestamp: datetime, current_session_id: str)
        self.state = {}

    def assign_sessions(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Appends a 'session_id' column to the DataFrame based on inactivity gaps.
        Handles state across batches by tracking the last timestamp per correlation_key.
        """
        if df.is_empty():
            return df

        df = df.sort("timestamp")
        
        session_ids = []
        
        # Iterate to handle cross-batch state accurately
        for row in df.iter_rows(named=True):
            key = row["correlation_key"]
            ts = row["timestamp"]
            
            # Default state if unseen: epoch zero
            last_ts, current_sess = self.state.get(key, (datetime.min.replace(tzinfo=timezone.utc), None))
            
            # If gap > threshold, start a new session
            # Note: ts and last_ts must both be timezone-aware or naive. Polars returns naive datetimes usually.
            # Convert both to timestamp (float) for safe math
            ts_float = ts.timestamp()
            last_ts_float = last_ts.timestamp()
            
            if (ts_float - last_ts_float) > self.gap_seconds or current_sess is None:
                current_sess = f"{key}-sess-{uuid.uuid4().hex[:8]}"
                
            session_ids.append(current_sess)
            self.state[key] = (ts, current_sess)

        # Add session_id column
        return df.with_columns(pl.Series("session_id", session_ids))
        
    def build_windows(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Assigns sessions and then aggregates the DataFrame by session_id.
        """
        if df.is_empty():
            return df
            
        df_with_sessions = self.assign_sessions(df)
        
        # Group by session_id to create the windowed representation
        session_windows = df_with_sessions.group_by("session_id", maintain_order=True).agg(
            pl.col("correlation_key").first(),
            pl.col("timestamp").min().alias("session_start"),
            pl.col("timestamp").max().alias("session_end"),
            pl.col("event_id"),
            pl.col("source_type"),
            pl.col("event_type"),
            pl.len().alias("event_count")
        )
        
        return session_windows
