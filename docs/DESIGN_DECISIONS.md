# AutoDev Studio — 设计决策总表

> 最后更新: 2026-06-23  
> 版本: V1.0.0  
> 决策数: 54  
> 其中 #34–#54 来自 `/grill-me` 三步管线深度访谈  

---

## 产品定位

| # | 决策 | 结论 |
|---|------|------|
| 1 | 首要用户 | **D — 全覆盖平台**：应用层/底层/系统/安全工程师统一平台 |
| 2 | 路由触发方式 | **自动推荐 + 每步人工可覆盖**：系统推荐 Agent/Workflow 链，用户确认 |
| 3 | 上传入口 | **需求文档 + 源码文件 + 自然语言指令**，三种混合 |
| 4 | 工程模式 | **C — 项目级会话**：多文件多轮对话，上下文累积 |
| 5 | 工程结构 | **Agent 任务节点树**：工程 = 多个 Agent 节点，每节点挂固定交付物 |

## 路由

| # | 决策 | 结论 |
|---|------|------|
| 6 | 匹配逻辑 | **AgentRouter 粗筛 + LLM 精排**（由 #37 细化）：AgentRouter 先做领域关键词+能力匹配过滤到 ~5 个领域（毫秒级），LLM 在过滤后的领域内做 3 选 1 + Agent 排序。文件类型仅在 AgentRouter 粗筛阶段使用。 |
| 17 | 路由第一步 | **AgentRouter 粗筛 → LLM 精排**（#37 对齐）：AgentRouter 先用 parse_task() 提取 metadata（领域关键词、标准、工具、ASIL 等级），过滤到 ~5 个候选领域；LLM 在候选领域内完成 3 选 1 + Agent 排序。用户可配置自己的 API key。 |

## 执行模型

| # | 决策 | 结论 |
|---|------|------|
| 7 | 节点启动方式 | **B — 手动启动单个**：Agent 节点创建后待执行，用户点击运行 |
| 8 | 执行模式 | **B — 后台异步执行**：节点状态灯（⏳🟢✅❌），可并行多节点 |
| 9 | Workflow 步骤 | **C — 可配置确认点**：关键决策步骤暂停等用户确认，纯生成步骤自动跑 |
| 21 | 确认点交互 | **C — 可编辑+追问**：中间输出可编辑，聊天输入框可追问 Agent |
| 22 | 追问机制 | **A — Agent 会话内续接**：确认点暂停不关闭会话，追问直接注入上下文 |

## 工程持久化

| # | 决策 | 结论 |
|---|------|------|
| 10 | 持久化方案 | **A — 纯本地文件**：工程文件夹 = Agent 节点目录 + 交付物文件 |

```
my-project/
├── .autodev/project.json
├── 01-需求分析/需求规格分析报告.md
├── 02-ADAS感知管道/sensor_fusion.c
└── 03-功能安全/HARA分析报告.md
```

## 上下文管理

| # | 决策 | 结论 |
|---|------|------|
| 18 | 上下文传递 | **B — 显式手动选择**：启动 Agent 时弹出上下文选择面板，预勾选上游节点输出 |

## GUI

| # | 决策 | 结论 |
|---|------|------|
| 11 | 布局 | **三栏布局 + 顶部折叠输入栏**：左栏工程树，中栏 Agent 执行面板，右栏交付物查看 |
| 20 | 技术栈 | **A — Electron + Vue**：复用 Apix CLIENT 的 Electron 骨架 |
| 23 | Apix 复用策略 | **C — 混合**：复用 CLIENT 的 Electron+Vue 框架，后端 FastAPI 全新写 |
| 24 | Apix CLIENT | **保留**：main/index.js, wsClient.js, preload, Vue入口, mdDisplayer, file_panel, 消息气泡, 图标资源。**改造**：IPC通道改为 agent_exec。**去掉**：登录注册, MCP/RAG/Role/Skill 卡片, Task 页面 |
| 25 | 项目目录 | **B — `autoagent/autodev-studio/`** 源码，参考项目保留不动 |
| 26 | 后端启动 | **A — Electron 内嵌 spawn**：首次运行自动引导 pip install |

