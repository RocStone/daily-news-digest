## 核心洞察
**这个东西在解决什么问题？** Prompt Engineering 缺乏系统化的分类框架。大多数人写 prompt 靠直觉和经验，这个仓库试图把 prompt 设计从"手艺"变成"工程"——提供一套可复用的**设计模式目录**（Pattern Catalog），类似软件工程中的 GoF 设计模式。
**核心思想一句话：** 把 prompt 拆解为"上下文声明"（Contextual Statements）的组合，每个模式由固定的声明结构定义，使 prompt 设计可教学、可复用、可组合。
**为什么有效？** 有效性来自两点：
1. **降低认知负荷**——把开放式的"怎么写好 prompt"转化为"选哪个模式+填什么槽"的结构化决策
2. **组合性**——模式之间可以叠加（比如 Persona + Cognitive Verifier + Template 三者组合），这比记忆零散技巧强得多

## 定位与对比
### 与 map 中已有文档的关系
这份文档和 map 中三篇 Meta-Prompting 文档形成了一个清晰的**层次结构**：

| 层次                     | 文档                   | 关注点                             |
| ---------------------- | -------------------- | ------------------------------- |
| **战术层（Pattern）**       | 本文 Awesome Prompting | 单次 prompt 内的结构模式——怎么写好一条 prompt |
| **策略层（Structure）**     | 清华 Meta Prompting    | 用结构模板替代 Few-Shot——怎么教模型"思考方式"   |
| **编排层（Orchestration）** | 斯坦福 Meta-Prompting   | 单模型多专家编排——怎么组织多轮调用的解题过程         |
| **迭代层（Iteration）**     | Knuth 教练模式           | 人机协作多轮迭代——怎么在复杂问题上持续逼近答案        |

**关键分野：** 本文的模式目录是**静态的、单轮的**——它教你怎么写好"一条"prompt，但不涉及多轮编排、自我反思、或动态调整。map 中的三篇文档都在解决**动态、多轮**的问题。这意味着：
- 本文的模式是**基础组件**，可以被嵌入到更高层的编排框架中
- 比如斯坦福 Meta-Prompting 的"创建专家角色"本质上就是 Persona Pattern 的自动化版本
- 清华 Meta Prompting 的结构模板可以看作是 Template Pattern + Recipe Pattern 的理论升华

### Trade-off
- **获得了**可教学性和系统性——新手可以快速上手
- **牺牲了**深度——模式目录停留在"怎么格式化指令"的层面，没有触及真正影响 LLM 输出质量的核心因素（推理策略、上下文管理、验证机制）
- 6 大类 22 个模式看似全面，实际上**缺失了最重要的几个维度**：没有 Chain-of-Thought 的系统性讨论（仅在末尾简单提及）、没有 Self-Consistency、没有 Tree-of-Thought、没有 Constitutional AI 式的约束模式

### 严格审视
这份资料的 claim 是"增强 prompt engineering"，但实际上：
- 来源论文 (arxiv 2302.11382) 发表于 2023 年 2 月，**基于 ChatGPT 早期版本**，当时的模型能力远弱于现在
- 很多模式在强模型上已经**不再需要显式声明**——比如 Cognitive Verifier Pattern（"先问澄清问题再回答"），现在的 Claude/GPT-4 级别模型默认就会这么做
- Refusal Breaker Pattern 在现代模型的安全对齐下效果大幅下降，且存在伦理争议
- 仓库 47 star、18 commits，**不是高影响力资源**，更像是一个课程笔记的整理

## 直觉建立
**类比 1：烹饪食谱书 vs 厨艺**
这份文档像是一本"基础烹饪技法大全"——教你什么是煎、炒、烤、蒸（对应 Persona、Template、Recipe 等模式）。有用，但真正做出好菜还需要理解食材特性（模型能力边界）、火候控制（temperature/采样参数）、和菜品设计（任务分解策略）。map 中的三篇 Meta-Prompting 更像是在教"菜品设计"和"厨房管理"。
**类比 2：编程中的语法 vs 设计模式 vs 架构**
- 本文 = 语法层面（if/for/while 怎么写）
- 清华 Meta Prompting = 设计模式层面（用什么模式组织代码）
- 斯坦福 Meta-Prompting = 架构层面（微服务/事件驱动怎么编排）
- Knuth 教练模式 = 敏捷开发方法论（怎么迭代交付）

