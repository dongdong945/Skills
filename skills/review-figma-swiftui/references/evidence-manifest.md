# 证据清单与生成器

用于创建及反复更新项目对比报告。脚本只处理累积清单、图片和 HTML；视觉判断与交互结果由实际复查提供。历史报告可以映射导入，原有模块和状态不能因新一次运行而丢失。

## 清单格式

UTF-8 JSON；`rows` 的数组顺序就是网页顺序。图片路径相对清单文件，也可传绝对本地路径。清单不是采样脚本，不能通过配置状态绕过真实业务门禁。

```json
{
  "title": "App UI 视觉复查",
  "scope": "Settings 与 History 模块",
  "boundaries": ["使用已提供的历史原生截图；本轮尚未重跑设备交互。"],
  "locale_labels": {"en": "English", "zh-Hans": "简体中文"},
  "columns": [
    {"id": "design", "label": "Figma 效果图", "viewport": [390, 844]},
    {"id": "reference", "label": "iPhone 12", "viewport": [390, 844]},
    {"id": "compact", "label": "iPhone SE 3", "viewport": [375, 667]},
    {"id": "iphone-duo-outer", "label": "iPhone Duo · 外屏", "viewport": [466, 678]}
  ],
  "rows": [
    {
      "key": "settings-reminder-selected-zh-Hans",
      "title": "提醒日期 · 选中",
      "group": "Settings",
      "route": "settings/reminder",
      "state": "selected · top",
      "locale": "zh-Hans",
      "status": "issue",
      "note": "待核对：底部末项是否能完整滚到操作区上方。",
      "figma_url": "https://www.figma.com/design/example?node-id=1-2",
      "cells": {
        "design": {
          "path": "figma/reminder.png", "source": "figma", "locale": "en", "revision": "节点导出版本或日期"
        },
        "reference": {
          "path": "reference/reminder-selected.png", "source": "runtime",
          "revision": "代码提交或工作区版本", "os": "实际系统版本",
          "captured_at": "实际采样时间", "note": "生产 View，隔离选中数据"
        },
        "compact": {"missing": "此设备尚未采集"},
        "iphone-duo-outer": {"missing": "尚未执行 Duo 外屏采样"}
      }
    }
  ]
}
```

这是字段示例，不包含可用图片，也不要求每个任务采集这三种设备；使用实际素材替换路径和示例值，不创建占位图片。列数至少两列，唯一的 Figma 参考列放在首位并保持原 id，其余列保存各设备或姿态的证据。普通设备每行显示首列与所选设备；Duo 的三个姿态合并为一个设备选项，选中后同时显示三列。`viewport` 是该列的逻辑基准，不是图片必须恰好等于的像素尺寸；横竖屏或不同 Sheet 尺寸可通过单个 cell 的 `viewport` 覆盖。Duo 的示例尺寸只代表一次外屏记录，内/外屏、半折与窗口尺寸按实际采样填写，见 [Duo 设备与折叠状态](iphone-duo.md)。

参考列 id 可自定义，但同一项目的所有增量必须与累计清单的首列 id 一致。首列有图时 `source` 必须为 `figma`，设备列有图时不能使用 `figma`；参考缺稿继续使用 `missing`。参考 id 改名属于单独的清单迁移，不能当作新增设备合并。

### 必填与可选

- 顶层 `title`、`scope`、`columns`、`rows` 必填；`boundaries` 是可选的证据边界字符串数组。
- 顶层 `locale_labels` 可选，格式为语言标识到显示名称的对象，如 `{"en": "English", "zh-Hans": "简体中文"}`；未提供名称时直接显示语言标识。名称按项目累积，不限制语言种类。
- 每列 `id` 唯一，`label` 与正数 `[width, height]` 形式的 `viewport` 必填。id 和 row key 使用字母、数字、点、下划线或连字符。
- 每行 `key` 在项目内唯一，推荐 `<module>-<page>-<state>`；`title`、`group`、`state`、`status`、`cells` 必填。`group` 是稳定模块名，不能用同 key 覆盖另一个模块；分支/步骤放在 route 或 state。`route`、`note`、`figma_url` 可选，稿件链接需对应实际图片节点。
- 每行 `locale` 可选，表示该状态的目标 UI 语言，使用 `en`、`zh-Hans`、`pt-BR` 等语言标识；下划线和大小写写法会规范化。不同语言使用不同 key，例如 `<module>-<page>-<state>-zh-Hans`。同 key 已声明语言时，不能换成另一语言覆盖；更新时继续明确填写 `locale`。旧清单未提供该字段仍能生成，网页显示“未标注语言”，不自动视为英文。
- 每行 cells 必须覆盖声明的每一列；实际图片用 `path` 加 `source`，尚无证据用非空 `missing` 原因，二者不能并存。不靠漏字段隐藏未采集设备。
- `source` 为 `figma`、`runtime`、`preview` 或 `baseline`。`revision`、`os`、`captured_at`、`note` 可选，缺少来源版本时网页显示“版本未记录”，不能凭文件名补造。
- 单个 cell 可用 `locale` 覆盖行语言，用于英文稿对照中文运行图等情况；未填写时继承 `row.locale`。筛选依据行语言，图片说明保留各自实际语言。`locale` 只记录证据，不会翻译图片或重新运行 App。
- status 为 `unreviewed`、`issue`、`fixed`、`verified` 或 `blocked`，分别显示待复查、发现问题、已修复待复验、视觉已复验、受阻。`verified` 由人工/实际复验提供；仍有 missing 的行不允许标为 verified。

