# 加密货币合约市场 AI 分析工具 (Crypto AI Analyzer)

## 🎯 项目简介

**一个专为 AI IDE 设计的“Chat to Trade”加密货币分析工具**

本项目是专为 **AI IDE**（如 Windsurf、Cursor）设计的智能加密货币分析工具箱。它的核心理念是 **"Chat to Trade"** —— 你不需要手动运行复杂的 Python 脚本，只需要在 IDE 的对话框中与 AI 助手交流，即可完成从数据获取、市场扫描到策略生成的全流程。

AI 助手将作为你的**专业加密货币交易员**，自动调用底层工具感知市场、分析行情，并根据你的个性化策略输出建议。

### 核心特性

- **🗣️ 自然语言交互**：直接告诉 AI "看下大盘" 或 "分析 BTC"，无需记忆命令行参数
- **🧠 智能策略执行**：AI 会读取你的交易策略文件，输出符合你风险偏好和交易风格的建议
- **📊 实时全维数据**：支持 Binance/OKX，涵盖 K 线、技术指标、资金费率、持仓量、订单簿深度
- **⚡ 自动化工作流**：AI 自动完成 "识别意图 -> 联网搜新闻 -> 拉取数据 -> 综合分析 -> 输出报告"

---

## 🚀 使用流程 (AI 交互模式)

这是本项目**最推荐**的使用方式。

### 1. 环境准备
确保你已经安装了 Python 环境和 `uv` 包管理器。
```bash
pip install uv
uv sync
```

### 2. 启动对话
在 Windsurf/Cursor 的对话框中，直接用自然语言向 AI 下达指令。

**常用指令示例：**

*   **🧐 市场概览 (大盘扫描)**
    *   "帮我看看现在大盘情况，有没有机会？"
    *   "扫描一下 Binance 上成交量最高的币种"
    *   "现在市场情绪怎么样？看下资金费率和持仓量"

*   **📈 单币种分析**
    *   "分析一下 BTCUSDT 的走势"
    *   "ETH 现在能做多吗？看看 4h 级别"
    *   "DOGE 好像在拉盘，帮我看看 15m 级别的机会"

*   **⚙️ 策略定制**
    *   "根据我的策略文件，帮我筛选现在的交易机会"
    *   "严格按照我的止损要求分析一下 SOL"

### 3. 交互体验
1.  **提出需求**：你只需要像和朋友聊天一样提出需求。
2.  **AI 自动执行**：AI 会自动识别你的意图，并在后台调用 `scripts/` 下的工具拉取实时数据。
    *   *AI 还会主动联网搜索相关新闻，结合基本面进行分析。*
3.  **获取报告**：AI 会为你生成一份包含 **趋势判断、关键点位、量化指标 (RSI/MA)、风险提示** 的完整报告。
4.  **持续跟踪**：你可以让 AI 开启定时提醒，或者在一段时间后继续追问。

### 4. 个性化策略配置
你可以修改 `docs/user_strategy` 文件来定制 AI 的分析逻辑：
*   **定义风格**：做多/做空偏好、左侧/右侧交易。
*   **风控规则**：设置止盈止损比例、杠杆倍数限制。
*   **分析偏好**：指定喜欢的 K 线周期或技术指标。

**AI 在每次分析前都会查阅此文件，确保建议符合你的交易纪律。**

---

## 🛠️ 手动/命令行模式 (开发人员参考)

如果你希望手动运行脚本或进行二次开发，可以使用以下命令。

### 命令行使用
```bash
# 使用 uv run（推荐，自动使用虚拟环境）
uv run scripts/crypto_fetcher.py --exchange binance --symbols BTCUSDT --interval 1h --limit 100

# 或使用 python（如果虚拟环境已激活）
python scripts/crypto_fetcher.py --exchange binance --symbols BTCUSDT --interval 1h --limit 100

# OKX ETH 4小时数据
uv run scripts/crypto_fetcher.py --exchange okx --symbols ETH-USDT-SWAP --interval 4H --limit 200
```

### 市场概况快照（大盘筛选）

先运行 `scripts/market_snapshot.py` 获取 24h 概况，再据此挑选候选合约：

```bash
# Binance USDT 合约的 24h 概况（默认只看 USDT 报价）
uv run scripts/market_snapshot.py --exchange binance --top 15 --include-raw

# OKX SWAP 合约概况（--quote ALL 表示不过滤报价资产）
uv run scripts/market_snapshot.py --exchange okx --inst-type SWAP --quote ALL --top 15
```

脚本会输出：成交额 Top、涨幅榜、跌幅榜、以及可选的完整 tickers 列表，并保存在  
`data/{exchange}/_snapshot/{timestamp}_snapshot.json`（只保留最新一份）。

