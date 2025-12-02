"""
商务部官网新闻采集器（基于 Playwright）

采集所有分页列表并进入详情页提取正文。
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from bs4 import BeautifulSoup

MOFCOM_BASE_URL = "https://www.mofcom.gov.cn"


class MofcomCollector:
    """采集商务部网站新闻列表"""

    def __init__(
        self,
        urls: Optional[Sequence[str]] = None,
        wait_selector: str = ".txtList_01, .listCon, .txtList_02",
        navigation_timeout: int = 30000,
        selector_timeout: int = 15000,
        category: str = "商务部新闻",
        detail_concurrency: int = 4,
    ):
        """
        Args:
            urls: 需要抓取的栏目页列表
            wait_selector: 页面就绪后等待的 CSS 选择器
            navigation_timeout: 页面跳转超时时间（毫秒）
            selector_timeout: 等待列表元素出现的超时（毫秒）
            category: 归类到的新闻分类
            detail_concurrency: 并发抓取详情页数量
        """
        self.urls: Sequence[str] = urls or (
            "https://www.mofcom.gov.cn/xwfb/ldrhd/index.html",
            "https://www.mofcom.gov.cn/xwfb/bldhd/index.html",
        )
        self.wait_selector = wait_selector
        self.navigation_timeout = navigation_timeout
        self.selector_timeout = selector_timeout
        self.category = category
        self.detail_concurrency = max(1, detail_concurrency)
        self.logger = logging.getLogger("news_analyzer.collectors.mofcom")
        self.news_cache: List[Dict[str, Any]] = []

    async def fetch_all(self) -> List[Dict[str, Any]]:
        """并发抓取所有栏目页，返回去重后的新闻条目"""
        async_playwright = self._load_playwright()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()

            tasks = [self._fetch_single(context, url) for url in self.urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            await browser.close()

        items: List[Dict[str, Any]] = []
        for url, result in zip(self.urls, results):
            if isinstance(result, Exception):
                self.logger.error("获取 %s 失败: %s", url, result)
                continue
            items.extend(result)

        unique_items = self._dedupe(items)
        self.news_cache = unique_items
        self.logger.info("商务部采集完成，共获取 %d 条新闻", len(unique_items))
        return unique_items

    async def fetch_and_save(
        self,
        storage,
        batch_key: Optional[str] = None,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        抓取并直接保存到 NewsStorage，便于在 GUI 中复用。

        Args:
            storage: NewsStorage 实例
            batch_key: 自定义批次名（可选）

        Returns:
            (保存的批次键, 去重后的新闻列表)
        """
        news_items = await self.fetch_all()
        saved_batch = storage.save_news(news_items, filename=batch_key)
        return saved_batch, news_items

    async def _fetch_single(self, context, url: str) -> List[Dict[str, Any]]:
        page = await context.new_page()
        try:
            html_pages = await self._collect_paginated_pages(page, url)
        except Exception as exc:
            self.logger.error("抓取 %s 失败: %s", url, exc)
            return []
        finally:
            await page.close()

        items: List[Dict[str, Any]] = []
        for _, html in html_pages:
            items.extend(self._parse_news(url, html))

        deduped = self._dedupe(items)
        enriched = await self._enrich_with_content(context, deduped)

        self.logger.info("解析 %s 成功，得到 %d 条新闻", url, len(enriched))
        return enriched

    async def _collect_paginated_pages(self, page, url: str) -> List[Tuple[str, str]]:
        """
        逐页抓取，返回 [(page_url, html)]。

        商务部分页通过 data-page 指定页码，对应 index_{page}.html。
        """
        html_pages: List[Tuple[str, str]] = []

        first_html = await self._load_page(page, url)
        html_pages.append((url, first_html))

        total_pages = self._extract_total_pages(first_html)
        if total_pages <= 1:
            return html_pages

        for page_num in range(2, total_pages + 1):
            try:
                await self._click_page(page, page_num)
                html = await page.content()
                html_pages.append((f"{url}#page-{page_num}", html))
            except Exception as exc:
                self.logger.warning("分页 %s 页加载失败: %s", page_num, exc)
                break

        return html_pages

    async def _click_page(self, page, page_num: int) -> None:
        """点击分页组件的 data-page，避免拼接 URL 失败"""
        locator = page.locator(f".layui-laypage a[data-page='{page_num}']")
        await locator.click()
        await page.wait_for_load_state("networkidle")
        await page.wait_for_function(
            """
            (num) => {
              const el = document.querySelector(".layui-laypage .layui-laypage-curr em:last-child");
              return el && el.innerText.trim() === String(num);
            }
            """,
            arg=page_num,
            timeout=self.selector_timeout,
        )
        await page.wait_for_selector(self.wait_selector, timeout=self.selector_timeout)

    async def _load_page(self, page, url: str) -> str:
        await page.goto(
            url,
            timeout=self.navigation_timeout,
            wait_until="domcontentloaded",
        )
        try:
            await page.wait_for_selector(self.wait_selector, timeout=self.selector_timeout)
        except Exception:
            self.logger.warning("列表选择器未出现，降级直接读取页面: %s", url)
            await page.wait_for_load_state("networkidle")
        return await page.content()

    def _extract_total_pages(self, html: str) -> int:
        soup = BeautifulSoup(html, "html.parser")
        max_page = 1

        for anchor in soup.select(".layui-laypage a[data-page]"):
            page_num = self._parse_int(anchor.get("data-page"))
            if page_num:
                max_page = max(max_page, page_num)

        current_text = soup.select_one(".layui-laypage .layui-laypage-curr em:last-child")
        current_page = self._parse_int(current_text.get_text(strip=True) if current_text else "")
        if current_page:
            max_page = max(max_page, current_page)

        return max_page

    def _build_page_url(self, base_url: str, page_num: int) -> str:
        """index.html -> index_2.html 形式"""
        if page_num <= 1:
            return base_url

        if base_url.endswith(".html"):
            prefix, ext = base_url.rsplit(".", 1)
            if prefix.endswith("index"):
                prefix = prefix[: -len("index")]
            return f"{prefix}index_{page_num}.{ext}"

        separator = "" if base_url.endswith("/") else "/"
        return f"{base_url}{separator}index_{page_num}.html"

    def _parse_news(self, url: str, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        links = soup.select(".txtList_01 li a")
        if not links:
            links = soup.select(".listCon ul li a")

        parsed: List[Dict[str, Any]] = []
        collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for anchor in links:
            title = anchor.get("title") or anchor.get_text(strip=True)
            link = anchor.get("href") or ""
            if link.startswith("/"):
                link = f"{MOFCOM_BASE_URL}{link}"

            if not title or not link:
                continue

            parsed.append(
                {
                    "title": title,
                    "link": link,
                    "description": "",
                    "pub_date": "",
                    "source_name": "商务部官网",
                    "source_url": url,
                    "category": self.category,
                    "collected_at": collected_at,
                }
            )

        return parsed

    async def _enrich_with_content(
        self, context, items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not items:
            return []

        semaphore = asyncio.Semaphore(self.detail_concurrency)

        async def _worker(item: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                content, pub_date = await self._fetch_detail(context, item["link"])
            if content:
                item["description"] = content
            if pub_date and not item.get("pub_date"):
                item["pub_date"] = pub_date
            return item

        return await asyncio.gather(*(_worker(item) for item in items))

    async def _fetch_detail(self, context, link: str) -> Tuple[str, str]:
        page = await context.new_page()
        try:
            await page.goto(
                link,
                timeout=self.navigation_timeout,
                wait_until="domcontentloaded",
            )
            html = await page.content()
            return self._extract_detail(html)
        except Exception as exc:
            self.logger.warning("抓取详情页失败 %s: %s", link, exc)
            return "", ""
        finally:
            await page.close()

    def _extract_detail(self, html: str) -> Tuple[str, str]:
        soup = BeautifulSoup(html, "html.parser")

        content_selectors = [
            ".artCon",
            ".art-con",
            ".art-con-bottonmLine",
            ".artText",
            ".conTxt",
            ".article",
            ".newsCon",
            ".txtBox",
            ".TRS_Editor",
            "#zoom",
            "#content",
        ]

        content_text = ""
        for selector in content_selectors:
            node = soup.select_one(selector)
            if not node:
                continue

            paragraphs = []
            for p in node.find_all(["p", "li"], recursive=True):
                text = p.get_text(strip=True)
                if text:
                    paragraphs.append(text)

            if not paragraphs:
                text = node.get_text(" ", strip=True)
                if text:
                    paragraphs.append(text)

            if paragraphs:
                content_text = "\n".join(paragraphs)
                break

        if not content_text:
            body = soup.body.get_text(" ", strip=True) if soup.body else ""
            content_text = body[:800]

        pub_date = ""
        date_selectors = [
            ".time",
            ".news_time",
            ".source",
            ".info",
            ".pubtime",
            ".pubDate",
        ]
        for selector in date_selectors:
            node = soup.select_one(selector)
            if node:
                pub_date = self._extract_date(node.get_text(" ", strip=True))
                if pub_date:
                    break

        if not pub_date:
            page_text = soup.get_text(" ", strip=True)
            pub_date = self._extract_date(page_text)

        return content_text, pub_date

    @staticmethod
    def _dedupe(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        unique: List[Dict[str, Any]] = []
        seen_links = set()
        for item in items:
            link = item.get("link")
            if not link or link in seen_links:
                continue
            seen_links.add(link)
            unique.append(item)
        return unique

    @staticmethod
    def _parse_int(value: Any) -> Optional[int]:
        try:
            return int(str(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _extract_date(text: str) -> str:
        date_pattern = re.compile(r"(20\d{2}[年\-/]\d{1,2}[月\-/]\d{1,2})")
        match = date_pattern.search(text or "")
        if not match:
            return ""
        date_text = match.group(1)
        return date_text.replace("年", "-").replace("月", "-").replace("日", "")

    @staticmethod
    def _load_playwright():
        """延迟加载 Playwright，缺少依赖时提供明确报错"""
        try:
            from playwright.async_api import async_playwright  # type: ignore
        except ImportError as exc:  # pragma: no cover - 仅在运行期提示
            raise ImportError(
                "需要安装 playwright 才能使用 MofcomCollector，请先 pip install playwright"
            ) from exc
        return async_playwright
