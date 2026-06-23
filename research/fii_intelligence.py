from database import get_connection
"""
FII Flow Intelligence — Daily NSDL FPI flow tracking
=====================================================
Fetches, stores, and analyses daily FII equity/debt flows
for India macro intelligence and portfolio vulnerability.
"""


from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).parent.parent
BILLING_DIR = BASE_DIR / "billing"
RESEARCH_DB = BILLING_DIR / "research.db"

NSDL_FPI_FLOWS_SQL = """
CREATE TABLE IF NOT EXISTS nsdl_fpi_flows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_date TEXT UNIQUE,
    equity_net REAL,
    debt_net REAL,
    total_net REAL,
    equity_buy REAL,
    equity_sell REAL,
    source TEXT,
    fetched_at TEXT DEFAULT CURRENT_TIMESTAMP
)
"""

FII_ALERT_THRESHOLD = 5000  # Cr, 5-day cumulative outflow triggers alert

SECTOR_FII_SENSITIVITY = {
    'NBFC': 0.85, 'BANK': 0.80, 'TECHNOLOGY': 0.90, 'CONSUMER': 0.65,
    'ENERGY': 0.55, 'PHARMA': 0.75, 'INFRASTRUCTURE': 0.60, 'FMCG': 0.60,
    'IT': 0.92, 'AUTO': 0.70, 'METALS': 0.75, 'REALTY': 0.80,
}


def _get_db():
    conn = get_connection()
    return conn


def init_fii_tables():
    with _get_db() as conn:
        conn.execute(NSDL_FPI_FLOWS_SQL)
        conn.commit()


