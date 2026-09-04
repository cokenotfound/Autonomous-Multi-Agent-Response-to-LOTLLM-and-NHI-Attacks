"""
preprocessing/dataframe/dataframe_builder.py

Converts standard event dictionaries into Polars DataFrames.
"""
import polars as pl
from typing import List, Dict, Any

class DataFrameBuilder:
    def build(self, events: List[Dict[str, Any]]) -> pl.DataFrame:
        """
        Converts a list of common_event dictionaries to a Polars DataFrame.
        Enforces a consistent schema.
        """
        if not events:
            return pl.DataFrame()

        # Build schema using the first event's keys, ensuring consistent types
        # Polars can infer most, but we explicitly cast timestamp to Datetime
        df = pl.DataFrame(events)
        
        # Parse timestamps into datetime objects before building the DataFrame
        from dateutil.parser import parse as parse_date
        for e in events:
            if "timestamp" in e and isinstance(e["timestamp"], str):
                try:
                    e["timestamp"] = parse_date(e["timestamp"])
                except Exception:
                    pass
        
        df = pl.DataFrame(events)
            
        return df

