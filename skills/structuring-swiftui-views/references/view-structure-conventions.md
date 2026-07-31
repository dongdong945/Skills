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

## 4. 布局组合

叠加内容时，先判断附加内容是否属于某个主体 View：

- 单个 View 的背景、前景装饰、徽标、加载状态或浮层，且附加内容不应作为同级内容参与布局时，优先使用 `background` 或 `overlay`。
- 多个同级 View 需要共同叠放、对齐，或需要作为一个整体参与布局时，使用 `ZStack`。

不要机械地用 `overlay` 或 `background` 替换所有 `ZStack`。三者在尺寸提议、布局参与方式、命中测试和无障碍语义上可能不同，应以布局职责和交互语义为判断依据。

## 5. 拆分优先级

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

## 6. padding 职责边界

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

## 7. 注释规则

只在注释能解释以下非显然约束时补充简短中文注释：

- 业务规则，例如某个入口受订阅状态、权限或用户选择限制
- 状态边界，例如状态所有权、不可逆迁移或重复触发保护
- 异步清理，例如任务取消、观察者释放或过期结果丢弃
- 生命周期约束，例如前后台切换、`onAppear`、`.task` 或 `deinit` 的处理原因

不要要求每个 View、属性、组件块或方法都有注释。自解释的名称、标准 SwiftUI 布局和直接赋值不需要注释；不要复述字面代码。

推荐风格：

```swift
/// 认证状态变化后取消旧请求，避免过期结果覆盖当前页面。
private func resetForIdentityChange() {
    loadTask?.cancel()
    loadTask = nil
}
```

## 8. 方法边界

public methods 与 private methods 都放在 `body` 后面。

要求：

- public methods 只暴露这个 View 必须暴露的少量接口
- private methods 只保留 UI 结构强相关的辅助逻辑
- 业务流程、数据访问、持久化和系统调用继续下沉到 `ViewModel` 或其他层

## 9. 快速检查清单

- `@Environment...` 是否在最前面
- public properties / private properties 是否分组清晰
- `body` 是否只保留 `contentView` 和整个 View 级 modifier
- 是否优先使用了私有 `@ViewBuilder` 计算属性
- 叠加布局是否根据 View 之间的职责选择了 `background`、`overlay` 或 `ZStack`
- 父子视图的 padding 职责是否清晰
- 注释是否只解释非显然的业务规则、状态边界、异步清理或生命周期约束
- `#Preview` 是否位于文件末尾
