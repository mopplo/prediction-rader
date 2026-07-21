import assert from 'node:assert/strict';
import test from 'node:test';

import {
  formatChange,
  formatChange7d,
  formatCoverageHours,
  formatDataConfidence,
  formatMarketStatus,
  formatPercent,
  formatRelativeUpdated,
  formatSpike,
  formatSyncedAtUtc,
  formatVolume,
} from '../src/lib/format.ts';

test('formatPercent renders probability', () => {
  assert.equal(formatPercent(0.58), '58%');
});

test('formatChange renders signed points in pp', () => {
  assert.equal(formatChange(0.16), '+16.0 pp');
  assert.equal(formatChange(-0.08), '-8.0 pp');
});

test('formatChange7d explains unavailable history', () => {
  assert.equal(formatChange7d(null, 'Only 5d of listing history'), 'Only 5d of listing history');
});

test('formatVolume abbreviates large values', () => {
  assert.equal(formatVolume(1_200_000), '$1.2M');
  assert.equal(formatVolume(850), '$850');
});

test('formatSpike renders multiplier baseline or unavailable', () => {
  assert.equal(formatSpike(2.4), '2.4x baseline');
  assert.equal(formatSpike(null), 'Baseline unavailable');
});

test('formatDataConfidence renders confidence tiers', () => {
  assert.equal(formatDataConfidence(95), 'Very High (95)');
  assert.equal(formatDataConfidence(81), 'High (81)');
  assert.equal(formatDataConfidence(50), 'Medium (50)');
  assert.equal(formatDataConfidence(49), 'Low (49)');
});

test('formatCoverageHours renders readable coverage', () => {
  assert.equal(formatCoverageHours(120), '5d of history');
  assert.equal(formatCoverageHours(0), 'No history yet');
});

test('formatSyncedAtUtc renders stable UTC timestamp', () => {
  assert.equal(formatSyncedAtUtc('2026-07-21T12:34:56Z'), '2026-07-21 12:34 UTC');
});

test('formatRelativeUpdated renders relative freshness', () => {
  const now = new Date('2026-07-21T12:30:00Z');
  assert.equal(
    formatRelativeUpdated('2026-07-21T12:25:00Z', now),
    'Updated 5 minutes ago',
  );
});

test('formatMarketStatus renders open and closed states', () => {
  assert.equal(formatMarketStatus('open', 3), 'Open · Resolves in 3 days');
  assert.equal(formatMarketStatus('closed', null), 'Closed');
});
