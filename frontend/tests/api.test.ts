import assert from 'node:assert/strict';
import test from 'node:test';

import {
  collectAllMarketPages,
  shouldContinueMarketPagination,
  type PaginatedMarkets,
} from '../src/lib/api.ts';

test('shouldContinueMarketPagination stops on empty page', () => {
  assert.equal(shouldContinueMarketPagination(0, 0, 200), false);
});

test('shouldContinueMarketPagination continues until total is reached', () => {
  assert.equal(shouldContinueMarketPagination(100, 100, 200), true);
  assert.equal(shouldContinueMarketPagination(200, 100, 200), false);
});

test('collectAllMarketPages merges paginated markets', async () => {
  const pages: PaginatedMarkets[] = [
    {
      items: [
        { id: '1', title: 'One' },
        { id: '2', title: 'Two' },
      ],
      total: 3,
      limit: 2,
      offset: 0,
    },
    {
      items: [{ id: '3', title: 'Three' }],
      total: 3,
      limit: 2,
      offset: 2,
    },
  ];

  let calls = 0;
  const items = await collectAllMarketPages(async (_limit, offset) => {
    const page = pages[calls];
    calls += 1;
    assert.equal(offset, page.offset);
    return page;
  }, 2);

  assert.deepEqual(
    items.map((item) => item.id),
    ['1', '2', '3'],
  );
  assert.equal(calls, 2);
});

test('collectAllMarketPages stops when a page returns no items', async () => {
  const items = await collectAllMarketPages(async () => ({
    items: [],
    total: 10,
    limit: 100,
    offset: 0,
  }));

  assert.deepEqual(items, []);
});
