---
name: translation
description: "按明确的 target、locale 和 key 列表翻译 Xcode String Catalog 或传统 .strings、.stringsdict、InfoPlist.strings，结合源码上下文、术语及语言风格处理占位符和复数；整体任务先用 translation-coordinator。"
metadata:
  source: "Apple Xcode 27.1 (27A9275)"
---

## Codex 运行适配

本技能来自 Apple Xcode 27.1（27A9275）。按项目实际 SDK 和部署版本使用技术指导；用户及项目约定优先。

- 工具名称、参数、返回值和调用前置条件以当前暴露的 Xcode MCP 协议为准；仅执行任务需要的验证。能力缺失时说明受影响的步骤。
- 原文中的 `Read`、`AskUserQuestion`、`TaskCreate`、`TaskGet`、`TaskList` 和 `TaskUpdate` 表示宿主的读取、提问及进度管理接口。使用当前可用的对应能力；无专用任务接口时用本地清单记录，不因接口名称不同停止任务。
- 用户已给出的授权持续有效。先完成已授权且可独立进行的分析和准备；需要新授权时，提供具体可评审的结果再询问。

## 本地名称与工具契约

本文件对应 Xcode 工具要求的 `xcode-integration:translation`。整体任务先读取 [translation-coordinator](../translation-coordinator/SKILL.md)；如需调用 `StringCatalogRead` 验收，也先读取该协调技能以满足工具前置条件，仅执行所需验收步骤。

# Localization Resource Translator

Translate a bounded set of user-facing strings for Apple-platform apps, using the actual target and resource format. For `.xcstrings`, use only the specialized Xcode MCP String Catalog tools; never read or write those files directly. For traditional `.strings`, `.stringsdict` and `InfoPlist.strings`, use authorized file tools as described below. Preserve the original resource format; translation does not imply migration to Catalogs.

Abort if no list of keys was provided, or if no target locale identifier was provided — something went wrong. Do not guess a locale from examples; the target locale must come from your initial instructions.

## Role Boundaries

A specific list of string keys and a target locale identifier have been provided via your initial instructions.
- Do not fetch additional string keys beyond what you were given
- Do not translate into any locale other than the one explicitly provided
- Do not use `LocalizationPlanner`; preparation is the coordinator's responsibility, and traditional resource translation does not require this Catalog-creating tool
- Do not spawn sub-agents of your own



## Format Requirements

按协调者给出的 target/Bundle、source locale、目标 locale、文件/表及键列表工作；混合工程中主 App 的传统资源与 Widget 的 Catalog 分开处理。缺少实际路径或存在 target/表歧义时先查项目配置，不能拿其他 target 的同名键代替。

- **传统资源读取与写入**：读取源语言和目标语言的对应文件、注释及现有译文，逐条执行下方六步；写入目标语言文件，不改键、其他语言或无关条目。新增缺少的目标文件时沿用项目 `.lproj`、target membership 和资源组织，不自动转换格式。
- **`.strings` / `InfoPlist.strings`**：保留现有编码、注释及布局，按实际文件格式解析；文本 `.strings` 使用其带引号的键值与分号语法，正确处理双引号、反斜线、换行等转义，不能套用 JSON 或 XML 转义规则。`InfoPlist.strings` 按真实配置中的权限说明、显示名称等键翻译，不发明不存在的权限需求。
- **`.stringsdict`**：使用与实际 plist 格式匹配的解析/写入方式。XML plist 的文本须正确转义 `&`、`<` 等 XML 字符，避免手工替换导致双重转义；不能套用 Catalog 的“禁止 XML entity”规则。保留类型、`NSStringLocalizedFormatKey`、变量引用、`NSStringFormatSpecTypeKey`、`NSStringFormatValueTypeKey` 及参数位置，按该条目的实际结构处理复数，不强套单一变量名、schema 或所有语言相同分支。
- **检查与范围**：优先复用项目已有资源检查，确认其覆盖的文件与 locale；补充相应语法/编码检查，解析为字典之前另查重复键。完成后按协调技能的分层验收分别说明资源、明确语言 Bundle 与页面抽查结果。缺少构建/设备能力仅阻塞对应层，不阻止可完成的传统资源翻译，不将资源通过写成全页面验收。

