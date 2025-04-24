import os
import pathlib
from typing import Set, List

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern


class FileManager:
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

        return PathSpec.from_lines(GitWildMatchPattern, patterns)

    @staticmethod
    def get_all_files(root_dir: str, gitignore_spec: PathSpec) -> Set[str]:
        """Get all files in directory that aren't ignored by .gitignore"""
        all_files = set()
        root_path = pathlib.Path(root_dir)

        for path in root_path.rglob("*"):
            if path.is_file():
                # 检查路径中是否包含以点开头的目录
                parts = path.relative_to(root_path).parts
                if any(part.startswith(".") for part in parts[:-1]):  # 排除路径中包含以点开头的目录
                    continue
                if parts[len(parts) - 1] == ".gitignore":
                    continue
                # 转换为相对路径
                relative_path = str(path.relative_to(root_path))

                # 跳过匹配 gitignore 模式的文件
                if not gitignore_spec.match_file(relative_path):
                    all_files.add(relative_path)

        return all_files

    @staticmethod
    def generate_toml_content(files: Set[str]) -> str:
        """Generate TOML content in the required format"""
        toml_dict = {
            "linting": {},
            "files": {file: "selected" for file in sorted(files)},
        }

        # Convert to TOML string with comments
        header_comments = [
            "# Remove '#' to select a file or turn off linting.\n",
            "\n",
            "# Linting with BLACK (Python) enhances code suggestions from LLMs. To disable linting, uncomment the relevant option in the linting settings.\n",
            "\n",
            "# gpt-engineer can only read selected files. Including irrelevant files will degrade performance, cost additional tokens and potentially overflow token limit.\n",
            "\n",
        ]

        toml_content = "".join(header_comments)
        toml_content += "[linting]\n"
        toml_content += '# "linting" = "off"\n\n'
        toml_content += "[files]\n"

        # Add file entries
        for file in sorted(files):
            toml_content += f'#"{file}" = "selected"\n'

        return toml_content

    @staticmethod
    def get_all_files_without_ignore(root_dir: str) -> Set[str]:
        # Read gitignore patterns
        gitignore_spec = FileManager.read_gitignore(root_dir)

        # Get all files
        return FileManager.get_all_files(root_dir, gitignore_spec)

    @staticmethod
    def create_selection_file(root_dir: str) -> None:
        """
        Create file selection TOML by scanning directory and excluding .gitignore files.
        Writes result to .gpteng/file_selection.toml
        """
        try:
            # Get all files
            all_files = FileManager.get_all_files_without_ignore(root_dir)

            # Generate TOML content
            toml_content = FileManager.generate_toml_content(all_files)

            # Ensure .gpteng directory exists
            gpteng_dir = os.path.join(root_dir, ".gpteng")
            os.makedirs(gpteng_dir, exist_ok=True)

            # Write selection file
            selection_path = os.path.join(gpteng_dir, "file_selection.toml")
            with open(selection_path, "w", encoding="utf-8") as f:
                f.write(toml_content)

        except Exception as e:
            raise Exception(f"Error creating selection file: {str(e)}")

    @staticmethod
    def get_selected_files(root_dir: str) -> Set[str]:
        """
        Read all filenames from .gpteng/file_selection.toml
        Returns a set of filenames (both commented and uncommented)

        Args:
            root_dir (str): The root directory containing .gpteng folder

        Returns:
            Set[str]: Set of all filenames found in the toml file
        """
        selection_path = os.path.join(root_dir, ".gpteng", "file_selection.toml")

        try:
            # First try to parse as valid TOML
            with open(selection_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Get all filenames by parsing lines manually since some might be commented
            files = set()
            for line in content.split("\n"):
                line = line.strip()
                if line.endswith('" = "selected"'):
                    # Extract filename between quotes, remove any leading #
                    filename = line.split('"')[1]
                    files.add(filename)

            return files

        except Exception as e:
            raise Exception(f"Error reading selection file: {str(e)}")

    @staticmethod
    def reuncomment_files(root_dir: str, files_to_uncomment: List[str]) -> None:
        """
        重新设置文件选择状态：取消注释指定的文件，确保其他文件被注释

        Args:
            root_dir (str): The root directory containing .gpteng folder
            files_to_uncomment (List[str]): List of filenames to uncomment
        """
        selection_path = os.path.join(root_dir, ".gpteng", "file_selection.toml")

        try:
            # 读取文件
            with open(selection_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # 将要取消注释的文件转换为集合
            files_set = set(files_to_uncomment)

            # 处理每一行
            for i, line in enumerate(lines):
                line = line.strip()

                # 跳过非文件行
                if not (
                    line.endswith('" = "selected"') or line.endswith('" = "selected"')
                ):
                    continue

                # 检查是否是注释行
                is_commented = line.startswith("#")

                # 提取文件名
                if is_commented:
                    # 移除注释符号
                    content = line[1:].strip()
                else:
                    content = line

                # 提取文件名 (在第一对引号之间)
                if '"' in content:
                    filename = content.split('"')[1]

                    # 决定是否需要注释或取消注释
                    if filename in files_set:
                        # 需要取消注释
                        if is_commented:
                            lines[i] = line.replace("#", "", 1) + "\n"
                    else:
                        # 需要注释
                        if not is_commented:
                            lines[i] = "#" + line + "\n"

            # 写回文件
            with open(selection_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

        except Exception as e:
            raise Exception(f"更新选择文件时出错: {str(e)}")


if __name__ == "__main__":
    # Example usage
    FileManager.create_selection_file("../.")
    print(FileManager.get_selected_files("../."))
    FileManager.reuncomment_files("../.", ["pyproject.toml"])