## 后端架构

| # | 决策 | 结论 |
|---|------|------|
| 12 | 通信方式 | **B — 单一 FastAPI 服务**：HTTP REST + WebSocket |
| 13 | 执行引擎 | **多 provider LLM 适配层**（#47 对齐）：不沿用 Apix 的 LangGraph。支持 OpenAI、Anthropic、Google、DeepSeek、Custom Provider，用户通过 `api_key` + `base_url` 或 `.env` 配置。SDK Client V1 为模拟器，后续替换为真实 LLM 调用。 |
| 14 | Agent→Skill 加载 | **构建时预编译 + 运行时按需下载**：manifest 记录 Agent→Skill 映射，执行时只下载当前 Agent 依赖 |
| 16 | 后端模块 | 见下方模块划分 |
| 27 | 数据模型 | 见下方 agent_skill_manifest.json 结构 |

### 后端模块划分

```
autodev_backend/
├── routers/           # project.py, agent.py, routing.py (AgentRouter 集成), file.py, websocket.py, audit.py
├── agent_engine/      # agent_runtime.py, agent_router.py (粗筛), pipeline.py (三步编排), skill_loader.py,
│                      #   manifest.py, step_checkpoint.py, output_stream.py
├── vector_store/      # embedding.py (text-embedding-3-small), vector_db.py (sqlite-vec), chunker.py
├── llm/               # adapter.py (多 provider 统一接口), providers/ (openai, anthropic, deepseek, google, custom)
├── sdk_adapter/       # yaml_converter.py, sdk_client.py (V1 模拟器)
├── project_store/     # project_manager.py, node_state.py
└── shared/            # models.py, state.py
```

## Agent→Skill 数据模型

| # | 决策 | 结论 |
|---|------|------|
| 15 | manifest 构建 | **CI 预构建**：`agent_skill_manifest.json` 随安装包分发 |
| 19 | Skills 下载源 | **B — GitHub 直读 + 本地缓存**：manifest 记录 commit SHA 做版本控制 |

### `agent_skill_manifest.json` 结构

```json
{
  "agents": {
    "perception-engineer": {
      "domain": "adas",
      "agent_file": "agents/adas/perception-engineer.yaml",
      "capabilities": ["camera-object-detection", "radar-signal-processing", ...],
      "required_skills": [
        "skills/adas/perception/camera-image-processing.yaml",
        "skills/adas/perception/radar-signal-processing.yaml",
        ...
      ],
      "tool_dependencies": ["carla_adapter", "tensorrt", "opencv", "pcl"]
    }
  }
}
```

## 生态仪表盘

| # | 决策 | 结论 |
|---|------|------|
| 28 | 位置 | **A+E — 启动首页 + 顶部 Tab 可切回** |
| 29 | 内容 | **B — 静态图谱 + 工程实时状态着色**：灰色=未启动，🟢=运行中，✅=完成，❌=失败 |
| 30 | 可视化库 | **Cytoscape.js**：图分析能力内置，路径高亮天然支持 |
| 31 | 数据来源 | **CI 预编译 `ecosystem_graph.json`**：4 类节点（Agent/Skill/Workflow/Command）+ 3 种边（calls/orchestrates/uses） |

## V1 范围

| # | 决策 | 结论 |
|---|------|------|
| 32 | V1 Agent 规模 | **Manifest 含 219 Agent / 25+ 域 / 4731 Skills**。预装 5 域 9 Agent（见下方表格）。仪表盘展示全部 Agent 生态图谱，未安装的灰色标记。 |