## Quick Reference — Catalog Tools

| Tool | Purpose |
|------|---------|
| `StringCatalogRead` | Get string keys by translation state (new, needs_review, translated, machine_translated) |
| `StringCatalogContext` | Get source value and context: comments, similar strings, code locations, plural cases |
| `StringCatalogEdit` | Insert the translation |

## Workflow

Do not call `LocalizationPlanner` inside a translation batch. The tool reference below applies only to `.xcstrings`; traditional resources use the file workflow above.

For each string, **one at a time**, follow these steps in order.

**Step 1: Get source value and context**
For `.xcstrings`, call `StringCatalogContext` with the target locale and translate its `sourceValues`; respect `shouldTranslate: false`. For traditional resources, read the source value/plural entry from the assigned source-language file, its comments, corresponding target translations and source usages; respect the project's do-not-translate rules. Gather the same context where available:
- Developer comments explaining intent
- Existing translations in other languages
- Similar strings with their translations (for terminology consistency)
- Code locations where the string is used
- UI appearance hints (button vs. label affects verb/noun choice)
- Required plural cases for the target locale

**Step 2: Read the source code** at the provided usage locations, or search the assigned keys and resource-loading helpers for traditional resources, to understand how the string is used. This reveals the developer's intention and helps you choose the right translation (e.g., a verb for buttons, descriptive for labels). For instance, the key "Save" could be a verb (button action → "Speichern") or a noun (a save file → "Spielstand") — only the source code reveals which. Reading the source code is REQUIRED for finding a good translation. Check the actual table/Bundle and dynamic `String` or interpolation path when relevant; a present resource does not prove the caller localizes it. If usage data is unavailable, use all the context clues you have so far — developer comments, similar strings, appearance hints, and existing translations in other languages.

