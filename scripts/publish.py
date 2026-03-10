#!/usr/bin/env python3
"""
从 Obsidian vault 过滤并发布新闻到 daily-news-digest 仓库。

功能：
1. 扫描 vault 的 新闻信息/news/ 和 新闻信息/深度解读/
2. 移除 YAML frontmatter
3. 移除「对我的启发」或「对我的价值」章节
4. 对比目标目录，只处理新增/变更文件（内容 hash）
5. 复制到 daily-news-digest 对应子目录
6. git add + commit + push
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

VAULT_BASE = Path.home() / "obsidian-stuff" / "thoughts" / "新闻信息"
REPO_BASE = Path.home() / "obsidian-stuff" / "daily-news-digest"

SOURCE_DIRS = {
    VAULT_BASE / "news": REPO_BASE / "news",
    VAULT_BASE / "深度解读": REPO_BASE / "深度解读",
}

# 关键词
_PERSONAL_KEYWORDS = r"(对我的启发|对我的.*?价值|Actionable Value)"

# 匹配章节标题形式（会跳过后续内容直到下一个标题/分隔线）：
#   ## 7. 对我的启发 / ### 对我的价值 / **7. 对我的启发** / **对我的具体价值**：
PERSONAL_SECTION_RE = re.compile(
    r"^(#{1,4}\s+(\d+\.\s*)?|\*\*(\d+\.\s*)?)" + _PERSONAL_KEYWORDS,
)

# 匹配任何包含个人关键词加粗的行（各种列表/编号形式，单行删除）：
#   - **对我的启发**：xxx / * **对我的价值**：xxx / 6. **对我的具体价值 (Actionable Value)**: xxx
PERSONAL_LINE_RE = re.compile(
    r"\*\*" + _PERSONAL_KEYWORDS,
)

# 匹配 YAML frontmatter
FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)


def remove_frontmatter(content: str) -> str:
    return FRONTMATTER_RE.sub("", content, count=1)


def remove_personal_sections(content: str) -> str:
    lines = content.split("\n")
    result = []
    skipping = False

    for line in lines:
        stripped = line.strip()

        # 检查是否是章节标题形式 → 跳过后续内容直到下一个标题
        if PERSONAL_SECTION_RE.match(stripped):
            skipping = True
            continue

        # 检查是否包含个人关键词加粗 → 只删除该行
        if PERSONAL_LINE_RE.search(stripped):
            continue

        if skipping:
            # 遇到下一个标题或分隔线时停止跳过
            if re.match(r"^#{1,4}\s+", stripped) or re.match(r"^---\s*$", stripped):
                skipping = False
                result.append(line)
            continue

        result.append(line)

    return "\n".join(result)


def filter_content(content: str) -> str:
    content = remove_frontmatter(content)
    content = remove_personal_sections(content)
    # 清理开头多余空行
    content = content.lstrip("\n")
    return content


def file_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def git_run(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(
        ["git"] + list(args),
        cwd=cwd or REPO_BASE,
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> None:
    changed_files: list[str] = []

    for src_dir, dst_dir in SOURCE_DIRS.items():
        if not src_dir.exists():
            print(f"源目录不存在，跳过: {src_dir}")
            continue

        dst_dir.mkdir(parents=True, exist_ok=True)

        for src_file in sorted(src_dir.glob("*.md")):
            raw = src_file.read_text(encoding="utf-8")
            filtered = filter_content(raw)
            dst_file = dst_dir / src_file.name

            # 对比 hash，只处理新增或变更文件
            if dst_file.exists():
                existing_hash = file_hash(dst_file.read_text(encoding="utf-8"))
                if file_hash(filtered) == existing_hash:
                    continue

            dst_file.write_text(filtered, encoding="utf-8")
            rel_path = dst_file.relative_to(REPO_BASE)
            changed_files.append(str(rel_path))
            print(f"已更新: {rel_path}")

    if not changed_files:
        print("没有新增或变更的文件。")
        return

    print(f"\n共 {len(changed_files)} 个文件变更，正在提交...")

    for f in changed_files:
        git_run("add", f)

    git_run("commit", "-m", f"更新 {len(changed_files)} 篇新闻")

    # 获取当前分支名并 push
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=REPO_BASE, capture_output=True, text=True, check=True,
    )
    branch = result.stdout.strip()
    try:
        git_run("push")
    except subprocess.CalledProcessError:
        git_run("push", "-u", "origin", branch)

    print("发布完成！")


if __name__ == "__main__":
    main()