| 域 | Agent | Skills |
|---|---|---|
| ADAS | perception-engineer, control-engineer, planning-engineer | ~25 |
| Functional Safety | hara-specialist, fmea-analyst, safety-case-writer | ~15 |
| SOTIF | sotif-analyst (自建) | 15 |
| AUTOSAR | architect | ~10 |
| Diagnostics | diagnostic-engineer | ~8 |

## 交付时间线

| # | 决策 | 结论 |
|---|------|------|
| 33 | 节奏 | **4 阶段** |

| 阶段 | 内容 | 交付物 | 状态 |
|---|---|---|---|
| **P1: 骨架** | Electron+Vue 框架、三栏布局、工程管理器、文件持久化、FastAPI 服务壳、SDK适配层、manifest 编译管线 | 可启动桌面应用壳 | ✅ 完成 |
| **P2: 路由+执行** | AgentRouter 粗筛引擎、LLM 精排（三步管线 Step 1）、YAML→SDK 转换、WebSocket 流式输出、Workflow 确认点+追问 | 路由+执行闭环 | 🟡 进行中 |
| **P3: 知识库+管线** | SQLite 向量存储、嵌入预构建、知识库检索（三步管线 Step 2）、pipeline.py 编排层、LLM 多 provider 适配层 | 三步管线端到端 | ⬜ 待开始 |
| **P4: 仪表盘+闭环** | 生态关系图谱、工程状态实时着色、上下文选择面板、交付物预览、纵向切片验证 | V1 完整可用 | ⬜ 待开始 |

## 三步智能路由管线 — Grill-Me 会话决策 (2026-06-23)

> 通过 `/grill-me` 深度访谈产出，逐项推敲每个架构分支。管线整体描述：
> 每个用户输入经过三次 LLM 调用：
> 1. 相关性判断 → 选出最优 Agent
> 2. 生成嵌入查询 → 向量检索知识库
> 3. 组装上下文 → Agent 执行并产出结果。

