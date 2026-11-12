# AI-ROMANCE 2.0 — 第二阶段详细实施计划（v3 最终执行版）

- 前置：《项目审计报告》（已确认）、《实施计划 v1》（已审阅）、《实施计划 v2》（已审阅认可架构）
- 本版依据用户 2026-11-12 的 8 条修订要求形成，**为最终执行版，取代 v1/v2**；经用户确认后按第 12 节顺序实施
- 本次仍只生成计划，不修改代码

## 保留项与红线（不因修订而改变）

- 路线 A：微信云函数网关（chat + data 两函数），Flask 网页版冻结为历史参考。
- 四个恋爱角色及原始 System Prompt 一字不改（小雅 🌸 / 陈默 🎸 / 晴天 ☀️ / 苏沫 🌙，原文以审计报告所录为准）。
- 双模式：通用 AI 助手 + AI 恋爱伴侣，System Prompt、上下文、记忆、会话严格隔离，共用 Provider 层。
- 第一版非流式；流式为独立子阶段 2.7，未经 iOS + Android 真机验证不得标记完成。
- 不购买、不升级任何云开发套餐；不开按量付费；不产生额外付费。
- 不执行 Git 历史重写等破坏性操作；历史密钥以「吊销旧 Key」处置（用户本人在控制台操作）。
- 不擅自修改或删除现有项目功能；现有 ai-proxy 与小程序骨架作为改造基础保留。

## v3.1 修订补丁（2026-11-12，用户正式授权时提出的两项修正，本版已并入下列章节）

- **补丁 1（requestId 唯一性）**：废止「messages.requestId 二级唯一索引」设计。改为：**user 消息的主键 _id 直接等于 requestId**，requestId 字段只存在于 user 消息；assistant 消息不写 requestId、只以 inReplyTo 关联。唯一性由主键天然保证，不存在 assistant 消息缺字段的空值冲突；并发同 requestId 只有一个 add 成功，另一个收主键冲突后转查复（返回已有回复或 IN_PROGRESS)。落实于第 3.3、7.1、7.2 节。
- **补丁 2（未知结果不自动重调）**：废止 v3 的「90 秒陈旧自动接管」。新增 execState 调度标记作为可证明边界：仅 'admitted'（可证明上游从未被调用）允许服务端接管执行；'dispatched' 后结果不可知时**永不自动重调**，返回 OUTCOME_UNKNOWN 交用户主动决定（重新生成 = 用户确认可能二次计费；或放弃该条）。落实于第 3.3、7.1、7.2、13(T5)、16(R12）节。

## 修订总览（8 条 → 落实章节）

| # | 修订要求 | 落实 |
|---|---|---|
| 1 | 删除全部数据不得重置安全额度 | 第 4 节：安全计数与个人统计物理分离（system_counters 按 OPENID 哈希键，用户删数据不触及） |
| 2 | 七集合统一定义 | 第 3 节：完整数据字典（含 rate_windows、system_counters） |
| 3 | rate_windows 首次创建并发安全 | 第 5.1 节：inc→add→重试的标准 upsert 协议 |
| 4 | 额度扣减/回滚规则分清请求/成功/Token，超时不等于没费用 | 第 6 节：三本账 + 按失败类型划分的回滚矩阵 |
| 5 | chat.send 幂等（requestId） | 第 7.1 节：user 消息主键即 requestId + inReplyTo 关联（v3.1 补丁 1) |
| 6 | DeepSeek 模型 ID 先验证才能设默认 | 第 8 节：模型状态机 unverified→verified 门禁 |
| 7 | 隐私与记忆管理 | 第 9 节：记忆可查/停用/删除、角色隔离、第三方传输隐私说明 |
| 8 | send/regenerate 写入顺序与异常处理 | 第 7.2–7.3 节：两段式事务写入 + 故障矩阵 |

---

## 1. 环境与套餐核实（沿用 v2 第 1 节，结论不变）

