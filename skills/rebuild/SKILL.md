---
name: rebuild
description: 不更改 Build Number，仅触发 CI 重新打包。当用户要求重新打包、rebuild、重新触发 CI 时使用。
allowed-tools: Read, Edit, Bash(git *)
---

## 重新打包流程

按以下步骤执行：

### 1. 检查分支

```bash
git branch --show-current
```

若在 `main` 或 `master` 上，**立即停止**，提示用户切换到 `release/`、`feat/`、`fix/` 等前缀的分支。

### 2. 触发文件变更

- 读取 `fastlane/release-notes.txt`
- 检查文件**最后一行末尾**是否有尾随空格：
  - **有空格** → 删除该尾随空格
  - **无空格** → 在最后一行末尾添加一个空格
- 目的：确保文件产生 diff，触发 CI 重新打包

### 3. Git 提交

- 执行 `git add fastlane/release-notes.txt`
- 执行 `git commit`，message 为：`chore: 🔧 触发重新打包`

### 4. 推送到远端

- 执行 `git push`

### 5. 输出结果

完成后**严格按以下格式**输出（将 `BRANCH` 替换为当前分支名）：

```
✅ 重新打包已触发

- **分支**: BRANCH
- **Commit**: `chore: 🔧 触发重新打包`

已推送到远端，等待 CI 打包即可。
```
