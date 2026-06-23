# AutoDev Studio — 开发状态文档

> 最后更新: 2026-06-23  
> 版本: V1.0.0-alpha  
> 设计决策: [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md)（含 `/grill-me` 三步管线决策 #34–#54）

---

## 一、项目规模

| 指标 | 数值 |
|------|------|
| 后端 Python 文件 | 23（含 `agent_router.py`） |
| 前端 Vue/JS 文件 | 32 (16 Vue 组件) |
| Manifest 编译脚本 | 1 (`build_manifest.py`) |
| 工具脚本 | 3 (`setup.sh`, `launch.sh`, `sync_agents.py`) |
| 设计文档 | 2 (`DESIGN_DECISIONS.md` 54条, `DEVELOPMENT_STATUS.md`) |
| 项目总大小 | ~12 MB |

## 二、架构总览

```
autodev-studio/
├── backend/                        23 Python 文件
│   ├── main.py                     FastAPI 入口 + 服务生命周期 + DI
│   ├── routers/                    5 路由模块
│   │   ├── agent.py               Agent 执行 + 安装 + 下载 + 域详情
│   │   ├── project.py             工程 CRUD + 节点树
│   │   ├── routing.py             AgentRouter 路由 (analyze/fan-out/consensus) + 三步管线接口预留
│   │   ├── file.py                文件上传/读/写/列
│   │   ├── websocket.py           WebSocket 实时流
│   │   └── audit.py               审计追踪
│   ├── agent_engine/              6 引擎模块
│   │   ├── agent_router.py        ⭐ AgentRouter 粗筛引擎（加权五因子打分 + Fan-Out/Fan-In + 共识构建）
│   │   ├── agent_runtime.py       Agent 生命周期管理
│   │   ├── manifest.py            Manifest 读取 + 查询
│   │   ├── skill_loader.py        Skill 按需安装 + 本地目录管理
│   │   ├── step_checkpoint.py     Workflow 状态机
│   │   └── output_stream.py       流式输出管理器
│   ├── sdk_adapter/               Claude SDK 适配层 (V1 模拟器)
│   ├── project_store/             工程文件系统 + 节点状态机
│   └── shared/                    Pydantic 模型 (含路由/管线模型) + Service Locator
│
├── knowledge-base/                ⭐ 汽车知识库 (127 文件 / 31 主题)
│   ├── standards/                 标准 (ISO 26262, ISO 21434, SOTIF, AUTOSAR, ASPICE...)
│   ├── technologies/              技术 (传感器融合, V2X, OTA, BMS, Yocto...)
│   ├── processes/                 流程 (FMEA, CI/CD, Code Review)
│   └── tools/                     工具 (CANoe, SocketCAN)
│
├── client/                        32 前端文件
│   ├── src/main/index.js          Electron 主进程 (内联 IPC + HTTP 轮询)
│   ├── src/preload/index.js       contextBridge API
│   └── src/renderer/src/
│       ├── views/                 4 页面
│       │   ├── dashboard/         DashboardPage — 已安装生态图谱
│       │   ├── agent/             AgentMarket — 域→Agents/Skills/Workflows
│       │   ├── project/           ProjectPage — 三栏工程工作区
│       │   └── settings/          SettingsPage — LLM Key + 中英文切换
│       ├── components/            12 功能组件
│       │   ├── layout/            AppLayout + CommandBar
│       │   ├── project_tree/      ProjectTree + TreeNode (状态灯)
│       │   ├── agent_panel/       AgentPanel + WorkflowSteps + OutputStream
│       │   ├── deliverable_view/  Markdown/代码预览
│       │   ├── context_selector/  上下文文件选择器
│       │   ├── file_upload/       拖拽上传
│       │   └── chat/              ChatPanel 追问界面
│       ├── store/                 Pinia: project.js + agent.js
│       ├── router/                Vue Router (Hash 模式)
│       └── i18n/                  zh-CN + en 语言包 (~300 键)
│
├── manifest/                      编译数据
│   ├── build_manifest.py          编译脚本 (纯 stdlib + argparse)
│   ├── catalog.json               完整目录 (6.9 MB, 219 agents + 4731 skills)
│   ├── preinstall.json            预装清单 (6 KB)
│   └── ecosystem_graph.json       Cytoscape 图谱 (4.8 MB)
│
├── agents/                        本地 Agent Cache (20+ files)
├── skills/                        本地 Skill Cache (136 files)
├── workflows/                     本地 Workflow Cache (11 files)
├── scripts/                       sync_agents.py + setup.sh + launch.sh
└── docs/                          设计决策 (54条) + 开发状态
```

