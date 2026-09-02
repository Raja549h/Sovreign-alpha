"""
═══════════════════════════════════════════════════════════════════════════════
SOVEREIGN ALPHA — 200-Day Historical Edge Verification Audit
═══════════════════════════════════════════════════════════════════════════════
Connects to live Aiven PostgreSQL, pulls all historical predictions,
ingests forward pricing from yfinance, and computes quantitative edge metrics.
"""

import sys, io, os, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore')

from dotenv import load_dotenv
load_dotenv()

import psycopg2
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════════════════════
# 1. DATABASE CONNECTION & DATA EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def connect_db():
    url = os.environ.get('DATABASE_URL') or os.environ.get('AIVEN_DATABASE_URL')
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg2.connect(url)

def fetch_predictions(conn):
    """Fetch all prediction ledger records."""
    cur = conn.cursor()
    cur.execute("""
        SELECT prediction_id, timestamp, asset, sector, thesis,
               confidence_score, status, actual_outcome, actual_return_pct,
               trade_signal, entry_price, target_price, stop_loss
        FROM prediction_ledger
        WHERE status IN ('resolved', 'active')
        ORDER BY timestamp ASC
    """)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return pd.DataFrame(rows, columns=cols)

def fetch_regime_observations(conn):
    """Fetch regime signal observations."""
    cur = conn.cursor()
    cur.execute("""
        SELECT timestamp, regime_relevance, headline
        FROM observations
        WHERE type = 'regime_signal'
        ORDER BY timestamp ASC
    """)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return pd.DataFrame(rows, columns=cols)

def fetch_macro_health(conn):
    """Fetch macro health snapshots for regime mapping."""
    cur = conn.cursor()
    cur.execute("""
        SELECT id, snapshot_date, composite_score, status
        FROM macro_health_snapshots
        ORDER BY snapshot_date ASC
    """)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return pd.DataFrame(rows, columns=cols)

def fetch_veto_archive(conn):
    """Fetch veto archive for divergence/risk analysis."""
    cur = conn.cursor()
    cur.execute("""
        SELECT veto_id, timestamp, asset, sector, rejection_reason,
               risk_score, expected_loss_pct, actual_outcome, actual_return_pct,
               avoided_drawdown, veto_correct
        FROM veto_archive
        ORDER BY timestamp ASC
    """)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return pd.DataFrame(rows, columns=cols)

# ═══════════════════════════════════════════════════════════════════════════════
# 2. YFINANCE PRICE INGESTION
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_price_history(tickers, start_date, end_date):
    """Download OHLC data for a list of tickers from yfinance."""
    price_data = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start_date, end=end_date, 
                           progress=False, auto_adjust=True)
            if not df.empty:
                # Handle multi-level columns from yfinance
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                price_data[ticker] = df
        except Exception as e:
            pass  # Skip tickers that fail
    return price_data

# ═══════════════════════════════════════════════════════════════════════════════
# 3. EDGE CALCULATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def compute_active_mtm(active_df, price_data):
    """
    Calculate Mark-to-Market (MTM) performance for active trades.
    """
    floating_returns = []
    profitable = 0
    losing = 0
    
    if active_df.empty:
        return {'count': 0, 'profitable': 0, 'losing': 0, 'avg_floating_return': 0.0}
        
    for _, row in active_df.iterrows():
        asset = row['asset']
        if asset not in price_data: continue
        
        prices = price_data[asset]
        if prices.empty: continue
        
        current_price = float(prices.iloc[-1]['Close'])
        entry_price = float(row['entry_price']) if row.get('entry_price') else current_price
        if entry_price == 0: continue
        
        signal = str(row.get('trade_signal', 'BUY')).upper()
        if signal == 'NONE' or not signal: signal = 'BUY'
        
        if signal in ('SHORT', 'SELL'):
            ret = (entry_price - current_price) / entry_price * 100
        else:
            ret = (current_price - entry_price) / entry_price * 100
            
        floating_returns.append(ret)
        if ret > 0:
            profitable += 1
        elif ret < 0:
            losing += 1
            
    avg_floating = (sum(floating_returns) / len(floating_returns)) if floating_returns else 0.0
    return {
        'count': len(active_df),
        'profitable': profitable,
        'losing': losing,
        'avg_floating_return': avg_floating
    }

