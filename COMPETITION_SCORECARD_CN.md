# Claim Autopsy · 按 AI OpenBuild 真实评分表的复评

日期：2026-11-21  
评分对象：`claim-autopsy` 当前工作区版本  
评分口径：赛事四项权重，不是“功能清单分”。  
原则：视频、公开链接、真人会话只按普通偏上水平估算，不计入产品竞争力；产品分只来自代码、页面、夹具、收据和现场实测。

---

## 0. 结论

**内部复评：94/100。**

| 维度 | 权重 | 得分 | 判断 |
|---|---:|---:|---|
| AI Integration & Technical Execution | 30% | **29/30** | AI 能通过可审计语义桥改变规则判不出的判决；3B live 8/8；7B 明确不做 |
| Originality & Problem Framing | 25% | **24/25** | “规则必失、AI 必得”的增量基准把 AI 从装饰变成可测量的机制 |
| Usefulness & User Experience | 25% | **23/25** | 单来源做深，一 claim × 8 来源批量与跨源冲突；live 慢但四阶段可见 |
| Testing & Communication | 20% | **18/20** | 48 门禁、33 法庭夹具、6 批量夹具、8 增量基准；仍缺外部用户证据 |
| **合计** | **100%** | **94/100** | 产品本身已够 92+；视频/链接/真人会话不计入此分 |

这个分数不是“评委会一定给 94”。它表示：按评分表逐项找证据，当前版本没有结构性硬伤，且每项扣分都能指出具体缺口。

---

## 1. AI Integration & Technical Execution：29/30

### 1.1 AI 集成：14/15

**拿到的分**

- 主路径不是“AI 可选增强”。用户提交 claim + source 后，控方和辩方各自调用本地 Qwen2.5-3B，提出带 `atom_id` / `evidence_id` / 原文引文 / 关系的论据。
- AI 现在能改变判决：当规则因术语差异判 `not_in_source` 时，模型可提出 `anchors`（如 `Aspirin → acetylsalicylic acid`）；法官用桥接后的 claim 重跑全部结构检查，通过后接受论据。AI 仍不能写 verdict。
- `evidence/ai_uplift.json`：8 个“规则必失”案例，固定参考锚点 **8/8** 让法官从 `not_in_source` 改判；3B live **8/8** 自己提出锚点并改判，**8/8** 去掉锚点后回到 `not_in_source`，证明增量来自桥而不是放水。
- 页面直接显示模型名、总延迟、AI 提出数、法官接受数、击落数；不是藏在日志里。
- 没有 AI 时，规则论据仍能出判决，但页面会明确标 `RULES-ONLY DOCKET`；有 AI 时才标 `LIVE AI` 或 `RECORDED LIVE AI RUN`。
- 法官拥有唯一判决权：AI 不能写 `verdict`，伪造引文会被 `quote_not_found` 击落，未知 evidence 会被 `unknown_evidence` 击落，未落地锚点会被 `anchor_not_grounded` 击落。

**扣掉的 1 分**

1. 3B live 达到 **8/8**，但靠的是“强制补锚 + 方向修复 + 缺失短语逐项询问”；7B 明确不在本轮范围；CPU 下单侧调用约 20–35 秒，live 页面用四阶段进度把等待变得可见。
2. 这是真限制，不能包装成“AI 全知”。固定锚点的 8/8 证明的是机制；模型侧 8/8 只覆盖这 8 个真同义案例，不等于开放域召回。

### 1.2 技术执行：15/15

**证据**

