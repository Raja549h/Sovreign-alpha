# SOVEREIGN ALPHA
## UI/UX Design Brief

**Version:** 2.0  
**Date:** 2026-05-25  
**Classification:** Internal Use Only  
**Design Target:** Bloomberg × Palantir × Institutional Intelligence Terminal

---

## 1. DESIGN PHILOSOPHY

### 1.1 Core Principles

| Principle | Description |
|-----------|-------------|
| **Calm** | No flashing elements, no neon gradients, no crypto-casino aesthetic |
| **Expensive** | Sparse whitespace, deliberate typography, muted authority |
| **Analytical** | Every pixel serves a data purpose. No decoration for its own sake |
| **High-Trust** | Immutable timestamps, confidence scores, audit indicators visible |
| **Operationally Real** | Displays live data, persists state, recovers gracefully from failure |

### 1.2 Primary Design References

- Bloomberg Terminal (dark theme, information density, monospace financial data)
- Palantir AIP (sober cards, regime indicators, intelligence panels)
- GS Platypus (analytical grid, confidence bars, forensic tagging)

### 1.3 What We Are NOT

- Crypto trading dashboard (no green-red price pumps, no confetti)
- Startup SaaS landing page (no hero images, no testimonials)
- AI chatbot wrapper (no chat bubbles, no personality)
- Retail analytics (no sparklines for the sake of it)

---

## 2. COLOR PALETTE

### 2.1 Dark Theme (Default)

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg-primary` | `#0a0b0e` | Main background |
| `--bg-secondary` | `#0f1115` | Sections, nav, panel headers |
| `--bg-tertiary` | `#14161c` | Hover states, table headers |
| `--bg-card` | `#111318` | Card backgrounds |
| `--bg-elevated` | `#191b22` | Skeleton loader, elevated surfaces |
| `--border` | `#1e2028` | Default borders |
| `--border-light` | `#282a32` | Hover borders, outline buttons |

### 2.2 Semantic Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `--accent` | `#00c9a5` | Positive signals, active state, primary CTAs |
| `--danger` | `#e04444` | Negative signals, vetoes, errors, critical severity |
| `--warning` | `#d4a030` | Caution, pending states, medium severity |
| `--info` | `#4488cc` | Informational, veto accuracy, low severity |

### 2.3 Text Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `--text-primary` | `#d8dae0` | Headings, key metrics |
| `--text-secondary` | `#80848f` | Body text, descriptions |
| `--text-dim` | `#585c66` | Labels, timestamps, secondary info |

---

## 3. TYPOGRAPHY

| Element | Font | Size | Weight |
|---------|------|------|--------|
| Body | `-apple-system, Segoe UI, Inter, sans-serif` | 14px (base) | 400 |
| Metrics | `SF Mono, Fira Code, Consolas, monospace` | 1.15rem | 700 |
| Labels | System font | 0.6rem (10px) | 600 |
| Navigation | System font, uppercase | 0.68rem | 500 |
| Page headers | System font, uppercase | 0.92rem | 600 |

### 3.1 Monospace (Data Display)
All financial values, timestamps, confidence scores, proof hashes, and ticker symbols must use monospace for alignment and information density.

---

## 4. COMPONENT SPECIFICATIONS

### 4.1 Stat Box
```
┌─────────────────────┐
│ LABEL               │  ← 0.6rem, uppercase, letter-spaced, text-dim
│ VALUE               │  ← 1.15rem, monospace, accent color
│ Sub-label           │  ← 0.6rem, text-dim
└─────────────────────┘
```
- Border: 1px solid `--border`, radius 4px
- Hover: border transitions to `--border-light`
- Min-width: 170px (flexible via auto-fill grid)

### 4.2 Intelligence Card (Intel Card)
```
┌───────────────────────────────┐
│ LABEL                         │  ← 0.55rem, uppercase, text-dim
│ STAT                          │  ← 1.1rem, monospace, semantic color
│ ━━━━━━━━━━━━━━━━━━━━━━━━     │  ← Confidence bar (4px height)
│ NOTE                          │  ← 0.6rem, text-dim
└───────────────────────────────┘
```
- Confidence bar: `--border` background, fill color matches semantic
- Fill width: proportional to value relative to threshold
- Used in: regime intelligence panel grid (4-column)

### 4.3 Signal Badge
- Padding: 0.1rem 0.45rem
- Border-radius: 4px
- Font: 0.6rem, monospace, bold

| Variant | Background | Text | Border |
|---------|-----------|------|--------|
| BUY / cleared / approved | `--accent-dim` (12%) | `--accent` | None |
| SELL / vetoed / rejected | `--danger-dim` (12%) | `--danger` | None |
| HOLD / pending | `--warning-dim` (12%) | `--warning` | None |

### 4.4 Severity Tag
- Same visual pattern as Signal Badge
- Used for: forensic flags, signal counts, risk severity

| Variant | Background | Text |
|---------|-----------|------|
| critical | `danger` 20% | `--danger` |
| high | `danger` 12% | `--danger` |
| medium | `warning` 12% | `--warning` |
| low | `info` 12% | `--info` |

