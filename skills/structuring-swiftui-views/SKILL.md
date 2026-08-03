---
name: structuring-swiftui-views
description: Use when 编写、重构或审查 SwiftUI `View` 文件，需要统一 `@Environment`、属性、`body`、方法与 `#Preview` 的顺序，判断局部 `@ViewBuilder` 与独立子 `View` 的拆分边界，并统一布局组合、注释与父子视图 padding 职责。
---

# SwiftUI View 结构

## 概述

用于统一 SwiftUI `View` 文件的组织顺序、`body` 拆分方式、注释规则和 padding 职责边界。

默认采用最低成本的结构整理方式，无需深度推理，不做与当前 View 无关的额外抽象。

## 执行步骤

1. 先读取 `references/view-structure-conventions.md`，再开始写代码或 review。
2. 先确认当前文件是 SwiftUI `View`、页面内私有子视图或可复用组件；不是就不要套用这套规则。
3. 按固定顺序组织文件：`@Environment...` -> public properties -> private properties -> `body` -> public methods -> private methods -> 同文件 private 子 `View` -> `#Preview`。
4. 让 `body` 优先只保留 `contentView` 与整个 View 级别的 modifier。
5. 按职责和复杂度拆分 `body`：小型、无入参、无独立状态的固定区块使用私有 `@ViewBuilder` 计算属性；只需简单参数且仍是轻量布局片段时使用私有 `@ViewBuilder` 函数。
6. 区块需要模型、`Binding`、独立状态、生命周期、异步任务、复杂分支或独立 Preview 时，提取为独立子 `View`；只服务当前页面时可使用同文件 `private struct`，可复用或体积较大时移到独立文件。
7. 让每个组件负责自己的内部 UI 和内部 padding；父视图只负责多个子视图之间的间距、外层排布和容器级 padding。
8. 组织叠加布局时，优先判断是否应使用 `overlay` 或 `background`；只有多个同级 View 需要共同参与叠放、对齐或布局时才使用 `ZStack`。
9. 只在注释能解释非显然的业务规则、状态边界、异步清理或生命周期约束时补充简短中文注释。不要为自解释的 View、属性、组件或方法机械添加注释。

## 快速检查

- `@Environment...` 永远放在最前面，不和普通属性交错。
- public properties 与 private properties 分开，不要混排。
- `body` 中优先保留 `contentView` 和整个 View 级 modifier。
- 小型固定区块优先使用私有 `@ViewBuilder` 计算属性；简单参数化区块才使用私有 `@ViewBuilder` 函数。
- 需要模型、`Binding`、独立状态、生命周期、异步任务、复杂分支或独立 Preview 的区块已提取为独立子 `View`。
- 页面私有子 View 优先使用同文件 `private struct`；可复用或体积较大的子 View 使用独立文件。
- 同文件 private 子 `View` 放在主 View 实现之后、`#Preview` 之前。
- 子组件负责内部 padding，父视图负责子视图之间的 spacing 和外层 padding。
- 单个 View 的背景、前景装饰或浮层优先使用 `background` / `overlay`；同级内容共同叠放时使用 `ZStack`。
- 注释只解释非显然的业务规则、状态边界、异步清理或生命周期约束；不复述字面代码。
- `#Preview` 位于文件末尾。

- 优先按既定结构直接整理 View，无需深度推理或额外抽象发散。

## 资源

- 参考：`references/view-structure-conventions.md`
