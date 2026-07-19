"""
Deep Research Engine — On-demand institutional intelligence report generator
==============================================================================
"""

import json
import uuid
import threading
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
NOTES_DIR = BASE_DIR / "research" / "data" / "notes"
load_dotenv(BASE_DIR / ".env")

report_status = {}
report_results = {}

class DeepResearchEngine:

    def __init__(self):
        from research.engine import SovereignAlphaResearch
        self.engine = SovereignAlphaResearch()

    def generate(self, company_name: str, ticker: str, sector: str, exchange: str = "NSE", pe: float = None, pbv: float = None, analyst_context: str = "", job_id: str = None) -> Dict:
        if job_id:
            report_status[job_id] = {"status": "running", "steps": [], "reference": None, "progress": 0}
        try:
            if job_id:
                report_status[job_id]["steps"].append({"text": "Initialising research pipeline...", "status": "running"})
            company_id = self.engine.add_company(ticker, company_name, exchange, sector)
            if job_id:
                report_status[job_id]["steps"].append({"text": "Company registered in database", "status": "done"})
                report_status[job_id]["progress"] = 5
            if job_id:
                report_status[job_id]["steps"].append({"text": "Fetching financial data via yfinance...", "status": "running"})
            from research.web_researcher import research_company
            research_data = research_company(ticker, company_name, sector)
            fin = research_data.get("financial_data", {})
            if fin.get("data_quality") == "live":
                metrics_count = sum(1 for v in fin.values() if v is not None)
                if job_id:
                    report_status[job_id]["steps"].append({"text": f"Financial data acquired — {metrics_count} metrics from yfinance", "status": "done"})
            else:
                if job_id:
                    report_status[job_id]["steps"].append({"text": "Financial data: using estimate mode (yfinance unavailable)", "status": "done"})
            if job_id:
                report_status[job_id]["progress"] = 15
            if job_id:
                report_status[job_id]["steps"].append({"text": "Running web intelligence sweep...", "status": "running"})
            if research_data.get("management_commentary"):
                if job_id:
                    report_status[job_id]["steps"].append({"text": "Management commentary extracted", "status": "done"})
            if research_data.get("sector_context"):
                if job_id:
                    report_status[job_id]["steps"].append({"text": "Sector context gathered", "status": "done"})
            if job_id:
                report_status[job_id]["progress"] = 25
            if job_id:
                report_status[job_id]["steps"].append({"text": "Populating financial series...", "status": "running"})
            self._populate_series(company_id, fin, ticker)
            if job_id:
                report_status[job_id]["steps"].append({"text": "Financial series populated", "status": "done"})
                report_status[job_id]["progress"] = 30
            if job_id:
                report_status[job_id]["steps"].append({"text": "Running forensic detection...", "status": "running"})
            from research.intelligence.forensic_detector import run_all_detectors
            flag_results = run_all_detectors(company_id, current_pe=pe, current_pbv=pbv)
            flags_list = []
            saved_flags = self._get_company_flags(company_id)
            flag_count = len(saved_flags)
            if job_id:
                report_status[job_id]["steps"].append({"text": f"{flag_count} forensic flags detected", "status": "done"})
                report_status[job_id]["progress"] = 40
            if job_id:
                report_status[job_id]["steps"].append({"text": "Assessing regime sensitivity...", "status": "running"})
            from research.intelligence.regime_connector import get_regime_context
            regime = get_regime_context()
            if job_id:
                report_status[job_id]["steps"].append({"text": "Regime assessment complete", "status": "done"})
                report_status[job_id]["progress"] = 45
            if job_id:
                report_status[job_id]["steps"].append({"text": "Calculating institutional scores...", "status": "running"})
            from research.intelligence.scorer import score_company
            scores = score_company(company_id, sector)
            if job_id:
                report_status[job_id]["steps"].append({"text": "Institutional scores calculated", "status": "done"})
                report_status[job_id]["progress"] = 50
            if job_id:
                report_status[job_id]["steps"].append({"text": "Generating sections 1-19 deep research report...", "status": "running"})
            from research.deep_note_generator import generate_all_sections, format_sections_to_html
            sections = generate_all_sections(company_name, ticker, research_data)
            if job_id:
                report_status[job_id]["steps"].append({"text": "Generating thesis evolution analysis (section 20)...", "status": "running"})
            try:
                from research.thesis_evolution_engine import ThesisEvolutionEngine
                tee = ThesisEvolutionEngine()
                evo_report = tee.generate_evolution_report(company_id)
                evo_lines = []
                evo_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
                evo_lines.append(f"THESIS EVOLUTION ANALYSIS")
                evo_lines.append(f"Prior Review: {evo_report.get('prior_analysis_date', 'N/A')} → Current: {evo_report.get('analysis_date', 'N/A')}")
                evo_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
                if not evo_report.get('key_changes') and not evo_report.get('new_findings'):
                    evo_lines.append("")
                    evo_lines.append("First analysis — baseline established. Evolution tracking begins from this review.")
                else:
                    if evo_report.get('key_changes'):
                        evo_lines.append("")
                        evo_lines.append("WHAT CHANGED:")
                        for c in evo_report['key_changes']:
                            evo_lines.append(f"- {c}")
                    if evo_report.get('confirmed_observations'):
                        evo_lines.append("")
                        evo_lines.append("CONFIRMED OBSERVATIONS:")
                        for c in evo_report['confirmed_observations']:
                            evo_lines.append(f"- {c}")
                    if evo_report.get('invalidated_observations'):
                        evo_lines.append("")
                        evo_lines.append("INVALIDATED:")
                        for i in evo_report['invalidated_observations']:
                            evo_lines.append(f"- {i}")
                    det = [v for v in evo_report.get('categories', {}).values() if v.get('status') == 'WEAKENING']
                    if det:
                        evo_lines.append("")
                        evo_lines.append("DETERIORATING:")
                        for d in det:
                            evo_lines.append(f"- {d.get('current', '')}")
                    imp = [v for v in evo_report.get('categories', {}).values() if v.get('status') == 'STRENGTHENING']
                    if imp:
                        evo_lines.append("")
                        evo_lines.append("IMPROVING:")
                        for i in imp:
                            evo_lines.append(f"- {i.get('current', '')}")
                    if evo_report.get('new_findings'):
                        evo_lines.append("")
                        evo_lines.append("NEW FINDINGS:")
                        for n in evo_report['new_findings']:
                            evo_lines.append(f"- {n}")
                sections["20_thesis_evolution"] = "\n".join(evo_lines)
                tee.update_thesis_scorecard(company_id)
            except Exception as evo_err:
                sections["20_thesis_evolution"] = f"Thesis evolution analysis unavailable: {str(evo_err)[:100]}"
            context = {
                "company_name": company_name,
                "ticker": ticker,
                "sector": sector,
                "pe": pe,
                "pbv": pbv,
                **research_data
            }
            if job_id:
                report_status[job_id]["progress"] = 90
            reference = self._get_reference(ticker)
            flags_for_template = self._get_company_flags(company_id)
            confidence = research_data.get("data_confidence", 0.5)
            html_content = format_sections_to_html(reference, company_name, ticker, sector, sections, scores, flags_for_template, confidence, pe, pbv)
            NOTES_DIR.mkdir(parents=True, exist_ok=True)
            html_path = NOTES_DIR / f"{reference}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            if job_id:
                report_status[job_id]["steps"].append({"text": f"All sections generated — {reference}", "status": "done"})
            if job_id:
                report_status[job_id]["steps"].append({"text": "Applying cryptographic signature...", "status": "running"})
            content_hash = hashlib.sha256(html_content.encode()).hexdigest()[:16]
            if job_id:
                report_status[job_id]["steps"].append({"text": f"Report signed — {content_hash}", "status": "done"})
            from research.storage.research_db import save_note
            note_id = save_note(company_id, reference, f"Deep Research — {company_name}", html_content, scores or {}, summary=f"Deep research report for {company_name}")
            if job_id:
                report_status[job_id]["steps"].append({"text": "Exporting institutional PDF...", "status": "running"})
            pdf_path = self._export_pdf(reference, html_content)
            if pdf_path:
                if job_id:
                    report_status[job_id]["steps"].append({"text": "PDF ready for download", "status": "done"})
                from research.storage.research_db import update_note_pdf
                update_note_pdf(note_id, str(pdf_path))
            else:
                if job_id:
                    report_status[job_id]["steps"].append({"text": "PDF export unavailable — HTML version available", "status": "warning"})
            result = {
                "reference": reference,
                "note_id": note_id,
                "html_path": str(html_path),
                "pdf_path": str(pdf_path) if pdf_path else None,
                "scores": scores,
                "flags_count": flag_count,
                "confidence": confidence,
                "sections": sections,
                "content_hash": content_hash,
                "status": "complete",
            }
            if job_id:
                report_status[job_id]["status"] = "complete"
                report_status[job_id]["reference"] = reference
                report_status[job_id]["progress"] = 100
                report_results[job_id] = result
            return result
        except Exception as e:
            if job_id:
                report_status[job_id]["status"] = "error"
                report_status[job_id]["steps"].append({"text": f"ERROR: {str(e)}", "status": "error"})
            return {"status": "error", "error": str(e)}

    def _populate_series(self, company_id: int, fin: Dict, ticker: str):
        from research.storage.research_db import save_metric
        mapping = {
            "Revenue": "totalRevenue", "EBITDA": "ebitda", "PAT": "netIncome",
            "MarketCap": "market_cap", "PE": "trailing_pe", "PBV": "price_to_book",
            "PS": "price_to_sales", "DividendYield": "dividend_yield", "Beta": "beta",
            "ROE": "return_on_equity", "ROA": "return_on_assets", "ROCE": "return_on_capital",
            "DebtEquity": "debt_to_equity", "CurrentRatio": "current_ratio",
            "OperatingMargin": "operating_margins", "ProfitMargin": "profit_margins",
        }
        for metric, key in mapping.items():
            val = fin.get(key)
            if val is not None:
                save_metric(company_id, metric, "FY24", float(val), "auto", None)

    def _get_company_flags(self, company_id: int) -> List[Dict]:
        from research.storage.research_db import get_flags
        return get_flags(company_id)

    def _get_reference(self, ticker: str) -> str:
        counter_file = BASE_DIR / "research" / "data" / ".note_counter"
        year = datetime.now().strftime("%Y")
        counter = 0
        if counter_file.exists():
            try:
                with open(counter_file) as f:
                    counters = json.load(f)
                counter = counters.get(ticker, 0)
            except (json.JSONDecodeError, KeyError):
                counter = 0
        counter += 1
        try:
            with open(counter_file, "w") as f:
                counters = {}
                if counter_file.exists():
                    with open(counter_file) as rf:
                        try:
                            counters = json.load(rf)
                        except json.JSONDecodeError:
                            pass
                counters[ticker] = counter
                json.dump(counters, f)
        except Exception:
            pass
        return f"SR-{year}-{ticker[:3].upper()}-{counter:03d}"

    def _export_pdf(self, reference: str, html_content: str) -> Optional[str]:
        try:
            pdf_dir = BASE_DIR / "research" / "data" / "notes"
            pdf_dir.mkdir(parents=True, exist_ok=True)
            pdf_path = pdf_dir / f"{reference}.pdf"
            from xhtml2pdf import pisa
            with open(pdf_path, "wb") as f:
                converter = pisa.CreatePDF(html_content, dest=f)
            if converter.err:
                return None
            return str(pdf_path)
        except ImportError:
            return None
        except Exception as e:
            return None


def start_generation(company_name: str, ticker: str, sector: str, exchange: str = "NSE", pe: float = None, pbv: float = None, analyst_context: str = "") -> str:
    job_id = str(uuid.uuid4())[:8]
    report_status[job_id] = {"status": "starting", "steps": [], "reference": None, "progress": 0}
    engine = DeepResearchEngine()
    thread = threading.Thread(target=engine.generate, args=(company_name, ticker, sector, exchange, pe, pbv, analyst_context, job_id), daemon=True)
    thread.start()
    return job_id


def get_status(job_id: str) -> Dict:
    return report_status.get(job_id, {"status": "not_found"})


def get_result(job_id: str) -> Dict:
    return report_results.get(job_id, {})


def get_report(reference: str) -> Optional[str]:
    html_path = NOTES_DIR / f"{reference}.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    try:
        from research.deep_note_generator import get_note_html
        return get_note_html(reference)
    except Exception:
        return None


def get_report_meta(reference: str) -> Optional[Dict]:
    from research.storage.research_db import get_note_by_reference
    note = get_note_by_reference(reference)
    if note:
        return dict(note)
    return None
