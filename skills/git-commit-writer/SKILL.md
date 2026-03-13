---
name: git-commit-writer
description: 分析 git diff 生成精炼的单行中文 Commit Message 并执行提交。当用户完成代码修改需要 commit，或 agent 完成功能实现/Bug 修复/重构后需要提交时使用。
---

# Git Commit Writer

## 工作流程

### 1. 检查变更

```bash
git status
```

- 无变更 → 告知用户无需提交，终止流程
- 有未合并冲突 → 告知用户解决冲突，终止流程
- 有变更 → 继续

### 2. 暂存与获取 Diff

- 已暂存 → `git diff --cached`
- 未暂存 → `git diff` 查看后，`git add -A` 暂存，再 `git diff --cached` 确认
- 有 untracked 文件 → 评估是否属于当前工作，属于则一并暂存

### 3. 分类变更

阅读 diff，判定**唯一**前缀：

| Prefix     | 场景                                   |
| ---------- | -------------------------------------- |
| `feat`     | 新功能、新 UI 组件、新文件实现功能     |
| `fix`      | Bug 修复、崩溃修复、错误处理修正       |
| `refactor` | 代码重构、架构调整，不改变外部行为     |
| `docs`     | 仅文档变更                             |
| `chore`    | 构建配置、依赖更新、CI、工具链维护     |

跨类别时选主导类别，优先级：feat > fix > refactor > chore > docs。

### 4. 生成 Commit Message

**格式（严格）：**

```
<prefix>: <emoji> <中文动词短语>
```

**Emoji 映射：**

| Prefix   | Emoji |
| -------- | ----- |
| feat     | ✨     |
| fix      | 🐛     |
| refactor | ♻️     |
| docs     | 📝     |
| chore    | 🔧     |

**规则：**

- 必须单行，禁止多行、禁止 body、禁止作者信息
- 动词短语必须中文，英文仅限技术标识符（文件名、类名、方法名、框架名）
- 以动词开头（添加/修复/移除/重构/更新/优化/实现/替换/调整/配置/迁移/支持/处理/完善/拆分/合并/封装/简化/提取/补充）
- 具体描述变更内容，禁止模糊表述

**正例：**

```
feat: ✨ 添加用户登录功能
fix: 🐛 修复 PreviewView 切换前置摄像头时崩溃
refactor: ♻️ 移除 Helper 单例，改用 Environment 注入
chore: 🔧 更新 Xcode 项目配置支持 Swift 6
```

**反例（禁止）：**

- `feat: ✨ Add user login` ← 英文动词短语
- `feat: ✨ 更新代码` ← 太模糊
- `fix: 🐛 修复bug` ← 太模糊

### 5. 执行提交

```bash
git commit -m "<message>"
git branch --show-current
git log --oneline -1
```

提交完成后检查当前分支：

- 若当前分支是 `main` 或 `master`，**不要阻塞提交结果**，改为在最终输出中追加结构化警告
- 警告只用于提醒风险，不要求用户二次确认，也不回滚已完成的提交

### 6. 输出结果

```
提交信息: <实际使用的 commit message>
```

若提交后检测到当前分支为 `main` 或 `master`，在上述结果后追加：

```
警告信息: 当前分支为 <main|master>，已直接提交，请注意主分支提交风险
```
