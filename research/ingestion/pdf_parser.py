"""
PDF Parser — Extract text, tables, and financial data from PDF filings
======================================================================
Uses pdfplumber for PDF extraction with institutional-grade parsing.
"""

import re
from typing import List, Dict, Optional

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

from research.storage.research_db import (
    save_metric, update_filing
)

FINANCIAL_METRICS = {
    'nim': ['net interest margin', 'nim', 'net interest income margin'],
    'cof': ['cost of funds', 'cof', 'cost of deposit'],
    'roa': ['return on assets', 'roa'],
    'roe': ['return on equity', 'roe'],
    'gnpa': ['gross npa', 'gnpa', 'gross non-performing assets'],
    'nnpa': ['net npa', 'nnpa', 'net non-performing assets'],
    'credit_cost': ['credit cost', 'loan loss', 'provisioning'],
    'opex_nti': ['opex to nti', 'opex/nti', 'operating expenses to net interest income'],
    'opex_aum': ['opex to aum', 'opex/aum', 'operating expenses to assets'],
    'pat': ['profit after tax', 'pat', 'net profit'],
    'pbt': ['profit before tax', 'pbt'],
    'nii': ['net interest income', 'nii'],
    'aum': ['aum', 'assets under management', 'total assets'],
    'nii_growth': ['nii growth', 'net interest income growth'],
    'pat_growth': ['pat growth', 'profit growth', 'net profit growth'],
    'aum_growth': ['aum growth', 'asset growth'],
}

MANAGEMENT_SECTIONS = [
    'management discussion and analysis',
    'md&a',
    "chairman's message",
    "managing director's review",
    'business overview',
    'directors report',
    'financial review',
    'operating review',
]


def extract_text(pdf_path: str) -> str:
    """
    Extract all text from PDF preserving structure.
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        Clean continuous text
    """
    if not PDFPLUMBER_AVAILABLE:
        return "[ERROR] pdfplumber not installed. Run: pip install pdfplumber"
    
    try:
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        full_text = '\n'.join(text_parts)
        full_text = re.sub(r'\n\s*\n', '\n\n', full_text)
        full_text = re.sub(r'Page \d+ of \d+', '', full_text)
        full_text = re.sub(r'\d+\s*/\s*\d+', '', full_text)
        
        return full_text.strip()
        
    except Exception as e:
        return f"[ERROR] Text extraction failed: {e}"


def extract_tables(pdf_path: str) -> List[Dict]:
    """
    Extract all tables from PDF.
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        List of table dicts with page, headers, rows, raw
    """
    if not PDFPLUMBER_AVAILABLE:
        return []
    
    tables = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_tables = page.extract_tables()
                for table in page_tables:
                    if table and len(table) > 1:
                        headers = [str(h).strip().lower() for h in table[0]] if table[0] else []
                        rows = []
                        for row in table[1:]:
                            cleaned = []
                            for cell in row:
                                if cell is None:
                                    cleaned.append('')
                                else:
                                    cleaned.append(str(cell).strip())
                            rows.append(cleaned)
                        
                        tables.append({
                            'page': page_num,
                            'headers': headers,
                            'rows': rows,
                            'raw': table
                        })
    except Exception as e:
        print(f"  [ERROR] Table extraction failed: {e}")
    
    return tables


def _parse_numeric(value: str) -> Optional[float]:
    """Convert string to float, handling percentages and commas."""
    if not value:
        return None
    value = str(value).strip().replace(',', '')
    if value.endswith('%'):
        try:
            return float(value[:-1])
        except ValueError:
            return None
    try:
        return float(value)
    except ValueError:
        return None


def extract_financial_tables(pdf_path: str, company_id: int, filing_id: int = None) -> List[Dict]:
    """
    Extract financial metrics from tables and save to database.
    
    Args:
        pdf_path: Path to PDF file
        company_id: Company ID for database
        filing_id: Optional filing ID
    
    Returns:
        List of extracted metrics
    """
    tables = extract_tables(pdf_path)
    extracted = []
    
    for table in tables:
        headers = table['headers']
        rows = table['rows']
        
        period_cols = []
        for i, h in enumerate(headers):
            if re.search(r'(FY\d{2}|Q\d|FY\s*\d{4})', h, re.IGNORECASE):
                period_cols.append(i)
        
        if not period_cols:
            for i, h in enumerate(headers):
                if re.search(r'\d{4}', h):
                    period_cols.append(i)
        
        for row in rows:
            if not row:
                continue
            
            row_label = str(row[0]).lower().strip() if row else ''
            
            for metric_key, aliases in FINANCIAL_METRICS.items():
                if any(alias in row_label for alias in aliases):
                    for col_idx in period_cols:
                        if col_idx < len(row):
                            value = _parse_numeric(row[col_idx])
                            if value is not None:
                                period = headers[col_idx] if col_idx < len(headers) else 'unknown'
                                period = re.sub(r'[^\w\s]', '', period).strip()
                                if not period:
                                    period = 'FY'
                                
                                unit = 'percent' if '%' in str(row[col_idx]) else 'ratio'
                                
                                save_metric(company_id, metric_key.upper(), period, value, unit, filing_id)
                                extracted.append({
                                    'metric': metric_key.upper(),
                                    'period': period,
                                    'value': value,
                                    'unit': unit
                                })
    
    return extracted


def extract_management_commentary(pdf_path: str) -> str:
    """
    Extract management discussion sections from PDF.
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        Concatenated commentary text
    """
    text = extract_text(pdf_path)
    if text.startswith('[ERROR]'):
        return text
    
    commentary = []
    text_lower = text.lower()
    
    for section in MANAGEMENT_SECTIONS:
        pattern = re.compile(rf'{re.escape(section)}.*?(?=\n\s*\n[A-Z]|\Z)', re.IGNORECASE | re.DOTALL)
        matches = pattern.findall(text)
        if matches:
            for match in matches:
                if len(match) > 100:
                    commentary.append(match.strip())
    
    if not commentary:
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if any(s in line.lower() for s in ['outlook', 'guidance', 'expect', 'anticipate', 'project']):
                start = max(0, i - 2)
                end = min(len(lines), i + 5)
                commentary.append('\n'.join(lines[start:end]))
    
    return '\n\n---\n\n'.join(commentary) if commentary else text[:2000]


def process_filing(filing_id: int, pdf_path: str, company_id: int) -> Dict:
    """
    Master function that runs full extraction pipeline.
    
    Args:
        filing_id: Filing ID in database
        pdf_path: Path to PDF file
        company_id: Company ID
    
    Returns:
        Summary of extraction
    """
    result = {
        'text_length': 0,
        'tables_count': 0,
        'metrics_extracted': 0,
        'commentary_length': 0,
        'status': 'success'
    }
    
    try:
        text = extract_text(pdf_path)
        result['text_length'] = len(text)
        update_filing(filing_id, extracted_text=text)
        
        tables = extract_tables(pdf_path)
        result['tables_count'] = len(tables)
        
        metrics = extract_financial_tables(pdf_path, company_id, filing_id)
        result['metrics_extracted'] = len(metrics)
        
        commentary = extract_management_commentary(pdf_path)
        result['commentary_length'] = len(commentary)
        
        update_filing(filing_id, status='processed')
        
    except Exception as e:
        result['status'] = f'error: {e}'
        update_filing(filing_id, status=f'error: {e}')
    
    return result
