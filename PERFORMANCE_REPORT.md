# Performance Report

## Latency Analysis
- **SQLite Latency**: Local disk-based IO guarantees sub-millisecond query responses (< 1ms), but suffers from multi-threading file locks during high-volume ingestions (e.g., `database is locked` exceptions).
- **Neon PostgreSQL Latency**: Network-bound IO to `us-east-1`. Expected latency is ~20-40ms per query.
- **Mitigation Strategy**: The implementation of `psycopg2.pool.SimpleConnectionPool` within `database.py` radically reduces connection initialization overhead, ensuring that Neon latency remains imperceptible to the Hugging Face dashboard UI.

## Dashboard Load
Because Hugging Face Space servers are ephemeral, offloading the database IO to a dedicated Neon compute instance will actively *improve* the server's RAM and CPU headroom for model inference.