## 三、Manifest 数据管线

### 3.1 数据源

| 仓库 | Author | GitHub Raw Root |
|------|--------|----------------|
| `automotive-claude-code-agents-main` | **Thejeswara Reddy R** | `https://raw.githubusercontent.com/im-hashim/automotive-claude-code-agents/main/` |
| `automotive-claude-code-agents` | **Yuxin ZHANG** | `https://raw.githubusercontent.com/AutoZYX-Labs/automotive-claude-code-agents/main/` |

两个仓库的关系：main = 国际基线版 (ISO 26262, ISO 21434, AUTOSAR, ASPICE 3.1)；无后缀版 = 中国增强版 (新增 GB/T 标准, SOTIF, ICV 法规, L2/L3/泊车合规, ASPICE 4.0, 硬件/软件/系统/验证域)。

### 3.2 编译输出

```
python3 build_manifest.py [--ref-main /path] [--ref-v2 /path] [--preinstall agent1,agent2,...]
```

| 输出文件 | 大小 | 内容 |
|---------|------|------|
| `catalog.json` | 6.9 MB | 219 agents + 4731 skills + 86 workflows + 192 commands, 每个含 `github_url`, `author`, `source_repo` |
| `preinstall.json` | 6 KB | 9 agents + 107 skills + 15 workflows (精简清单，安装脚本使用) |
| `ecosystem_graph.json` | 4.8 MB | 5228 nodes + 15177 edges (Cytoscape 格式) |

### 3.3 合并策略

- 同名 agent → v1 (Thejeswara Reddy R) 优先
- v2 独有 agent (22 个) → Yuxin ZHANG
- skills 全重叠，使用 v1

## 四、本地存储规范

```
agents/<domain>/<name>.yaml        # 例如: agents/adas/perception-engineer.yaml
skills/<category>/.../<name>.yaml   # 例如: skills/adas/perception/camera-object-detection.yaml
workflows/<domain>/<name>.yaml      # 例如: workflows/adas/perception-validation.yaml
```

无对应领域时自动新建目录。按域按名按 `/<domain>/<name>.yaml` 存储。

## 五、Manifest Agent 规模

| 指标 | 数值 |
|------|------|
| Agent 总数 | 219 |
| 领域数 | 25+ |
| Skills 总数 | 4731 |
| Workflows 总数 | 86 |
| Commands 总数 | 192 |
| 预装 Agent | 9（5 域） |

### V1 预装清单 (5 域 × 9 Agent)

| 域 | Agent | Skills | Author |
|---|---|---|---|
| **ADAS** | perception-engineer | 21 | Thejeswara Reddy R |
| | control-engineer | 7 | Thejeswara Reddy R |
| | planning-engineer | 21 | Thejeswara Reddy R |
| **Functional Safety** | hara-specialist | 19 | Thejeswara Reddy R |
| | fmea-analyst | 6 | Thejeswara Reddy R |
| | safety-case-writer | 6 | Thejeswara Reddy R |
| **SOTIF** | sotif-analyst | 0 (自建) | — |
| **AUTOSAR** | autosar-architect | 18 | Thejeswara Reddy R |
| **Diagnostics** | diagnostic-engineer | 13 | Thejeswara Reddy R |
| **总计** | **9 agents** | **~107 skills** | |

## 六、安装与下载逻辑

| 方式 | 触发 | 数据来源 | 存储位置 |
|------|------|---------|---------|
| **预装** | `python3 scripts/sync_agents.py` | 本地参考仓库 (读 preinstall.json) | `agents/` `skills/` `workflows/` |
| **按需下载** | Agent Market 点击 ⬇下载 | GitHub Raw URL (`/agent/download` → httpx fetch) | 同上 |
| **工程安装** | "Use Agent" 创建工程 | 从本地 cache 拷贝到工程工作区 (`~/autodev-projects/<id>/`) | 工程目录 |

## 七、前端页面完成度

| 页面 | 完成度 | 功能 |
|------|------|------|
| **Dashboard (仪表盘)** | ✅ 95% | 生态图谱 (仅已安装)、统计卡片 (Agent/Skill/WF/Domain)、最近工程、新建工程对话框 |
| **Agent Market (智能体市场)** | ✅ 95% | 45 域卡片列表 → 域详情三栏 (Agents/Skills/Workflows)、搜索过滤、下载/已安装状态、Use Agent 流程 |
| **Project Page (工程页)** | ⚠️ 60% | 三栏布局完成、工程树+Vue 组件就绪、但**端到端执行流程未打通** |
| **Settings (设置)** | ✅ 90% | LLM API Key 配置、中英文切换 (el-switch)、技能缓存管理、关于信息 |
| **i18n 国际化** | ✅ 100% | zh-CN + en 双语言包、$t() 响应式翻译、35+ 域中文映射 |

