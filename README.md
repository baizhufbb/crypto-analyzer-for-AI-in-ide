# 加密货币合约市场数据获取脚本

## 🎯 核心功能

这是一个用于获取和分析加密货币**合约市场数据**的脚本项目，支持 Binance 与 OKX，可输出：
- 单个或多个合约的 K 线及 MA20 / MA50 / RSI14 等技术指标
- 24 小时行情快照、资金费率、持仓量、订单簿深度等附加信息

> **若由高胜率专业加密货币交易员（AI 交易员）接管自动化流程**，请参考 `docs/AI_GUIDE.md`，其中包含专用的操作规程与避坑建议。

## 快速开始

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

> **AI 交易员专用说明**：若由高胜率专业加密货币交易员（AI 交易员）操作，请改查 `docs/AI_GUIDE.md` 获取完整的自动化流程与规范。
