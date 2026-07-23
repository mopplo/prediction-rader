export function formatPercent(value: number | null | undefined, digits = 0): string {
  if (value == null || Number.isNaN(value)) {
    return '—';
  }
  return `${(value * 100).toFixed(digits)}%`;
}

export function formatChange(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return '—';
  }
  const points = (value * 100).toFixed(1);
  return `${value > 0 ? '+' : ''}${points} pp`;
}

export function formatChange7d(
  value: number | null | undefined,
  unavailableReason?: string | null,
): string {
  if (value != null && !Number.isNaN(value)) {
    return formatChange(value);
  }
  return unavailableReason ?? 'Unavailable';
}

export function formatVolume(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return '—';
  }
  if (value >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(1)}M`;
  }
  if (value >= 1_000) {
    return `$${(value / 1_000).toFixed(1)}K`;
  }
  return `$${Math.round(value).toLocaleString()}`;
}

export function formatSpike(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return 'Baseline unavailable';
  }
  return `${value.toFixed(1)}x baseline`;
}

export function formatConfidence(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return 'Unknown confidence';
  }
  return `${Math.round(value)} data confidence`;
}

export function formatDataConfidence(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return '—';
  }
  if (value >= 90) {
    return `Very High (${Math.round(value)})`;
  }
  if (value >= 70) {
    return `High (${Math.round(value)})`;
  }
  if (value >= 50) {
    return `Medium (${Math.round(value)})`;
  }
  return `Low (${Math.round(value)})`;
}

export function formatScore(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return '—';
  }
  return Math.round(value).toString();
}

export function formatScoreOutOf100(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return '—';
  }
  return `${Math.round(value)}/100`;
}

export function formatCount(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return '—';
  }
  return Math.round(value).toLocaleString('en-US');
}

export function formatSyncCadence(minutes: number | null | undefined): string {
  if (minutes == null || Number.isNaN(minutes) || minutes <= 0) {
    return 'Every 2 hours';
  }
  if (minutes >= 60 && minutes % 60 === 0) {
    const hours = minutes / 60;
    return `Every ${hours} hour${hours === 1 ? '' : 's'}`;
  }
  return `Every ${Math.round(minutes)} min`;
}

export function dailyRadarWhySelected(item: {
  why_it_moved?: string[] | null;
  signal_reason?: string | null;
}): string {
  const why = item.why_it_moved?.[0]?.trim();
  if (why) {
    return why;
  }
  const reason = item.signal_reason?.trim();
  if (reason) {
    return reason;
  }
  return 'High-confidence signal with meaningful movement';
}

export function formatSignificance(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return '—';
  }
  if (value >= 70) {
    return `High (${Math.round(value)})`;
  }
  if (value >= 40) {
    return `Moderate (${Math.round(value)})`;
  }
  return `Low (${Math.round(value)})`;
}

export function formatCoverageHours(value: number | null | undefined): string {
  if (value == null || value <= 0) {
    return 'No history yet';
  }
  if (value >= 24) {
    const days = Math.round(value / 24);
    return `${days}d of history`;
  }
  return `${Math.round(value)}h of history`;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) {
    return '—';
  }
  return new Date(value).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatSyncedAtUtc(value: string | null | undefined): string {
  if (!value) {
    return '—';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '—';
  }
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, '0');
  const day = String(date.getUTCDate()).padStart(2, '0');
  const hours = String(date.getUTCHours()).padStart(2, '0');
  const minutes = String(date.getUTCMinutes()).padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes} UTC`;
}

export function formatRelativeUpdated(
  value: string | null | undefined,
  now: Date = new Date(),
): string {
  if (!value) {
    return 'Update time unavailable';
  }
  const updatedAt = new Date(value);
  if (Number.isNaN(updatedAt.getTime())) {
    return 'Update time unavailable';
  }
  const diffMs = Math.max(0, now.getTime() - updatedAt.getTime());
  const diffMinutes = Math.floor(diffMs / 60_000);
  if (diffMinutes < 1) {
    return 'Updated just now';
  }
  if (diffMinutes < 60) {
    return `Updated ${diffMinutes} minute${diffMinutes === 1 ? '' : 's'} ago`;
  }
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `Updated ${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
  }
  const diffDays = Math.floor(diffHours / 24);
  return `Updated ${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
}

export function formatMarketStatus(
  status: string | null | undefined,
  resolvesInDays: number | null | undefined,
): string {
  if (status === 'closed') {
    return 'Closed';
  }
  if (status === 'open') {
    if (resolvesInDays == null) {
      return 'Open';
    }
    return `Open · Resolves in ${resolvesInDays} day${resolvesInDays === 1 ? '' : 's'}`;
  }
  return 'Status unavailable';
}

export function changeClass(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value) || value === 0) {
    return 'neutral';
  }
  return value > 0 ? 'positive' : 'negative';
}

export function narrativeDirectionLabel(
  direction: string | null | undefined,
  coherence: number | null | undefined,
  minCoherence = 0.6,
): string {
  if (!direction || coherence == null || coherence < minCoherence) {
    return 'Mixed / active';
  }
  if (direction === 'higher') {
    return 'Moving higher';
  }
  if (direction === 'lower') {
    return 'Moving lower';
  }
  return 'Mixed / active';
}