- 官方单价：数据库 200 点/万次、容量 40 点/GB/天；云函数调用 13.3 点/万次、资源使用量 0.11108 点/GBs、外网出流量 800 点/GB。
- 微信侧免费环境 40,000 点/月、体验期六个月、不支持按量付费；CloudBase 侧免费体验版 3,000 点/月，两者勿混。用户控制台显示「微信体验版、40,000 点/月、按量付费关、自动续费关」。
- 耗尽 = 超限停服、数据保留、不产生费用；免费环境无自动扣费通道。
- ⚠️ 小程序发布上线后，免费环境到期变为上线后第 15 天——发布前必须由用户单独决策是否转付费（¥19.9/月），本计划任何步骤不含购买动作。
- 估算一次聊天 ≈0.15 资源点，资源点非瓶颈；瓶颈在第三方模型 API 余额。
- 步骤 2.0 由用户在控制台确认三项数值（到期时间、本月已用资源点、套餐名），确认前一切估算仅作参考。

## 2. 总体架构与目录（沿用 v2，局部增补）

小程序 → services 统一调用层 → 云函数 `chat`（security / context / providers）+ 云函数 `data` → 云数据库 7 集合（客户端零直连）。增补文件：

- `cloudfunctions/chat/security/quota.js`：第 6 节记账规则的唯一实现（事务预扣、结果记账、回滚）。
- `cloudfunctions/chat/security/rate-limit.js`：第 5 节分钟限流（原子 inc 协议实现）。
- `cloudfunctions/chat/services/idempotency.js`：requestId 查复/接管逻辑（第 7 节）。
- `cloudfunctions/chat/providers/catalog.js`：增加 status 状态字段（第 8 节）。
- `docs/test-evidence/`：每步证据存档（沿用 v2 第 11 节交付模板）。

---

## 3. 数据字典（修订 2：七集合统一定义）

**通用规则**：全部集合权限为「所有用户不可读写」，仅云函数可访问；云函数以 `cloud.getWXContext()` 的 OPENID 为唯一身份来源；一切按 ID 的读写先过归属校验（`_id + _openid` 联合查询，查不到统一返回 FORBIDDEN，不区分不存在与无权）；时间字段一律服务端时间。

### 3.1 users（用户档案与设置）

职责：保存用户设置；首次调用自动建档。**不承担任何计数职责。**

| 字段 | 类型 | 说明 |
|---|---|---|
| _id | String | 服务端生成 |
| _openid | String | 唯一索引 |
| settings.defaultModel | String | 仅允许取值为 catalog 中 status=verified 的模型（第 8 节） |
| settings.assistantPrompt | String | ≤2000 字，空则内置默认 |
| settings.theme | String | 界面偏好 |
| createdAt / lastActiveAt | Date | |

索引：_openid 唯一。保留：长期。清理：用户「删除全部数据」时删除（不影响第 4 节安全计数）。

### 3.2 conversations（会话）

职责：双模式会话的归属与元数据；mode 与 personaId 创建后不可变。

| 字段 | 类型 | 说明 |
|---|---|---|
| _id / _openid | String | |
| mode | String | 'assistant' / 'companion' |
| personaId | String / Null | 伴侣模式必填四角色之一；助手模式 Null |
| modelKey | String | 会话当前模型，可切换 |
| title | String | 自动生成 + 可重命名 |
| summary | String | 长会话摘要（v1 规则版，字段先行） |
| msgCount | Number | _.inc 原子维护 |
| createdAt / updatedAt | Date | 列表按 updatedAt 倒序 |

索引：(_openid, updatedAt)、(_openid, mode, personaId)。保留：直到用户删除。清理：硬删除 + 级联删 messages（分批、计数核对）。

### 3.3 messages（消息与幂等锚点）

职责：消息存储；同时充当 chat.send/regenerate 的幂等记录（不另设集合，理由：幂等窗口为分钟级，与消息同生命周期最不易不一致）。

