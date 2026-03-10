# MetaPrompts：跨平台AI编码助手定制框架深度分析

https://github.com/JBurlison/MetaPrompts


## 一、这个项目到底是什么
MetaPrompts 不是一个传统意义上的"库"或"框架"，它是一套**AI编码助手定制文件的模板系统**，核心产物是一个叫 `ai-builder` 的 meta agent——一个**专门用来创建和管理其他 AI agent 的 agent**。
它解决的问题是：当你使用 GitHub Copilot、Claude Code、Codex、OpenCode 等 AI 编码助手时，如何**系统性地组织和定制**这些助手的行为，而不是每次对话都从零开始 prompt。

## 二、核心架构：四种定制文件类型
这个框架定义了四种文件类型，每种有明确的角色分工：

| 类型              | 文件格式               | 类比        | 核心用途                       |
| --------------- | ------------------ | --------- | -------------------------- |
| **Agent**       | `.agent.md`        | 团队中的专家成员  | 交互式AI人格，有特定专长和行为           |
| **Skill**       | 目录下的 `SKILL.md`    | 参考手册      | 可复用的知识和流程，多个agent共享        |
| **Prompt**      | `.prompt.md`       | 表单模板      | 一次性任务模板，用 `/promptname` 触发 |
| **Instruction** | `.instructions.md` | 贴在墙上的编码规范 | 基于文件类型自动应用的规则              |

文件组织结构（跨平台统一）：
```
<provider>/                          # .github/, .claude/, .codex/ 等
├── copilot-instructions.md         # 全局always-on指令
├── agents/
│   ├── my-agent.agent.md           # 用户可调用的agent
│   └── helper.subagent.agent.md    # 子agent（工作流组件）
├── skills/
│   └── my-skill/
│       ├── SKILL.md                # 必需
│       ├── scripts/                # 可选 - 可执行代码
│       ├── references/             # 可选 - 参考文档
│       └── assets/                 # 可选 - 模板等静态资源
├── prompts/
│   └── my-prompt.prompt.md
└── instructions/
    └── python.instructions.md
```
**关键设计决策：** 不同 provider 只是 base folder 不同（`.github/` vs `.claude/` vs `.codex/`），内部结构完全一致。这意味着你写的定制文件可以跨平台复用。

## 三、核心思想：为什么它有效
### 3.1 Prompt 的结构化和持久化
传统做法是每次对话手写 prompt，问题是：
- **不可复用**：下次对话要重新写
- **不一致**：每次 prompt 质量参差不齐
- **不可协作**：团队成员无法共享 prompt 经验
MetaPrompts 把 prompt 从"一次性对话"变成了**版本控制下的代码资产**。你可以 git commit、code review、团队共享。
### 3.2 关注点分离（Separation of Concerns）
四种文件类型的划分对应了不同的"变化轴"：
- **Agent**: 行为人格变化（我需要一个安全专家 vs 数据库专家）
- **Skill**: 知识变化（同一份 Python 最佳实践可以被多个 agent 引用）
- **Prompt**: 任务变化（创建 React 组件 vs 做安全审查）
- **Instruction**: 上下文变化（编辑 .py 文件时自动应用 PEP8 规范）
这和软件工程中的 MVC、微服务等思想一脉相承——**把变化的原因分开，减少耦合**。
### 3.3 渐进式上下文加载（Progressive Disclosure）
Skill 的设计特别精巧，它有三层加载机制：