| # | 决策 | 结论 |
|---|------|------|
| 34 | **管线架构** | **三步 LLM 管线**：Step 1 领域筛选+Agent精排 → Step 2 嵌入查询+向量检索 → Step 3 Agent执行。非三个独立执行分支，Step 1+2 只为 Step 3 组装提示词，最终只有一个 Agent 执行 |
| 35 | **Step 1 输入** | **仅输入 25 个领域名称**给 LLM 做 3 选 1，不附带 Agent 描述 |
| 36 | **Step 1 领域内 Agent 选取** | **LLM 做 relevance ranking**，取与用户输入相关度最高的 5 个 Agent（非简单字段过滤） |
| 37 | **AgentRouter 与 LLM 分工** | **B — AgentRouter 粗筛 + LLM 精排**：AgentRouter 先用领域关键词+能力匹配过滤到 ~5 个领域（毫秒级），产出 metadata（检测到的标准、工具、ASIL 等级）喂给 LLM，LLM 在 5 个领域内做 3 选 1 + Agent 排序 |
| 38 | **Step 2 嵌入查询形态** | **C — LLM 自由发挥**：输入用户需求 + Agent 概述，产出 2 条自然语言描述，目标最大化知识库检索覆盖面和精度 |
| 39 | **嵌入模型** | **OpenAI text-embedding-3-small（512 维）**：中英混合强，$0.02/1M tokens，127 篇文档嵌入总成本 <$0.01 |
| 40 | **向量存储** | **SQLite + sqlite-vec**（非 Milvus/Qdrant）：单文件嵌入 Electron 桌面应用无外部依赖，检索 <10ms；507 篇规模不需要分布式向量库 |
| 41 | **分块策略** | **按文档 5 级结构分块**：1-overview / 2-conceptual / 3-detailed / 4-reference / 5-advanced，每个层级自然独立语义块，127 文件 → ~500 向量 |
| 42 | **嵌入构建时机** | **A — 启动时预构建**：启动时一次性嵌入全部 MD 文件写入 SQLite，总时间 <30s，后续只读不写 |
| 43 | **知识库缺失处理** | **A（不限制领域）+ LLM 参数化知识兜底**：管线不限制用户输入任何领域，第三步知识库无命中时 LLM 用自身参数化知识回答 |
| 44 | **Step 3 执行模式** | **混合：A 为主 + B 做安全兜底**：ADAS/AUTOSAR/诊断等分析型 Agent 用 System Prompt 直调（一次 chat completion）；功能安全/网络安全/SOTIF 等有合规要求的 Agent 走 Workflow + Checkpoint 逐步执行 |
| 45 | **第三步 Tool Use** | **暂不作为独立模式**：目前 Agent 的 `tool_dependencies` 指向商业工具（CANoe、Medini Analyze），MCP 集成未做。后续作为 A 的可选增强 |
| 46 | **LLM 模型分层策略** | **前两步便宜模型 + 第三步按需升级**：Step 1（领域筛选）和 Step 2（生成嵌入查询）用轻量模型（DeepSeek-V3 / GPT-4o-mini）；Step 3 根据任务复杂度选择中等或最强模型（Opus / GPT-4o） |
| 47 | **LLM 适配架构** | **B — 多 provider 可切换**：用户通过 `api_key` + `base_url` 或 `.env` 接入任意 LLM；支持 OpenAI、Anthropic、Google、DeepSeek、Custom Provider |
| 48 | **Agent 级 LLM 绑定** | **B 为主 + C 的步骤级默认值**：Step 1/2 全局设定默认轻量模型；Step 3 每个 Agent 可绑定自己的模型，未绑定的继承全局默认 |
| 49 | **LLM 绑定 UI** | **运行时下拉选择**：在 workspace 调用 Agent 时下拉框选择已配置的 LLM provider + model，不做全局 Agent 模型映射表（太繁琐） |
| 50 | **管线编排位置** | **B — `backend/agent_engine/pipeline.py`** 作为独立编排模块：三步之间有状态传递，前端不应该管流程控制；可被 HTTP 和 WebSocket 端点复用 |
| 51 | **UI 触发入口** | **C 为主 + A 做补充**：主流程 = 创建 Agent 节点时输文字描述任务 → 管线自动匹配 Agent（替代手动浏览 Agent 市场）；辅流程 = 已创建节点的右侧面板输入新指令重新分析 |
| 52 | **异步执行方式** | **B — 同步 HTTP + 确认点 + 现有 WebSocket**：`POST /routing/pipeline/prepare` 同步返回推荐 Agent + 知识库加载清单 + 提示词摘要 → 用户确认 → 走现有 `/agent/execute` + `/ws/` 流式执行 |
| 53 | **实现优先级** | **A — 纵向切片**：先做通一条端到端链路（一个固定 Agent 场景走完三步管线），验证可行后再横向扩展 |
| 54 | **三方工具适配器** | **暂时不用**：`参考项目/automotive-claude-code-agents/tools/adapters/` 下的 MCP 工具适配器不在 V1 范围 |

## 三步管线架构图

