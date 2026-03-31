---
name: structuring-swiftui-views
description: Use when 编写、重构或审查 SwiftUI `View` 文件，需要统一 `@Environment`、属性、`body`、方法与 `#Preview` 的顺序，约束 `body` 的拆分方式，并统一注释与父子视图 padding 职责边界。
---

# Structuring SwiftUI Views

先读取 `references/view-structure-conventions.md`，再开始写代码或 review。

## 执行步骤

1. 先确认当前文件是 SwiftUI `View`、页面内私有子视图或可复用组件；不是就不要套用这套规则。
2. 按固定顺序组织文件：`@Environment...` -> public properties -> private properties -> `body` -> public methods -> private methods -> `#Preview`。
3. 让 `body` 优先只保留 `contentView` 与整个 View 级别的 modifier；不要把布局细节、分支和零散组件直接堆在 `body` 里。
4. 拆分 `body` 时，优先提取成私有 `@ViewBuilder` 计算属性；只有在需要参数、复用局部输入或表达更自然时，再用私有 `@ViewBuilder` 函数。
5. 让每个组件负责自己的内部 UI 和内部 padding；父视图只负责多个子视图之间的间距、外层排布和容器级 padding。
6. 为 View 本身、每个属性、每个组件、每个方法补简短中文注释，只说明职责或意图，不复述字面代码。
7. 把业务流程、数据访问、持久化和系统调用下沉到 `ViewModel` 或其他层；`View` 只保留展示状态、转发用户意图和纯 UI 逻辑。

## 快速检查

- `@Environment...` 永远放在最前面，不和普通属性交错。
- public properties 与 private properties 分开，不要混排。
- `body` 中优先保留 `contentView`，以及属于整个 View 的 modifier。
- 私有 `@ViewBuilder` 计算属性优先于私有 `@ViewBuilder` 函数。
- 子组件负责内部 padding，父视图负责子视图之间的 spacing 和外层 padding。
- View、属性、组件、方法都要有简短中文注释。
- 公共子视图提取到公共组件文件，不要长期留在页面文件内部。

## 参考

- 完整约定：`references/view-structure-conventions.md`
