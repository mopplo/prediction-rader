# Prediction Radar V1.1 Optimization PRD

## Product Mission

Prediction Radar helps users discover where market beliefs are changing before everyone else notices.

The product is not a trading tool.

The product is a signal discovery engine for understanding shifts in collective expectations about the future.

---

# Core User Question

When opening Prediction Radar, users should be able to answer:

1. What changed today?
2. What deserves attention?
3. Why does it matter?

within 30 seconds.

---

# Information Architecture

Homepage consists of three primary signal layers.

## 1. Top Movers

Purpose:

Identify markets experiencing the largest belief shifts.

User Question:

"What important future event changed the most in the last 24 hours?"

Prioritize:

- Probability change
- Market significance
- Data quality

Ranking:

Primary:

- Absolute 24h probability change

Secondary:

- Signal score
- Data confidence

Requirements:

- Change ≥ 5 percentage points
- Volume above threshold
- Liquidity above threshold
- Resolution date > 7 days
- Probability between 5% and 95%
- Data confidence ≥ 40

Goal:

Highlight major belief changes.

Not noise.

---



## 2. Emerging Signals

Purpose:

Identify markets where attention is increasing before consensus fully moves.

User Question:

"What is starting to matter?"

Prioritize:

- Volume spike
- Attention growth
- Early narrative formation

Ranking:

Primary:

- Signal score

Signal score weighting:

50% volume spike

30% probability change

20% liquidity score

Requirements:

- Change ≥ 3 percentage points
- Volume spike ≥ 1.5x baseline
- Data confidence ≥ 40

Goal:

Find emerging stories before they become Top Movers.

---



## 3. Daily Radar

Purpose:

Provide the highest quality daily briefing.

User Question:

"If I only read 10 things today, what should they be?"

Characteristics:

- Maximum 10 entries
- One market per event
- Maximum two entries per category
- Diverse topics
- High confidence only

Ranking:

Signal score

Data confidence

Market significance

Goal:

Serve as a daily intelligence briefing.

Not another Top Movers list.

---



# Signal Quality Improvements



## Probability Boundary Filtering

Exclude:

Probability < 5%

Probability > 95%

Reason:

Markets near certainty rarely provide useful information.

---



## Resolution Date Filtering

Exclude:

Markets resolving within 7 days.

Reason:

Short-term contracts create noise.

Focus on belief changes rather than event settlement.

---



## Market Type Filtering

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
- Pure entertainment markets

Reason:

Prediction Radar focuses on future narratives.

Not event outcomes.

---



## Volume Threshold

Require minimum volume.

Suggested:

Volume > $10,000

Reason:

Reduce manipulation and low-liquidity noise.

---



# Event Clustering

Current issue:

Similar contracts can occupy multiple positions.

Examples:

Iran Ceasefire July 24

Iran Ceasefire July 31

Solution:

Group markets using:

- event_id
- condition_id
- groupItemId

Display:

Only highest quality representative market.

Goal:

Narrative-level discovery.

Not contract-level repetition.

---



# Narrative Layer (New)

Add a new homepage section:

## Narrative Trends

Purpose:

Surface clusters of related market activity.

Example:

AI Acceleration

3 related markets moved higher

Average move +9.2%

---

Middle East Tension

4 related markets active

Volume +230%

---

Crypto Bullishness

5 related markets rising

Average move +6.1%

Goal:

Help users understand themes.

Not just individual contracts.

Priority:

High

---



# Why It Moved (New)

Every market detail page should include:

## Why It Moved

Automatically generated explanation.

No LLM required initially.

Rule-based generation is sufficient.

Example:

Why It Moved

- Probability increased by 12 points
- Volume increased by 240%
- Liquidity improved
- 3 related markets moved in the same direction

Goal:

Increase trust and interpretability.

Priority:

High

---



# Signal Score Improvements

Current score is acceptable for MVP.

Recommended V1.1 formula:

Signal Score =
0.5 × Volume Spike
+
0.3 × Probability Change
+
0.2 × Liquidity Score

Normalize all inputs to 0–100.

Purpose:

Reward markets where both belief and attention are changing.

---



# Detail Page Improvements

Apply signal calculations to all markets.

Do not depend on whether the market appears in:

- Top Movers
- Emerging Signals
- Daily Radar

Every market should display:

- Probability
- Volume
- Liquidity
- Data confidence
- Signal score
- Why It Moved

Goal:

Consistent user experience.

---



# UI Improvements

Different sections should emphasize different metrics.

Top Movers:

Large probability change display.

Example:

+12.4 pp

---

Emerging Signals:

Large volume spike display.

Example:

Volume +340%

---

Daily Radar:

High-level intelligence card.

Example:

High Confidence

Signal Score 87

---

Goal:

Users should understand the difference within 5 seconds.

---



# Success Criteria

A first-time visitor can immediately understand:

Top Movers:
"What changed?"

Emerging Signals:
"What is gaining attention?"

Daily Radar:
"What should I read?"

Narrative Trends:
"What broader story is forming?"

Why It Moved:
"Why is this signal important?"

within 30 seconds.

If these five questions can be answered, Prediction Radar V1.1 is successful.