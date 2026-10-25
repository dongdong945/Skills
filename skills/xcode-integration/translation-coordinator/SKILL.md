---
name: translation-coordinator
description: "协调 Xcode 工程本地化：按 target 与实际资源格式处理 String Catalog、.strings、.stringsdict 和 InfoPlist.strings，收集待译键、划分批次并分层验收；逐条翻译使用 translation。"
metadata:
  source: "Apple Xcode 27.1 (27A9275)"
---

## Codex 运行适配

本技能来自 Apple Xcode 27.1（27A9275）。按项目实际 SDK 和部署版本使用技术指导；用户及项目约定优先。

- 工具名称、参数、返回值和调用前置条件以当前暴露的 Xcode MCP 协议为准；仅执行任务需要的验证。能力缺失时说明受影响的步骤。
- 原文中的 `Read`、`AskUserQuestion`、`TaskCreate`、`TaskGet`、`TaskList` 和 `TaskUpdate` 表示宿主的读取、提问及进度管理接口。使用当前可用的对应能力；无专用任务接口时用本地清单记录，不因接口名称不同停止任务。
- 用户已给出的授权持续有效。先完成已授权且可独立进行的分析和准备；需要新授权时，提供具体可评审的结果再询问。

## 本地名称与工具契约

工具说明中的 `xcode-integration:translation-coordinator` 对应本文件，`xcode-integration:translation` 对应 [translation](../translation/SKILL.md)。调用要求激活这些名称时，先读取对应文件。

当前 `LocalizationPlanner` 从 `changesMade` 提供目录和变更信息；按实际结果识别 String Catalog 路径，不依赖旧版 `stringCatalogPaths` 字段。工具返回的建议不自动授权额外迁移。

# Localization Coordinator

Orchestrate localization by target and resource format, collecting untranslated strings and completing bounded translation batches. Access `.xcstrings` **only** through the String Catalog tools below—never read or write those files directly. Translate traditional resources with authorized file tools, preserving their format.
Prepare the project and exact translation batches first. Load the sibling `translation` skill before translating a batch, whether executing directly or delegating.

## Resource Routing

先确认请求涉及的 target、Bundle、source locale、明确的目标 locale、资源路径和实际格式；检查 target membership、构建资源配置及项目已有的语言选择/Bundle 查找方式。不能因工程中存在一个 `.xcstrings`，就把全部 target 当作 Catalog 工程。

| 资源 | 执行路径 |
|------|----------|
| `.xcstrings` | 使用当前 Xcode MCP 的 `StringCatalogRead` / `StringCatalogContext` / `StringCatalogEdit`；工具不可用时仅阻塞这些 Catalog 的处理 |
| `<locale>.lproj/*.strings`（含 `InfoPlist.strings`）、`.stringsdict` | 使用获准文件工具和项目已有检查；读取 source 与目标语言的对应文件，按键收集缺译/待复查项，保留原格式、编码和现有组织 |
| 混合工程 | 为各 target、格式、文件和 locale 分别建批次；例如主 App 的传统资源与 Widget 的 Catalog 各走对应路径 |

新增语言也先按此表路由。传统资源可按现有 `.lproj` 和工程资源配置补齐目标语言文件，不自动迁移为 Catalog，不为处理旧 `.strings` 调用会创建 Catalog 的 `LocalizationPlanner`。若项目配置修改缺少可用工具，继续不依赖该修改的翻译，并单列接入缺口。

## Quick Reference

| Tool | Purpose |
|------|---------|
| `LocalizationPlanner` | Prepare project for new language (creates String Catalogs, adds locale) or other localization changes |
| `StringCatalogRead` | Get string keys by translation state (new, needs_review, translated, machine_translated) |

## Workflow

### 1. Prepare the Project (Optional)

仅在 Catalog 路径确需准备工程或新增语言、且其影响范围符合本次授权时调用 `LocalizationPlanner`。先确认其可能修改的容器；该工具会创建 Catalog，不能因整项目/功能翻译请求而无条件调用。混合工程中若当前协议无法将准备限制到适用的 Catalog 容器，保留传统资源，跳过该 Planner；已有 Catalog 的可执行翻译仍继续。迁移属于额外范围，工具建议不构成授权。

If Catalog preparation requires a build to extract strings, use the project's authorized Xcode MCP build capability. If unavailable, record the extraction gap; continue work whose keys and source values are already available.

### 2. Select Relevant Resources

Select resources by the requested targets/features and locales, using Resource Routing above. 对传统资源核对源语言与目标语言文件、表名、已有复数条目和权限说明键；不要把源文案相同但属于不同 target/表的键混为一条。不要照搬其他项目的语言矩阵或复数结构。

### 3. Get Strings to Translate

If the prompt already contains per-locale key lists, skip this step, as you have already been given the keys and languages to translate.
Otherwise, for `.xcstrings`, call `StringCatalogRead` with the file path, target locale, and `requestedState: "new"`. You can also request `"needs_review"` or `"machine_translated"` states to improve existing translations. For traditional resources, compare the requested source and target tables with format-appropriate parsing and existing checks, and collect missing, empty or explicitly requested review keys. Do not infer completeness from a fallback lookup.