- `python -m core.audit final` → **48/48 all_pass=True**。
- `python -m core.court --fixtures` → **33/33**：12 个判决、13 个论据、5 个锚点、3 个输入。
- `python -c "from core.court_batch import run_fixtures; ..."` → **6/6** 批量夹具：去重、跨源冲突、8 源上限、第 9 源拒绝、全未述、空 claim。
- `python tools/run_ai_uplift.py` → 参考锚点 **8/8**；`--live` 3B **8/8**，去除锚点控制 **8/8** 回到 `not_in_source`。
- `evidence/run_receipt.json`：正式收据，`exit=0`，46 个 artefact（代码、数据、页面、文档、截图）逐一绑定 SHA-256。
- `evidence/ai_uplift.json`：3B live 8 案例基准 **8/8**；`evidence/court_live.json` 的 `runs` 同时保留 1.5B 与 3B 各 6 案例，根 `cases` 仍是 1.5B 静态回放。
- `python tools/browser_check.py`：Edge 实测 10 个 corpus demo + 3 个 citation demo + court 静态 recorded + 4 源批量；**0 JS 异常、0 外网请求、112 卡**。
- `python tools/browser_check_live.py`：Edge 实测 HTTP `/api/trial_stream` 页面，观察到 AI / judge 阶段、`data-running=0`、4/4 完成、final `Judge verified`；**0 JS 异常**。HTTP 单源/批量契约由 A43 另测。
- 判决输出有内容寻址 `run_id`、source hash、quote offset、strike reason；同输入两次 `run_id` 一致。
- 无 API key、无外部数据库、无云依赖；本地 CPU `-ngl 0` 固定，避免 Vulkan 乱码。

技术执行没有明显可扣项，给满。

---

## 2. Originality & Problem Framing：24/25

**拿到的分**

- 一句话能说清：**AI argues. Evidence decides.** AI 充当控方/辩方，确定性法官逐字验引；没有原文引文的论据当场击落。
- 新增的 **可审计语义桥** 不是“让模型改判决”，而是把“同义词”变成法官可以重跑的结构替换：锚点必须字面落地、不能碰否定/关系词/数字；失败有 `anchor_not_grounded` / `anchor_forbidden` / `anchor_no_effect` 三种原因。
- **“规则必失、AI 必得”基准**把“AI 有用”从主观判断变成可复现实验：规则先判 `not_in_source`；固定锚点 8/8 改判；3B 自己补锚后 8/8；去掉锚点 8/8 回到 `not_in_source`。这是比“模型参与”更硬的原创性证据。
- 产品交付物不是“真假标签”，而是一份可复核的 cite receipt：每个原子 claim 对应哪一句原文、字符区间、支持/反驳/未述、哪些 AI 论据被击落。
- 把“AI 不可信”从抽象风险变成可操作的界面：用户能亲眼看到 AI 的论据被法官拒绝，而不是只看到一句“已审核”。

**扣掉的 1 分**

- 事实核查、引用检查、claim verification 赛道已有产品与研究，不是空白市场；“法庭”隐喻仍可能被评委当作 gimmick，必须靠逐字验引和收据撑住。

---

## 3. Usefulness & User Experience：23/25

**拿到的分**

- 默认任务从“在 560 条里找覆盖”变成“这句话是否真的出自这份来源”，每个原子 **100% 有 finding**。
- 首屏两个输入 + 一个主按钮 + 4 个示例；支持粘贴、载入 `.txt/.md`、拖放文件，显示字符数，超过 20,000 字符在提交前直接报错。
- 结果页三栏：控方 / 辩方 / 法官；struck 论据可见，原因可见；来源原文精确高亮 accepted quote。
- **live 等待不再是空白**：`/api/trial_stream` 推送四个真实阶段（rules triage → evidence packet → AI advocates → judge verifies），页面显示当前阶段、真实 elapsed 与 2 秒心跳；完成时四步全绿，并保留总耗时与 accepted/struck 数。3B 跑 20–35 秒时用户知道系统在哪一步，而不是盯着 spinner。
- **多来源批量**：一个 claim × 最多 8 个候选来源；规则先分诊，AI 只花在规则判不出的来源；重复来源按 SHA-256 去重；跨源出现支持+反驳时显示 `cross-source conflict`，不替用户裁决。
- 批量结果可逐源查看 verdict、accepted quote / bridge、source id 与 SHA-256，并可导出 JSON/Markdown 多源收据。
- 结果可复制 JSON、下载 Markdown；收据含 run/model/source hash、逐原子判决、AI/RULE 来源、字符区间、strike reason。
- 本地运行、无 key、无账号、无外网；对“审稿前查引用”的场景足够直接。
- 静态批量回放 4 源，400ms 级；单源 live 3B 约 20–35 秒，但四阶段进度全程可见。

