from database import IntegrityError, OperationalError, DatabaseError, get_connection
import os
from collections import defaultdict

patterns = [
    "import sqlite3",
    "sqlite3.connect",
    "sqlite3.Row",
    "IntegrityError",
    "OperationalError",
    "db",
    "db",
    "db",
    "db"
]

results = []
file_counts = defaultdict(lambda: {"total": 0, "A": 0, "B": 0, "C": 0, "D": 0, "E": 0})
cat_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}

for root, _, files in os.walk('.'):
    if '.git' in root or '__pycache__' in root or 'venv' in root or 'sqlite_archive' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            path_lower = path.lower()
            
            # Match the EXACT filtering from the first script to isolate the 246 RUNTIME_PRODUCTION files
            if "archive" in path_lower or "migration" in path_lower or "sqlite" in path_lower or "seed_db.py" in path_lower or "scripts" in path_lower:
                continue
            if "test" in path_lower:
                continue
            if "dry_run" in path_lower:
                continue
                
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f, 1):
                        for p in patterns:
                            if p in line:
                                # We have a hit. Now classify it.
                                line_lower = line.lower()
                                
                                # D: database.py legacy
                                if "database.py" in path_lower:
                                    cat = "D"
                                # B: Exception compatibility
                                elif "sqlite3.integrityerror" in line_lower or "sqlite3.operationalerror" in line_lower:
                                    cat = "B"
                                # C: Import only
                                elif "import sqlite3" in line_lower or "from sqlite3" in line_lower:
                                    cat = "C"
                                # E: False positive (commented out)
                                elif line.strip().startswith("#"):
                                    cat = "E"
                                # A: Direct database access (sqlite3.connect, sqlite3.Row, .db)
                                else:
                                    cat = "A"
                                    
                                results.append({
                                    "path": path,
                                    "line": i,
                                    "snippet": line.strip(),
                                    "cat": cat,
                                    "pattern": p
                                })
                                
                                cat_counts[cat] += 1
                                file_counts[path]["total"] += 1
                                file_counts[path][cat] += 1
                                
                                break # avoid double counting same line
            except Exception:
                pass

print(f"Total: {len(results)}")
print(f"A: {cat_counts['A']} B: {cat_counts['B']} C: {cat_counts['C']} D: {cat_counts['D']} E: {cat_counts['E']}")

top_files = sorted(file_counts.items(), key=lambda x: x[1]['total'], reverse=True)[:20]

md = ["# Exact Dependency Breakdown Report\n"]

md.append("## Phase 3 - Counts")
md.append(f"- Category A Count: {cat_counts['A']}")
md.append(f"- Category B Count: {cat_counts['B']}")
md.append(f"- Category C Count: {cat_counts['C']}")
md.append(f"- Category D Count: {cat_counts['D']}")
md.append(f"- Category E Count: {cat_counts['E']}")
md.append(f"**Verify:** A+B+C+D+E = {sum(cat_counts.values())}\n")

md.append("## Phase 6 - Top Blockers")
for f, data in top_files:
    mix = f"A:{data['A']} B:{data['B']} C:{data['C']} D:{data['D']} E:{data['E']}"
    risk = "HIGH" if data['A'] > 0 else ("MEDIUM" if data['B'] > 0 else "LOW")
    md.append(f"- File: {f} | Count: {data['total']} | Mix: {mix} | Risk: {risk}")
    
with open('EXACT_BREAKDOWN.md', 'w') as f:
    f.write('\n'.join(md))

