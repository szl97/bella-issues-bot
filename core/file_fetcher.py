import os
import pathlib
from typing import Set

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern


class FileFetcher:
    """Manages file operations and selections for the project"""

    @staticmethod
    def read_gitignore(root_dir: str) -> PathSpec:
        """Read .gitignore file and create a PathSpec for pattern matching"""
        gitignore_path = os.path.join(root_dir, ".gitignore")
        patterns = []

        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.append(line)

        gpteng_path = os.path.join(root_dir, ".eng", ".engignore")

        if os.path.exists(gpteng_path):
            with open(gpteng_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.append(line)
        return PathSpec.from_lines(GitWildMatchPattern, patterns)

    @staticmethod
    def get_all_files(root_dir: str, gitignore_spec: PathSpec) -> Set[str]:
        """Get all files in directory that aren't ignored by .gitignore"""
        all_files = set()
        root_path = pathlib.Path(root_dir)

        for path in root_path.rglob("*"):
            if path.is_file():
                # 转换为相对路径
                relative_path = str(path.relative_to(root_path))

                # 跳过匹配 gitignore 模式的文件
                if not gitignore_spec.match_file(relative_path):
                    all_files.add(relative_path)

        return all_files

    @staticmethod
    def get_all_files_without_ignore(root_dir: str) -> Set[str]:
        # Read gitignore patterns
        gitignore_spec = FileFetcher.read_gitignore(root_dir)

        # Get all files
        return FileFetcher.get_all_files(root_dir, gitignore_spec)


if __name__ == "__main__":
    # Example usage
    print(FileFetcher.get_all_files_without_ignore(".."))