`source` 记录图片来源，不代替当前验收范围。历史采样、仅观察图或 fixture 的适用范围写入 `note` / `boundaries`，保留真实版本与日期。缺少对应稿件的运行图可记录布局观察，但该行仍保留缺稿及未完成对稿的状态；生成器不自动判断图是否黑屏、状态错配或已被实际审阅。

在现有逐页记录或独立审图台账中，将复验结果绑定到 key、设备列和实际图片 hash；来源与复用依据见 [视觉复查与修正闭环](review-workflow.md)。生成器校验文件和清单完整性，不校验这些审阅结论的真实性。

同一图片可被多个状态引用，脚本会复用输出文件，但状态依然独立。长稿可以用于顶部、底部两个状态；备注说明这是同一整页稿，不表示滚动位置完全一致。动画静态状态、输入 fixture 或历史证据写入对应 cell.note / boundaries，真实计时和手势结果另行记录。

多语言仍是一份参考稿加设备列；每种语言按页面状态增加行，不把语言混作模块或设备。语言下拉框包含已有行语言和实际存在的“未标注语言”，可与模块、状态、搜索组合。缺少某种语言的页面需要按采集范围补充，不复制另一语言的截图来填充，也不把筛选结果当成完整覆盖证明。

设备下拉框从首列之后的列生成；`iphone-duo-outer`、`iphone-duo-half-fold`、`iphone-duo-inner`（兼容 `duo-` 前缀）合并为唯一的 `iphone-duo` / iPhone Duo 选项。选择后依次显示外屏、半折叠、展开，底层各列的图片和来源独立保留。同一姿态不能重复声明别名列。其他设备继续按其稳定 id 显示。默认优先选择 id 为 `iphone12`（兼容连字符/下划线）或 label 明确为 iPhone 12 的列；iPhone 12 Pro/mini 不当作 iPhone 12。兼容历史 `reference` 等列 id，不为默认设备改名。没有 iPhone 12 时使用已声明的第一个设备，不自动增加图片或列。

每次切换所选机型的图和对应表头，Figma 始终保留。Duo 即使只声明一种姿态，也会展示其余姿态的文字缺口和「尺寸待测量」，不猜造尺寸、不复用其他姿态的图；缺口统计包含这些未声明姿态，原图像证据数不变。仅覆盖原列的 verified 行在网页显示待复查，清单中的原 status 保留原有证据范围。所有隐藏设备的证据、缺口、语言和版本仍保存在清单中，顶部统计针对完整矩阵；当前选择的设备缺图时显示该单元原有 missing 原因。URL 中的未声明设备显示“未纳入此报告”，不回退到其他设备。设备切换不会改变行状态或将缺口降为通过。

## 生成

选择可导入 `PIL` 的 Python。Pillow 是报告工具依赖，不属于 iOS App。

```sh
python3 <skill-dir>/scripts/build_comparison.py settings.json --project-root <project-root> --check
python3 <skill-dir>/scripts/build_comparison.py settings.json --project-root <project-root>
python3 <skill-dir>/scripts/build_comparison.py history.json --project-root <project-root>
```

结果固定为：

```text
<project-root>/output/ui-review/
  index.html        # 全项目累积视图，支持选择模块
  manifest.json     # 生成器维护的累积清单，引用本目录中的真实媒体
  media/            # 按内容摘要命名的原图
  .update.lock      # 更新进程的文件锁
```

`--project-root` 默认当前目录，建议显式传入。每个模块的输入清单可保存在 `output/ui-review/inputs/`；这是可选输入位置，不要创建空目录。不要再使用旧版 `--output`，也不要按模块换输出目录来替代累积更新。

`--check` 只读校验本轮输入、已有累积清单及合并结果，不写文件。生成时复制实际 PNG/JPEG/WebP 至 `media/`，不裁切或重绘原图。HTML 和累积清单均只引用本地相对媒体，搬动整个报告目录后仍可用；本轮输入和源图片保持不变。没有联网或 App 构建操作。