| 字段 | 类型 | 说明 |
|---|---|---|
| _id / _openid / conversationId | String | _openid 冗余，保证一切查询可强制过滤 |
| role | String | 'user' / 'assistant' |
| content | String | ≤8000 字 |
| requestId | String | **仅 user 消息持有，且直接作为该消息的 _id**（客户端生成的 UUID，同一次发送意图的重试复用同一个）；assistant 消息不写此字段，从根本上避免唯一性冲突 |
| inReplyTo | String / Null | assistant 消息指向其 user 消息 _id（即其 requestId）；user 消息为 Null |
| execState | String | **仅 user 消息**：'admitted'（已准入、未发出）/ 'dispatched'（已发出、结果未定）/ 'completed' / 'failed' / 'unknown' / 'abandoned'（用户主动放弃的未知结果消息，不进上下文） |
| modelKey | String | assistant 消息的实际调用模型 |
| usageIn / usageOut | Number / Null | 厂商返回的实际值；未知（如超时）为 Null，**不写 0 冒充** |
| estimated | Boolean | usage 是否为估算 |
| status | String | 'ok' / 'superseded'（被重新生成取代）/ 'orphaned'（上游可能已生成但回写失败） |
| createdAt | Date | |

索引：(conversationId, createdAt)、(_openid, conversationId)、(inReplyTo)。**requestId 的唯一性由 user 消息主键（_id=requestId）天然保证**——不建二级唯一索引，也就不存在 assistant 消息缺失该字段时的空值冲突；并发同 requestId 写入时只有一个 add 能成功，另一个收到主键冲突后转入查复流程（第 7.1 节）。保留：随会话。清理：随会话级联硬删除。上下文组装只读 status='ok' 的消息（第 7.3 节）。

### 3.4 memories（长期记忆）

职责：用户可管理的长期记忆；分用户偏好与角色关系两域。

| 字段 | 类型 | 说明 |
|---|---|---|
| _id / _openid | String | |
| scope | String | 'user' / 'persona' |
| personaId | String / Null | scope='persona' 必填 |
| type | String | 'preference' / 'fact' / 'relationship' |
| content | String | ≤200 字/条 |
| enabled | Boolean | 停用后不注入、不删除（第 9 节） |
| source | String | v1 仅 'manual'；自动提取不在第一版 |
| createdAt / updatedAt | Date | |

索引：(_openid, scope, personaId, enabled)。保留：直到用户删除/停用。清理：硬删除；按角色清空只影响该 personaId 的记录。注入上限：每次 ≤10 条、总长 ≤800 字。

### 3.5 usage（个人使用统计 — 展示账）

职责：**仅**供个人中心展示（请求数、成功数、Token 汇总）；**不参与任何限流判定**，允许最终一致、允许被用户删除。

| 字段 | 类型 | 说明 |
|---|---|---|
| _id | String | 确定性：`${_openid}_${YYYYMMDD}` |
| _openid / date | String | date 为 Asia/Shanghai 日期 |
| requests / succeeded / failed / unknown | Number | 四类计数（口径见第 6 节），_.inc 累加 |
| tokensIn / tokensOut | Number | 仅汇总已知实际值；unknown 请求不计入 |
| byModel | Object | 分模型同上结构 |
| updatedAt | Date | |

索引：(_openid, date) 唯一（由 _id 保证）。保留：13 个月滚动，超期由维护步骤删除。清理：随「删除全部数据」删除——**删它不影响限流**（第 4 节）。

### 3.6 rate_windows（分钟限流计数 — 安全域）

职责：单用户分钟级请求计数，防刷；弱一致可接受（第 5.1 节协议）。

| 字段 | 类型 | 说明 |
|---|---|---|
| _id | String | 确定性：`${openidHash}_${YYYYMMDDHHmm}`（分钟粒度） |
| count | Number | _.inc 原子自增 |
| createdAt / updatedAt | Date | |

