---
name: bump-build-release
description: Use when 用户要求触发 iOS 或 Xcode 项目的正式包打包，并且需要递增 Build Number、更新发布说明、提交并推送到远端以触发 CI。
---

# 正式包打包

## 概述

用于递增 Xcode 项目的 Build Number，更新 `fastlane/release-notes.txt`，并通过提交与推送触发 Release 正式包打包。

## 执行步骤

1. 检查当前分支；如果在 `main` 或 `master`，立即停止并提示用户切换到功能分支或发布分支。
2. 在 `*.xcodeproj/project.pbxproj` 中找到所有 `CURRENT_PROJECT_VERSION = <N>;`，统一加 1，并记录新的 Build Number 为 `NEW_BUILD`。
3. 更新 `fastlane/release-notes.txt`：
   - 将 `打包环境:` 后面的内容替换为 `Release`
   - 将 `测试内容:` 之后的全部内容替换为：
     ```text
     Build NEW_BUILD
     正式包
     ```
4. 执行 `git add <xcodeproj>/project.pbxproj fastlane/release-notes.txt`。
5. 执行 `git commit -m "chore: 🔧 更新 build 至 NEW_BUILD 并打正式包"`。
6. 执行 `git push`。
7. 按固定格式返回 Build Number、打包环境、分支和 Commit 信息。

## 快速检查

- 只在非 `main` / `master` 分支执行。
- 所有 `CURRENT_PROJECT_VERSION` 必须同步更新。
- `release-notes.txt` 的打包环境必须是 `Release`。
- 测试内容必须固定为 `Build NEW_BUILD` 与 `正式包`。
- 输出结果必须使用固定模板。

## 资源

- 无额外资源文件。