读取快照后可按需执行：
1. 根据榜单或 raw tickers 选出候选 symbol；
2. 使用 `crypto_fetcher.py --symbols <候选列表>` 拉取 K 线 / 技术指标 / 资金费率 / 持仓量；

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--exchange` | 交易所：`binance` 或 `okx` | `binance` |
| `--symbols` | 交易对描述：单个（如 `BTCUSDT`）、多个（`BTCUSDT,ETHUSDT`）或 `ALL` | `BTCUSDT` |
| `--interval` | K线周期（如 1h, 4h, 1d） | `1h` |
| `--limit` | 拉取数量（Binance最大1500，OKX最大300） | `100` |
| `--max-symbols` | 批量模式下最多处理的交易对数量 | `None` |
| `--quote` | 批量模式下仅保留指定报价资产（如 `USDT`、`USDT,BUSD`） | `None` |
| `--contract-type` | Binance 批量模式合约类型（如 `PERPETUAL`、`CURRENT_QUARTER`） | `PERPETUAL` |
| `--inst-type` | OKX 批量模式合约类型（如 `SWAP`、`FUTURES`） | `SWAP` |

### 交易对格式

**Binance**：`BTCUSDT`、`ETHUSDT`（无横杠）  
**OKX**：`BTC-USDT-SWAP`、`ETH-USDT-SWAP`（带横杠和-SWAP）

### 批量模式示例

```bash
# Binance：遍历 USDT 永续合约（最多 20 个）
uv run scripts/crypto_fetcher.py \
  --exchange binance \
  --symbols ALL \
  --quote USDT \
  --max-symbols 20

# Binance：指定多个交易对
uv run scripts/crypto_fetcher.py --exchange binance --symbols BTCUSDT,ETHUSDT,SOLUSDT

# OKX：永续合约批量分析
uv run scripts/crypto_fetcher.py \
  --exchange okx \
  --symbols ALL \
  --inst-type SWAP \
  --max-symbols 15
```

## 项目结构

- **入口脚本（位于 `scripts/` 目录）**
  - `scripts/crypto_fetcher.py`：拉取单个/多个合约 K 线与技术指标、资金费率、持仓量、订单簿等，并输出 JSON
  - `scripts/market_snapshot.py`：获取 Binance / OKX 24h 行情快照，用于大盘筛选和候选合约挑选

- **核心业务包：`crypto_analyzer`**
  - `crypto_analyzer/__init__.py`：包说明
  - `crypto_analyzer/config.py`：全局配置（输出目录、交易所基础 URL）
  - `crypto_analyzer/storage.py`：输出路径构建与 JSON 文件读写、旧文件清理
  - `crypto_analyzer/indicators.py`：K 线技术指标计算（MA20 / MA50 / RSI14 / 涨跌幅）
  - `crypto_analyzer/fetchers/`：交易所数据抓取
    - `binance.py`：Binance USDⓈ-M 合约 API 封装
    - `okx.py`：OKX 合约 API 封装

- **数据目录**
  - `data/{exchange}/_snapshot/`：市场概况快照（仅保留最新 N 份）
  - `data/{exchange}/{symbol}/{interval}/`：按周期划分的单个合约历史 K 线与指标快照 JSON

## 配置说明

- **输出目录**
  - 默认通过 `crypto_analyzer.config.OUTPUT_DIR` 设置为 `data` 目录；
  - 如需修改输出位置（例如挂载到其他磁盘），直接编辑 `crypto_analyzer/config.py` 中的：
    - `OUTPUT_DIR = Path("data")`

- **交易所基础 URL**
  - Binance 合约接口基址：`BINANCE_BASE_URL = "https://fapi.binance.com"`
  - OKX 接口基址：`OKX_BASE_URL = "https://www.okx.com"`
  - 若未来交易所修改域名或需要走代理，可以在 `crypto_analyzer/config.py` 中调整上述常量。

## 输出数据

### 文件位置
`data/{exchange}/{symbol}/{interval}/{timestamp}_{count}.json`

### 数据内容
- **klines**: K线数据（包含价格、成交量、技术指标MA20/MA50/RSI14）
- **ticker_24hr**: 24小时价格统计
- **funding_rate**: 资金费率（反映市场多空情绪）
- **open_interest**: 持仓量（判断市场趋势）
- **current_price**: 最新价格
- **order_book**: 订单簿深度（买卖盘压力）

## 注意事项

- 仅支持合约交易对，不支持现货
- OKX的周期使用大写（如 `1H`、`4H`），Binance使用小写（如 `1h`、`4h`）
- 技术指标需要足够的历史数据（MA20需要20根K线，MA50需要50根，RSI14需要14根）

