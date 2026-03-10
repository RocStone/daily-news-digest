link: https://arxiv.org/abs/2406.06608

**大白话：这是一本 Prompt 工程的"新华字典"——把散落在几百篇论文里的 58 种文本 Prompting 技术、40 种多模态技术、33 个术语统一编目，并附带一份 meta-analysis 告诉你哪些真有用。**

# 1. 核心洞察

## 它在解决什么问题？
Prompt 工程领域发展极快，但术语混乱、技术散落、缺乏统一分类。同一个技术不同论文叫不同名字，不同技术又用相同名字。开发者面对的是一堆碎片化的 tricks，而非一个有组织的知识体系。

**这个问题为什么重要？** 因为没有地图，你就不知道自己站在哪里、还有什么没探索过。大多数人的 prompt 技能树是随机点亮的——看到哪篇论文就学哪个技巧，完全没有全局视角。

## 核心机制一句话
用 PRISMA 系统综述方法论，对整个 prefix-prompting 文献做穷举式编目，构建出 **5 大类 × 58 技术** 的分层分类体系（taxonomy），并用 meta-analysis 验证"更好的 prompt 确实带来更好的结果"这一基本命题。

## 为什么它有价值？
不是因为它提出了新技术，而是因为它做了三件事：
1. **统一了语言**：33 个术语的精确定义，终结了社区里 "Chain-of-Thought 算不算 Few-Shot" 这类无意义争论
2. **画了全景地图**：5 大类的分类不是随意的，而是按 **信息流方向** 组织的——从"给模型看什么"（ICL）到"让模型怎么想"（Thought Generation）到"把问题怎么拆"（Decomposition）到"多条路怎么合"（Ensembling）到"结果怎么改"（Self-Criticism）
3. **提供了选择依据**：meta-analysis 不只是说"有用"，而是给出了不同技术在不同任务类型上的相对表现

# 2. 定位与对比

## 五大类技术的本质逻辑

| 类别                  | 核心思想        | 代表技术                                                 | 本质操作     |
| ------------------- | ----------- | ---------------------------------------------------- | -------- |
| In-Context Learning | 给模型"看"参考答案  | Few-Shot, Role Prompting, Emotion Prompting          | 操纵输入分布   |
| Thought Generation  | 让模型"展示"推理过程 | CoT, Step-Back, Analogical Prompting                 | 展开隐式计算   |
| Decomposition       | 把大问题拆成小问题   | Least-to-Most, Tree-of-Thought, Plan-and-Solve       | 降低单步复杂度  |
| Ensembling          | 多条推理路径投票/合并 | Self-Consistency, DiVeRSe, MoRE                      | 用多样性换准确性 |
| Self-Criticism      | 让模型检查/修正自己  | Self-Refine, Chain-of-Verification, Self-Calibration | 闭环反馈     |

**关键发现**：这五类不是互斥的，而是可以**自由组合叠加**的。最强的 prompting 策略往往是跨类组合——比如 CoT（Thought Generation）+ Self-Consistency（Ensembling）+ Self-Refine（Self-Criticism）。

## 与已有笔记的关系

和你已有的笔记体系形成了一个非常清晰的层次关系：

- [[2026-03-04 Awesome Prompting：Prompt模式目录与技术分类框架深度分析]] 提出的 6 大类 22 个模式，是 **设计模式层面** 的分类（Persona、Template 等），更接近"怎么写"
- **The Prompt Report 的 58 技术**是 **算法层面** 的分类（CoT、ToT、Self-Consistency 等），更接近"怎么想"
- [[2026-03-04 斯坦福 Meta-Prompting：单模型多专家编排框架]] 的 Conductor 模式，在本文分类中属于 **Decomposition + Agent** 的组合——先拆解（Decomposition），再分配给专家角色（Role Prompting × ICL），最后综合（Ensembling 思想）
- [[2026-03-04 清华Meta Prompting：用结构模板替代Few-Shot的推理框架]] 的结构模板，本质上是将 Thought Generation 类的技术（CoT 等）从 "示例驱动" 变成 "结构驱动"——用 template 替代 exemplar
- [[2026-03-04 MetaPrompts：跨平台AI编码助手定制框架深度分析]] 的 Skill 系统，是把本文列出的这些技术 **工程化封装** 的具体方案