For Catalog results, if `totalForRequestedState` exceeds the number of returned keys, paginate by increasing `offset` until you have collected all keys. Collect all requested keys before moving to step 4.

Preserve each resource's exact keys when editing or delegating; include its target, table/file and locale so identical keys in different resources remain distinct.

### 4. Translate bounded batches

1. Split the complete collected keys into batches of at most 15 strings. Put app-name keys such as `CFBundleDisplayName` and `CFBundleName` first so later batches can reuse the terminology.
2. Load [translation](../translation/SKILL.md) before translating. A tool requirement naming `xcode-integration:translation` refers to that same local skill. Provide the exact target locale, target/Bundle, workspace identifier, resource format, source and target file/table paths, key list, and the user's terminology/style instructions.
3. Execute batches sequentially in the current agent by default. Delegate only when authorized and supported; never exceed the available agent slots or 5 workers, whichever is smaller. Each worker owns a disjoint batch and must not spawn more workers. Traditional resource files need a single writer per file; disjoint keys do not make concurrent file rewrites safe.
4. Skip `LocalizationPlanner` inside translation batches. Preserve keys and use escaping appropriate to the resource and transport format. Explicit user style instructions take precedence over existing translations; both take precedence over the locale style guide for conflicts, while the guide still supplies uncovered defaults.
5. Complete every batch before verification. Do not broaden the key list or target locale during batch execution.

### 5. Verify Results

按本次 target、locale、文件与键的范围验收，分别报告以下层次；小范围翻译不强加全语言、全设备矩阵：

1. **资源与源码检查**：Catalog 用 `StringCatalogRead` 复核请求键及各变体状态；传统资源用相应语法/编码解析和项目已有检查。核对缺键、空译、重复键、参数位置/类型、复数引用与适用分支，以及实际 target 所需权限说明。字典解析可能吞掉重复键，需在原文件或能保留重复项的解析结果中另查。检查脚本的覆盖范围，不把某项目固定语言数、表结构或输出 schema 当作通用要求。
2. **Bundle 查找**：有可用的构建/测试能力且本次变更需要时，验证目标 target 的构建产物包含所需语言资源。读取目标语言自身文件，并对请求键使用明确的语言 Bundle/table 与独特的缺失哨兵值；不能只检查返回值非空，否则 source/system fallback 可能掩盖缺译。复数和格式串覆盖与改动有关的代表值；复用项目已有语言解析，不自行更改 locale 映射。
3. **页面与外部显示**：按改动范围抽查语言切换、动态 `String`/插值、Toast、Alert、邮件标题/正文及权限说明等实际调用路径，区分 UI 本地化键与运行时普通字符串。系统权限弹窗、邮件客户端等需实际显示证据，资源存在或替身回调不算外部显示通过。

构建、测试、Preview 和设备交互遵守项目工具约束。缺少能力时仅标记受影响层及 target/locale/页面；已完成的资源翻译继续交付，不能宣称全部设备、全部页面或外部系统已验收。


# Tool Reference

## LocalizationPlanner

Prepares Catalog containers for localization when Resource Routing and the preparation scope above permit it. It is not a prerequisite for traditional resource translation or every project/feature translation request.

### What It Does

1. Adds target language to all localizable containers (projects, packages)
2. Prepares the project for translation by creating String Catalogs as necessary

### Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspaceIdentifier` | String | No | Workspace identifier or absolute workspace/project path |
| `targetLocaleIdentifier` | String | Yes | Locale identifier (e.g., `de`, `pt-PT`) |

### Outputs

| Field | Type | Description |
|-------|------|-------------|
| `nextStep` | String | What to do next (e.g. "ready for translation") |
| `stepsFailed` | String? | Failed steps requiring manual intervention |
| `changesMade` | String? | Changes made, including catalog paths when returned by the current tool |
| `suggestions` | String? | Non-blocking suggestions the user may want to follow (e.g., migrate `.strings` to String Catalogs) |

Apply `nextStep` only within the requested scope and available project tools; it does not authorize resource migration or changes to unrelated targets.

---

## StringCatalogRead

Returns string keys grouped by translation state for the requested locale. Includes counts of all string keys grouped by translation state. Supports pagination. Curly apostrophes and quotes are escaped (e.g., \\u2019 for curly apostrophe, \\u201C for curly quote).

### Inputs

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `workspaceIdentifier` | String | No | — | Workspace identifier or absolute workspace/project path |
| `filePath` | String | Yes | — | Path to String Catalog (relative or absolute) |
| `targetLocaleIdentifier` | String | Yes | — | Locale to check translations for (e.g., `de`, `pt-PT`) |
| `requestedState` | String? | No | nil | State to retrieve: `new`, `needs_review`, `translated`, `machine_translated`. If omitted, only counts for all states are returned. |
| `keyLimit` | Int | No | 50 | Maximum keys to return |
| `offset` | Int | No | 0 | Keys to skip (for pagination) |

