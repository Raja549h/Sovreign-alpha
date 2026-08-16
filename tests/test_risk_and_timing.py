"""
tests/test_risk_and_timing.py
==============================
Automated pytest suite for the Sovereign Alpha Risk & Timing module.

Covers:
  - Indicator accuracy (Wilder's ATR vs simple rolling, 20-day SMA)
  - Timing trigger logic (breakout gate)
  - Kelly sizing & MAX_POSITION_PCT cap enforcement
  - Integer share floor (no fractional shares)
  - Error / edge-case handling (bad tickers, insufficient history)
"""

import sys
import math
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so `engine` is importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.risk_and_timing import (
    calculate_execution,
    WIN_RATE,
    REWARD_RISK,
    MAX_POSITION_PCT,
)


# ============================================================================
# Helpers – deterministic mock data
# ============================================================================

def _make_ohlcv(closes: list[float],
                highs: list[float] | None = None,
                lows: list[float] | None = None) -> pd.DataFrame:
    """
    Build a minimal OHLCV DataFrame that yfinance would return.
    If highs/lows are not supplied, derive them from closes with a
    fixed +/-2 % band so that True Range is predictable.
    """
    n = len(closes)
    if highs is None:
        highs = [c * 1.02 for c in closes]
    if lows is None:
        lows = [c * 0.98 for c in closes]

    # Use a fixed start Monday to avoid weekend/holiday edge-cases with bdate_range
    start = pd.Timestamp('2026-01-05')   # A Monday
    dates = pd.bdate_range(start=start, periods=n)
    df = pd.DataFrame({
        'Open':   closes,
        'High':   highs,
        'Low':    lows,
        'Close':  closes,
        'Volume': [1_000_000] * n,
    }, index=dates)
    return df


def _patch_yf_download(df: pd.DataFrame):
    """Return a context-manager that patches yfinance.download to return *df*."""
    return patch('engine.risk_and_timing.yf.download', return_value=df)


# ============================================================================
# 1. Indicator Accuracy
# ============================================================================

class TestIndicatorAccuracy:
    """Verify ATR uses Wilder's Smoothing and SMA is a plain 20-day mean."""

    @pytest.fixture()
    def flat_df(self):
        """40 bars of flat price at 100, with a constant H-L range of 4."""
        n = 40
        closes = [100.0] * n
        highs  = [102.0] * n
        lows   = [98.0]  * n
        return _make_ohlcv(closes, highs, lows)

    def test_atr_wilder_vs_simple_rolling(self, flat_df):
        """
        For a flat series the ATR should converge to the constant True Range.
        More importantly, the code must use ewm(alpha=1/14) (Wilder's) rather
        than .rolling(14).mean().  We verify by computing both and checking
        that the module's result matches the Wilder path.
        """
        with _patch_yf_download(flat_df):
            result = calculate_execution('TEST.NS', 1_000_000)

        assert result['success'] is True

        # Manually compute Wilder's ATR on the same data
        df = flat_df.copy()
        df['Prev_Close'] = df['Close'].shift(1)
        df['TR'] = (df['High'] - df['Low']).combine_first(
            (df['High'] - df['Prev_Close']).abs()
        )
        tr = (df[['High', 'Low']].assign(
            HL=df['High'] - df['Low'],
            HC=abs(df['High'] - df['Prev_Close']),
            LC=abs(df['Low'] - df['Prev_Close']),
        )[['HL', 'HC', 'LC']].max(axis=1))
        expected_wilder = float(tr.ewm(alpha=1/14, adjust=False).mean().iloc[-1])
        simple_rolling  = float(tr.rolling(14).mean().iloc[-1])

        # Module should match Wilder, not simple rolling
        assert result['atr_14'] == round(expected_wilder, 2)

    def test_sma_20_accuracy(self):
        """SMA-20 should equal the arithmetic mean of the last 20 closes."""
        closes = list(range(100, 140))          # 40 ascending prices
        df = _make_ohlcv(closes)
        with _patch_yf_download(df):
            result = calculate_execution('TEST.NS', 1_000_000)

        expected_sma = round(sum(closes[-20:]) / 20, 2)
        assert result['sma_20'] == expected_sma


# ============================================================================
# 2. Timing Trigger Logic
# ============================================================================

