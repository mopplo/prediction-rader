from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.config import Settings, get_settings


@dataclass
class ParsedMarket:
    id: str
    slug: str | None
    title: str
    yes_token_id: str | None
    current_probability: float | None
    volume_24h: float | None
    volume_1wk: float | None
    liquidity: float | None
    category: str | None
    image_url: str | None
    end_date: datetime | None
    condition_id: str | None = None
    group_item_id: str | None = None
    topic_key: str | None = None
    event_id: str | None = None
    event_slug: str | None = None
    event_title: str | None = None
    is_active: bool | None = None
    is_closed: bool | None = None
    tags: list[str] = field(default_factory=list)
    created_at: datetime | None = None


@dataclass
class PricePoint:
    timestamp: datetime
    price: float


@dataclass
class ProbabilityChanges:
    change_1h: float | None
    change_24h: float | None
    change_7d: float | None
    has_1h_history: bool = False
    has_24h_history: bool = False
    has_7d_history: bool = False


class PolymarketClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.timeout = self.settings.http_timeout_seconds

    async def fetch_active_markets(self, limit: int | None = None) -> list[ParsedMarket]:
        limit = limit or self.settings.sync_market_limit
        volume_sample = min(self.settings.sync_volume_sample, limit)
        bucket_sample = min(self.settings.sync_bucket_sample, max(0, limit - volume_sample))

        volume_markets = await self._fetch_market_pages(limit=volume_sample, offset=0)
        seen_ids = {market.id for market in volume_markets}
        bucket_markets: list[ParsedMarket] = []

        if bucket_sample > 0:
            offset = volume_sample
            max_scan = volume_sample + bucket_sample * 20
            while len(bucket_markets) < bucket_sample and offset < max_scan:
                page = await self._fetch_market_pages(limit=50, offset=offset)
                if not page:
                    break
                for parsed in page:
                    if parsed.id in seen_ids:
                        continue
                    if not is_information_market(parsed.title, parsed.tags, parsed.category):
                        continue
                    bucket_markets.append(parsed)
                    seen_ids.add(parsed.id)
                    if len(bucket_markets) >= bucket_sample:
                        break
                if len(page) < 50:
                    break
                offset += 50

        return volume_markets + bucket_markets

    async def _fetch_market_pages(self, *, limit: int, offset: int = 0) -> list[ParsedMarket]:
        markets: list[ParsedMarket] = []
        page_size = min(100, limit)
        current_offset = offset

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            while len(markets) < limit:
                response = await client.get(
                    f"{self.settings.gamma_api_base}/markets",
                    params={
                        "active": "true",
                        "closed": "false",
                        "order": "volume24hr",
                        "ascending": "false",
                        "limit": page_size,
                        "offset": current_offset,
                    },
                )
                response.raise_for_status()
                payload = response.json()
                if not payload:
                    break

                for raw in payload:
                    parsed = self._parse_market(raw)
                    if parsed:
                        markets.append(parsed)
                        if len(markets) >= limit:
                            break

                if len(payload) < page_size:
                    break
                current_offset += page_size

        return markets

    async def fetch_market_by_id(self, market_id: str) -> ParsedMarket | None:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.settings.gamma_api_base}/markets/{market_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return self._parse_market(response.json())

    async def fetch_price_history(
        self,
        token_id: str,
        *,
        interval: str = "1w",
        fidelity: int = 60,
    ) -> list[PricePoint]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.settings.clob_api_base}/prices-history",
                params={"market": token_id, "interval": interval, "fidelity": fidelity},
            )
            response.raise_for_status()
            payload = response.json()
            history = payload.get("history", payload if isinstance(payload, list) else [])
            return self._parse_price_history(history)

    async def fetch_batch_price_history(
        self,
        token_ids: list[str],
        *,
        interval: str = "1w",
        fidelity: int = 60,
    ) -> dict[str, list[PricePoint]]:
        results: dict[str, list[PricePoint]] = {}
        chunk_size = 20

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for index in range(0, len(token_ids), chunk_size):
                chunk = token_ids[index : index + chunk_size]
                response = await client.post(
                    f"{self.settings.clob_api_base}/batch-prices-history",
                    json={"markets": chunk, "interval": interval, "fidelity": fidelity},
                )
                response.raise_for_status()
                payload = response.json()
                history_map = payload.get("history", {})
                for token_id, history in history_map.items():
                    results[token_id] = self._parse_price_history(history)

        return results

    def _parse_market(self, raw: dict[str, Any]) -> ParsedMarket | None:
        market_id = str(raw.get("id") or raw.get("conditionId") or "")
        if not market_id:
            return None

        title = raw.get("question") or raw.get("title") or "Untitled market"
        yes_token_id = self._extract_yes_token_id(raw)
        current_probability = self._extract_probability(raw)
        if current_probability is None and not yes_token_id:
            return None

        end_date = self._parse_datetime(raw.get("endDate") or raw.get("end_date_iso"))
        created_at = self._parse_datetime(raw.get("createdAt") or raw.get("startDate"))
        category, event_id, event_slug, event_title, tags = self._extract_event_metadata(raw)
        condition_id = str(raw.get("conditionId") or raw.get("condition_id") or "") or None
        group_item_id = str(raw.get("groupItemId") or raw.get("group_item_id") or "") or None
        topic_key = compute_topic_key(
            event_id=event_id,
            group_item_id=group_item_id,
            title=title,
            event_title=event_title,
        )

        return ParsedMarket(
            id=market_id,
            slug=raw.get("slug"),
            title=title,
            yes_token_id=yes_token_id,
            current_probability=current_probability,
            volume_24h=self._to_float(raw.get("volume24hr")),
            volume_1wk=self._to_float(raw.get("volume1wk")),
            liquidity=self._to_float(raw.get("liquidity") or raw.get("liquidityClob")),
            category=category,
            image_url=raw.get("image") or raw.get("icon"),
            end_date=end_date,
            condition_id=condition_id,
            group_item_id=group_item_id,
            topic_key=topic_key,
            event_id=event_id,
            event_slug=event_slug,
            event_title=event_title,
            is_active=self._to_bool(raw.get("active")),
            is_closed=self._to_bool(raw.get("closed")),
            tags=tags,
            created_at=created_at,
        )

    def _extract_event_metadata(
        self, raw: dict[str, Any]
    ) -> tuple[str | None, str | None, str | None, str | None, list[str]]:
        category = None
        event_id = None
        event_slug = None
        event_title = None
        tags: list[str] = []

        events = raw.get("events") or []
        if events and isinstance(events[0], dict):
            event = events[0]
            category = event.get("category") or event.get("title")
            event_id = str(event.get("id")) if event.get("id") is not None else None
            event_slug = event.get("slug") or event.get("eventSlug")
            event_title = event.get("title")
            for tag in event.get("tags") or []:
                if isinstance(tag, dict):
                    label = tag.get("label") or tag.get("slug")
                    if label:
                        tags.append(str(label).lower())
                elif tag:
                    tags.append(str(tag).lower())

        for tag in raw.get("tags") or []:
            if isinstance(tag, dict):
                label = tag.get("label") or tag.get("slug")
                if label:
                    tags.append(str(label).lower())
            elif tag:
                tags.append(str(tag).lower())

        return category, event_id, event_slug, event_title, sorted(set(tags))

    def _extract_yes_token_id(self, raw: dict[str, Any]) -> str | None:
        token_ids = raw.get("clobTokenIds")
        if isinstance(token_ids, str):
            try:
                parsed = json.loads(token_ids)
            except json.JSONDecodeError:
                parsed = [part.strip() for part in token_ids.split(",") if part.strip()]
        elif isinstance(token_ids, list):
            parsed = token_ids
        else:
            parsed = []

        if not parsed:
            return None
        return str(parsed[0])

    def _extract_probability(self, raw: dict[str, Any]) -> float | None:
        outcome_prices = raw.get("outcomePrices")
        if isinstance(outcome_prices, str):
            try:
                outcome_prices = json.loads(outcome_prices)
            except json.JSONDecodeError:
                outcome_prices = None

        if isinstance(outcome_prices, list) and outcome_prices:
            return self._to_float(outcome_prices[0])

        last_trade = self._to_float(raw.get("lastTradePrice"))
        if last_trade is not None:
            return last_trade

        return self._to_float(raw.get("bestBid"))

    def _parse_price_history(self, history: list[dict[str, Any]]) -> list[PricePoint]:
        points: list[PricePoint] = []
        for item in history:
            timestamp = item.get("t")
            price = item.get("p")
            if timestamp is None or price is None:
                continue
            points.append(
                PricePoint(
                    timestamp=datetime.fromtimestamp(int(timestamp), tz=UTC),
                    price=float(price),
                )
            )
        points.sort(key=lambda point: point.timestamp)
        return points

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_bool(value: Any) -> bool | None:
        if value is None or value == "":
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes"}:
                return True
            if normalized in {"false", "0", "no"}:
                return False
        return bool(value)

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=UTC)
        try:
            normalized = str(value).replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except ValueError:
            return None


