---
name: device-interaction
description: "通过 Xcode MCP 在真机或模拟器验证应用 UI 和交互，使用截图、辅助功能层级、点击、滑动、输入及日志定位问题；不用于纯编译、单元测试或无需设备验证的改动。"
metadata:
  source: "Apple Xcode 27.1 (27A9275)"
---

## Codex 运行适配

本技能来自 Apple Xcode 27.1（27A9275）。按项目实际 SDK 和部署版本使用技术指导；用户及项目约定优先。

- 工具名称、参数、返回值和调用前置条件以当前暴露的 Xcode MCP 协议为准；仅执行任务需要的验证。能力缺失时说明受影响的步骤。
- 全局约定或用户已允许截图回退时，MCP 缺少截图能力或返回报错、超时、全黑及无法导出的图片，应通过 Xcode / Device Hub 原生图形界面完成采集，无需重复确认。回退仅包含采集所需的页面定位、设备/姿态选择和图片导出，其他操作权限不变。核对原生界面实际显示，记录失败情况、来源与尺寸；原生界面同样黑屏时保留实际显示问题。使用当前原生界面控制工具的协议与界面状态，不将下面的 MCP 会话或坐标命令套用于原生界面操作。
- 原文中的 `Read`、`AskUserQuestion`、`TaskCreate`、`TaskGet`、`TaskList` 和 `TaskUpdate` 表示宿主的读取、提问及进度管理接口。使用当前可用的对应能力；无专用任务接口时用本地清单记录，不因接口名称不同停止任务。
- 用户已给出的授权持续有效。先完成已授权且可独立进行的分析和准备；需要新授权时，提供具体可评审的结果再询问。

# Device Interaction

TRIGGER when: user asks to verify/test/check if the app works on device, after implementing a UI-affecting feature that needs device verification, user says "does it work", "test this", "check on device", user reports UI doesn't work as expected, need to debug touch/interaction issues.
DO NOT TRIGGER when: user asks about unit tests only, build-only requests without device testing, code review without device testing, simulator configuration questions, changes that don't affect UI (e.g. comments, refactors, non-UI logic).

---

## 执行方式

由当前代理直接执行所需验证。只有用户或适用约定授权且环境支持时才委派子代理；同一设备会话只由一个执行者操作。

`DeviceInteractionStartWorkspaceSession` 和 `DeviceInteractionStartSession` 返回 `interactionSessionKey`。传给 `DeviceInteractionSynthesize` 时参数名为 `interactSessionKey`；安装运行和结束会话使用各自协议中的 `interactionSessionKey`。每次新建会话后，在成功、失败或中断路径都调用 `DeviceInteractionEndSession` 清理本次不再使用的会话。

## Session Lifecycle

```
DeviceInteractionStartWorkspaceSession (workspace-backed; do this early, runs in the background)
  → DeviceInteractionInstallAndRun (after each code change; includes building)
    → DeviceInteractionSynthesize (interact + observe, repeatable)
  → DeviceInteractionEndSession (when done — keeping sessions open is resource-heavy)
```

There are two ways to start a session:
- **DeviceInteractionStartWorkspaceSession** — bound to a workspace. Required for DeviceInteractionInstallAndRun. Use this when verifying the app you are building.
- **DeviceInteractionStartSession** — not bound to any workspace. Use this only when interacting with an already-installed app.

## DeviceInteraction(Workspace)StartSession tools

### Device Discovery

For a workspace-backed session, pass a device identifier to select a device, or omit it when the current tool schema allows the active destination. A standalone session requires its deviceIdentifier parameter. Do not assume an empty string lists devices unless the currently exposed tool documents that behavior.

## DeviceInteractionInstallAndRun tool

### Optional Parameters

- `commandLineArguments` — arguments passed to the app at launch. Use `$(inherited)` as a token to preserve the scheme's existing arguments (e.g. `["$(inherited)", "--reset-state"]` to add an extra argument at the end).
- `environmentVariables` — key/value pairs set in the app's environment at launch. Use `"$(inherited)"` as a key to preserve the scheme's existing environment variables (e.g. `{"$(inherited)": "", "DEBUG_MODE": "1"}`).

Omit both parameters to leave the scheme's arguments and environment unchanged.

**Prefer these parameters over editing the scheme directly.** They are applied only for that one run and have no lasting effect on the user's configuration.

---

# Interaction Checks

**ALWAYS** report UI issues that might be caused by code: overlapping or unreadable text, unexpectedly cropped image/text, wrong colors etc.

