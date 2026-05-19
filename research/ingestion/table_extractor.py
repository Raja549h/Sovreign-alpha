"""
Table Extractor — Extract financial tables from PDF filings
============================================================
This module provides table extraction functionality.
Note: Core table extraction logic is integrated into pdf_parser.py.
This module re-exports for backward compatibility.
"""

from research.ingestion.pdf_parser import (
    extract_tables,
    extract_financial_tables,
    FINANCIAL_METRICS,
    _parse_table_row,
    _identify_metric,
    _extract_value,
)


def extract_financial_table(pdf_path: str, company_id: int = None) -> list:
    """
    Extract financial tables from a PDF filing.
    
    Args:
        pdf_path: Path to PDF file
        company_id: Optional company ID to save metrics
    
    Returns:
        List of extracted table data
    """
    return extract_financial_tables(pdf_path, company_id)


def extract_table_from_page(pdf_path: str, page_num: int = 0) -> list:
    """
    Extract table from specific page of PDF.
    
    Args:
        pdf_path: Path to PDF file
        page_num: Page number (0-indexed)
    
    Returns:
        List of table rows
    """
    if not PDFPLUMBER_AVAILABLE:
        return []
    
    import pdfplumber
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_num < len(pdf.pages):
                page = pdf.pages[page_num]
                tables = page.extract_tables()
                return tables or []
    except Exception:
        pass
    return []


def save_table_metrics(tables: list, company_id: int) -> int:
    """
    Save extracted table metrics to database.
    
    Args:
        tables: List of extracted tables
        company_id: Company ID
    
    Returns:
        Number of metrics saved
    """
    saved = 0
    for table in tables:
        for row in table:
            metric = _identify_metric(row)
            if metric:
                value = _extract_value(row)
                if value is not None:
                    save_metric(company_id, metric, 'current', value, 'percent', None)
                    saved += 1
    return saved
