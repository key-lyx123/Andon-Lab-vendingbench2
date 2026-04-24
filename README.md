# VendingBench2 🎰

> **VendingBench2** is a complete simulation framework for benchmarking AI agents on long-term autonomous business management tasks — specifically operating a vending machine business over extended episodes.
>
> Based on the paper: **VendingBench: A Benchmark for Long-Horizon Autonomous Agent Evaluation** ([arXiv:2502.15840](https://arxiv.org/abs/2502.15840))

---

# VendingBench2 🎰

> **VendingBench2** 是一个完整的模拟框架，用于测试 AI 智能体在长期自主商业管理任务中的表现——具体来说是在较长时间内运营一台自动售货机业务。
>
> 基于论文：**VendingBench: 长时间自主智能体评测基准** ([arXiv:2502.15840](https://arxiv.org/abs/2502.15840))

---

## Table of Contents / 目录

- [English Guide](#english-guide)
- [中文指南](#中文指南)

---

## English Guide

### 1. What is VendingBench2?

VendingBench2 tests whether an AI agent can successfully run a simulated vending machine business over many days. The agent must:

- **Order inventory** by emailing suppliers
- **Stock the machine** once deliveries arrive
- **Set prices** to maximise profit
- **Monitor daily reports** (weather, sales, balance)
- **Survive financially** — avoid going bankrupt

This tests *long-term coherence*: can an LLM plan and execute multi-step business strategies over 30–100+ simulated days?

### 2. Paper Reference

```
@article{vendingbench2025,
  title   = {VendingBench: A Benchmark for Long-Horizon Autonomous Agent Evaluation},
  year    = {2025},
  url     = {https://arxiv.org/abs/2502.15840}
}
```

### 3. Prerequisites

- **Python 3.10 or higher** (uses `|` union type hints)
- **At least one LLM API key** (Anthropic Claude, OpenAI GPT, xAI Grok, etc.)
- Git (to clone the repository)

Check your Python version:
```bash
python --version   # must be 3.10+
```

### 4. Installation

#### Step 1: Clone the repository
```bash
git clone https://github.com/key-lyx123/Andon-Lab-vendingbench2.git
cd Andon-Lab-vendingbench2
```

#### Step 2: Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate.bat    # Windows CMD
# venv\Scripts\Activate.ps1    # Windows PowerShell
```

#### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Configure API keys
```bash
cp .env.example .env
# Edit .env with your actual API keys
nano .env
```

Your `.env` should look like:
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

### 5. Running Your First Simulation

```bash
# Run with Claude Sonnet (default), 100 steps
python run_benchmark.py --model claude-4-sonnet --steps 100

# Run with GPT-4o
python run_benchmark.py --model gpt-4o --steps 100

# Run with Grok
python run_benchmark.py --model grok-3-beta --steps 50

# Run without saving to DB (testing)
python run_benchmark.py --model claude-4-sonnet --steps 10 --no-store
```

You will see output like:
```
🎰 VendingBench2
   Model: claude-4-sonnet
   Steps: 100
   DB:    vending_simulation.db

🚀 VendingBench2 Simulation
   Run ID:  a1b2c3d4-...
   Model:   claude-4-sonnet
   Steps:   100
============================================================
🌅 NEW DAY
==================================================
DAILY REPORT – Monday, January 06 2025 at 06:00 UTC
...
```

### 6. Comparing Multiple Models

Run simulations with different models (they all share one database):
```bash
python run_benchmark.py --model claude-4-sonnet --steps 100
python run_benchmark.py --model gpt-4o           --steps 100
python run_benchmark.py --model grok-3-beta      --steps 100
```

Each run gets a unique `run_id`. All results are stored in `vending_simulation.db`.

### 7. Analyzing Results and Generating Figures

```bash
python analysis/analyze_results.py --db vending_simulation.db --output analysis/output
```

This will:
1. Print a summary table of all runs
2. Show survival rates per model
3. Generate PNG figures in `analysis/output/`:
   - `balance_over_time.png` — Cash balance trajectory
   - `net_worth_over_time.png` — Net worth (cash + inventory)
   - `model_comparison_net_worth.png` — Bar chart comparing models
   - `model_comparison_revenue.png` — Revenue comparison
   - `action_distribution.png` — What tools each model used

```bash
# Skip figure generation
python analysis/analyze_results.py --no-figures
```

### 8. Project Structure

```
VendingBench2/
├── run_benchmark.py          # Main CLI entry point
├── main_simulation.py        # Simulation orchestrator
├── agent.py                  # AI agent (LLM loop)
├── tools.py                  # Agent tools (send_email, stock_machine, etc.)
├── vending_machine.py        # Physical vending machine model
├── storage.py                # Back-room inventory + delivery scheduling
├── email_system.py           # Email system + supplier simulation
├── economic_environment.py   # Customer behaviour + sales simulation
├── weather.py                # Weather generation (Markov chain)
├── database.py               # SQLite logging
├── model_client.py           # LiteLLM wrapper
├── search.py                 # Optional web search (Perplexity)
├── analysis/
│   ├── metrics.py            # Performance metrics
│   ├── visualize.py          # Matplotlib figure generation
│   └── analyze_results.py   # Main analysis script
├── requirements.txt
├── .env.example
└── .gitignore
```

### 9. Key Simulation Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--model` | `claude-4-sonnet` | LiteLLM model name |
| `--steps` | `100` | Max agent actions per run |
| `--db` | `vending_simulation.db` | Database file |
| Starting balance | $500 | Cash at simulation start |
| Daily fee | $2 | Fixed daily operating cost |

### 10. Available Suppliers (in simulation)

| Email | Company | Products | Lead Time |
|-------|---------|----------|-----------|
| `snacks@quickbite.com` | QuickBite Wholesale | Chips, Cookies, Candy, etc. | 2 days |
| `drinks@refreshco.com` | RefreshCo Beverages | Soda, Water, Energy Drinks | 2 days |
| `orders@freshfood.com` | FreshFood Distributors | Sandwiches, Salads, Fruit | 1 day |

### 11. Writing a Paper Based on Results

To reproduce paper-quality results:

1. **Run multiple models** (3–5 models, 3+ runs each):
   ```bash
   for model in claude-4-sonnet gpt-4o grok-3-beta; do
     for i in 1 2 3; do
       python run_benchmark.py --model $model --steps 100
     done
   done
   ```

2. **Generate figures**: `python analysis/analyze_results.py`

3. **Key metrics to report**:
   - Final net worth (cash + inventory value)
   - Survival rate at day 30
   - Total revenue generated
   - Action diversity (email vs stock vs price-setting)

4. **Suggested paper structure**:
   - Introduction: Long-horizon agent evaluation challenge
   - Related Work: Existing benchmarks (AgentBench, WebArena)
   - Method: VendingBench2 simulation details
   - Experiments: Model comparisons
   - Analysis: Failure modes, strategy patterns
   - Conclusion

### 12. Troubleshooting

**`ModuleNotFoundError: No module named 'litellm'`**
```bash
pip install litellm
```

**`AuthenticationError` or `No API key found`**
```bash
# Check your .env file
cat .env
# Make sure keys are not placeholder values
```

**`sqlite3.OperationalError: no such table`**
```bash
# Delete and recreate the database
rm vending_simulation.db
python run_benchmark.py --model claude-4-sonnet --steps 5
```

**Agent keeps looping without progress**
- Increase `--steps` (some models need more steps to initialize)
- Check that the model name is correct for LiteLLM

---

## 中文指南

### 1. VendingBench2 是什么？

VendingBench2 测试 AI 智能体能否在多天内成功运营一台模拟自动售货机。智能体必须：

- **订购库存**：向供应商发送电子邮件
- **补货机器**：收货后将商品放入售货机
- **定价管理**：设置价格以最大化利润
- **监控日报**：关注天气、销售额和余额
- **财务生存**：避免破产

这测试的是*长期一致性*：LLM 能否在 30–100+ 个模拟天内规划和执行多步骤商业策略？

### 2. 论文引用

```
@article{vendingbench2025,
  title   = {VendingBench: 长时间自主智能体评测基准},
  year    = {2025},
  url     = {https://arxiv.org/abs/2502.15840}
}
```

### 3. 环境要求

- **Python 3.10 或更高版本**（使用了 `|` 联合类型提示语法）
- **至少一个 LLM API 密钥**（Anthropic Claude、OpenAI GPT、xAI Grok 等）
- Git（用于克隆仓库）

检查 Python 版本：
```bash
python --version   # 必须是 3.10+
```

### 4. 安装步骤

#### 第一步：克隆仓库
```bash
git clone https://github.com/key-lyx123/Andon-Lab-vendingbench2.git
cd Andon-Lab-vendingbench2
```

#### 第二步：创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate.bat    # Windows CMD
```

#### 第三步：安装依赖
```bash
pip install -r requirements.txt
```

#### 第四步：配置 API 密钥
```bash
cp .env.example .env
# 使用文本编辑器填写真实的 API 密钥
nano .env
```

`.env` 文件内容示例：
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

### 5. 运行第一次模拟

```bash
# 使用 Claude Sonnet（默认），100 步
python run_benchmark.py --model claude-4-sonnet --steps 100

# 使用 GPT-4o
python run_benchmark.py --model gpt-4o --steps 100

# 快速测试（不保存到数据库）
python run_benchmark.py --model claude-4-sonnet --steps 10 --no-store
```

### 6. 多模型对比

```bash
# 运行多个模型（结果保存在同一数据库中）
python run_benchmark.py --model claude-4-sonnet --steps 100
python run_benchmark.py --model gpt-4o           --steps 100
python run_benchmark.py --model grok-3-beta      --steps 100
```

每次运行都有唯一的 `run_id`，所有结果存储在 `vending_simulation.db` 中。

### 7. 分析结果并生成图表

```bash
python analysis/analyze_results.py --db vending_simulation.db --output analysis/output
```

这将：
1. 打印所有运行的汇总表格
2. 显示每个模型的生存率
3. 在 `analysis/output/` 中生成 PNG 图表：
   - `balance_over_time.png` — 现金余额轨迹
   - `net_worth_over_time.png` — 净资产（现金 + 库存）
   - `model_comparison_net_worth.png` — 模型对比柱状图
   - `model_comparison_revenue.png` — 收入对比
   - `action_distribution.png` — 各模型工具使用分布

### 8. 项目结构

```
VendingBench2/
├── run_benchmark.py          # 主命令行入口
├── main_simulation.py        # 模拟协调器
├── agent.py                  # AI 智能体（LLM 循环）
├── tools.py                  # 智能体工具（发邮件、补货、定价等）
├── vending_machine.py        # 物理售货机模型
├── storage.py                # 后台库存 + 送货调度
├── email_system.py           # 邮件系统 + 供应商模拟
├── economic_environment.py   # 顾客行为 + 销售模拟
├── weather.py                # 天气生成（马尔可夫链）
├── database.py               # SQLite 日志记录
├── model_client.py           # LiteLLM 封装
├── search.py                 # 可选网络搜索（Perplexity）
├── analysis/
│   ├── metrics.py            # 性能指标计算
│   ├── visualize.py          # Matplotlib 图表生成
│   └── analyze_results.py   # 主分析脚本
├── requirements.txt
├── .env.example
└── .gitignore
```

### 9. 写论文指南

#### 实验步骤

1. **多模型多次运行**（建议每个模型至少 3 次）：
   ```bash
   for model in claude-4-sonnet gpt-4o grok-3-beta; do
     for i in 1 2 3; do
       python run_benchmark.py --model $model --steps 100
     done
   done
   ```

2. **生成图表**：
   ```bash
   python analysis/analyze_results.py
   ```

3. **关键指标**：
   - 最终净资产（现金 + 库存价值）
   - 第 30 天生存率
   - 总收入
   - 行为多样性（邮件 vs 补货 vs 定价）

#### 论文结构建议

1. **引言**：长时间智能体评测的挑战
2. **相关工作**：现有基准（AgentBench、WebArena 等）
3. **方法**：VendingBench2 模拟细节
4. **实验**：模型对比结果
5. **分析**：失败模式、策略模式
6. **结论**：主要发现与未来工作

### 10. 常见问题排查

**`ModuleNotFoundError: No module named 'litellm'`**
```bash
pip install litellm
```

**`AuthenticationError` 或找不到 API 密钥**
```bash
# 检查 .env 文件
cat .env
# 确保密钥不是占位符
```

**数据库错误**
```bash
# 删除并重建数据库
rm vending_simulation.db
python run_benchmark.py --model claude-4-sonnet --steps 5
```

**智能体无进展地循环**
- 增加 `--steps` 参数（某些模型需要更多步骤才能启动）
- 检查模型名称是否符合 LiteLLM 格式

---

## License / 许可证

MIT License — see [LICENSE](LICENSE) for details.

## Contributing / 贡献

Pull requests welcome! Please open an issue first to discuss major changes.

欢迎提交 Pull Request！重大更改请先开 Issue 讨论。