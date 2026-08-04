# 来源与口径

## 证据优先级

| 层级 | 来源 | 可以证明 | 不能单独证明 |
| --- | --- | --- | --- |
| 1 | 开发者披露、财务报告、可验证的一方后台截图 | 指定范围内的真实下载、消费者支出或到账 | 未披露平台、地区或月份 |
| 2 | Apple App Store、Apple Lookup、开发者官网 | 身份、作品组合、平台、版本、公开价格和商业化方式 | 下载量、付费转化、收入、利润 |
| 3 | Sensor Tower、Appfigures、AppMagic、data.ai 等 | 其覆盖范围内的第三方下载或收入估算 | Apple 官方结算、未覆盖平台和站外收入 |
| 4 | Appdex 等聚合或校准站点 | 粗粒度数量级与第二来源校验 | 精确月收入或完整 Studio 总额 |
| 5 | 排名、评分数、评论、社媒热度 | 活跃度和趋势线索 | 可直接换算的当月收入 |

优先使用原始页面。每次分析都重新确认第三方页面对 gross/net、最近 30 天/自然月、全球/单国、iOS/Mac 的定义，不依赖本文件保存的旧口径。

## Apple 数据

- Lookup URL：`https://itunes.apple.com/lookup?id=ID&country=us`。
- Apple 官方示例：`https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/LookupExamples.html`。
- 通过开发者 `artistId` 加 `entity=software&limit=200` 可枚举当前 storefront 返回的作品。
- `software` 与 `mac-software` 分开统计。地区下架、旧产品和 API 未返回条目可能缺失。
- `price=0` 或 `formattedPrice=Free` 只表示下载免费，不代表没有内购、订阅或广告。
- App 页面显示的内购价格受 storefront、试验和时间影响；记录观察日期。

## 第三方估算

读取页面时保存原始措辞，例如：`last month`、`past 30 days`、`<$5k`、`$500-$1k`。不要把不同写法自动视为相同月份。

- Publisher 级数据通常优先于逐 App 相加，因为它可能已经处理组合覆盖；仍需检查是否仅含 mobile。
- App 级区间可以定位头部产品。只有确认产品集合互不重叠、口径相同时才能求和。
- 同一底层数据供应商的多个网站不算真正独立来源。
- 页面未显示收入、需要付费或仅在搜索摘要出现时，标记为不可验证。

## 收入口径

- **Consumer spend / gross IAP revenue**：消费者在商店内支付的金额，通常是第三方收入估算的默认口径，但必须核对来源定义。
- **Developer proceeds**：gross 扣除平台佣金、适用税费、退款等后的开发者到账。必须列出费率假设。
- **Profit**：proceeds 再扣服务器、获客、工资、退款、公司税等成本。没有成本证据时不估算。
- **广告、Web、企业授权、其他商店**：通常不在 App Store IAP 估算内。存在迹象但无法量化时作为未覆盖收入单列。

## 区间纪律

- `<X` 写成 `[0, X)`，不能默认中点。
- `>X` 写成 `(X, 无上界]`，不能私设上界。
- 来源区间无交集时报告冲突；除非有明确权重依据，否则不平均。
- 只有间接指标时，可列低/中/高情景及每个显式假设，但结论标为 D；假设不是证据。
- 对外汇换算注明汇率来源、日期和四舍五入规则。