全部输入检查完成后才写入报告；未声明的缺图、重复 key、无效图片或非法状态会返回错误。明确声明的 missing 会生成文字缺口及统计，不生成伪造图片。生成器不会把“图片齐全”推导成 verified。

缺口说明区分设计缺稿、目标设备/系统运行图未采及采集受阻；汇总时按实际原因解释数量。缺口数是证据单元数量，不等于未实现功能数，缺稿或受阻也不能用其他状态图片补成通过。

### 增量合并约定

- 新模块/新状态追加；同 key 在原模块内更新。未出现在本轮输入的模块与状态全部保留，并按模块聚合显示。不同模块使用相同 key 时拒绝写入，避免覆盖旧模块。
- 同模块中，既有状态保留顺序，新状态追加到该模块末尾。输入遗漏不是删除指令；页面删除、重排或模块改名需要单独明确处理累积清单。
- 列按稳定 id 累积；同 id 改成另一设备名称会拒绝合并。同一列的逻辑视口可以按 cell 保留，因此不同尺寸的稿件不会改变旧图的布局基准。
- 新增设备列后，旧模块保留，未采集的单元明确缺图。该行此前的 verified 只覆盖旧矩阵，会退回待复查并保留说明。刷新同 key 时，未在本轮提供的设备列也记缺口，不把旧版本截图冒充新证据。
- 全 App 输入也执行相同合并规则，不清空以前逐模块积累的内容。已有模块下已撤除的页面会继续保留，直到明确确认删除。
- 元数据保留各图来源和版本；报告另有内容决定的 `report_revision`，不是 App build number，也不证明所有模块来自同一 App 版本。

生成器在文件锁内重读清单并合并，避免两个模块并发更新丢数据；文件以原子替换方式写入，失败不拿新清单覆盖已校验失败的报告。生成器已在 macOS 验证；静态报告可在其他系统浏览。`manifest.json` 是权威累积数据，`index.html` 可重建；多文件并非数据库事务，写入中断后按清单重建一次即可。

重复生成复用相同图片摘要，新图产生新路径避免缓存混淆。不会删除旧图片或其他文件。只剩报告目录、原采样文件已不在时，可直接从其累积清单重建：

```sh
python3 <skill-dir>/scripts/build_comparison.py <project-root>/output/ui-review/manifest.json --project-root <project-root>
```

这条命令重建生成器自身的累积清单；普通模块输入仍保持不变。不要直接修改生成的 HTML 代替更新数据。

可直接打开 HTML，也可用普通本地 HTTP 服务提供整个输出目录。端口由当前环境选择，不写死 8765；仅需本机查看时绑定 127.0.0.1。不要为了查看报告改变网络公开范围。

## 网页验收

先生成 A 模块再生成 B，核对 A 的状态和原图仍在；再刷新 A，确认 B 不变。核对列名、模块分组、状态数、缺口数和原图比例；实际操作搜索、模块/语言/设备/状态筛选、定位、重复定位、长图展开、放大和关闭。默认仅显示 Figma + iPhone 12；切换 Duo 后表头及每行依次显示 Figma + 外屏 + 半折叠 + 展开，缺图状态同样显示。

选择写入 `?module=<模块名>&locale=<语言标识>&device=<设备id>`；Duo 使用 `device=iphone-duo`，兼容已声明姿态列 id 的旧链接并归一化；当前筛选链接和每个状态标题均保留设备、语言及 `#row-<key>`，刷新/重新打开后仍可定位。设备切换时当前定位应保持可见，旧链接没有 device 时使用默认设备。`locale=__unlabeled__` 选择未标注语言；没有对应采样的语言链接显示空结果，不回退到英文；未声明的设备链接保留明确缺口。清除筛选恢复全部语言、旧状态及默认设备。放大后切换设备应关闭原设备放大图，不能留着旧图冒充新选择。

脚本完成的是输入完整性和报告生成。它不理解页面的布局、不验证实际设备、不读取源码修复 UI，也不替代视觉复验。浏览器不可用时保留生成物并说明网页交互尚未验证。

维护生成器时运行 `python3 <skill-dir>/scripts/test_build_comparison.py`，覆盖原图不变、参考列角色与 id 稳定性、缺稿兼容、列与缺口、损坏输入、累积/刷新、冲突保护、原采样文件消失、重建、并发更新、多语言兼容、iPhone 12 默认选择、Duo 机型合并、三姿态顺序、缺图与独立证据保留；测试仅写临时目录。JavaScript 设备切换、组合筛选与链接行为仍需实际浏览器验证。
