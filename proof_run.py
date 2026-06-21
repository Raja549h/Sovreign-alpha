import sys
import time
from pathlib import Path
from datetime import datetime

# Set path so imports work
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))

from research.engine import SovereignAlphaResearch
from database import get_connection
from dotenv import load_dotenv
load_dotenv()

def count_rows(table: str, ticker: str = None) -> int:
    with get_connection() as conn:
        c = conn.cursor()
        if ticker and table in ['companies', 'observation_memory', 'research_notes', 'institutional_scores', 'observation_autopsy', 'evidence_timeline', 'prediction_ledger']:
            if table == 'companies':
                c.execute(f"SELECT COUNT(*) as cnt FROM {table} WHERE ticker = %s", (ticker,))
            elif table == 'observation_memory':
                c.execute(f"SELECT COUNT(*) as cnt FROM {table} WHERE company_id = (SELECT id FROM companies WHERE ticker = %s LIMIT 1)", (ticker,))
            elif table == 'research_notes':
                c.execute(f"SELECT COUNT(*) as cnt FROM {table} WHERE company_id = (SELECT id FROM companies WHERE ticker = %s LIMIT 1)", (ticker,))
            elif table == 'institutional_scores':
                c.execute(f"SELECT COUNT(*) as cnt FROM {table} WHERE company_id = (SELECT id FROM companies WHERE ticker = %s LIMIT 1)", (ticker,))
            elif table == 'observation_autopsy':
                c.execute(f"SELECT COUNT(*) as cnt FROM {table} WHERE company_id = (SELECT id FROM companies WHERE ticker = %s LIMIT 1)", (ticker,))
            elif table == 'evidence_timeline':
                c.execute(f"SELECT COUNT(*) as cnt FROM {table} WHERE company_id = (SELECT id FROM companies WHERE ticker = %s LIMIT 1)", (ticker,))
            elif table == 'prediction_ledger':
                c.execute(f"SELECT COUNT(*) as cnt FROM {table} WHERE asset = %s", (ticker,))
        else:
            c.execute(f"SELECT COUNT(*) as cnt FROM {table}")
        return c.fetchone()['cnt']

def get_latest_pk(table: str) -> int:
    with get_connection() as conn:
        c = conn.cursor()
        if table == 'prediction_ledger':
             c.execute(f"SELECT prediction_id as id FROM {table} ORDER BY created_at DESC LIMIT 1")
        else:
             c.execute(f"SELECT id FROM {table} ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        return row['id'] if row else None

def main():
    ticker = "HDFCBANK"
    
    # Pre-execution counts
    counts_before = {
        'observation_memory': count_rows('observation_memory', ticker),
        'research_notes': count_rows('research_notes', ticker),
        'institutional_scores': count_rows('institutional_scores', ticker),
        'observation_autopsy': count_rows('observation_autopsy', ticker),
        'evidence_timeline': count_rows('evidence_timeline', ticker)
    }
    
    print(f"Starting organic pipeline proof for {ticker}...")
    start_time = time.time()
    
    engine = SovereignAlphaResearch()
    
    # Pass a dummy filing list to trigger analysis and note generation
    filings_list = [] 
    
    try:
        result = engine.full_pipeline(ticker=ticker, filings_list=filings_list)
        success = True
        error_msg = ""
    except Exception as e:
        import traceback
        success = False
        error_msg = str(e)
        print("Pipeline Failed!")
        traceback.print_exc()
        result = {}
        
    duration = time.time() - start_time
    
    counts_after = {
        'observation_memory': count_rows('observation_memory', ticker),
        'research_notes': count_rows('research_notes', ticker),
        'institutional_scores': count_rows('institutional_scores', ticker),
        'observation_autopsy': count_rows('observation_autopsy', ticker),
        'evidence_timeline': count_rows('evidence_timeline', ticker)
    }
    
    rows_created = {k: counts_after[k] - counts_before[k] for k in counts_after}
    
    pks = {
        'observation_memory': get_latest_pk('observation_memory'),
        'research_notes': get_latest_pk('research_notes'),
        'institutional_scores': get_latest_pk('institutional_scores'),
        'observation_autopsy': get_latest_pk('observation_autopsy'),
        'evidence_timeline': get_latest_pk('evidence_timeline')
    }
    
    report = f"""# Organic Pipeline Proof Report
**Date:** {datetime.utcnow().isoformat()}Z
**Ticker:** {ticker}

## Execution Metrics
- **Duration:** {duration:.2f} seconds
- **Success:** {success}
- **Failures:** {error_msg if not success else 'None'}

## Rows Created Natively
- `observation_memory`: {rows_created['observation_memory']} (PK: {pks['observation_memory']})
- `research_notes`: {rows_created['research_notes']} (PK: {pks['research_notes']})
- `institutional_scores`: {rows_created['institutional_scores']} (PK: {pks['institutional_scores']})
- `observation_autopsy`: {rows_created['observation_autopsy']} (PK: {pks['observation_autopsy']})
- `evidence_timeline`: {rows_created['evidence_timeline']} (PK: {pks['evidence_timeline']})

## Pipeline Output Trace
```json
{result}
```

## Verdict
{ 'YES' if all(v > 0 for v in rows_created.values()) else 'NO' }
"""

    with open(r'C:\Users\lokes\.gemini\antigravity\brain\97baeab8-58a0-45d2-a695-ce010c46102d\ORGANIC_PIPELINE_PROOF.md', 'w') as f:
        f.write(report)
        
    print(f"Proof written. Verdict: {'YES' if success else 'NO'}")

if __name__ == "__main__":
    main()