def probability_at_or_before(
    points: list[PricePoint],
    target: datetime,
    *,
    max_deviation: timedelta | None = None,
) -> tuple[float | None, bool]:
    if not points:
        return None, False

    eligible = [point for point in points if point.timestamp <= target]
    if not eligible:
        return None, False

    selected = eligible[-1]
    if max_deviation is not None and target - selected.timestamp > max_deviation:
        return None, False

    return selected.price, True


def compute_probability_changes(
    current_probability: float | None,
    history: list[PricePoint],
    *,
    now: datetime | None = None,
    max_deviation_hours: float = 6.0,
) -> ProbabilityChanges:
    if current_probability is None:
        return ProbabilityChanges(None, None, None)

    sorted_history = sorted(history, key=lambda point: point.timestamp)
    now = now or datetime.now(tz=UTC)
    max_deviation = timedelta(hours=max_deviation_hours)

    previous_1h, has_1h = probability_at_or_before(
        sorted_history, now - timedelta(hours=1), max_deviation=max_deviation
    )
    previous_24h, has_24h = probability_at_or_before(
        sorted_history, now - timedelta(hours=24), max_deviation=max_deviation
    )
    previous_7d, has_7d = probability_at_or_before(
        sorted_history, now - timedelta(days=7), max_deviation=timedelta(hours=24)
    )

    return ProbabilityChanges(
        change_1h=current_probability - previous_1h if previous_1h is not None else None,
        change_24h=current_probability - previous_24h if previous_24h is not None else None,
        change_7d=current_probability - previous_7d if previous_7d is not None else None,
        has_1h_history=has_1h,
        has_24h_history=has_24h,
        has_7d_history=has_7d,
    )