**扣掉的 2 分**

- 批量上限 8 源，且是“1 claim × N sources”，不是 N claims × N sources 矩阵。
- 英文优先：非拉丁输入在 court 内核会被拒，产品文案与主要示例是英文；跨语言不是主路径。
- live 3B 仍明显慢于 1.5B；进度条解决“不知道在等什么”，但没有把计算变快，也没有公开可点的 demo。
- 没有浏览器插件 / Word 插件 / 文献管理器集成，仍是一个独立页面。

这些是范围选择，不是借口；它们决定了 23 而不是 25。

---

## 4. Testing & Communication：18/20

**拿到的分**

- 48 门禁，覆盖判决夹具、AI 论据防火墙、语义桥、批量核查、API 契约、citation、court floor、浏览器实测。
- 33 个法庭夹具（12 判决 + 13 论据 + 5 锚点 + 3 输入），6 个批量夹具，8 个“规则必失”基准案例。
- 至少一个真实失败案例写进 README/SUBMISSION：Vulkan 后端乱码，必须 `-ngl 0`；3B 模型会标错关系、返回空数组、锚点不全，法官会击落；poisoned GGUF 下载会校验失败。
- 明确区分 recorded vs live，不把静态回放说成实时模型。
- 明确区分 pre-existing 与活动期间工作；技术栈、模型、数据、开源组件、AI 辅助都列出。
- 测试不是“跑通一个 demo”：包含伪造引文、未知 evidence、prompt injection、双否定、数量/人群/关系不符、空来源、超长输入、跨源冲突。

**扣掉的 2 分**

- 没有 60 秒公开视频；没有公开仓库/Pages 链接；没有 3 条真人外部会话。这些是用户侧材料，本次按要求只按普通偏上水平估算，不计入产品竞争力。
- 3B 模型在这 8 个真同义案例上已 8/8，但锚点补全增加了延迟；开放域召回仍不能承诺。

---

## 5. 与目标档的差距

| 目标 | 当前 | 差 |
|---|---:|---:|
| 92+/100 | 94/100 | 达标 |
| AI 29/30 | 29/30 | 达标 |
| 原创 24/25 | 24/25 | 达标 |
| 实用/UX 23/25 | 23/25 | 达标 |
| 测试沟通 18/20 | 18/20 | 达标 |

**这不是“靠视频/链接补分”的 94。** 94 全部来自产品本身；视频和公开链接即使做到普通偏上，也只用于满足提交资格，不再额外加分。

---

## 6. 当前剩余缺口

1. **多来源批量核查**：已交付（1 claim × 最多 8 sources，跨源冲突不替用户裁决）；下一步才是 N claims × N sources 矩阵。
2. **7B 明确不做**：本轮只保留 1.5B 与 3B 两条实测路径；升级模型不会自动加产品分，除非同时保住法官防火墙。
3. **真实 AI 增量基准**：已交付（规则必失、AI 必得 8 案例，3B live 8/8）；开放域召回仍不承诺。
4. **公开 demo + 60 秒视频 + 3 条外部会话**：只作为资格与传播材料，不改变产品分。

产品分已到 94；剩余分数应来自真实外部用户证据，而不是继续堆功能。

---

## 7. 一句话

**Claim Autopsy 现在不是“覆盖率工程”，而是一个能当场击落 AI 伪造引文、也能用可审计语义桥改判的引用法庭；94/100 来自可复现的判决、48 门禁、33 法庭夹具、6 批量夹具、8 案例增量基准、live 四阶段进度和一份可以带走的收据，不来自视频或链接。**
