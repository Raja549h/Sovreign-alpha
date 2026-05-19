"""
PDF Exporter — Convert HTML research notes to print-ready PDF
==============================================================
Uses xhtml2pdf for PDF generation with institutional formatting.
"""

import os
from pathlib import Path
from typing import Optional

from research.storage.research_db import get_note_by_reference, update_note_pdf

BASE_DIR = Path(__file__).parent.parent.parent
NOTES_DIR = BASE_DIR / "research" / "data" / "notes"
PDF_DIR = BASE_DIR / "research" / "data" / "notes"

PRINT_CSS = """
@page {
    size: A4;
    margin: 25mm;
    @bottom-center {
        content: "Page " counter(page) " of " counter(pages);
        font-family: 'Courier New', monospace;
        font-size: 8pt;
        color: #666;
    }
    @top-center {
        content: "Sovereign Alpha Research — Confidential";
        font-family: 'Courier New', monospace;
        font-size: 8pt;
        color: #666;
    }
}

body {
    font-family: 'Courier New', monospace;
    font-size: 10pt;
    line-height: 1.6;
    color: #1a1a1a;
    background: white;
}

h1 {
    font-size: 16pt;
    color: #0a3d6b;
    border-bottom: 2px solid #0a3d6b;
    padding-bottom: 8px;
    margin-bottom: 20px;
}

h2 {
    font-size: 13pt;
    color: #1a5a8b;
    margin-top: 24px;
    margin-bottom: 12px;
}

h3 {
    font-size: 11pt;
    color: #2a6a9b;
    margin-top: 18px;
    margin-bottom: 8px;
}

.scorecard {
    background: #f0f4f8;
    border: 1px solid #d0d8e0;
    padding: 15px;
    margin: 15px 0;
}

.scorecard table {
    width: 100%;
    border-collapse: collapse;
}

.scorecard td {
    padding: 6px 10px;
    border-bottom: 1px solid #d0d8e0;
}

.flags {
    background: #f8f4f0;
    border: 1px solid #e0d8d0;
    padding: 15px;
    margin: 15px 0;
}

.flag-high {
    color: #c0392b;
    font-weight: bold;
}

.flag-medium {
    color: #d4a017;
}

.flag-low {
    color: #27ae60;
}

.meta {
    color: #666;
    font-size: 9pt;
    margin-bottom: 20px;
}

.hash {
    color: #0a3d6b;
    font-size: 8pt;
    margin-top: 30px;
    padding-top: 10px;
    border-top: 1px solid #ddd;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 10px 0;
}

th, td {
    border: 1px solid #ddd;
    padding: 6px 10px;
    text-align: left;
}

th {
    background: #f0f4f8;
    font-weight: bold;
}
"""


def export_to_pdf(html_path: str, output_path: str) -> str:
    """
    Convert HTML file to print-ready PDF.
    
    Args:
        html_path: Path to HTML file
        output_path: Path for output PDF
    
    Returns:
        Output PDF path
    """
    try:
        from xhtml2pdf import pisa
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        with open(output_path, 'wb') as f:
            converter = pisa.CreatePDF(html_content, dest=f)
        
        if converter.err:
            print(f"  [ERROR] PDF export failed with errors")
            return None
            
        return output_path
        
    except ImportError:
        print("  [WARN] xhtml2pdf not installed. Skipping PDF export.")
        print("  Install with: pip install xhtml2pdf")
        return None
    except Exception as e:
        print(f"  [ERROR] PDF export failed: {e}")
        return None


def export_note_to_pdf(note_reference: str) -> Optional[str]:
    """
    Export a research note to PDF by reference.
    
    Args:
        note_reference: Note reference number (e.g., SR-2026-BAF-001)
    
    Returns:
        PDF path or None
    """
    note = get_note_by_reference(note_reference)
    if not note:
        print(f"  [ERROR] Note {note_reference} not found")
        return None
    
    html_content = note.get('full_content', '')
    if not html_content:
        print(f"  [ERROR] Note {note_reference} has no content")
        return None
    
    html_path = NOTES_DIR / f"{note_reference}.html"
    pdf_path = PDF_DIR / f"{note_reference}.pdf"
    
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    result = export_to_pdf(str(html_path), str(pdf_path))
    
    if result:
        update_note_pdf(note['id'], str(pdf_path))
        print(f"  [OK] PDF exported: {pdf_path}")
    
    return result