| 层级      | 内容                             | 加载时机           | 大小目标          |
| ------- | ------------------------------ | -------------- | ------------- |
| Level 1 | name + description             | 启动时（始终加载）      | ~100 tokens   |
| Level 2 | SKILL.md body                  | 当描述匹配当前任务时     | < 5000 tokens |
| Level 3 | scripts/, references/, assets/ | 按需（agent主动引用时） | 不限            |
这意味着你可以安装很多 skill 而不会撑爆 context window。只有相关的内容才会被加载。这本质上是一种**注意力管理机制**——对 LLM 有限的 context window 做高效分配。
## 四、Agentic Workflow：编排器+子agent模式
这是整个框架中最有技术含量的部分。
### 4.1 基本模式
```
[Orchestrator] --#runSubagent--> [Sub-Agent A: 需求收集]
       │
       ▼ （收集输出，转发问题）
[Orchestrator] --#runSubagent--> [Sub-Agent B: 尽职调查]
       │
       ▼
[Orchestrator] --#runSubagent--> [Sub-Agent C: 规划]
       │
       ▼
[Orchestrator] --#runSubagent--> [Sub-Agent D: 实现]
       │
       ▼
[Orchestrator] --#runSubagent--> [Sub-Agent E: 审查]
```
### 4.2 推荐的开发流程
```
Requirements → Due Diligence → Plan → Implement → Review
```
每个阶段对应一个子 agent，工具权限严格隔离：
- 需求收集/尽职调查/规划阶段：**只读工具**（search, fetch, usages）
- 实现阶段：**编辑工具**（editFiles）
- 审查阶段：**读 + 有限编辑**
### 4.3 Question Relay Rule（问题中继规则）
这是一个非常重要的设计约束：
**子 agent 不能直接与用户对话。** 如果子 agent 遇到需要澄清的问题，它必须在输出中结构化地返回问题（`## Questions for User` section），由编排器转发给用户，再将用户回答传回子 agent。
```
用户 <--#askQuestions-- 编排器 <--结构化输出-- 子Agent
用户 --回答--> 编排器 --重新调用+答案--> 子Agent
```
**编排器永远不能替子 agent 回答问题或编造信息**——它是一个中继站，不是信息源。