def compute_signal_hit_rate(predictions_df, price_data):
    """
    For each prediction, check if target was hit before stop_loss
    within a 30-day forward window using actual market data.
    
    For predictions that already have actual_outcome in DB, use that.
    For others, compute from yfinance price data.
    """
    wins = 0
    losses = 0
    indeterminate = 0
    total_evaluated = 0
    profit_amounts = []
    loss_amounts = []
    per_ticker_results = defaultdict(lambda: {'wins': 0, 'losses': 0, 'indet': 0})
    
    for _, row in predictions_df.iterrows():
        asset = row['asset']
        db_outcome = row.get('actual_outcome')
        
        # Use DB outcome if resolved
        if db_outcome == 'HIT':
            wins += 1
            total_evaluated += 1
            per_ticker_results[asset]['wins'] += 1
            ret = float(row.get('actual_return_pct') or 0.0)
            if ret > 100 or ret < 0:  # Fix legacy DB corruption (e.g., 23805%)
                ep = float(row.get('entry_price') or 0)
                tp = float(row.get('target_price') or 0)
                if ep > 0 and tp > 0:
                    ret = abs(tp - ep) / ep * 100
                else:
                    ret = 9.0  # Default 1:3 R/R target
            profit_amounts.append(abs(ret))
            continue
        elif db_outcome == 'MISS':
            losses += 1
            total_evaluated += 1
            per_ticker_results[asset]['losses'] += 1
            ret = float(row.get('actual_return_pct') or 0.0)
            if ret < -100 or ret > 0 or abs(ret) > 100:
                ep = float(row.get('entry_price') or 0)
                sl = float(row.get('stop_loss') or 0)
                if ep > 0 and sl > 0:
                    ret = abs(ep - sl) / ep * 100
                else:
                    ret = 3.0  # Default 1:3 R/R stop
            loss_amounts.append(abs(ret))
            continue
        elif db_outcome == 'indeterminate':
            # Try to resolve from price data
            pass
        
        # Try yfinance forward-looking resolution
        if asset not in price_data:
            indeterminate += 1
            per_ticker_results[asset]['indet'] += 1
            continue
            
        prices = price_data[asset].copy()
        if prices.index.tz is not None:
            prices.index = prices.index.tz_localize(None)
        
        # Parse prediction timestamp
        try:
            pred_date = pd.Timestamp(row['timestamp']).tz_localize(None)
        except:
            try:
                pred_date = pd.Timestamp(row['timestamp'][:19])
            except:
                indeterminate += 1
                per_ticker_results[asset]['indet'] += 1
                continue
        
        # Get the entry price (use close on prediction date or first available after)
        forward_start = pred_date
        forward_end = pred_date + timedelta(days=30)
        
        # Filter to 30-day forward window
        mask = (prices.index >= forward_start) & (prices.index <= forward_end)
        forward_prices = prices.loc[mask]
        
        if forward_prices.empty:
            indeterminate += 1
            per_ticker_results[asset]['indet'] += 1
            continue
        
        total_evaluated += 1
        entry_close = float(forward_prices.iloc[0]['Close'])
        
        # Check if entry_price and target_price exist in DB
        entry_price = float(row['entry_price']) if row.get('entry_price') else entry_close
        target_price = float(row['target_price']) if row.get('target_price') else entry_close * 1.08
        stop_loss = float(row['stop_loss']) if row.get('stop_loss') else entry_close * 0.95
        
        # Determine signal direction
        signal = row.get('trade_signal', 'BUY') or 'BUY'
        
        # Evaluate: did target get hit before stop_loss?
        target_hit = False
        stop_hit = False
        
        for _, bar in forward_prices.iterrows():
            high = float(bar['High'])
            low = float(bar['Low'])
            
            if signal.upper() in ('BUY', 'LONG'):
                if high >= target_price:
                    target_hit = True
                    break
                if low <= stop_loss:
                    stop_hit = True
                    break
            else:  # SELL / SHORT
                if low <= target_price:
                    target_hit = True
                    break
                if high >= stop_loss:
                    stop_hit = True
                    break
        
        if target_hit:
            wins += 1
            per_ticker_results[asset]['wins'] += 1
            profit_pct = abs(target_price - entry_price) / entry_price * 100
            profit_amounts.append(profit_pct)
        elif stop_hit:
            losses += 1
            per_ticker_results[asset]['losses'] += 1
            loss_pct = abs(entry_price - stop_loss) / entry_price * 100
            loss_amounts.append(loss_pct)
        else:
            # Neither hit within 30 days — evaluate by final price
            final_close = float(forward_prices.iloc[-1]['Close'])
            if final_close > entry_price:
                wins += 1
                per_ticker_results[asset]['wins'] += 1
                profit_amounts.append(abs(final_close - entry_price) / entry_price * 100)
            else:
                losses += 1
                per_ticker_results[asset]['losses'] += 1
                loss_amounts.append(abs(entry_price - final_close) / entry_price * 100)
    
    resolved = wins + losses
    win_rate = (wins / resolved * 100) if resolved > 0 else 0
    avg_profit = (sum(profit_amounts) / len(profit_amounts)) if profit_amounts else 0.0
    avg_loss = (sum(loss_amounts) / len(loss_amounts)) if loss_amounts else 1.0
    profit_loss_ratio = (avg_profit / avg_loss) if avg_loss > 0 else 0.0
    
    return {
        'total_predictions': len(predictions_df),
        'total_evaluated': total_evaluated,
        'wins': wins,
        'losses': losses,
        'indeterminate': indeterminate,
        'win_rate': win_rate,
        'avg_profit_pct': avg_profit,
        'avg_loss_pct': avg_loss,
        'profit_loss_ratio': profit_loss_ratio,
        'per_ticker': dict(per_ticker_results),
    }

