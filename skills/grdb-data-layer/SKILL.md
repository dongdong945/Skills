---
name: grdb-data-layer
description: 在新增、重构或审查 Swift GRDB 数据层代码时使用，适用于本地缓存、历史记录、软删除、派生状态等场景。尤其适合在定义 Record、追加 migration、判断查询与 ValueObservation 应放在 LocalDataSource 还是 Repository，以及梳理 Record、LocalDataSource、Repository 职责边界时触发。
---

# GRDB Data Layer

## Overview

用明确分层来构建 Swift GRDB 数据层：

- `Record` 负责表结构、列名、Codable 持久化桥接，以及轻量实体映射
- `LocalDataSource` 负责 GRDB 读写、过滤、排序、批量更新删除，以及 `ValueObservation`
- `Repository` 负责业务规则、兜底行为、派生状态，以及本地与远端数据协调

当你需要具体存储形态或落地判断示例时，继续读 [patterns.md](references/patterns.md)。

## Workflow

1. 先定持久化形态

- 先判断这个功能需要的是：
  - 单行缓存
  - 只追加历史
  - 按日期或周期分片的快照
  - 支持软删除的实体
  - 由多张表共同推导的派生状态
- 优先新增一张职责单一的表，不要把新语义硬塞进无关旧表。

2. 把职责放回正确层级

- 数据库初始化层：
  - 创建 queue 或 pool
  - 追加新的 migration
  - 注册新表，不回写旧 migration
- `Record`：
  - 定义 `databaseTableName`
  - 定义 `createTable(in:)`
  - 只有在持久化格式确实特殊时，才把编码解码逻辑放在这里
- `LocalDataSource`：
  - 暴露读写意图明确、颗粒度窄的方法
  - 把 `dbQueue.read` 和 `dbQueue.write` 放在这里
  - 默认把 `ValueObservation` 放在这里
- `Repository`：
  - 组合多条记录形成业务行为
  - 在这里决定缓存兜底、重试、日期规则、跨表语义

3. 明确选择写入语义

- 对稳定主键、可整体替换的状态，优先用 `save`。
- 对只追加历史，或者需要拿到自动生成主键的场景，优先用 `insert` + `MutablePersistableRecord`。
- 只有在查询范围明确且很窄时，才使用 `updateAll` 或 `deleteAll`。
- 只要产品可能需要撤销、保留历史、按条件过滤，就优先考虑软删除。

4. 只给真正需要联动的状态加观察

- 用 `ValueObservation` 观察行数据或本地派生状态。
- 向上发布 domain 值，不要把 SQL 细节直接暴露出去。
- 用 `catch` 或等价安全默认值明确兜底行为。

5. 检查整条链路

- 检查 migration 是否注册。
- 检查非基础类型列的编码解码是否正确。
- 检查本地层的读、写、观察查询是否闭环。
- 检查 repository 在空状态、重复写入、删除语义下是否符合预期。

## Core Rules

### 保持 `Record` 足够薄

应该做：

- 把建表、列定义、持久化编码，以及小型 `toDomain()` 放在这里
- 当 GRDB 列类型和 Swift 类型无法自然对齐时，把自定义持久化格式放在这里

不应该做：

- 不要把推荐算法放进来
- 不要把缓存策略放进来
- 不要让 `Record` 依赖远端 API 或展示层状态

### 默认把 GRDB 查询留在本地层

下面这些能力优先放 `LocalDataSource`：

- `filter`, `order`, `fetchOne`, `fetchAll`, `fetchCount`
- 批量更新或删除
- `ValueObservation`

只有当现有代码库已经有少量 repository 直连 GRDB 的模式，而且额外再包一层 `LocalDataSource` 只会徒增噪音时，才允许 repository 直接查询。即便如此，也要把查询限制在本地状态范围内，不要混入远端刷新或 UI 关注点。

### 只追加 migration，不改写历史

- 每次 schema 变化都追加一个新 migration 名称。
- 保证旧 migration 从全新安装开始仍然可运行。
- 优先增量演进或新增表，避免破坏式重写。

### 让存储形态匹配数据生命周期

- 缓存 payload：通常是一行稳定 id，加一个序列化 payload 字段
- 历史记录：通常一条事件一行，带时间戳和可选来源字段
- 按日或按周期状态：通常使用日期字符串这类自然主键
- 软删除：通常是 `isDeleted` 标记，加默认排除已删除数据的查询

## Decision Guide

优先选择最简单但匹配的方案：

- 需要离线保存一份远端 payload：
  - 用一张带稳定主键的缓存表
- 需要可撤销、可审计的事件流：
  - 用只追加行
- 需要从事件历史推导“当前状态”：
  - 在 `LocalDataSource` 或 `Repository` 中计算；除非有明确性能取舍，否则不要把同一个事实存两份
- 需要 UI 响应式联动：
  - 围绕真正驱动 UI 的那条本地查询加 `ValueObservation`

## Common Mistakes

- 把业务规则塞进 `Record`
- 把 schema 变化偷偷改进旧 migration
- 让 repository 同一个方法同时碰本地、远端和 UI 语义
- 在需要软删除时直接使用 `deleteAll`
- 明明可以低成本从本地记录推导，却还额外持久化派生状态
- 调用方需要 domain 值时仍向上暴露原始 record

## Reference Use

需要下面内容时继续读 [patterns.md](references/patterns.md)：

- 推荐的表结构形态
- `ValueObservation` 应该放在哪里
- 如何在缓存、历史、派生状态表之间做取舍
- Swift GRDB 代码里常见的反模式
