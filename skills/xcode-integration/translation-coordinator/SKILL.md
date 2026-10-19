---
name: translation-coordinator
description: "协调 Xcode String Catalog 本地化：新增语言、翻译工程或功能、收集待译键、划分翻译批次并验收结果；具体逐条翻译使用 translation。"
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

Orchestrate the translation of an Xcode project by preparing it, fetching untranslated strings, and completing bounded translation batches. Access String Catalogs **only** through the tools below—never write .xcstrings files directly.
Prepare the project and exact translation batches first. Load the sibling `translation` skill before translating a batch, whether executing directly or delegating.

## Quick Reference

| Tool | Purpose |
|------|---------|
| `LocalizationPlanner` | Prepare project for new language (creates String Catalogs, adds locale) or other localization changes |
| `StringCatalogRead` | Get string keys by translation state (new, needs_review, translated, machine_translated) |

## Workflow

### 1. Prepare the Project (Optional)

Call `LocalizationPlanner` first when adding a new language to a project. Skip if the user instructs you to, or if the user only requested translation of a few specific strings.

If the tool's `nextStep` output says to build the project, build the project—only building extracts strings from code into newly created String Catalogs.

### 2. Select Relevant String Catalogs

Identify all String Catalogs relevant to the user's request. If the user's request is very broad, all catalogs may be relevant.

### 3. Get Strings to Translate

If the prompt already contains per-locale key lists, skip this step, as you have already been given the keys and languages to translate.
Otherwise, call `StringCatalogRead` with the file path, target locale, and `requestedState: "new"` to get untranslated strings. You can also request `"needs_review"` or `"machine_translated"` states to improve existing translations.

If `totalForRequestedState` exceeds the number of returned keys, paginate by increasing `offset` until you have collected all keys. Collect all keys before moving to step 4.

The keys are unique identifiers to strings in this String Catalog. Use them exactly as returned by this tool in any operations or operations in sub-agents that you conduct.

### 4. Translate bounded batches

1. Split the complete collected keys into batches of at most 15 strings. Put app-name keys such as `CFBundleDisplayName` and `CFBundleName` first so later batches can reuse the terminology.
2. Load [translation](../translation/SKILL.md) before translating. A tool requirement naming `xcode-integration:translation` refers to that same local skill. Provide the exact target locale, workspace identifier, catalog path, key list, and the user's terminology/style instructions.
3. Execute batches sequentially in the current agent by default. Delegate only when authorized and supported; never exceed the available agent slots or 5 workers, whichever is smaller. Each worker owns a disjoint batch and must not spawn more workers.
4. Skip `LocalizationPlanner` inside translation batches. Preserve keys and all escaping verbatim. Explicit user style instructions take precedence over existing translations; both take precedence over the locale style guide for conflicts, while the guide still supplies uncovered defaults.
5. Complete every batch before verification. Do not broaden the key list or target locale during batch execution.

### 5. Verify Results

Once all translation batches have completed, use the `StringCatalogRead` tool to verify the strings you requested to translate are translated. 


# Tool Reference

## LocalizationPlanner

Prepares an Xcode project for localization. **Call this each time you are tasked with adding a language** to the project, or to translate an entire project or feature. It is ok to skip this tool if requested explicitly.

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

Follow the instructions in the `nextStep` field.

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
4. **Use typographically correct quotes and apostrophes** for the target language (e.g., „...“ for German, «...» for French). All curly quotes must be escaped (e.g., \\u201E...\\u201C for German „...“), as well as apostrophes (e.g. \\u2019 for curly apostrophe). NEVER XML-escape the ampersand: write a literal `&`, NOT `&amp;`. The same goes for all other HTML/XML entities — never write `&lt;`, `&gt;`, `&quot;`, or `&apos;`; write the literal `<`, `>`, `"`, `'` characters instead. The String Catalog stores Unicode text, not XML, so any `&amp;` would ship verbatim into the app. Other non-ascii characters do not need extra escaping either. 
5. Do NOT skip strings to save time, even when there are hundreds of strings. Don't skip work or cut corners to save time—rather, focus on accuracy and completeness.
6. Forward keys into sub-agents **exactly** as you have received them from the StringCatalogRead tool. Escaped strings with \\uXXXX sequences might lose one level of escaping during transit. Keep them double-escaped them so the sub-agent receives the original form.
7. **Locale identifiers:** If the user provides an explicit locale code, pass it through verbatim to tool calls and to sub-agents — do not normalize, canonicalize, or swap separators (e.g., if told `pt_BR`, use `pt_BR`; if told `zh-TW`, use `zh-TW`). If the user only names a language/region in prose (e.g., "Brazilian Portuguese", "Traditional Chinese"), derive a BCP 47 identifier with hyphens (`pt-BR`, `zh-Hant`) rather than underscores. The explicit-code rule always wins over the BCP 47 default.

### Examples

#### Entire Project

1. User requests translating the project into Japanese
2. Agent calls `LocalizationPlanner` tool. Once completed, the project is ready for localization.
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