def compute_regime_evasion(regime_df, nifty_prices):
    """
    Compute average 14-day forward return of Nifty 50 on days classified
    as RISK_ON vs RISK_OFF.
    """
    if regime_df.empty or nifty_prices is None or nifty_prices.empty:
        return {'risk_on_14d_return': 0, 'risk_off_14d_return': 0, 'regime_delta': 0,
                'risk_on_count': 0, 'risk_off_count': 0, 'neutral_count': 0}
    
    # Normalize nifty index to tz-naive
    nifty = nifty_prices.copy()
    if nifty.index.tz is not None:
        nifty.index = nifty.index.tz_localize(None)
    
    risk_on_returns = []
    risk_off_returns = []
    neutral_returns = []
    
    # Deduplicate regime observations by date (take first per day)
    seen_dates = set()
    
    for _, row in regime_df.iterrows():
        regime = row.get('regime_relevance', '') or ''
        try:
            obs_date = pd.Timestamp(row['timestamp']).tz_localize(None)
        except:
            try:
                obs_date = pd.Timestamp(str(row['timestamp'])[:19])
            except:
                continue
        
        date_key = obs_date.date()
        if date_key in seen_dates:
            continue
        seen_dates.add(date_key)
        
        # Find prices in forward window using mask
        forward_mask = (nifty.index >= obs_date) & (nifty.index <= obs_date + timedelta(days=14))
        forward = nifty.loc[forward_mask]
        
        if len(forward) < 2:
            continue
        
        start_price = float(forward.iloc[0]['Close'])
        end_price = float(forward.iloc[-1]['Close'])
        
        fwd_return = (end_price - start_price) / start_price * 100
        
        if 'RISK_ON' in regime.upper() or 'BULLISH' in regime.upper():
            risk_on_returns.append(fwd_return)
        elif 'RISK_OFF' in regime.upper() or 'BEARISH' in regime.upper():
            risk_off_returns.append(fwd_return)
        else:
            neutral_returns.append(fwd_return)
    
    avg_risk_on = np.mean(risk_on_returns) if risk_on_returns else 0
    avg_risk_off = np.mean(risk_off_returns) if risk_off_returns else 0
    avg_neutral = np.mean(neutral_returns) if neutral_returns else 0
    
    return {
        'risk_on_14d_return': avg_risk_on,
        'risk_off_14d_return': avg_risk_off,
        'neutral_14d_return': avg_neutral,
        'regime_delta': avg_risk_on - avg_risk_off,
        'risk_on_count': len(risk_on_returns),
        'risk_off_count': len(risk_off_returns),
        'neutral_count': len(neutral_returns),
    }

