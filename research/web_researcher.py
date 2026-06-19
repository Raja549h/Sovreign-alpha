"""
Web Researcher — Automatic public data collection for deep research
===================================================================
Uses yfinance for financial data and Groq web search for qualitative context.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
load_dotenv(BASE_DIR / ".env")
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

HISTORICAL_METRICS = [
    "Revenue", "EBITDA", "PAT", "ROE", "ROA", "ROCE",
    "DebtEquity", "CurrentRatio", "DividendYield",
    "MarketCap", "Beta", "PE", "PBV", "PS"
]

SECTOR_KEYWORDS = {
    "NBFC": "credit cost, NIM, AUM growth, disbursement, asset quality, cost of funds",
    "BANKING": "NIM, credit cost, NPA, loan growth, CASA ratio, cost of funds",
    "IT": "deal wins, attrition, pricing, H1B, digital revenue, margin trajectory",
    "ENERGY": "refining margin, crude spread, regulatory, renewable mix, marketing margin",
    "PHARMA": "R&D pipeline, USFDA, ANDA, price erosion, complex generics, China",
    "FMCG": "volume growth, rural demand, input cost, distribution, competition",
    "AUTO": "volume, mix, EV transition, export, commodity cost, regulatory",
    "REALTY": "pre-sales, launch pipeline, debt, inventory, commercial leasing",
    "MEDIA": "subscription, ARPU, ad revenue, content cost, digital transition",
    "TELECOM": "ARPU, subscriber, churn, spectrum, data usage, 5G capex",
    "METAL": "realization, volume, cost curve, demand, inventory, global trade",
}

SEARCH_TEMPLATES = [
    "{ticker} {company} annual report FY24 FY25 financial results",
    "{ticker} {company} management commentary earnings call transcript analyst meet",
    "{ticker} {company} credit rating debt balance sheet FY25",
    "{ticker} {company} shareholding pattern promoter pledge FII DII",
    "{company} competitors market share industry position ranking",
    "{ticker} {company} revenue EBITDA PAT margin ROE ROCE trend",
    "{ticker} {company} capex dividend buyback debt reduction",
]

def _fetch_yfinance_data(ticker: str) -> Dict:
    data = {}
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker + ".NS" if not ticker.endswith(".NS") else ticker)
        info = stock.info or {}
        data["market_cap"] = info.get("marketCap")
        data["enterprise_value"] = info.get("enterpriseValue")
        data["trailing_pe"] = info.get("trailingPE")
        data["forward_pe"] = info.get("forwardPE")
        data["price_to_book"] = info.get("priceToBook")
        data["price_to_sales"] = info.get("priceToSalesTrailing12Months")
        data["dividend_yield"] = info.get("dividendYield")
        data["beta"] = info.get("beta")
        data["fifty_two_week_high"] = info.get("fiftyTwoWeekHigh")
        data["fifty_two_week_low"] = info.get("fiftyTwoWeekLow")
        data["current_price"] = info.get("currentPrice") or info.get("regularMarketPrice")
        data["target_mean_price"] = info.get("targetMeanPrice")
        data["recommendation"] = info.get("recommendationKey")
        data["sector"] = info.get("sector")
        data["industry"] = info.get("industry")
        data["short_ratio"] = info.get("shortRatio")
        data["held_percent_institutions"] = info.get("heldPercentInstitutions")
        data["held_percent_promoters"] = info.get("heldPercentInsiders")
        data["revenue_3y"] = []
        for year in ["totalRevenue", "revenuePerShare"]:
            val = info.get(year)
            if val:
                data["revenue_3y"].append(val)
        data["ebitda"] = info.get("ebitda")
        data["total_debt"] = info.get("totalDebt")
        data["total_cash"] = info.get("totalCash")
        data["operating_cash_flow"] = info.get("operatingCashFlow")
        data["free_cash_flow"] = info.get("freeCashFlow")
        data["gross_margins"] = info.get("grossMargins")
        data["operating_margins"] = info.get("operatingMargins")
        data["profit_margins"] = info.get("profitMargins")
        data["return_on_equity"] = info.get("returnOnEquity")
        data["return_on_assets"] = info.get("returnOnAssets")
        data["debt_to_equity"] = info.get("debtToEquity")
        data["current_ratio"] = info.get("currentRatio")
        data["quick_ratio"] = info.get("quickRatio")
        data["revenue_growth"] = info.get("revenueGrowth")
        data["earnings_growth"] = info.get("earningsGrowth")
        data["trailing_eps"] = info.get("trailingEps")
        hist = stock.history(period="3y")
        if not hist.empty:
            data["history_high"] = float(hist["High"].max())
            data["history_low"] = float(hist["Low"].min())
            data["history_avg_volume"] = int(hist["Volume"].mean())
            data["history_start"] = str(hist.index[0].date())
            data["history_end"] = str(hist.index[-1].date())
            returns = hist["Close"].pct_change().dropna()
            data["history_volatility"] = float(returns.std() * (252**0.5))
        data["data_source"] = "yfinance"
        data["data_quality"] = "live"
    except ImportError:
        data["data_source"] = "yfinance_unavailable"
        data["data_quality"] = "unavailable"
    except Exception as e:
        data["data_source"] = "yfinance"
        data["data_quality"] = f"error: {str(e)}"
    return data

def _groq_web_search(query: str) -> str:
    if not GROQ_API_KEY:
        return ""
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a financial research assistant. Provide factual, data-based information about the company. If you don't know exact numbers, state that clearly. Never fabricate data."},
                {"role": "user", "content": f"Find and summarize information about: {query}. Return specific numbers, dates, and facts where available. If data is unavailable, say so."}
            ],
            temperature=0.1,
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[Search unavailable: {e}]"

def _get_sector_keywords(sector: str) -> str:
    for key in SECTOR_KEYWORDS:
        if key.lower() in (sector or "").lower():
            return SECTOR_KEYWORDS[key]
    return "financial performance, competitive position, growth strategy, risk factors"

def _calculate_data_confidence(financial: Dict, searches: List[str]) -> float:
    score = 0.0
    checks = 0
    key_fields = ["trailing_pe", "price_to_book", "market_cap", "ebitda", "return_on_equity", "debt_to_equity", "revenue_growth", "dividend_yield"]
    for field in key_fields:
        checks += 1
        if financial.get(field) is not None:
            score += 1
    searches_found = sum(1 for s in searches if s and "[Search unavailable" not in s and len(s) > 50)
    total_searches = len(searches) if searches else 1
    search_score = searches_found / max(total_searches, 1)
    score += search_score * 4
    checks += 4
    return min(1.0, score / max(checks, 1))

def research_company(ticker: str, company_name: str, sector: str) -> Dict:
    financial_data = _fetch_yfinance_data(ticker)
    search_results = []
    for template in SEARCH_TEMPLATES:
        query = template.format(ticker=ticker, company=company_name)
        result = _groq_web_search(query)
        search_results.append(result)
    management_commentary = search_results[1] if len(search_results) > 1 else ""
    sector_context = search_results[5] if len(search_results) > 5 else ""
    competitive_position = search_results[4] if len(search_results) > 4 else ""
    sources = [f"yfinance: {ticker}.NS"]
    if GROQ_API_KEY:
        sources.append("groq-web-search")
    data_confidence = _calculate_data_confidence(financial_data, search_results)
    warnings = []
    if financial_data.get("data_quality") == "unavailable":
        warnings.append("yfinance package not installed. Financial data limited.")
    elif "error" in financial_data.get("data_quality", ""):
        warnings.append(f"yfinance error: {financial_data['data_quality']}")
    if not GROQ_API_KEY:
        warnings.append("GROQ_API_KEY not set. Web search unavailable.")
    macro_context = {}
    try:
        from research.intelligence.regime_connector import get_regime_context, assess_regime_sensitivity
        macro_context = get_regime_context()
        if sector:
            macro_context["sector_sensitivity"] = assess_regime_sensitivity(sector)
    except Exception:
        macro_context = {"regime": "NEUTRAL", "summary": "Regime context unavailable"}
    return {
        "financial_data": financial_data,
        "management_commentary": management_commentary,
        "sector_context": sector_context,
        "competitive_position": competitive_position,
        "macro_context": macro_context,
        "data_confidence": round(data_confidence, 2),
        "sources": sources,
        "warnings": warnings,
        "search_results": search_results,
    }