索引：_id 即主键，无需额外索引。权限：同通用规则，且**不在用户可删除范围**。清理：保留 2 天，维护步骤按 createdAt 删除旧文档（量小，不做 TTL 承诺）。

### 3.7 system_counters（安全额度计数 — 安全域，修订 1 的核心）

职责：日额度的**唯一权威账**：准入判定、全局熔断、实际消耗记账。键为 **OPENID 的 SHA-256 哈希**，不存明文 OPENID；用户删除任何个人数据都不触及本集合。

| 字段 | 类型 | 说明 |
|---|---|---|
| _id | String | 用户档：`${openidHash}_${YYYYMMDD}`；全局档：`global_${YYYYMMDD}` |
| scope | String | 'user' / 'global' |
| date | String | |
| consumed | Number | 当日已占用额度：准入时 +1，仅「未接触上游的失败」可回滚 -1（第 6 节） |
| succeeded / failed / unknown | Number | 结果三分类计数；三者之和 ≤ consumed，差额为在途请求 |
| tokensIn / tokensOut | Number | 成功响应的实际 Token（厂商返回值）累计 |
| updatedAt | Date | |

索引：_id 主键。权限：同通用规则 + **任何用户侧 action 不可写、不可删**（仅 chat 函数内部与维护步骤可操作）。保留：35 天（审计与对账），超期由维护步骤删除；删除全部数据、注销 users 档案均不影响当日计数，次日自然换新文档。

---

## 4. 安全计数与个人统计分离（修订 1）

- 两本账物理分离：**限流/额度只读 system_counters**；usage 只是展示账，写失败或被删除都不影响安全判定。
- 计数键用 openidHash 而非 users 文档：即使用户删光全部个人数据（含 users 档案）并重新建档，当日 consumed 依然存在，**额度无法被重置**。
- 「删除全部数据」的删除清单明确写死为：messages → conversations → memories → usage → users 五步，**不含 rate_windows 与 system_counters**；隐私说明中如实披露这一点（第 9 节）：安全计数以哈希形式保留至次日失效、最长 35 天后清除，不含对话内容与明文身份。
- 全局熔断读 system_counters 的 global 档，与用户档在同一次准入事务中一并校验、递增。

## 5. 限流设计（修订 3）

### 5.1 rate_windows 并发安全 upsert 协议

禁止「先查有没有、再决定 add/update」的裸写法。固定协议（最多重试 3 次）：

1. 先对确定性 _id 执行 `doc(id).update({ count: _.inc(1) })`；若 `stats.updated === 1`，自增成功，读回 count 判定。
2. 若 updated === 0（文档尚不存在），尝试 `add({ _id, count: 1, ... })`；成功则本次计数为 1。
3. 若 add 抛**主键冲突**错误（并发请求已抢先创建），回到第 1 步重试 inc——此时文档必已存在。
4. 3 次仍失败 → 返回 SYSTEM_BUSY（可重试错误），不放行、不静默通过。

该协议保证：同一分钟内并发任意多个请求，只产生 1 个窗口文档，count 精确，冲突错误不外泄为未捕获异常。

### 5.2 两级限流

- 分钟级（防刷）：rate_windows，默认 10 次/分钟，计数原子、判定在自增后（弱一致，极端并发允许多放行个位数，费用安全由日额度兜底）。
- 日级（费用）：system_counters + 事务强一致（第 6 节），默认单用户 200 次/日；全局阈值在 2.0 核实资源点后设定。

## 6. 额度记账规则（修订 4）

三本账严格区分：**请求次数**（consumed，准入占用）、**成功返回次数**（succeeded）、**实际 Token 消耗**（tokensIn/tokensOut，仅厂商返回值，未知记 Null 并计入 unknown，绝不以 0 或估算冒充实际）。

### 准入（发送前，事务内）

`db.runTransaction` 内同时处理用户档与全局档：读 consumed → ≥ 上限则中止事务返回 QUOTA_EXCEEDED → 否则两档 consumed 各 +1 后提交。判定与自增同事务完成，并发下不穿透。

