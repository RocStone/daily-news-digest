# 2026-03-04 Stanford Meta-Prompting：单模型多专家编排框架

## 1. 资源链接
- **GitHub**：[suzgunmirac/meta-prompting](https://github.com/suzgunmirac/meta-prompting)
- **论文**：[Meta-Prompting: Enhancing Language Models with Task-Agnostic Scaffolding (arXiv 2401.12954)](https://arxiv.org/abs/2401.12954)
- **作者**：Mirac Suzgun（斯坦福）、Adam Tauman Kalai（微软研究院）
- **项目主页**：[suzgunmirac.github.io/meta-prompting](https://suzgunmirac.github.io/meta-prompting/)
- **数据集**：[HuggingFace: turingmachine/meta-prompting](https://huggingface.co/datasets/turingmachine/meta-prompting)
## 2. 一句话精髓
把一个 LLM 变成**指挥家（Conductor）**，让它自己决定需要哪些"专家"，自己拆解任务、委派子查询、综合结果——**全程用同一个模型，零样本，任务无关**。

---

## 3. 架构：怎么运作的

```
用户问题
    ↓
┌─────────────────────┐
│   Meta Model (指挥家) │ ← 有完整对话历史
│   决定需要什么专家     │
│   拆解 → 委派 → 综合  │
└────┬───────┬────────┘
     ↓       ↓
  Expert A  Expert B    ← 每个专家都是同一个LLM的独立调用
  (全新上下文)  (全新上下文)    没有共享记忆！
```

**关键机制：**
1. **Fresh Eyes（全新视角）**：每个专家只收到指挥家精心撰写的指令，不会看到完整对话历史。这防止了锚定偏差，让每个专家真正独立思考。
2. **动态专家创建**：没有预定义的专家列表。指挥家按需"发明"专家名——"Expert Chess Strategist"、"Expert Number Theorist"、"Expert Linguist"都是即时生成的。
3. **交叉验证**：指挥家可以让第二个专家检查第一个专家的工作，比较两个方案，解决分歧。
4. **工具集成**：Expert Python 比较特殊——它能实际执行代码，弥合了推理和计算之间的鸿沟。

### 实现机制：本质就是多次 API 调用

所谓"专家"不是一个持久存在的实体，就是**一次独立的 API call**。不需要多个模型，不需要多个 session——同一个模型 endpoint，同一个 API key，同一组权重。区别仅仅在于每次调用传入的 `messages` 不同。

```python
# 指挥家的主循环
conversation_history = [system_prompt, user_question]

while rounds < 16:
    # 1. 指挥家生成回复（带完整历史）
    response = llm.call(messages=conversation_history)

    # 2. 检测是否调用了专家
    if "Expert" in response:
        expert_name, instructions = parse(response)

        # 3. 关键：用全新的、独立的消息列表调用同一个 API
        #    这就是 Fresh Eyes —— 专家完全看不到 conversation_history
        expert_response = llm.call(messages=[
            {"role": "system", "content": f"You are {expert_name}"},
            {"role": "user", "content": instructions}
        ])

        # 4. 把专家回复塞回指挥家的历史
        conversation_history.append(expert_response)

    elif "FINAL ANSWER" in response:
        return extract_answer(response)
```

**和"多开session"的关键区别**：多开 session 需要人类手动复制粘贴、手动综合结果，而且每个 session 有持久状态。Meta-Prompting 是程序自动化——指挥家自己写指令、自己发调用、自己综合，专家调用是一次性的，调完就丢。

---

## 4. 核心 Prompt 模板拆解

指挥家的系统提示词是整个方法的全部"秘密"。以下是逐元素分析：

| 要素   | 原文要点                                  | 作用                          |
| ---- | ------------------------------------- | --------------------------- |
| 角色定义 | "你是 Meta-Expert，能协调多个专家"              | 建立角色和能力边界                   |
| 调用协议 | `Expert XXX:\n"""指令"""`               | 标准化的专家调用格式，系统用正则检测          |
| 隔离原则 | "每次交互是隔离的，包含所有必要信息"                   | **强制 Fresh Eyes**——每个专家从零开始 |
| 纠错机制 | "如果发现错误，请新专家审查"                       | 内置 error recovery           |
| 验证步骤 | "最终答案前，至少咨询一个专家确认"                    | 强制多专家交叉验证                   |
| 终止控制 | "在15轮内给出最终答案" + `>> FINAL ANSWER:` 标记 | 防止无限循环 + 明确终止信号             |
| 工具提示 | "你可以使用 Expert Python 执行代码"            | 引导计算密集型任务走代码路线              |

### 完整调用示例
```
Expert Mathematician:
"""
你是一个数学专家，专攻几何与代数。
计算点(-2, 5)和(3, 7)之间的欧氏距离。
"""
```
系统用正则 `Expert ((?:\w+ ?){1,5}):\n` 检测到调用后：
1. 提取专家名和指令
2. 用**全新上下文**调用同一个 LLM（不带对话历史）
3. 如果是 Expert Python 且生成了代码，执行代码并附加输出
4. 把专家回复返回给指挥家
### 参数配置

所有模块统一：`temperature=0.1, top_p=0.95, max_tokens=1024`。低温度保证确定性和一致性。最多跑16轮，第14轮强制要求给出最终答案。

---

## 5. 论文中的专家实例：指挥家到底召唤了谁

这是理解整个系统最关键的部分。专家**不是预定义的**——指挥家根据任务即时发明。但论文中出现了清晰的模式。

### 系统提示词中给出的示例专家名

系统提示词中举了这些名字作为示范：Expert Problem Solver、Expert Mathematician、Expert Essayist、Expert Linguist、Expert Puzzle Solver、**Expert Python**（特殊——能执行代码）。但指挥家完全可以发明任何名字。

### 各任务中实际出现的专家

| 任务 | 有 Python 时的专家 | 无 Python 时的专家 | 典型轮数 |
|------|-------------------|-------------------|---------|
| **Game of 24** | Expert Mathematician → Expert Python（暴力搜索） | Expert Mathematician, Expert Problem Solver, Expert Number Theorist | ~3.5轮 |
| **单词排序** | Expert Python（写排序脚本） | Expert Linguist, Expert Problem Solver | ~3.3轮 |
| **国际象棋将杀** | Expert Chess Player（找杀招）→ Expert Chess Analyst（验证） | 同左 | ~3.5轮 |
| **十四行诗写作** | Expert Poet（起草）→ Expert Literary Critic（审稿） | Expert Poet, Expert Literary Critic, Expert Essayist | ~4轮 |
| **Python谜题** | Expert Python, Expert Python Programmer, Expert Mathematician | Expert Problem Solver, Expert Puzzle Solver | ~6轮 |
| **多语言数学** | Expert Translator（翻译）→ Expert Mathematician（计算）→ 再验证 | Expert Linguist, Expert Mathematician | ~3轮 |

### 一个具体的协作流程：国际象棋将杀

```
用户：找到一步将杀的走法 [棋盘状态]

指挥家：这是个棋类问题，我需要棋类专家。

    Expert Chess Player:
    """
    你是一个国际象棋专家。分析以下棋盘状态，找到白方一步将杀的走法。
    [完整棋盘描述]
    """
    → 专家回复：Qh7# (后到h7将杀)

指挥家：让我找另一个专家独立验证。

    Expert Chess Analyst:
    """
    你是一个国际象棋分析专家。在以下棋盘状态中，请验证 Qh7# 是否是合法的一步将杀。
    [完整棋盘描述 + 提议的走法]
    """
    → 专家回复：确认，Qh7# 是正确的将杀。

指挥家：两个独立专家一致同意。
>> FINAL ANSWER: Qh7#
```

注意两个关键细节：
- Expert Chess Analyst **看不到** Expert Chess Player 的推理过程，只看到指挥家转述的结论——这就是 Fresh Eyes
- 指挥家主动选择了"先解题再验证"的两步策略——**没有人教它这么做**，这是它自己的决策

### 一个具体的协作流程：多语言数学（MGSM）

这个例子展示了指挥家自发涌现的三阶段模式：

```
用户：[一道泰语数学题]

指挥家：这是非英语问题，先翻译。

    Expert Thai Language Specialist:
    """
    你是泰语专家。请将以下泰语数学题翻译为英文，保持数学含义准确。
    [泰语原题]
    """
    → 翻译结果

指挥家：现在让数学专家解题。

    Expert Mathematician:
    """
    你是数学专家。请解决以下问题：[英文翻译后的题目]
    """
    → 计算结果

指挥家：验证后给出最终答案。
>> FINAL ANSWER: 42
```

**这个"翻译→计算→验证"的流水线完全是指挥家自己发明的**——系统提示词里没有任何关于多语言处理策略的指导。

### 关键发现：有 Python vs 无 Python 的专家分布变化

- **有 Python 时**：指挥家明显偏好技术和计算类专家，Expert Python 成为万能工具。很多本该用领域专家的任务也被扔给了 Python 写脚本解决。
- **无 Python 时**：专家谱系变得更多样化，出现了更多领域特异性的专家（诗歌评论家、语言学家、几何学家等）。
- 指挥家在 Game of 24 中有 9 次（100题中）诚实地承认"无解"——比其他方法更诚实，其他方法倾向于给出错误答案。

---

## 6. 实验结果

| 任务 | 标准提示 | Meta+Python | 提升 |
|------|---------|-------------|------|
| **Game of 24** | 3.0% | 67.0% | **+64%** |
| 单词排序 | 80.4% | 99.6% | +19% |
| 国际象棋将杀 | 36.4% | 57.2% | +21% |
| 十四行诗写作 | 62.0% | 79.6% | +18% |
| Python谜题 | 31.1% | 45.8% | +15% |
| 多步算术 | 84.0% | 90.0% | +6% |
| 几何形状 | 56.8% | 59.2% | +2% |
| 多语言数学 | 84.4% | 84.8% | +0.4% |
| **宏观平均** | **54.8%** | **72.9%** | **+18%** |

**规律很明显：模型本身越弱的任务，Meta-Prompting 提升越大。** 模型已经很强的任务（如多语言数学），提升微乎其微。Game of 24 从 3% 跳到 67%，完全是因为指挥家学会了让 Expert Python 暴力搜索所有可能的四则运算组合。

---

## 7. 与其他方法的本质区别

| 方法 | 区别 |
|------|------|
| **CoT（思维链）** | 单次调用，单一视角。Meta-Prompting 是多次调用、多视角 |
| **Multi-Agent（多智能体）** | 需要多个不同模型或复杂框架。Meta 只用一个模型 |
| **Self-Consistency** | 多次采样取多数票。Meta 是有结构的分工协作 |
| **Multi-Persona** | 多人格在同一上下文中。Meta 的专家是**隔离的独立调用** |

Meta-Prompting 的独特之处在于：**它让模型自己决定该怎么拆解任务**，而不是人类预设分解策略。

---

## 8. 5个可直接复用的实操要点

**1. 你自己就能实现这个系统**
核心就是：一个系统提示词 + 一个循环（检测专家调用 → 发起新的LLM查询 → 把结果返回给指挥家）。调用协议就是正则匹配 `Expert (名字):\n"""..."""`。
**2. Fresh Context 是关键**
给专家的每次调用都用干净的上下文。**不要传完整对话历史**。这是区别于普通 multi-turn 对话的核心设计。
**3. 加上代码执行能力**
Game of 24 从 3% 跳到 67%，完全是因为指挥家学会了让 Expert Python 暴力搜索。计算密集型任务一定要给工具。
**4. 用低温度（0.1）**
所有模块都用 `temperature=0.1, top_p=0.95`，保证输出的确定性和一致性。
**5. 多专家验证 > 单次回答**
Prompt 中明确要求"用两个独立专家验证最终答案"。这本质上是用计算资源换准确率——同一个模型跑多次，从不同角度检查。

---

## 9. 局限性

- **API 成本高**：每个问题多次 LLM 调用
- **弱模型效果差**：GPT-3.5 提升远不如 GPT-4，基础模型需要强指令遵循能力
- **不可分解的任务收益低**：如果任务本身缺乏自然的子任务结构，效果有限
- **延迟高**：串行的多轮调用意味着更长的等待时间
- **论文发表于 2024 年初**，方法本身不算最新，但核心思想仍然有效

---

## 10. 根本洞察

这个工作的根本洞察是：**编排（orchestration）比单次推理更强大**。Meta-Prompting 不教模型具体怎么解题，而是教它**怎么组织解题过程**。这是一个从"做事"到"管理做事"的抽象层级跃迁。

隔离上下文（Fresh Eyes）是反直觉但极其有效的设计——我们直觉上觉得给模型更多信息更好，但实际上信息过载会导致锚定偏差。让每个专家只看到精心筛选过的信息，反而能得到更高质量的输出。