class FIIIntelligence:

    def fetch_daily_fii_flows(self) -> Dict:
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        try:
            import requests
            from bs4 import BeautifulSoup
            url = "https://www.fpi.nsdl.co.in/web/Reports/Yearwise.aspx"
            resp = requests.get(url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                table = soup.find('table', {'id': 'ContentPlaceHolder1_GridView1'})
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 6:
                            date_str = cols[0].get_text(strip=True)
                            if today[:7] in date_str:
                                equity_buy = self._parse_cr(cols[1].get_text(strip=True))
                                equity_sell = self._parse_cr(cols[2].get_text(strip=True))
                                debt_buy = self._parse_cr(cols[3].get_text(strip=True))
                                debt_sell = self._parse_cr(cols[4].get_text(strip=True))
                                equity_net = round(equity_buy - equity_sell, 2)
                                debt_net = round(debt_buy - debt_sell, 2)
                                return {
                                    'date': date_str, 'equity_net': equity_net,
                                    'debt_net': debt_net, 'total_net': round(equity_net + debt_net, 2),
                                    'equity_buy': equity_buy, 'equity_sell': equity_sell,
                                    'source': 'NSDL'
                                }
        except Exception as _e:
            print(f"[fii] Primary NSDL fetch failed: {_e}")
        try:
            import yfinance as yf
            nsei = yf.download('^NSEI', period='5d', interval='1d', progress=False)
            if not nsei.empty:
                latest = nsei.iloc[-1]
                prev = nsei.iloc[-2] if len(nsei) > 1 else nsei.iloc[-1]
                price_change = float(latest['Close'] - prev['Close'])
                volume = int(latest['Volume']) if 'Volume' in nsei.columns else 0
                est_flow = round(price_change * volume / 1e8, 2)
                return {
                    'date': today, 'equity_net': est_flow, 'debt_net': 0.0,
                    'total_net': est_flow, 'equity_buy': max(est_flow, 0),
                    'equity_sell': abs(min(est_flow, 0)),
                    'source': 'YFINANCE_ESTIMATE'
                }
        except Exception as _e:
            print(f"[fii] yfinance fallback failed: {_e}")
        return {
            'date': today, 'equity_net': 0.0, 'debt_net': 0.0,
            'total_net': 0.0, 'equity_buy': 0.0, 'equity_sell': 0.0,
            'source': 'UNAVAILABLE'
        }

    def store_daily_flow(self, flow_data: Dict) -> bool:
        init_fii_tables()
        try:
            with _get_db() as conn:
                c = conn.cursor()
                c.execute(
                    """INSERT OR IGNORE INTO nsdl_fpi_flows
                       (flow_date, equity_net, debt_net, total_net,
                        equity_buy, equity_sell, source)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (flow_data.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d')),
                     flow_data.get('equity_net', 0.0), flow_data.get('debt_net', 0.0),
                     flow_data.get('total_net', 0.0), flow_data.get('equity_buy', 0.0),
                     flow_data.get('equity_sell', 0.0), flow_data.get('source', 'UNKNOWN'))
                )
                conn.commit()
                return c.rowcount > 0
        except Exception as _e:
            print(f"[fii] store_daily_flow failed: {_e}")
            return False

    def get_flow_summary(self, days: int = 30) -> Dict:
        with _get_db() as conn:
            c = conn.cursor()
            cut = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%d')
            c.execute("""SELECT flow_date, equity_net, debt_net, total_net
                         FROM nsdl_fpi_flows WHERE flow_date >= ? ORDER BY flow_date ASC""", (cut,))
            rows = c.fetchall()
        if not rows:
            return {'1d': 0.0, '5d': 0.0, '10d': 0.0, '30d': 0.0,
                    'trend': 'MIXED', 'pressure': 'LOW', 'alert': False}
        data = [dict(r) for r in rows]
        total_net = [r['total_net'] for r in data]
        equity_nets = [r['equity_net'] for r in data]
        d1 = total_net[-1] if total_net else 0.0
        d5 = sum(total_net[-5:]) if len(total_net) >= 5 else sum(total_net)
        d10 = sum(total_net[-10:]) if len(total_net) >= 10 else sum(total_net)
        d30 = sum(total_net)
        recent_3 = sum(total_net[-3:]) if len(total_net) >= 3 else d5
        if recent_3 > 1000:
            trend = 'INFLOW'
            pressure = 'LOW' if d30 > 0 else 'MEDIUM'
        elif recent_3 < -1000:
            trend = 'OUTFLOW'
            pressure = 'HIGH' if d30 < -5000 else 'MEDIUM'
        else:
            trend = 'MIXED'
            pressure = 'LOW'
        alert = abs(d5) > FII_ALERT_THRESHOLD and d5 < 0
        return {
            '1d': round(d1, 2), '5d': round(d5, 2), '10d': round(d10, 2),
            '30d': round(d30, 2), 'trend': trend, 'pressure': pressure,
            'alert': alert, 'days_of_data': len(data)
        }

    def get_portfolio_fii_exposure(self, tickers: List[str]) -> Dict:
        from research.storage.research_db import get_all_companies
        companies = get_all_companies()
        flow_summary = self.get_flow_summary(30)
        regime_pressure = 1.0 if flow_summary.get('trend') == 'OUTFLOW' else 0.5 if flow_summary.get('trend') == 'MIXED' else 0.0
        results = {}
        for ticker in tickers:
            company = next((c for c in companies if c.get('ticker', '').upper() == ticker.upper()), None)
            sector = company.get('sector', 'NBFC') if company else 'NBFC'
            sensitivity = SECTOR_FII_SENSITIVITY.get(sector.upper(), 0.65)
            vulnerability = round(sensitivity * regime_pressure * 10, 1)
            results[ticker] = {
                'sector': sector, 'sensitivity': sensitivity,
                'vulnerability_score': min(vulnerability, 10.0),
                'regime_pressure': 'OUTFLOW' if regime_pressure > 0.5 else 'NEUTRAL' if regime_pressure > 0 else 'INFLOW'
            }
        return results

    def generate_fii_alert(self) -> Optional[str]:
        summary = self.get_flow_summary(30)
        if not summary.get('alert'):
            return None
        d5 = summary.get('5d', 0)
        d10 = summary.get('10d', 0)
        d30 = summary.get('30d', 0)
        if abs(d5) > FII_ALERT_THRESHOLD and d5 < 0:
            fii_out = abs(round(d5))
            return (
                f"FII equity outflows of ₹{fii_out:,.0f} Cr over 5 sessions. "
                f"10-day net ₹{abs(round(d10)):,.0f} Cr, 30-day net ₹{abs(round(d30)):,.0f} Cr. "
                f"NBFC and financials sector exposure elevated."
            )
        return None

    def get_flow_history(self, days: int = 90) -> List[Dict]:
        with _get_db() as conn:
            c = conn.cursor()
            start_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%d')
            c.execute("""SELECT * FROM nsdl_fpi_flows WHERE flow_date >= %s
                         ORDER BY flow_date ASC""", (start_date,))
            return [dict(r) for r in c.fetchall()]

    def _parse_cr(self, text: str) -> float:
        text = text.replace(',', '').replace(' ', '').strip()
        try:
            return float(text) if text else 0.0
        except ValueError:
            return 0.0
