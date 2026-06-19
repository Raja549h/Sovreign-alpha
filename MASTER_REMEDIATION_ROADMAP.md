# MASTER REMEDIATION ROADMAP
## Sovereign Alpha

## Prioritization by ROI (Impact / Effort)

---

### 1. Fix `DatabaseConnection.executescript` (Critical, High ROI)
- **Effort**: Low (1-2 hours)
- **Risk**: Low
- **Business Impact**: High (enables DB initialization and schema setup)
- **Institutional Impact**: High (enables proper persistence)
- **Action**: Implement `executescript` to split and execute PostgreSQL commands

---

### 2. Document Neon DB Setup (Critical, High ROI)
- **Effort**: Low (30 mins)
- **Risk**: Low
- **Business Impact**: High (enables deployment)
- **Institutional Impact**: High (enables production use)
- **Action**: Add step-by-step Neon setup guide to README

---

### 3. Add Comprehensive Tests (High, Medium ROI)
- **Effort**: Medium (1-2 days)
- **Risk**: Low
- **Business Impact**: High (ensures stability)
- **Institutional Impact**: High (institutional clients demand testing)
- **Action**: Add unit tests for agents, engine, data layer; add integration tests for DB

---

### 4. Remove Legacy SQLite Comments (Medium, Low-Medium ROI)
- **Effort**: Low (30 mins)
- **Risk**: Low
- **Business Impact**: Low
- **Institutional Impact**: Low (cleanup)
- **Action**: Search and remove all SQLite-related comments

---

### 5. Improve Dashboard Error Handling (Medium, Medium ROI)
- **Effort**: Low (1 hour)
- **Risk**: Low
- **Business Impact**: Medium (better UX)
- **Institutional Impact**: Medium (more robust UI)
- **Action**: Add user-friendly error messages for DB failures

---

### 6. Add DB Migration System (Medium, Medium ROI)
- **Effort**: Medium (1 day)
- **Risk**: Medium
- **Business Impact**: Medium (enables schema changes safely)
- **Institutional Impact**: Medium (institutional-grade schema management)
- **Action**: Implement a simple migration system (e.g., using Alembic or custom)

---

### 7. Verify & Complete Research Engines (Medium, Medium-High ROI)
- **Effort**: High (2-3 days)
- **Risk**: Medium
- **Business Impact**: High (completes core features)
- **Institutional Impact**: High (delivers on promised features)
- **Action**: Test each research engine, fix issues, integrate fully

---

### 8. Clean Up Dead Code (Low, Low ROI)
- **Effort**: Low (1 hour)
- **Risk**: Low
- **Business Impact**: Low
- **Institutional Impact**: Low
- **Action**: Remove unused variables, functions, and code paths

---

### 9. Add Linting & Code Style (Low, Low ROI)
- **Effort**: Low (1 hour)
- **Risk**: Low
- **Business Impact**: Low
- **Institutional Impact**: Low (better code quality)
- **Action**: Set up black, flake8, isort

---

### 10. Improve Documentation (Low, Low ROI)
- **Effort**: Medium (1 day)
- **Risk**: Low
- **Business Impact**: Medium (onboarding easier)
- **Institutional Impact**: Medium (better maintainability)
- **Action**: Improve README, add docstrings, add architecture diagrams