### Outputs

**Always returned:**

| Field | Type | Description |
|-------|------|-------------|
| `newCount` | Int | Untranslated strings |
| `needsReviewCount` | Int | Strings marked needs review |
| `translatedCount` | Int | Human-translated strings |
| `machineTranslatedCount` | Int | Machine-translated strings |

**When `requestedState` is provided:**

| Field | Type | Description |
|-------|------|-------------|
| `requestedState` | String | The requested state bucket |
| `totalForRequestedState` | Int | Total keys in state bucket before pagination |
| `returnedCount` | Int | Keys returned after pagination |
| `keys` | [String] | Array of string keys |

A key can appear in multiple state buckets if variants have different states.

---

# Critical Rules

1. **Load `translation` for each bounded batch**. Translate sequentially or delegate only when authorized and supported.
2. **Use only String Catalog tools** to access .xcstrings files. Never read or write them directly.
3. **Complete the entire task**—continue until all requested strings are translated.
4. **Match escaping to the format**. Catalog tool parameters follow their current protocol: use literal text rather than HTML/XML entities, and preserve required transport escaping. This rule applies to `.xcstrings`, not XML `.stringsdict`. Traditional resources follow the format-specific workflow in `translation`; XML plist text needs XML escaping, while `.strings` needs its own quoted-string syntax and existing encoding.
5. Do NOT skip strings to save time, even when there are hundreds of strings. Don't skip work or cut corners to save time—rather, focus on accuracy and completeness.
6. Forward keys into sub-agents **exactly** as you have received them from the StringCatalogRead tool. Escaped strings with \\uXXXX sequences might lose one level of escaping during transit. Keep them double-escaped them so the sub-agent receives the original form.
7. **Locale identifiers:** If the user provides an explicit locale code, pass it through verbatim to tool calls and to sub-agents — do not normalize, canonicalize, or swap separators (e.g., if told `pt_BR`, use `pt_BR`; if told `zh-TW`, use `zh-TW`). If the user only names a language/region in prose (e.g., "Brazilian Portuguese", "Traditional Chinese"), derive a BCP 47 identifier with hyphens (`pt-BR`, `zh-Hant`) rather than underscores. The explicit-code rule always wins over the BCP 47 default.

### Examples

#### Catalog Target

1. User requests translating a Catalog target into Japanese.
2. Agent checks preparation scope, then calls `LocalizationPlanner` only if needed and permitted by Resource Routing.
3. Agent reviews the returned String Catalog paths and selects only those relevant to the user's request.
4. Agent uses `StringCatalogRead` on the relevant String Catalogs to understand what string keys need translating.
5. Agent prepares bounded batches and uses the following instructions directly, or forwards them to authorized workers:

============
Translate the strings for the following keys into Japanese (ja). Skip running the `LocalizationPlanner` tool. Do NOT spawn further sub-agents. Translate only the keys listed below. Use the `translation` Skill.

IMPORTANT: Use the keys EXACTLY as written below, including all escaping. You must preserve this escaping exactly when passing the key to StringCatalogContext and StringCatalogEdit.

- Workspace identifier: <workspaceIdentifier>
- String Catalog: path/to/string/catalog.xcstrings
- Keys:

```
key1
```

```
key2
```

```
key3
```
============

6. Once all translation batches have completed, agent uses `StringCatalogRead` to verify that each requested string has received a translation.

#### Specific Strings

1. User requests translation of specific strings in a specific String Catalog into Japanese.
2. Agent skips `LocalizationPlanner` and `StringCatalogRead` since the user already specified which strings to translate.
3. Agent prepares bounded translation batches, prompting each with the following: 

============
Translate the strings for the following keys into Japanese (ja). Skip running the `LocalizationPlanner` tool. Do NOT spawn further sub-agents. Translate only the keys listed below. Use the `translation` Skill.

IMPORTANT: Use the keys EXACTLY as written below, including all escaping. You must preserve this escaping exactly when passing the key to StringCatalogContext and StringCatalogEdit.

- Workspace identifier: <workspaceIdentifier>
- String Catalog: path/to/string/catalog.xcstrings
- Keys:

```
key1
```

```
key2
```

```
key3
```
============

4. Once all translation batches have completed, agent uses `StringCatalogRead` to verify that each requested string has received a translation.

#### Mixed Project

主 App 使用 `<locale>.lproj/Localizable.strings`、`Localizable.stringsdict`、`InfoPlist.strings`，Widget 使用 `.xcstrings`：分别收集两 target 的请求键，主 App 用文件路径完成翻译及语法检查，Widget 用 Catalog 工具完成翻译及状态复核。不为主 App 调用 Planner，也不把 Widget Catalog 的完成状态当作主 App 完成证据。最后按实际可用能力分别报告资源、Bundle 与页面验证结果。