**具体例子——模式组合的威力：**
假设你要让 LLM 帮你做竞品分析：
```
[Persona] Act as a senior market analyst at McKinsey.
[Cognitive Verifier] Before analyzing, ask me 3 clarifying questions about the industry scope and comparison criteria.
[Template] Use this format: | Feature | Product A | Product B | Winner | Reasoning |
[Reflection] After the analysis, list your key assumptions and potential blind spots.
[Fact Check List] At the end, list all factual claims that should be independently verified.
```
五个模式叠加，比任何单一模式都强得多。这种**组合性**是本文最有价值的贡献。

## 高价值模式的具体用法

### 高价值点 1：Input Semantics 创建个人 DSL——高频任务的终极提效
**为什么高价值：** 如果你每天都要让 LLM 做类似的事（读论文、写代码审查、整理笔记），每次都写一大段 prompt 是巨大的浪费。Meta Language Creation 让你定义缩写指令，Menu Actions 让你创建操作菜单，两者结合就是在为自己创建一个**和 LLM 交互的快捷语言**。
**场景 1：论文阅读助手 DSL**
```
从现在开始，当我输入以下指令时，按对应方式处理：

"abs <论文标题或链接>" = 用3句话总结这篇论文：问题是什么、方法是什么、结果如何
"vs <论文A> <论文B>" = 对比两篇论文的核心方法差异，用表格呈现
"hole <论文>" = 找出这篇论文方法论中最大的3个逻辑漏洞或未验证假设
"so?" = 基于我们刚才讨论的论文，告诉我这对我的研究方向意味着什么
"chain" = 基于当前论文，推荐3篇我应该接着读的论文，并解释阅读顺序的逻辑

每次执行完一个指令后，显示可用指令列表，等待我的下一个输入。
```
这样你读论文时只需要打 `abs`、`hole`、`so?` 这样的短指令，省掉每次重写 prompt 的时间。
**场景 2：代码审查 DSL**
```
定义以下快捷指令用于代码审查：

"r" = 审查我接下来粘贴的代码，关注：安全漏洞、性能问题、可读性
"r sec" = 只关注安全问题（注入、权限、数据泄露）
"r perf" = 只关注性能（时间复杂度、内存、不必要的计算）
"fix" = 基于上一次审查结果，直接给出修复后的完整代码
"explain L<行号>-L<行号>" = 解释指定行范围的代码逻辑
"test" = 为上一段代码生成单元测试

每次审查后列出发现的问题数量和严重等级。
```
**关键原则：** DSL 的指令要短（最好 1-4 个字符）、要符合你的直觉（`r` = review, `abs` = abstract），并且要包含一个"菜单回显"机制让你不用记指令。

### 高价值点 2：Tail Generation 作为手动 Agent Loop
**为什么高价值：** 这个模式表面上只是"在末尾追加一句话"，但它的本质是**把单轮对话变成多轮工作流**。在你还没用上正式 agent 框架的场景下，这是最低成本的"伪 agent"。
**场景：迭代式写作助手**
```
你是我的写作编辑。我们将迭代改进一篇文章。

每次你给出修改建议后，必须在末尾：
1. 用一句话总结当前版本的最大剩余问题
2. 给出3个选项让我选择下一步方向：
   - [A] 继续改进当前最大问题
   - [B] 换一个角度审视（换成读者/审稿人/导师视角重新评估）
   - [C] 我满意了，帮我润色定稿
3. 问我选哪个，或者我可以给新的指示

我的文章如下：[粘贴内容]
```
**场景：渐进式调研**
```
帮我调研一个技术主题。

每轮结束时：
1. 总结到目前为止我们覆盖了哪些方面（✓）和还没覆盖的方面（○）
2. 推荐下一步最应该深入的方向，给出理由
3. 问我：继续你推荐的方向 / 我指定方向 / 够了帮我整理成文档

主题：[你的调研主题]
```
这个模式的精髓在于**每轮结束时强制输出状态总结 + 下一步选项**，形成一个人工驱动的 agent 循环。没有任何框架依赖，任何聊天界面都能用。

