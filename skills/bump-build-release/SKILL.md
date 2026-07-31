---
name: bump-build-release
description: Use when 用户要求触发 iOS 或 Xcode 项目的正式包打包，并且需要递增 Build Number、更新发布说明、提交并推送到远端以触发 CI。
---

# 正式包打包

## 概述

用于递增 Xcode 项目的 Build Number，更新 `fastlane/release-notes.txt`，并通过提交与推送触发 Release 正式包打包。

默认采用最低成本的直接执行方式，无需深度推理，不做与打包无关的扩展分析。

## 执行步骤

1. 执行 `git status --short` 检查冲突、已暂存和未暂存内容；保留既有改动，禁止使用 `git add -A`。
2. 检查当前分支；如果在 `main` 或 `master`，立即停止并提示用户切换到功能分支或发布分支。
3. 在当前分支的第一父链上查找最近一次打包提交，记录为 `LAST_BUILD_COMMIT`：
   ```bash
   git log --first-parent --extended-regexp \
     --grep='^chore: .*更新 build 至 [0-9]+ 并(打包|打正式包)$' \
     -n 1 --format='%H'
   ```
4. 生成一句不超过 20 字、不得换行的中文测试内容摘要 `SUMMARY`：
   - 如果找到 `LAST_BUILD_COMMIT`，读取从该提交之后到当前 `HEAD` 的所有非合并提交标题，并根据全部标题归纳摘要，不得只总结最新一条：
     ```bash
     git log --reverse --no-merges --format='%s' "${LAST_BUILD_COMMIT}..HEAD"
     ```
   - 如果没有找到 `LAST_BUILD_COMMIT`，将 `SUMMARY` 设为 `初始化打包`。
   - 如果找到 `LAST_BUILD_COMMIT`，但区间内没有非合并提交，将 `SUMMARY` 设为 `无功能变更`。
5. 在 `*.xcodeproj/project.pbxproj` 中找到所有 `CURRENT_PROJECT_VERSION = <N>;`，统一加 1，并记录新的 Build Number 为 `NEW_BUILD`。
6. 在 `*.xcodeproj/project.pbxproj` 中读取所有 `MARKETING_VERSION = <VERSION>;`：
   - 所有值必须一致；不一致时停止并提示用户处理。
   - 记录该值为 `MARKETING_VERSION`，但不在此流程中修改它。
7. 通过 `git rev-parse --show-toplevel` 获取仓库根目录名，记录为 `PROJECT_NAME`。
8. 更新 `fastlane/release-notes.txt`：
   - 将第一行完整替换为 `PROJECT_NAME vMARKETING_VERSION`。
   - 将 `打包环境:` 后面的内容替换为 `Release`
   - 将 `测试内容:` 之后的全部内容替换为：
     ```text
     Build NEW_BUILD
     SUMMARY
     ```
9. 仅暂存本次修改的所有 `*.xcodeproj/project.pbxproj` 和 `fastlane/release-notes.txt`。对这些路径执行 `git diff --cached --check -- <paths>`，并确认其 diff 与路径列表。
10. 执行 `git commit --only -m "chore: 🔧 更新 build 至 NEW_BUILD 并打正式包" -- <paths>`。提交只能包含项目描述文件和 `fastlane/release-notes.txt`，不得混入既有暂存内容。
11. 使用 `git show --format= --name-only HEAD` 验证提交路径仅为上述文件，再执行 `git push`。
12. 按固定格式返回项目名、Build Number、Marketing Version、打包环境、分支和 Commit 信息；如仍有既有改动，明确说明其未被本次提交包含。

## 快速检查

- 只在非 `main` / `master` 分支执行。
- 所有 `CURRENT_PROJECT_VERSION` 必须同步更新。
- 所有 `MARKETING_VERSION` 必须一致，且 `release-notes.txt` 第一行必须为 `PROJECT_NAME vMARKETING_VERSION`。
- `release-notes.txt` 的打包环境必须是 `Release`。
- 摘要必须基于上次打包后的全部非合并提交；没有历史打包提交时必须为 `初始化打包`。
- 测试内容必须包含 `Build NEW_BUILD`，且下一行只能有一句中文摘要。
- 提交只能包含本次修改的 `*.xcodeproj/project.pbxproj` 与 `fastlane/release-notes.txt`；已暂存或未暂存的其他内容必须保留。
- 输出结果必须使用固定模板。

- 优先直接执行既定流程，无需深度推理或额外方案比较。

## 资源

- 无额外资源文件。
