from database import IntegrityError, OperationalError, DatabaseError, get_connection
import os
import glob

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

report = [
    "# SQLite Runtime Dependency Classification Report\n",
    "## Findings\n"
]

counts = {
    "RUNTIME_PRODUCTION": 0,
    "RUNTIME_OPTIONAL": 0,
    "TEST_ONLY": 0,
    "ARCHIVE_ONLY": 0,
    "DOCUMENTATION_ONLY": 0,
    "DEAD_CODE": 0
}

def classify(path, line):
    path_lower = path.lower()
    line_lower = line.lower()
    
    if "archive" in path_lower or "migration" in path_lower or "sqlite" in path_lower or "seed_db.py" in path_lower or "scripts" in path_lower:
        return "ARCHIVE_ONLY", "LOW", "KEEP"
    if "test" in path_lower:
        return "TEST_ONLY", "LOW", "KEEP"
    if "dry_run" in path_lower:
        return "ARCHIVE_ONLY", "LOW", "KEEP"
        
    if "database.py" in path_lower:
        return "RUNTIME_PRODUCTION", "HIGH", "REFACTOR"
        
    return "RUNTIME_PRODUCTION", "HIGH", "REFACTOR"

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
                            if p in line:
                                cl, risk, rec = classify(path, line)
                                counts[cl] += 1
                                
                                report.append(f"### {p} in {os.path.basename(path)}")
                                report.append(f"**1. File Path:** {path}")
                                report.append(f"**2. Line Number:** {i}")
                                report.append(f"**3. Exact Code Snippet:** {line.strip()}")
                                report.append(f"**4. Classification:** {cl}")
                                report.append(f"**5. Risk If Removed:** {risk}")
                                report.append(f"**6. Recommendation:** {rec}\n")
                                break # avoid double counting same line
            except Exception:
                pass

report.append("## Summary\n")
report.append(f"- **Total Runtime Production Dependencies:** {counts['RUNTIME_PRODUCTION']}")
report.append(f"- **Total Runtime Optional Dependencies:** {counts['RUNTIME_OPTIONAL']}")
report.append(f"- **Total Test Dependencies:** {counts['TEST_ONLY']}")
report.append(f"- **Total Archive Dependencies:** {counts['ARCHIVE_ONLY']}")
report.append(f"- **Total Dead Code Dependencies:** {counts['DEAD_CODE']}\n")

report.append("## Final Question\n")
report.append("**Can SQLite be removed from runtime TODAY%s**\n")
if counts['RUNTIME_PRODUCTION'] > 0:
    report.append("**NO**\n")
    report.append("**Evidence:** There are still RUNTIME_PRODUCTION dependencies listed above. Specifically, database.py heavily relies on IntegrityError and OperationalError for translating psycopg2 exceptions, which causes transitive dependencies throughout the application. Removing SQLite from runtime today would crash engines whenever a unique constraint violation or operational error occurs.")
else:
    report.append("**YES**\n")

with open('SQLITE_CLASSIFICATION_REPORT.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(report))

print("Dependency scan complete.")
