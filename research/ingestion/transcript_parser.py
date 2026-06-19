"""
Transcript Parser — Earnings call transcript parser
=====================================================
Extracts structured information from earnings call transcripts.
Handles both text files and PDFs.
"""

import re
from typing import List, Dict

from research.ingestion.pdf_parser import extract_text

GUIDANCE_PATTERNS = [
    r'we expect', r'we estimate', r'we guide', r'guidance',
    r'we target', r'corridor of', r'in the range of',
    r'we anticipate', r'outlook', r'we project',
    r'we foresee', r'we are confident', r'we remain confident',
]

METRIC_PATTERNS = {
    'NIM': r'(?:net interest margin|nim)\s*(?:of|at|is|was|to be)?\s*([\d.]+)\s*(?:%|percent|bps)?',
    'ROA': r'(?:return on assets|roa)\s*(?:of|at|is|was|to be)?\s*([\d.]+)\s*(?:%|percent|bps)?',
    'ROE': r'(?:return on equity|roe)\s*(?:of|at|is|was|to be)?\s*([\d.]+)\s*(?:%|percent|bps)?',
    'AUM': r'(?:aum|assets under management)\s*(?:of|at|is|was|to be)?\s*([\d.]+)\s*(?:cr|crore|billion|mn)?',
    'CREDIT_COST': r'(?:credit cost|loan loss)\s*(?:of|at|is|was|to be)?\s*([\d.]+)\s*(?:%|percent|bps)?',
    'COF': r'(?:cost of funds|cof)\s*(?:of|at|is|was|to be)?\s*([\d.]+)\s*(?:%|percent|bps)?',
    'GNPA': r'(?:gross npa|gnpa)\s*(?:of|at|is|was|to be)?\s*([\d.]+)\s*(?:%|percent|bps)?',
    'NNPA': r'(?:net npa|nnpa)\s*(?:of|at|is|was|to be)?\s*([\d.]+)\s*(?:%|percent|bps)?',
    'PAT': r'(?:pat|profit after tax|net profit)\s*(?:of|at|is|was|to be)?\s*([\d.]+)\s*(?:cr|crore|billion|mn)?',
    'NII': r'(?:nii|net interest income)\s*(?:of|at|is|was|to be)?\s*([\d.]+)\s*(?:cr|crore|billion|mn)?',
}

MANAGEMENT_TITLES = [
    'md', 'ceo', 'cfo', 'chairman', 'managing director',
    'chief', 'director', 'president', 'executive',
]

ANALYST_PATTERNS = [
    r'analyst', r'question', r'from', r'(?:morgan|goldman|jp|citi|hsbc|icici|kotak|hdfc|axis)',
]


def parse_transcript(filepath: str) -> Dict:
    """
    Parse earnings transcript into structured dict.
    
    Args:
        filepath: Path to transcript file (txt or pdf)
    
    Returns:
        Structured transcript dict
    """
    result = {
        'company': '',
        'period': '',
        'date': '',
        'management_statements': [],
        'guidance_statements': [],
        'analyst_questions': [],
        'management_responses': [],
        'key_metrics_mentioned': {},
        'forward_statements': []
    }
    
    try:
        if filepath.endswith('.pdf'):
            text = extract_text(filepath)
        else:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            is_management = any(t in line.lower() for t in MANAGEMENT_TITLES)
            is_analyst = any(re.search(p, line, re.IGNORECASE) for p in ANALYST_PATTERNS)
            
            if is_management:
                result['management_statements'].append(line)
                
                if any(re.search(p, line, re.IGNORECASE) for p in GUIDANCE_PATTERNS):
                    result['guidance_statements'].append(line)
                
                for metric, pattern in METRIC_PATTERNS.items():
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        result['key_metrics_mentioned'][metric] = match.group(1)
            
            elif is_analyst:
                result['analyst_questions'].append(line)
            
            if any(p in line.lower() for p in ['expect', 'estimate', 'guide', 'target', 'project', 'outlook']):
                result['forward_statements'].append(line)
        
        if not result['company']:
            match = re.search(r'([A-Z]{2,})\s*(?:limited|ltd|corp|corporation)', text, re.IGNORECASE)
            if match:
                result['company'] = match.group(1)
        
        period_match = re.search(r'(Q\d\s*FY\d{2}|\w+\s+\d{4})', text)
        if period_match:
            result['period'] = period_match.group(1)
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


def extract_guidance_claims(transcript_dict: Dict) -> List[Dict]:
    """
    Extract guidance claims from parsed transcript.
    
    Args:
        transcript_dict: Parsed transcript dict
    
    Returns:
        List of guidance claim dicts
    """
    claims = []
    
    for stmt in transcript_dict.get('guidance_statements', []):
        confidence = 'aspirational'
        if any(w in stmt.lower() for w in ['will', 'definitely', 'certain', 'committed']):
            confidence = 'definitive'
        elif any(w in stmt.lower() for w in ['expect', 'estimate', 'project', 'anticipate']):
            confidence = 'conditional'
        
        metric = 'general'
        for m in METRIC_PATTERNS.keys():
            if m.lower() in stmt.lower():
                metric = m
                break
        
        claims.append({
            'metric': metric,
            'guided_value': transcript_dict.get('key_metrics_mentioned', {}).get(metric, ''),
            'period': transcript_dict.get('period', ''),
            'exact_statement': stmt[:200],
            'speaker': 'management',
            'confidence': confidence
        })
    
    return claims


def parse_transcript_file(filepath: str) -> Dict:
    """
    Full transcript parsing pipeline.
    
    Args:
        filepath: Path to transcript file
    
    Returns:
        Complete parsed transcript with guidance
    """
    transcript = parse_transcript(filepath)
    transcript['guidance_claims'] = extract_guidance_claims(transcript)
    return transcript
