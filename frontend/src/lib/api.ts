const API_BASE_URL = import.meta.env?.API_BASE_URL ?? 'http://localhost:8000';

export interface MarketSummary {
  id: string;
  title: string;
  slug?: string | null;
  category?: string | null;
  probability?: number | null;
  volume?: number | null;
  liquidity?: number | null;
  change24h?: number | null;
  change7d?: number | null;
  signal_score?: number | null;
  attention_score?: number | null;
  market_significance?: number | null;
  confidence?: number | null;
  confidence_label?: string | null;
  signal_reason?: string | null;
  volume_spike?: number | null;
  signal_type?: string | null;
  updated_at?: string | null;
  polymarket_url?: string | null;
}

export interface SignalComponents {
  probability?: number | null;
  volume?: number | null;
  liquidity?: number | null;
  persistence?: number | null;
}

export interface MarketDetail {
  id: string;
  title: string;
  slug?: string | null;
  probability?: number | null;
  change1h?: number | null;
  change24h?: number | null;
  change7d?: number | null;
  change7d_unavailable_reason?: string | null;
  volume?: number | null;
  volume_1wk?: number | null;
  volume_spike?: number | null;
  liquidity?: number | null;
  signal_score?: number | null;
  attention_score?: number | null;
  market_significance?: number | null;
  confidence?: number | null;
  confidence_label?: string | null;
  signal_reason?: string | null;
  why_it_moved?: string[];
  signal_components?: SignalComponents | null;
  category?: string | null;
  image_url?: string | null;
  end_date?: string | null;
  updated_at?: string | null;
  last_synced_at?: string | null;
  polymarket_url?: string | null;
  market_status?: string | null;
  resolves_in_days?: number | null;
  history_coverage_hours?: number | null;
  has_24h_history?: boolean;
  has_7d_history?: boolean;
  history: Array<{
    timestamp: string;
    probability: number;
    volume24h?: number | null;
  }>;
}

export interface DailyRadarItem {
  rank: number;
  market_id: string;
  title: string;
  signal_score: number;
  confidence?: number | null;
  confidence_label?: string | null;
  signal_reason?: string | null;
  change24h?: number | null;
  volume_spike?: number | null;
  why_it_moved?: string[];
}

export interface NarrativeTrendItem {
  id: number;
  title: string;
  category?: string | null;
  market_count: number;
  active_count: number;
  median_abs_change_24h?: number | null;
  aggregate_volume_spike?: number | null;
  direction_coherence?: number | null;
  dominant_direction?: string | null;
  narrative_score: number;
  representative_market_id?: string | null;
  summary?: string | null;
}

export interface PaginatedMarkets {
  items: MarketSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface RadarStats {
  markets_tracked: number;
  active_signals: number;
  last_synced_at?: string | null;
  sync_interval_minutes: number;
}

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`API ${path} failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function getStats(): Promise<RadarStats> {
  return fetchJson('/api/stats');
}

export function getTopMovers(): Promise<MarketSummary[]> {
  return fetchJson('/api/top-movers');
}

export function getEmergingSignals(): Promise<MarketSummary[]> {
  return fetchJson('/api/emerging-signals');
}

export function getDailyRadar(): Promise<DailyRadarItem[]> {
  return fetchJson('/api/daily-radar');
}

export function getNarrativeTrends(): Promise<NarrativeTrendItem[]> {
  return fetchJson('/api/narrative-trends');
}

export function getMarketDetail(id: string): Promise<MarketDetail> {
  return fetchJson(`/api/market/${id}`);
}

export function listMarkets(limit = 100, offset = 0): Promise<PaginatedMarkets> {
  return fetchJson(`/api/markets?limit=${limit}&offset=${offset}`);
}

export function shouldContinueMarketPagination(
  itemsSoFar: number,
  pageItemCount: number,
  total: number,
): boolean {
  if (pageItemCount === 0) {
    return false;
  }
  return itemsSoFar < total;
}

export async function collectAllMarketPages(
  fetchPage: (limit: number, offset: number) => Promise<PaginatedMarkets>,
  pageSize = 100,
): Promise<MarketSummary[]> {
  const items: MarketSummary[] = [];
  let offset = 0;

  while (true) {
    const page = await fetchPage(pageSize, offset);
    items.push(...page.items);
    if (!shouldContinueMarketPagination(items.length, page.items.length, page.total)) {
      break;
    }
    offset += pageSize;
  }

  return items;
}

export function getAllMarkets(pageSize = 100): Promise<MarketSummary[]> {
  return collectAllMarketPages(listMarkets, pageSize);
}

export async function getAllMarketDetails(pageSize = 100): Promise<MarketDetail[]> {
  const markets = await getAllMarkets(pageSize);
  const details: MarketDetail[] = [];

  const chunkSize = 20;
  for (let index = 0; index < markets.length; index += chunkSize) {
    const chunk = markets.slice(index, index + chunkSize);
    const chunkDetails = await Promise.all(chunk.map((market) => getMarketDetail(market.id)));
    details.push(...chunkDetails);
  }

  return details;
}
