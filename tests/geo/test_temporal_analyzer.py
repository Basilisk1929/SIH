"""Unit tests for TemporalAnalyzer."""

import pandas as pd
import pytest

from geo.temporal.temporal_analyzer import TemporalAnalyzer


def test_temporal_analysis_hourly_and_dow():
    # 20 transactions spread across days and hours
    # 10 nocturnal (2am) and 10 daytime (2pm)
    timestamps = [
        "2024-08-15T02:00:00Z", "2024-08-15T02:15:00Z", "2024-08-15T02:30:00Z",
        "2024-08-16T02:00:00Z", "2024-08-16T02:45:00Z", "2024-08-17T02:00:00Z",
        "2024-08-17T02:10:00Z", "2024-08-18T02:20:00Z", "2024-08-18T02:30:00Z",
        "2024-08-18T02:40:00Z",
        "2024-08-15T14:00:00Z", "2024-08-15T14:15:00Z", "2024-08-15T14:30:00Z",
        "2024-08-16T14:00:00Z", "2024-08-16T14:45:00Z", "2024-08-17T14:00:00Z",
        "2024-08-17T14:10:00Z", "2024-08-18T14:20:00Z", "2024-08-18T14:30:00Z",
        "2024-08-18T14:40:00Z",
    ]
    series = pd.Series(timestamps)

    result = TemporalAnalyzer.analyze_timestamps(series)
    assert result.total_events == 20
    assert result.peak_hour in [2, 14]
    assert result.nocturnal_count == 10
    assert result.nocturnal_ratio == 0.50
    assert result.is_nocturnal_burst is True


def test_empty_temporal_analysis():
    result = TemporalAnalyzer.analyze_timestamps(pd.Series([]))
    assert result.total_events == 0
    assert result.nocturnal_count == 0
    assert result.is_nocturnal_burst is False
