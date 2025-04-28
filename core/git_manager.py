import os
import shutil
from dataclasses import dataclass
from typing import Optional, List
from urllib.parse import urlparse, urlunparse

import git

from core.log_config import get_logger

logger = get_logger(__name__)


@dataclass
class GitConfig:
    """Git configuration parameters"""

    repo_path: str
    remote_name: str = "origin"
    default_branch: str = "main"
    remote_url: Optional[str] = os.getenv("GIT_REMOTE")
    auth_token: Optional[str] = os.getenv("GITHUB_TOKEN")


class GitManager:
    """Manages git operations including push, pull, branch creation and switching"""

    def __init__(self, config: GitConfig):
        """Initialize GitManager with configuration"""
        self.config = config
        self.repo = None
        self._ensure_repo()

    def _ensure_repo(self) -> None:
        """Ensure git repository exists and is properly initialized"""
        if not os.path.exists(self.config.repo_path) or len(os.listdir(self.config.repo_path)) == 0:
            if self.config.remote_url:
                self.clone()
            else:
                raise ValueError(
                    f"Repository path does not exist: {self.config.repo_path}"
                )
        else:
            try:
                self.repo = git.Repo(self.config.repo_path)
                # Set auth token for remote operations if provided
                if self.config.auth_token and self.config.remote_url:
                    self._set_remote_with_auth()
            except git.InvalidGitRepositoryError:
                raise ValueError(
                    f"Invalid git repository at: {self.config.repo_path}"
                )



    def _get_url_with_token(self, url: str) -> str:
        """
        Insert authentication token into git URL

        Args:
            url: Original git URL

        Returns:
            URL with authentication token
        """
        if not self.config.auth_token:
            return url

        parsed = urlparse(url)

        # Handle different URL formats
        if parsed.scheme in ["http", "https"]:
            netloc = f"{self.config.auth_token}@{parsed.netloc}"
            return urlunparse(
                (
                    parsed.scheme,
                    netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment,
                )
            )
        elif "@" in url and ":" in url and url.startswith("git@"):  # Handle SSH format: git@github.com:username/repo.git
            return url  # Don't modify SSH URLs
        else:
            return url  # Return original if format is not recognized

    def _set_remote_with_auth(self) -> None:
        """Configure remote with authentication token"""
        if not self.repo or not self.config.auth_token or not self.config.remote_url:
            return

        try:
            # Get current remotes
            remotes = list(self.repo.remotes)
            remote_exists = any(
                remote.name == self.config.remote_name for remote in remotes
            )

            # Prepare URL with token
            url_with_token = self._get_url_with_token(self.config.remote_url)

            # Set or update remote
            if remote_exists:
                self.repo.git.remote("set-url", self.config.remote_name, url_with_token)
            else:
                self.repo.git.remote("add", self.config.remote_name, url_with_token)

            logger.info(
                f"Configured remote '{self.config.remote_name}' with authentication"
            )
        except git.GitCommandError as e:
            logger.error(f"Failed to configure remote with authentication: {str(e)}")
            raise

    def clone(self) -> None:
        """
        Clone the repository specified in config

        Raises:
            ValueError: If remote_url is not set in config
            git.GitCommandError: If clone operation fails
        """
        if not self.config.remote_url:
            raise ValueError("Remote URL must be set to clone a repository")

        self._clone_repo(branch=self.config.default_branch)

    def _clone_repo(self, branch: Optional[str] = None) -> None:
        """
        Internal method to perform the clone operation

        Args:
            branch: Branch to checkout after cloning
        """
        try:
            # Prepare parent directory if it doesn't exist
            parent_dir = os.path.dirname(self.config.repo_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir)

            # Remove target directory if it exists
            if os.path.exists(self.config.repo_path):
                shutil.rmtree(self.config.repo_path)

            # Prepare URL with token if provided
            clone_url = self._get_url_with_token(self.config.remote_url)

            # Clone options
            clone_args = {
                "url": clone_url,
                "to_path": self.config.repo_path,
            }

            # Add branch if specified
            if branch:
                clone_args["branch"] = branch

            # Clone the repository
            self.repo = git.Repo.clone_from(**clone_args)

            logger.info(f"Successfully cloned repository to {self.config.repo_path}")

            # Configure remote with auth token if provided
            if self.config.auth_token:
                self._set_remote_with_auth()

        except git.GitCommandError as e:
            logger.error(f"Failed to clone repository: {str(e)}")
            # Clean up if clone failed
            if os.path.exists(self.config.repo_path):
                shutil.rmtree(self.config.repo_path)
            raise

    def pull(self, branch: Optional[str] = None) -> None:
        """
        Pull changes from remote repository

        Args:
            branch: Branch to pull from. If None, pulls current branch
        """
        try:
            if branch:
                self.repo.git.pull(self.config.remote_name, branch)
            else:
                self.repo.git.pull()
            logger.info(
                f"Successfully pulled changes from {branch or 'current branch'}"
            )
        except git.GitCommandError as e:
            logger.error(f"Failed to pull changes: {str(e)}")
            raise

    def push(
        self,
        branch: Optional[str] = None,
        force: bool = False,
        set_upstream: bool = True,
    ) -> None:
        """
        Push changes to remote repository

        Args:
            branch: Branch to push. If None, pushes current branch
            force: Whether to force push
            set_upstream: Whether to set upstream branch if it doesn't exist
        """
        try:
            # 确保远程 URL 包含认证令牌
            if self.config.auth_token:
                self._set_remote_with_auth()

            # 如果没有指定分支，获取当前分支
            current_branch = branch or self.get_current_branch()

            # 执行推送操作
            if force:
                if set_upstream:
                    self.repo.git.push(
                        "-f", "--set-upstream", self.config.remote_name, current_branch
                    )
                else:
                    if branch:
                        self.repo.git.push("-f", self.config.remote_name, branch)
                    else:
                        self.repo.git.push("-f")
            else:
                if set_upstream:
                    self.repo.git.push(
                        "--set-upstream", self.config.remote_name, current_branch
                    )
                else:
                    if branch:
                        self.repo.git.push(self.config.remote_name, branch)
                    else:
                        self.repo.git.push()

            logger.info(f"Successfully pushed changes to {current_branch}")
        except git.GitCommandError as e:
            logger.error(f"Failed to push changes: {str(e)}")
            raise

    def create_branch(
        self, branch_name: str, start_point: Optional[str] = None
    ) -> None:
        """
        Create a new branch

        Args:
            branch_name: Name of the new branch
            start_point: Branch/commit to create branch from. If None, uses current HEAD
        """
        try:
            if start_point:
                self.repo.git.branch(branch_name, start_point)
            else:
                self.repo.git.branch(branch_name)
            logger.info(f"Successfully created branch: {branch_name}")
        except git.GitCommandError as e:
            logger.error(f"Failed to create branch: {str(e)}")
            raise

    def switch_branch(self, branch_name: str, create: bool = False) -> None:
        """
        Switch to specified branch

        Args:
            branch_name: Name of the branch to switch to
            create: Create branch if it doesn't exist
        """
        try:
            if create:
                try:
                    self.repo.git.checkout("-b", branch_name)
                except:
                    self.repo.git.checkout(branch_name)
            else:
                self.repo.git.checkout(branch_name)
            logger.info(f"Successfully switched to branch: {branch_name}")
        except git.GitCommandError as e:
            logger.error(f"Failed to switch branch: {str(e)}")
            raise

    def delete_branch(self, branch_name: str, force: bool = False) -> None:
        """
        Delete specified branch

        Args:
            branch_name: Name of the branch to delete
            force: Force delete even if branch not fully merged
        """
        try:
            if force:
                self.repo.git.branch("-D", branch_name)
            else:
                self.repo.git.branch("-d", branch_name)
            logger.info(f"Successfully deleted branch: {branch_name}")
        except git.GitCommandError as e:
            logger.error(f"Failed to delete branch: {str(e)}")
            raise

    def get_current_branch(self) -> str:
        """Get name of current branch"""
        return self.repo.active_branch.name

    def list_branches(self, remote: bool = False) -> List[str]:
        """
        List all branches

        Args:
            remote: Whether to list remote branches instead of local

        Returns:
            List of branch names
        """
        if remote:
            return [ref.name for ref in self.repo.remote().refs]
        return [branch.name for branch in self.repo.heads]

    def get_current_commit_id(self) -> str:
        """获取当前提交的 ID"""
        try:
            return self.repo.head.commit.hexsha
        except Exception as e:
            logger.error(f"获取当前提交 ID 失败: {str(e)}")
            return ""

    def get_changed_files(self, old_commit: str, new_commit: str) -> List[str]:
        """
        获取两个提交之间变更的文件列表

        Args:
            old_commit: 旧提交的 ID
            new_commit: 新提交的 ID

        Returns:
            变更的文件路径列表
        """
        try:
            # 获取提交对象
            old = self.repo.commit(old_commit)
            new = self.repo.commit(new_commit)

            # 获取差异
            diff_index = old.diff(new)

            # 收集所有变更的文件
            changed_files = set()

            # 添加修改的文件
            for diff in diff_index.iter_change_type("M"):
                if not self.is_ignore(diff.a_path):
                    changed_files.add(diff.a_path)

            # 添加增加的文件
            for diff in diff_index.iter_change_type("A"):
                if not self.is_ignore(diff.b_path):
                    changed_files.add(diff.b_path)

            # 添加删除的文件
            for diff in diff_index.iter_change_type("D"):
                if not self.is_ignore(diff.b_path):
                    changed_files.add(diff.a_path)

            return list(changed_files)
        except Exception as e:
            logger.error(f"获取变更文件列表失败: {str(e)}")
            return []

    def is_ignore(self, path: str) -> bool:
        # 检查文件名是否以点开头
        file_name = os.path.basename(path)
        if file_name.startswith("."):
            return True
        # 检查路径中是否包含以点开头的目录
        path_parts = path.split(os.path.sep)
        for part in path_parts:
            # 跳过空字符串（可能出现在路径开头）
            if not part:
                continue
            # 如果目录名以点开头，则忽略
            if part.startswith("."):
                return True

        # 如果不满足任何忽略条件，则不忽略
        return False

    def delete_local_repository(self, remove_git_config: bool = False) -> None:
        """
        删除本地代码仓库和可选的全局 git 配置

        Args:
            remove_git_config: 是否同时删除与此仓库相关的全局 git 配置

        Raises:
            ValueError: 如果仓库路径不存在
            OSError: 如果删除操作失败
        """
        if not os.path.exists(self.config.repo_path):
            logger.warning(f"仓库路径不存在，无需删除: {self.config.repo_path}")
            return

        try:
            # 关闭仓库连接以释放文件锁
            if self.repo:
                self.repo.close()
                self.repo = None

            # 删除本地仓库目录
            shutil.rmtree(self.config.repo_path)
            logger.info(f"成功删除本地仓库: {self.config.repo_path}")

            # 可选：删除全局 git 配置中与此仓库相关的条目
            if remove_git_config:
                self._remove_git_config()

        except (OSError, shutil.Error) as e:
            logger.error(f"删除本地仓库失败: {str(e)}")
            raise

    def _remove_git_config(self) -> None:
        """
        从全局 git 配置中删除与当前仓库相关的配置

        这包括：
        - 与远程仓库 URL 相关的凭证
        - 特定于此仓库的用户配置
        """
        try:
            # 获取仓库的规范路径
            repo_path = os.path.abspath(self.config.repo_path)
            repo_name = os.path.basename(repo_path)

            # 尝试从 git 配置中删除与此仓库相关的条目
            if self.config.remote_url:
                # 解析远程 URL 以获取主机名
                parsed = urlparse(self.config.remote_url)
                if parsed.netloc:
                    # 尝试删除凭证
                    try:
                        git.cmd.Git().execute(
                            ["git", "credential", "reject"],
                            input=f"url={self.config.remote_url}\n\n",
                        )
                        logger.info(f"已尝试从凭证存储中删除 {parsed.netloc} 的凭证")
                    except git.GitCommandError:
                        logger.debug("凭证删除操作未成功，可能没有存储凭证")

            # 尝试删除仓库特定的配置（如果有）
            try:
                git.cmd.Git().execute(
                    [
                        "git",
                        "config",
                        "--global",
                        "--remove-section",
                        f"remote.{repo_name}",
                    ]
                )
                logger.info(f"已删除全局 git 配置中的 remote.{repo_name} 部分")
            except git.GitCommandError:
                logger.debug(f"全局配置中没有 remote.{repo_name} 部分")

            logger.info("已完成 git 配置清理")

        except Exception as e:
            logger.warning(f"清理 git 配置时出错: {str(e)}")
            # 不抛出异常，因为这是次要操作

    def add_issue_comment(self, issue_number: int, comment_text: str) -> bool:
        """
        在 GitHub 仓库的指定 Issue 下添加评论

        Args:
            issue_number: Issue 编号
            comment_text: 评论内容

        Returns:
            bool: 操作是否成功

        Raises:
            ValueError: 如果未配置认证令牌或远程 URL
            Exception: 如果添加评论过程中发生其他错误
        """
        try:
            # 检查必要的配置
            if not self.config.auth_token:
                raise ValueError("添加 Issue 评论需要认证令牌 (auth_token)")

            if not self.config.remote_url:
                raise ValueError("添加 Issue 评论需要远程仓库 URL (remote_url)")

            # 导入 PyGithub
            try:
                from github import Github
            except ImportError:
                raise ImportError("添加 Issue 评论需要安装 PyGithub 库: pip install PyGithub")

            # 解析仓库所有者和名称
            parsed_url = urlparse(self.config.remote_url)
            path_parts = parsed_url.path.strip("/").split("/")

            if len(path_parts) < 2 or not all(path_parts[:2]):
                raise ValueError(f"无法从 URL 解析仓库所有者和名称: {self.config.remote_url}")

            owner = path_parts[0]
            repo_name = path_parts[1]
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]  # 移除 .git 后缀

            # 初始化 GitHub 客户端
            g = Github(self.config.auth_token)

            # 获取仓库和 Issue
            repo = g.get_repo(f"{owner}/{repo_name}")
            issue = repo.get_issue(issue_number)

            # 添加评论
            comment = issue.create_comment(f"bella-issues-bot已处理：\n{comment_text}")

            logger.info(f"成功在 Issue #{issue_number} 下添加评论 (ID: {comment.id})")
            return True

        except Exception as e:
            logger.error(f"添加 Issue 评论失败: {str(e)}")
            raise

    def commit(
        self, message: str, add_all: bool = True, files: Optional[List[str]] = None
    ) -> str:
        """
        创建一个新的提交

        Args:
            message: 提交信息
            add_all: 是否添加所有变更的文件，默认为 True
            files: 要添加的特定文件列表，如果 add_all 为 True 则忽略此参数

        Returns:
            str: 新提交的 SHA 哈希值

        Raises:
            git.GitCommandError: 如果 Git 操作失败
        """
        try:
            # 添加文件到暂存区
            if add_all:
                self.repo.git.add(A=True)
            elif files:
                for file in files:
                    self.repo.git.add(file)

            # 创建提交
            commit = self.repo.index.commit(message)
            logger.info(f"成功创建提交: {commit.hexsha[:7]} - {message}")

            return commit.hexsha
        except git.GitCommandError as e:
            logger.error(f"创建提交失败: {str(e)}")
            raise

    def reset_to(self, target_branch: str) -> bool:
        """
        将当前分支重置到远程目标分支的状态

        Args:
            target_branch: 目标分支名称

        Returns:
            bool: 操作是否成功
        """
        try:
            # 获取远程分支
            remote_name = self.config.remote_name
            remote_branches = self.list_branches(remote=True)
            remote_target = f"{remote_name}/{target_branch}"
            # 检查目标分支是否存在于远端
            if remote_target not in remote_branches:
                logger.warning(f"目标分支 {remote_target} 不存在于远端")
                return False

            # 切换到目标分支，如果不存在则创建
            logger.info(f"切换到分支: {target_branch}")
            self.switch_branch(target_branch, create=True)

            # 强制重置到远程分支状态
            logger.info(f"重置到远程分支: {remote_target}")
            self.repo.git.reset(f"{remote_target}", hard=True)
            self.pull(target_branch)
            logger.info(f"成功重置到版本: {target_branch}")
            return True
        except git.GitCommandError as e:
            logger.error(f"重置到分支 {target_branch} 失败: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"重置过程中发生未知错误: {str(e)}")
            return False

    def reset_to_issue_branch(self, issue_id: int) -> str:
        """
        拉取指定issue对应的最新分支并切换到该分支
        如果该issue还未创建过分支，则切换到默认分支

        Args:
            issue_id: Issue编号

        Returns:
            str: 成功切换到的分支名称

        Raises:
            git.GitCommandError: 如果Git操作失败
        """
        try:
            # 确保远程仓库信息是最新的
            self.repo.git.fetch(self.config.remote_name)
            logger.info(f"成功获取远程仓库信息")
            
            # 获取所有远程分支
            remote_branches = self.repo.git.branch("-r").splitlines()
            remote_branches = [branch.strip() for branch in remote_branches]
            
            # 查找与指定issue相关的分支
            issue_branch_name = f"bella-issues-bot-{issue_id}"
            remote_issue_branch = f"{self.config.remote_name}/{issue_branch_name}"
            
            branch_exists = False
            for branch in remote_branches:
                if remote_issue_branch in branch:
                    branch_exists = True
                    break

            if branch_exists:
                # 切换到issue分支
                self.reset_to(issue_branch_name)
            else:
                self.pull()
                self.switch_branch(issue_branch_name, create=True)
            logger.info(f"成功切换到issue #{issue_id}的分支: {issue_branch_name}")
            
            return issue_branch_name
        except git.GitCommandError as e:
            logger.error(f"切换到issue分支时出错: {str(e)}")
            raise
