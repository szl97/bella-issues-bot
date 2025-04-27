import datetime
import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LogConfig:
    """日志管理配置"""

    project_dir: str
    issue_id: int
    issues_dir: str = "memory/issues"
    base_dir: str = ".eng"


@dataclass
class LogEntry:
    """存储单次代码生成日志的数据类"""
    issue_id: int
    round_num: int
    sys_prompt: str
    prompt: str
    response: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    log_path: str = ""


class LogManager:
    """管理代码生成日志的存档和检索"""

    def __init__(self, config: LogConfig):
        """
        初始化日志管理器

        Args:
            config: LogConfig实例，包含必要的配置信息
        """
        self.config = config
        self.issue_id = self.config.issue_id
        self.issues_path = os.path.join(
            self.config.project_dir, self.config.base_dir, self.config.issues_dir, "#" + str(self.issue_id)
        )

        # 初始化当前轮次
        self.current_round = self._get_next_round()

        # 确保必要的目录存在
        os.makedirs(self.issues_path, exist_ok=True)

        # 定义日志文件名常量
        self.SYS_PROMPT_FILE = "system_prompt.txt"
        self.USER_PROMPT_FILE = "user_prompt.txt"
        self.AI_RESPONSE_FILE = "ai_response.txt"
        self.TIMESTAMP_FILE = "timestamp.txt"

    def archive_logs(self, sys_prompt: str, prompt: str, response: str) -> str:
        """
        将代码生成日志存档到指定的目录

        Args:
            issue_id: GitHub issue的ID
            sys_prompt: 系统提示词
            prompt: 用户提示词
            response: AI响应

        Returns:
            str: 存档目录的路径
        """
        # 获取下一个轮次号

        round_num = self.current_round

        # 获取当前时间戳
        timestamp = datetime.datetime.now().isoformat()
        
        # 创建轮次目录
        round_dir = os.path.join(self.issues_path, f"round_{round_num}")
        os.makedirs(round_dir, exist_ok=True)
        
        # 保存系统提示词
        with open(os.path.join(round_dir, self.SYS_PROMPT_FILE), "w", encoding="utf-8") as f:
            f.write(sys_prompt)
        
        # 保存用户提示词
        with open(os.path.join(round_dir, self.USER_PROMPT_FILE), "w", encoding="utf-8") as f:
            f.write(prompt)
        
        # 保存AI响应
        with open(os.path.join(round_dir, self.AI_RESPONSE_FILE), "w", encoding="utf-8") as f:
            f.write(response)
            
        # 保存时间戳
        with open(os.path.join(round_dir, self.TIMESTAMP_FILE), "w", encoding="utf-8") as f:
            f.write(timestamp)
        
        # 记录日志
        logger.info(f"已将日志存档至: {round_dir}")
        
        # 返回存档目录的路径
        return round_dir

    def _get_next_round(self) -> int:
        """
        获取下一个轮次号

        Returns:
            int: 下一个轮次号
        """
        issue_path = self.issues_path
        if not os.path.exists(issue_path):
            return 1

        existing_rounds = [
            int(d[6:])
            for d in os.listdir(issue_path)
            if os.path.isdir(os.path.join(issue_path, d)) and (d[6:]).isdigit()
        ]

        return max(existing_rounds, default=0) + 1

    def get_current_round(self) -> int:
        return self.current_round
        
    def get_issue_log_entries(self) -> List[LogEntry]:
        """
        获取当前issue的所有轮次的日志条目

        Returns:
            List[LogEntry]: 日志条目列表，按轮次排序
        """
        
        log_entries = []

        issue_dir = self.issues_path
        # 遍历所有轮次目录
        for dir_name in os.listdir(issue_dir):
            if not dir_name.startswith("round_"):
                continue
                
            try:
                round_num = int(dir_name[6:])  # 提取轮次号
                round_dir = os.path.join(issue_dir, dir_name)
                
                # 读取系统提示词
                sys_prompt_path = os.path.join(round_dir, self.SYS_PROMPT_FILE)
                with open(sys_prompt_path, "r", encoding="utf-8") as f:
                    sys_prompt = f.read()
                
                # 读取用户提示词
                user_prompt_path = os.path.join(round_dir, self.USER_PROMPT_FILE)
                with open(user_prompt_path, "r", encoding="utf-8") as f:
                    prompt = f.read()
                
                # 读取AI响应
                ai_response_path = os.path.join(round_dir, self.AI_RESPONSE_FILE)
                with open(ai_response_path, "r", encoding="utf-8") as f:
                    response = f.read()
                    
                # 读取时间戳
                timestamp_path = os.path.join(round_dir, self.TIMESTAMP_FILE)
                timestamp = datetime.datetime.now().isoformat()  # 默认当前时间
                if os.path.exists(timestamp_path):
                    try:
                        with open(timestamp_path, "r", encoding="utf-8") as f:
                            timestamp = f.read().strip()
                    except Exception as e:
                        logger.error(f"读取时间戳失败: {str(e)}")
                
                # 创建并添加LogEntry对象
                entry = LogEntry(issue_id=self.issue_id, round_num=round_num,
                                 sys_prompt=sys_prompt, prompt=prompt, 
                                 response=response, timestamp=timestamp, log_path=round_dir)
                log_entries.append(entry)
            except Exception as e:
                logger.error(f"读取轮次 {dir_name} 的日志失败: {str(e)}")
        
        # 按轮次号排序
        return sorted(log_entries, key=lambda entry: entry.round_num)
    
    def get_issue_round_log_entry(self, round_num: int) -> Optional[LogEntry]:
        """
        获取特定轮次的日志条目

        Args:
            round_num: 轮次号

        Returns:
            Optional[LogEntry]: 指定轮次的日志条目，如果不存在则返回None
        """
        round_dir = os.path.join(self.issues_path, f"#{self.issue_id}", f"round_{round_num}")
        
        if not os.path.exists(round_dir):
            logger.warning(f"Issue #{self.issue_id} 的轮次 {round_num} 不存在")
            return None
            
        try:
            # 直接使用现有方法获取所有轮次，然后过滤出指定轮次
            all_entries = self.get_issue_log_entries()
            return next((entry for entry in all_entries if entry.round_num == round_num), None)
        except Exception as e:
            logger.error(f"获取 Issue #{self.issue_id} 轮次 {round_num} 的日志失败: {str(e)}")
            return None

if __name__ == "__main__":
    config = LogConfig("..", 1)
    log_manager = LogManager(config)