```
用户输入 "Develop ISO 26262 ASIL-D ACC with sensor fusion"
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  Step 1a: AgentRouter 粗筛 (Python, <50ms)          │
│  parse_task() → metadata {domains, standards, tools} │
│  25 domains → ~5 domains (keyword + adjacency)       │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  Step 1b: LLM 精排 (轻量模型, 1-3s)                  │
│  Input: 5 domains + user input                       │
│  Output: 3 domains → max 5 agents/domain → 1 best    │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  Step 2: 嵌入查询 (轻量模型 + 向量检索, 2-4s)        │
│  LLM: user input + agent overview → 2 条查询描述      │
│  Vector: text-embedding-3-small → SQLite sqlite-vec  │
│  每条查询 max 30 hits → 合并去重 → 候选上下文          │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  用户确认 (同步 HTTP 返回)                            │
│  · 推荐 Agent: hara-specialist (conf=0.87)           │
│  · 知识库: 12 篇文档加载                              │
│  · 提示词组装摘要预览                                 │
└──────────────────────┬──────────────────────────────┘
                       │ 用户点击"确认执行"
                       ▼
┌─────────────────────────────────────────────────────┐
│  Step 3: Agent 执行 (最强模型, 10-60s+)              │
│  System: Agent YAML system_prompt + guidelines       │
│  Context: KB docs (vector hits) + rules + goals      │
│  User: 原始输入 + 候选 Agent 列表                     │
│  → WebSocket 流式输出 (/ws/{project_id}/{node_id})   │
│  → 安全 Agent: Workflow + Checkpoint 暂停确认         │
└─────────────────────────────────────────────────────┘
```

## LLM 配置模型

```python
# Step 1/2 默认轻量模型（全局设定）
default_light_model: str = "deepseek-chat"  # 或 "gpt-4o-mini"

# Step 3 默认大模型（全局设定）
default_heavy_model: str = "claude-opus-4-8"

# 运行时 Agent 绑定（workspace 调用时下拉选择）
agent_llm_binding = {
    "agent_name": "hara-specialist",
    "provider": "anthropic",        # 用户已配置的 provider key
    "model": "claude-sonnet-4-6",   # 可覆盖默认
}

# Settings 中已有的 provider 结构（扩展 model 字段）
providers = [
    {"key": "openai",   "endpoint": "https://api.openai.com/v1",          "models": ["gpt-4o", "gpt-4o-mini"]},
    {"key": "anthropic","endpoint": "https://api.anthropic.com",           "models": ["claude-opus-4-8", "claude-sonnet-4-6", "claude-haiku-4-5"]},
    {"key": "google",   "endpoint": "https://generativelanguage.googleapis.com", "models": ["gemini-2.5-pro", "gemini-2.5-flash"]},
    {"key": "deepseek", "endpoint": "https://api.deepseek.com",            "models": ["deepseek-chat", "deepseek-reasoner"]},
    {"key": "custom",   "endpoint": "Custom endpoint",                     "models": []},  # 用户手动输入 model name
]
```

## 知识库向量存储设计

```
启动时 (main.py lifespan):
  knowledge-base/
    ├── standards/iso26262/1-overview.md  ──→ chunk → embed → sqlite-vec
    ├── standards/iso26262/2-conceptual.md ──→ chunk → embed → sqlite-vec
    ├── ... (127 files × avg 4 levels → ~500 vectors)
    └── technologies/sensor-fusion/5-advanced.md ──→ chunk → embed → ...

检索时 (Step 2):
  LLM 产出 ["safety analysis ASIL decomposition fault tree", 
            "sensor fusion radar lidar camera redundancy"]
  → text-embedding-3-small → 2 个 512-dim 向量
  → sqlite-vec 余弦相似度检索
  → 每条查询 max 30 hits → 合并去重 → 返回 chunk + metadata
  → 按文档名分组，组装为 Step 3 上下文
```

## 更新后的用户旅程

```
打开应用 → 仪表盘首页（生态图谱全览）
  → 创建工程 "L2高速智驾系统"
  → 新建 Agent 节点 → 输入任务描述 "ASIL-D ACC with sensor fusion"
  → 三步管线自动执行：
      ① AgentRouter 粗筛 + LLM 精排 → 推荐 hara-specialist (87%)
      ② LLM 生成嵌入查询 → 向量检索加载 12 篇相关知识库文档
      ③ 用户确认 → Agent 执行 → WebSocket 实时流式输出
  → Workflow 确认点暂停（安全 Agent） → 用户编辑+追问 → 继续
  → 交付物挂到节点下 → 节点状态 ✅
  → 切回仪表盘 → 节点绿色高亮 → 查看全貌
```
