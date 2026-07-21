# Prediction Radar MVP

## Vision

**Discover where the world is changing its mind.**

Prediction Radar monitors prediction markets and highlights the most meaningful changes in probability, volume, and attention.

Instead of showing every market, it surfaces the signals that matter.

---

## Product Positioning

Prediction Radar is not a betting tool.

Prediction Radar is a signal discovery engine for prediction markets.

It helps users discover where market beliefs are changing before everyone else notices.

---

## Problem

Prediction markets contain valuable information about how people collectively assess future events.

However:

* There are thousands of active markets.
* Most users cannot monitor them continuously.
* Important probability changes are easily missed.
* Large volume movements often go unnoticed.
* Market sentiment shifts are difficult to identify early.

Users need a way to discover meaningful signals without manually tracking every market.

---

## Target Users

### Primary Users

Prediction market traders:

* Polymarket users
* Kalshi users
* Manifold users
* Sports prediction users

Goals:

* Find opportunities early
* Detect information shifts
* Discover emerging narratives

---

### Secondary Users

Information-oriented users:

* Investors
* Researchers
* Journalists
* AI enthusiasts
* Startup founders

Goals:

* Understand what the market believes
* Track changing expectations
* Monitor emerging trends

---

## Core Value Proposition

Prediction Radar helps users:

* Discover market belief changes
* Identify emerging signals
* Track attention shifts
* Surface important events before they become obvious

The product does not tell users what to buy.

The product helps users discover what deserves attention.

---

# MVP Scope

## Data Source

Phase 1:

* Polymarket only

Future:

* Kalshi
* Manifold
* Sports betting markets
* Other prediction platforms

---

## Homepage

### Section 1 — Hero

Title:

Prediction Radar

Subtitle:

Discover where the world is changing its mind.

Description:

Track the biggest probability shifts across prediction markets and uncover emerging signals before they become obvious.

---

### Section 2 — Top Movers

Purpose:

Show the largest probability changes.

Example:

BTC > $200k by 2027

Probability:

42% → 58%

Change:

+16%

Volume:

$1.2M

---

GPT-6 released before 2027

Probability:

51% → 68%

Change:

+17%

Volume:

$850k

---

Ranking Logic:

Sort by:

* 24h probability change
* Volume threshold
* Market activity

---

### Section 3 — Emerging Signals

Purpose:

Detect markets receiving unusual attention.

Metrics:

* Volume spike
* Trade count spike
* Sudden activity increase

Example:

OpenAI GPT-6 before 2027

Volume:

+340%

Last 24h

Signal:

Emerging Attention

---

### Section 4 — Daily Radar

Purpose:

Provide a daily summary.

Example:

Top Signals Today

1. GPT-6 before 2027
2. Bitcoin > $200k
3. US Election Market
4. AI Regulation Market

---

## Market Detail Page

URL Example:

/market/{market-id}

Content:

* Market title
* Current probability
* 24h change
* 7d change
* Volume
* Historical chart

Future:

* AI explanation
* News integration
* Market comparison

---

# Metrics

## Probability Change

Formula:

Current Probability - Previous Probability

Periods:

* 1h
* 24h
* 7d

---

## Volume Change

Formula:

Current Volume / Historical Average Volume

Used to identify unusual attention.

---

## Signal Score

Simple MVP formula:

Signal Score =
(Probability Change Weight)
+
(Volume Spike Weight)

Example:

60% probability movement weight

40% volume movement weight

---

# Technical Architecture

## Backend

Recommended:

FastAPI

Responsibilities:

* Fetch market data
* Store historical snapshots
* Calculate signals
* Provide API endpoints

---

## Database

Recommended:

PostgreSQL

Tables:

markets

market_snapshots

signals

---

## Scheduler

Cron Job

Frequency:

Every 15 minutes

Responsibilities:

* Fetch latest market data
* Save snapshots
* Generate signals

---

## Frontend

Recommended:

Astro

Pages:

/

/market/[id]

---

# API Endpoints

## Markets

GET /api/markets

Return:

* title
* probability
* volume
* change24h

---

## Top Movers

GET /api/top-movers

Return:

Top probability movers.

---

## Emerging Signals

GET /api/emerging-signals

Return:

Markets with unusual activity.

---

## Market Details

GET /api/market/{id}

Return:

Detailed market information.

---

# Future Roadmap

## V2

AI Explanations

Example:

Why did this market move?

AI summarizes:

* News
* Market activity
* Narrative changes

---

## V3

Cross-Market Comparison

Compare:

* Polymarket
* Kalshi
* Manifold

Identify pricing differences.

---

## V4

Personalized Radar

User chooses interests:

* AI
* Crypto
* Politics
* Sports

System generates custom daily signals.

---

# Success Criteria

A user opens Prediction Radar and can answer:

1. What changed today?
2. What deserves attention?
3. Why does it matter?

within 30 seconds.
