# 清华 Meta Prompting：用结构模板替代 Few-Shot 的推理框架

## 1. 资源链接
- **GitHub**：[meta-prompting/meta-prompting](https://github.com/meta-prompting/meta-prompting)
- **论文**：[Meta Prompting for AI Systems (arXiv 2311.11482)](https://arxiv.org/abs/2311.11482)
- **作者**：Yifan Zhang, Yang Yuan, Andrew Chi-Chih Yao（清华大学 & 上海期智研究院）
- **发表**：ICLR 2024 BGPT Workshop
- **项目主页**：[meta-prompting.github.io](https://meta-prompting.github.io)

> **注意区分**：这篇和斯坦福 Suzgun 的 "Meta-Prompting"（arXiv 2401.12954）是完全不同的工作。Stanford 那篇是让一个 LLM 作为 conductor 调度多个"专家角色"；本篇是用范畴论形式化"结构化模板替代 few-shot 示例"的 prompting 范式。

---

## 2. 核心思想：教模型"怎么想"，而不是"想什么"

### 一句话总结
Meta Prompting (MP) 提供一个**与具体示例无关的结构性模板**（structural template），告诉模型解题的**程序和格式**，而不是像 few-shot 那样给模型看具体的 (问题, 解答) 对。
### 直觉类比
- **Few-shot prompting** = 给学生看 3 道已解的例题，希望他"照葫芦画瓢"
- **Meta Prompting** = 给学生一份"解题方法论手册"：先做什么、再做什么、结果怎么呈现——但**不给任何具体题目**
### 为什么这样做有效？

1. **消除示例偏差**：Few-shot 示例会引入内容偏差——模型可能过度关注示例的具体数字或领域，而非推理结构本身。MP 是真正的 zero-shot，避免了这种干扰。
2. **强制结构化思维**：通过规定"先说 Let's think step by step"→"分步推理"→"用 \boxed{} 给出答案"的严格格式，模型被迫按流程走，减少跳步或胡乱推理。
3. **可复用性极强**：一个 meta-prompt 适用于整个任务类别（如所有数学题），而 few-shot 需要为不同子领域精心挑选不同示例。
4. **Token 效率**：不需要塞入多个完整的 (Q, A) 对，prompt 更短，留更多 context window 给实际推理。

---

## 3. 具体对比：Meta Prompt vs Few-Shot Prompt

### Meta Prompt（结构模板）

```
Integrate step-by-step reasoning to solve mathematical problems:

{
  "Problem": "[question to be answered]",
  "Solution": {
    "Step 1": "Begin with 'Let's think step by step.'",
    "Step 2": "Break down reasoning clearly and logically.",
    "Step 3": "End with final answer in $\boxed{...}$"
  },
  "Final Answer": "[final answer]"
}
```

关键特征：**没有任何具体的数学内容**，只有解题的结构蓝图。

### Few-Shot Prompt（具体示例）

```
Problem: Find the domain of $\frac{\sqrt{x-2}}{\sqrt{5-x}}$.
Solution: $x-2 \ge 0 \Rightarrow x\ge2$, $5-x>0 \Rightarrow x<5$. Domain is $\boxed{[2,5)}$.
---------
Problem: If $\det A = 2$, $\det B = 12$, find $\det(AB)$.
Solution: $\det(AB) = \det A \cdot \det B = 24$. Answer: $\boxed{24}$.
---------
[actual question here]
```

关键特征：需要精心挑选具体示例，示例的领域和难度会影响模型表现。
### 本质区别

| 维度 | Few-Shot | Meta Prompting |
|------|----------|---------------|
| 给模型看什么 | 具体的 (Q,A) 对 | 解题的程序结构 |
| 零/少样本 | N-shot (N≥1) | 真正的 zero-shot |
| Token 开销 | 高（多个完整示例） | 低（仅结构描述） |
| 示例选择偏差 | 有（且难以消除） | 无 |
| 跨任务复用 | 差（需要换示例） | 强（同类任务通用） |
| 本质 | "what to think" | "how to think" |

---

## 4. 理论框架：用范畴论形式化 Prompting

这是本文的一个独特贡献——试图给 prompt engineering 建立数学基础。
### 4.1 Meta Prompting Functor

将 MP 建模为一个**函子（Functor）**，从任务范畴 $\mathcal{T}$ 映射到 prompt 范畴 $\mathcal{P}$：

$$F: \mathcal{T} \to \mathcal{P}$$

**直觉理解**：如果一个复杂任务可以分解为子任务的组合（$T = T_1 \circ T_2$），那么对应的 prompt 也可以通过组合子 prompt 来构造（$P = P_1 \circ P_2$）。函子保证了这种**组合性（compositionality）**和**模块性（modularity）**。

**为什么重要**：这不只是装饰性的数学——它提供了一个理论保证：如果你的 meta-prompt 设计遵循这个框架，那么复杂问题的 prompt 可以系统地由简单问题的 prompt 组合而成，而不需要为每个复杂问题从头设计。

### 4.2 Recursive Meta Prompting (RMP) — Writer Monad

RMP 是让 LLM **自己生成和改进自己的 prompt** 的过程。用 **Writer Monad** 建模：
- **Endofunctor $T$**：$T(P) = P \times W$，其中 $W$ 是 edit scripts 的集合（形成幺半群）
- **Unit $\eta$**：将 prompt 提升到带空编辑历史的上下文中
- **Multiplication $\mu$**：将嵌套的元推理层级展平为单一的线性编辑轨迹

$$\mu: T(T(P)) \to T(P)$$

#### 4.2.1 为什么"Prompt 改进 Prompt"能生效？——深入机制

先澄清一个误解：**RMP 不是 4.1 的函子（任务分解）的重复**。4.1 说的是"复杂任务可以拆成子任务"；4.2 说的是完全不同的事情——**让 LLM 迭代地审视和改进一个 prompt 本身**。

这背后有三层原因：

**原因 1：LLM 是更好的"批评者"而非"一次性创作者"**

人类写代码也是这样：第一版往往有缺陷，但拿到一版初稿之后做 code review 反而容易——你能看到"这里缺了边界检查"、"那里逻辑跳跃了"。LLM 也一样：
- 从零生成一个完美的 prompt 很难（搜索空间太大）
- 但给它一个现有的 prompt，让它指出缺陷并改进，这是一个**受约束的、更容易的任务**
- 每一轮改进都在缩小"当前 prompt"和"最优 prompt"之间的差距

**原因 2：编辑脚本的积累 = 自然语言版的"梯度下降"**

每一轮迭代产生的不只是新 prompt $P_{i+1}$，还有一个 **edit script** $w_i$（"我做了什么改动、为什么"）。这些 edit scripts 累积起来形成一条优化轨迹：

$$P_0 \xrightarrow{w_1} P_1 \xrightarrow{w_2} P_2 \xrightarrow{w_3} P_3 \cdots$$

Writer Monad 保证这些编辑脚本可以线性组合（$w_1 \cdot w_2 \cdot w_3$），不会出现：
- 后面的改动撤销前面的改动（代数一致性）
- 嵌套改动导致逻辑混乱（$\mu$ 操作把嵌套展平）

这就像梯度下降中每一步都沿着损失下降的方向走，而 Writer Monad 保证这些步骤可以被正确组合。

**原因 3：元认知能力的递归利用**

LLM 在预训练时见过大量的"评价→修改"模式（代码 review、论文 revision、编辑反馈）。RMP 正是利用了模型已经学会的这种**元认知能力**——不是让它解具体的题，而是让它思考"怎样的指令能让我更好地解题"。

#### 4.2.2 具体例子：一个 Prompt 如何被逐步改进

仓库中的 **MP-PT (Prompt Tuning)** 就是执行 RMP 的工具。下面用一个完整例子演示这个过程：

**起点：一个普通的 prompt $P_0$**

```
Solve this math problem step by step.
```

**第 1 轮：将 $P_0$ 喂给 MP-PT meta-prompt**

MP-PT 的指令要求 LLM：
1. 整合复杂问题解决元素（complex problem-solving elements）
2. 嵌入多步推理过程（multi-step reasoning processes）
3. 加入挑战常规思维的场景（scenarios challenging conventional thinking）

LLM 分析 $P_0$ 后发现缺陷：
- ❌ 没有要求识别问题类型和关键变量
- ❌ 没有要求考虑多种解法
- ❌ 没有规定输出格式

**edit script $w_1$**："添加问题解析步骤；要求比较多种策略；规定 LaTeX 输出格式"

**输出 $P_1$**：
```
Approach this mathematical problem methodically:

1. **Parse**: Identify all variables, given conditions, and what is being asked.
2. **Strategize**: Consider at least 2 different solution approaches.
   Choose the most promising one and explain why.
3. **Solve**: Break the solution into clear logical steps.
   Show your reasoning for each step.
4. **Verify**: Check your answer against the original constraints.
5. **Output**: Present the final answer in $\boxed{...}$ format.
```

**第 2 轮：将 $P_1$ 再次喂给 MP-PT**

LLM 分析 $P_1$ 后发现新的改进空间：
- ❌ 没有要求用代码验证（数值错误是数学推理的常见问题）
- ❌ 没有处理边界情况的指令
- ❌ 没有前置知识激活步骤

**edit script $w_2$**："添加代码验证要求；添加边界情况检查；添加前置知识回顾步骤"

**输出 $P_2$**：
```
Approach this mathematical problem as a mathematician and programmer:

1. **Recall**: List relevant theorems, formulas, or known results.
2. **Parse**: Identify variables, constraints, and the exact question.
3. **Strategize**: Consider ≥2 approaches. Choose the best and justify.
4. **Solve step by step**:
   - For each step, write the mathematical reasoning.
   - Immediately verify with Python/SymPy code.
   - Use Rational() and symbolic computation, never float approximations.
5. **Edge cases**: Check boundary conditions and special cases.
6. **Cross-verify**: Confirm the answer using an alternative method.
7. **Output**: Final answer in $\boxed{...}$ with brief justification.
```

**第 3 轮：$P_2$ → $P_3$**（如果继续）

LLM 可能发现：
- 可以添加"分解为子问题"的指令
- 可以要求"先给出直觉预估再精确求解"

**整个过程的 edit trace**：$w_1 \cdot w_2 \cdot w_3 =$ "添加结构化步骤 → 添加代码验证和边界检查 → 添加子问题分解和直觉预估"

**注意这里发生了什么**：
- $P_0$ 是一句话的平庸 prompt → $P_2$ 已经非常接近仓库中 CR Agent 的 system prompt 了
- 每一轮 LLM 都在做**不同层面的改进**：第 1 轮改结构，第 2 轮改验证机制，第 3 轮改认知策略
- 这不是简单的"拆解问题"——这是 LLM 在**元层面反思什么样的指令能引导出更好的推理**

#### 4.2.3 仓库中的三个 RMP 工具

仓库提供了三个实际的 meta-prompt，对应 RMP 的不同用途：

| 工具 | 功能 | 输入 | 输出 |
|------|------|------|------|
| **MP-PT Reasoning** | 增强 prompt 的分析推理能力 | 一个现有 prompt | 改进版 prompt（更深的推理） |
| **MP-PT Concise** | 精简 prompt 同时保留核心 | 一个冗长的 prompt | 简洁版 prompt（去除冗余） |
| **MP-ICPD** | 从任务描述生成 prompt | 一份任务文档 | 为该任务定制的结构化 prompt |

**MP-PT Reasoning** 的核心指令（LaTeX 格式）：

```
Task: Prompt Revision

[input prompt]

Objective: Revise the above prompt to enhance critical thinking
and reasoning capabilities.

Key Revision Elements:
1. Integrate complex problem-solving elements
2. Embed multi-step reasoning processes
3. Incorporate scenarios challenging conventional thinking

Expected Outcome: The revised prompt should encourage deeper
analytical thought, facilitate comprehensive understanding,
promote exploration of multiple viewpoints, and encourage
synthesis of information from various domains.
```

**MP-PT Concise** 则相反——它的指令是：

```
Task: Prompt Simplification

Goal: Transform the original prompt into a more concise version
while preserving its core essence and objective.

Instructions:
1. Maintain the primary purpose and objectives
2. Distill to only key instructions and essential information
3. Eliminate extraneous or non-essential details
4. Use clear, direct language
5. Employ bullet points or numbered steps for clarity
```

**MP-ICPD** 是最"元"的——它不是改进现有 prompt，而是**从一份任务描述文档自动生成 prompt**：

```
Meta Prompting for In-Context Prompt Design:

1. Document Analysis — 分析输入文档，提取关键概念、方法论、挑战、目标
2. Task Interpretation — 综合信息，明确核心问题、约束、需求
3. Prompt Design — 设计包含清晰指令、分步骤、上下文背景的结构化 prompt
4. (Optional) Direct Solution — 直接给出可行的解决策略
5. Output — 生成一个连贯的、可执行的 prompt
```

#### 4.2.4 RMP vs 其他自动 Prompt 优化方法

| 方法 | 优化信号 | 需要标注数据？ | 优化粒度 |
|------|---------|-------------|---------|
| **OPRO** (Google) | 任务准确率分数 | 需要验证集 | 整体 prompt 替换 |
| **DSPy** (Stanford) | 编译优化 pipeline | 需要 few-shot 示例 | 模块级 prompt |
| **APE** (自动 prompt 工程) | LLM 评分 | 需要任务示例 | 整体 prompt 生成 |
| **RMP** (本文) | LLM 自身的元认知 | **不需要** | 增量 edit script |

RMP 的独特之处：**完全不需要外部反馈信号**。它只依赖 LLM 自身的判断力来改进 prompt。这既是优势（零成本、零数据），也是风险（如果 LLM 的元认知有偏差，改进方向可能跑偏）。

**对 PhD 的价值**：
- 如果你在做 prompt optimization / automatic prompt engineering 方向的研究，这个形式化框架提供了一个干净的理论语言
- 可以帮助证明某些 prompt 优化策略的收敛性或一致性
- 范畴论视角打开了将 prompt engineering 与程序语言理论（PLT）连接的可能性
- **关键研究问题**：RMP 的迭代什么时候会收敛？什么时候会退化？能否设计一个"停止准则"？

#### 4.2.5 诚实的反思：RMP 的理论承诺 vs 实际交付

上面的 Writer Monad 理论描绘了一幅美好的图景：prompt 可以无限递归地自我改进，每一轮都沿着某个"优化方向"前进。但仔细审视仓库中的实际工具后，会发现**理论和实践之间存在显著的 gap**。

**核心问题：这三个工具本质上是"固定审视镜头"，不是真正的自我迭代**

三个 RMP 工具各自做的事情：
- MP-PT Reasoning：用一套**固定的标准**审视 prompt——"是否有多步推理？是否挑战常规思维？"
- MP-PT Concise：用另一套**固定的标准**精简 prompt——"是否冗余？是否可以更直接？"
- MP-ICPD：用**固定的流程**从文档生成 prompt——"分析→解读→设计→输出"

这些 meta-prompt 本身是**人工设计的、静态的**。它们不会进化，不会根据上一轮的结果调整自己的审视标准。这意味着：

1. **第一轮改进最大**：MP-PT Reasoning 第一次应用时，会发现"缺少结构化步骤"、"没有代码验证"等明显缺陷，改进幅度大
2. **第二轮迅速衰减**：再用同样的标准审视已经改进过的 prompt，能发现的新问题很少
3. **第三轮基本无效**：同一个镜头看第三遍，几乎找不到新东西了

**类比**：这就像让同一个 code reviewer 反复 review 同一段代码——第一轮 review 收获最大，第二轮可能还能挑出一些细节，第三轮基本就是"LGTM"了。真正的持续改进需要**换不同的 reviewer**（换不同的审视标准），或者**引入外部信号**（比如"这个 prompt 在真实任务上的准确率是 X%，还不够好"）。

**理论 vs 实践的差距**：

| 维度             | Writer Monad 理论承诺  | 实际工具交付              |
| -------------- | ------------------ | ------------------- |
| 迭代深度           | 任意深（数学上无限）         | 实际 1-2 轮就饱和         |
| 改进信号           | 每轮产生新的 edit script | edit script 的内容很快重复 |
| Meta-prompt 自身 | 理论上也可以被改进          | 实际是固定的、人工设计的        |
| 收敛保证           | Monad 公理保证代数一致性    | 但不保证"每轮都在变好"        |

**这个 gap 揭示的深层问题**：

没有外部反馈信号的自我改进本质上是**开环优化**——你让 LLM 自己判断"什么是更好的 prompt"，但这个判断标准也来自 LLM 自己。这就像让一个人自己批改自己的试卷——他能发现一些明显错误，但系统性的盲点是发现不了的。

**真正的递归自我改进需要什么？**

1. **外部验证信号**：比如 OPRO 那样，在真实任务上跑一遍，用准确率作为反馈——这是闭环优化
2. **动态变化的审视标准**：meta-prompt 本身也需要被改进（meta-meta-prompting），但这会导致无限回归
3. **不同视角的组合**：交替使用 Reasoning → Concise → Reasoning 可能比重复使用同一个好，因为每个工具关注不同维度——但组合空间仍然有限

**结论**：RMP 的 Writer Monad 形式化是一个有趣的理论框架，但目前的实践实现更接近"**用 2-3 个固定的专家视角做 prompt review**"，而非理论所承诺的"无限递归自我改进"。这本身是一个很好的研究方向——**如何让 prompt 优化真正成为闭环的、持续改进的过程？**

---

## 5. 多模态扩展：基于类型论

用 **类型论（Type Theory）** 将 MP 扩展到多模态场景。核心思想：为不同模态的输入/输出定义显式的"类型化槽位（typed slots）"。

```xml
<task_schema>
    <input_slots>
        <data type="image/png" name="problem_diagram"/>
        <data type="audio/mp3" name="verbal_instructions"/>
        <data type="model/obj" name="object_model"/>
    </input_slots>
    <output_schema>
        <synthesis type="text/markdown" name="analysis_summary"/>
        <result type="video/mp4" name="solution_animation"/>
    </output_schema>
</task_schema>
```

**直觉**：就像编程语言的类型系统确保 int 不会和 string 混用一样，多模态 meta-prompt 确保图片输入不会被当成文本处理，不同模态的信息被正确地"类型检查"后才融合。

---

## 6. 实验结果：硬数据

### 6.1 MATH Benchmark

| 模型 | 微调数据 | 工具使用 | 方法 | 准确率 |
|------|---------|---------|------|--------|
| Claude-2 | - | 无 | CoT | 32.5% |
| Minerva-540B | Arxiv+Web | 无 | CoT | 33.6% |
| PaLM-2 | - | 无 | CoT | 34.3% |
| GPT-4 (2023-0314) | - | 无 | CoT | 42.5% |
| Llama-2-70B (base) | - | 无 | CoT | 13.5% |
| **Qwen-14B (base) + MP** | **-** | **无** | **MP** | **28.9%** |
| Qwen-72B-MetaMathQA | MetaMathQA | 无 | CoT | 41.7% |
| **Qwen-72B (base) + MP** | **-** | **无** | **MP** | **46.3%** |

**关键发现**：
- Qwen-72B base + MP (46.3%) **超过了 GPT-4 早期版本** (42.5%)
- Qwen-72B base + MP (46.3%) **超过了在 MetaMathQA 上微调过的 Qwen-72B** (41.7%)
- 这意味着：**一个好的结构化 prompt > 在专用数学数据上微调**

### 6.2 GSM8K Benchmark

| 模型 | 微调数据 | 方法 | 准确率 |
|------|---------|------|--------|
| Llama-2-70B (base) | - | CoT | 56.8% |
| **Qwen-14B (base) + MP** | **-** | **MP** | **64.8%** |
| WizardMath-70B | WizardMath | CoT | 81.6% |
| MetaMath-70B | MetaMathQA | CoT | 82.3% |
| **Qwen-72B (base) + MP** | **-** | **MP** | **83.5%** |

**关键发现**：
- 再次超过了微调模型（MetaMath-70B: 82.3%, WizardMath-70B: 81.6%）
- 14B 参数的 Qwen + MP (64.8%) 已经比 70B 的 Llama-2 + CoT (56.8%) 强

### 6.3 Game of 24（最惊人的结果）

| 方法 | LLM 调用次数/样本 | 生成/Prompt tokens | 成本/样本 | 成功率 |
|------|-------------------|-------------------|----------|--------|
| IO (best of 100) | 100 | 1.8k / 1.0k | $0.13 | 33% |
| CoT (best of 100) | 100 | 6.7k / 2.2k | $0.47 | 49% |
| Tree-of-Thought (b=5) | 61.72 | 5.5k / 1.4k | $0.74 | 74% |
| **Meta Prompting** | **1/N** | **≈ 8k / 1k** | **≈ $0.0003** | **100%** |

**这组数据令人震惊**：
- 成功率：100% vs ToT 的 74%
- 成本：$0.0003 vs ToT 的 $0.74，**差 2400 倍**
- LLM 调用：1/N（整批只调用一次）vs 每个样本几十到一百次

### Game of 24 的关键洞察：范式转换

传统方法（IO、CoT、ToT）把 Game of 24 当成**一个个独立的搜索问题**——对每道题，让 LLM 尝试不同的运算组合。

Meta Prompting 的做法完全不同：**让 LLM 写一个 Python 程序来穷举求解所有可能的 Game of 24 题目**。

```python
# 核心逻辑：枚举所有排列 × 所有运算组合
def generate_results(numbers):
    if len(numbers) == 1:
        return [(numbers[0], str(numbers[0]))]
    results = []
    for i in range(len(numbers)):
        for j in range(len(numbers)):
            if i != j:
                remaining = [numbers[k] for k in range(len(numbers))
                             if k != i and k != j]
                for result, expr in try_ops(numbers[i], numbers[j]):
                    if remaining:
                        for final_result, final_expr in generate_results(
                            remaining + [result]):
                            results.append((final_result, final_expr))
                    else:
                        results.append((result, expr))
    return results
```

**这揭示了一个深刻的道理**：与其让 LLM 在每个实例上做推理搜索，不如让它**理解问题的结构，然后生成一个通用的程序化解法**。Meta-prompt 引导模型思考"如何系统地解决这类问题"，而不是"这4个数怎么凑成24"。

---

## 7. CR Agent：Meta Prompting 在复杂推理中的实际系统 Prompt

>[[2026-03-04 斯坦福 Meta-Prompting：单模型多专家编排框架]] 这个也是拆解成专家
>[[2026-03-04 Knuth论文启发与AI科研Skill设计思考]]也强调要每一步都验证
> 拆解加上验证确实是有效的


仓库里最有实践价值的是 `cr-agent-xml-assistant-v0.2.xml`，这是一个完整的数学推理 Agent 的 system prompt。其设计体现了 MP 的核心原则：

### 角色设定
将 AI 定义为"杰出的数学家、逻辑学家、程序员和 AI 科学家"，要求方法论性地解决问题。

### 结构化解题流程（XML 标签）
```xml
<problem_definition>问题定义</problem_definition>
<solution_approach>解题策略（分步骤）</solution_approach>
<preliminary_contents>前置知识</preliminary_contents>
<hints>分解提示</hints>
<intermediate_steps>
  中间问题 → 解答草稿 → 代码验证 → 输出
</intermediate_steps>
<final_solution>最终解答 + 代码验证 + \boxed{answer}</final_solution>
```

### 关键设计决策
1. **每一步都必须写代码验证**："YOU MUST CALL THE CODE INTERPRETER IMMEDIATELY IN EVERY QUESTION"
2. **用 SymPy 做精确计算**：避免浮点误差，用 `Rational` 和 `pi` 而非小数
3. **分层推理**：先建立前置知识 → 生成提示 → 拆解为中间问题 → 逐个解决 → 综合最终答案

---

## 8. Recursive Meta Prompting (RMP) 的实际 Prompt

> 三个 RMP 工具（MP-PT Reasoning、MP-PT Concise、MP-ICPD）的详细说明、原始 prompt 内容、具体例子和与其他方法的对比，已在 **4.2.3** 和 **4.2.4** 中展开。这里不再重复。

---

## 9. 对我（AI PhD）的价值和行动指南

### 9.1 研究价值

**如果你在做 Prompt Engineering / LLM Reasoning 方向：**
- 范畴论形式化是一个有趣的切入点，但坦率说，目前的形式化更多是"描述性"的而非"预测性"的——它给了一个优雅的语言来描述 MP，但还不能直接指导你发现新的更好的 prompting 策略
- 真正有贡献的实验发现是：**结构模板在数学推理上可以超过 few-shot 甚至微调**——这挑战了"更多数据/示例 = 更好表现"的直觉

**如果你在做 Automatic Prompt Optimization：**
- RMP 的 Writer Monad 形式化提供了一个理论框架来分析 prompt 优化的收敛性
- 可以与 DSPy、OPRO 等工作对比：它们是否也可以用类似的代数结构来描述？

**如果你在做 LLM 评估：**
- MP 作为 zero-shot 方法，提供了一种更公平的模型能力评估方式——消除了 few-shot 示例选择带来的噪声

### 9.2 实践价值
**立即可用的技巧：**
1. **设计 prompt 时，先写结构再填内容**。不要急着给模型看示例，先定义清楚：
   - 问题应该怎么被理解（problem definition）
   - 解答应该分几步走（solution structure）
   - 中间结果怎么呈现（intermediate format）
   - 最终答案怎么给出（output format）
1. **对于可以程序化解决的问题，引导模型写代码而非直接推理**。Game of 24 的案例完美说明了这一点——让模型"升一个抽象层级"来解决问题。
2. **用 XML/JSON 标签强制结构化输出**。CR Agent 的 XML 标签设计是一个很好的实践模板。
3. **在数学/逻辑推理场景下，试试只给结构模板不给示例**。可能效果比你精心挑选的 few-shot 更好。

### 9.3 第一性原理反思
**为什么"结构 > 示例"？**
从信息论角度思考：
- Few-shot 示例包含两类信息：(a) 解题结构/流程 (b) 具体内容/数字
- 模型需要从示例中**同时**提取这两类信息，这增加了认知负担，而且 (b) 部分实际上是噪声
- Meta Prompt 直接给出 (a)，完全去除 (b) 的干扰
- 这类似于机器学习中"归纳偏置"的概念——好的归纳偏置比更多的数据更有价值

> 总结的非常好
> Few Shot 
> 给出一些例子其实就是给更多的数据
> 而 Meta Prompt 的思想是给一个好的归纳偏置
> 所以它不需要去你精心挑选一些 Few Shot 立子
> 然后又可以比较轻松的
> 告诉他应该怎么解决问题
> Meta Prompt，在我看来是一个很有前景的事情


**更深层的洞察**：
- 这暗示 LLM 的推理能力**已经内化**在权重中了，它缺的不是"看到怎么做的例子"，而是"被告知应该用什么流程"
- 这与 "LLM as a reasoning engine that needs proper activation" 的观点一致
- 也解释了为什么 Chain-of-Thought 有效——"Let's think step by step" 本身就是一个极简的结构模板

### 9.4 批判性思考

1. **实验局限性**：只在 Qwen 系列上做了实验，其他模型（Llama、Mistral）上的泛化性未知
2. **范畴论形式化的实质贡献**：虽然优雅，但目前更像是事后的数学包装——还没有看到这个理论能**预测**什么新现象或**推导**出什么新策略
3. **Game of 24 的"作弊"嫌疑**：用 MP 引导模型写穷举程序，和其他方法（IO/CoT/ToT 直接推理）不在同一个赛道上——这更像是在测试"模型能否写正确的枚举算法"而非"模型的数学推理能力"
4. **与 Stanford Meta-Prompting 的关系**：两篇论文名字几乎一样但思路不同，容易混淆。Stanford 那篇侧重 role-based orchestration，本篇侧重 structural template。学术界需要更好的命名约定。
5. **可能的天花板**：对于真正需要创造性推理而非流程化解题的问题（如开放式研究问题），结构模板的价值可能有限

---

## 10. 与相关工作的关系图谱

```
Prompting 技术演化：

Zero-shot ("直接问")
    ↓
Chain-of-Thought ("Let's think step by step")  ← 最简单的结构模板
    ↓
Few-shot CoT (给几个推理示例)
    ↓                        ↓
Tree-of-Thought             Meta Prompting (本文)
(搜索多条推理路径)            (只给结构，不给示例)
    ↓                        ↓
自动 Prompt 优化              Recursive Meta Prompting
(OPRO, DSPy, APE)            (LLM 自己改进 prompt)
```

**Meta Prompting 在这个图谱中的位置**：它走了一条"少即是多"的路线——不是通过增加示例、增加搜索、增加优化来提升表现，而是通过**精准地给出结构模板**来释放模型已有的推理能力。这是一个值得深入研究的方向。
