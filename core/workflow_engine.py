import os
import shutil
import tempfile
from dataclasses import dataclass
from typing import Optional, Tuple
import uuid
from core.ai import AIConfig
from core.chat_processor import ChatProcessor, ChatProcessorConfig
from core.code_engineer import CodeEngineer, CodeEngineerConfig
from core.decision import DecisionProcess
from core.diff import Diff
from core.file_memory import FileMemory, FileMemoryConfig
from core.file_selector import FileSelector
from core.git_manager import GitManager, GitConfig, get_issues_branch_name
from core.log_manager import LogManager, LogConfig
from core.prompt_generator import PromptGenerator, PromptData
from core.version_manager import VersionManager
from log_config import get_logger

logger = get_logger(__name__)

@dataclass
class WorkflowEngineConfig:
    project_dir: str
    issue_id:int
    core_model:str = "gpt-4o"
    data_model:str = "gpt-4o"
    core_template: float = 0.7
    data_template: float = 0.7
    max_retry: int = 3,
    default_branch: str = "main"
    mode: str = "client" # ["client", "bot"] bot模式下，每次进行工作时，会hard reset到issues的最新分支上
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    github_remote_url: Optional[str] =None
    github_token: Optional[str] = None


class WorkflowEngine:
    CODE_TIMES = 0
    CHAT_TIMES = 0
    """
    工作流引擎，协调版本管理、日志管理和AI交互
    """
    def __init__(self, config: WorkflowEngineConfig):
        """
        初始化工作流引擎
        
        Args:
            config: 工作流配置
        """
        self.CODE_TIMES = 0
        self.CHAT_TIMES = 0
        # 存储原始配置
        self.original_config = config
        
        # 根据模式设置工作目录
        if config.mode == "bot":
            # 创建临时目录作为工作区
            self.temp_dir = os.path.join(
                tempfile.gettempdir(), 
                f"bella-bot-{config.issue_id}-{str(uuid.uuid4())[:8]}"
            )
            os.makedirs(self.temp_dir, exist_ok=True)
            # 更新配置以使用临时目录
            self.config = WorkflowEngineConfig(
                project_dir=self.temp_dir,
                **{k: v for k, v in vars(config).items() if k != 'project_dir'}
            )
            logger.info(f"Bot模式：创建临时工作目录 {self.temp_dir}")
        else:
            # 客户端模式直接使用指定的目录
            self.config = config
            self.temp_dir = None

        self.project_dir = os.path.abspath(self.config.project_dir)
        # 创建AI配置
        self.core_ai_config = AIConfig(
            model_name=config.core_model,
            temperature=config.core_template,
            base_url=config.base_url,
            api_key=config.api_key
        )
        
        self.data_ai_config = AIConfig(
            model_name=config.data_model,
            temperature=config.data_template,
            base_url=config.base_url,
            api_key=config.api_key
        )
        
        # 创建Git配置
        self.git_config = GitConfig(
            repo_path=self.project_dir,
            remote_url=config.github_remote_url,
            auth_token=config.github_token,
            default_branch=config.default_branch
        )
        
        # 创建日志配置
        self.log_config = LogConfig(
            project_dir=self.project_dir,
            issue_id=config.issue_id
        )
        
        # 初始化管理器
        self.log_manager = LogManager(config=self.log_config)
        self.git_manager = GitManager(config=self.git_config)
        self.version_manager = VersionManager(
            issue_id=config.issue_id,
            ai_config=self.core_ai_config,
            log_manager=self.log_manager,
            git_manager=self.git_manager
        )
        self.file_selector = FileSelector(
            self.project_dir,
            self.config.issue_id,
            ai_config=self.core_ai_config
        )
        self.file_memory = FileMemory(
            config=FileMemoryConfig(
                git_manager=self.git_manager,
                ai_config=self.core_ai_config,
                project_dir=self.project_dir
            )
        )
        
        # 初始化代码工程师
        self.code_engineer_config = CodeEngineerConfig(
            project_dir=self.project_dir,
            ai_config=self.core_ai_config
        )
        self.engineer = CodeEngineer(
            self.code_engineer_config,
            self.log_manager,
            Diff(self.data_ai_config)
        )
        
        # 初始化聊天处理器
        self.chat_processor = ChatProcessor(
            ai_config=self.core_ai_config,
            log_manager=self.log_manager,
            config=ChatProcessorConfig(system_prompt="你是一个项目助手，负责回答关于代码库的问题。下面会给出用户的问题以及相关的项目文件信息。")
        )
        
        # 初始化决策环境
        self.decision_env = DecisionProcess(
            ai_config=self.core_ai_config,
            version_manager=self.version_manager
        )
    
    def process_requirement(self, user_requirement: str) -> Optional[str]:
        """
        处理用户需求
        
        Args:
            user_requirement: 用户需求

        Returns:
            str: 处理结果的响应文本
        """
        try:
            # 初始化环境
            self._setup_environment()
            
            response = self._process_requirement_internal(user_requirement)
            
            # 如果是bot模式，在结束时清理临时目录
            if self.config.mode == "bot":
                self._cleanup_environment()
            
            return response
        except Exception as e:
            logger.error(f"处理需求时发生错误: {str(e)}")
            raise

    def _setup_environment(self) -> None:
        """
        根据模式设置工作环境
        """
        if self.config.mode == "bot":
            try:
                # 重置到issue对应的分支
                self.git_manager.reset_to_issue_branch(self.config.issue_id)
                logger.info(f"成功初始化Bot模式环境，工作目录: {self.temp_dir}")
            except Exception as e:
                logger.error(f"初始化Bot模式环境失败: {str(e)}")
                self._cleanup_environment()
                raise
        
    def _cleanup_environment(self) -> None:
        """
        清理工作环境，删除临时目录
        """
        if self.config.mode == "bot" and self.temp_dir and os.path.exists(self.temp_dir):
            try:
                # 关闭git仓库连接
                if hasattr(self, 'git_manager') and self.git_manager:
                    self.git_manager.delete_local_repository()
                
                # 删除临时目录
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                logger.info(f"已清理临时工作目录: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"清理临时目录时出错: {str(e)}")
                # 即使清理失败也不抛出异常，让主流程继续

    def _process_requirement_internal(self, user_requirement: str) -> Optional[str]:
        """
        内部处理需求的方法
        
        Args:
            user_requirement: 用户需求
            
        Returns:
            str: 处理结果
        """
        # 先通过决策环境分析需求类型
        decision_result = self.decision_env.analyze_requirement(user_requirement)
        
        logger.info(f"决策结果: 是否需要修改代码={decision_result.needs_code_modification}, "
                    f"理由={decision_result.reasoning}")
        
        if decision_result.needs_code_modification:
            # 执行代码修改流程
            response = self._run_code_generation_workflow(user_requirement)
        else:
            # 执行对话流程
            response = self._run_chat_workflow(user_requirement)
        
        # 如果是Bot模式且有GitHub配置，自动回复到issue
        if self.config.mode == "bot" and self.config.github_remote_url and response:
            try:
                self.git_manager.add_issue_comment(issue_number=self.config.issue_id, comment_text=response)
                logger.info(f"已在Issue #{self.config.issue_id}中添加回复")
            except Exception as e:
                logger.error(f"添加Issue评论时出错: {str(e)}")
                
        return response
    
    def _run_code_generation_workflow(self, user_requirement: str) -> Optional[str]:
        """
        执行代码生成流程，基于example_code_generate.py的逻辑
        
        Args:
            user_requirement: 用户需求
            
        Returns:
            str: 处理结果
        """
        logger.info("开始执行代码生成流程")

        # 确定当前版本
        requirement, history = self.version_manager.ensure_version_and_generate_context(user_requirement)

        # 初始化工作区
        branch_name = self._init_env()

        # 生成提示词
        user_prompt = self._get_user_prompt(requirement, history)

        # 根据提示词修改代码
        success, response = self.engineer.process_prompt(prompt=user_prompt)
        
        # 提交更改
        if success:
            self.git_manager.commit(f"issues#{self.config.issue_id}-generate by Bella-Issues-Bot")
            
            # 对于客户端和机器人模式，都尝试推送更改
            if self.config.github_remote_url:
                try:
                    self.git_manager.push(branch=branch_name, force=True)
                except Exception as e:
                    logger.warning(f"推送代码更改失败: {str(e)}")
            return response
        else:
            self.CODE_TIMES += 1
            if self.CODE_TIMES >= self.config.max_retry:
                logger.error("code workflow超过最大重试次数")
                return self._run_chat_workflow(user_requirement)
            else:
                return self._run_code_generation_workflow(user_requirement)
    
    def _run_chat_workflow(self, user_requirement: str) -> Optional[str]:
        """
        执行聊天流程，基于example_chat_process.py的逻辑
        
        Args:
            user_requirement: 用户需求
            
        Returns:
            str: 处理结果
        """
        logger.info("开始执行聊天回复流程")


        history = self.version_manager.get_formatted_history()
        # 初始化工作区
        branch_name = self._init_env()

        # 生成提示词
        user_prompt = self._get_user_prompt(user_requirement, history)
        
        # 处理聊天请求
        response = self.chat_processor.process_chat(user_prompt)

        if(response):
            self.git_manager.commit(f"issues#{self.config.issue_id}-generate by Bella-Issues-Bot")
            
            # 对于客户端和机器人模式，都尝试推送更改
            if self.config.github_remote_url:
                try:
                    self.git_manager.push(branch=branch_name, force=True)
                except Exception as e:
                    logger.warning(f"推送代码更改失败: {str(e)}")
            return response
        else:
            self.CHAT_TIMES += 1
            if self.CHAT_TIMES >= self.config.max_retry:
                logger.error("chat workflow超过最大重试次数")
                return None
            else:
                return self._run_chat_workflow(user_requirement)

    def _get_user_prompt(self, requirement: str, history: str) -> str:
        # 选择文件
        files = self.file_selector.select_files_for_requirement(requirement)
        descriptions = FileMemory.get_selected_file_descriptions(self.project_dir, files)

        # 准备提示词数据
        data = PromptData(
            requirement=requirement,
            project_dir=self.project_dir,
            steps=history,
            files=files,
            file_desc=descriptions
        )

        # 生成提示词
        return PromptGenerator.generatePrompt(data)

    def _init_env(self) -> str:
        # 获取当前轮次
        current_round = self.log_manager.get_current_round()

        # 获取分支名称
        branch_name = get_issues_branch_name(self.config.issue_id, current_round)

        # 如果轮次大于1，增量更新上一轮修改的文件详细信息
        if current_round > 1:
            self.file_memory.update_file_details()
        # 切换到适当的分支
        self.git_manager.switch_branch(branch_name, True)
        return branch_name