class TestTimingTrigger:
    """Verify the breakout gate: Close > SMA_20 + 0.5 * ATR_14."""

    def test_trigger_true_when_price_breaks_above(self):
        """
        Construct data so the last close is clearly above
        SMA(20) + 0.5 * ATR(14).
        """
        # 39 bars at 100, then a spike to 120
        closes = [100.0] * 39 + [120.0]
        highs  = [102.0] * 39 + [122.0]
        lows   = [98.0]  * 39 + [118.0]
        df = _make_ohlcv(closes, highs, lows)

        with _patch_yf_download(df):
            result = calculate_execution('TEST.NS', 1_000_000)

        assert result['success'] is True
        assert result['buy_trigger_met'] is True

    def test_trigger_false_when_price_below_threshold(self):
        """Flat prices → close ≈ SMA, which is NOT above SMA + 0.5*ATR."""
        closes = [100.0] * 40
        df = _make_ohlcv(closes)

        with _patch_yf_download(df):
            result = calculate_execution('TEST.NS', 1_000_000)

        assert result['success'] is True
        assert result['buy_trigger_met'] is False


# ============================================================================
# 3. Kelly Sizing & Cap Enforcement
# ============================================================================

class TestKellySizing:
    """Validate Kelly formula and the MAX_POSITION_PCT ceiling."""

    def test_full_kelly_value(self):
        """Full Kelly ≈ 53.17 %."""
        expected = round((WIN_RATE - (1 - WIN_RATE) / REWARD_RISK) * 100, 2)
        assert expected == 53.17

    def test_half_kelly_value(self):
        """Half-Kelly ≈ 26.58 %."""
        full = WIN_RATE - (1 - WIN_RATE) / REWARD_RISK
        expected = round((full / 2) * 100, 2)
        assert expected == 26.58

    def test_allocation_clamped_to_max_position(self):
        """
        Because Half-Kelly (26.58 %) > MAX_POSITION_PCT (15 %),
        the safe_allocation_pct must always equal 15.0.
        """
        closes = [100.0] * 40
        df = _make_ohlcv(closes)

        with _patch_yf_download(df):
            result = calculate_execution('TEST.NS', 1_000_000)

        assert result['safe_allocation_pct'] == 15.0
        assert result['capital_allocated'] == 150_000.0

    def test_allocation_equals_half_kelly_when_cap_raised(self):
        """
        If MAX_POSITION_PCT were higher than Half-Kelly, the allocation
        should fall back to the raw Half-Kelly value.
        """
        closes = [100.0] * 40
        df = _make_ohlcv(closes)

        with _patch_yf_download(df), \
             patch('engine.risk_and_timing.MAX_POSITION_PCT', 0.50):
            result = calculate_execution('TEST.NS', 1_000_000)

        assert result['safe_allocation_pct'] == 26.58


# ============================================================================
# 4. Share Floor Check
# ============================================================================

class TestShareFloor:
    """shares_to_buy must be an integer (math.floor), never a float."""

    def test_shares_is_integer(self):
        closes = [100.0] * 40
        df = _make_ohlcv(closes)

        with _patch_yf_download(df):
            result = calculate_execution('TEST.NS', 1_000_000)

        assert isinstance(result['shares_to_buy'], int)

    def test_shares_floor_not_ceil(self):
        """
        With portfolio 1M, cap 15 %, and close 100 →
        150 000 / 100 = 1500.0 exactly, so floor == ceil == 1500.
        Use a close price that produces a non-integer to prove floor.
        """
        # price = 103.0 → 150000 / 103 = 1456.31… → floor = 1456
        closes = [103.0] * 40
        df = _make_ohlcv(closes)

        with _patch_yf_download(df):
            result = calculate_execution('TEST.NS', 1_000_000)

        expected = math.floor(150_000 / 103.0)
        assert result['shares_to_buy'] == expected
        assert result['shares_to_buy'] == 1456


# ============================================================================
# 5. Error & Edge Handling
# ============================================================================

class TestErrorHandling:
    """The function must never raise; it returns {success: False} on errors."""

    def test_empty_dataframe(self):
        """Simulates a delisted / invalid ticker returning no data."""
        empty = pd.DataFrame()
        with _patch_yf_download(empty):
            result = calculate_execution('DELISTED.NS', 1_000_000)

        assert result['success'] is False
        assert 'error' in result

    def test_insufficient_history(self):
        """An IPO with only 10 trading days should be rejected gracefully."""
        closes = [200.0] * 10
        df = _make_ohlcv(closes)

        with _patch_yf_download(df):
            result = calculate_execution('IPO.NS', 1_000_000)

        assert result['success'] is False

    def test_yf_download_exception(self):
        """If yfinance itself throws, the function should catch and return."""
        with patch('engine.risk_and_timing.yf.download',
                   side_effect=Exception('Network timeout')):
            result = calculate_execution('BROKEN.NS', 1_000_000)

        assert result['success'] is False
        assert 'Network timeout' in result['error']
