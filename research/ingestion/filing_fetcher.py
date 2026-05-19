"""
Filing Fetcher — BSE/NSE filing downloader
============================================
Fetches company filings from NSE India, BSE India, or direct URLs.
Includes fallback for manual registration of locally downloaded files.
"""

import os
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from research.storage.research_db import (
    get_company, add_company, save_filing, get_connection
)

BASE_DIR = Path(__file__).parent.parent.parent
FILINGS_DIR = BASE_DIR / "research" / "data" / "filings"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/pdf,application/octet-stream,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


def _ensure_dir(ticker: str) -> Path:
    """Ensure filing directory exists for ticker."""
    dir_path = FILINGS_DIR / ticker
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def _download_pdf(url: str, dest_path: Path) -> bool:
    """Download PDF from URL to destination path."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        resp.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"  [ERROR] Download failed: {e}")
        return False


def fetch_nse_filings(ticker: str, filing_type: str = 'annual-report', company_id: int = None) -> List[Dict]:
    """
    Fetch filings from NSE India corporate filings page.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'BAJFINANCE')
        filing_type: Type of filing ('annual-report', 'quarterly', 'investor-presentation')
        company_id: Optional company ID for database registration
    
    Returns:
        List of filing metadata dicts
    """
    filings = []
    dir_path = _ensure_dir(ticker)
    
    try:
        search_url = f"https://www.nseindia.com/api/search?q={ticker}&type=corporate-filings"
        resp = requests.get(search_url, headers=HEADERS, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('items', []) if isinstance(data, dict) else []
            
            for item in items:
                title = item.get('title', '')
                link = item.get('link', '')
                if filing_type.replace('-', ' ') in title.lower() or filing_type in title.lower():
                    filename = f"{ticker}_{filing_type}_{datetime.now().strftime('%Y%m%d')}.pdf"
                    dest = dir_path / filename
                    
                    if not dest.exists():
                        if _download_pdf(link, dest):
                            filing_id = save_filing(company_id, filing_type, 'current', link, str(dest)) if company_id else None
                            filings.append({
                                'ticker': ticker,
                                'type': filing_type,
                                'url': link,
                                'local_path': str(dest),
                                'filing_id': filing_id,
                                'status': 'downloaded'
                            })
                            print(f"  [OK] Downloaded: {filename}")
                        else:
                            filings.append({
                                'ticker': ticker,
                                'type': filing_type,
                                'url': link,
                                'local_path': None,
                                'filing_id': None,
                                'status': 'failed'
                            })
                    else:
                        filings.append({
                            'ticker': ticker,
                            'type': filing_type,
                            'url': link,
                            'local_path': str(dest),
                            'filing_id': None,
                            'status': 'already_exists'
                        })
                    
                    time.sleep(2)
        else:
            print(f"  [WARN] NSE search returned {resp.status_code}")
            
    except Exception as e:
        print(f"  [ERROR] NSE fetch failed: {e}")
    
    return filings


def fetch_bse_filings(ticker_code: str, company_name: str, company_id: int = None) -> List[Dict]:
    """
    Fetch filings from BSE India.
    
    Args:
        ticker_code: BSE numeric code or ticker
        company_name: Company name for search
        company_id: Optional company ID for database registration
    
    Returns:
        List of filing metadata dicts
    """
    filings = []
    dir_path = _ensure_dir(ticker_code)
    
    try:
        search_url = f"https://api.bseindia.com/BseIndiaAPI/api/StockReachNew/w?scripcode={ticker_code}"
        resp = requests.get(search_url, headers=HEADERS, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            announcements = data.get('Table', []) if isinstance(data, dict) else []
            
            for ann in announcements[:5]:
                headline = ann.get('Headline', '')
                pdf_url = ann.get('PDFURL', '')
                if pdf_url and 'pdf' in pdf_url.lower():
                    filename = f"{ticker_code}_bse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    dest = dir_path / filename
                    
                    if not dest.exists():
                        full_url = f"https://www.bseindia.com{pdf_url}" if not pdf_url.startswith('http') else pdf_url
                        if _download_pdf(full_url, dest):
                            filing_id = save_filing(company_id, 'bse_filing', 'current', full_url, str(dest)) if company_id else None
                            filings.append({
                                'ticker': ticker_code,
                                'type': 'bse_filing',
                                'url': full_url,
                                'local_path': str(dest),
                                'filing_id': filing_id,
                                'status': 'downloaded'
                            })
                            print(f"  [OK] Downloaded BSE: {filename}")
                        time.sleep(2)
    except Exception as e:
        print(f"  [ERROR] BSE fetch failed: {e}")
    
    return filings


def fetch_from_url(url: str, ticker: str, filing_type: str, period: str, company_id: int = None) -> Dict:
    """
    Download filing from direct URL.
    
    Args:
        url: Direct PDF URL
        ticker: Stock ticker
        filing_type: Type of filing
        period: Period identifier (e.g., 'FY25', 'Q3FY25')
        company_id: Optional company ID
    
    Returns:
        Filing metadata dict
    """
    dir_path = _ensure_dir(ticker)
    filename = f"{ticker}_{filing_type}_{period.replace('/', '_')}.pdf"
    dest = dir_path / filename
    
    result = {
        'ticker': ticker,
        'type': filing_type,
        'period': period,
        'url': url,
        'local_path': None,
        'filing_id': None,
        'status': 'failed'
    }
    
    if dest.exists():
        result['status'] = 'already_exists'
        result['local_path'] = str(dest)
        print(f"  [INFO] File already exists: {filename}")
        return result
    
    if _download_pdf(url, dest):
        result['local_path'] = str(dest)
        result['status'] = 'downloaded'
        if company_id:
            result['filing_id'] = save_filing(company_id, filing_type, period, url, str(dest))
        print(f"  [OK] Downloaded: {filename}")
    
    return result


def register_local_filing(filepath: str, ticker: str, filing_type: str, period: str, company_id: int = None) -> Dict:
    """
    Register a locally downloaded filing in the database.
    This is the most important fallback when NSE/BSE scraping is blocked.
    
    Args:
        filepath: Path to local PDF file
        ticker: Stock ticker
        filing_type: Type of filing
        period: Period identifier
        company_id: Optional company ID
    
    Returns:
        Filing metadata dict
    """
    src = Path(filepath)
    if not src.exists():
        return {'status': 'error', 'message': f'File not found: {filepath}'}
    
    dir_path = _ensure_dir(ticker)
    filename = f"{ticker}_{filing_type}_{period.replace('/', '_')}.pdf"
    dest = dir_path / filename
    
    try:
        import shutil
        shutil.copy2(str(src), str(dest))
        
        filing_id = None
        if company_id:
            filing_id = save_filing(company_id, filing_type, period, None, str(dest))
        
        result = {
            'ticker': ticker,
            'type': filing_type,
            'period': period,
            'local_path': str(dest),
            'filing_id': filing_id,
            'status': 'registered'
        }
        print(f"  [OK] Registered local filing: {filename}")
        return result
        
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def get_filing_status(ticker: str, filing_type: str = None) -> List[Dict]:
    """Get status of filings for a ticker."""
    dir_path = FILINGS_DIR / ticker
    if not dir_path.exists():
        return []
    
    filings = []
    for f in dir_path.glob("*.pdf"):
        filings.append({
            'filename': f.name,
            'path': str(f),
            'size': f.stat().st_size,
            'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat()
        })
    
    return filings
