"""
Master Engine Orchestrator — Sovereign Alpha Research Engine
=============================================================
Orchestrates the full forensic research pipeline.
"""

import os
import sys
import io
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, TextColumn

console = Console(force_terminal=True, width=120)

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from research.storage.research_db import (
    init_db, get_company, add_company, get_filings_count,
    get_metrics_count, get_flags_count, get_flags_by_severity, get_notes,
    get_latest_scores
)
from research.ingestion.filing_fetcher import (
    fetch_from_url, register_local_filing
)
from research.ingestion.pdf_parser import process_filing
from research.intelligence.cross_verifier import run_full_verification
from research.intelligence.forensic_detector import run_all_detectors
from research.intelligence.regime_connector import get_regime_context
from research.intelligence.scorer import score_company, format_scorecard
from research.output.note_generator import generate_research_note
from research.output.pdf_exporter import export_note_to_pdf


class SovereignAlphaResearch:
    """Master orchestrator for the forensic research pipeline."""
    
    def __init__(self):
        """Initialize all modules and database."""
        load_dotenv()
        init_db()
        self.cerebras_key = os.environ.get('LLM_API_KEY', '')
        console.print(Panel(
            "[bold cyan]Sovereign Alpha Research Engine — Ready[/bold cyan]\n"
            f"Cerebras API: {'[green]Configured[/green]' if self.cerebras_key else '[yellow]Not configured[/yellow]'}",
            title="Research Engine",
            border_style="cyan"
        ))
    
    def add_company(self, ticker: str, name: str, exchange: str = 'NSE', sector: str = None) -> int:
        """
        Add company to database.
        
        Args:
            ticker: Stock ticker symbol
            name: Company name
            exchange: Exchange (default: NSE)
            sector: Sector classification
        
        Returns:
            Company ID
        """
        existing = get_company(ticker, exchange)
        if existing:
            console.print(f"  [yellow]Company {ticker} already exists (ID: {existing['id']})[/yellow]")
            return existing['id']
        
        company_id = add_company(ticker, name, exchange, sector)
        console.print(f"  [green]Added {name} ({ticker}) — ID: {company_id}[/green]")
        return company_id
    
    def ingest_filing(self, ticker: str, filepath_or_url: str, filing_type: str, period: str) -> Dict:
        """
        Ingest a filing (from URL or local file).
        
        Args:
            ticker: Stock ticker
            filepath_or_url: Local path or URL
            filing_type: Type of filing
            period: Period identifier
        
        Returns:
            Ingestion summary
        """
        company = get_company(ticker)
        if not company:
            return {'error': f'Company {ticker} not found. Add it first.'}
        
        company_id = company['id']
        
        if filepath_or_url.startswith('http'):
            console.print(f"  [cyan]Downloading from URL...[/cyan]")
            result = fetch_from_url(filepath_or_url, ticker, filing_type, period, company_id)
        else:
            console.print(f"  [cyan]Registering local file...[/cyan]")
            result = register_local_filing(filepath_or_url, ticker, filing_type, period, company_id)
        
        if result.get('status') in ['downloaded', 'registered'] and result.get('filing_id'):
            filing_id = result['filing_id']
            local_path = result.get('local_path', '')
            
            if local_path and Path(local_path).exists():
                console.print(f"  [cyan]Extracting data from PDF...[/cyan]")
                extraction = process_filing(filing_id, local_path, company_id)
                result['extraction'] = extraction
        
        return result
    
    def run_analysis(self, ticker: str, current_pe: float = None, current_pbv: float = None, run_id: str = None) -> Dict:
        """
        Run full analysis pipeline for a company.
        
        Args:
            ticker: Stock ticker
            current_pe: Current P/E multiple (optional)
            current_pbv: Current P/BV multiple (optional)
        
        Returns:
            Complete analysis dict
        """
        company = get_company(ticker)
        if not company:
            return {'error': f'Company {ticker} not found'}
        
        company_id = company['id']
        sector = company.get('sector', 'NBFC')
        
        analysis = {
            'ticker': ticker,
            'company': company['company_name'],
            'sector': sector,
            'steps': {}
        }
        
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running cross-verification...", total=None)
            analysis['steps']['cross_verification'] = run_full_verification(company_id)
            progress.update(task, description="Cross-verification complete")
            
            task = progress.add_task("Running forensic detectors...", total=None)
            analysis['steps']['forensic_detection'] = run_all_detectors(
                company_id, current_pe=current_pe, current_pbv=current_pbv
            )
            progress.update(task, description="Forensic detection complete")
            
            task = progress.add_task("Assessing regime sensitivity...", total=None)
            analysis['steps']['regime_context'] = get_regime_context()
            progress.update(task, description="Regime assessment complete")
            
            task = progress.add_task("Calculating institutional scores...", total=None)
            analysis['steps']['scores'] = score_company(company_id, sector, run_id=run_id)
            progress.update(task, description="Scoring complete")
        
        return analysis
    
    def generate_note(self, ticker: str, analyst_context: str = '', run_id: str = None) -> Dict:
        """
        Generate research note for a company.
        
        Args:
            ticker: Stock ticker
            analyst_context: Optional analyst context
        
        Returns:
            Note generation result
        """
        company = get_company(ticker)
        if not company:
            return {'error': f'Company {ticker} not found'}
        
        console.print(f"  [cyan]Generating research note for {ticker}...[/cyan]")
        result = generate_research_note(company['id'], analyst_context, run_id=run_id)
        
        if result.get('reference'):
            console.print(f"  [green]Note generated: {result['reference']}[/green]")
            console.print(f"  [dim]HTML: {result.get('html_path', 'N/A')}[/dim]")
            
            pdf_path = export_note_to_pdf(result['reference'])
            if pdf_path:
                result['pdf_path'] = pdf_path
                console.print(f"  [green]PDF exported: {pdf_path}[/green]")
        
        return result
    
    def full_pipeline(self, ticker: str, filings_list: List[Dict],
                      current_pe: float = None, current_pbv: float = None, run_id: str = None, progress_callback=None) -> Dict:
        """
        Run complete pipeline: add company, ingest filings, analyze, generate note.
        
        Args:
            ticker: Stock ticker
            filings_list: List of filing dicts with path/url, type, period
            current_pe: Current P/E multiple
            current_pbv: Current P/BV multiple
        
        Returns:
            PDF path or note reference
        """
        console.print(Panel(f"[bold]Full Pipeline — {ticker}[/bold]", border_style="cyan"))
        
        company = get_company(ticker)
        if not company:
            console.print(f"  [cyan]Adding company...[/cyan]")
            self.add_company(ticker, ticker, 'NSE', 'NBFC')
        
        for filing in filings_list:
            path_or_url = filing.get('path') or filing.get('url', '')
            filing_type = filing.get('type', 'annual_report')
            period = filing.get('period', 'current')
            
            console.print(f"  [cyan]Ingesting {filing_type} ({period})...[/cyan]")
            result = self.ingest_filing(ticker, path_or_url, filing_type, period)
            console.print(f"    Status: {result.get('status', 'unknown')}")
        
        if progress_callback: progress_callback(20, 'Running Analysis')
        console.print(f"  [cyan]Running analysis...[/cyan]")
        analysis = self.run_analysis(ticker, current_pe, current_pbv, run_id=run_id)
        
        scores = analysis.get('steps', {}).get('scores', {})
        if scores:
            console.print(Panel(format_scorecard(scores), title="Scorecard", border_style="green"))
            
        # 1. Observation
        from research.observation_registry import ObservationRegistry
        registry = ObservationRegistry()
        obs_id = registry.register_observation(
            company_id=company['id'],
            category="organic_analysis",
            observation_text="Full pipeline automated observation",
            expected_implication="Positive trajectory",
            confidence=0.8,
            source="Pipeline Test",
            metric_value=None,
            run_id=run_id
        )
        if progress_callback: progress_callback(40, 'Observation Registered')
        
        if progress_callback: progress_callback(60, 'Generating Note')
        console.print(f"  [cyan]Generating note...[/cyan]")
        note_result = self.generate_note(ticker, run_id=run_id)
        
        # 2. Prediction
        from zkml.proof_generator import create_proof_generator
        from blockchain.ledger import create_ledger
        proof_gen = create_proof_generator()
        ledger = create_ledger()
        
        comp_score = scores.get('composite_score', 0.6)
        decision = {
            'decision_id': f"ORG-{ticker}-{obs_id}",
            'agent_id': 'analyst',
            'risk_checks': {'position_size_ok': True, 'sector_limit_ok': True, 'confidence_ok': True},
            'approved': True,
            'decision_type': 'trade_approval'
        }
        proof_record = proof_gen.generate_proof(decision, decision['risk_checks'])
        ledger.log_decision(proof_record.get('commitment_hash', ''), decision)
        
        # 3. Autopsy & Timeline
        from research.evolution_quality import AutopsyEngine, EvidenceTimeline
        autopsy = AutopsyEngine()
        autopsy_scores = {
            'signal_strength': comp_score,
            'novelty_score': 0.7,
            'actionability_score': 0.8,
            'falsifiability_score': 0.9,
            'relevance_score': 0.8
        }
        if progress_callback: progress_callback(80, 'Scoring Observation Autopsy')
        autopsy_id = autopsy.score_observation(obs_id, autopsy_scores, "Organic pipeline test autopsy.", run_id=run_id)
        
        timeline = EvidenceTimeline()
        if progress_callback: progress_callback(90, 'Logging Timeline Event')
        timeline.record_event(obs_id, company['id'], "PIPELINE_EXECUTION", f"End-to-end execution for {ticker}", "Generated via full_pipeline", "NEW", "ACTIVE", "SYSTEM", run_id=run_id)
        
        if progress_callback: progress_callback(100, 'Pipeline Complete')
        
        return {
            'observation_id': obs_id,
            'autopsy_id': autopsy_id,
            'decision_id': decision['decision_id'],
            'note_reference': note_result.get('reference', 'N/A')
        }
    
    def status(self, ticker: str) -> None:
        """
        Print current status for a company.
        
        Args:
            ticker: Stock ticker
        """
        company = get_company(ticker)
        if not company:
            console.print(f"  [red]Company {ticker} not found[/red]")
            return
        
        company_id = company['id']
        
        table = Table(title=f"Research Status — {company['company_name']} ({ticker})")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Filings Ingested", str(get_filings_count(company_id)))
        table.add_row("Metrics Extracted", str(get_metrics_count(company_id)))
        table.add_row("Forensic Flags", str(get_flags_count(company_id)))
        
        severity = get_flags_by_severity(company_id)
        sev_str = ', '.join(f"{k}: {v}" for k, v in severity.items())
        table.add_row("Flag Severity", sev_str or "None")
        
        notes = get_notes(company_id)
        table.add_row("Notes Generated", str(len(notes)))
        
        scores = get_latest_scores(company_id)
        if scores:
            comp = scores.get('composite')
            comp_str = f"{float(comp):.1f}/10" if comp is not None else 'N/A'
            table.add_row("Composite Score", comp_str)
        
        console.print(table)
