# GRDB 数据层模式

这份参考来自一个真实 Swift 应用中反复出现的 GRDB 落地模式，核心分层是 `Record + LocalDataSource + Repository`。把它当作模式目录，不要把它当成僵硬框架。

## 存储形态

### 1. 单行缓存

适用于一份 payload 总是整体替换上一份 payload 的场景。

典型结构：

- 稳定主键，例如 `"cache"`
- 一个序列化 payload 字段
- 一个抓取时间字段

原因：

- 覆盖写入就是预期行为
- 本地 API 会很简单
- repository 可以自己决定远端新数据是否要立刻替换内存状态

### 2. 按日期主键的快照

适用于每天或每个周期只应存在一条逻辑记录的场景。

典型结构：

- 文本主键，例如 `yyyy-MM-dd`
- 若干被选中项或汇总状态字段
- 如果没必要正规化，可以把数组编码成 JSON 字符串落一列

原因：

- 自然主键足够明确
- 去重逻辑简单
- repository 可以直接推导每日行为，不需要额外 join 表

### 3. 只追加历史表

适用于每一次用户动作、完成事件都需要被保留的场景。

典型结构：

- 自增主键
- 业务 id 或关联 id
- 事件发生时间
- 可选的来源字段

原因：

- 方便审计、历史展示、撤销和重算
- 避免“到底该覆盖还是新增”的歧义

如果插入后的 row id 有意义，优先使用 `MutablePersistableRecord`。

### 4. 软删除

适用于删除动作应该隐藏数据，但不该破坏历史语义的场景。

典型结构：

- `isDeleted` boolean
- 默认查询排除已删除行
- 删除操作变成 `updateAll(... set(to: true))`

原因：

- 比硬删除更安全
- 为未来撤销或后台查看留余地

## 分层放置

### Record

适合放：

- `databaseTableName`
- `Columns`
- `createTable(in:)`
- 持久化数组、UUID、payload blob 等自定义编码解码
- 很薄的 `toDomain()` 辅助

不适合放：

- 随机选择逻辑
- 启动期缓存策略
- 远端刷新规则
- 跨表派生状态

### LocalDataSource

适合放：

- `dbQueue.read` and `dbQueue.write`
- 过滤和排序查询
- count 检查
- 范围明确的批量更新或删除
- `ValueObservation`
- 仅涉及本地持久化语义的 record 到 domain 映射

判断问题：

- “这个方法能不能只用本地持久化行为来解释清楚？”

如果能，通常就应该放这里。

### Repository

适合放：

- 协调本地和远端数据
- 惰性创建派生记录
- 缓存为空时的兜底行为
- 把多条本地查询组合成一个业务结果
- 暴露 domain publisher 或 domain 方法

判断问题：

- “这个行为是在表达产品语义，而不是持久化细节吗？”

如果是，通常就应该放这里。

## Observation 放置

默认推荐：

- 把 `ValueObservation` 放在 `LocalDataSource`
- 由 `Repository` 向上暴露面向 domain 的 publisher

这样能把 GRDB 细节压在更底层，让 repository 更像业务代码。

可接受的例外：

- 现有代码库已经有少量 repository 级本地观察逻辑
- 再新增一个 local data source 抽象只是在包一层，没有澄清任何行为

这时要满足：

- 查询范围要窄
- 返回值要是 domain 值
- 观察闭包里不要混入远端刷新逻辑

## Migration 规则

- 每次 schema 变化都追加一个新 migration。
- 不要因为某张表“还很新”就直接改旧 migration。
- 只有当初始化策略确实需要时，才在建表方法里使用 `ifNotExists` 保持幂等。
- 优先增量演进，避免破坏式重写。

## 反模式

### 没有理由地存两份真相

坏例子：

- 同一个事实既存事件历史，又额外存一份可变标记行

更好的做法：

- 除非性能分析证明有必要，否则优先从历史推导当前状态

### 过胖的 Record

坏例子：

- 一个 record 同时知道表结构、推荐策略和网络兜底行为

更好的做法：

- 让 record 专注持久化，把编排逻辑往上移

### 泄漏持久化细节的 Repository

坏例子：

- repository 在整个应用里到处暴露原始 record

更好的做法：

- 在持久化边界或 repository 边界转换成 domain 类型

### 对简单本地状态过度正规化

坏例子：

- 一个很小的按日本地状态，却拆成多张表和复杂 join

更好的做法：

- 从最简单、又能匹配生命周期和查询需求的表结构起步
