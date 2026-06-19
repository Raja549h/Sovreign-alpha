import os
import re

def build_dependency_graph():
    code_dirs = ['agents', 'automation', 'backtesting', 'billing', 'blockchain', 'dashboard', 'engine', 'rag', 'research', 'zkml']
    tables = [
        'prediction_ledger', 'veto_archive', 'decisions', 'performance_log', 'inference_log', 'monthly_summary',
        'companies', 'filings', 'financial_series', 'forensic_flags', 'research_notes', 'institutional_scores',
        'nsdl_fpi_flows', 'fii_flows', 'fii_flow_snapshots', 'edge_scorecard', 'watchlist', 'observation_memory',
        'observation_validations', 'evidence_timeline', 'multi_source_evidence', 'framework_performance',
        'reproducibility_log', 'observation_autopsy', 'reasoning_audit', 'failure_analysis', 'calibration_history',
        'edge_discovery_framework', 'shadow_portfolio', 'shadow_trades', 'credibility_evidence', 'research_quality_metrics',
        'confidence_calibration', 'portfolios', 'portfolio_positions', 'portfolio_scores', 'portfolio_stress_results',
        'theses', 'thesis_checks', 'thesis_evolution', 'thesis_scorecard', 'observations', 'fund_params', 'fund_uploads',
        'proofs', 'performance'
    ]
    
    dependencies = {}
    
    for root_dir in code_dirs + ['.']:
        if not os.path.exists(root_dir) or not os.path.isdir(root_dir):
            if root_dir != '.':
                continue
            
        for root, _, files in os.walk(root_dir):
            for file in files:
                if not file.endswith('.py'):
                    continue
                filepath = os.path.join(root, file)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Find all SQL queries in the file
                # Simple heuristic: Look for execute( or INSERT or SELECT or UPDATE or DELETE
                # Then check if table names are in the query
                
                used_tables = set()
                for table in tables:
                    if re.search(r'\b' + table + r'\b', content, re.IGNORECASE):
                        used_tables.add(table)
                
                if used_tables:
                    mod_name = filepath.replace('\\', '/')
                    if mod_name.startswith('./'):
                        mod_name = mod_name[2:]
                    dependencies[mod_name] = used_tables
                    
    md = "# System Dependency Graph\n\n"
    for mod, used in sorted(dependencies.items()):
        md += f"### Module: `{mod}`\n"
        md += "- **Tables Touched**:\n"
        for t in sorted(used):
            md += f"  - `{t}`\n"
        md += "\n"
        
    with open('DEPENDENCY_GRAPH.md', 'w') as f:
        f.write(md)

if __name__ == '__main__':
    build_dependency_graph()
