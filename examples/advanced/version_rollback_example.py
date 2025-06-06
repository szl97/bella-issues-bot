"""
高级示例：版本回退操作演示

展示如何在复杂场景下使用版本管理器进行智能回退操作
"""

import logging
import os
import tempfile
import shutil
from typing import List
from dotenv import load_dotenv

from core.ai import AIConfig
from core.diff import DiffInfo
from core.git_manager import GitManager, GitConfig
from core.log_config import setup_logging
from core.log_manager import LogManager, LogConfig
from core.version_manager import VersionManager


class VersionRollbackDemo:
    """版本回退演示类"""
    
    def __init__(self, demo_project_dir: str):
        """
        初始化演示环境
        
        Args:
            demo_project_dir: 演示项目目录
        """
        self.demo_project_dir = demo_project_dir
        self.issue_id = 100  # 演示用的issue ID
        
        # 配置AI
        self.ai_config = AIConfig(
            model_name="gpt-4o",
            temperature=0.7
        )
        
        # 配置Git
        self.git_config = GitConfig(
            repo_path=demo_project_dir,
            default_branch="main"
        )
        self.git_manager = GitManager(config=self.git_config)
        
        # 配置日志
        self.log_config = LogConfig(
            project_dir=demo_project_dir,
            issue_id=self.issue_id,
            mode="client"
        )
        self.log_manager = LogManager(config=self.log_config)
        
        # 创建版本管理器
        self.version_manager = VersionManager(
            issue_id=self.issue_id,
            ai_config=self.ai_config,
            log_manager=self.log_manager,
            git_manager=self.git_manager
        )
    
    def setup_demo_files(self):
        """设置演示文件"""
        # 创建一些示例文件
        demo_files = {
            "main.py": """def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
""",
            "utils.py": """def add_numbers(a, b):
    return a + b

def multiply_numbers(a, b):
    return a * b
""",
            "config.py": """DATABASE_URL = "sqlite:///app.db"
DEBUG = True
"""
        }
        
        for filename, content in demo_files.items():
            filepath = os.path.join(self.demo_project_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"已创建演示文件: {list(demo_files.keys())}")
    
    def simulate_round_modifications(self):
        """模拟多轮修改"""
        rounds_data = [
            {
                "requirement": "添加用户认证功能",
                "response": "已添加基础的用户认证系统，包括登录和注册功能。",
                "modified_files": [
                    DiffInfo(
                        file_name="auth.py",
                        is_create=True,
                        file_content=None,
                        new_content="""class AuthManager:
    def __init__(self):
        self.users = {}
    
    def register(self, username, password):
        if username in self.users:
            return False
        self.users[username] = password
        return True
    
    def login(self, username, password):
        return self.users.get(username) == password
"""
                    )
                ]
            },
            {
                "requirement": "优化数据库连接",
                "response": "已优化数据库连接，使用连接池提高性能。",
                "modified_files": [
                    DiffInfo(
                        file_name="config.py",
                        is_modify=True,
                        file_content="""DATABASE_URL = "sqlite:///app.db"
DEBUG = True
""",
                        new_content="""DATABASE_URL = "postgresql://user:pass@localhost/db"
DEBUG = False
CONNECTION_POOL_SIZE = 10
"""
                    )
                ]
            },
            {
                "requirement": "添加日志记录功能",
                "response": "已添加完整的日志记录系统，支持不同级别的日志输出。",
                "modified_files": [
                    DiffInfo(
                        file_name="logger.py",
                        is_create=True,
                        file_content=None,
                        new_content="""import logging

def setup_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger
"""
                    )
                ]
            }
        ]
        
        # 模拟存储每轮的日志
        for i, round_data in enumerate(rounds_data, 1):
            print(f"\n模拟第 {i} 轮修改...")
            
            # 创建文件（如果是新建的话）
            for diff_info in round_data["modified_files"]:
                file_path = os.path.join(self.demo_project_dir, diff_info.file_name)
                if diff_info.is_create:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(diff_info.new_content)
                elif diff_info.is_modify:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(diff_info.new_content)
            
            # 存储日志
            self.log_manager.archive_logs(
                sys_prompt="系统提示词",
                prompt=f"用户需求：{round_data['requirement']}",
                response=round_data["response"],
                diff_infos=round_data["modified_files"]
            )
            
            # 更新当前轮次
            self.log_manager.current_round += 1
            
            print(f"完成第 {i} 轮修改")
    
    def demonstrate_rollback_analysis(self):
        """演示回退分析"""
        print("\n" + "="*60)
        print("演示版本回退分析")
        print("="*60)
        
        # 获取当前历史
        history = self.version_manager.get_formatted_history()
        print("当前历史记录:")
        print(history)
        
        # 模拟一个需要回退的需求
        problematic_requirement = """
        上一次的数据库优化有问题，导致系统不稳定。
        请回退到添加用户认证功能的版本，然后重新实现数据库优化，
        但这次使用SQLite而不是PostgreSQL。
        """
        
        print(f"\n新需求（可能需要回退）:")
        print(problematic_requirement)
        
        # 分析是否需要回退
        try:
            requirement, context = self.version_manager.ensure_version_and_generate_context(problematic_requirement)
            print(f"\n分析结果:")
            print(f"最终需求: {requirement}")
            print(f"上下文: {context}")
        except Exception as e:
            print(f"分析过程中出错: {str(e)}")
    
    def demonstrate_manual_rollback(self):
        """演示手动回退操作"""
        print("\n" + "="*60)
        print("演示手动版本回退")
        print("="*60)
        
        # 显示回退前的文件状态
        print("回退前的文件状态:")
        for filename in ["auth.py", "config.py", "logger.py"]:
            filepath = os.path.join(self.demo_project_dir, filename)
            if os.path.exists(filepath):
                print(f"  ✓ {filename} 存在")
            else:
                print(f"  ✗ {filename} 不存在")
        
        # 执行回退到第1轮
        target_round = 1
        print(f"\n执行回退到第 {target_round} 轮...")
        success = self.version_manager._rollback_to_version(target_round)
        
        if success:
            print("回退成功！")
            
            # 显示回退后的文件状态
            print("\n回退后的文件状态:")
            for filename in ["auth.py", "config.py", "logger.py"]:
                filepath = os.path.join(self.demo_project_dir, filename)
                if os.path.exists(filepath):
                    print(f"  ✓ {filename} 存在")
                else:
                    print(f"  ✗ {filename} 不存在")
        else:
            print("回退失败！")
    
    def run_demo(self):
        """运行完整的演示"""
        print("开始版本回退演示...")
        
        # 设置演示文件
        self.setup_demo_files()
        
        # 模拟多轮修改
        self.simulate_round_modifications()
        
        # 演示回退分析
        self.demonstrate_rollback_analysis()
        
        # 演示手动回退
        self.demonstrate_manual_rollback()
        
        print("\n演示完成！")


def main():
    """主函数"""
    setup_logging(log_level=logging.INFO)
    load_dotenv()
    
    # 创建临时目录用于演示
    temp_dir = tempfile.mkdtemp(prefix="version_rollback_demo_")
    print(f"创建演示目录: {temp_dir}")
    
    try:
        # 运行演示
        demo = VersionRollbackDemo(temp_dir)
        demo.run_demo()
        
    except Exception as e:
        print(f"演示过程中出错: {str(e)}")
        logging.error(f"演示失败: {str(e)}", exc_info=True)
    
    finally:
        # 清理临时目录
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"已清理演示目录: {temp_dir}")


if __name__ == "__main__":
    main()