def compute_veto_effectiveness(veto_df, price_data):
    if veto_df.empty:
        return {'avg_avoided_return': 0, 'veto_correct_pct': 0, 'total_vetoes': 0, 'evaluated_vetoes': 0, 'correct_vetoes': 0}
    
    forward_returns = []
    correct_vetoes = 0
    evaluated_vetoes = 0
    
    for _, row in veto_df.iterrows():
        asset = row.get('asset', '')
        
        # Use DB fields if available: avoided_drawdown of 11.9 means a return of -11.9
        if row.get('avoided_drawdown') is not None and row['avoided_drawdown'] != 0:
            actual_fwd = -float(row['avoided_drawdown'])
            forward_returns.append(actual_fwd)
            
            # For a vetoed BUY signal: CORRECT if forward return < 0
            if actual_fwd < 0:
                correct_vetoes += 1
            evaluated_vetoes += 1
            continue
        
        # Try yfinance lookup
        if asset not in price_data:
            continue
            
        prices = price_data[asset].copy()
        if prices.index.tz is not None:
            prices.index = prices.index.tz_localize(None)
        try:
            veto_date = pd.Timestamp(row['timestamp']).tz_localize(None)
        except:
            try:
                veto_date = pd.Timestamp(str(row['timestamp'])[:19])
            except:
                continue
        
        forward_end = veto_date + timedelta(days=30)
        mask = (prices.index >= veto_date) & (prices.index <= forward_end)
        forward = prices.loc[mask]
        
        if len(forward) < 2:
            continue
        
        evaluated_vetoes += 1
        entry = float(forward.iloc[0]['Close'])
        final = float(forward.iloc[-1]['Close'])
        fwd_return = (final - entry) / entry * 100
        forward_returns.append(fwd_return)
        
        if fwd_return < 0:
            correct_vetoes += 1
    
    avg_fwd = (sum(forward_returns) / len(forward_returns)) if forward_returns else 0.0
    correct_pct = (correct_vetoes / evaluated_vetoes * 100) if evaluated_vetoes > 0 else 0.0
    
    return {
        'avg_avoided_return': avg_fwd,
        'veto_correct_pct': correct_pct,
        'total_vetoes': len(veto_df),
        'evaluated_vetoes': evaluated_vetoes,
        'correct_vetoes': correct_vetoes,
    }

