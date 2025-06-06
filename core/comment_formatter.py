import re
from typing import List, Optional

from core.log_config import get_logger

logger = get_logger(__name__)


class CommentFormatter:
    """
    处理 GitHub 评论中的 diff 代码块，将代码内容替换为指定格式的文本
    """

    @staticmethod
    def format_diff_blocks(comment_text: str, branch_name: str) -> str:
        """
        将评论中的所有 diff 块中的代码替换为指定格式的文本

        Args:
            comment_text: 原始评论内容
            branch_name: 分支名称，用于替换文本

        Returns:
            处理后的评论内容
        """
        logger.info(f"开始处理评论中的 diff 块，分支名称: {branch_name}")

        # 提取所有 ```diff 代码块
        pattern = r'(```diff\s+)(.*?)(```)'
        
        def replace_diff_block(match):
            # 获取 diff 块的内容
            diff_start = match.group(1)  # ```diff 开头
            diff_content = match.group(2)  # diff 内容
            diff_end = match.group(3)  # ``` 结尾
            
            # 提取文件路径信息
            file_paths = CommentFormatter._extract_file_paths(diff_content)
            
            if file_paths:
                # 保留文件路径信息，替换其余内容
                file_info = "\n".join(file_paths)
                replacement = f"{diff_start}{file_info}\n在{branch_name}分支可查看详细代码\n{diff_end}"
                return replacement
            else:
                # 如果没有找到文件路径信息，直接替换整个代码块
                return f"{diff_start}在{branch_name}分支可查看详细代码\n{diff_end}"
        
        # 替换所有匹配的 diff 块
        formatted_text = re.sub(pattern, replace_diff_block, comment_text, flags=re.DOTALL)
        
        logger.info("评论中的 diff 块处理完成")
        return formatted_text

    @staticmethod
    def _extract_file_paths(diff_content: str) -> List[str]:
        """
        从 diff 内容中提取文件路径信息

        Args:
            diff_content: diff 块的内容

        Returns:
            文件路径信息列表
        """
        file_paths = []
        
        # 匹配 --- 和 +++ 开头的行，这些通常包含文件路径信息
        path_lines = re.findall(r'^(---\s+.*|\+\+\+\s+.*)', diff_content, re.MULTILINE)
        
        # 如果找到了文件路径行，添加到结果列表
        if path_lines:
            file_paths.extend(path_lines)
        
        # 也可能有 diff --git 格式的行
        git_diff_lines = re.findall(r'^(diff --git .*)', diff_content, re.MULTILINE)
        if git_diff_lines:
            file_paths.extend(git_diff_lines)
        
        return file_paths


if __name__ == "__main__":
    # 测试示例
    test_comment = """
这是一个测试评论

```diff
--- api/sdk/src/main/java/com/ke/bella/openapi/protocol/completion/CompletionRequest.java
+++ api/sdk/src/main/java/com/ke/bella/openapi/protocol/completion/CompletionRequest.java
public class CompletionRequest {
    private String model;
    private List<Message> messages;
-    private Double temperature;
+    private Double temperature = 0.7;
    private Integer maxTokens;
}
```

其他内容
"""
    
    formatted = CommentFormatter.format_diff_blocks(test_comment, "bella-issues-bot-8")
    print(formatted)