### 结果记账与回滚矩阵（请求离开准入后的每种结局）

| 结局 | consumed | 结果计数 | Token | 说明 |
|---|---|---|---|---|
| 成功返回 | 保持 | succeeded +1 | 记厂商实际值（无返回则估算并标 estimated） | |
| 厂商明确拒绝（401/400/429 等有响应体） | 保持 | failed +1 | 记 0（厂商未生成，有响应为据） | 防刷口径下尝试即占用 |
| 未接触上游即失败（入参二次校验失败、模型未配置、DNS/连接建立失败——请求未发出） | **回滚 -1** | 不计 failed | 无 | 唯一允许回滚的类别 |
| **网络超时/连接中断（请求已发出）** | 保持 | **unknown +1** | **Null（未知）** | **不得认定厂商未收费**；不回滚、不自动重试上游 |
| 上游成功但回写数据库失败 | 保持 | succeeded +1（补记） | 记实际值；消息标 orphaned | 回复可能丢失但费用已发生，如实记账（第 7.2 节） |

回滚与记账均走 _.inc 原子操作；结果记账在独立短事务/原子更新中完成，不与准入共用长事务。

## 7. chat.send / chat.regenerate：幂等与写入顺序（修订 5、8）

### 7.1 requestId 幂等协议

- 客户端每次「发送意图」生成一个 UUID 作为 requestId，用户消息的重试、网络层重发、误触连点**复用同一 requestId**；regenerate 每次生成新 requestId 并带 targetMessageId。
- 查复路径（主键直读）：按 requestId 读 user 消息 doc，并校验其 _openid 与调用者一致（不一致按不存在处理并记告警日志）：
  - 不存在 → 正常准入（T1 写入 user 消息，_id=requestId、execState='admitted'）。
  - 已存在且 execState='completed' → 按 inReplyTo 取回 assistant 回复，**直接返回那对消息**（duplicated:true)，不再准入扣费、不再调上游。
  - 已存在且 execState='dispatched'（已发出、结果未定）→ 返回 IN_PROGRESS；客户端只能轮询查复，**绝不触发新的上游调用**（恢复策略见 7.2)。
  - 已存在且 execState='admitted'（可证明未发出：进程在打调度标记前中断）→ 允许服务端**接管执行**——上游从未被调用，接管不产生第二次费用。
- 并发同 requestId 提交：只有一个 T1 的 add 成功；另一个收到主键冲突后转查复路径，按当时 execState 返回已有回复或 IN_PROGRESS，不报错、不重复执行。

### 7.2 chat.send 写入顺序（固定五步）

1. 鉴权 + 入参校验（无写操作）。
2. **事务 T1**：幂等查复 → 额度准入（第 6 节）→ 写入 user 消息（新会话则同事务建 conversations 并生成标题）。任一步失败整体回滚，不留半成品。
3. 发出前先把 user 消息 execState 原子置为 'dispatched'（调度标记，恢复策略的分界线），然后调上游（期间除此之外零数据库写入）。
4. **事务/原子写 T2**（成功时）：写入 assistant 消息（_id 定为 `r_${userMsgId}` 使回写本身幂等、inReplyTo、usage）→ counters 记 succeeded 与 Token → usage 展示账累加 → conversations 的 msgCount _.inc、updatedAt 更新，并把 user 消息 execState 置 'completed'。
5. 失败时按第 6 节矩阵记账；**不写 assistant 消息**，user 消息保留，界面以该 user 消息上的「重试」触发 regenerate，避免历史里出现重复的用户消息。

