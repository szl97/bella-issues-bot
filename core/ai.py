import logging
from dataclasses import dataclass
from typing import Any, List, Optional

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.tools import Tool
from langchain_core.language_models import BaseLanguageModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


@dataclass
class AIConfig:
    """Configuration for AI model and tools"""

    sys_prompt: str = None
    base_url: str = None
    api_key: str = None
    model_name: str = "gpt-4o"
    temperature: float = 0.7
    verbose: bool = True
    max_retries: int = 3
    request_timeout: int = 60


class AIAssistant:
    """AI Assistant that can use tools and engage in conversations"""

    def __init__(
        self, config: Optional[AIConfig] = None, tools: Optional[List[Tool]] = None
    ):
        self.config = config or AIConfig()
        self.tools = tools or []

        # Initialize the language model
        self.llm = self._init_llm()

        # Initialize tools and agent if tools are provided
        if self.tools:
            self.agent = self._init_agent()

    def _init_llm(self) -> BaseLanguageModel:
        """Initialize the language model with configuration"""
        callbacks = [StreamingStdOutCallbackHandler()]

        return ChatOpenAI(
            base_url=self.config.base_url,
            api_key=self.config.api_key,
            model_name=self.config.model_name,
            temperature=self.config.temperature,
            streaming=True,
            verbose=self.config.verbose,
            max_retries=self.config.max_retries,
            request_timeout=self.config.request_timeout,
            callbacks=callbacks,
        )

    def _init_agent(self) -> AgentExecutor:
        """Initialize the agent with tools"""
        system_message = """You are a helpful AI assistant that can use tools to accomplish tasks. 
        Always think step by step about what tools you need to use and why.
        If you're not sure about something, ask for clarification.
        """

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    system_message
                    if self.config.sys_prompt is None
                    else self.config.sys_prompt,
                ),
                ("user", "{input}"),
                ("user", "{agent_scratchpad}"),
            ]
        )

        agent = create_openai_tools_agent(llm=self.llm, tools=self.tools, prompt=prompt)

        return AgentExecutor(
            agent=agent, tools=self.tools, verbose=self.config.verbose, max_iterations=5
        )

    def generate_response(
        self, prompt: str, use_tools: bool = False, **kwargs: Any
    ) -> str:
        try:
            if use_tools and self.tools:
                response = self.agent.invoke({"input": prompt})
                return response["output"]
            else:
                chain = self._create_simple_chain()
                response = chain.invoke({"input": prompt})
                return response
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise

    def _create_simple_chain(self) -> RunnableSequence:
        """Create a simple chain for direct LLM interactions"""
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant. Provide clear and concise responses.",
                ),
                ("user", "{input}"),
            ]
        )

        return prompt | self.llm | StrOutputParser()

    def add_tool(self, tool: Tool) -> None:
        """Add a new tool to the assistant"""
        self.tools.append(tool)
        if len(self.tools) == 1:
            self.agent = self._init_agent()
        else:
            self.agent = self._init_agent()


def create_example_tool() -> Tool:
    """Create an example tool for demonstration"""

    def calculator(expression: str) -> str:
        try:
            return str(eval(expression))
        except Exception as e:
            return f"Error calculating: {str(e)}"

    return Tool(
        name="calculator",
        description="Useful for performing mathematical calculations. Input should be a mathematical expression.",
        func=calculator,
    )


if __name__ == "__main__":
    # Initialize the assistant with a tool
    assistant = AIAssistant(
        config=AIConfig(
            base_url="https://test-bella-openapi.ke.com/v1",
            api_key="",
            temperature=0.7,
        ),
        tools=[create_example_tool()],
    )

    response = assistant.generate_response("What is 15 * 7?", use_tools=True)
    print(f"Response: {response}")
