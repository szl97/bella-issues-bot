import os

from dotenv import load_dotenv

from core.git_manager import GitManager, GitConfig
import tempfile
import time


def test_create_branch_then_commit_then_push():
    config = GitConfig(
        repo_path="../."
    )
    git_manager = GitManager(config)
    git_manager.switch_branch(branch_name="test-branches", create=True)
    git_manager.commit("test commit")
    git_manager.push()

def test_clone_and_pull():
    load_dotenv()
    os.makedirs("../../test-clone", exist_ok=True)
    config = GitConfig(
        default_branch="test-branches",
        repo_path="../../test-clone",
        remote_url="https://github.com/szl97/bella-issues-bot.git",
        auth_token=os.getenv("GITHUB_TOKEN")
    )
    git_manager = GitManager(config)
    git_manager.pull()
    git_manager.switch_branch(branch_name="test-branches", create=True)
    git_manager.commit("test commit")
    git_manager.push(force=True)



def test_real_github_operations():
    load_dotenv()
    """
    真实测试与 GitHub 仓库的交互
    
    注意：此测试需要互联网连接和有效的 GitHub 访问令牌
    跳过此测试：pytest -k "not test_real_github_operations"
    """

    github_token = os.getenv("GITHUB_TOKEN")

    repo_url = os.getenv("GIT_REMOTE")
    
    # 创建临时目录用于克隆
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建配置
        config = GitConfig(
            repo_path=temp_dir,
            remote_url=repo_url,
            auth_token=github_token
        )
        
        # 初始化 GitManager 并克隆仓库
        git_manager = GitManager(config)
        
        # 验证克隆成功
        assert os.path.exists(os.path.join(temp_dir, ".git"))
        assert git_manager.repo is not None
        
        # 获取当前分支名称
        original_branch = git_manager.get_current_branch()
        print(f"当前分支: {original_branch}")
        
        # 创建并切换到新分支
        branch_name = f"test-branch-{int(time.time())}"
        git_manager.create_branch(branch_name)
        git_manager.switch_branch(branch_name)
        
        # 验证分支切换成功
        assert git_manager.get_current_branch() == branch_name
        
        # 创建一个新文件
        test_file = os.path.join(temp_dir, f"test_file_{int(time.time())}.txt")
        with open(test_file, "w") as f:
            f.write(f"Test content created at {time.time()}")
        
        # 添加并提交文件
        git_manager.repo.git.add(test_file)
        git_manager.repo.git.commit("-m", f"Test commit on branch {branch_name}")
        
        # 推送到远程仓库
        try:
            git_manager.push(branch_name)
            push_successful = True
        except Exception as e:
            print(f"推送失败，但这可能是预期的: {str(e)}")
            push_successful = False
        
        # 验证推送尝试
        assert push_successful, "推送操作应该成功"
        
        # 清理：删除本地仓库
        git_manager.delete_local_repository(remove_git_config=True)


def test_add_issue_comment():
    load_dotenv()
    """
    测试在 GitHub Issues 下添加评论的功能
    
    注意：此测试需要互联网连接、有效的 GitHub 访问令牌，以及仓库中存在的 Issue
    跳过此测试：pytest -k "not test_add_issue_comment"
    """
    github_token = os.getenv("GITHUB_TOKEN")

    repo_url = os.getenv("GIT_REMOTE")
    issue_number = 1  # 确保仓库中存在此 Issue 编号
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建配置
        config = GitConfig(
            repo_path=temp_dir,
            remote_url=repo_url,
            auth_token=github_token
        )
        
        # 初始化 GitManager
        git_manager = GitManager(config)
        
        # 生成唯一的评论内容
        comment_text = f"自动化测试评论 - {time.strftime('%Y-%m-%d %H:%M:%S')} - {time.time()}"
        
        # 添加评论
        try:
            result = git_manager.add_issue_comment(issue_number, comment_text)
            assert result is True, "添加评论应该返回 True"
            print(f"成功添加评论: {comment_text}")
        except Exception as e:
            assert False, f"添加评论时出错: {str(e)}"
        
        # 清理：删除本地仓库
        git_manager.delete_local_repository(remove_git_config=True)
