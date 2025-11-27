"""
预设新闻源模块

提供默认的RSS新闻源列表，按类别组织。
"""

RSSHUB_BASE = "https://rsshub.rssforever.com"

def get_default_sources():
    """
    获取默认的RSS新闻源列表
    
    Returns:
        list: 包含预设新闻源信息的字典列表
    """
    return [
        # 综合新闻 - 中文
        {
            "url": "https://www.thepaper.cn/rss_newslist.jsp",
            "name": "澎湃新闻",
            "category": "综合新闻"
        },
        {
            "url": f"{RSSHUB_BASE}/reuters/cn/china",
            "name": "路透中文网",
            "category": "综合新闻",
            "provider": "rsshub",
            "is_third_party": True
        },
        {
            "url": "https://www.zaobao.com/rss/realtime/china",
            "name": "联合早报",
            "category": "综合新闻"
        },
        {
            "url": "https://www.ftchinese.com/rss/feed",
            "name": "FT中文网",
            "category": "综合新闻"
        },
        {
            "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
            "name": "纽约时报国际",
            "category": "国际新闻"
        },
        {
            "url": "https://feeds.washingtonpost.com/rss/world",
            "name": "华盛顿邮报国际",
            "category": "国际新闻"
        },
        {
            "url": "https://www.theguardian.com/world/rss",
            "name": "卫报国际",
            "category": "国际新闻"
        },
        {
            "url": "https://www.aljazeera.com/xml/rss/all.xml",
            "name": "半岛电视台",
            "category": "国际新闻"
        },
        {
            "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
            "name": "BBC国际",
            "category": "国际新闻"
        },
        {
            "url": "http://rss.cnn.com/rss/edition_world.rss",
            "name": "CNN国际",
            "category": "国际新闻"
        },
        {
            "url": "https://www.nhk.or.jp/rss/news/cat6.xml",
            "name": "NHK国际",
            "category": "国际新闻"
        },
        
        # 科技新闻
        {
            "url": "https://www.wired.com/feed/rss",
            "name": "WIRED",
            "category": "科技新闻"
        },
        {
            "url": "https://www.engadget.com/rss.xml",
            "name": "Engadget",
            "category": "科技新闻"
        },
        {
            "url": "https://www.theverge.com/rss/index.xml",
            "name": "The Verge",
            "category": "科技新闻"
        },
        {
            "url": "https://techcrunch.com/feed/",
            "name": "TechCrunch",
            "category": "科技新闻"
        },
        {
            "url": "https://feeds.arstechnica.com/arstechnica/index",
            "name": "Ars Technica",
            "category": "科技新闻"
        },
        {
            "url": "https://www.solidot.org/index.rss",
            "name": "Solidot",
            "category": "科技新闻"
        },
        {
            "url": f"{RSSHUB_BASE}/36kr/news/latest",
            "name": "36氪",
            "category": "科技新闻",
            "provider": "rsshub",
            "is_third_party": True
        },
        {
            "url": "https://sspai.com/feed",
            "name": "少数派",
            "category": "科技新闻"
        },
        
        # 商业与金融
        {
            "url": "https://www.economist.com/finance-and-economics/rss.xml",
            "name": "经济学人",
            "category": "商业与金融"
        },
        {
            "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
            "name": "华尔街日报市场",
            "category": "商业与金融"
        },
        {
            "url": "https://www.ft.com/rss/home/uk",
            "name": "金融时报",
            "category": "商业与金融"
        },
        {
            "url": "https://www.forbes.com/business/feed/",
            "name": "福布斯商业",
            "category": "商业与金融"
        },
        {
            "url": "https://www.businessinsider.com/rss",
            "name": "商业内幕",
            "category": "商业与金融"
        },
        {
            "url": "https://www.cnbc.com/id/10001147/device/rss/rss.html",
            "name": "CNBC财经",
            "category": "商业与金融"
        },
        {
            "url": "https://rsshub.app/caixin/finance/regulation",
            "name": "财新网",
            "category": "商业与金融"
        },
        
        # 政治新闻
        {
            "url": "https://rss.politico.com/politics.xml",
            "name": "Politico",
            "category": "政治新闻"
        },
        {
            "url": "https://www.realclearpolitics.com/index.xml",
            "name": "RealClearPolitics",
            "category": "政治新闻"
        },
        {
            "url": "https://thehill.com/feed",
            "name": "The Hill",
            "category": "政治新闻"
        },
        {
            "url": "https://feeds.nbcnews.com/nbcnews/public/politics",
            "name": "NBC政治",
            "category": "政治新闻"
        },
        {
            "url": "https://feeds.bbci.co.uk/news/politics/rss.xml",
            "name": "BBC政治",
            "category": "政治新闻"
        },
        
        # 科学新闻
        {
            "url": "https://www.science.org/rss/news_current.xml",
            "name": "Science",
            "category": "科学新闻"
        },
        {
            "url": "https://www.nature.com/nature.rss",
            "name": "Nature",
            "category": "科学新闻"
        },
        {
            "url": "https://feeds.newscientist.com/science-news",
            "name": "New Scientist",
            "category": "科学新闻"
        },
        {
            "url": "https://phys.org/rss-feed/",
            "name": "Phys.org",
            "category": "科学新闻"
        },
        {
            "url": "https://www.scientificamerican.com/feed/",
            "name": "Scientific American",
            "category": "科学新闻"
        },
        {
            "url": "https://www.space.com/feeds/all",
            "name": "Space.com",
            "category": "科学新闻"
        },
        
        # 体育新闻
        {
            "url": "https://www.espn.com/espn/rss/news",
            "name": "ESPN",
            "category": "体育新闻"
        },
        {
            "url": "https://www.skysports.com/rss/12040",
            "name": "Sky Sports",
            "category": "体育新闻"
        },
        {
            "url": "http://rss.nytimes.com/services/xml/rss/nyt/Sports.xml",
            "name": "纽约时报体育",
            "category": "体育新闻"
        },
        {
            "url": "https://api.foxsports.com/v1/rss?partnerKey=zBaFxRyGKCfxBagJG9b8pqLyndmvo7UU",
            "name": "Fox Sports",
            "category": "体育新闻"
        },
        {
            "url": "https://www.cbssports.com/rss/headlines",
            "name": "CBS Sports",
            "category": "体育新闻"
        },
        {
            "url": "https://www.theguardian.com/sport/rss",
            "name": "卫报体育",
            "category": "体育新闻"
        },
        
        # 娱乐新闻
        {
            "url": "https://www.hollywoodreporter.com/feed/",
            "name": "好莱坞记者",
            "category": "娱乐新闻"
        },
        {
            "url": "https://variety.com/feed/",
            "name": "Variety",
            "category": "娱乐新闻"
        }
    ]


def initialize_sources(rss_collector):
    """
    使用预设源初始化RSS收集器
    
    Args:
        rss_collector: RSSCollector实例
    
    Returns:
        int: 添加的源数量
    """
    sources = get_default_sources()
    count = 0
    
    for source in sources:
        try:
            rss_collector.add_source(
                url=source["url"],
                name=source["name"],
                category=source["category"],
                is_user_added=source.get("is_user_added", False),
                provider=source.get("provider", "official"),
                priority=source.get("priority", 2),
                source_type=source.get("source_type", "rss")
            )
            count += 1
        except Exception as e:
            print(f"添加源失败: {source['name']} - {str(e)}")
    
    return count
