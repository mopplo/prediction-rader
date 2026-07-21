import assert from 'node:assert/strict';
import test from 'node:test';

import { narrativeDirectionLabel } from '../src/lib/format.ts';

test('narrativeDirectionLabel shows mixed when coherence is low', () => {
  assert.equal(narrativeDirectionLabel('higher', 0.4), 'Mixed / active');
});

test('narrativeDirectionLabel shows direction when coherent', () => {
  assert.equal(narrativeDirectionLabel('higher', 0.8), 'Moving higher');
  assert.equal(narrativeDirectionLabel('lower', 0.75), 'Moving lower');
});
