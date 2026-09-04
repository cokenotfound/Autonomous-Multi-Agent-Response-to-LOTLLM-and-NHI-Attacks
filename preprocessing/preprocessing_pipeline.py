"""
preprocessing/preprocessing_pipeline.py

END-TO-END MODULE 2 ORCHESTRATION PIPELINE
"""
import logging
import polars as pl
from typing import Dict, Any, Tuple

from redis_reader import RedisBatchReader
from source_router import SourceRouter
from validation.event_validator import EventValidator
from cleaning.event_cleaner import EventCleaner
from normalization.timestamp_normalizer import TimestampNormalizer
from normalization.field_normalizer import FieldNormalizer
from correlation.event_correlator import EventCorrelator
from dataframe.dataframe_builder import DataFrameBuilder
from windows.fixed_time_windows import FixedTimeWindowBuilder
from windows.session_windows import SessionWindowBuilder

logger = logging.getLogger(__name__)

class PreprocessingPipeline:
    def __init__(self):
        self.reader = RedisBatchReader()
        self.router = SourceRouter()
        self.validator = EventValidator()
        self.cleaner = EventCleaner()
        self.ts_normalizer = TimestampNormalizer()
        self.field_normalizer = FieldNormalizer()
        self.correlator = EventCorrelator()
        
        self.df_builder = DataFrameBuilder()
        self.fixed_window_builder = FixedTimeWindowBuilder()
        self.session_window_builder = SessionWindowBuilder()
        
        # Stats tracking for the run
        self.stats = {
            "read": 0,
            "routed": 0,
            "valid": 0,
            "invalid": 0,
            "cleaned": 0,
            "normalized": 0,
            "dropped_duplicates": 0,
        }

    def start(self) -> bool:
        return self.reader.connect()

    def process_batch(self) -> Tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
        """
        Runs one full batch through the pipeline.
        Returns:
            (raw_events_df, fixed_windows_df, session_windows_df)
        """
        # 1. Redis Batch Reader
        raw_events = self.reader.read_batch(block_ms=10)
        self.stats["read"] += len(raw_events)
        
        if not raw_events:
            return pl.DataFrame(), pl.DataFrame(), pl.DataFrame()

        processed_events = []
        
        for stream_name, msg_id, envelope in raw_events:
            try:
                # 2 & 3. Source Routing & Parsing
                routed = self.router.route_and_parse(envelope)
                self.stats["routed"] += 1
                
                # 4. Validation (includes duplicate handling)
                is_valid, reason, validated = self.validator.validate(envelope, routed["parsed"])
                if is_valid:
                    self.stats["valid"] += 1
                else:
                    self.stats["invalid"] += 1
                    if "Duplicate" in reason:
                        self.stats["dropped_duplicates"] += 1
                    # Depending on policy, it might be dropped here. If returned False, we skip.
                    if validated == {}:
                        continue
                
                # 5. Cleaning
                cleaned = self.cleaner.clean(validated)
                self.stats["cleaned"] += 1
                
                # 6. Timestamp Normalization
                ts_normalized = self.ts_normalizer.normalize(cleaned)
                
                # 7. Field Normalization + Common Event Rep
                fully_normalized = self.field_normalizer.normalize(ts_normalized)
                self.stats["normalized"] += 1
                
                processed_events.append(fully_normalized)
                
            except Exception as e:
                logger.error(f"Pipeline error processing event {msg_id}: {e}")
                self.stats["invalid"] += 1

        # 8. Identity/Host Correlation + Chronological Ordering
        # This strips out the wrapping metadata and returns only the sorted 'common_event' dictionaries
        correlated_events = self.correlator.process_batch(processed_events)
        
        # 9. Polars DataFrame
        events_df = self.df_builder.build(correlated_events)

        # 10. Fixed Windows
        fixed_windows_df = self.fixed_window_builder.build_windows(events_df)

        # 11. Session Windows
        session_windows_df = self.session_window_builder.build_windows(events_df)

        # 12. Persist DataFrames
        from pathlib import Path

        output_dir = Path(__file__).resolve().parent / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        events_df.write_parquet(output_dir / "normalized_events.parquet")
        fixed_windows_df.write_parquet(output_dir / "fixed_windows.parquet")
        session_windows_df.write_parquet(output_dir / "session_windows.parquet")

        logger.info(f"Saved normalized events: {len(events_df)} rows")
        logger.info(f"Saved fixed windows: {len(fixed_windows_df)} windows")
        logger.info(f"Saved session windows: {len(session_windows_df)} sessions")

        return events_df, fixed_windows_df, session_windows_df

if __name__ == "__main__":
    import sys
    
    # Configure simple logging for stdout
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    
    pipeline = PreprocessingPipeline()
    if not pipeline.start():
        sys.exit(1)
        
    print("=" * 60)
    print("RUNNING END-TO-END PIPELINE ON STEP 0 DEV DATA")
    print("=" * 60)
    
    events_df, fixed_df, session_df = pipeline.process_batch()
    
    print("\n[PIPELINE STATS]")
    for k, v in pipeline.stats.items():
        print(f"  {k:<20}: {v}")
        
    print(f"\n[EVENTS DATAFRAME] Rows: {len(events_df)}")
    if not events_df.is_empty():
        # Hide raw_payload for cleaner output
        print(events_df.drop("raw_payload").head())
        
    print(f"\n[FIXED WINDOWS DATAFRAME] Windows created: {len(fixed_df)}")
    if not fixed_df.is_empty():
        print(fixed_df.head())
        
    print(f"\n[SESSION WINDOWS DATAFRAME] Sessions identified: {len(session_df)}")
    if not session_df.is_empty():
        print(session_df.head())
        
    print("=" * 60)
