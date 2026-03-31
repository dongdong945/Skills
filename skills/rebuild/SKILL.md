---
name: rebuild
description: Use when 用户要求重新打包、rebuild 或重新触发 CI，并且不希望变更 Build Number，只需要制造一次可提交的变更来触发流水线。
---

# 重新打包

## 概述

用于在不修改 Build Number 的前提下，制造一次最小文件变更并提交推送，从而重新触发 CI 打包。

默认采用最低成本的直接执行方式，无需深度推理，只做触发重新打包所需的最小改动。

## 执行步骤

1. 检查当前分支；如果在 `main` 或 `master`，立即停止并提示用户切换到功能分支或发布分支。
2. 读取 `fastlane/release-notes.txt`，通过切换文件最后一行的尾随空格来制造最小 diff。
3. 执行 `git add fastlane/release-notes.txt`。
4. 执行 `git commit -m "chore: 🔧 触发重新打包"`。
5. 执行 `git push`。
6. 按固定格式返回分支和 Commit 信息。

## 快速检查

- 不修改 Build Number。
- 只使用 `fastlane/release-notes.txt` 作为触发变更文件。
- 尾随空格的切换必须稳定且可重复。
- 输出结果必须使用固定模板。
- 只在非 `main` / `master` 分支执行。

- 优先制造最小可提交变更，无需深度推理或额外改动。

## 资源

- 无额外资源文件。
