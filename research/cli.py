"""
CLI Interface — Command-line interface for Sovereign Alpha Research Engine
==========================================================================
Provides simple commands for running the research pipeline.
"""

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

console = Console()

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from research.engine import SovereignAlphaResearch


def cmd_add_company(args):
    """Add a company to the database."""
    engine = SovereignAlphaResearch()
    company_id = engine.add_company(
        args.ticker, args.name,
        exchange=args.exchange or 'NSE',
        sector=args.sector
    )
    console.print(f"[green]Company added with ID: {company_id}[/green]")


def cmd_ingest(args):
    """Ingest a filing."""
    engine = SovereignAlphaResearch()
    
    if args.url:
        result = engine.ingest_filing(args.ticker, args.url, args.type, args.period)
    elif args.file:
        result = engine.ingest_filing(args.ticker, args.file, args.type, args.period)
    else:
        console.print("[red]Error: Provide either --file or --url[/red]")
        return
    
    console.print(f"Status: {result.get('status', 'unknown')}")
    if 'extraction' in result:
        ext = result['extraction']
        console.print(f"  Text: {ext.get('text_length', 0)} chars")
        console.print(f"  Tables: {ext.get('tables_count', 0)}")
        console.print(f"  Metrics: {ext.get('metrics_extracted', 0)}")


def cmd_analyze(args):
    """Run analysis for a ticker."""
    engine = SovereignAlphaResearch()
    result = engine.run_analysis(
        args.ticker,
        current_pe=args.pe,
        current_pbv=args.pbv
    )
    
    if 'error' in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return
    
    scores = result.get('steps', {}).get('scores', {})
    if scores:
        from research.intelligence.scorer import format_scorecard
        console.print(Panel(format_scorecard(scores), title="Scorecard", border_style="green"))
    
    flags = result.get('steps', {}).get('forensic_detection', {})
    if flags.get('total_flags'):
        console.print(f"[yellow]Forensic flags: {flags['total_flags']}[/yellow]")
        for sev, count in flags.get('severity_summary', {}).items():
            if count:
                console.print(f"  {sev}: {count}")


def cmd_generate_note(args):
    """Generate research note."""
    engine = SovereignAlphaResearch()
    result = engine.generate_note(args.ticker, args.context or '')
    
    if 'error' in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return
    
    console.print(f"[green]Note: {result.get('reference', 'N/A')}[/green]")
    console.print(f"HTML: {result.get('html_path', 'N/A')}")
    if result.get('pdf_path'):
        console.print(f"PDF: {result.get('pdf_path')}")


def cmd_full_pipeline(args):
    """Run complete pipeline."""
    engine = SovereignAlphaResearch()
    
    filings = []
    if args.filings:
        with open(args.filings, 'r') as f:
            filings = json.load(f)
    
    result = engine.full_pipeline(
        args.ticker, filings,
        current_pe=args.pe,
        current_pbv=args.pbv
    )
    
    console.print(f"[green]Pipeline complete: {result}[/green]")


def cmd_status(args):
    """Show status for a ticker."""
    engine = SovereignAlphaResearch()
    engine.status(args.ticker)


def main():
    parser = argparse.ArgumentParser(
        description='Sovereign Alpha Research Engine CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python research/cli.py add-company BAJFINANCE "Bajaj Finance Limited" --sector NBFC
  python research/cli.py ingest BAJFINANCE --file annual_report.pdf --type annual_report --period FY25
  python research/cli.py analyze BAJFINANCE --pe 29.2 --pbv 4.6
  python research/cli.py generate-note BAJFINANCE --context "Value-oriented holder"
  python research/cli.py full-pipeline BAJFINANCE --filings filings.json --pe 29.2 --pbv 4.6
  python research/cli.py status BAJFINANCE
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # add-company
    p_add = subparsers.add_parser('add-company', help='Add a company')
    p_add.add_argument('ticker', help='Stock ticker')
    p_add.add_argument('name', help='Company name')
    p_add.add_argument('--exchange', default='NSE', help='Exchange')
    p_add.add_argument('--sector', help='Sector')
    p_add.set_defaults(func=cmd_add_company)
    
    # ingest
    p_ingest = subparsers.add_parser('ingest', help='Ingest a filing')
    p_ingest.add_argument('ticker', help='Stock ticker')
    p_ingest.add_argument('--file', help='Local file path')
    p_ingest.add_argument('--url', help='Filing URL')
    p_ingest.add_argument('--type', default='annual_report', help='Filing type')
    p_ingest.add_argument('--period', default='current', help='Period')
    p_ingest.set_defaults(func=cmd_ingest)
    
    # analyze
    p_analyze = subparsers.add_parser('analyze', help='Run analysis')
    p_analyze.add_argument('ticker', help='Stock ticker')
    p_analyze.add_argument('--pe', type=float, help='Current P/E')
    p_analyze.add_argument('--pbv', type=float, help='Current P/BV')
    p_analyze.set_defaults(func=cmd_analyze)
    
    # generate-note
    p_note = subparsers.add_parser('generate-note', help='Generate research note')
    p_note.add_argument('ticker', help='Stock ticker')
    p_note.add_argument('--context', help='Analyst context')
    p_note.set_defaults(func=cmd_generate_note)
    
    # full-pipeline
    p_full = subparsers.add_parser('full-pipeline', help='Run complete pipeline')
    p_full.add_argument('ticker', help='Stock ticker')
    p_full.add_argument('--filings', help='JSON file with filings list')
    p_full.add_argument('--pe', type=float, help='Current P/E')
    p_full.add_argument('--pbv', type=float, help='Current P/BV')
    p_full.set_defaults(func=cmd_full_pipeline)
    
    # status
    p_status = subparsers.add_parser('status', help='Show company status')
    p_status.add_argument('ticker', help='Stock ticker')
    p_status.set_defaults(func=cmd_status)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == '__main__':
    main()
