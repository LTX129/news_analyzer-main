"""
国际组织数据源配置（非RSS）

这些源采用官方JSON接口或HTML列表页，需要专用采集器处理。
"""

def get_org_sources():
    return [
        {
            "id": "world_bank",
            "name": "世界银行新闻",
            "url": "https://search.worldbank.org/api/v2/news?format=json&rows=30&language=English",
            "category": "国际组织",
            "type": "json",
            "priority": 1,
            "provider": "official"
        },
        {
            "id": "imf",
            "name": "IMF新闻",
            "url": "https://www.imf.org/en/News",
            "category": "国际组织",
            "type": "html",
            "priority": 1,
            "provider": "official",
            "base_url": "https://www.imf.org"
        },
        {
            "id": "oecd",
            "name": "OECD新闻室",
            "url": "https://www.oecd.org/newsroom/",
            "category": "国际组织",
            "type": "html",
            "priority": 1,
            "provider": "official",
            "base_url": "https://www.oecd.org"
        },
        {
            "id": "wto",
            "name": "WTO新闻",
            "url": "https://www.wto.org/english/news_e/news_e.htm",
            "category": "国际组织",
            "type": "html",
            "priority": 1,
            "provider": "official",
            "base_url": "https://www.wto.org"
        },
        {
            "id": "unctad",
            "name": "UNCTAD新闻",
            "url": "https://unctad.org/unctad-news",
            "category": "国际组织",
            "type": "html",
            "priority": 1,
            "provider": "official",
            "base_url": "https://unctad.org"
        },
        {
            "id": "itu",
            "name": "ITU新闻",
            "url": "https://news.itu.int/",
            "category": "国际组织",
            "type": "html",
            "priority": 1,
            "provider": "official",
            "base_url": "https://news.itu.int"
        }
    ]
