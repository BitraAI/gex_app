"""Live news feed for tracked tickers using Yahoo Finance RSS.

Polls headlines every 5 minutes in the background and caches them
per-ticker.  Also exposes a ``get_new_alerts`` method for pushing
breaking stories through the existing Telegram alert pipeline.
"""

import asyncio
import time
from typing import Any

import feedparser

POLL_INTERVAL = 300  # 5 minutes

YAHOO_RSS_URL = "https://finance.yahoo.com/rss/headline?s={symbol}"


class NewsService:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        self._articles: list[dict[str, Any]] = []
        self._seen: set[str] = set()
        self._last_poll: float = 0.0
        self._running = False
        self._tickers: list[str] = []

    @property
    def is_running(self) -> bool:
        return self._running

    def update_tickers(self, tickers: list[str]):
        self._tickers = list(tickers)

    def start(self):
        self._running = True

    def stop(self):
        self._running = False

    def get_all_news(self, max_items: int = 30) -> list[dict[str, Any]]:
        return self._articles[:max_items]

    def get_new_alerts(self) -> list[str]:
        """Return all unseen headlines as alerts."""
        alerts: list[str] = []
        for item in self._articles:
            link = item.get("link", "")
            if link not in self._seen:
                alerts.append(item.get("title", ""))
        self._seen.update(a.get("link", "") for a in self._articles)
        return alerts

    async def poll(self, symbols: list[str]):
        """Poll RSS feeds for all tracked symbols.  Skips polling if
        less than ``POLL_INTERVAL`` seconds have passed since the last
        successful poll."""
        if not self._running:
            return
        now = time.time()
        if now - self._last_poll < POLL_INTERVAL:
            return
        self._last_poll = now

        new_articles: list[dict[str, Any]] = []
        for sym in symbols:
            try:
                url = YAHOO_RSS_URL.format(symbol=sym)
                f = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: feedparser.parse(url)
                )
                for entry in f.entries:
                    title = entry.get("title", "")
                    link = entry.get("link", "")
                    if link in self._seen:
                        continue
                    # Skip paywalled / rate-limited placeholder articles
                    if "reached a limit" in title.lower() or "sign in" in title.lower():
                        continue
                    # Skip Trefis (paid subscription)
                    if "trefis" in title.lower() or "trefis" in link.lower():
                        continue
                    self._seen.add(link)
                    new_articles.append({
                        "title": title,
                        "link": link,
                        "published": entry.get("published", ""),
                    })
            except Exception:
                pass
        if new_articles:
            self._articles = new_articles + self._articles
            # Cap at 200 to avoid unbounded memory growth
            if len(self._articles) > 200:
                self._articles = self._articles[:200]
