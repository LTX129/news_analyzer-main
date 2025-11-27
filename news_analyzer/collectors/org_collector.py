"""
国际组织新闻采集器（非RSS）

使用官方 JSON 或 HTML 列表页抓取新闻，避免依赖不稳定的 RSS。
"""

import logging
import time
from typing import List, Dict, Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from news_analyzer.collectors.org_sources import get_org_sources


class OrgCollector:
    """国际组织专用采集器"""

    def __init__(self):
        self.logger = logging.getLogger("news_analyzer.collectors.org")
        self.sources: List[Dict[str, Any]] = get_org_sources()
        self.news_cache: List[Dict[str, Any]] = []

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; NewsAnalyzer/1.0; +mailto:news@example.com)",
            "Accept": "text/html,application/json;q=0.9,*/*;q=0.8"
        })
        self.request_timeout = 10

    def fetch_all(self) -> List[Dict[str, Any]]:
        """抓取所有国际组织源"""
        all_items: List[Dict[str, Any]] = []
        for source in self.sources:
            try:
                items = self._fetch_source(source)
                all_items.extend(items)
                self.logger.info("从 %s 获取了 %d 条新闻", source["name"], len(items))
            except Exception as exc:
                self.logger.error("获取 %s 的新闻失败: %s", source["name"], exc)

        self.news_cache = self._dedupe(all_items)
        return self.news_cache

    def get_sources(self) -> List[Dict[str, Any]]:
        return self.sources

    def get_categories(self) -> List[str]:
        categories = {s["category"] for s in self.sources}
        return sorted(list(categories))

    def _fetch_source(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        source_id = source.get("id")
        if source_id == "world_bank":
            return self._fetch_world_bank(source)
        if source_id == "imf":
            return self._fetch_imf(source)
        if source_id == "oecd":
            return self._fetch_oecd(source)
        if source_id == "wto":
            return self._fetch_wto(source)
        if source_id == "unctad":
            return self._fetch_unctad(source)
        if source_id == "itu":
            return self._fetch_itu(source)
        self.logger.warning("未实现的国际组织源: %s", source_id)
        return []

    def _fetch_world_bank(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []

        resp = self.session.get(source["url"], timeout=self.request_timeout)
        resp.raise_for_status()
        data = resp.json()

        docs = data.get("documents") or {}
        if isinstance(docs, dict):
            iterable = docs.values()
        else:
            iterable = docs or []

        for entry in iterable:
            # title 可能是 list / dict，这里做个兜底
            raw_title = entry.get("title") or ""
            if isinstance(raw_title, list):
                title = " ".join(t for t in raw_title if isinstance(t, str))
            elif isinstance(raw_title, dict):
                title = raw_title.get("value", "") or raw_title.get("0", "")
            else:
                title = str(raw_title)

            raw_descr = entry.get("descr") or entry.get("content") or ""
            if isinstance(raw_descr, list):
                description = " ".join(t for t in raw_descr if isinstance(t, str))
            else:
                description = str(raw_descr)

            link = entry.get("url") or entry.get("link") or ""
            pub_date = entry.get("lnchdt") or entry.get("date") or entry.get("publishedDate") or ""

            if not title or not link:
                continue

            items.append(self._build_item(title, link, description, pub_date, source))

        return items

    def _fetch_imf(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self._fetch_html_links(
            source,
            link_filter="/en/News/",
            title_selector="a[href*='/en/News/']"
        )

    def _fetch_oecd(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self._fetch_html_links(
            source,
            container_selector=".newsroom-item, article, li",
            link_filter="/newsroom/"
        )

    def _fetch_wto(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self._fetch_html_links(
            source,
            link_filter="/english/news_e/news",
            title_selector="a[href*='news_e/news']"
        )

    def _fetch_unctad(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self._fetch_html_links(
            source,
            title_selector="a[href^='/news/']",
            link_filter="/news/"
        )

    def _fetch_itu(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self._fetch_html_links(
            source,
            container_selector="article, .post",
            link_filter="/"
        )

    def _fetch_html_links(
            self,
            source: Dict[str, Any],
            container_selector: str = "",
            link_filter: str = "",
            title_selector: str = ""
    ) -> List[Dict[str, Any]]:
        resp = self.session.get(source["url"], timeout=self.request_timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        if title_selector:
            links = soup.select(title_selector)
        elif container_selector:
            containers = soup.select(container_selector)
            links = []
            for c in containers:
                links.extend(c.find_all("a", href=True))

            # 如果容器里啥都没有，降级用全局 a
            if not links:
                links = soup.find_all("a", href=True)
        else:
            links = soup.find_all("a", href=True)

        items: List[Dict[str, Any]] = []
        seen = set()

        for a in links:
            href = a.get("href")
            if not href:
                continue
            if link_filter and link_filter not in href:
                continue

            full_link = urljoin(source.get("base_url") or source["url"], href)
            if full_link in seen:
                continue
            seen.add(full_link)

            title = a.get_text(strip=True)
            if not title:
                continue

            items.append(self._build_item(
                title=title,
                link=full_link,
                description="",
                pub_date="",
                source=source
            ))

        return items

    def _build_item(self, title: str, link: str, description: str, pub_date: str, source: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "title": title,
            "link": link,
            "description": description.strip(),
            "pub_date": pub_date,
            "source_name": source["name"],
            "source_url": source["url"],
            "category": source["category"],
            "collected_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def _dedupe(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        unique = {}
        for item in items:
            key = item.get("link")
            if key and key not in unique:
                unique[key] = item
        return list(unique.values())
