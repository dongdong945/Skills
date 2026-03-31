---
name: feature-directory-scaffold
description: 在现有 iOS 或 SwiftUI 项目中，按 MVVM + Clean 分层为一个业务 Feature 创建目录骨架时使用；适用于用户要求新增模块、搭建 Feature scaffold、只创建目录不创建文件，且项目已经存在类似 App/Presentation、App/Domain、App/Data 分层的场景。
---

# Feature Directory Scaffold

## 概述

用于在现有 iOS 项目里，为一个业务 Feature 建立与 STAR108 风格一致的 MVVM + Clean 目录骨架。
默认只创建目录，不创建 Swift 文件；优先贴合已有分层，避免额外引入 `Modules` 之类的新根目录。

## 核心规则

- 先检查项目是否已经存在 `App/Presentation`、`App/Domain`、`App/Data` 这一类分层，再决定是否使用本 skill。
- 将“一个业务 Feature”视为最小单元；不要把单个页面、弹窗或 Step View 当成独立业务 Feature 来建整套骨架。
- 默认生成 `Presentation + Domain + Data` 全套目录；只有用户明确要求轻量模式时，才减少目录。
- 只创建目录，不创建 Swift 文件、不修改 Xcode 工程、不顺带添加 `Core` 或 `Resources` 子目录。
- 目录命名优先使用 PascalCase Feature 名称，并与项目现有命名保持一致。

## 默认目录骨架

```text
App/Presentation/Features/<Feature>/
App/Presentation/Features/<Feature>/Views/
App/Presentation/Features/<Feature>/ViewModels/
App/Presentation/Features/<Feature>/Models/
App/Domain/Entities/<Feature>/
App/Domain/Repositories/<Feature>/
App/Data/Repositories/<Feature>/
App/Data/DataSources/Remote/<Feature>/
App/Data/DataSources/Local/<Feature>/
App/Data/Models/<Feature>/
```

## 执行流程

1. 读取项目结构，确认目标仓库已经采用与 STAR108 相近的 `App/Presentation`、`App/Domain`、`App/Data` 分层。
2. 从用户请求中提取业务 Feature 名称，并规范化为 PascalCase，例如 `subscription` -> `Subscription`、`face-scan` -> `FaceScan`。
3. 优先使用 `scripts/create_feature_directories.py` 创建标准目录骨架。
4. 创建后检查哪些目录是新建的、哪些目录已存在，并在回复中明确说明。
5. 如果用户后续要补文件模板，再交给别的技能或常规实现流程处理；本 skill 只负责目录。

## 使用脚本

在项目根目录执行：

```bash
python3 /path/to/feature-directory-scaffold/scripts/create_feature_directories.py Subscription --root /path/to/project
```

仅预览将要创建的目录：

```bash
python3 /path/to/feature-directory-scaffold/scripts/create_feature_directories.py subscription --root . --dry-run
```

### 脚本行为

- 要求项目中已经存在以下基础目录：
  - `App/Presentation/Features`
  - `App/Domain/Entities`
  - `App/Domain/Repositories`
  - `App/Data/Repositories`
  - `App/Data/DataSources/Remote`
  - `App/Data/DataSources/Local`
  - `App/Data/Models`
- 如果基础目录缺失，先停止并向用户说明当前项目不符合这套脚手架假设。
- 已存在目录不会报错，会被归类为 `existing`。

## 何时不要使用

- 用户只是想新建一个页面、一个弹窗、一个临时调试视图。
- 项目并没有 `App/Presentation` / `App/Domain` / `App/Data` 这种既有分层。
- 用户要求直接创建 Swift 文件、Xcode group、UseCase 模板或 Repository 实现。

## 常见错误

- 为了“更 Clean”额外预建 `UseCases`、`Services`、`Coordinators` 等目录，导致过度设计。
- 把新 Feature 放到自创的 `Modules/` 根目录，破坏项目现有结构。
- 把 `FaceScanResult` 这种页面名误当成业务 Feature，结果生成了一整套不必要目录。
- 创建完目录后不核对结果，导致目录创建到了错误根路径。

## 回复建议

完成后优先说明两件事：

1. 新建了哪些目录。
2. 哪些目录原本已存在，因此被跳过。

如果因为项目结构不匹配而没有执行，也要直接说明缺了哪些基础目录。
