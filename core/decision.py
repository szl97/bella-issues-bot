"""
决策环境模块，用于分析用户需求类型并确定处理流程。

该模块主要功能：
1. 分析用户输入的需求是否需要修改代码
2. 根据分析结果决定使用代码修改流程还是对话流程
3. 为AI助手提供决策工具
"""

from dataclasses import dataclass
from typing import Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from core.ai import AIAssistant, AIConfig
from core.log_config import get_logger
from core.version_manager import VersionManager

logger = get_logger(__name__)

@dataclass
class DecisionResult:
    """存储决策结果信息"""
    needs_code_modification: bool
    reasoning: str


class DecisionProcess:
    """
    决策环境类，用于确定用户需求是代码修改还是对话
    """
    
    def __init__(self, ai_config: AIConfig, version_manager: VersionManager):
        """
        初始化决策环境
        
        Args:
            ai_config: AI配置信息
            version_manager: 版本管理器实例
        """
        self.version_manager = version_manager
        self.ai_assistant = AIAssistant(
            config=ai_config, 
            tools=[self._create_requirement_analyzer_tool()]
        )

    def analyze_requirement(self, user_requirement: str) -> DecisionResult:
        """
        分析用户需求类型
        
        Args:
            user_requirement: 用户输入的需求
            
        Returns:
            DecisionResult: 决策结果
        """
        # 获取历史上下文
        history_context = self.version_manager.get_formatted_history()
        
        # 构建提示词
        prompt = f"""
# 任务
你需要分析用户的需求是否需要修改项目文件，如代码或文档，还是只需要回答问题。

# 历史上下文
{history_context}

# 当前用户需求
{user_requirement}

# 决策步骤
1. 仔细阅读用户当前的需求
2. 分析需求是否包含代码修改、文档修改、新增功能、修复bug、回滚代码等要求
3. 如果用户只是提问、咨询、请求解释或澄清，则判断为不需要修改代码
4、只要需要修改项目中的文件，则判断为需要修改代码

请使用requirement_analyzer工具返回决策结果。
"""

        # 发送给AI进行分析
        response = self.ai_assistant.generate_response(prompt, use_tools=True)
        
        # 如果没有得到有效决策，默认为需要修改代码
        if not isinstance(response, dict) or 'needs_code_modification' not in response:
            logger.warning("未获取到有效决策结果，默认为需要修改代码")
            return DecisionResult(
                needs_code_modification=True,
                reasoning="无法确定需求类型，默认为代码修改"
            )
            
        return DecisionResult(
            needs_code_modification=response['needs_code_modification'],
            reasoning=response['reasoning']
        )

    class _RequirementAnalyzerSchema(BaseModel):
        needs_code_modification: bool = Field(..., description="是否需要修改项目文件，如代码或文档")
        reasoning: Optional[str] = Field(None, description="决策理由")

    def _create_requirement_analyzer_tool(self) -> StructuredTool:
        """创建需求分析工具"""
        return StructuredTool.from_function(
            name="requirement_analyzer",
            description="分析用户需求是否需要修改项目文件，如代码或文档的工具",
            func=lambda **kwargs: kwargs,
            args_schema=self._RequirementAnalyzerSchema,
            return_direct=True
        )
