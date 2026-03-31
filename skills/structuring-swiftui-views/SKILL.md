---
name: structuring-swiftui-views
description: Use when 编写、重构或审查 SwiftUI `View` 文件，需要统一 `@Environment`、属性、`body`、方法与 `#Preview` 的顺序，控制 `body` 的拆分方式，并统一注释与父子视图 padding 职责边界。
---

# SwiftUI View 结构

## 概述

用于统一 SwiftUI `View` 文件的组织顺序、`body` 拆分方式、注释规则和 padding 职责边界。

默认采用最低成本的结构整理方式，无需深度推理，不做与当前 View 无关的额外抽象。

## 执行步骤

1. 先读取 `references/view-structure-conventions.md`，再开始写代码或 review。
2. 先确认当前文件是 SwiftUI `View`、页面内私有子视图或可复用组件；不是就不要套用这套规则。
3. 按固定顺序组织文件：`@Environment...` -> public properties -> private properties -> `body` -> public methods -> private methods -> `#Preview`。
4. 让 `body` 优先只保留 `contentView` 与整个 View 级别的 modifier。
5. 拆分 `body` 时，优先提取成私有 `@ViewBuilder` 计算属性；只有在需要参数、复用局部输入或表达更自然时，再用私有 `@ViewBuilder` 函数。
6. 让每个组件负责自己的内部 UI 和内部 padding；父视图只负责多个子视图之间的间距、外层排布和容器级 padding。
7. 为 View 本身、每个属性、每个组件、每个方法补简短中文注释，只说明职责或意图。

## 快速检查

- `@Environment...` 永远放在最前面，不和普通属性交错。
- public properties 与 private properties 分开，不要混排。
- `body` 中优先保留 `contentView` 和整个 View 级 modifier。
- 私有 `@ViewBuilder` 计算属性优先于私有 `@ViewBuilder` 函数。
- 子组件负责内部 padding，父视图负责子视图之间的 spacing 和外层 padding。
- View、属性、组件、方法都要有简短中文注释。
- `#Preview` 位于文件末尾。

- 优先按既定结构直接整理 View，无需深度推理或额外抽象发散。

## 资源

- 参考：`references/view-structure-conventions.md`
