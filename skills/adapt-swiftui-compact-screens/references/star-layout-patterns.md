# STAR 判断与布局模式

用于 STAR 系列现有竖屏、全屏 iPhone 页面。其他项目先查自己的设计基准和容器契约，不能把这些取值当作平台规范。

## 根容器分类

STAR 当前约定是根容器 **可用高度不超过 700pt** 时使用紧凑布局。统一阈值来源；同一展示页的子树复用结果，避免在扣除底栏后的局部 GeometryReader 重新判断。复用已有 Environment、参数或展示上下文即可，不为此强制新增全局状态。

STAR301 的落点示例：

```swift
GeometryReader { proxy in
    FlowPageTransitionContainer(/* existing arguments */) {
        // Existing production pages.
    }
    .environment(\.isCompactFlowLayout, proxy.size.height <= 700)
}
```

这是测量位置示意，不是可复制编译的组件。实际入口、安全区扣除和转场 proposal 需查当前代码。375×667 的屏幕高度也不等于 667pt 可用正文高度。iPhone 12 的子视图即使只剩 650pt，也不应因此覆盖根层的常规分类。

700pt 不适用于任意高度 Sheet、键盘抬升区、iPad 或横屏。转场临时改变 proposal、但页面不应中途切换构图时，可让分类在本次展示周期稳定；不要持久化设备布局类别。

Duo 的短高度和较大总宽度不能直接代表内容预算。先按项目的区域容器确定实际无阻挡可读区域，再使用其中的宽高布局；折叠、展开或窗口实际改变尺寸时重新计算，保留同一页面的输入与进度，不把转场期间的临时分类锁定延续到真实窗口变化。端点截图只证明对应姿态的渲染，状态保持需要连续操作验证。

## 正文、底栏与导航

选择方案取决于实际几何与页面设计：

| 结构 | 适用情况 | 必须检查 |
| --- | --- | --- |
| 既有 bottom safeAreaInset | 父级确实为底栏分配空间的普通页面 | 正文末项与按钮不重叠；背景覆盖底栏的完整区域 |
| 正文与底栏同级 VStack | 自定义 Flow 中 inset 未形成预期正文视口 | 标题起点、剩余高度、转场和参考设备回归 |
| 渐变 overlay 加内容底部留白 | 设计或用户明确要求底栏覆盖正文 | 留白容纳底栏、渐变及所需安全区；末项滚到底可完整看到并点击 |

不要用整页 ignoresSafeArea 修复背景。让背景独立铺满；前景继承项目的安全区管理。导航栏已经管理顶部 inset 时，不再加一次 safeTop 或 44pt。

有固定标题的选择页应让选项滚动；固定页头、滚动主体、固定操作区三者职责清楚。导航底色使用项目已有 config，并考虑某些子页自带标题条；盲目套父级不透明层可能把子页标题盖住。长汇总页的整页滚动是合理例外。

## 图片与空间预算

先比较图片可见内容、透明留白、绘制溢出与容器边界。资源 frame 对齐不代表主视觉对齐；缩小了 frame 后图片偏上，也可能是背景 fit/fill 和锚点改变，不能只继续调负 padding。

装饰背景按项目已有背景机制调整构图，必要时 fill 后裁切；含文字、用户照片、图表的内容图保护完整信息。含透明开孔、描边或扫描环的组合图需核对前后层是否仍对齐。

适配取值按页面剩余高度推导，不复制其他页面的插图高度、偏移量或底部 padding。STAR301 曾压缩插图后仍需独立下移介绍页背景，说明“没有重叠”与“构图正确”需分别核对。

## 可追溯来源

以下是已验证模式的来源线索，不是要求下次直接修改同名文件。实际路径、实现及证据需重新读取。

- STAR301，提交 `956b616`、`5cc4343` 的历史记录现位于 `output/verification/legacy-docs/OnboardingComparison/audit.md`、`Docs/Plans/Onboarding-Design-Changes.md`；前者是本地归档，后者保留 iPhone 12 / SE3 对比、交互及证据边界。归档缺失时先查持久文档或对应历史提交，不把无法读取的截图视为已复核。
- STAR301：`App/Presentation/Features/Onboarding/Views/OnboardingFlowView.swift` 的根层分类；`Components/OnboardingContinueButton.swift` 的正文/底栏分配；`Views/StepViews/OnboardingHuntObjectsView.swift` 的渐变覆盖方案。后两条相对同一个 Onboarding 目录。
- STAR301：`Docs/Plans/Verification/Settings-2026-10-23.md`、`Mission-Implementation-2026-10-23.md` 分别记录文字与开关占宽、正文错误层的返回可达性；后者相对同一个 Verification 目录。
- STAR301：`Docs/Plans/Verification/Insights-UI-Self-Review-2026-10-24.md`、`PreQA-Fixes-2026-10-25.md` 分别记录临时宿主缺少正式区域约束、有效滚动视口与局部手势锚定；后者相对同一个 Verification 目录。`Docs/Plans/iPhone-Duo-Adaptation.md` 记录实际可读区域与动态窗口方案，其旧采样范围不代表当前完整验收。
- STAR112：`App/Presentation/Features/Onboarding/Components/OnboardingQuestionChoiceComponents.swift` 与 `App/Presentation/Features/Onboarding/Views/StepViews/OnboardingPlanCommitmentView.swift`，分别参考选择页滚动和承诺页紧凑布局，读取时确认是否已有更新。
- Obsidian：`wiki/playbooks/STAR-SwiftUI-Compact-Screen-Adaptation.md`、`wiki/concepts/SwiftUI-Safe-Area-Layout.md`，分别说明 STAR 约定与自定义 Flow 的安全区验收边界。知识库不可用时仍可根据当前源码与运行证据完成任务。