**一句话关系**：The Prompt Report 是你已有知识体系的**底层元件清单**，其他几篇是在这些元件之上的不同层次的**组装方案**。

## Trade-off
作为综述论文，它的 trade-off 很明确：
- **广度 vs 深度**：覆盖了 58 种技术，但每种只能给 1-2 段描述，无法深入讨论每种技术的适用边界和失败模式
- **分类完整性 vs 时效性**：论文初版 2024 年 6 月，虽然更新到 2025 年 2 月，但 2025 年之后的新技术（如更成熟的 Agent 工作流、更复杂的 multi-turn 策略）覆盖有限
- **聚焦 prefix-prompting**：明确排除了 soft prompt（连续向量优化）和 cloze prompt，这意味着 prompt tuning、P-tuning 等微调类方法不在讨论范围内

## 严格审视
论文 claim "better prompts lead to improved results" 这个 meta-analysis 结论几乎是 trivially true——如果 prompt 没用，整个领域就不存在了。更有价值的问题是 **"哪些技术在哪些条件下提升最大"**，但论文在这方面给出的定量分析偏弱。分类体系本身也存在边界模糊的问题——比如 Tree-of-Thought 既涉及 Decomposition 也涉及 Ensembling，强行归入单一类别会丢失信息。

# 3. 直觉建立

## 类比：Prompt 技术 = 思维工具箱
把 5 大类想象成你解题时的 5 种元策略：
1. **ICL = 模仿学习**：给学生看几道例题，让他模仿着做。关键变量是例题的选择（K-NN selection）和呈现方式（Role Prompting）
2. **Thought Generation = 草稿纸**：强制学生把解题步骤写在草稿纸上（CoT），而不是直接跳到答案。Step-Back Prompting 就是让学生先退一步想想"这题考的是什么知识点"
3. **Decomposition = 大纲法**：先列提纲再写文章。Least-to-Most 是从最简单的子问题开始，逐步构建到完整解答；Tree-of-Thought 是同时探索多条提纲路线
4. **Ensembling = 三个臭皮匠**：让同一个学生用不同方法解三遍，取多数答案。Self-Consistency 就是 sample 多条 CoT 路径然后投票
5. **Self-Criticism = 检查作业**：做完后回头检查。Chain-of-Verification 是先生成答案，再生成验证问题，逐一检查
这五个东西非常重要，写map的时候一定要写进去

## 具体例子：一道数学题的五层加持
问题：小明有 23 个苹果，给了小红 7 个，又买了 15 个，问还剩多少？

| 层级 | 技术 | 效果 |
|------|------|------|
| 裸 prompt | "23个苹果，给了7个，买了15个，还剩？" | 模型可能直接输出 31（正确）或犯错 |
| + CoT | "请一步一步想" | 23-7=16, 16+15=31 ✓ 展示过程 |
| + Self-Consistency | 跑 5 次 CoT 取众数 | 降低单次 CoT 出错概率 |
| + Self-Verification | 生成后反向验证 "31-15+7=23?" | 增加一层校验 |
| + Decomposition | "先算给出后剩多少，再算买入后总数" | 显式拆解，适合更复杂的问题 |

对简单题来说 1-2 层足够，但随着问题复杂度上升，叠加更多层的收益会显著增加。

## 安全维度的关键架构

论文专门讨论了 prompt 安全，值得注意的分类：
- **Prompt Injection**：在用户输入中嵌入指令覆盖系统 prompt
- **Jailbreaking**：诱导模型绕过安全限制
- **Prompt Leaking**：诱导模型泄露系统 prompt 内容
- **Package Hallucination**：模型推荐不存在的代码包（供应链攻击向量）

