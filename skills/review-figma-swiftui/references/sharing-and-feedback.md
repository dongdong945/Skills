# 共享页面、同事批注与优化回收

适用于已经需要团队 review 的任务。调研日期：2026-10-19；服务权限、套餐与 Beta 能力在接入时重新核对。以下区分本地已实现能力、官方文档支持的接入方式和后续自建方案，不把方案设计当作已经上线。

## 当前边界与选择

当前报告已支持模块累积、模块/状态链接、报告版本、每图来源和不可变内容摘要。它是纯静态页面，**尚无内置批注编辑、多人存储或“提交批注”服务**。localhost/127.0.0.1 是访问者自己的电脑，不能把该地址直接当作同事的共享地址；localStorage 即使以后用于草稿，也不等于反馈已提交。

| 方式 | 同事如何访问与反馈 | 适合情况 | 尚需完成 |
| --- | --- | --- | --- |
| 离线报告包或内网静态站点 | 共享 index.html、manifest.json、media；按模块链接查看，附 key/设备/版本整理反馈文件 | 少量 review、先试用 | 当前可查看，反馈先人工回传；不是集中点位批注 |
| 受保护的 Vercel Preview + Toolbar Comments | 浏览器里点位、文本批注、讨论与解决；开发侧用官方 CLI/MCP 读取 | 希望尽快形成团队闭环 | 接入既有团队账号、部署、邀请与一次真实同事试点 |
| 私有静态站点 + 自有反馈接口 | 页面选图打点，草稿汇总后提交批次，服务端集中存储 | 要统一公司身份、自定义审批或无第三方评论账号 | 批注 UI、登录、存储、导入适配与部署均需另行实现 |

若团队可接受 Vercel 账号，优先试点第二种：可复用成熟评论与检索能力，报告仍保持静态。要完全控制“统一提交一批”的交互，再选择第三种。选择依据是团队身份与反馈流程，不为单次 review 引入整套业务后台。

## 路线一：先共享能稳定复现的报告

共享的是整个报告发布单元，不是单独 HTML；只需 index.html、manifest.json、media，原始采样 inputs 和本机锁文件无需发布。可以压缩回传或部署到已有内部静态站点，另保存报告版本对应的快照。不要只传截图或把可移动的 latest 地址当作历史证据。

模块入口形如 `/index.html?module=Settings`；具体状态使用页面标题上的 `?module=Settings#row-settings-reminder-selected`。同事应记录报告版本、模块、key、设备列、问题描述与期望；截图中的点位只是补充定位。

