---
name: git-commit-workflow
description: Use when 用户要求提交当前改动，或任务完成后需要根据 git diff 生成提交信息。
---

# Git 提交流程

## 概述

用于检查当前改动、根据 `config.toml` 中的 `git-commit-instructions` 生成中文 commit message，并完成 `git commit`。

默认采用最低成本的直接执行方式，无需深度推理，不做与当前提交无关的额外延伸。

## 执行步骤

1. 确认可以读取 `config.toml`，且其中存在 `git-commit-instructions`。
2. 执行 `git status` 检查是否有改动或未解决冲突。
3. 根据暂存状态读取 `git diff` 或 `git diff --cached`，必要时先执行 `git add -A` 暂存当前工作相关文件。
4. 阅读 diff，判定唯一前缀：`feat`、`fix`、`refactor`、`docs` 或 `chore`。
5. 严格遵循 `config.toml` 中的 `git-commit-instructions` 生成提交信息；标题单行，body 按配置要求生成。
6. 使用支持多段 body 的方式执行提交，优先使用临时 message file 并执行 `git commit -F <message-file>`。
7. 提交后执行 `git branch --show-current` 与 `git log --oneline -1` 记录结果。
8. 如果当前分支是 `main` 或 `master`，在最终输出里追加结构化风险警告，但不要回滚已完成的提交。

## 快速检查

- 无改动时直接停止，不生成 commit。
- 有冲突时直接停止，先让用户解决冲突。
- 如果无法读取 `config.toml`，或其中不存在 `git-commit-instructions`，直接停止并提示用户补齐配置；禁止自行回退到旧的单行提交规范。
- 提交标题必须是单行，且动词短语必须是中文。
- 提交 body 必须遵循 `config.toml` 中的三段式结构，除非用户明确要求只生成单行提交信息。
- 英文只允许出现在技术标识符里。
- 输出里必须包含提交信息；主分支提交时必须追加警告。
- prefix、emoji、标题和 body 结构以 `config.toml` 中的 `git-commit-instructions` 为准。
- 不要在本 skill 内复制大段格式规范；本 skill 只负责检查改动、生成提交、执行提交和回显结果。
- 优先根据当前 diff 直接生成并提交，无需深度推理或额外延伸。

## 资源

- 无额外资源文件。
