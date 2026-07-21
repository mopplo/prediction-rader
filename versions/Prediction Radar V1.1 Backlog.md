# Prediction Radar V1.1 Backlog

## Goal

Improve signal quality, explainability, and user retention.

The objective is to evolve Prediction Radar from a market dashboard into a prediction intelligence product.

---

# P0 - Must Have

## 1. Polymarket Deep Link

Add a prominent button on every market detail page.

Examples:

- View on Polymarket
- Open Market
- Trade on Polymarket

Purpose:

- Verify source data
- Increase trust
- Allow deeper research

---

## 2. Last Updated Timestamp

Display:

- Updated X minutes ago
- Last synced at YYYY-MM-DD HH:mm UTC

Purpose:

- Improve data transparency
- Increase trust

---

## 3. Market Status

Display:

- Open
- Closed
- Resolves in X days

Purpose:

Provide context beyond probability.

---

## 4. Data Confidence Labels

Convert numeric confidence into human-readable levels.

Example:

- 90+ = Very High
- 70+ = High
- 50+ = Medium
- <50 = Low

Purpose:

Improve readability.

---

# P1 - Signal Quality

## 5. Probability Boundary Filter

Exclude:

- Probability < 5%
- Probability > 95%

Purpose:

Remove near-certain markets from signal rankings.

---

## 6. Resolution Date Filter

Exclude:

- Markets resolving within 7 days

Purpose:

Reduce short-term noise.

---

## 7. Market Type Filter

Prioritize:

- AI
- Technology
- Crypto
- Politics
- Economics
- Business
- Geopolitics

Exclude:

- Sports
- Weather
- Intraday price contracts
- Entertainment

Purpose:

Focus on long-term narrative shifts.

---

## 8. Minimum Volume Threshold

Require:

- Volume > $10,000

Purpose:

Avoid low-liquidity noise.

---

# P1 - Homepage Improvements

## 9. Top Movers

Purpose:

Show largest belief changes.

Display emphasis:

- 24h probability change
- Direction
- Confidence

Question answered:

"What changed?"

---

## 10. Emerging Signals

Purpose:

Show increasing attention.

Display emphasis:

- Volume spike
- Activity growth
- Signal score

Question answered:

"What is gaining attention?"

---

## 11. Daily Radar

Purpose:

Provide a daily briefing.

Rules:

- Max 10 items
- Diverse topics
- One market per event
- High confidence only

Question answered:

"What should I read today?"

---

# P2 - Explainability

## 12. Why It Moved

Add to every market detail page.

Examples:

Why It Moved

- Probability increased by 12 points
- Volume increased by 240%
- Liquidity improved
- Related markets moved together

Rule-based implementation is sufficient.

No LLM required.

Purpose:

Increase trust and interpretability.

---

## 13. Narrative Tags

Examples:

- AI
- OpenAI
- Bitcoin
- Middle East
- US Election

Purpose:

Improve discovery and navigation.

---

# P2 - Discovery

## 14. Related Markets

Display related contracts on detail pages.

Examples:

GPT-6 before 2027

Related:

- GPT-6 before 2028
- OpenAI valuation > $500B
- AGI before 2030

Purpose:

Shift from contract discovery to narrative discovery.

---

## 15. Search

Support:

- GPT
- Bitcoin
- China
- OpenAI

Purpose:

Improve navigation.

---

## 16. Category Filters

Examples:

- All
- AI
- Crypto
- Politics
- Macro

Purpose:

Allow focused exploration.

---

# P3 - Narrative Layer

## 17. Narrative Trends

New homepage section.

Examples:

AI Acceleration

- 3 related markets moving higher
- Average move +9.2%

Middle East Tension

- 4 active markets
- Volume +230%

Purpose:

Help users understand themes instead of isolated contracts.

Question answered:

"What broader story is forming?"

---

# P3 - Retention

## 18. Watchlist

Initial implementation:

LocalStorage only.

Features:

- Star market
- Save locally
- View in My Radar page

No authentication required.

Purpose:

Increase repeat visits.

---

## 19. Weekly Recap

Generate:

This Week's Biggest Belief Shifts

Include:

- Top Movers
- Emerging Signals
- Major narratives

Purpose:

Content distribution and retention.

---

# Success Criteria

A user can answer within 30 seconds:

1. What changed?
2. What is gaining attention?
3. What should I read today?
4. Why did it move?
5. What larger narrative is forming?

If these questions are answered clearly, Prediction Radar V1.1 is successful.