def compute_volume_spike(
    volume_24h: float | None,
    volume_1wk: float | None,
    *,
    market_created_at: datetime | None = None,
    now: datetime | None = None,
    min_market_age_days: int = 7,
    min_baseline_daily: float = 100.0,
) -> float | None:
    now = now or datetime.now(tz=UTC)
    if market_created_at is not None and (now - market_created_at) < timedelta(days=min_market_age_days):
        return None

    if volume_24h is None or volume_1wk is None:
        return None

    baseline_total = volume_1wk - volume_24h
    if baseline_total <= 0:
        return None

    baseline_daily = baseline_total / 6
    if baseline_daily < min_baseline_daily:
        return None

    return volume_24h / baseline_daily


def history_coverage_hours(history: list[PricePoint], *, now: datetime | None = None) -> float:
    if not history:
        return 0.0
    now = now or datetime.now(tz=UTC)
    earliest = min(point.timestamp for point in history)
    return max(0.0, (now - earliest).total_seconds() / 3600)


EXCLUDED_TAG_KEYWORDS = {
    "sports",
    "esports",
    "nba",
    "nfl",
    "mlb",
    "soccer",
    "tennis",
    "atp",
    "wta",
    "lol",
    "league of legends",
    "weather",
    "climate",
}

EXCLUDED_TITLE_PATTERNS = [
    re.compile(r"\blol:\b", re.I),
    re.compile(r"\bvs\b.*\bbo\d+\b", re.I),
    re.compile(r"open:.*\bvs\b", re.I),
    re.compile(r"\batp\b", re.I),
    re.compile(r"\bwta\b", re.I),
    re.compile(r"\bup or down\b", re.I),
    re.compile(r"\bhighest temperature\b", re.I),
    re.compile(r"\btemperature in\b", re.I),
    re.compile(r"\bprice of bitcoin be above\b", re.I),
    re.compile(r"\bprice of bitcoin be below\b", re.I),
    re.compile(r"\bon (january|february|march|april|may|june|july|august|september|october|november|december)\b", re.I),
    re.compile(r"\bon \d{1,2}/\d{1,2}\b", re.I),
    re.compile(r"\btoday\b", re.I),
    re.compile(r"\btomorrow\b", re.I),
]

INCLUDED_TAG_KEYWORDS = {
    "politics",
    "elections",
    "economy",
    "macro",
    "technology",
    "tech",
    "ai",
    "science",
    "crypto",
    "bitcoin",
    "regulation",
    "geopolitics",
    "world",
    "business",
}


def is_short_cycle_market(title: str, tags: list[str]) -> bool:
    normalized_tags = {tag.lower() for tag in tags}
    if normalized_tags & EXCLUDED_TAG_KEYWORDS:
        return True

    for pattern in EXCLUDED_TITLE_PATTERNS:
        if pattern.search(title):
            return True

    return False


def normalize_title_family(title: str) -> str:
    normalized = re.sub(
        r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b",
        "",
        title,
        flags=re.I,
    )
    normalized = re.sub(r"\$\d[\d,]*(?:\.\d+)?[kKmMbB]?", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip().lower()
    return normalized


def compute_topic_key(
    *,
    event_id: str | None,
    group_item_id: str | None,
    title: str,
    event_title: str | None = None,
) -> str:
    if event_id:
        return f"event:{event_id}"
    if group_item_id:
        return f"group:{group_item_id}"
    if event_title:
        return f"event_title:{event_title.lower()}"
    family = normalize_title_family(title)
    if family:
        return f"title:{family}"
    return f"market:{title.lower()}"


def is_information_market(title: str, tags: list[str], category: str | None) -> bool:
    normalized_tags = {tag.lower() for tag in tags}
    if normalized_tags & INCLUDED_TAG_KEYWORDS:
        return True

    haystack = " ".join([title.lower(), (category or "").lower(), " ".join(normalized_tags)])
    keywords = (
        "election",
        "president",
        "fed",
        "inflation",
        "gdp",
        "ai",
        "openai",
        "regulation",
        "bitcoin",
        "ethereum",
        "war",
        "ceasefire",
        "tariff",
        "recession",
        "gpt",
        "trump",
        "congress",
        "senate",
    )
    return any(keyword in haystack for keyword in keywords)
