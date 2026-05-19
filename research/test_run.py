"""
Test Run — Populate database with Bajaj Finance data and verify pipeline
========================================================================
Uses real Bajaj Finance financial data to test the full research pipeline.
"""

import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from research.storage.research_db import (
    init_db, add_company, get_company, save_metric, save_flag,
    get_company_by_id
)
from research.engine import SovereignAlphaResearch


def populate_bajaj_finance():
    """Populate database with Bajaj Finance test data."""
    console.print(Panel("[bold]Step 1: Adding Bajaj Finance[/bold]", border_style="cyan"))
    
    company_id = add_company('BAJFINANCE', 'Bajaj Finance Limited', 'NSE', 'NBFC')
    console.print(f"  [green]Company ID: {company_id}[/green]")
    
    console.print(Panel("[bold]Step 2: Populating Financial Series[/bold]", border_style="cyan"))
    
    metrics = {
        'NIM': [('FY23', 10.8, 'percent'), ('FY24', 10.1, 'percent'), ('FY25', 10.1, 'percent')],
        'COF': [('FY23', 7.04, 'percent'), ('FY24', 7.74, 'percent'), ('FY25', 7.99, 'percent')],
        'ROA': [('FY23', 4.2, 'percent'), ('FY24', 3.86, 'percent'), ('FY25', 3.58, 'percent')],
        'ROE': [('FY23', 22.5, 'percent'), ('FY24', 19.1, 'percent'), ('FY25', 17.4, 'percent')],
        'GNPA': [('FY23', 1.2, 'percent'), ('FY24', 0.85, 'percent'), ('FY25', 1.0, 'percent')],
        'NNPA': [('FY23', 0.4, 'percent'), ('FY24', 0.37, 'percent'), ('FY25', 0.44, 'percent')],
        'CREDIT_COST': [('FY23', 1.25, 'percent'), ('FY24', 1.63, 'percent'), ('FY25', 2.05, 'percent')],
        'OPEX_NTI': [('FY23', 25.7, 'percent'), ('FY24', 24.0, 'percent'), ('FY25', 20.8, 'percent')],
        'OPEX_AUM': [('FY23', 4.18, 'percent'), ('FY24', 3.86, 'percent'), ('FY25', 3.66, 'percent')],
        'PAT_GROWTH': [('FY24', 25.6, 'percent'), ('FY25', 15.1, 'percent')],
        'AUM_GROWTH': [('FY24', 34.0, 'percent'), ('FY25', 28.0, 'percent')],
        'NII_GROWTH': [('FY24', 25.7, 'percent'), ('FY25', 23.8, 'percent')],
        'INT_EXP_GROWTH': [('FY24', 48.7, 'percent'), ('FY25', 32.3, 'percent')],
    }
    
    total_metrics = 0
    for metric, values in metrics.items():
        for period, value, unit in values:
            save_metric(company_id, metric, period, value, unit)
            total_metrics += 1
    
    console.print(f"  [green]Populated {total_metrics} metric entries[/green]")
    
    console.print(Panel("[bold]Step 3: Adding Sample Forensic Flags[/bold]", border_style="cyan"))
    
    save_flag(company_id, 'credit_cost_acceleration', 'high',
             'Credit cost accelerated 64% from FY23 to FY25 (1.25% → 2.05%)',
             {'fy23': 1.25, 'fy25': 2.05, 'change_pct': 64}, 'FY25')
    console.print("  [yellow][HIGH] credit_cost_acceleration[/yellow]")
    
    save_flag(company_id, 'margin_compression', 'medium',
             'NIM compressed 70 bps from FY23 to FY25 (10.8% → 10.1%)',
             {'fy23': 10.8, 'fy25': 10.1, 'compression_bps': 70}, 'FY25')
    console.print("  [yellow][MEDIUM] margin_compression[/yellow]")
    
    save_flag(company_id, 'guidance_divergence', 'high',
             'Credit cost guidance diverged from actual trajectory',
             {'metric': 'CREDIT_COST', 'divergence': 'actual exceeded guidance'}, 'FY25')
    console.print("  [yellow][HIGH] guidance_divergence[/yellow]")
    
    save_flag(company_id, 'roe_decline', 'medium',
             'ROE declined 510 bps from FY23 to FY25 (22.5% → 17.4%)',
             {'fy23': 22.5, 'fy25': 17.4, 'decline_bps': 510}, 'FY25')
    console.print("  [yellow][MEDIUM] roe_decline[/yellow]")
    
    console.print(Panel("[bold]Step 4: Running Full Analysis Pipeline[/bold]", border_style="cyan"))
    
    engine = SovereignAlphaResearch()
    analysis = engine.run_analysis('BAJFINANCE', current_pe=29.2, current_pbv=4.6)
    
    if 'error' in analysis:
        console.print(f"  [red]Analysis error: {analysis['error']}[/red]")
        return None
    
    scores = analysis.get('steps', {}).get('scores', {})
    if scores:
        from research.intelligence.scorer import format_scorecard
        console.print(Panel(format_scorecard(scores), title="Scorecard", border_style="green"))
    
    console.print(Panel("[bold]Step 5: Generating Research Note[/bold]", border_style="cyan"))
    
    note_result = engine.generate_note('BAJFINANCE',
        analyst_context='Value-oriented concentrated NBFC holder')
    
    if 'error' in note_result:
        console.print(f"  [red]Note generation error: {note_result['error']}[/red]")
    else:
        console.print(f"  [green]Note reference: {note_result.get('reference', 'N/A')}[/green]")
        console.print(f"  [dim]HTML: {note_result.get('html_path', 'N/A')}[/dim]")
        if note_result.get('pdf_path'):
            console.print(f"  [green]PDF: {note_result.get('pdf_path')}[/green]")
    
    console.print(Panel("[bold]Step 6: Final Status[/bold]", border_style="cyan"))
    engine.status('BAJFINANCE')
    
    return note_result.get('reference')


if __name__ == '__main__':
    console.print(Panel(
        "[bold cyan]Sovereign Alpha Research Engine — Test Run[/bold cyan]\n"
        "Populating Bajaj Finance data and running full pipeline",
        border_style="cyan"
    ))
    
    reference = populate_bajaj_finance()
    
    if reference:
        console.print(Panel(
            f"[green]Test run complete![/green]\n"
            f"Note Reference: {reference}\n"
            "Check dashboard at /research for results.",
            border_style="green"
        ))
    else:
        console.print("[red]Test run encountered errors. Check output above.[/red]")
