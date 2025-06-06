"""
高级示例：版本管理与工作流引擎集成

展示版本管理器如何与WorkflowEngine协同工作，
实现智能的需求处理和版本控制
"""

import logging
import os
import tempfile
import shutil
from dotenv import load_dotenv

from core.workflow_engine import WorkflowEngine, WorkflowEngineConfig
from core.log_config import setup_logging


class VersionIntegrationDemo:
    """版本管理集成演示类"""
    
    def __init__(self, demo_project_dir: str):
        """
        初始化演示环境
        
        Args:
            demo_project_dir: 演示项目目录
        """
        self.demo_project_dir = demo_project_dir
        self.issue_id = 200  # 演示用的issue ID
        
        # 创建工作流引擎配置
        self.config = WorkflowEngineConfig(
            project_dir=demo_project_dir,
            issue_id=self.issue_id,
            core_model="gpt-4o",
            data_model="gpt-4o",
            core_template=0.7,
            data_template=0.7,
            mode="client"
        )
        
        # 创建工作流引擎
        self.workflow_engine = WorkflowEngine(self.config)
    
    def setup_initial_project(self):
        """设置初始项目文件"""
        initial_files = {
            "app.py": """from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World!"

if __name__ == "__main__":
    app.run(debug=True)
""",
            "requirements.txt": """Flask==2.3.3
""",
            "README.md": """# Demo Project

A simple Flask application for demonstration.
"""
        }
        
        for filename, content in initial_files.items():
            filepath = os.path.join(self.demo_project_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"已创建初始项目文件: {list(initial_files.keys())}")
    
    def demonstrate_incremental_development(self):
        """演示增量开发过程"""
        print("\n" + "="*70)
        print("演示增量开发过程")
        print("="*70)
        
        # 定义一系列渐进式需求
        requirements = [
            {
                "description": "第一轮：添加用户模型",
                "requirement": """
                为应用添加用户模型，包括：
                1. User类，包含id、username、email字段
                2. 基础的用户管理功能
                3. 更新requirements.txt添加必要的依赖
                """
            },
            {
                "description": "第二轮：添加用户注册功能", 
                "requirement": """
                基于已有的用户模型，添加用户注册功能：
                1. 创建注册表单
                2. 添加注册路由
                3. 实现用户注册逻辑
                """
            },
            {
                "description": "第三轮：添加用户登录功能",
                "requirement": """
                继续完善用户系统，添加登录功能：
                1. 创建登录表单
                2. 添加登录路由
                3. 实现用户认证逻辑
                4. 添加会话管理
                """
            }
        ]
        
        # 逐步处理每个需求
        for i, req_data in enumerate(requirements, 1):
            print(f"\n{'='*50}")
            print(f"{req_data['description']}")
            print(f"{'='*50}")
            
            try:
                # 使用工作流引擎处理需求
                response = self.workflow_engine.process_requirement(req_data['requirement'])
                
                if response:
                    print(f"✓ 第{i}轮处理完成")
                    print(f"响应摘要: {response[:200]}..." if len(response) > 200 else response)
                else:
                    print(f"✗ 第{i}轮处理失败")
                    
            except Exception as e:
                print(f"✗ 第{i}轮处理出错: {str(e)}")
    
    def demonstrate_rollback_scenario(self):
        """演示回退场景"""
        print("\n" + "="*70)
        print("演示版本回退场景")
        print("="*70)
        
        # 模拟一个需要回退的需求
        rollback_requirement = """
        我发现之前的登录功能有安全问题，需要重新实现。
        请回退到添加用户注册功能的版本，然后重新实现更安全的登录系统：
        1. 使用密码哈希
        2. 添加登录失败次数限制
        3. 实现更安全的会话管理
        """
        
        print("提交回退需求...")
        print(f"需求内容: {rollback_requirement}")
        
        try:
            response = self.workflow_engine.process_requirement(rollback_requirement)
            
            if response:
                print("✓ 回退需求处理完成")
                print(f"响应: {response}")
            else:
                print("✗ 回退需求处理失败")
                
        except Exception as e:
            print(f"✗ 回退需求处理出错: {str(e)}")
    
    def run_demo(self):
        """运行完整的集成演示"""
        print("开始版本管理与工作流引擎集成演示...")
        
        # 设置初始项目
        self.setup_initial_project()
        
        # 演示增量开发
        self.demonstrate_incremental_development()
        
        # 演示回退场景
        self.demonstrate_rollback_scenario()
        
        print("\n集成演示完成！")

def main():
    """主函数"""
    setup_logging(log_level=logging.INFO)
    load_dotenv()
    
    # 创建临时目录用于演示
    temp_dir = tempfile.mkdtemp(prefix="version_integration_demo_")
    print(f"创建演示目录: {temp_dir}")
    
    try:
        # 运行演示
        demo = VersionIntegrationDemo(temp_dir)
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
