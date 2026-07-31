---
name: rebuild
description: Use when 用户要求重新打包、rebuild 或重新触发 CI，并且不希望变更 Build Number，只需要制造一次可提交的变更来触发流水线。
---

# 重新打包

## 概述

用于在不修改 Build Number 的前提下，制造一次最小文件变更并提交推送，从而重新触发 CI 打包。

默认采用最低成本的直接执行方式，无需深度推理，只做触发重新打包所需的最小改动。

## 执行步骤

1. 执行 `git status --short` 检查冲突、已暂存和未暂存内容；保留既有改动，禁止使用 `git add -A`。
2. 检查当前分支；如果在 `main` 或 `master`，立即停止并提示用户切换到功能分支或发布分支。
3. 读取 `fastlane/release-notes.txt`，仅在最后一个非空行切换一个 ASCII 尾随空格，制造稳定且可重复的最小 diff。此文件变更是 CI 的触发条件，必须保留。
4. 仅暂存 `fastlane/release-notes.txt`，并确认暂存 diff 只包含该文件及该行的尾随空格变化。不要对这个文件运行 `git diff --check`，因为该检查会按预期报告此 CI 触发空格。
5. 执行 `git commit --only -m "chore: 🔧 触发重新打包" -- fastlane/release-notes.txt`，不得混入既有暂存内容。
6. 使用 `git show --format= --name-only HEAD` 验证提交路径仅为 `fastlane/release-notes.txt`，再执行 `git push`。
7. 按固定格式返回分支和 Commit 信息；如仍有既有改动，明确说明其未被本次提交包含。

## 快速检查

- 不修改 Build Number。
- 只使用 `fastlane/release-notes.txt` 作为触发变更文件。
- 尾随空格的切换必须稳定且可重复。
- 尾随空格是 CI 触发协议的例外，不对 `fastlane/release-notes.txt` 运行 `git diff --check`。
- 提交只能包含 `fastlane/release-notes.txt`；已暂存或未暂存的其他内容必须保留。
- 输出结果必须使用固定模板。
- 只在非 `main` / `master` 分支执行。

- 优先制造最小可提交变更，无需深度推理或额外改动。

## 资源

- 无额外资源文件。