## DeviceInteractionSynthesize tool

This tool allows performing an interaction and observing the state of a device.

## Reading Hierarchy Files

The hierarchy files include calculated hitPoint positions for each element:

```
UIView {{100, 200}, {60, 30}}, hitPoint: {130.0, 215.0}
  UIButton "Login" {{110, 205}, {30, 20}}, hitPoint: {125.0, 215.0}
  UIButton "Login2" {{140, 205}, {20, 20}}, hitPoint: {150.0, 215.0}, activationBundleId: com.your.app
```

- `{100, 200}` - origin position
- `{50, 30}` - width and height
- `hitPoint: {125.0, 215.0}` - calculated hitPoint point (best for tapping)

**Always use hitPoint coordinates from the most recent hierarchy for touch events.** If a tap fails, recapture and retry once using the updated hierarchy. Do not estimate positions from screenshots alone.

Elements marked `isRemoteLeafPlaceholder` may not report child elements. Recapture the hierarchy; if a valid target position remains unavailable, report that interaction as unverified.

### Multiple Applications (activationBundleId annotations)

When windows from more than one application overlap on screen, each element line is annotated with a `activationBundleId: <bundle-identifier>` suffix.

If an element line carries a `activationBundleId`, **any interaction with it requires activating that application first** by passing `activationBundleId` parameter to the DeviceInteractionSynthesize tool.

Tip: you can pass `activationBundleId` with no `interactionCommand`.
**Application activation is expensive so use that only if necessary.**

#### Example:

```
Device orientation: Landscape Right
------------------------
Application bundle identifier: com.some.app
Application UI orientation: Landscape Left
Application, pid: 123, label: ' '
 Window, {{0.0, 0.0}, {1133.0, 744.0}}, hitPoint: {566.5, 372.0}
  Other, {{0.0, 0.0}, {744.0, 1133.0}}, hitPoint: {372.0, 372.0}
...
------------------------
Application bundle identifier: com.some.other.app
Application UI orientation: Landscape Left
Application, pid: 333, label: ' '
 Window, {{0.0, 0.0}, {1133.0, 744.0}}, hitPoint: {566.5, 372.0}
...
```

## Interaction Command Syntax

The `interactionCommand` parameter accepts a command syntax:

| Command | Description |
|---|---|
| `t <x> <y> [duration]` | Tap at coordinates with optional hold duration |
| `d <x> <y>` | Double tap |
| `t <x1> <y1> f <x2> <y2> [duration]` | Swipe from (x1,y1) to (x2,y2) |
| `drag <x1> <y1> <x2> <y2> [holdDuration] [moveDuration]` | Drag-and-drop: press-and-hold at (x1,y1) then slowly move to (x2,y2). Use for reordering lists or drag-and-drop targets |
| `mt [x1 y1, ...] dur [x1 y1, ...] dur ...` | Multi-touch sequence. Each `[...]` keyframe lists touch positions (`x y`). The duration after each block is the travel time to the next keyframe; for the last block it is the hold time before lifting. A finger ends when its slot is an empty comma entry (e.g. `[, x y]`) **or** when the frame has fewer entries than the finger's index — both are equivalent. A finger that reappears in a later keyframe after lifting starts a new tap. |
| `b h/p/u/d [duration]` | Hardware button: h=Home, p=Power, u=VolUp, d=VolDown |
| `b c/s/a [duration]` | **watchOS only.** c=Digital Crown press, s=side button, a=Action button (some devices only) |
| `sender keyboard kbd <text>` | Type text; **must be the last command in the chain** — all content after `kbd ` is taken verbatim (multiple spaces preserved). For special characters use `\u{XXXX}` Unicode escapes: `\u{000A}` (return/newline), `\u{0009}` (tab) |
| `w duration` | Wait for a duration without any work |
| `orientation faceDown/faceUp/landscapeLeft/landscapeRight/portrait/portraitUpsideDown` | Set device orientation (iOS only) |
| `c <rotations>` | **watchOS only.** Rotate the Digital Crown; sign sets direction, 1.0 = one full revolution |
| `r up/down/left/right/select/menu/playpause/home` | **tvOS only.** Press a Siri Remote button to move focus, select, or go to the Home screen |