## 八、关键 API 端点

| 端点 | 方法 | 用途 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/agent/list` | GET | 列出所有 219 agents |
| `/agent/domains-detail` | GET | 域详情 (agents+skills+workflows+依赖边+installed 状态) |
| `/agent/download` | POST | 从 GitHub 下载 Agent+Skills+Workflows 到本地 cache |
| `/agent/install-to-cache` | POST | 从参考仓库拷贝到本地 cache (离线模式) |
| `/agent/install` | POST | 安装 Agent+Skills 到工程工作区 |
| `/agent/execute` | POST | 启动 Agent 执行 |
| `/agent/stop/{id}` | POST | 停止 Agent |
| `/agent/status/{id}` | GET | Agent 执行状态 |
| `/agent/checkpoint/{id}/continue` | POST | 确认点继续 |
| `/agent/checkpoint/{id}/chat` | POST | 确认点追问 |
| `/projects` | CRUD | 工程管理 |
| `/projects/{id}/nodes` | CRUD | 节点树管理 |
| `/routing/analyze` | POST | ⭐ AgentRouter 多因子路由分析（加权打分+Fan-Out+共识） |
| `/routing/fan-out` | POST | ⭐ 强制 Fan-Out 分发方案（每域最优 Agent） |
| `/routing/consensus` | POST | ⭐ 多 Agent 输出共识构建（Jaccard 聚类） |
| `/routing/suggest` | POST | `/analyze` 别名（向后兼容） |
| `/files/*` | CRUD | 文件管理 |

### 规划中的端点（三步管线）

| 端点 | 方法 | 用途 |
|------|------|------|
| `/routing/pipeline/prepare` | POST | 三步管线 Step 1+2：粗筛→LLM精排→嵌入查询→返回推荐+知识库清单 |
| `/routing/pipeline/execute` | POST | 三步管线 Step 3：用户确认后走现有 Agent 执行+WebSocket 流式 |

## 九、已知问题 & 待办

| 优先级 | 问题 | 说明 |
|--------|------|------|
| 🔴 P0 | 端到端执行流程未打通 | Agent 执行→前端交付物展示全链路未串联验证 |
| 🔴 P0 | ContextSelector/DeliverableView 未接入 | 组件存在但未挂载到工程流 |
| 🔴 P0 | 三步管线未实现 | pipeline.py 编排层、向量存储、LLM 适配层待开发 |
| 🟡 P1 | sotif-analyst 等合成 Agent 无 capabilities | manifest 中 capabilities/expertise_areas 为空，评分偏低 |
| 🟡 P1 | Web 端 0 domains | CSP + `window.autodev` 缺失 (仅 Electron 内可用) |
| 🟡 P1 | Electron HMR 断线 | Vite HMR 在 Playwright 中持续断开 (生产构建正常) |
| 🟡 P1 | Settings provider 缺少 model 选择 | 用户配置 API key 后无法选择具体模型 |
| 🟢 P2 | ELECTRON_RUN_AS_NODE 环境变量 | Claude Code VSCode 扩展设置，需 `unset` 后启动 |
| 🟢 P2 | Python 依赖安装 | `aiofiles` 移除后改用同步文件操作 |

## 十、启动方式

```bash
# 1. 编译 Manifest
cd autodev-studio/manifest
python3 build_manifest.py

# 2. 同步预装文件
cd ../scripts
python3 sync_agents.py

# 3. 启动后端
cd ../backend
pip install -r requirements.txt
python3 main.py                              # → http://localhost:5090

# 4. 启动前端 (新终端)
cd ../client
npm install
unset ELECTRON_RUN_AS_NODE
npm run dev                                   # → Electron 窗口

# 或使用一键脚本
bash scripts/launch.sh
```

## 十一、技术栈

| 层 | 技术 |
|----|------|
| 桌面框架 | Electron 37 |
| 前端 | Vue 3.5 + Pinia + Vue Router + Element Plus |
| 构建 | electron-vite + Vite 7 |
| 图谱 | Cytoscape.js |
| 后端 | FastAPI + Uvicorn + Pydantic + httpx |
| 数据 | JSON Manifest (catalog.json + preinstall.json) |
| 存储 | 本地文件系统 |
| i18n | 自建 Vue Plugin (zh-CN / en) |
