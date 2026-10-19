# 证据清单与生成器

用于创建及反复更新项目对比报告。脚本只处理累积清单、图片和 HTML；视觉判断与交互结果由实际复查提供。历史报告可以映射导入，原有模块和状态不能因新一次运行而丢失。

## 清单格式

UTF-8 JSON；`rows` 的数组顺序就是网页顺序。图片路径相对清单文件，也可传绝对本地路径。清单不是采样脚本，不能通过配置状态绕过真实业务门禁。

```json
{
  "title": "App UI 视觉复查",
  "scope": "Settings 与 History 模块",
  "boundaries": ["使用已提供的历史原生截图；本轮尚未重跑设备交互。"],
  "columns": [
    {"id": "design", "label": "Figma 效果图", "viewport": [390, 844]},
    {"id": "reference", "label": "参考设备", "viewport": [390, 844]},
    {"id": "compact", "label": "用户指定的小屏设备", "viewport": [375, 667]}
  ],
  "rows": [
    {
      "key": "settings-reminder-selected",
      "title": "提醒日期 · 选中",
      "group": "Settings",
      "route": "settings/reminder",
      "state": "selected · top",
      "status": "issue",
      "note": "待核对：底部末项是否能完整滚到操作区上方。",
      "figma_url": "https://www.figma.com/design/example?node-id=1-2",
      "cells": {
        "design": {
          "path": "figma/reminder.png", "source": "figma", "revision": "节点导出版本或日期"
        },
        "reference": {
          "path": "reference/reminder-selected.png", "source": "runtime",
          "revision": "代码提交或工作区版本", "os": "实际系统版本",
          "captured_at": "实际采样时间", "note": "生产 View，隔离选中数据"
        },
        "compact": {"missing": "此设备尚未采集"}
      }
    }
  ]
}
```

这是字段示例，不包含可用图片；使用实际素材替换路径和示例值，不创建占位图片。列数至少两列，参考列放在首位，其余列按用户要求排列。`viewport` 是该列的逻辑基准，不是图片必须恰好等于的像素尺寸；横竖屏或不同 Sheet 尺寸可通过单个 cell 的 `viewport` 覆盖。不要把不同视口的截图放进同一状态而不说明。

### 必填与可选

- 顶层 `title`、`scope`、`columns`、`rows` 必填；`boundaries` 是可选的证据边界字符串数组。
- 每列 `id` 唯一，`label` 与正数 `[width, height]` 形式的 `viewport` 必填。id 和 row key 使用字母、数字、点、下划线或连字符。
- 每行 `key` 在项目内唯一，推荐 `<module>-<page>-<state>`；`title`、`group`、`state`、`status`、`cells` 必填。`group` 是稳定模块名，不能用同 key 覆盖另一个模块；分支/步骤放在 route 或 state。`route`、`note`、`figma_url` 可选，稿件链接需对应实际图片节点。
- 每行 cells 必须覆盖声明的每一列；实际图片用 `path` 加 `source`，尚无证据用非空 `missing` 原因，二者不能并存。不靠漏字段隐藏未采集设备。
- `source` 为 `figma`、`runtime`、`preview` 或 `baseline`。`revision`、`os`、`captured_at`、`note` 可选，缺少来源版本时网页显示“版本未记录”，不能凭文件名补造。
- status 为 `unreviewed`、`issue`、`fixed`、`verified` 或 `blocked`，分别显示待复查、发现问题、已修复待复验、视觉已复验、受阻。`verified` 由人工/实际复验提供；仍有 missing 的行不允许标为 verified。

同一图片可被多个状态引用，脚本会复用输出文件，但状态依然独立。长稿可以用于顶部、底部两个状态；备注说明这是同一整页稿，不表示滚动位置完全一致。动画静态状态、输入 fixture 或历史证据写入对应 cell.note / boundaries，真实计时和手势结果另行记录。

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

先生成 A 模块再生成 B，核对 A 的状态和原图仍在；再刷新 A，确认 B 不变。核对列名、模块分组、状态数、缺口数和原图比例；实际操作搜索、模块/状态筛选、定位、重复定位、长图展开、放大和关闭。模块选择写入 `?module=<模块名>`；状态标题提供该模块与 `#row-<key>` 的组合链接，刷新/重新打开后仍可定位。

脚本完成的是输入完整性和报告生成。它不理解页面的布局、不验证实际设备、不读取源码修复 UI，也不替代视觉复验。浏览器不可用时保留生成物并说明网页交互尚未验证。

维护生成器时运行 `python3 <skill-dir>/scripts/test_build_comparison.py`，覆盖原图不变、列与缺口、损坏输入、累积/刷新、冲突保护、原采样文件消失、重建及并发更新；测试仅写临时目录。
