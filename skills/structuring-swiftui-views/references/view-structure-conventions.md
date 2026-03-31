# View 结构约定

本文档定义通用 SwiftUI `View` 的内部组织顺序、`body` 拆分方式、注释要求与 padding 职责边界。

## 1. 适用范围

适用于大多数 SwiftUI `View` 文件，包括：

- 页面级 View
- 页面内部私有子视图
- 可复用组件

不适用于：

- 纯 UIKit 类型
- 只包含极少量代码且无需长期维护的临时调试视图

## 2. 固定顺序

`View` 文件按以下顺序组织：

1. `@Environment...`
2. public properties
3. private properties
4. `body`
5. public methods
6. private methods
7. `#Preview`

要求：

- `@Environment`、`@EnvironmentObject`、`@ScaledMetric` 等环境相关属性放在最前面。
- public properties 与 private properties 分开组织，不要混排。
- `#Preview` 永远放在整个文件最后。

## 3. body 约定

`body` 只负责表达整个 View 的主结构。

优先形式：

```swift
var body: some View {
    contentView
        .modifierForWholeView()
}
```

要求：

- 优先让 `body` 只保留 `contentView`。
- 属于整个 View 的 modifier，例如外层 `padding`、`background`、`navigationTitle`、`task`、`onAppear`，保留在 `body`。
- 不要把多个区块、复杂条件分支和零散布局细节直接堆在 `body`。
- 如果 `body` 只有一个非常简单的元素，可直接返回，不强制引入 `contentView`。

## 4. 拆分优先级

当 `body` 或某个区块开始变复杂时，按以下优先级拆分：

1. 私有 `@ViewBuilder` 计算属性
2. 私有 `@ViewBuilder` 函数

优先使用计算属性的场景：

- 不需要额外入参
- 语义上是当前 View 的固定组成部分
- 适合作为 `contentView`、`headerView`、`actionSection` 这类命名区块

改用 `@ViewBuilder` 函数的场景：

- 需要显式入参
- 同一结构要根据输入生成多个变体
- 用函数表达比复制多个近似计算属性更自然

不要做的事：

- 为了“拆而拆”把每个 `Text`、`Image`、`Button` 都提成独立块
- 同时提供一个计算属性版本和一个函数版本来表达同一段 UI

## 5. padding 职责边界

布局职责按层次划分：

- 每个组件负责自己的内部 UI 和内部 padding
- 父视图负责子视图之间的 spacing
- 父视图负责容器级 padding 和整体排布

示例理解：

- `CardView` 内部标题、按钮、背景和内部边距，由 `CardView` 自己负责
- 多个 `CardView` 之间的垂直间距，由父级 `VStack` 负责
- 整页左右边距，由页面容器负责

避免：

- 子组件和父视图同时给同一层内容加外边距
- 父视图侵入子组件内部结构去补局部 padding

## 6. 注释规则

以下对象都要补简短中文注释：

- View 本身
- 每个属性
- 每个组件块
- 每个方法

要求：

- 注释说明职责、意图或边界
- 保持简短，一般一行即可
- 不要复述字面代码，例如“设置标题文本”

推荐风格：

```swift
/// 用户资料页，负责展示基础信息与操作入口。
struct ProfileView: View {
    /// 路由能力，用于处理页面跳转。
    @Environment(AppRouter.self) private var router

    /// 页面标题。
    let title: String

    /// 控制编辑弹窗是否展示。
    @State private var isEditing = false

    var body: some View {
        contentView
            .navigationTitle(title)
    }

    /// 页面主体内容。
    @ViewBuilder
    private var contentView: some View {
        VStack(spacing: 16) {
            profileHeader
            actionSection
        }
        .padding(.horizontal, 20)
    }

    /// 处理编辑按钮点击。
    private func handleEditTapped() {
        isEditing = true
    }
}
```

## 7. 方法边界

public methods 与 private methods 都放在 `body` 后面。

要求：

- public methods 只暴露这个 View 必须暴露的少量接口
- private methods 只保留 UI 结构强相关的辅助逻辑
- 业务流程、数据访问、持久化和系统调用继续下沉到 `ViewModel` 或其他层

## 8. 快速检查清单

- `@Environment...` 是否在最前面
- public properties / private properties 是否分组清晰
- `body` 是否只保留 `contentView` 和整个 View 级 modifier
- 是否优先使用了私有 `@ViewBuilder` 计算属性
- 父子视图的 padding 职责是否清晰
- View、属性、组件、方法是否都有简短中文注释
- `#Preview` 是否位于文件末尾
