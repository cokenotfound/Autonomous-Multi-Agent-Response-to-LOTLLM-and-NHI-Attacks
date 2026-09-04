"""
preprocessing/windows/fixed_time_windows.py

Groups events into fixed time intervals (e.g. 5 minute buckets).
"""
import polars as pl
from config import TIME_WINDOW_SIZE

class FixedTimeWindowBuilder:
    def __init__(self, window_seconds: int = TIME_WINDOW_SIZE):
        self.window_seconds = window_seconds

    def build_windows(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Groups events by fixed time intervals.
        Returns a DataFrame where each row represents a time window, 
        and the events are aggregated into lists.
        """
        if df.is_empty():
            return df
            
        # Ensure data is sorted by timestamp
        df = df.sort("timestamp")
        
        # We can also group by correlation_key if we want windows per host/identity.
        # But generally fixed time windows are global or per-host.
        # Let's group by correlation_key AND timestamp window.
        
        window_expr = f"{self.window_seconds}s"
        
        # Using group_by_dynamic for time-based windowing
        windowed_df = df.group_by_dynamic(
            "timestamp", 
            every=window_expr,
            group_by="correlation_key"
        ).agg(
            pl.col("event_id"),
            pl.col("source_type"),
            pl.col("event_type"),
            pl.len().alias("event_count")
        )
        
        return windowed_df