**未知结果恢复策略（v3.1 补丁 2，废止 v3 的 90 秒自动接管）**：execState='dispatched' 且无回复落库时，上一次调用结果**不可知**（可能已生成并计费）——服务端**永不自动重调**。查复一律返回 OUTCOME_UNKNOWN，界面明示「上次回复结果未确认，可能已产生费用」，由用户二选一：① 点「重新生成」——用户主动发起的新调用（走 regenerate 流程，可能产生第二次费用，点击即确认）；② 点「放弃这条」——该 user 消息置 execState='abandoned'，不进上下文、历史中灰显。只有 execState='admitted'（可证明未发出）才允许服务端自动接管，无一例外。
异常兜底：T2 失败（上游已成功）→ 消息标 orphaned、counters 补记 succeeded 并写脱敏错误日志；后续查复按 OUTCOME_UNKNOWN 处理（回复内容已丢失，不自动重调），由用户决定重新生成或放弃。

### 7.3 chat.regenerate 顺序与上下文完整性

1. 校验会话与目标 user 消息归属；幂等：新版本消息的 _id 定为 `r_${genRequestId}`，先按主键查复——已存在则直接返回该版本，不重复调上游；并发同 genRequestId 时只有一个 add 成功。
2. 上下文组装规则（context 模块固定）：只取 status='ok' 消息，按 createdAt 排序；**排除** superseded、orphaned、错误占位；目标 user 消息之后的旧 assistant 回复不进上下文。
3. 上游成功后才落库：先写新 assistant 消息（status='ok'），**再**把旧回复置 'superseded'。两步之间若中断，组装规则以「同一 user 消息取最新一条 ok 回复」自愈，不产生双回复上下文。
4. 上游失败：零消息写入，旧回复保持 'ok' 原样可见，仅记 counters 的 failed/unknown。

## 8. Provider 验证门禁（修订 6）

- catalog 每个模型带 status：`unverified`（初始）→ `verified`（官方文档核对 + 真实调用成功）/ `unreachable`（探针判定不可达）/ `unconfigured`（未配 Key）。状态只能由验证步骤的实测结果推进，**代码与界面不得把 unverified 显示为可用**。
- **默认模型门禁**：users.settings.defaultModel 与会话默认模型，只能在 DeepSeek 目标模型 status 变为 verified 之后才写入；在那之前，已部署骨架中 `deepseek-v4-flash` 的默认仅为占位，2.1 的第一项产出就是核对该 ID：查 DeepSeek 官方文档现行模型名 → 用已配置 Key 做真实最小调用（max_tokens=1）→ 成功才标 verified 并确立默认；失败则按官方文档修正 ID 后复测，全程留证据。
- GPT/Claude 同规：无 Key 探针（401/400 官方响应=可达；超时/DNS/TLS=不可达；403 地区类=地区限制）+ 有 Key 后真实调用，两级都过才 verified。不可达者保持 unreachable，前端置灰明示，**不写任何模拟回复兜底**。

## 9. 隐私与记忆管理（修订 7）

- **记忆用户可控**：个人中心与各角色页提供记忆列表（按 scope/persona 分组展示），每条可查看、编辑、**停用**（enabled=false，不注入）、删除；支持「清空本角色全部记忆」与「清空全部用户偏好」，均二次确认。
- **隔离**：记忆的一切查询强制 scope+personaId 过滤；注入时只取「user 域 + 当前角色域」，角色 A 的记忆永不进入角色 B 的上下文；助手模式只取 user 域。注入条数留脱敏日志（仅计数，不记内容）供抽查。
- **隐私说明**（小程序内独立页面 + 首次聊天前一句话提示）必须写明：
  1. 对话内容会发送给你所选的第三方模型厂商（DeepSeek / OpenAI / Anthropic，逐一列名）处理，受其各自隐私政策约束；不要输入身份证号、密码等敏感信息；
  2. 数据存储于腾讯云微信云开发环境（环境 ID 明示），仅你的微信身份可访问；
  3. 四个角色均为 AI，不是真人；
  4. 你可随时删除会话、记忆与全部个人数据；安全额度计数以不可逆哈希形式保留至当日失效、最长 35 天清除，不含对话内容（与第 4 节口径一致，不隐瞒）；
  5. API Key 只存于服务端，不经过你的设备。
