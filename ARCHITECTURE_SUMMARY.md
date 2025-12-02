# 新闻聚合与分析系统架构综述

## 项目定位
- 以 PyQt5 为主界面的新闻聚合工具，抓取 RSS 与国际组织站点新闻，落盘 PostgreSQL 并提供本地 LLM（Ollama）分析与聊天辅助。
- 入口脚本有两个等价版本：根目录的 `main.py` 与包内 `news_analyzer/main.py`，均完成日志、存储、采集器和 UI 的组装。

## 核心流程
- 启动：`main.py` 创建日志目录与配置，实例化 `NewsStorage`（PostgreSQL 连接）、`RSSCollector`、`OrgCollector`，加载预设源 `initialize_sources` 后启动 `MainWindow`。
- 获取新闻：`MainWindow.refresh_news` 触发并行抓取 RSS 与国际组织源，去重后写入数据库；界面侧边栏与列表同步分类与内容。
- 浏览与过滤：`SearchPanel` 支持关键词检索；`CategorySidebar` 按分类筛选；日期清洗设置（QSettings 持久化）用于过滤旧新闻。
- 分析与对话：选中新闻后 `LLMPanel` 走本地 Ollama 的 OpenAI 兼容接口做摘要/深度分析等；`ChatPanel` 可带入已选新闻的上下文进行聊天。
- 历史/持久化：`NewsStorage` 以批次键保存新闻，启动时加载最近批次填充缓存与 UI，`HistoryPanel` 可浏览历史批次并回填列表。

## 模块组成
- UI（`news_analyzer/ui`）  
  - `main_window.py`：主框架，菜单/工具栏、状态栏、分割布局，组织搜索、侧边栏、新闻列表、LLM 分析和聊天面板。  
  - `search_panel.py`：关键词搜索。`sidebar.py`：分类树。`news_list.py`：新闻列表与选择事件。  
  - `llm_panel.py`：选择分析类型并在子线程调用 LLM，展示 HTML 结果与进度。  
  - `chat_panel.py`：聊天输入、上下文选择、模拟流式输出。  
  - `history_panel.py`、`history_tab.py`：浏览历史批次，加载旧新闻；`llm_settings.py`：本地模型 API 参数配置。
- 采集器（`news_analyzer/collectors`）  
  - `rss_collector.py`：Feedparser+Requests 抓取 RSS，支持添加源、按分类/关键字过滤、去重缓存。  
  - `default_sources.py`：预置数十个 RSS 源（综合/国际/科技/商业等），可切换 RSSHub 基址。  
  - `org_collector.py`：针对世界银行、IMF、OECD、WTO、UNCTAD、ITU 等站点的 JSON/HTML 抓取；含 NewsAPI JSON 兼容。  
  - `org_sources.py`：国际组织源配置（URL、分类、解析策略）。
- 存储（`news_analyzer/storage/news_storage.py`）  
  - 通过 psycopg2 连接 PostgreSQL，创建 `news_batches` 与 `news_items`；按批次写入 JSONB，`link` 唯一索引去重。  
  - 提供 `save_news`、`load_news`（默认取最新批次）、`list_news_files` 等接口。
- LLM（`news_analyzer/llm/llm_client.py`）  
  - 默认本地 Ollama，OpenAI 兼容 `/v1/chat/completions`；`analyze_news` 生成摘要/观点等 HTML 片段；`chat` 支持上下文并模拟流式回调。  
  - 依赖环境变量 `LLM_API_URL`、`LLM_MODEL`（在 UI 设置中写入 QSettings 并导出到 env）。

## 数据与运行
- 运行：`python main.py`；依赖见 `requirements.txt`（PyQt5、feedparser、requests、psycopg2、beautifulsoup4 等）。  
- 数据：运行时新闻批次示例存放于 `data/news/`，日志在 `logs/news_analyzer.log`。  
- 配置：数据库默认读取 `PG*` 环境变量，可在 `NewsStorage` 初始化传参覆盖；LLM 与清洗日期等用户设置持久化在 QSettings。  
- 测试：目前未提供自动化测试，指南建议使用 `pytest`；快速语法检查可用 `python -m py_compile news_analyzer/**/**/*.py`。

## 可参考的报告要点
- 系统打通“采集-存储-展示-分析-对话”完整链路，抓取能力覆盖 RSS 与国际组织站点，支持自定义源。  
  - 去重：`rss_collector` 以链接和标题正则过滤重复；`OrgCollector` 内部 `_dedupe`；数据库层面再以 `link` 唯一索引兜底。  
  - 数据质量：可设置日期阈值做清洗，避免旧新闻干扰分析。  
- LLM 集成强调本地可控性（默认 Ollama），UI 内可切换模型、键值，分析线程化避免阻塞界面。  
- 可扩展性：新增源只需在 `default_sources.py`/`org_sources.py` 增加配置，或通过 UI 对话框临时添加；存储与 LLM 均通过环境变量可替换。