### 4.4 四种工作流模式
**模式1：标准开发流程（推荐）**
Requirements → Due Diligence → Plan → Implement → Review
适用于功能开发，强调在实现前进行充分的尽职调查。
**模式2：Research → Design → Build**
研究 → 架构设计 → 构建。适用于需要先做调研的新技术选型。
**模式3：Triage → Specialize**
分诊 → 专科处理。适用于问题类型不确定、需要先判断再路由到合适专家的场景。
**模式4：Iterative Refinement**
生成 → 批评 → 重新生成（循环直到满意）。这是经典的 "Generator-Critic" 模式。
### 4.5 Handoff 机制
Handoff 是可选的，只在用户明确要求时才添加。它在 orchestrator 的回复结束后显示可点击的按钮，让用户手动触发下一阶段：
```yaml
handoffs:
  - label: "实施计划"
    agent: implementer
    prompt: "基于上面的计划开始实现"
    send: false   # false = 填充但不自动提交，用户可以编辑
```
`send: false` vs `send: true` 的选择决定了人在回路中的控制程度。
## 五、ai-builder：Meta Agent 的设计哲学
`ai-builder` 本身作为一个 agent，它的设计体现了几个值得学习的原则：
### 5.1 五条核心规则（Non-Negotiable）
1. **永远不要假设** - 有歧义就问，不要猜
2. **理解意图而非表面请求** - 用户要 X 可能实际需要 Y
3. **不做 Yes Man** - 指出潜在问题，挑战不当假设
4. **思考下游影响** - 边界情况、扩展性、可维护性
5. **澄清未知** - 不懂就承认，不要基于假设做决策
这五条规则要求被嵌入到每一个创建的 agent 中（domain-specific 版本）。
### 5.2 评估框架：创建前先评估
在创建任何文件之前，必须经过决策流程：
1. 这是单个任务还是多步流程？
2. 步骤间需要人类审批吗？
3. 应该自动触发还是按需触发？
4. 这是可复用知识还是行为人格？
5. 涉及多个专业领域吗？
这个"先评估后创建"的思路本身就是一种 meta-cognitive 策略。
## 六、Skill 系统的细节
### 6.1 命名规则（严格验证）
| 规则 | 合法 | 非法 |
|------|------|------|
| 只能小写 | `pdf-processing` | `PDF-Processing` |
| 不能前后缀连字符 | `my-skill` | `-my-skill` |
| 不能连续连字符 | `my-skill` | `my--skill` |
| 只能字母数字+连字符 | `data-analysis` | `data_analysis` |
| 1-64 字符 | `a` | 空或超过64字符 |
| 目录名必须和 name 字段一致 | `skills/my-skill/` → `name: my-skill` | 不匹配 |
### 6.2 Description 是关键
Skill 的 description 决定了何时被激活。好的 description 包含：
- **做什么**（能力描述）
- **什么时候用**（触发条件）
- 具体的动词和领域术语
好例子：
```yaml
description: "Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction."
```
坏例子：
```yaml
description: "Helps with PDFs."
```
### 6.3 Skill vs Instruction 的区别
| 特性 | Skill | Instruction |
|------|-------|-------------|
| 目的 | 专门能力和工作流 | 编码规范和指南 |
| 可移植性 | 开放标准，跨平台 | VS Code 特有 |
| 内容 | 指令+脚本+示例+资源 | 仅指令 |
| 作用范围 | 按需加载，任务特定 | 始终应用或按 glob 匹配 |
## 七、Agent 文件的完整属性表
```yaml
---
name: agent-name              # 标识符，默认用文件名
description: "..."            # 简短描述，显示在聊天输入框
user-invokable: true          # false = 子agent，不出现在选择器中
argument-hint: "..."          # 输入提示
tools: ['tool1', 'tool2']    # 可用工具列表
agents: ['*']                 # 可调用的子agent（* = 所有）
model: Claude Sonnet 4        # 或数组: ['Claude Sonnet 4', 'GPT-4o']
disable-model-invocation: false  # true = 阻止被其他agent调用
handoffs:                     # 可选，工作流转换按钮
  - label: "显示文本"
    agent: "目标agent"
    prompt: "传递的prompt"
    send: false               # false = 预填充，true = 自动提交
    model: "GPT-5 (copilot)"
---
```
## 八、Prompt 文件的变量系统
Prompt 文件支持多种变量：
**工作区变量：**
- `${workspaceFolder}` - 工作区根目录完整路径
- `${workspaceFolderBasename}` - 工作区文件夹名
**选择变量：**
- `${selection}` / `${selectedText}` - 编辑器中当前选中的文本
**文件上下文：**
- `${file}` - 当前文件完整路径
- `${fileBasename}` - 文件名含扩展名
- `${fileDirname}` - 当前文件的目录路径
**输入变量：**
- `${input:varName}` - 弹出输入框让用户填写
- `${input:varName:placeholder}` - 带占位提示的输入框
**实际例子——React 表单生成器：**
```markdown
---
name: create-react-form
description: Generate a React form component with validation
agent: agent
tools: ['editFiles']
---
# Create React Form Component
Generate a React form component named ${input:formName:MyForm} with:
- TypeScript
- Form validation
- Follow [coding standards](../instructions/react.instructions.md)
## Form Fields
${input:fields:Describe the form fields needed}
```
## 九、Instruction 的两种模式
### 9.1 Always-On（始终生效）
- `<provider>/copilot-instructions.md` - 全局指令，每次对话都包含
- `AGENTS.md` - 放在 workspace 根目录，多 agent 工作区共享
### 9.2 File-Based（基于文件模式匹配）
```markdown
---
name: Python Standards
description: Coding standards for Python files
applyTo: "**/*.py"
---
# Python Coding Standards
- Follow PEP 8
- 所有函数签名用 type hints
- 所有公共函数写 docstring
```
`applyTo` 支持 glob 模式：`"**/*.ts"`, `["**/*.ts", "**/*.tsx"]`, `"src/frontend/**"` 等。
**优先级：** 个人指令 > 仓库指令 > 组织级指令。
## 十、具体使用场景示例
### 场景1：团队协作的代码规范
你的团队有一套 TypeScript 编码规范。与其每次 prompt 里重复，不如：
```markdown
# .github/instructions/typescript.instructions.md
---
name: TypeScript Standards
applyTo: ["**/*.ts", "**/*.tsx"]
---
- Use TypeScript strict mode
- Prefer functional components with hooks
- Use date-fns instead of moment.js
- Error handling: always use custom AppError class
```
现在任何人在编辑 `.ts` 文件时，AI 助手自动遵循这些规范。
### 场景2：论文写作工作流
作为 PhD，你可以设计一个论文阅读和总结的工作流：
```
Orchestrator: paper-analysis
  → Sub-agent: paper-reader（提取关键信息）
  → Sub-agent: critic（批判性分析方法论）
  → Sub-agent: synthesizer（与已有知识整合）
```
### 场景3：安全审查 Prompt
```markdown
---
name: security-review
description: Perform a security review of a REST API endpoint
agent: ask
tools: ['search', 'usages']
---
Review the selected code for security vulnerabilities:
${selection}
## Check For
- SQL injection and NoSQL injection
- Authentication and authorization bypass
- Input validation issues
- Sensitive data exposure
- Rate limiting concerns
## Output Format
Findings organized by severity: Critical, High, Medium, Low.
```
## 十一、与现有方法的本质区别
### vs 直接写 System Prompt
| 维度 | 直接 System Prompt | MetaPrompts 框架 |
|------|-------------------|-----------------|
| 持久性 | 会话级，对话结束就没了 | 文件级，版本控制 |
| 复用性 | 复制粘贴 | 引用和组合 |
| 协作性 | 无 | Git 协作 |
| 上下文效率 | 全量加载 | 渐进式加载 |
| 模块化 | 单一大 prompt | 4 种文件类型分离 |
### vs CLAUDE.md / cursor rules
CLAUDE.md 和 cursor rules 本质上只是 "always-on instruction"——MetaPrompts 框架中四种类型之一。MetaPrompts 的区别在于：
1. 它有 **Agent**（带工具和行为约束的人格），而不仅仅是指令
2. 它有 **Skill**（可复用、跨 agent 的知识模块），CLAUDE.md 不支持这种模块化
3. 它有 **Prompt Template**（带变量的任务模板），CLAUDE.md 做不到
4. 它有 **Multi-Agent Workflow**（编排器+子agent），这是完全不同的抽象层次
### vs LangChain / CrewAI 等 Agent 框架
| 维度 | LangChain/CrewAI | MetaPrompts |
|------|-----------------|-------------|
| 运行环境 | 独立 Python 进程 | IDE 内嵌 |
| 抽象层次 | 代码级 agent 定义 | Markdown 声明式定义 |
| 工具调用 | 自定义工具函数 | IDE 已有工具（search, editFiles等） |
| 部署 | 需要服务器 | 零部署，放在仓库里 |
| 学习曲线 | 需要编程 | 只需要写 Markdown |
本质区别：MetaPrompts 是**声明式的**，而 LangChain 是**命令式的**。你不写代码，你写配置。
## 十二、批判性反思
### 12.1 这个框架真的有效吗？
**有效的部分：**
- 文件的结构化和持久化确实解决了 prompt 复用的问题
- 四种文件类型的分类是合理的，对应了真实的使用模式
- 跨平台的统一格式降低了迁移成本
- 渐进式加载是对 context window 限制的务实应对
**存疑的部分：**
1. **Multi-Agent Workflow 的实际效果**：编排器+子 agent 模式在 IDE 聊天场景中是否真的比单个高质量 prompt 更好？每次子 agent 调用都有额外的 token 开销和延迟。对于简单的代码编辑任务，这可能是过度工程化。
2. **Question Relay Rule 的现实可行性**：这个规则要求子 agent 结构化输出问题，编排器转发，再重新调用子 agent。这个流程每一轮都是一次完整的 LLM 调用，成本和延迟会迅速累积。在实际使用中，用户是否有耐心等待这种多轮中继？
3. **Skill 的触发机制依赖 description 的语义匹配**：这意味着如果你的 description 写得不好，skill 可能永远不会被激活。这种隐式匹配比显式调用更脆弱。
4. **声明式的局限**：Markdown 声明式定义在简单场景下很优雅，但面对复杂的条件逻辑（比如"如果代码包含 SQL 查询，先做安全审查，否则跳过"），纯 Markdown 的表达力不足。
5. **跨平台承诺的现实**：虽然文件格式统一，但不同 provider 对这些文件的解析和执行可能有差异。`.github/agents/` 在 VS Code Copilot 中是原生支持的，但在 Claude Code 中的支持程度需要验证。
### 12.2 对 AI PhD 的价值判断
**高价值：**
- **Agent 设计模式**的思考方式——编排器+子agent、Question Relay、渐进式上下文加载——这些是 agent 系统设计的通用模式，不局限于这个框架
- **Prompt 工程的工程化**——把 prompt 当代码管理的理念，对任何使用 LLM 的人都有价值
- **关注点分离在 AI 系统中的应用**——传统软件工程原则如何映射到 AI agent 系统
**低价值：**
- 具体的文件格式和属性——这些是实现细节，可能随 VS Code 更新而变化
- 具体的 provider 兼容性信息——随时可能过时
### 12.3 从第一性原理看
这个项目的核心洞察是：**AI 助手的定制化本质上是一个软件工程问题**，而不仅仅是一个 NLP 问题。所以它用软件工程的方法来解决：模块化、版本控制、关注点分离、接口设计。
但它也暴露了当前 AI agent 系统的一个基本张力：**声明式简单性** vs **运行时复杂性**。用 Markdown 写 agent 很容易，但 agent 的实际行为取决于底层 LLM 如何解释这些指令，而这是不可控的。你在 agent.md 里写的 "Never assume" 和 LLM 实际上是否会遵守，中间有一道 gap。
这个 gap 是当前所有 agent 框架（包括 LangChain、CrewAI、AutoGen）都面临的根本问题，MetaPrompts 并没有解决它，只是把问题的复杂度藏在了 Markdown 的简洁性后面。
## 十三、我自己怎么用
### 13.1 立即可用的
1. 在你的项目仓库中建立 `.claude/instructions/` 目录，把常用的编码规范写成 `.instructions.md`
2. 把常用的任务（代码审查、测试生成等）封装成 `.prompt.md` 模板
3. 用 CLAUDE.md 或 copilot-instructions.md 做全局指令
### 13.2 值得实验的
1. 用 Skill 封装你的论文阅读方法论，包含批判性分析的步骤
2. 设计一个简单的 2-3 步工作流（比如 "调研→设计→实现"），观察多 agent 编排是否真的比单个好 agent 更有效
3. 试验 Description 的不同写法，观察 skill 触发的准确性
### 13.3 不建议的
1. 不要一开始就搞复杂的 5 步工作流——先用简单的工具建立直觉
2. 不要追求跨平台——先在你最常用的一个平台上做好
3. 不要把所有知识都塞进 agent——用 skill 和 instruction 分流
## 十四、关键概念速查
| 概念 | 一句话解释 |
|------|-----------|
| Agent | 有特定专长的AI人格，可以限制工具和行为 |
| Sub-Agent | `user-invokable: false`，不能直接与用户对话，只能通过编排器 |
| Orchestrator | 管理多步工作流的agent，用 `#runSubagent` 调用子agent |
| Skill | 目录级的可复用知识模块，渐进式加载 |
| Prompt | `/slash-command` 触发的任务模板，支持变量 |
| Instruction | 基于文件 glob 模式自动应用的规则 |
| Handoff | agent 回复结束后的按钮，触发工作流转换 |
| Question Relay | 子agent的问题必须经编排器转发给用户 |
| Progressive Disclosure | 三层加载机制，避免 context window 浪费 |
| Agent Skills Standard | agentskills.io 定义的开放标准 |