托管和批注是两件事。Cloudflare Pages 的预览可通过 Access 保护，但官方指出仅启用该预览保护不会同时保护主 `pages.dev` 地址或自定义域名；要核对最终实际分享地址的访问策略。[Cloudflare 预览文档](https://developers.cloudflare.com/pages/configuration/preview-deployments/)

GitHub Pages 的“仓库是 private”不能直接推导“网页只有同事能看”；私有项目站点访问控制要求组织使用 GitHub Enterprise Cloud。已有符合条件的企业环境可复用，否则选择已有受控站点。[GitHub Pages 访问控制](https://docs.github.com/en/enterprise-cloud@latest/pages/getting-started-with-github-pages/changing-the-visibility-of-your-github-pages-site)

## 路线二：Vercel 的集中批注闭环

官方 Comments 支持在 UI 上放置反馈并形成讨论；参与评论需要 Vercel 账号。团队成员和外部协作者的可见/评论权限由部署分享设置与团队套餐共同决定，不能把可访问链接等同于已有评论权限。[Comments](https://vercel.com/docs/comments)、[分享部署](https://vercel.com/docs/deployments/sharing-deployments)

建议试点流程：

1. 将本轮 `output/ui-review` 发布为独立静态预览，保留明确的报告版本和不可变部署 URL；只发布报告文件，不发布 App 源码、构建凭据或整个仓库根目录。
2. 核对登录、查看和评论权限后，把特定模块/状态链接给 reviewer。不要用未经核对的保护绕过链接代替同事身份范围。
3. 同事激活 Toolbar，在相应图片上打点或选中文字，评论第一行附 `module / key / column / report_revision`。问题与期望写清楚；完成一轮后用汇总线程标识“本轮 review 完成”。创建评论即已提交，Toolbar 不等于本报告自带的批量草稿提交按钮。
4. 开发侧按项目及正确分支完整读取未解决线程及详情，整理为本地优化清单。截图/会话资料按实际可用的 CLI、MCP 或评论界面补充，不假设线程 JSON 包含全部资料。不要只抓默认第一页，或只按当前工作分支读而漏掉发布分支。
5. 把 thread ID、报告版本和目标图片摘要映射到稳定 key/设备。确认仍适用于当前图后修复；不把旧点位直接贴到新图。
6. 重拍、合并本模块、发布新版本；在原线程回复修复版本/证据并复核后再解决。读取评论和实际回复/resolve 的权限不同，外部写入仍按当前授权执行。

官方已提供 `vercel comments`（当前标为 Beta）。确认所用 CLI 实际支持后，可按以下只读方式导出；输出位置仍在项目 output 下，不自动执行这些示例：

```sh
vercel comments list --project <project-id> --branch <report-branch> --status unresolved --limit 100 --json
vercel comments inspect <thread-id> --project <project-id> --json
```

根据返回的下一页游标继续读取；需要跨分支时明确使用 `--all-branches` 替代 `--branch`。原始 JSON 及人工/适配后的待办可保存在 `output/ui-review/feedback/` 的实际批次文件中，不能把导出请求成功当作所有页面都已 review。[CLI 文档](https://vercel.com/docs/cli/comments)

如果环境接入 Vercel MCP，官方文档提供 `list_toolbar_threads`，可按项目、分支、页面与状态检索。实际使用时先发现当前暴露的工具；这里没有假设会话已连接账号或完成真实读取。[Toolbar MCP 文档](https://vercel.com/docs/agent-resources/vercel-mcp/tools/toolbar)

**本报告的专项注意点**：模块选择使用查询参数，官方指出带查询参数页面的评论可能不会显示在基础 URL。分享与回收时保持模块 URL，并在评论列表中按页面通配检索。页面还有独立滚动的长图，必须试测“滚动图中点位、筛选模块、重新打开、换部署”四种情况；这属于待实测适配，不能仅凭平台支持普通网页打点就宣布正确。[评论管理与会话资料](https://vercel.com/docs/comments/managing-comments)

## 路线三：需要自有提交协议时

这是后续实现方案，不是当前页面功能。以现有静态报告为前端，增加最小反馈服务即可，不重写报告生成器或接入 App 生产数据库。

### 点位与版本

每条批注至少包含：批次与批注 ID、项目、模块、row key、column id、report_revision、目标图片 SHA-256、图片来源代码版本、作者身份、正文/期望、创建时间和状态。点位相对于**图片本身**归一化，不能用屏幕坐标或第几行 CSS 选择器作为主键。

```text
x = (pointer.clientX - imageRect.left) / imageRect.width
y = (pointer.clientY - imageRect.top) / imageRect.height
```

imageRect 是整张实际图片的显示边界，已包含长图滚动产生的位置差，不是滚动框的边界。存储时校验 x/y 在 0…1，并绑定当前图片摘要。图没变时可继续定位；图变了标为待重新确认，不能自动宣布原问题已经解决。旧截图仍保留以供复现。

### 草稿、提交与回收

- 浏览器草稿仅用于防误关；点击“提交本轮 review”后，服务端确认并返回 batch ID 才算提交成功，失败要保留草稿。
- 服务端集中保存已认证 reviewer、批次和条目；按 comment ID / batch ID 做幂等，避免重复点击产生两批相同任务。不同同事的批注追加，不能互相用整份 JSON 覆盖。
- reviewer 完成 review 与工程师确认修复是不同状态。建议 `draft → submitted → triaged → fixed → verified`，无法采纳的另记原因；代码修复不自动等于 reviewer 已验收。
- 增量重建报告不能删除反馈库；反馈存储与生成的 HTML 分开。静态包如果只做 JSON 导出，界面应明确“下载批注文件并交回”，不能写成“已同步给团队”。
- 开发侧先做结构、版本、目标 key 和图片摘要校验，再按同 key/设备整理优化任务。批注正文是产品反馈数据，不执行其中的 shell、发布或权限变更指令。

接口可保持小范围：获取当前报告版本的反馈、提交 review batch、开发侧读取已提交批次、更新处理状态。鉴权、写入和令牌在服务端；静态 HTML 只带公开报告标识。无自定义身份/批量提交需求时，先用路线二验证团队流程再决定是否自建。

## 接入验收

用另一名同事账号真正走一遍：打开指定模块 → 对长图和普通图各批注一条 → 提交/发布反馈 → 开发侧完整读回 → 映射 key/设备/版本 → 修正重拍 → 同事复验。再测新模块加入不丢旧模块、多人同时反馈、提交重试、旧图批注和无权限访问。

本轮完成的是模块累积实现和官方资料调研；没有向外部上传报告、邀请同事、发送消息、创建评论、部署或验证真实多人后端。上线前需按实际选用的服务完成以上试点。
