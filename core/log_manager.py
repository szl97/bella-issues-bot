import datetime
import os
import json
import shutil
from dataclasses import dataclass, field
from typing import List, Optional
from pydantic import BaseModel

from core.diff import DiffInfo
from core.log_config import get_logger

logger = get_logger(__name__)

@dataclass
class LogConfig:
    """日志管理配置"""

    project_dir: str
    issue_id: int
    mode: str = "client" # ["client", "bot"]


class LogEntry(BaseModel):
    """存储单次代码生成日志的数据类"""
    issue_id: int
    round_num: int
    sys_prompt: str
    prompt: str
    response: str
    timestamp: str = datetime.datetime.now().isoformat()
    log_path: str = ""
    modified_files: List[DiffInfo] = []


class LogManager:
    """管理代码生成日志的存档和检索"""
    base_dir: str = ".eng"
    logs_base_dir: str = "memory"
    rollback_dir: str = "rollback"

    def __init__(self, config: LogConfig):
        """
        初始化日志管理器

        Args:
            config: LogConfig实例，包含必要的配置信息
        """
        self.config = config
        self.issue_id = self.config.issue_id

        
        # 根据模式选择存储目录
        if self.config.mode == "bot":
            logs_dir = "issues"
        else:
            logs_dir = "queries"
            
        # 构建完整的日志存储路径
        self.logs_path = os.path.join(
            self.config.project_dir, 
            self.base_dir,
            self.logs_base_dir,
            logs_dir)
        self.issues_path = os.path.join(
            self.logs_path, "#" + str(self.issue_id)
        )

        self.rollback_path = os.path.join(
            self.logs_path, "#" + str(self.issue_id), self.rollback_dir
        )

        # 初始化当前轮次
        self.current_round = self._get_next_round()

        # 确保必要的目录存在
        os.makedirs(self.issues_path, exist_ok=True)
        os.makedirs(self.rollback_path, exist_ok=True)

        # 定义日志文件名常量
        self.SYS_PROMPT_FILE = "system_prompt.txt"
        self.USER_PROMPT_FILE = "user_prompt.txt"
        self.AI_RESPONSE_FILE = "ai_response.txt"
        self.TIMESTAMP_FILE = "timestamp.txt"
        self.MODIFIED_FILES_FILE = "modified_files.txt"

    def archive_logs(self, sys_prompt: str, prompt: str, response: str, diff_infos: List[DiffInfo] = None) -> str:
        """
        将代码生成日志存档到指定的目录

        Args:
            diff_infos: 文件的修改信息
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

        # 保存修改的文件列表
        if diff_infos:
            # 使用 Pydantic 的 dict 方法进行序列化
            diff_dicts = [diff.dict() for diff in diff_infos]
                
            # 序列化为 JSON 并保存
            with open(os.path.join(round_dir, self.MODIFIED_FILES_FILE), "w", encoding="utf-8") as f:
                json.dump(diff_dicts, f, ensure_ascii=False, indent=2)
            logger.info(f"保存了 {len(diff_infos)} 个修改的文件记录")
        
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
        
    def get_issue_log_entries(self, include_diff: bool = False) -> List[LogEntry]:
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
                    
                # 读取修改的文件列表(如果存在)
                modified_files = []
                if include_diff:
                    modified_files_path = os.path.join(round_dir, self.MODIFIED_FILES_FILE)
                    if os.path.exists(modified_files_path):
                        try:
                            with open(modified_files_path, "r", encoding="utf-8") as f:
                                diff_dicts = json.load(f)
                                
                                # 将字典转换回 DiffInfo 对象
                                modified_files = [DiffInfo(**diff_dict) for diff_dict in diff_dicts]
                        except Exception as e:
                            logger.error(f"读取修改文件列表失败: {str(e)}")
                    
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
                                 response=response, timestamp=timestamp, log_path=round_dir,
                                 modified_files=modified_files)
                log_entries.append(entry)
            except Exception as e:
                logger.error(f"读取轮次 {dir_name} 的日志失败: {str(e)}")
        
        # 按轮次号排序
        return sorted(log_entries, key=lambda entry: entry.round_num)
    
    def get_issue_round_log_entry(self, round_num: int, include_diff: bool = False) -> Optional[LogEntry]:
        """
        获取特定轮次的日志条目

        Args:
            round_num: 轮次号
            include_diff: 是否包含修改信息

        Returns:
            Optional[LogEntry]: 指定轮次的日志条目，如果不存在则返回None
        """
        round_dir = os.path.join(self.issues_path, f"round_{round_num}")
        
        if not os.path.exists(round_dir):
            logger.warning(f"Issue #{self.issue_id} 的轮次 {round_num} 不存在")
            return None
            
        try:
            # 直接使用现有方法获取所有轮次，然后过滤出指定轮次
            all_entries = self.get_issue_log_entries(include_diff)
            return next((entry for entry in all_entries if entry.round_num == round_num), None)
        except Exception as e:
            logger.error(f"获取 Issue #{self.issue_id} 轮次 {round_num} 的日志失败: {str(e)}")
            return None
            
    def rollback_logs(self, target_round: int) -> bool:
        """
        将目标轮次之后的日志移至回滚目录
        
        Args:
            target_round: 保留到的轮次，之后的轮次会被移到回滚目录
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 确保回滚目录存在
            os.makedirs(self.rollback_path, exist_ok=True)
            
            # 获取所有轮次目录
            round_dirs = [d for d in os.listdir(self.issues_path) 
                         if os.path.isdir(os.path.join(self.issues_path, d)) 
                         and d.startswith("round_")]
            
            # 筛选出需要回滚的轮次目录
            rounds_to_rollback = []
            for dir_name in round_dirs:
                try:
                    round_num = int(dir_name[6:])  # 提取轮次号
                    if round_num > target_round:
                        rounds_to_rollback.append((round_num, dir_name))
                except ValueError:
                    continue
            
            # 按轮次号排序
            rounds_to_rollback.sort(key=lambda x: x[0])
            
            if not rounds_to_rollback:
                logger.info(f"没有轮次需要回滚")
                return True
                
            # 移动轮次日志到回滚目录
            for round_num, dir_name in rounds_to_rollback:
                source_path = os.path.join(self.issues_path, dir_name)
                dest_path = os.path.join(self.rollback_path, dir_name)
                
                # 如果目标路径已存在，先删除
                if os.path.exists(dest_path):
                    shutil.rmtree(dest_path)
                    
                # 移动目录
                shutil.move(source_path, dest_path)
                logger.info(f"已将轮次 {round_num} 的日志移至回滚目录: {dest_path}")
            
            # 更新当前轮次
            self.current_round = self._get_next_round()
            return True
            
        except Exception as e:
            logger.error(f"回滚日志失败: {str(e)}")
            return False
    
    def get_rollback_log_entries(self, include_diff: bool = False) -> List[LogEntry]:
        """
        获取已回滚的所有轮次的日志条目

        Args:
            include_diff: 是否包含diff信息

        Returns:
            List[LogEntry]: 回滚的日志条目列表，按轮次排序
        """
        try:
            # 如果回滚目录不存在，返回空列表
            if not os.path.exists(self.rollback_path):
                return []
                
            # 临时保存当前issues_path
            original_path = self.issues_path
            
            # 将issues_path指向rollback_path，复用get_issue_log_entries方法
            self.issues_path = self.rollback_path
            
            # 获取回滚目录中的日志条目
            rollback_entries = self.get_issue_log_entries(include_diff)
            
            # 恢复issues_path
            self.issues_path = original_path
            
            return rollback_entries
        except Exception as e:
            logger.error(f"获取回滚日志条目失败: {str(e)}")
            return []

if __name__ == "__main__":
    config = LogConfig("..", 1)
    log_manager = LogManager(config)
