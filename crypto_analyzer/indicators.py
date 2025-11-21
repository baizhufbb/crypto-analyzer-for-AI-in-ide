import math
from typing import Any, Dict, List


def calculate_indicators(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    为 K 线数据计算技术指标：MA、RSI、涨跌幅、波动率等。
    预计算这些指标可以节省 AI 分析时的计算时间。
    """
    if not records:
        return records

    result: List[Dict[str, Any]] = []
    closes = [r["close"] for r in records]

    for i, record in enumerate(records):
        enriched = record.copy()

        if i >= 19:
            enriched["ma20"] = round(sum(closes[i - 19 : i + 1]) / 20, 8)
        if i >= 49:
            enriched["ma50"] = round(sum(closes[i - 49 : i + 1]) / 50, 8)

        if i >= 14:
            period_closes = closes[i - 14 : i + 1]
            gains = []
            losses = []
            for j in range(1, len(period_closes)):
                change = period_closes[j] - period_closes[j - 1]
                if change > 0:
                    gains.append(change)
                    losses.append(0.0)
                else:
                    gains.append(0.0)
                    losses.append(abs(change))
            avg_gain = sum(gains) / 14
            avg_loss = sum(losses) / 14
            if avg_loss == 0:
                enriched["rsi14"] = 100.0
            else:
                rs = avg_gain / avg_loss
                enriched["rsi14"] = round(100 - (100 / (1 + rs)), 2)

        if i > 0:
            prev_close = records[i - 1]["close"]
            price_change = record["close"] - prev_close
            price_change_pct = (price_change / prev_close) * 100
            enriched["price_change"] = round(price_change, 8)
            enriched["price_change_pct"] = round(price_change_pct, 4)

        # 计算波动率指标（ATR和标准差）
        # ATR (Average True Range) - 14周期
        if i >= 14:
            true_ranges = []
            for j in range(max(1, i - 13), i + 1):
                high = records[j]["high"]
                low = records[j]["low"]
                if j > 0:
                    prev_close = records[j - 1]["close"]
                    tr = max(
                        high - low,
                        abs(high - prev_close),
                        abs(low - prev_close)
                    )
                else:
                    tr = high - low
                true_ranges.append(tr)
            enriched["atr14"] = round(sum(true_ranges) / len(true_ranges), 8)
            # ATR百分比（相对于价格）
            if record["close"] > 0:
                enriched["atr14_pct"] = round((enriched["atr14"] / record["close"]) * 100, 4)

        # 标准差波动率（20周期）
        if i >= 19:
            period_closes = closes[i - 19 : i + 1]
            mean = sum(period_closes) / len(period_closes)
            variance = sum((x - mean) ** 2 for x in period_closes) / len(period_closes)
            std_dev = math.sqrt(variance)
            enriched["volatility_20"] = round(std_dev, 8)
            # 波动率百分比
            if mean > 0:
                enriched["volatility_20_pct"] = round((std_dev / mean) * 100, 4)

        result.append(enriched)

    return result


