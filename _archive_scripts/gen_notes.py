import sys, os
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from research.storage.research_db import get_all_companies
from research.output.note_generator import generate_research_note

companies = get_all_companies()
print(f"Found {len(companies)} companies. Generating notes...")
for c in companies:
    print(f"Generating note for {c['ticker']}...")
    try:
        note = generate_research_note(c['id'])
        print(f"Success: {note.get('reference')}")
    except Exception as e:
        print(f"Failed for {c['ticker']}: {e}")
