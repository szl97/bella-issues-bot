from dataclasses import dataclass
from typing import Any, List, Optional

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.base import RunnableSequence
from langchain_core.tools import BaseTool, Tool
from langchain_openai import ChatOpenAI

from core.log_config import get_logger

logger = get_logger(__name__)


@dataclass
class AIConfig:
    model_name: str = "gpt-4o"
    temperature: float = 0.7
    verbose: bool = True
    max_retries: int = 3
    request_timeout: int = 180
    sys_prompt: str = "You are a helpful AI assistant."
    base_url: Optional[str] = None
    api_key: Optional[str] = None


class AIAssistant:
    """AI 助手类，负责与 AI 模型交互"""

    def __init__(self, config: AIConfig, tools: Optional[List[BaseTool]] = None):
        """
        初始化 AI 助手

        Args:
            config: AIConfig 实例，包含必要的配置信息
            tools: 可选的工具列表
        """
        self.config = config
        self.tools = tools or []
        self.llm = self._init_llm()
        self.agent = None

        # Initialize agent if tools are provided
        if self.tools:
            self.agent = self._init_agent()

    def _init_llm(self) -> ChatOpenAI:
        """Initialize the language model"""
        callbacks = [StreamingStdOutCallbackHandler()] if self.config.verbose else None
        
        return ChatOpenAI(
            base_url=self.config.base_url,
            api_key=self.config.api_key,
            model=self.config.model_name,
            temperature=self.config.temperature,
            timeout=self.config.request_timeout,
            max_retries=self.config.max_retries,
            callbacks=callbacks,
        )

    def _init_agent(self) -> AgentExecutor:
        """Initialize the agent with tools"""
        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.config.sys_prompt),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # 创建代理
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        
        # 创建代理执行器
        return AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=self.config.verbose,
            max_iterations=5,
            handle_parsing_errors=True
        )

    def _create_simple_chain(self) -> RunnableSequence:
        """创建简单的对话链，不使用工具"""
        from langchain_core.prompts import ChatPromptTemplate
        
        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.config.sys_prompt),
            ("human", "{input}")
        ])
        
        # 创建简单链
        chain = prompt | self.llm | (lambda x: x.content)
        
        return chain

    def add_tool(self, tool: BaseTool) -> None:
        """
        添加工具

        Args:
            tool: 要添加的工具
        """
        # 检查是否已经有同名工具
        for existing_tool in self.tools:
            if existing_tool.name == tool.name:
                # 替换同名工具
                self.tools.remove(existing_tool)
                break
                
        # 添加新工具
        self.tools.append(tool)
        
        # 重新初始化代理
        self.agent = self._init_agent()

    def generate_response(
        self, prompt: str, use_tools: bool = False, **kwargs: Any
    ) -> Any:
        """
        生成响应

        Args:
            prompt: 用户的提示词
            use_tools: 是否使用工具
            **kwargs: 其他参数

        Returns:
            any: 生成的响应
        """
        try:
            if use_tools and self.tools:
                # 确保代理已初始化
                if self.agent is None:
                    self.agent = self._init_agent()
                    
                # 使用代理生成响应
                response = self.agent.invoke({"input": prompt})
                return response["output"]
            else:
                # 使用简单链生成响应，始终使用流式输出
                chain = self._create_simple_chain()
                
                # 使用流式输出
                response_chunks = []
                for chunk in chain.stream({"input": prompt}):
                    response_chunks.append(chunk)
                
                # response_chunks 连接起来就是完整的响应结果
                return "".join(response_chunks)
        except Exception as e:
            logger.error(f"生成响应时出错: {str(e)}")
            raise


def create_example_tool() -> Tool:
    """Create an example tool for demonstration"""

    def calculator(expression: str) -> str:
        try:
            result = eval(expression)
            return f"计算结果: {result}"
        except Exception as e:
            logger.error(f"计算错误: {str(e)}")
            return f"计算错误: {str(e)}"

    return Tool.from_function(
        func=calculator,
        name="calculator",
        description="计算数学表达式",
    )


if __name__ == "__main__":
    # 设置环境变量
    load_dotenv()
    
    # 创建AI助手
    ai_assistant = AIAssistant(
        config=AIConfig(model_name="gpt-4o", temperature=0.7)
    )
    
    # 添加示例工具
    ai_assistant.add_tool(create_example_tool())
    
    # 测试生成响应
    response = ai_assistant.generate_response(
        "计算 3 + 5 的结果是多少?", use_tools=True
    )
    
    logger.info(f"Response: {response}")
