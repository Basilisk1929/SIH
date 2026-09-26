"""Temporal distribution, time-of-day, and day-of-week analysis for geospatial events."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional
import pandas as pd


@dataclass
class TemporalAnalysisResult:
    total_events: int
    hourly_distribution: Dict[int, int]
    peak_hour: int
    trough_hour: int
    time_of_day_breakdown: Dict[str, int]
    nocturnal_count: int
    nocturnal_ratio: float
    is_nocturnal_burst: bool
    day_of_week_distribution: Dict[str, int]
    peak_day: str
    weekend_count: int
    weekend_ratio: float
    is_weekend_surge: bool


DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class TemporalAnalyzer:
    """Analyzes diachronic patterns (time-of-day, day-of-week) for spatial events."""

    @classmethod
    def analyze_timestamps(
        cls,
        timestamps: pd.Series,
        nocturnal_threshold: float = 0.30,
        weekend_surge_threshold: float = 0.40,
    ) -> TemporalAnalysisResult:
        """Perform comprehensive time-of-day and day-of-week analysis on a Series of timestamps."""
        ts_clean = pd.to_datetime(timestamps.dropna(), utc=True)
        total_events = len(ts_clean)

        if total_events == 0:
            return TemporalAnalysisResult(
                total_events=0,
                hourly_distribution={h: 0 for h in range(24)},
                peak_hour=0,
                trough_hour=0,
                time_of_day_breakdown={"NOCTURNAL": 0, "MORNING": 0, "BUSINESS_HOURS": 0, "EVENING": 0},
                nocturnal_count=0,
                nocturnal_ratio=0.0,
                is_nocturnal_burst=False,
                day_of_week_distribution={d: 0 for d in DAYS_OF_WEEK},
                peak_day="Monday",
                weekend_count=0,
                weekend_ratio=0.0,
                is_weekend_surge=False,
            )

        # Hours (0-23)
        hours = ts_clean.dt.hour
        hour_counts = hours.value_counts().to_dict()
        hourly_dist = {h: int(hour_counts.get(h, 0)) for h in range(24)}
        peak_hour = max(hourly_dist, key=hourly_dist.get)
        trough_hour = min(hourly_dist, key=hourly_dist.get)

        # Time-of-day categorization
        # Nocturnal: 23:00 - 04:59 (hours 23, 0, 1, 2, 3, 4)
        # Morning: 05:00 - 10:59 (hours 5, 6, 7, 8, 9, 10)
        # Business: 11:00 - 16:59 (hours 11, 12, 13, 14, 15, 16)
        # Evening: 17:00 - 22:59 (hours 17, 18, 19, 20, 21, 22)
        nocturnal_hours = {23, 0, 1, 2, 3, 4}
        morning_hours = {5, 6, 7, 8, 9, 10}
        business_hours = {11, 12, 13, 14, 15, 16}
        evening_hours = {17, 18, 19, 20, 21, 22}

        nocturnal_count = sum(hourly_dist[h] for h in nocturnal_hours)
        morning_count = sum(hourly_dist[h] for h in morning_hours)
        business_count = sum(hourly_dist[h] for h in business_hours)
        evening_count = sum(hourly_dist[h] for h in evening_hours)

        nocturnal_ratio = round(nocturnal_count / total_events, 4)
        is_nocturnal_burst = nocturnal_ratio >= nocturnal_threshold and nocturnal_count >= 5

        # Days of week (0=Monday, 6=Sunday)
        dows = ts_clean.dt.dayofweek
        dow_counts = dows.value_counts().to_dict()
        dow_dist = {DAYS_OF_WEEK[i]: int(dow_counts.get(i, 0)) for i in range(7)}
        peak_day = max(dow_dist, key=dow_dist.get)

        weekend_count = dow_dist["Saturday"] + dow_dist["Sunday"]
        weekend_ratio = round(weekend_count / total_events, 4)
        is_weekend_surge = weekend_ratio >= weekend_surge_threshold and weekend_count >= 5

        return TemporalAnalysisResult(
            total_events=total_events,
            hourly_distribution=hourly_dist,
            peak_hour=int(peak_hour),
            trough_hour=int(trough_hour),
            time_of_day_breakdown={
                "NOCTURNAL": nocturnal_count,
                "MORNING": morning_count,
                "BUSINESS_HOURS": business_count,
                "EVENING": evening_count,
            },
            nocturnal_count=nocturnal_count,
            nocturnal_ratio=nocturnal_ratio,
            is_nocturnal_burst=bool(is_nocturnal_burst),
            day_of_week_distribution=dow_dist,
            peak_day=str(peak_day),
            weekend_count=weekend_count,
            weekend_ratio=weekend_ratio,
            is_weekend_surge=bool(is_weekend_surge),
        )

    @classmethod
    def analyze_dataframe(
        cls,
        df: pd.DataFrame,
        timestamp_col: str = "timestamp",
    ) -> Dict[str, Any]:
        """Analyze temporal columns in a DataFrame."""
        if df.empty or timestamp_col not in df.columns:
            return asdict(cls.analyze_timestamps(pd.Series([])))
        return asdict(cls.analyze_timestamps(df[timestamp_col]))