# ═══════════════════════════════════════════════════════════════════════════════
# 4. MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 72)
    print("  SOVEREIGN ALPHA — 200-Day Historical Edge Verification Audit")
    print("=" * 72)
    print(f"  Audit Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  Database: Aiven PostgreSQL (Live)")
    print()
    
    # 1. Connect and extract
    print("[1/5] Connecting to Aiven PostgreSQL...")
    conn = connect_db()
    
    predictions = fetch_predictions(conn)
    regimes = fetch_regime_observations(conn)
    macro = fetch_macro_health(conn)
    vetoes = fetch_veto_archive(conn)
    conn.close()
    
    print(f"      Predictions loaded:  {len(predictions)}")
    print(f"      Regime observations: {len(regimes)}")
    print(f"      Macro snapshots:     {len(macro)}")
    print(f"      Veto archive:        {len(vetoes)}")
    
    # Date range
    if not predictions.empty:
        min_ts = predictions['timestamp'].min()[:10]
        max_ts = predictions['timestamp'].max()[:10]
        print(f"      Date range:          {min_ts} to {max_ts}")
    
    # 2. Fetch yfinance data
    print("\n[2/5] Ingesting historical pricing via yfinance...")
    unique_tickers = list(predictions['asset'].unique())
    all_tickers = unique_tickers + ['^NSEI']  # Add Nifty 50
    
    # Determine date range (200 days back from now + 30 day forward buffer)
    end_date = datetime.now() + timedelta(days=1)
    start_date = end_date - timedelta(days=250)
    
    price_data = fetch_price_history(all_tickers, 
                                     start_date.strftime('%Y-%m-%d'),
                                     end_date.strftime('%Y-%m-%d'))
    
    print(f"      Tickers fetched:     {len(price_data)}/{len(all_tickers)}")
    for t in sorted(price_data.keys()):
        bars = len(price_data[t])
        print(f"        {t:20s} {bars:4d} bars")
    
    nifty_prices = price_data.get('^NSEI')
    
    # Split predictions
    resolved_df = predictions[predictions['status'] == 'resolved']
    active_df = predictions[predictions['status'] == 'active']
    
    # 3. Signal Hit Rate
    print("\n[3/5] Computing signal hit rate (30-day forward window)...")
    hit_rate = compute_signal_hit_rate(resolved_df, price_data)
    print(f"      Total predictions:   {hit_rate['total_predictions']}")
    print(f"      Evaluated:           {hit_rate['total_evaluated']}")
    print(f"      Wins:                {hit_rate['wins']}")
    print(f"      Losses:              {hit_rate['losses']}")
    print(f"      Indeterminate:       {hit_rate['indeterminate']}")
    
    # Active MTM
    print("\n[*] Computing Mark-to-Market for active trades...")
    mtm_stats = compute_active_mtm(active_df, price_data)
    print(f"      Active evaluated:    {mtm_stats['count']}")
    
    # 4. Regime Evasion
    print("\n[4/5] Computing macro regime evasion (14-day forward Nifty)...")
    regime_evasion = compute_regime_evasion(regimes, nifty_prices)
    print(f"      RISK_ON observations:  {regime_evasion['risk_on_count']}")
    print(f"      RISK_OFF observations: {regime_evasion['risk_off_count']}")
    
    # 5. Veto Effectiveness
    print("\n[5/5] Computing veto engine effectiveness...")
    veto_stats = compute_veto_effectiveness(vetoes, price_data)
    print(f"      Total vetoes:          {veto_stats['total_vetoes']}")
    print(f"      Evaluated:             {veto_stats['evaluated_vetoes']}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # FINAL SCORECARD
    # ═══════════════════════════════════════════════════════════════════════
    
    win_rate_pct = hit_rate['win_rate']
    
    print()
    print("=" * 72)
    print("  SOVEREIGN ALPHA — EDGE VERIFICATION SCORECARD")
    print("=" * 72)
    print()
    print(f"  {'Metric':<45s} {'Value':>20s}")
    print(f"  {'—' * 45}  {'—' * 20}")
    print(f"  {'Total Historical Predictions (Resolved)':<45s} {hit_rate['total_predictions']:>20d}")
    print(f"  {'Predictions Evaluated (Resolved)':<45s} {hit_rate['total_evaluated']:>20d}")
    print(f"  {'Wins (Target Hit / Positive at 30d)':<45s} {hit_rate['wins']:>20d}")
    print(f"  {'Losses (Stop Hit / Negative at 30d)':<45s} {hit_rate['losses']:>20d}")
    print(f"  {'Still Indeterminate':<45s} {hit_rate['indeterminate']:>20d}")
    print(f"  {'—' * 45}  {'—' * 20}")
    print(f"  {'Overall Win Rate':<45s} {win_rate_pct:>19.2f}%")
    print(f"  {'Average Profit per Win':<45s} {hit_rate['avg_profit_pct']:>19.2f}%")
    print(f"  {'Average Loss per Loss':<45s} {hit_rate['avg_loss_pct']:>19.2f}%")
    print(f"  {'Profit / Loss Ratio':<45s} {hit_rate['profit_loss_ratio']:>20.2f}")
    print(f"  {'—' * 45}  {'—' * 20}")
    print(f"  {'Active Trades in Queue':<45s} {mtm_stats['count']:>20d}")
    print(f"  {'Floating Profitable Trades':<45s} {mtm_stats['profitable']:>20d}")
    print(f"  {'Floating Losing Trades':<45s} {mtm_stats['losing']:>20d}")
    print(f"  {'Average Floating Profit':<45s} {mtm_stats['avg_floating_return']:>19.2f}%")
    print(f"  {'—' * 45}  {'—' * 20}")
    print(f"  {'Nifty 14d Fwd Return (RISK_ON days)':<45s} {regime_evasion['risk_on_14d_return']:>19.2f}%")
    print(f"  {'Nifty 14d Fwd Return (RISK_OFF days)':<45s} {regime_evasion['risk_off_14d_return']:>19.2f}%")
    print(f"  {'Regime Delta (ON - OFF)':<45s} {regime_evasion['regime_delta']:>19.2f}%")
    print(f"  {'—' * 45}  {'—' * 20}")
    print(f"  {'Vetoes Evaluated':<45s} {veto_stats['evaluated_vetoes']:>20d}")
    print(f"  {'Veto Correct Rate':<45s} {veto_stats['veto_correct_pct']:>19.2f}%")
    print(f"  {'Avg Forward Return of Vetoed Assets':<45s} {veto_stats['avg_avoided_return']:>19.2f}%")
    print()
    
    # Per-ticker breakdown
    print(f"  {'TICKER BREAKDOWN':<45s}")
    print(f"  {'—' * 45}  {'—' * 20}")
    print(f"  {'Ticker':<20s} {'Wins':>6s} {'Losses':>8s} {'Win %':>10s}")
    for ticker in sorted(hit_rate['per_ticker'].keys()):
        stats = hit_rate['per_ticker'][ticker]
        t_total = stats['wins'] + stats['losses']
        t_rate = (stats['wins'] / t_total * 100) if t_total > 0 else 0
        print(f"  {ticker:<20s} {stats['wins']:>6d} {stats['losses']:>8d} {t_rate:>9.1f}%")
    
    print()
    print("=" * 72)
    
    # Final verdict
    if win_rate_pct >= 54.0:
        print("  [PASS] EDGE VERIFIED: Ready for Inbound Distribution")
    else:
        print("  [FAIL] INSUFFICIENT EDGE: Parameter Recalibration Required")
    
    print("=" * 72)
    print()


if __name__ == '__main__':
    main()
