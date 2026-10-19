# Xcode 内置技能来源

- 来源：Apple Xcode 27.1，构建号 27A9275；导出日期：2026-10-19。
- 使用官方命令 `xcrun agent plugin path --plugin-format codex` 生成完整插件，再复制其中的 `skills/`；共 15 项。
- `xcrun agent skills export --output-dir <新目录>` 在此版本只导出 10 项 portable skills，缺少翻译协调、翻译和三项无障碍技能，因此没有作为完整来源。
- 安装位置为本目录；现有 `~/.codex/skills/workspace-skills` 软链接覆盖其上级 `skills/`，无需新增或修改软链接。

## Codex 适配范围

- 保留官方技能名、技术指导、参考资料和安全审计脚本；`modernize-tests` 为官方导出的准确名称。
- 将描述缩短为中文触发说明，移除 Codex 校验器不支持的 Xcode UI 元数据；C 边界安全的 when_to_use 移入正文。
- 修复翻译参考资料中复数与设备差异文档的两个相对链接。
- 用当前宿主接口解释原文的提问和任务工具；保留用户及项目指令的优先级。
- 本地化文档使用当前工具的 workspaceIdentifier 参数；明确两个 xcode-integration 命名空间别名与本地技能文件的对应关系。
- 设备交互采用当前 DeviceInteractionSynthesize 名称，明确会话键、清理和最新层级坐标要求；设备检查与翻译批次支持主代理直接执行，不强制创建子代理。
- 安全审计先形成可评审计划再取得尚未提供的实际变更授权；构建设置通过 MCP 核对，移除直接解析 project.pbxproj 的验证方式。
- C 边界安全迁移不通过 shell 绕过 Xcode MCP 的构建或设置能力限制。

## 更新方式

升级 Xcode 后重新运行官方插件导出命令，比较导出的完整技能目录与本地版本，再重放上述兼容适配。不要直接覆盖本目录，否则会丢失兼容修正。

## 官方导出入口的 SHA-256

| Skill | SHA-256 |
|---|---|
| `accessibility-dynamic-type-specialist` | `50eef76bb30334207e37ab6f637dd5d9a5f3a4c691e4a983356d046b8dc6f788` |
| `accessibility-sufficient-contrast-specialist` | `3992214215d77b5d04e0bd0e4d9c685a2315ce35844a456a9c33f5740e6758c9` |
| `accessibility-voiceover-specialist` | `d395d53a018b034d80dd4b8d5214fda3dae5b5b01536b26d61c207841f4301f6` |
| `adopt-c-bounds-safety` | `03a574322440e1ce4f45634e402147bf69316d3faa06825a9641d1d0f9ace3ec` |
| `app-intents-specialist` | `2fc4d82086fa888bca4a71e2d1b23374c1778f58817b163f4176906d8102627e` |
| `app-intents-whats-new-27` | `15660e2a7db3f480c3dce9375ff5e6cf850752e4c4fac38d28b58c3b6455be50` |
| `app-resizability` | `1b16afdc3702c1ab843ff8ca5c629d7fc2aaf01079852336cb150b4fe16cfdf2` |
| `audit-xcode-security-settings` | `96bb69548c26e3d3772e4daabe70cefb8d670ff3111dbbbe547df6bbdcbd1786` |
| `building-document-based-swiftui-applications` | `f6a7567b32ff182268f91d76ae3e484c5b8b07192967d60930614df89c386f8d` |
| `device-interaction` | `584d29b72201066f2acca85de958eb477d4f25e87e5c795d4ba870625f6173bc` |
| `modernize-tests` | `880f46b4b39ca7d895f78857230e0082c299d481f74461ee977cd14f3315cfb3` |
| `swiftui-specialist` | `0ef5b3a2a95f43714b4e5e7a07a987341c966911cd9da01bcfbca8041277715f` |
| `swiftui-whats-new-27` | `92f352f8a1570bc3252e0144525a284c4795425265bec720f0a22e5791f58ed7` |
| `translation` | `f62f448da4a6d32acd36c338feb0376c0011e4545a398951b4a592c08665ad1a` |
| `translation-coordinator` | `cc360a0a5a820d2a916af3863891242cf03b0c93814f6c2a43f2b520fe52bc45` |
