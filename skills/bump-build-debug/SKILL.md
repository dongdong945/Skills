---
name: bump-build-debug
description: 递增 Xcode 项目的 Build Number 并提交测试包打包。当用户要求打包、打测试包、debug 打包时使用。
allowed-tools: Read, Grep, Edit, Bash(git *)
---

## 测试包打包流程

按以下步骤执行：

### 1. 检查分支

```bash
git branch --show-current
```

若在 `main` 或 `master` 上，**立即停止**，提示用户切换到 `release/`、`feat/`、`fix/` 等前缀的分支。

### 2. 递增 CURRENT_PROJECT_VERSION

- 在 `*.xcodeproj/project.pbxproj` 中找到所有 `CURRENT_PROJECT_VERSION = <N>;`
- 将 `<N>` 加 1，所有出现位置统一更新
- 记录新的 Build Number 为 `NEW_BUILD`

### 3. 更新 release-notes.txt

- 执行 `git log --oneline -10` 获取最近提交记录
- 根据提交内容总结本次变更，生成一句话中文描述，**不超过 20 字**
- 读取 `fastlane/release-notes.txt`
- 将 `打包环境:` 后面的内容替换为 `Debug`
- 将 `测试内容:` 之后的**所有内容**替换为：
  ```
  Build NEW_BUILD
  SUMMARY
  ```
  其中 `SUMMARY` 为生成的一句话总结

### 4. Git 提交

- 执行 `git add <xcodeproj>/project.pbxproj fastlane/release-notes.txt`
- 执行 `git commit`，message 为：`chore: 🔧 更新 build 至 NEW_BUILD 并打包`

### 5. 推送到远端

- 执行 `git push`

### 6. 输出结果

完成后**严格按以下格式**输出（将 `NEW_BUILD` 替换为实际的新 Build Number，`BRANCH` 替换为当前分支名）：

```
✅ 测试包打包完成

- **Build Number**: NEW_BUILD
- **打包环境**: Debug
- **分支**: BRANCH
- **Commit**: `chore: 🔧 更新 build 至 NEW_BUILD 并打包`

已推送到远端，等待 CI 打包即可。
```
