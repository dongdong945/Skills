# 证据清单与生成器

用于需要新建或通用化对比报告的任务；已有合适报告时无需转换格式。脚本只处理清单、图片及 HTML，视觉判断和交互结果由实际复查提供。

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
- 每行 `key` 唯一，`title`、`group`、`state`、`status`、`cells` 必填；`route`、`note`、`figma_url` 可选。稿件链接只记录一处，检查它确实指向当前图片的节点，避免链接与图片来源漂移。
- 每行 cells 必须覆盖声明的每一列；实际图片用 `path` 加 `source`，尚无证据用非空 `missing` 原因，二者不能并存。不靠漏字段隐藏未采集设备。
- `source` 为 `figma`、`runtime`、`preview` 或 `baseline`。`revision`、`os`、`captured_at`、`note` 可选，缺少来源版本时网页显示“版本未记录”，不能凭文件名补造。
- status 为 `unreviewed`、`issue`、`fixed`、`verified` 或 `blocked`，分别显示待复查、发现问题、已修复待复验、视觉已复验、受阻。`verified` 由人工/实际复验提供；仍有 missing 的行不允许标为 verified。

同一图片可被多个状态引用，脚本会复用输出文件，但状态依然独立。长稿可以用于顶部、底部两个状态；备注说明这是同一整页稿，不表示滚动位置完全一致。动画静态状态、输入 fixture 或历史证据写入对应 cell.note / boundaries，真实计时和手势结果另行记录。

## 生成

选择可导入 `PIL` 的 Python。Pillow 是报告工具依赖，不属于 iOS App。

```sh
python3 <skill-dir>/scripts/build_comparison.py manifest.json --check
python3 <skill-dir>/scripts/build_comparison.py manifest.json --output Docs/UIComparison/index.html
```

`--check` 只读检查清单及图片解码。生成时复制实际引用的 PNG/JPEG/WebP 到输出目录的 `media/`，以内容摘要命名，不修改、裁切或重绘原图。HTML 使用相对图片链接，整个输出目录可搬动或共享；清单与源图片不变。没有额外联网或 App 构建操作。

全部输入检查完成后才写入报告；未声明的缺图、重复 key、无效图片或非法状态会返回错误。明确声明的 missing 会生成文字缺口及统计，不生成伪造图片。生成器不会把“图片齐全”推导成 verified。

重复生成会更新 HTML，复用相同图片摘要；新图产生新路径，避免浏览器沿用旧截图。不会删除输出目录中其他文件或旧图片。继续复查时更新原始清单，不手改生成的 HTML 充当源数据。

可直接打开 HTML，也可用普通本地 HTTP 服务提供整个输出目录。端口由当前环境选择，不写死 8765；仅需本机查看时绑定 127.0.0.1。不要为了查看报告改变网络公开范围。

## 网页验收

核对列名/顺序、模块分组、状态总数、缺口数及原始图比例；至少实际操作搜索、模块/状态筛选、定位、重复定位、长图展开、放大和关闭。跳转应清除阻挡目标的筛选；直接链接 `#row-<key>` 可定位同一状态。

脚本完成的是输入完整性和报告生成。它不理解页面的布局、不验证实际设备、不读取源码修复 UI，也不替代视觉复验。浏览器不可用时保留生成物并说明网页交互尚未验证。

维护生成器时可运行 `python3 <skill-dir>/scripts/test_build_comparison.py`，检查可搬动输出、原图不变、任意设备列、缺口、解码失败与重复生成；测试数据仅写临时目录。
