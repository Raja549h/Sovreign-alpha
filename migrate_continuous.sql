CREATE TABLE IF NOT EXISTS analysis_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker TEXT NOT NULL,
    run_type TEXT DEFAULT 'MANUAL',
    status TEXT NOT NULL DEFAULT 'PENDING',
    progress_pct INTEGER DEFAULT 0,
    current_step TEXT DEFAULT 'Initialized',
    retry_count INTEGER DEFAULT 0,
    heartbeat_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    result_data JSONB,
    error_log TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analysis_run_events (
    event_id SERIAL PRIMARY KEY,
    run_id UUID REFERENCES analysis_runs(run_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE observation_memory ADD COLUMN IF NOT EXISTS run_id UUID;
ALTER TABLE research_notes ADD COLUMN IF NOT EXISTS run_id UUID;
ALTER TABLE institutional_scores ADD COLUMN IF NOT EXISTS run_id UUID;
ALTER TABLE observation_autopsy ADD COLUMN IF NOT EXISTS run_id UUID;
ALTER TABLE evidence_timeline ADD COLUMN IF NOT EXISTS run_id UUID;
