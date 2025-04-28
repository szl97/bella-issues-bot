"""
聊天处理模块，负责非代码修改类的用户交互。

该模块提供以下功能:
1. 处理用户的问题、咨询和澄清请求
2. 使用上下文信息提供有针对性的回答
3. 记录聊天互动日志
"""

from copy import copy
from dataclasses import dataclass
from typing import Optional

from core.ai import AIAssistant, AIConfig
from core.log_config import get_logger
from core.log_manager import LogManager

logger = get_logger(__name__)

@dataclass
class ChatProcessorConfig:
    """聊天处理器配置"""
    system_prompt: str = "你是一个专业的开发助手，负责回答用户关于项目的问题和提供技术支持。下面会给出用户需求相关的代码和文档，以及历史迭代信息。"


class ChatProcessor:
    """
    聊天处理器，处理非代码修改类需求
    """

    def __init__(self, 
                 ai_config: AIConfig, 
                 log_manager: LogManager,
                 config: Optional[ChatProcessorConfig] = None):
        """
        初始化聊天处理器
        
        Args:
            ai_config: AI配置信息
            log_manager: 日志管理器
            config: 聊天处理器配置
        """
        self.config = config or ChatProcessorConfig()
        self.log_manager = log_manager
        
        # 设置系统提示词
        self.ai_config = copy(ai_config)
        self.ai_config.sys_prompt = self.config.system_prompt
        self.ai_assistant = AIAssistant(config=self.ai_config)

    def process_chat(self, user_query: str) -> str:
        """
        处理用户的聊天请求
        
        Args:
            user_query: 用户的问题或请求
            
        Returns:
            str: AI助手的回答
        """
        
        # 生成回答
        response = self.ai_assistant.generate_response(user_query)
        
        # 记录日志
        self.log_manager.archive_logs(
            sys_prompt=self.config.system_prompt,
            prompt=user_query,
            response=response
        )
        
        return response
