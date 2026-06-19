from database import IntegrityError, OperationalError, DatabaseError
import os

patterns = [
    "import sqlite3",
    "sqlite3.connect",
    "sqlite3.Row",
    "IntegrityError",
    "OperationalError",
    "db",
    "db",
    "db",
    "db",
    "PRAGMA",
    "AUTOINCREMENT"
]

breakdown = {
    "A": {"count": 0, "files": set(), "risk": "HIGH", "desc": "Direct Database Access"},
    "B": {"count": 0, "files": set(), "risk": "MEDIUM", "desc": "Exception Compatibility"},
    "C": {"count": 0, "files": set(), "risk": "LOW", "desc": "Import Only"},
    "D": {"count": 0, "files": set(), "risk": "LOW", "desc": "Legacy Compatibility Layer"},
    "E": {"count": 0, "files": set(), "risk": "LOW", "desc": "False Positive"}
}

def classify_dep(path, line):
    path_lower = path.lower()
    line_lower = line.lower()
    
    if "archive" in path_lower or "migration" in path_lower or "scripts" in path_lower or "test" in path_lower or "dry_run" in path_lower or "seed_db.py" in path_lower:
        return None # Ignore non-production files

    if "database.py" in path_lower:
        return "D"
        
    if "sqlite3.connect" in line_lower or "sqlite3.row" in line_lower or "pragma " in line_lower or ".db" in line_lower or "autoincrement" in line_lower:
        # Wait, if we already replaced sqlite3.connect with get_connection, it might be in comments.
        if line.strip().startswith("#"):
            return "E"
        # However, earlier I found  in the codebase.
        # sqlite3.Row assignment is direct DB access compatibility.
        if "sqlite3.row" in line_lower:
            return "A"
        if ".db" in line_lower:
            return "A"
            
    if "sqlite3.integrityerror" in line_lower or "sqlite3.operationalerror" in line_lower:
        return "B"
        
    if "import sqlite3" in line_lower or "from sqlite3" in line_lower:
        # Check if the file actually uses sqlite3
        return "C"
        
    return "E"

# Walk
for root, _, files in os.walk('.'):
    if '.git' in root or '__pycache__' in root or 'venv' in root or 'sqlite_archive' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f, 1):
                        for p in patterns:
                            # Use exact matches as requested by previous phase pattern logic
                            if p in line:
                                cl = classify_dep(path, line)
                                if cl:
                                    breakdown[cl]["count"] += 1
                                    breakdown[cl]["files"].add(path)
                                break
            except Exception:
                pass

md = ["# SQLite Dependency Breakdown Report\n"]

for cat, data in breakdown.items():
    md.append(f"## CATEGORY {cat}: {data['desc']}")
    md.append(f"- **Count:** {data['count']}")
    md.append(f"- **Risk:** {data['risk']}")
    md.append(f"- **Files ({len(data['files'])}):**")
    for f in sorted(list(data['files'])):
        md.append(f"  - {f}")
    md.append("")
    
with open('SQLITE_DEPENDENCY_BREAKDOWN.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(md))

print(f"A: {breakdown['A']['count']} B: {breakdown['B']['count']} C: {breakdown['C']['count']} D: {breakdown['D']['count']} E: {breakdown['E']['count']}")
