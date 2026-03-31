---
name: git-commit-writer
description: Use when 用户要求提交当前改动，或任务完成后需要根据 git diff 生成中文单行 commit message 并执行 git commit。
---

# Git 提交信息

## 概述

用于检查当前改动、生成符合约定的中文单行 commit message，并完成 `git commit`。

## 执行步骤

1. 执行 `git status` 检查是否有改动或未解决冲突。
2. 根据暂存状态读取 `git diff` 或 `git diff --cached`，必要时先执行 `git add -A` 暂存当前工作相关文件。
3. 阅读 diff，判定唯一前缀：`feat`、`fix`、`refactor`、`docs` 或 `chore`。
4. 生成严格符合规范的提交信息：`<prefix>: <emoji> <中文动词短语>`。
5. 执行 `git commit -m "<message>"`，随后执行 `git branch --show-current` 与 `git log --oneline -1` 记录结果。
6. 如果当前分支是 `main` 或 `master`，在最终输出里追加结构化风险警告，但不要回滚已完成的提交。

## 快速检查

- 无改动时直接停止，不生成 commit。
- 有冲突时直接停止，先让用户解决冲突。
- 提交信息必须是单行，且动词短语必须是中文。
- 英文只允许出现在技术标识符里。
- 输出里必须包含提交信息；主分支提交时必须追加警告。

## 资源

- 无额外资源文件。