- 内容安全：用户输入过微信内容安全检查（云调用）后才调上游，列入 2.5 必做（发布硬要求）。

## 10. 密钥管理（沿用 v2 第 7 节）

密钥仅存云函数环境变量（chat 函数持有三家 Key，data 函数不持有）；禁止进入代码/GitHub/日志/客户端返回（chat.models 只回 configured 布尔）；每次推送前全仓密钥特征扫描，命中即中止；历史 Key 由用户吊销、新 Key 新建；.gitignore 补齐随 2.2 提交。

## 11. 流式定位（沿用 v2 第 8 节）

第一版非流式、如实标注；流式为 2.7 独立子阶段（HTTP 云函数 + 分块 + 短时令牌），iOS/Android 真机双验证通过才标记完成。

## 12. 开发顺序（v3 修订验收点）

| 步 | 内容 | 验收要点（v3 强化处加粗） |
|---|---|---|
| 2.0 | 环境与套餐核实（用户提供到期/已用/套餐名三值） | 数值有据；零购买动作 |
| 2.1 | 厂商验证：DeepSeek 文档核对 + 真实调用定默认；GPT/Claude 两级探针；HTTP 云函数探测 | **catalog 状态推进有实测证据；未验证模型不可选、不可默认** |
| 2.2 | 数据层：7 集合按第 3 节建齐 + 索引 + 权限；data 函数全 action；归属校验纯函数与单测；.gitignore | 控制台逐 action 测试；代码层越权单测；**「删除全部数据」清单不含安全域两集合（代码审查留痕）** |
| 2.3 | 网关 + DeepSeek：chat 函数、事务准入、原子限流、幂等、两段式写入 | 端到端多轮；**并发测试（第 13 节 T3/T5）；故障注入矩阵全过（T4/T8）** |
| 2.4 | 小程序骨架：目录/主题/五页/组件/services | 编译零错误；跳转走查 |
| 2.5 | 双模式 + 记忆管理 + 隐私说明 + 内容安全 | 四角色不串味；**记忆查/停用/删与角色隔离走查（T7）**；隐私页内容核对 |
| 2.6 | GPT/Claude（仅 verified 者）适配 + 目录下发 | 每家真实调用留证 |
| 2.7 | 流式子阶段 | 双真机验证 |
| 2.8 | 阶段收尾：测试报告 + 未完成清单 + 文档 | 与后续阶段衔接 |

## 13. 测试方案（v3 新增专项，编号 T1–T8 对应 8 条修订）

| # | 对应修订 | 测试方法 | 通过标准 |
|---|---|---|---|
| T1 | 1 额度不重置 | 测试账号先消耗部分当日额度 → 执行「删除全部数据」→ 再 chat.send 至上限 | 被限流的时点与删除前计数一致；system_counters 文档删除前后不变（查询留证） |
| T2 | 2 集合定义 | 按第 3 节逐项核对集合/字段/索引/权限截图；客户端代码全仓搜索 database 直连 | 无直连代码；权限均为不可直读 |
| T3 | 3 窗口并发 | 同一分钟并发 20 次请求（同账号脚本连发） | rate_windows 仅 1 个文档、count=20、无未捕获冲突错误（函数日志留证） |
| T4 | 4 记账矩阵 | 故障注入四连：无效 Key（401)、端点改不可达主机（连接失败）、慢响应触发超时、正常成功 | 四种结局的 consumed/succeeded/failed/unknown/Token 与第 6 节矩阵逐项一致 |
| T5 | 5 幂等 | 同 requestId 顺序提交 3 次 + 并发提交 2 次；杀客户端响应后重发；模拟 dispatched 后中断 | 上游实际调用 1 次（counters succeeded=1)、消息恰好 1 对、第二次起返回 duplicated；dispatched 中断场景返回 OUTCOME_UNKNOWN 且上游调用次数不增加，用户点重新生成后才产生新调用 |
| T6 | 6 验证门禁 | 2.1 留档：官方文档模型名截图/链接 + 真实调用返回 JSON；前端检查未验证模型状态 | unverified 模型不可选、不可设默认；默认模型 = 已 verified 者 |
| T7 | 7 隐私记忆 | 记忆增/改/停用/删逐项走查；角色 A 存记忆后切角色 B 对话抽查注入日志计数 | B 的注入不含 A 的记忆；停用条目不注入；隐私页五项内容齐全 |
| T8 | 8 写入顺序 | 故障矩阵：上游失败、超时、T2 写库模拟异常、regenerate 上游失败、regenerate 中断于两步之间 | 无重复消息；错误/superseded 不进上下文；regenerate 失败旧回复仍在；上下文自愈规则生效 |

