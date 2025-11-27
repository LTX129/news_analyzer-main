"""
新闻数据存储

改为使用 PostgreSQL 存储新闻数据，按批次保存和读取。
"""

import logging
import os
from datetime import datetime

import psycopg2
from psycopg2.extras import Json


class NewsStorage:
    """新闻数据存储类（PostgreSQL 版）"""
    
    def __init__(
        self,
        db_name=None,
        db_user=None,
        db_password=None,
        db_host=None,
        db_port=None
    ):
        self.logger = logging.getLogger('news_analyzer.storage')
        
        # 连接配置（可通过环境变量覆盖）
        self.db_name = db_name or os.environ.get('PGDATABASE', 'database')
        self.db_user = db_user or os.environ.get('PGUSER', 'postgres')
        self.db_password = db_password or os.environ.get('PGPASSWORD', '1234')
        self.db_host = db_host or os.environ.get('PGHOST', 'localhost')
        self.db_port = db_port or os.environ.get('PGPORT', '5432')
        
        self._connect()
        self._ensure_tables()
        self.logger.info(
            f"已连接 PostgreSQL 数据库 {self.db_name}，使用批次方式存储新闻"
        )
    
    def _connect(self):
        """建立数据库连接"""
        try:
            self.conn = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port,
                connect_timeout=5
            )
            self.conn.autocommit = True
        except Exception as e:
            self.logger.error(f"连接数据库失败: {str(e)}")
            raise
    
    def _ensure_tables(self):
        """创建所需表"""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS news_batches (
                    batch_key TEXT PRIMARY KEY,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS news_items (
                    id SERIAL PRIMARY KEY,
                    batch_key TEXT REFERENCES news_batches(batch_key) ON DELETE CASCADE,
                    link TEXT,
                    data JSONB NOT NULL
                );
                """
            )
            # 迁移老表：确保存在 link 列与唯一索引
            cur.execute("ALTER TABLE news_items ADD COLUMN IF NOT EXISTS link TEXT;")
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_news_items_batch ON news_items(batch_key);"
            )
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_news_items_link ON news_items(link);"
            )
    
    def save_news(self, news_items, filename=None):
        """保存新闻数据到数据库
        
        Args:
            news_items: 新闻条目列表
            filename: 批次标识（可选，默认使用时间戳）
            
        Returns:
            str: 保存的批次键（用于后续查询）
        """
        if not news_items:
            self.logger.warning("没有新闻数据可保存")
            return None
        
        # 使用旧的文件命名模式作为批次键，便于界面复用
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"news_{timestamp}.json"
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO news_batches (batch_key)
                    VALUES (%s)
                    ON CONFLICT (batch_key) DO NOTHING;
                    """,
                    (filename,)
                )
                
                insert_rows = []
                for item in news_items:
                    link = item.get('link')
                    if not link:
                        continue
                    insert_rows.append((filename, link, Json(item)))
                
                if insert_rows:
                    cur.executemany(
                        """
                        INSERT INTO news_items (batch_key, link, data)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (link) DO NOTHING;
                        """,
                        insert_rows
                    )
            
            self.logger.info(f"保存了 {len(insert_rows)} 条新闻到批次 {filename}")
            return filename
        
        except Exception as e:
            self.logger.error(f"保存新闻数据失败: {str(e)}")
            return None
    
    def load_news(self, filename=None):
        """加载指定批次或最新批次的新闻数据"""
        try:
            batch_key = filename
            if not batch_key:
                with self.conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT batch_key
                        FROM news_batches
                        ORDER BY created_at DESC
                        LIMIT 1;
                        """
                    )
                    row = cur.fetchone()
                    if not row:
                        self.logger.warning("没有找到新闻批次")
                        return []
                    batch_key = row[0]
            
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT data
                    FROM news_items
                    WHERE batch_key = %s
                    ORDER BY id ASC;
                    """,
                    (batch_key,)
                )
                rows = cur.fetchall()
            
            news_items = [row[0] for row in rows]
            self.logger.info(f"从批次 {batch_key} 加载了 {len(news_items)} 条新闻")
            return news_items
        
        except Exception as e:
            self.logger.error(f"加载新闻数据失败: {str(e)}")
            return []
    
    def list_news_files(self):
        """列出所有批次键（兼容历史文件名显示）"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT batch_key
                    FROM news_batches
                    ORDER BY created_at ASC;
                    """
                )
                rows = cur.fetchall()
            
            return [row[0] for row in rows]
        except Exception as e:
            self.logger.error(f"列出新闻批次失败: {str(e)}")
            return []
