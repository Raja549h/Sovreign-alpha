import os

files = {
    # MODIFIED
    "dashboard/app.py": ("CATEGORY D", "Decouples synchronous pipeline run into async jobs for dashboard stability", "YES"),
    "dashboard/templates/calibration.html": ("CATEGORY D", "UI fixes for calibration dashboard", "YES"),
    "dashboard/templates/edge.html": ("CATEGORY D", "UI fixes for edge dashboard", "YES"),
    "data/regime/regime_history.json": ("CATEGORY H", "System state output", "NO"),
    "database.py": ("CATEGORY B", "Thread-safe Neon pooling fixes", "YES"),
    "research/data/.note_counter": ("CATEGORY H", "System counter", "NO"),
    "research/data/notes/SR-2026-HDF-001.html": ("CATEGORY H", "Generated research note", "NO"),
    "research/engine.py": ("CATEGORY C", "Connects core pipeline to worker tracking architecture", "YES"),
    "research/evolution_quality.py": ("CATEGORY A", "Fixes for Autopsy connection handling", "YES"),
    "research/intelligence/scorer.py": ("CATEGORY A", "Fixes for scorer connection handling", "YES"),
    "research/observation_registry.py": ("CATEGORY A", "Fixes for observation creation logic", "YES"),
    "research/output/note_generator.py": ("CATEGORY A", "Fixes for note generation PDF export thread safety", "YES"),
    "research/storage/research_db.py": ("CATEGORY A", "Fixes for underlying storage architecture queries", "YES"),
    
    # UNTRACKED - NEW ARCHITECTURE
    "dashboard/templates/runs.html": ("CATEGORY D", "New UI template for tracking background jobs", "YES"),
    "dashboard/worker.py": ("CATEGORY A", "Background daemon to execute pipeline jobs asynchronously", "YES"),
    "migrate_continuous.sql": ("CATEGORY C", "Schema definitions for analysis_runs", "YES"),
    
    # UNTRACKED - SCRIPTS & TESTS
    "artifact_generator.py": ("CATEGORY G", "Script to generate markdown artifacts", "NO"),
    "artifact_generator2.py": ("CATEGORY G", "Script to generate markdown artifacts", "NO"),
    "audit_phase4.py": ("CATEGORY G", "Live API testing script", "NO"),
    "audit_script.py": ("CATEGORY G", "Live API testing script", "NO"),
    "check_db.py": ("CATEGORY E", "Database connection check script", "NO"),
    "check_results.py": ("CATEGORY E", "Continuous testing monitor", "NO"),
    "clean_db.py": ("CATEGORY G", "Cleanup utility script", "NO"),
    "proof_run.py": ("CATEGORY E", "Execution validation script", "NO"),
    "run_migration.py": ("CATEGORY G", "Local schema migration trigger", "NO"),
    "test_run2.py": ("CATEGORY E", "Validation script", "NO"),
    "test_write2.py": ("CATEGORY E", "Validation script", "NO"),
    "verify_continuous.py": ("CATEGORY E", "Validation script", "NO"),
    "verify_continuous2.py": ("CATEGORY E", "Validation script", "NO"),
    "run_me.bat": ("CATEGORY G", "Local runner script", "NO"),
    
    # UNTRACKED - ARTIFACTS
    "audit_results.json": ("CATEGORY F", "Audit metadata", "NO"),
    "verification_results.json": ("CATEGORY F", "Audit metadata", "NO"),
    "audit.log": ("CATEGORY F", "Execution logs", "NO"),
}

import glob

# Add dynamically generated blockchain and research notes to Category H
for f in glob.glob("blockchain/transactions/*.json"):
    files[f.replace("\\", "/")] = ("CATEGORY H", "Generated blockchain log", "NO")
for f in glob.glob("research/data/notes/*.html"):
    if f.replace("\\", "/") not in files:
        files[f.replace("\\", "/")] = ("CATEGORY H", "Generated research note HTML", "NO")
for f in glob.glob("research/data/notes/*.pdf"):
    files[f.replace("\\", "/")] = ("CATEGORY H", "Generated research note PDF", "NO")

# Phase 2: PRODUCTION_RELEASE_MANIFEST.md
with open("C:/Users/lokes/.gemini/antigravity/brain/97baeab8-58a0-45d2-a695-ce010c46102d/PRODUCTION_RELEASE_MANIFEST.md", "w") as f:
    f.write("# PRODUCTION RELEASE MANIFEST\n\n")
    f.write("| Path | Category | Reason | Required for Deployment |\n")
    f.write("|------|----------|--------|-------------------------|\n")
    for path, (cat, reason, req) in sorted(files.items()):
        f.write(f"| `{path}` | {cat} | {reason} | {req} |\n")

# Phase 3: SAFE_COMMIT_SET.md
safe_files = [path for path, (_, _, req) in files.items() if req == "YES"]
with open("C:/Users/lokes/.gemini/antigravity/brain/97baeab8-58a0-45d2-a695-ce010c46102d/SAFE_COMMIT_SET.md", "w") as f:
    f.write("# SAFE COMMIT SET\n\n")
    f.write("The following files MUST be committed to resolve live HF 500 errors and enable continuous execution.\n\n")
    for path in sorted(safe_files):
        f.write(f"- `{path}`\n")

# Phase 4: DO_NOT_COMMIT.md
unsafe_files = [path for path, (_, _, req) in files.items() if req == "NO"]
with open("C:/Users/lokes/.gemini/antigravity/brain/97baeab8-58a0-45d2-a695-ce010c46102d/DO_NOT_COMMIT.md", "w") as f:
    f.write("# DO NOT COMMIT\n\n")
    f.write("The following files MUST NOT be committed to the production branch.\n\n")
    for path in sorted(unsafe_files):
        f.write(f"- `{path}`\n")
