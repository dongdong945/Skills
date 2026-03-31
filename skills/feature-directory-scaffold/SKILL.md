---
name: feature-directory-scaffold
description: Use when 用户要求在现有 iOS 或 SwiftUI 项目中，为一个业务 Feature 创建 MVVM + Clean 目录骨架，并且只需要创建目录、不需要创建文件。
---

# Feature 目录骨架

## 概述

用于在现有 iOS 项目里，为一个业务 Feature 建立与 MVVM + Clean 分层一致的目录骨架。
默认只创建目录，不创建 Swift 文件；优先贴合已有分层，避免额外引入 `Modules` 之类的新根目录。

默认采用最低成本的直接执行方式，无需深度推理，不额外发明目录层级或脚手架模式。

## 执行步骤

1. 先检查项目是否已经存在 `App/Presentation`、`App/Domain`、`App/Data` 这一类分层，再决定是否使用本 skill。
2. 将“一个业务 Feature”视为最小单元；不要把单个页面、弹窗或 Step View 当成独立业务 Feature。
3. 从用户请求中提取业务 Feature 名称，并规范化为 PascalCase，例如 `subscription` -> `Subscription`、`face-scan` -> `FaceScan`。
4. 优先使用 `scripts/create_feature_directories.py` 创建标准目录骨架。
5. 创建后检查哪些目录是新建的、哪些目录已存在，并在回复中明确说明。
6. 如果项目缺少基础目录，立即停止并向用户说明当前项目不符合这套脚手架假设。

## 快速检查

- 默认生成 `Presentation + Domain + Data` 全套目录。
- 只创建目录，不创建 Swift 文件、不修改 Xcode 工程。
- 目录命名优先使用 PascalCase。
- 轻量场景只有在用户明确要求时才减少目录。
- 回复中必须区分“新建目录”和“已存在目录”。

- 优先按现有规则直接建目录，无需深度推理或额外架构发散。

## 资源

- 脚本：`scripts/create_feature_directories.py`
- 无其他必需资源。