防御分三层：prompt 层面的防御指令、检测器（分类器判断输入是否恶意）、guardrail 系统（如 NeMo Guardrails）。

## 作为 AI PhD
1. **文献地图**：当你读到一篇新的 prompting 论文时，可以立刻在这个 taxonomy 中定位它属于哪一类、和哪些已有技术最相关、它的创新点在分类体系中的哪个缝隙
2. **研究选题**：论文的分类体系暗示了几个未被充分探索的方向：
   - 跨类组合的系统性研究（大多数论文只在单一类别内创新）
   - Decomposition 和 Self-Criticism 的自动化（目前仍需人工设计拆解策略和验证问题）
   - 多模态 prompting 的理论基础（40 种技术但缺乏统一框架）
3. **写作参考**：如果你写 prompting 相关的论文，这篇是必引的——它定义了领域的标准术语

## 作为求职者
- 面试中被问到 "prompt engineering 有哪些主要方法" 时，**五大类分类 + 每类 2-3 个代表技术** 是一个干净利落的回答框架
- 如果面试涉及 LLM 应用开发，能清晰区分 ICL vs CoT vs Ensembling 的适用场景，说明你有系统性认知

## 可执行的下一步
1. **建立个人技术索引**：不需要记住 58 种技术，但至少要对 5 大类各掌握 2-3 个核心技术的原理和适用场景
2. **在实际项目中刻意练习组合**：下次写 prompt 时，有意识地思考"我现在用的是哪一类技术？能不能叠加另一类？"
3. **关注本文没覆盖的前沿**：2025 年后的 agent 工作流、multi-turn reasoning、tool-augmented prompting 正在快速发展，这些是本文的盲区

# 5. 非显而易见的东西

## 大多数人会忽略什么？
1. **Prompt 的安全章节比技术章节更有实战价值**。大多数人读这篇论文只关注"怎么写更好的 prompt"，但 prompt injection 和 jailbreaking 的分类对任何部署 LLM 应用的人都是必修课。Package Hallucination 作为攻击向量尤其被低估——模型推荐一个不存在的 npm 包，攻击者抢注这个包名，就完成了供应链攻击
2. **Emotion Prompting 的存在暗示了一个深刻问题**：给 prompt 加上 "This is very important to my career" 能提升性能，说明 RLHF 在模型中植入了对情感信号的响应——这到底是 feature 还是 bug？它意味着模型的输出质量不仅取决于问题本身，还取决于你"看起来多重视这个问题"，这在公平性上是有问题的
3. **33 个术语定义**看似无聊，但对跨团队协作极其重要。当你的团队里有人说 "prompt chaining" 而另一个人说 "prompt pipeline" 时，统一术语可以避免大量沟通成本

## 隐含假设
- **假设 prefix-prompting 是主流范式**：排除了 soft prompt 和 cloze prompt，这在 2024 年是合理的（API 访问为主），但随着开源模型普及和微调成本降低，soft prompt 的重要性可能回升
- **假设技术之间是可独立评估的**：实际上很多技术的效果高度依赖具体模型、任务和数据，A 技术在 GPT-4 上好不代表在 Llama 上也好。论文承认了这一点但没有深入处理
- **假设 "更多技术 = 更好"**：分类越细、技术越多，实际使用中的选择成本也越高。对大多数开发者来说，掌握 5-8 个核心技术比知道 58 个名字更有价值

## 六个月后的预判
- **最可能被验证的部分**：五大类的分类框架会成为领域共识，后续论文会引用这个分类来定位自己的工作
- **最可能被推翻/过时的部分**：具体技术的排名和推荐——随着模型能力提升，很多需要精心设计 prompt 的场景会被模型自身能力覆盖（比如 GPT-4 已经内化了很多 CoT 能力，显式写 "think step by step" 的边际收益在下降）。Agent 和 tool-use 部分的分类也会被快速发展的实践超越
- **最值得持续关注的方向**：Self-Criticism 类技术——这是通向 AI 自我改进的基础设施，可能是 58 种技术中长期价值最高的一类
