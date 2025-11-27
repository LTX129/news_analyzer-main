"""
RSS新闻收集器

负责从RSS源获取新闻数据。
"""

import logging
import time
import re
from typing import Dict, List, Any

import feedparser
import requests


class RSSCollector:
    """RSS新闻收集器类"""
    
    def __init__(self):
        """初始化RSS收集器"""
        self.logger = logging.getLogger('news_analyzer.collectors.rss')
        self.sources: List[Dict[str, Any]] = []
        self.news_cache: List[Dict[str, Any]] = []

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; NewsAnalyzer/1.0; +mailto:news@example.com)",
            "Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.7"
        })
        # 与旧实现一致，默认不校验证书以提升兼容性（需在生产环境按需打开）
        self.verify_ssl = False
        self.request_timeout = 10
    
    def add_source(
        self,
        url,
        name=None,
        category="未分类",
        is_user_added=False,
        provider="official",
        priority=2,
        source_type="rss",
        **extra_fields
    ):
        """添加RSS新闻源
        
        Args:
            url: RSS源URL
            name: 来源名称（可选）
            category: 分类名称（可选）
            is_user_added: 是否为用户手动添加
            provider: 数据来源类型（official / rsshub / thirdparty）
            priority: 优先级（1=高，2=正常，3=次要）
            source_type: 源类型（rss / json / html）
            extra_fields: 额外透传字段
        """
        if not url:
            raise ValueError("URL不能为空")
        
        # 如果没有提供名称，使用URL作为默认名称
        if not name:
            name = url.split("//")[-1].split("/")[0]
        
        # 检查是否已存在相同URL的源
        for source in self.sources:
            if source['url'] == url:
                self.logger.warning(f"RSS源已存在: {url}")
                return
        
        # 添加新源
        source_info = {
            'url': url,
            'name': name,
            'category': category,
            'is_user_added': is_user_added,
            'provider': provider,
            'priority': priority,
            'source_type': source_type
        }
        source_info.update(extra_fields)
        
        self.sources.append(source_info)
        
        self.logger.info(f"添加RSS源: {name} ({url}), 分类: {category}")
    
    def fetch_from_source(self, url):
        """从特定RSS源获取新闻
        
        Args:
            url: RSS源URL
            
        Returns:
            list: 新闻条目列表
        """
        source = None
        for s in self.sources:
            if s['url'] == url:
                source = s
                break
        
        if not source:
            self.logger.warning(f"未找到RSS源: {url}")
            return []
        
        if source.get('source_type', 'rss') != 'rss':
            self.logger.info(f"源 {source['name']} 类型为 {source.get('source_type')}，当前仅支持RSS，已跳过")
            return []
        
        return self._fetch_rss(source)
    
    def fetch_all(self):
        """从所有RSS源获取新闻
        
        Returns:
            list: 新闻条目列表
        """
        all_news = []
        
        for source in self.sources:
            if source.get('source_type', 'rss') != 'rss':
                self.logger.info(f"跳过非RSS源: {source['name']} ({source.get('source_type')})")
                continue
            try:
                items = self._fetch_rss(source)
                all_news.extend(items)
                self.logger.info(f"从 {source['name']} 获取了 {len(items)} 条新闻")
            except Exception as e:
                self.logger.error(f"从 {source['name']} 获取新闻失败: {str(e)}")
        
        # 去重
        unique_news = self._remove_duplicates(all_news)
        
        # 更新缓存
        self.news_cache = unique_news
        
        return unique_news
    
    def get_all_news(self):
        """获取所有缓存的新闻
        
        Returns:
            list: 新闻条目列表
        """
        return self.news_cache
    
    def get_news_by_category(self, category):
        """按分类获取新闻
        
        Args:
            category: 分类名称
            
        Returns:
            list: 该分类下的新闻条目列表
        """
        if not category or category == "所有":
            return self.news_cache
        
        return [item for item in self.news_cache if item.get('category') == category]
    
    def search_news(self, query):
        """搜索新闻
        
        Args:
            query: 搜索关键词
            
        Returns:
            list: 匹配的新闻条目列表
        """
        if not query:
            return self.news_cache
        
        query_lower = query.lower()
        results = []
        
        for item in self.news_cache:
            title = item.get('title', '').lower()
            description = item.get('description', '').lower()
            
            if query_lower in title or query_lower in description:
                results.append(item)
        
        return results
    
    def get_sources(self):
        """获取所有RSS源
        
        Returns:
            list: RSS源列表
        """
        return self.sources
    
    def get_categories(self):
        """获取所有分类
        
        Returns:
            list: 分类名称列表
        """
        categories = set()
        for source in self.sources:
            categories.add(source['category'])
        return sorted(list(categories))
    
    def _fetch_rss(self, source):
        """从RSS源获取新闻
        
        Args:
            source: 新闻源信息字典
            
        Returns:
            list: 新闻条目列表
        """
        items = []
        
        try:
            response = self.session.get(
                source['url'],
                timeout=self.request_timeout,
                verify=self.verify_ssl
            )
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '').lower()
            if content_type and all(t not in content_type for t in ['xml', 'rss', 'atom']):
                self.logger.warning(f"{source['name']} 返回非RSS内容（Content-Type: {content_type}），已跳过解析")
                return []

            parsed = feedparser.parse(response.content)
            if parsed.bozo:
                self.logger.warning(f"{source['name']} RSS 解析存在问题: {parsed.bozo_exception}")

            for entry in parsed.entries:
                news_item = self._parse_entry(entry, source)
                if news_item:
                    items.append(news_item)

            self.logger.info(f"从 {source['name']} 获取了 {len(items)} 条新闻")

        except requests.exceptions.RequestException as exc:
            self.logger.error(f"获取 {source['name']} 的新闻失败: {exc}")
        except Exception as exc:  # 兜底避免单个源阻塞
            self.logger.error(f"解析 {source['name']} 的新闻时出错: {exc}", exc_info=True)
        
        return items
    
    def _parse_entry(self, entry, source):
        """使用 feedparser 解析条目"""
        title = entry.get('title', '')
        link = entry.get('link', '')
        if not title or not link:
            return None

        description = ""
        if 'summary' in entry:
            description = entry.get('summary', '') or ''
        elif entry.get('content'):
            description = entry.content[0].get('value', '') if entry.content else ''

        description = self._clean_html(description)
        pub_date = entry.get('published', '') or entry.get('updated', '')

        return {
            'title': title,
            'link': link,
            'description': description,
            'pub_date': pub_date,
            'source_name': source['name'],
            'source_url': source['url'],
            'category': source['category'],
            'collected_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _clean_html(self, text):
        """去除简单HTML标签"""
        if not text:
            return ""
        cleaned = re.sub(r'<[^>]+>', ' ', text)
        return re.sub(r'\s+', ' ', cleaned).strip()
    
    def _remove_duplicates(self, news_items):
        """移除重复的新闻条目（按链接去重）"""
        unique_items = {}
        
        for item in news_items:
            key = item.get('link', '')
            if key and key not in unique_items:
                unique_items[key] = item
        
        return list(unique_items.values())