**Examples:**
- `"t 100 200"` - Tap at (100, 200)
- `"d 200 300"` - Double tap at (200, 300)
- `"t 200 600 f 200 200 0.3"` - Swipe up (scroll to the content below)
- `"t 200 200 f 200 600 0.3"` - Swipe down (scroll to the content above)
- `"drag 100 300 100 100"` - Drag-and-drop from (100,300) to (100,100) with default durations
- `"drag 100 300 100 100 0.5 1.5"` - Drag-and-drop with 0.5s hold, 1.5s move
- `"mt [100 200] 0.5 [100 200] 1.0 [300 400] 0.2"` - Drag: hold at (100,200) for 0.5s, move to (300,400) over 1.0s, hold 0.2s then lift
- `"mt [100 300, 300 300] 0.5 [175 300, 225 300] 0.5"` - Two-finger pinch: both fingers start 200px apart and move toward each other
- `"b h"` - Press home button
- `"b h b h"` - Press home button twice to go to the app switcher
- `"b h w 0 b h"` - Wake and unlock a device (non-passcode devices only)
- `"b c"` - watchOS: press the Digital Crown
- `"b s"` - watchOS: press the side button
- `"b a"` - watchOS: press the Action button (some devices only)
- `"sender keyboard kbd hello world"` - Type text with spaces
- `"sender keyboard kbd hello   world"` - Type text preserving multiple spaces
- `"sender keyboard kbd submit\u{000A}"` - Type text then press Return/submit
- `"w 0.3"` - Wait for 0.3s
- `"orientation landscapeLeft"` - Rotate device to landscape
- `"c 1.0"` - watchOS: rotate the Digital Crown one full turn (e.g. scroll a list)
- `"c -0.5"` - watchOS: rotate the crown half a turn the other way
- `"r down"` - tvOS: move focus down
- `"r select"` - tvOS: press Select on the focused element
- `"r home"` - tvOS: go to the Home screen

## Verification Workflow

Before any interaction, always capture and read the hierarchy (and screenshot). After any interaction, capture again and verify the result. For complex components (like toggles or switches), look at nested elements (like `Switch` or `Slider`) — nearby elements might correspond to the actual control. When done, report findings to the user.

- To capture without interacting, use DeviceInteractionSynthesize with an empty interactionCommand.
- Never guess positions from screenshots alone; use the most recent hierarchy hitPoint coordinates.
- If not confident or thumbnail resolution is insufficient, analyze the full-size screenshot.

## tvOS (Apple TV)

tvOS is **focus-based**: there is no touchscreen, so coordinate taps/swipes do not apply. Exactly one element is focused at a time, and you can only activate whatever currently has focus. Drive it with the Siri Remote instead:

- Read the hierarchy to see all focusable elements and which one is marked `Focused`.
- Move focus toward the target with `r up`/`r down`/`r left`/`r right`, then activate it with `r select`. Use `r menu` to go back.
- **Chain multiple presses in one command and capture once**, rather than capturing after every single press. The hierarchy lists element order, so compute how many steps to the target and send them together, e.g. `r right r right r right`, then capture to confirm focus landed.

## Timing and Retries

- **App launch**: After starting a session, the app may take a few seconds to load. Capture the hierarchy and check it has meaningful UI elements before interacting. If the hierarchy is mostly empty or shows a launch screen, capture again before proceeding.
- **After interaction**: If a tap or swipe doesn't produce the expected change, recapture the hierarchy and retry the interaction once (the element may have shifted during an animation). If it still fails after one retry, report the failure rather than retrying indefinitely.
- **Loading states**: If the hierarchy shows a spinner or loading indicator, capture again after a brief pause. Do not interact with elements that are still loading.
- **Performance**: Avoid adding wait delays that might slow down the process. Tools are designed to complete once animations are done.

## Judging Success vs Failure

When verifying, distinguish between these categories:

- **Functional bug** (always report): element doesn't respond to tap, navigation goes to wrong screen, crash, data not displayed, missing expected UI element.
- **Visual/layout bug** (always report): overlapping text, truncated labels, elements rendered off-screen, wrong colors, broken alignment.
- **Transient state** (do NOT report as bug): loading spinners, brief animations, keyboard appearing/dismissing. Capture again after the transition completes.
- **Unexpected exits** (always report): crashes, application exits. To identify, track process id and capture process's standard output.
- **Expected behavior** (do NOT report as bug): empty states with placeholder text, disabled buttons when form is incomplete, permission dialogs.

## Error Handling

- If application is not visible, retry once, as this might be caused by a slow device.
- If tap target unclear, re-read hierarchy data for correct hitPoint coordinates.
- You can inspect runtime logs to troubleshoot. If you suspect timing bugs, explain to the user that temporarily adding `print` statements in the relevant code may help diagnose the issue.
- Report issues to the user with details and suggestions.
