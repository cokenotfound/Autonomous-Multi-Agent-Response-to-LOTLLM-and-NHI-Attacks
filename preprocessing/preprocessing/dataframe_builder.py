from typing import Iterable
import polars as pl

from .models import NormalizedEvent

def events_to_dataframe(events: Iterable[NormalizedEvent]) -> pl.DataFrame:
    rows = [event.to_dict() for event in events]
    if not rows:
        return pl.DataFrame()
    return pl.DataFrame(rows).sort("timestamp")