### 4.5 Regime Badge
- Same as signal badge with 1px border

| Variant | Background | Text | Border |
|---------|-----------|------|--------|
| RISK_ON | `--accent-dim` | `--accent` | `--accent` |
| RISK_OFF | `--danger-dim` | `--danger` | `--danger` |
| NEUTRAL | `--warning-dim` | `--warning` | `--warning` |

### 4.6 Panel
``` 
┌─ Panel Header ──────────────────┐  ← bg-secondary, 0.7rem uppercase
│  Title                     CTA  │
├─────────────────────────────────┤
│  Panel Body                     │  ← bg-card, padded 0.9rem
│                                 │
└─────────────────────────────────┘
```

### 4.7 Signal Card (compact)
```
┌─────────────────────────────────────┐
│ SYMBOL  reason text                 │  ← 0.7rem
└─────────────────────────────────────┘
```
- Used in: live market signal panels
- Spacing: 0.6rem 0.8rem padding, 0.4rem gap between cards

---

## 5. PAGE LAYOUTS

### 5.1 Dashboard Home (index)
```
┌──────────────────────────────────────────────────────┐
│ TOP BAR: Status dot + System name + UTC Clock          │
├──────────────────────────────────────────────────────┤
│ TICKER STRIP: SPX VIX DXY 10Y GOLD WTI NSEI           │
├──────────────────────────────────────────────────────┤
│ NAV: Brand | Dashboard | Decisions | Predictions | ...│
├──────────────────────────────────────────────────────┤
│ PAGE HEADER: Market Intelligence Dashboard + timestamp │
├──────────────────────────────────────────────────────┤
│ STATS ROW: Regime | Total Pred. | Approval Rate | ... │
├──────────────────────────────────────────────────────┤
│ INTEL GRID: VIX | 10Y Treasury | DXY | HY OAS         │
├──────────────────────────────────────────────────────┤
│ REGIME INTELLIGENCE SUMMARY panel                      │
├──────────────────────────────────────────────────────┤
│ 2-COL GRID:                                            │
│ ┌── Recent Predictions ──┐ ┌── Recent Vetoes ──┐     │
│ │ Table with ticker,     │ │ Table with ticker, │     │
│ │ signal, confidence,    │ │ confidence, reason,│     │
│ │ outcome, date          │ │ avoided DD, correct│     │
│ └────────────────────────┘ └────────────────────┘     │
├──────────────────────────────────────────────────────┤
│ QUICK ACTIONS panel                                    │
└──────────────────────────────────────────────────────┘
```

### 5.2 Decision Log
```
Page Header → Stats Row (5 boxes) → Full-width table
```
No charts — pure tabular audit view.

### 5.3 Prediction Ledger
```
Page Header → Stats Row (5 boxes) → Full-width table + Export CSV
```
Write-once immutable table with outcome tracking.

### 5.4 Veto Archive
```
Page Header → Stats Row (4 boxes) → Full-width table
```
Risk-rejection record with correctness badges.

### 5.5 Performance Analytics
```
Page Header → Stats Row (6 boxes) → 2-chart grid → 2-col grid (chart + metrics)
```
Charts: confidence trend (line), sector breakdown (bar), return distribution (bar).

### 5.6 Live Market
```
Page Header → Watchlist table → 3-col signal panels
```
Signal panels: oversold, overbought, unusual volume with severity-tag counts.

---

## 6. INTERACTION DESIGN

### 6.1 Auto-Refresh
- Dashboard polls `/api/refresh` every 60 seconds
- Only updates DOM nodes with `data-key` attributes (no full reload)
- Stats, regime badge, predictions table, and vetoes table update in-place
- Timestamp in nav updates to show "last updated"

### 6.2 Loading States
- Skeleton shimmer animation on initial page load (CSS `@keyframes shimmer`)
- Duration: 1.5s infinite, gradient background
- Applied via `.skeleton` class: `skeleton-value`, `skeleton-label`, `skeleton-row`

### 6.3 Transitions
- Page content: `fadeIn` 0.3s ease on `.fade-in` containers
- Navigation hover: background change 180ms ease
- Stat box hover: border-color transition 180ms ease
- Confidence bar fill: width transition 0.6s ease

### 6.4 Error Handling
- All fetch calls in JS have `.catch()` handlers
- Failed API calls logged to console.warn (no alerts, no toast)
- Server errors render `error.html` with code + message (no stack traces)
- 429 errors: "Too many requests. Please wait before trying again."
- 413 errors: "File too large. Maximum 10MB."

### 6.5 Empty States
- Centered layout with `—` icon and descriptive message
- Examples: "No predictions recorded. Run analysis to begin."
- Never shows NaN, undefined, or raw error messages in UI

---

## 7. RESPONSIVE BEHAVIOR

| Breakpoint | Behavior |
|------------|----------|
| > 1024px | Full layout: 4-col intel grid, 2-col content, full nav |
| 768-1024px | 3-col stats, 2-col grids, ticker strip visible |
| < 768px | 2-col stats, 1-col grids, ticker strip hidden, nav wraps |
| < 480px | 1-col stats, stacked layout, hamburger could be added |

---
