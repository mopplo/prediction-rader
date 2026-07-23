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

export class ApiError extends Error {
  status: number;

  constructor(path: string, status: number) {
    super(`API ${path} failed: ${status}`);
    this.name = 'ApiError';
    this.status = status;
  }
}

export function resolveApiBaseUrl(
  runtimeEnv?: Record<string, unknown> | null,
  buildTimeUrl: string | undefined = import.meta.env?.API_BASE_URL,
): string {
  const fromRuntime = runtimeEnv?.API_BASE_URL;
  if (typeof fromRuntime === 'string' && fromRuntime.trim().length > 0) {
    return fromRuntime.trim().replace(/\/$/, '');
  }
  if (typeof buildTimeUrl === 'string' && buildTimeUrl.trim().length > 0) {
    return buildTimeUrl.trim().replace(/\/$/, '');
  }
  return 'http://localhost:8000';
}

async function fetchJson<T>(path: string, baseUrl: string): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`);
  if (!response.ok) {
    throw new ApiError(path, response.status);
  }
  return response.json() as Promise<T>;
}

export function getStats(baseUrl: string): Promise<RadarStats> {
  return fetchJson('/api/stats', baseUrl);
}

export function getTopMovers(baseUrl: string): Promise<MarketSummary[]> {
  return fetchJson('/api/top-movers', baseUrl);
}

export function getEmergingSignals(baseUrl: string): Promise<MarketSummary[]> {
  return fetchJson('/api/emerging-signals', baseUrl);
}

export function getDailyRadar(baseUrl: string): Promise<DailyRadarItem[]> {
  return fetchJson('/api/daily-radar', baseUrl);
}

export function getNarrativeTrends(baseUrl: string): Promise<NarrativeTrendItem[]> {
  return fetchJson('/api/narrative-trends', baseUrl);
}

export function getMarketDetail(id: string, baseUrl: string): Promise<MarketDetail> {
  return fetchJson(`/api/market/${id}`, baseUrl);
}

export function listMarkets(
  baseUrl: string,
  limit = 100,
  offset = 0,
): Promise<PaginatedMarkets> {
  return fetchJson(`/api/markets?limit=${limit}&offset=${offset}`, baseUrl);
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
