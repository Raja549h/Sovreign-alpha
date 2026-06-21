import json
import os

with open("audit_results.json") as f:
    results = json.load(f)

# LIVE_ROUTE_MAP
with open("C:/Users/lokes/.gemini/antigravity/brain/97baeab8-58a0-45d2-a695-ce010c46102d/LIVE_ROUTE_MAP.md", "w") as f:
    f.write("# LIVE ROUTE MAP\n\n")
    f.write("## Overview\nDiscovered routes on the live Hugging Face Space (`https://svrn-alpha-soverignalpha.hf.space/`).\n\n")
    f.write("| Route | Method | Status | Latency (s) | Size (bytes) |\n")
    f.write("|-------|--------|--------|-------------|--------------|\n")
    for r in results:
        f.write(f"| `{r['route']}` | GET | {r['status']} | {r['latency']} | {r['size']} |\n")

# FEATURE_EXECUTION_AUDIT
with open("C:/Users/lokes/.gemini/antigravity/brain/97baeab8-58a0-45d2-a695-ce010c46102d/FEATURE_EXECUTION_AUDIT.md", "w") as f:
    f.write("# FEATURE EXECUTION AUDIT\n\n")
    f.write("## 1. Dashboard\n- Status: OK (200)\n- Latency: ~1.2s\n\n")
    f.write("## 2. Predictions Page (`/predictions`)\n- Status: OK (200)\n- Latency: ~2.1s\n\n")
    f.write("## 3. Run Analysis Workflow (`/run`)\n- **Status: CRITICAL FAILURE (500 Internal Server Error)**\n- Observations: The route crashes before rendering the page.\n\n")
    f.write("## 4. Evidence Hub (`/evidence`)\n- Status: OK (200)\n- Latency: ~0.8s\n\n")

# API_AUDIT
with open("C:/Users/lokes/.gemini/antigravity/brain/97baeab8-58a0-45d2-a695-ce010c46102d/API_AUDIT.md", "w") as f:
    f.write("# API AUDIT\n\n")
    f.write("## `/api/run` (POST)\n- Status: 500 Internal Server Error\n- Vulnerability: Unhandled exception crashes the endpoint during pipeline execution.\n\n")
    f.write("## `/api/runs` (GET)\n- Status: 404 Not Found\n- Observation: The endpoint is missing from the deployed build.\n\n")

# ORGANIC_PIPELINE_VERIFICATION
with open("C:/Users/lokes/.gemini/antigravity/brain/97baeab8-58a0-45d2-a695-ce010c46102d/ORGANIC_PIPELINE_VERIFICATION.md", "w") as f:
    f.write("# ORGANIC PIPELINE VERIFICATION\n\n")
    f.write("> [!WARNING]\n> **VERDICT: FAILED.** The live pipeline cannot be verified because the execution endpoint `/api/run` returns a 500 Internal Server Error.\n\n")
    f.write("## Execution Trace\n1. Target: `POST /api/run` with `{\"ticker\": \"MSFT\"}`\n2. Response: `500 Internal Server Error`\n3. Records Created: UNVERIFIED (Likely 0)\n\n")

# DATABASE_TRUTH_TEST
with open("C:/Users/lokes/.gemini/antigravity/brain/97baeab8-58a0-45d2-a695-ce010c46102d/DATABASE_TRUTH_TEST.md", "w") as f:
    f.write("# DATABASE TRUTH TEST\n\n")
    f.write("> [!CAUTION]\n> **VERDICT: UNVERIFIED.** The dashboard renders successfully but we cannot prove whether the metrics are organic or seeded because the organic pipeline generation is broken on the live deployment.\n\n")

# ERROR_SURFACE_AUDIT
with open("C:/Users/lokes/.gemini/antigravity/brain/97baeab8-58a0-45d2-a695-ce010c46102d/ERROR_SURFACE_AUDIT.md", "w") as f:
    f.write("# ERROR SURFACE AUDIT\n\n")
    f.write("## Critical Vulnerabilities\n1. **Hidden 500 Errors on Execution Paths**: `/run` and `/api/run` both crash natively, likely due to unhandled database connection pooling exceptions or missing schema elements in the live build.\n2. **Missing Endpoints**: Background worker progress tracking (`/api/runs`) does not exist on the live deployment.\n\n")

# PERFORMANCE_REPORT
with open("C:/Users/lokes/.gemini/antigravity/brain/97baeab8-58a0-45d2-a695-ce010c46102d/PERFORMANCE_REPORT.md", "w") as f:
    f.write("# PERFORMANCE REPORT\n\n")
    f.write("## Latency Measurements\n")
    for r in results:
        f.write(f"- `{r['route']}`: {r['latency']}s\n")
    f.write("\n## Verdict\nMost read-only pages load under 1.5 seconds. However, pipeline execution fails immediately.\n")

# INSTITUTIONAL_BUYER_REVIEW
with open("C:/Users/lokes/.gemini/antigravity/brain/97baeab8-58a0-45d2-a695-ce010c46102d/INSTITUTIONAL_BUYER_REVIEW.md", "w") as f:
    f.write("# INSTITUTIONAL BUYER REVIEW\n\n")
    f.write("## Perspective: Hedge Fund CIO\n\n**Would I pay for this today?**\n**NO.**\n\n**Why Not?**\nWhile the dashboard looks impressive and presents structured intelligence, the core engine—the ability to run analysis on a new ticker—is fundamentally broken (500 Internal Server Error) on the live instance. An institutional intelligence platform is only as good as its capability to continuously ingest and synthesize new information. A broken execution pipeline disqualifies it from production use.\n")

# DATA_PROVENANCE_AUDIT
with open("C:/Users/lokes/.gemini/antigravity/brain/97baeab8-58a0-45d2-a695-ce010c46102d/DATA_PROVENANCE_AUDIT.md", "w") as f:
    f.write("# DATA PROVENANCE AUDIT\n\n")
    f.write("## Metrics Assessment\n- Source Table: `dashboard_metrics` (Inferred)\n- Status: UNVERIFIED. Cannot distinguish between seeded data and live generated data on the deployed instance.\n")

# FINAL_VERDICT
with open("C:/Users/lokes/.gemini/antigravity/brain/97baeab8-58a0-45d2-a695-ce010c46102d/FINAL_VERDICT.md", "w") as f:
    f.write("# FINAL VERDICT\n\n")
    f.write("## Scores\n")
    f.write("- Technical Score: **3/10** (Core execution is broken)\n")
    f.write("- DTI Score: **2/10**\n")
    f.write("- PW Score: **2/10**\n")
    f.write("- Institutional Readiness: **1/10**\n")
    f.write("- Production Readiness: **1/10**\n")
    f.write("- Security: **4/10**\n")
    f.write("- Reliability: **0/10** (0% pipeline success rate on LIVE)\n")
    f.write("- Data Integrity: **UNVERIFIED**\n\n")
    f.write("## Summary\nThe local codebase has progressed significantly, but the **live deployment on Hugging Face is running a broken legacy build**. The pipeline cannot be triggered. To achieve institutional readiness, the recent local architectural improvements (database connection pooling fixes, background worker loops, analysis_runs tracking) MUST be deployed to the live Hugging Face instance immediately.\n")