通用测试（沿用 v2 第 9 节）：静态检查与密钥扫描、控制台逐 action 测试与证据存档、越权矩阵（代码层单测先行；真机层需第二个微信号，完成前持续挂「未完成」）、开发者工具走查、真机走查（2.5/2.7)。

## 14. 步骤交付模板（沿用 v2 第 11 节，每步强制）

每步报告固定五项：①修改文件清单（路径+增删改+说明）; ②测试结果（用例→期望→实际→结论）; ③证据（控制台返回 JSON 存 docs/test-evidence/步号/，或截图文件名与说明）; ④未完成事项逐条；⑤GitHub commit 哈希 + 推送前密钥扫描结果。

## 15. 修订 → 文件/模块 → 测试 映射表（交付检查用）

| 修订 | 主要文件/模块（计划路径） | 测试 |
|---|---|---|
| 1 | `chat/security/quota.js`；`data` 的 deleteAllData action（删除清单常量）；system_counters 集合定义 | T1 |
| 2 | `docs/` 数据字典（本计划第 3 节即源）；2.2 建集合步 | T2 |
| 3 | `chat/security/rate-limit.js`（upsert 协议） | T3 |
| 4 | `chat/security/quota.js`（准入事务 + 回滚矩阵）；providers 各适配器的错误分类 | T4 |
| 5 | `chat/services/idempotency.js`；`chat/services/chat-service.js`；小程序 `services/chat-service.js`（requestId 生成与复用） | T5 |
| 6 | `chat/providers/catalog.js`（status 字段与门禁）；2.1 验证步产出 | T6 |
| 7 | 小程序 `pages/profile/`（记忆管理与隐私页）；`data` 的 mem.* actions; `chat/context/memory-inject.js` | T7 |
| 8 | `chat/services/chat-service.js`（T1/T2 两段写）; `chat/context/window.js`（组装过滤规则） | T8 |

## 16. 技术风险（v2 的 R1–R11 保留，增补）

| # | 风险 | 对策 |
|---|---|---|
| R12 | 上游结果未知时（dispatched 后中断）任何自动重调都可能产生第二次厂商费用（主流厂商 chat 接口不提供幂等键） | v3.1 策略：服务端永不自动重调未知结果；仅 execState='admitted'（可证明未发出）可接管；未知结果交用户主动决定（重新生成/放弃），界面明示可能重复计费 |
| R13 | 事务准入在高并发下冲突重试增加延迟 | 个人规模可接受；分钟限流在事务之前先挡刷量 |
| R14 | requestId 唯一索引与历史骨架数据（旧 ai-proxy 无此字段）冲突 | 2.2 建索引前先清理/迁移骨架测试数据，索引设为非强制存量兼容（新写入必带） |

## 17. 本版确认点

请用户确认：(1) 第 4 节安全计数分离与删除清单；(2) 第 6 节记账与回滚矩阵（尤其「超时不回滚」口径）;(3) 第 7 节幂等与两段式写入；(4) 第 3 节七集合数据字典；(5) 其余沿用 v2 确认内容。确认后从 2.0 开始实施，每步按第 14 节模板交付。