Some UI words are both noun and verb (e.g. "Bookmark", "Archive", "Save"), and the noun is the more common reading, so might be the one you fall back to by default. When the comment, code, or appearance information shows the string is a button or other action control, you **MUST** translate it as a verb, not a noun (or the appropriate part-of-speech according to the target language's style guide). For instance, a "Bookmark" button is the action "add a bookmark", not the object "a bookmark", hence it should be translated as a verb, and reading the source code and the appearance info gives you clarity over its usage.
Give both labels of a toggle (e.g. the two sides of a ternary) the same part of speech — never one as a verb and the other as a noun.
Follow the target-languages style-guide to determine what part-of-speech buttons, toggles, and labels should use.

**Step 3: Gather available style and terminology input, then make style choices**

Read and consider guidance from the following:
- Explicit guidance in your instructions
- Existing translations for the target locale
- The locale-specific style guide

They cover different concerns, and the higher-priority sources are often incomplete — the lower-priority ones fill the gaps rather than being ignored:

1. **Explicit guidance in your instructions.** Any terminology or style direction in the instructions you were given (how to translate a specific term, the app name, tone guidance, DNT list, etc.) is authoritative — follow it above all else.
2. **Existing translations for the target locale.** Match their terminology, phrasing, register, tone, etc. so the app's translations stay consistent. These reflect choices already made for this project and take precedence over the style guide.
3. **The locale-specific style guide.** Always read `references/styleguide_{locale}.md` (resolve it relative to the skill's base directory) when one exists for the target locale (e.g. `styleguide_pt-BR.md`, `styleguide_zh-Hans.md`—if the file doesn't exist, there isn't a style guide for that locale). Use it to inform your choices when specific guidance doesn't exist in your instructions or existing translations.

When these sources conflict, higher-priority items win: explicit instructions override existing translations, which override the style guide. Where none of them settles a question, default to informal/colloquial style.

**Step 4: Formulate translation**
Consider:
- **Terminology**: Match terms used in similar strings. If "Save" is translated as "Speichern" elsewhere, use it consistently. No matter the similar strings, make sure the part of speech of your target string is preserved: a noun sibling ("Bookmarks") is not a precedent for an action button that shares its stem ("Bookmark") — reuse the term, keep the part of speech the usage calls for.
- **Tone and formality**: Decide on the style of your translation based on your choices in step 3
- **App names**: Once you decide on how to translate an app name, make sure to to stick to this decision everywhere the app name is referenced.
- **Format specifiers**: Understand what each specifier represents by reading the source code (e.g., `%lld` might be a count of items, files, or users).

**Step 5: Determine if variation is needed**
Check whether the translation needs plural variation, device variation, or both. The following Catalog tool/reference instructions apply only to `.xcstrings`:

- **Plural**: If the string contains a numeric format specifier (`%lld`, `%d`, `%u`, etc.) paired with a countable noun, read [references/plural-variations.md](./references/plural-variations.md) (resolve it relative to the skill's base directory). The context tool provides `relevantPluralCases` for your target locale—use all of them.
    - If the context tool also returned `sourcePluralCasesToAdd`, the source itself isn't plural-varied yet. Vary the source first in a separate `StringCatalogEdit` call before translating the target — [references/plural-variations.md](./references/plural-variations.md) walks through this two-step flow.
- **Device**: If the string references a device-specific interaction (tap vs. click) or mentions a device by name, read [references/device-variations.md](./references/device-variations.md) (resolve it relative to the skill's base directory)
- **Both**: A string can need both — for example, "Tap to launch %lld spaceships" differs by device AND has a countable noun. Combine device and plural keys (e.g., `device.iphone.plural.one`), but keep `device.other` as a flat fallback string that covers both variations

For traditional resources, preserve and translate the actual plural entries, matching variable references and format value types. Check the required categories for the target locale using project guidance or verified locale rules, including a usable `other` branch where the plural rule requires it; do not copy source-language categories blindly. Numeric text alone does not authorize changing application logic or adding a new lookup mechanism. Record any required source/call-site change outside the assigned batch rather than silently inventing it. Catalog device-variation trees and `%arg` tool templates are not `.stringsdict` syntax.

**Step 6: Insert translation**
For traditional resources, write the translation with format-appropriate escaping to the assigned target file, then parse/lint the result and compare the requested entries, placeholders and plural references with the source. For `.xcstrings`, call `StringCatalogEdit` with the appropriate translation type. Translate the **source value** from `sourceValues` in Step 1 with the context you gathered. If the string is a String Set (marked `isStringSet: true` in context), provide natural alternatives in the target language using the `stringSetTranslation` parameter — these are **not** 1:1 translations but synonyms that express similar intent. For example, English `["order food in ${applicationName}", "get food in ${applicationName}"]` → German `["Essen bestellen in ${applicationName}", "Essen holen auf ${applicationName}"]`. Continue to the next string.

**Repeat these 6 steps until all requested strings are translated.**

Do not rush and cut corners; follow these 6 steps exactly for every string requested.


# Tool Reference — `.xcstrings` Only
## StringCatalogContext

Returns context and the source language value for a given string. The `sourceValues` field contains the text that must be translated. Also includes comments, translations for other languages if present, and relevant plural case hints for the target locale if applicable. Curly apostrophes and quotes are escaped (e.g., \\u2019 for curly apostrophe, \\u201C for curly quote).

### Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspaceIdentifier` | String | No | Workspace identifier or absolute workspace/project path |
| `filePath` | String | Yes | Path to String Catalog |
| `stringKey` | String | Yes | String key to get context for |
| `targetLocaleIdentifier` | String | Yes | Locale for translation (e.g., `de`, `pt-PT`) |

### Outputs

| Field | Type | Description |
|-------|------|-------------|
| `sourceValues` | SourceValues | The source language values to translate (see SourceValues type below) |
| `shouldTranslate` | Bool | Whether string should be translated (false = DO NOT TRANSLATE) |
| `isStringSet` | Bool? | Whether this is a String Set (only present when true) |
| `comment` | String? | Developer comment from String Catalog |
| `relevantPluralCases` | [String]? | Plural cases for target locale (e.g., `["plural.one", "plural.other"]`). Absent when the string doesn't require pluralization. |
| `sourcePluralCasesToAdd` | [String]? | Plural cases for the source locale. Present when the source string has a numerical format specifier but is not yet plural-varied. Absent when the source string doesn't require pluralization. |
| `translations` | [LocalizationInfo] | All existing translations across non-source locales |
| `usageLocations` | [UsageLocation]? | Source code locations where string is used |
| `appearances` | [AppearanceInfo]? | UI appearance hints (button, label, UI framework) |
| `usageDataUnavailable` | String? | Message when usage data can't be retrieved (e.g., "Build the project...") |
| `similarStrings` | [SimilarStringInfo] | Similar strings from other String Catalogs |
| `supportedDevices` | [String]? | Devices this app builds for (e.g., `["device.iphone", "device.mac"]`). Only present when the app targets multiple device families. |

### Output Types

#### LocalizationInfo

The terminology choices for this string in other languages can be an indicator of what terminology to choose for this translation. The `isVaried` field is only present (and `true`) when the localization contains plural, device, or width variations; for plain translations it is omitted.

```json
{
  "localeIdentifier": "de",
  "value": "Willkommen!"
}
```

When the localization is varied, `value` carries a human-readable description of the variation tree:

```json
{
  "localeIdentifier": "he",
  "value": "plural.one: ...\nplural.other: ...",
  "isVaried": true
}
```

#### UsageLocation

Checking how the string is used in source code can provide important context on the terminology to choose (noun vs. verb, etc.)

```json
{
  "fileURL": "file:///path/to/File.swift",
  "lineNumber": 42,
  "columnNumber": 15
}
```

#### AppearanceInfo

The way this string is presented in UI is a strong signal for part of speech to choose: translate a button or other action control as an action.

```json
{
  "usageHint": "This string is used in a SwiftUI button"
}
```

#### SimilarStringInfo

Ensure consistent terminology, formality, and style by basing new translations off existing similar strings.

```json
{
  "key": "save_button",
  "sourceDescription": "Save",
  "targetDescription": "Speichern"
}
```

#### SourceValues

The source language values that must be translated. Exactly one of `value`, `setValues`, or `variationDescription` will be non-null.

| Field | Type | Description |
|-------|------|-------------|
| `sourceLocaleIdentifier` | String | The source locale identifier |
| `value` | String? | Source text for simple strings |
| `setValues` | [String]? | Source values for string sets |
| `variationDescription` | String? | Variation tree for varied strings |

---

## StringCatalogEdit

Inserts or updates a translation in a String Catalog. Can handle simple strings, varied strings, and String Sets. If the string needs variation (e.g., plural forms), provide the `templateTranslation` or `variationTranslation` parameter. For String Sets (voice assistant commands), use `stringSetTranslation`. Prefer typographically correct quotes for the target language (e.g., „...“ for German, «...» for French). All curly quotes must be escaped (e.g., \\u201E...\\u201C for German „...“).

**Critical:** Translations must be in the correct target locale. Refer to your initial instructions to determine which locale applies. Do not infer a locale from examples in this document.

### Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspaceIdentifier` | String | No | Workspace identifier or absolute workspace/project path |
| `filePath` | String | Yes | Path to String Catalog |
| `stringKey` | String | Yes | String key to translate |
| `targetLocaleIdentifier` | String | Yes | Target locale (e.g., `de`, `pt-PT`) |

**Plus exactly one of the following (mutually exclusive):**

| Parameter | Type | Description |
|-----------|------|-------------|
| `translation` | String | Simple string translation (no variations) |
| `templateTranslation` | TemplateTranslation | Template with substitutions for multiple plural nouns |
| `variationTranslation` | VariationTranslation | Top-level variations (device, width, or single plural noun) |
| `stringSetTranslation` | [String] | Array of values for String Sets |

### Translation Types

#### Simple Translation

For strings without variations:

```json
{
  "stringKey": "welcome_message",
  "targetLocaleIdentifier": "de",
  "translation": "Willkommen in unserer App!"
}
```

#### Template Translation

For strings with multiple format specifiers + countable nouns:

```json
{
  "stringKey": "usage_message",
  "targetLocaleIdentifier": "de",
  "templateTranslation": {
    "template": "iCloud+ wird von %#@arg1@ und %#@arg2@ verwendet.",
    "substitutions": [
      {
        "name": "arg1",
        "argNum": 1,
        "formatSpecifier": "lu",
        "variants": {
          "plural.one": "%arg Gerät",
          "plural.other": "%arg Geräte"
        }
      },
      {
        "name": "arg2",
        "argNum": 2,
        "formatSpecifier": "lu",
        "variants": {
          "plural.one": "%arg Mitglied",
          "plural.other": "%arg Mitglieder"
        }
      }
    ]
  }
}
```

#### Variation Translation

For strings with top-level plural, device, or width variations, or a single format specifier + countable noun:

**Single plural noun:**

```json
{
  "stringKey": "item_count",
  "targetLocaleIdentifier": "pl",
  "variationTranslation": {
    "topLevelVariation": {
      "plural.one": "Masz %lld przedmiot",
      "plural.few": "Masz %lld przedmioty",
      "plural.many": "Masz %lld przedmiotów",
      "plural.other": "Masz %lld przedmiotu"
    }
  }
}
```

**Device-only variations (no plurals):**

```json
{
  "stringKey": "action_hint",
  "targetLocaleIdentifier": "es",
  "variationTranslation": {
    "topLevelVariation": {
      "device.iphone": "Toca aquí",
      "device.mac": "Haz clic aquí",
      "device.other": "Pulsa aquí"
    }
  }
}
```

**Device variations with single plural noun:**

```json
{
  "stringKey": "launch_button",
  "targetLocaleIdentifier": "fr",
  "variationTranslation": {
    "topLevelVariation": {
      "device.iphone.plural.one": "Touchez pour lancer %lld vaisseau spatial",
      "device.iphone.plural.other": "Touchez pour lancer %lld vaisseaux spatiaux",
      "device.mac.plural.one": "Cliquez pour lancer %lld vaisseau spatial",
      "device.mac.plural.other": "Cliquez pour lancer %lld vaisseaux spatiaux",
      "device.other": "Touchez pour lancer %lld vaisseaux spatiaux"
    }
  }
}
```

**Device variations with substitutions (multiple plural nouns):**

```json
{
  "stringKey": "device_usage",
  "targetLocaleIdentifier": "de",
  "variationTranslation": {
    "topLevelVariation": {
      "device.iphone": "iCloud+ wird von %#@arg1_iphone@ und %#@users@ verwendet",
      "device.mac": "iCloud+ wird von %#@arg1_mac@ und %#@users@ verwendet",
      "device.other": "iCloud+ wird von %lld und %lld verwendet"
    },
    "substitutions": [
      {
        "name": "arg1_iphone",
        "argNum": 1,
        "formatSpecifier": "lld",
        "variants": {
          "plural.one": "%arg anderes iPhone",
          "plural.other": "%arg andere iPhones"
        }
      },
      {
        "name": "arg1_mac",
        "argNum": 1,
        "formatSpecifier": "lld",
        "variants": {
          "plural.one": "%arg anderer Mac",
          "plural.other": "%arg andere Macs"
        }
      },
      {
        "name": "users",
        "argNum": 2,
        "formatSpecifier": "lld",
        "variants": {
          "plural.one": "%arg Benutzer",
          "plural.other": "%arg Benutzer"
        }
      }
    ]
  }
}
```

**Critical**: See [plural-variations.md](./references/plural-variations.md) for detailed rules.

**Critical:** Insert the entire variation structure, including already translated variants. This overwrites what was there before.

#### String Set Translation

For String Sets (voice assistant commands):

```json
{
  "stringKey": "COMMAND_ORDER",
  "targetLocaleIdentifier": "de",
  "stringSetTranslation": ["Essen bestellen", "Essen holen", "Essen kaufen"]
}
```

Note: provide synonyms/alternatives, not direct 1:1 translations.

### Type Definitions

**TemplateTranslation:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `template` | String | Yes | Template with `%#@name@` substitution references |
| `substitutions` | [Substitution] | Yes | Array of substitution definitions |

**VariationTranslation:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `topLevelVariation` | {String: String} | Yes | Maps variation paths to templates (e.g., `"plural.one"`, `"device.iphone"`) |
| `substitutions` | [Substitution]? | No | Optional substitutions referenced by templates |

**Substitution:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | String | Yes | Placeholder name (used as `%#@name@` in template) |
| `argNum` | Int | Yes | 1-indexed argument position |
| `formatSpecifier` | String | Yes | Format type without % (e.g., `lld`, `@`, `u`) |
| `variants` | {String: String} | Yes | Maps variation paths to values (use `%arg` as number placeholder) |

### Outputs

| Field | Type | Description |
|-------|------|-------------|
| `success` | Bool | Whether translation was inserted |
| `message` | String | Success or error message |

---


## StringCatalogRead

This tool should only be used to verify your work.

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

1. **Use only String Catalog tools** to access .xcstrings files. Never write to them directly.
2. **Translate one string at a time**, following all 6 steps for **each** before moving to the next.
3. **Preserve format specifiers exactly** as they appear in source (`%1$lld`, `%@`, etc.).
4. **Make explicit choices about translation style**—a well-translated app has consistent style throughout. Always read the target locale's style guide when one exists and use it as the baseline; explicit instructions and existing translations take precedence over it wherever they apply.
5. **Keep app names consistent**—when you translate them once, make sure to translate them everywhere.
6. **Complete the entire task**—continue until all requested translations are done.
7. **Use typographically correct quotes and apostrophes**, with escaping suited to the resource. For Catalog tool parameters, follow the current transport protocol for quotes/Unicode and use literal `&`, `<`, `>` rather than HTML/XML entities; Catalog text is not XML. This restriction does **not** apply to XML `.stringsdict`: follow Format Requirements for XML escaping, and use `.strings` syntax for traditional string tables. Do not blindly escape everything.
8. Do NOT skip steps to save time, even when there are hundreds of strings. Each step exists to prevent translation errors that are harder to find and fix later. This process takes time, and that's ok. Don't skip work or cut corners to save time, rather focus on accuracy and completeness.
9. **Use the exact locale identifier from your instructions** as the `targetLocaleIdentifier` in every tool call. Do NOT normalize, canonicalize, or expand it (e.g., if told `zh-TW`, use `zh-TW` — never `zh-Hant-TW`; if told `pt-BR`, use `pt-BR` — never `pt-Latn-BR`). The String Catalog uses these identifiers as-is, and mismatches will cause translations to be stored under the wrong locale. For traditional resources, use the assigned locale and its verified project file mapping; do not rename `.lproj` directories or invent locale mappings.


### Catalog Example

For each Catalog string key:

1. Agent calls `StringCatalogContext` to get the source value, developer comments, similar strings, code locations, and plural cases.
2. Agent reads the source code at the provided file paths to understand how the string is used (verb vs. noun, button vs. label).
3. Agent reads the locale style guide (when one exists for the target locale), reviews existing translations for terminology and tone, and notes any explicit guidance in its instructions — then applies them with explicit instructions taking precedence over existing translations, and existing translations over the style guide.
4. Agent formulates the translation, considering terminology consistency, tone, app names, and format specifiers.
5. Agent determines whether variation is needed: plural variation (format specifiers + countable nouns), device variation (interaction verbs or device names + multiple `supportedDevices`), or both.
6. Agent calls `StringCatalogEdit` to insert the translation for the requested target language.

### Traditional Resource Example

对于主 App 中明确的 `ja` 批次：读取指定 source `.lproj` 与 `ja.lproj` 中的对应表，逐键查源码和已有术语，翻译普通值、真实复数分支及请求内的权限说明，再用文件工具写回原格式。运行适用的资源检查；若具备所需 Xcode MCP 能力，补明确 `ja` Bundle 的缺失哨兵查找和相关页面抽查。Widget 的 `.xcstrings` 另用 Catalog 工具，不因主 App 使用旧资源而停止整个任务，也不调用 Planner 迁移它。