### 高价值点 3：模式组合——更多场景范本
除了上面的竞品分析例子，再给几个针对你实际场景的组合：
**场景：论文方法论批判性审查（Persona + Flipped Interaction + Reflection + Fact Check）**
```
[Persona] 你是一个以严谨著称的 ML 审稿人，AAAI/NeurIPS 资深 Area Chair。

[Flipped Interaction] 不要直接给我审查意见。先问我以下问题：
- 这篇论文声称的核心贡献是什么？
- 实验中的 baseline 选择合理吗？
- 你觉得最弱的环节是什么？
基于我的回答，再给出你的审查意见，必须指出我遗漏的问题。

[Reflection] 在审查意见之后，列出你做出每个判断的推理依据和你可能存在的偏见。

[Fact Check List] 最后列出审查意见中所有可以被论文原文验证的事实性断言，标注 [需验证]。
```
为什么用 Flipped Interaction？因为先让你自己思考再看 LLM 的意见，能避免锚定效应——如果 LLM 先给意见，你会不自觉地被带偏。
**场景：学习新概念（Audience Persona + Recipe + Alternative Approaches + Cognitive Verifier）**
```
我要学习 [Flash Attention 的原理]。

[Audience Persona] 假设我理解标准 Attention 的 Q/K/V 计算，但不了解 GPU 内存层级。

[Cognitive Verifier] 在开始解释之前，先问我2-3个问题来判断我的具体知识盲点在哪。

[Recipe] 给出学习这个概念的完整步骤序列，从我的现有知识出发，每一步都建立在上一步之上。

[Alternative Approaches] 如果有多种理解角度（比如从硬件视角 vs 从算法视角），都列出来，标注哪个角度对我的背景最合适。
```

### 作为 AI PhD
- 这份资料本身**研究价值有限**——模式分类框架偏描述性，缺乏形式化（对比清华 Meta Prompting 用范畴论形式化 prompting）
- 但可以作为**教学素材**——如果你需要给非技术背景的人讲 prompt engineering，这个分类框架是很好的脚手架
- 22 个模式中，对研究最有启发的是 **Cognitive Verifier**（对应 Self-Ask 和验证式推理）和 **Reflection**（对应 Reflexion 等自我反思范式）——这两个模式背后的思想在 agent 研究中被大量使用

### 作为工具使用者
实际可执行的下一步：
1. **建立个人模式库**：从 22 个模式中挑出你常用的 5-6 个，写成自己的 prompt 模板存在 Obsidian 中
2. **重点掌握组合技**：单一模式价值有限，模式组合才是真正的杠杆点。上面竞品分析的例子就是一个范本
3. **和 map 中的框架对接**：把这些基础模式作为"原子操作"，嵌入到 Meta-Prompting 的编排框架中使用

### 知识连接
```
已有知识体系中的位置：
├── Prompting 理论
│   ├── 基础模式（本文）← 你在这里
│   ├── 结构模板 Meta Prompting（清华）
│   ├── 多专家编排 Meta-Prompting（斯坦福）
│   └── 迭代教练模式（Knuth）
├── Agent 架构
│   ├── ReAct（本文末尾提及，但未深入）
│   ├── Reflexion = Reflection Pattern 的 agent 化
│   └── Self-Ask = Cognitive Verifier Pattern 的 agent 化
└── 实际应用
    └── 模式组合 → 个人 prompt 模板库
```

## 非显而易见的东西
**大多数人会忽略什么？**
1. **模式的组合性**比模式本身重要 10 倍。大多数人会逐个学习模式，但不会想到把 5 个模式叠加在一条 prompt 里
2. **Input Semantics 类（Meta Language Creation + Menu Actions）被严重低估**——这两个模式本质上是在**创建人机交互的 DSL（领域特定语言）**，对于高频重复任务，这比任何其他模式都省时间
3. **Tail Generation Pattern 看似最无聊，实际上是 agent loop 的雏形**——"在末尾问我下一步要做什么"就是最原始的 agent 循环

**反直觉的点：**
- 论文声称有 16 个模式（本仓库整理为 22 个含变体），但实际上**真正独立的思想只有 4-5 个**：角色设定、结构约束、交互控制、自我验证、上下文管理。其余都是这些核心思想的具体化
- 越来越多的模式正在被**模型内化**——随着模型能力增强，显式 prompt 模式的边际价值在递减。2023 年需要写 "think step by step" 才能触发 CoT，现在的模型（尤其是推理模型如 o1/DeepSeek-R1）已经默认就会这么做

**六个月后回看：**
- **最可能被验证的**：模式组合的思路会持续有效，因为它本质上是在做信息压缩和约束优化
- **最可能被推翻的**：具体模式的"最佳实践"写法会大幅变化——随着模型理解能力增强，很多冗长的 contextual statements 会被更简洁的指令替代。另外，Refusal Breaker 这类模式可能会被彻底淘汰或被视为不当使用
