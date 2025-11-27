"""
LLM客户端

精简版：只支持本地 Ollama（OpenAI 兼容接口），不再支持远程 OpenAI/Anthropic 等。
"""

import os
import json
import logging
import requests
import time
import threading
from typing import Callable, Dict, List, Optional, Union, Any


class LLMClient:
    """LLM客户端类（仅本地 Ollama）"""

    def __init__(self, api_url=None, model=None):
        """初始化LLM客户端

        Args:
            api_url: Ollama 的 API URL，如果为 None 则使用默认值
            model: 模型名称，如果为 None 则使用默认值
        """
        self.logger = logging.getLogger("news_analyzer.llm.client")

        # 只使用本地 Ollama，默认走 OpenAI 兼容接口
        # 例如: ollama serve 后的 /v1/chat/completions
        self.api_url = api_url or os.environ.get(
            "LLM_API_URL",
            "http://localhost:11434/v1/chat/completions",
        )

        # 模型名称：比如 "qwen2.5:7b"、"llama3.1:8b" 等
        self.model = model or os.environ.get("LLM_MODEL", "qwen3:4b")

        # 默认参数
        self.temperature = 0.7
        self.max_tokens = 2048
        self.timeout = 150

        # 仅为了兼容其他代码，如果有地方读取 api_type，就固定为 "ollama"
        self.api_type = "ollama"

        self.logger.info(f"初始化LLM客户端（本地 Ollama），模型: {self.model}, 接口: {self.api_url}")

    # ---------------- 核心功能：新闻分析 ---------------- #

    def analyze_news(self, news_item, analysis_type="摘要"):
        """分析新闻

        Args:
            news_item: 新闻数据字典
            analysis_type: 分析类型，默认为 '摘要'

        Returns:
            str: 格式化的分析结果 HTML
        """
        if not news_item:
            raise ValueError("新闻数据不能为空")

        # 获取提示词
        prompt = self._get_prompt(analysis_type, news_item)

        try:
            headers = self._get_headers()

            # 使用 OpenAI 兼容格式调用 Ollama /v1/chat/completions
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=self.timeout,
            )

            response.raise_for_status()
            result = response.json()

            # 提取回复内容（按 OpenAI /v1/chat/completions 风格）
            content = self._extract_content_from_response(result)

            if not content:
                raise ValueError("LLM 返回的内容为空")

            return self._format_analysis_result(content, analysis_type)

        except Exception as e:
            self.logger.error(f"调用本地 Ollama 失败: {str(e)}")
            raise

    # ---------------- 聊天接口 ---------------- #

    def chat(self, messages, context: str = "", stream: bool = True, callback=None):
        """聊天功能

        Args:
            messages: 聊天历史消息列表（OpenAI 风格）
            context: 上下文文本
            stream: 是否使用“模拟流式输出”
            callback: 用于接收流式更新的回调函数

        Returns:
            str: 非流式模式下的回复内容；流式模式下返回 None
        """
        # 准备消息列表（加上 system 提示）
        processed_messages: List[Dict[str, str]] = []

        if context:
            processed_messages.append(
                {
                    "role": "system",
                    "content": f"你是一个新闻分析助手。以下是相关的新闻信息：\n\n{context}",
                }
            )
        else:
            processed_messages.append(
                {
                    "role": "system",
                    "content": "你是一个专业的新闻分析助手，可以回答各种问题。",
                }
            )

        processed_messages.extend(messages)

        if stream and callback:
            # 用一个线程模拟“打字机”式输出
            thread = threading.Thread(
                target=self._simulated_stream_response,
                args=(processed_messages, callback),
            )
            thread.daemon = True
            thread.start()
            return None
        else:
            # 直接一次性拿完整回复
            response = self._send_chat_request(processed_messages)
            if callback:
                callback(response, True)
            return response

    def _simulated_stream_response(self, messages, callback):
        """模拟流式响应：先拿完整回复，再按小块回调，营造打字效果"""
        try:
            full_response = self._send_chat_request(messages)

            collected_message = ""
            chunk_size = 5   # 每次输出的字符数
            delay = 0.05     # 每次输出间隔

            for i in range(0, len(full_response), chunk_size):
                chunk = full_response[i : i + chunk_size]
                collected_message += chunk
                callback(collected_message, False)
                time.sleep(delay)

            callback(full_response, True)

        except Exception as e:
            self.logger.error(f"流式处理失败: {str(e)}")
            error_message = f"""
            <div style="color: #d32f2f; font-weight: bold;">
                处理失败: {str(e)}
            </div>
            <div>
                请检查 Ollama 是否已启动，以及接口地址是否正确（默认 http://localhost:11434/v1/chat/completions）。
            </div>
            """
            callback(error_message, True)

    # ---------------- 与 Ollama 通信的底层封装 ---------------- #

    def _send_chat_request(self, messages):
        """发送聊天请求到本地 Ollama（OpenAI 兼容接口）

        Args:
            messages: 消息列表

        Returns:
            str: 回复内容
        """
        headers = self._get_headers()

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        response = requests.post(
            self.api_url,
            headers=headers,
            json=data,
            timeout=self.timeout,
        )

        response.raise_for_status()
        result = response.json()

        content = self._extract_content_from_response(result)

        if not content:
            raise ValueError("LLM 返回的内容为空")

        return content

    def _extract_content_from_response(self, result: Dict[str, Any]) -> str:
        """从 Ollama(OpenAI 兼容)响应中提取内容

        期望的响应格式类似：

        {
          "id": "...",
          "object": "chat.completion",
          "choices": [
            {
              "index": 0,
              "message": {"role": "assistant", "content": "..."},
              ...
            }
          ],
          ...
        }
        """
        try:
            return (
                result.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
        except Exception as e:
            self.logger.error(f"解析 LLM 响应失败: {str(e)}, 原始数据: {result}")
            return ""

    def test_connection(self) -> bool:
        """测试本地 Ollama 连接是否可用"""
        try:
            headers = self._get_headers()
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": "你好"}],
                "max_tokens": 5,
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=10,
            )

            response.raise_for_status()
            result = response.json()

            # 简单检查是否存在 choices 字段
            return "choices" in result and len(result["choices"]) > 0

        except Exception as e:
            self.logger.error(f"测试连接到 Ollama 失败: {str(e)}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头（本地 Ollama 一般不需要认证）"""
        return {
            "Content-Type": "application/json",
        }

    # ---------------- 提示词与结果格式化 ---------------- #

    def _get_prompt(self, analysis_type, news_item):
        """根据分析类型构造提示词"""
        title = news_item.get("title", "无标题")
        source = news_item.get("source_name", "未知来源")
        content = news_item.get("description", "无内容")
        pub_date = news_item.get("pub_date", "未知日期")

        if analysis_type == "摘要":
            return f"""
请对以下新闻进行简明扼要的摘要分析。

新闻标题: {title}
新闻来源: {source}
发布日期: {pub_date}

新闻内容:
{content}

请提供:
1. 一段 200 字以内的新闻摘要，包含关键信息点
2. 3-5 个要点列表，提炼新闻中最重要的信息
"""
        elif analysis_type == "深度分析":
            return f"""
请对以下新闻进行深度分析。

新闻标题: {title}
新闻来源: {source}
新闻内容:
{content}

请提供背景、影响和发展趋势分析。
"""
        elif analysis_type == "关键观点":
            return f"""
请提取以下新闻中的关键观点和立场。

新闻标题: {title}
新闻来源: {source}
新闻内容:
{content}

请分析:
1. 新闻中表达的主要观点
2. 各方立场和态度
3. 潜在的倾向性或偏见
"""
        elif analysis_type == "事实核查":
            return f"""
请对以下新闻进行事实核查分析。

新闻标题: {title}
新闻来源: {source}
新闻内容:
{content}

请分析:
1. 新闻中的主要事实声明
2. 可能需要核实的关键信息点
3. 潜在的误导或不准确之处
"""
        else:
            return f"""
请对以下新闻进行 {analysis_type}。

新闻标题: {title}
新闻来源: {source}
新闻内容:
{content}
"""

    def _format_analysis_result(self, content, analysis_type):
        """格式化分析结果为 HTML"""
        html = f"""
        <div style="font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; padding: 15px; line-height: 1.5;">
            <h2 style="color: #1976D2; border-bottom: 1px solid #E0E0E0; padding-bottom: 8px;">{analysis_type}结果</h2>
            <div style="padding: 10px 0;">
                {content.replace("\n\n", "</p><p>").replace("\n- ", "</p><li>").replace("\n", "<br>")}
            </div>
        </div>
        """
        return html