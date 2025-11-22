import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

from crypto_analyzer.volatility_analysis import (
    detect_volatility_expansion_signals,
    format_volatility_analysis,
)


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def latest_kline(klines: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    data = list(klines)
    if not data:
        raise ValueError("No kline data found in JSON")
    
    # 自动判断顺序：取 open_time 最大的那个
    first = data[0]
    last = data[-1]
    
    t1 = first.get('open_time', 0)
    t2 = last.get('open_time', 0)
    
    if t1 > t2:
        return first  # 倒序，第一个是最新的
    else:
        return last   # 正序，最后一个是最新的


def order_book_imbalance(order_book: Dict[str, Any], depth: int = 10) -> float:
    bids = order_book.get("bids") or []
    asks = order_book.get("asks") or []
    bid_value = sum(float(price) * float(qty) for price, qty in bids[:depth])
    ask_value = sum(float(price) * float(qty) for price, qty in asks[:depth])
    total = bid_value + ask_value
    return (bid_value - ask_value) / total if total else 0.0


def volume_spike(klines: Iterable[Dict[str, Any]], lookback: int = 20) -> float:
    """计算最后一根K线的成交量相对于过去平均值的倍数"""
    data = list(klines)
    if len(data) < lookback + 1:
        return 0.0
    last_vol = float(data[-1].get('volume', 0))
    # 取前 n 根（不含当前）计算平均
    prev_vols = [float(k.get('volume', 0)) for k in data[-lookback-1:-1]]
    avg_vol = sum(prev_vols) / len(prev_vols) if prev_vols else 0
    return last_vol / avg_vol if avg_vol > 0 else 0.0


def analyze_signals(summary: Dict[str, Any], klines: list) -> Dict[str, Any]:
    """客观识别技术信号，不含主观判断"""
    signals = {}
    
    # 1. RSI 状态
    rsi = summary.get('rsi14')
    if rsi is not None:
        if rsi < 20:
            signals['rsi_status'] = 'extreme_oversold'
            signals['rsi_level'] = '<20'
        elif rsi < 30:
            signals['rsi_status'] = 'oversold'
            signals['rsi_level'] = '20-30'
        elif rsi > 80:
            signals['rsi_status'] = 'extreme_overbought'
            signals['rsi_level'] = '>80'
        elif rsi > 70:
            signals['rsi_status'] = 'overbought'
            signals['rsi_level'] = '70-80'
        elif rsi > 50:
            signals['rsi_status'] = 'bullish'
            signals['rsi_level'] = '50-70'
        elif rsi > 30:
            signals['rsi_status'] = 'bearish'
            signals['rsi_level'] = '30-50'

    # 2. 均线位置关系
    price = summary.get('current_price', 0)
    ma20 = summary.get('ma20')
    ma50 = summary.get('ma50')
    
    if ma20 and ma50 and price:
        # 价格与均线的距离百分比
        signals['price_vs_ma20_pct'] = round(((price - ma20) / ma20) * 100, 2)
        signals['price_vs_ma50_pct'] = round(((price - ma50) / ma50) * 100, 2)
        signals['ma20_vs_ma50_pct'] = round(((ma20 - ma50) / ma50) * 100, 2)
        
        # 趋势判断
        if price > ma20 > ma50:
            signals['trend'] = 'uptrend'
        elif price < ma20 < ma50:
            signals['trend'] = 'downtrend'
        elif ma20 > ma50 and price < ma20:
            signals['trend'] = 'uptrend_pullback'
        elif ma20 < ma50 and price > ma20:
            signals['trend'] = 'downtrend_rebound'
        else:
            signals['trend'] = 'sideways'

    # 3. 成交量比率
    vol_ratio = volume_spike(klines)
    signals['volume_ratio'] = round(vol_ratio, 2)
    if vol_ratio > 3.0:
        signals['volume_status'] = 'extreme_spike'
    elif vol_ratio > 2.0:
        signals['volume_status'] = 'spike'
    elif vol_ratio > 1.5:
        signals['volume_status'] = 'elevated'
    elif vol_ratio < 0.5:
        signals['volume_status'] = 'low'
    else:
        signals['volume_status'] = 'normal'
    
    summary['signals'] = signals
    return summary


def summarize(payload: Dict[str, Any]) -> Dict[str, Any]:
    """提取客观技术指标和市场数据"""
    klines = payload.get("klines", [])
    last = latest_kline(klines)
    ticker = payload.get("ticker_24hr", {})
    funding = payload.get("funding_rate", {})
    open_interest = payload.get("open_interest", {})
    order_book = payload.get("order_book", {})
    current_price_data = payload.get("current_price", {})

    # 优先使用实时价格，如果没有则使用最后一根K线的收盘价
    price = current_price_data.get("price")
    if price is None:
        price = float(last.get("close", 0))

    summary = {
        "symbol": last.get("symbol") or ticker.get("symbol") or current_price_data.get("symbol") or payload.get("exchange", "unknown"),
        "current_price": price,
        "kline_close": float(last.get("close", 0)),
        "open": float(last.get("open", 0)),
        "high": float(last.get("high", 0)),
        "low": float(last.get("low", 0)),
        "ma20": last.get("ma20"),
        "ma50": last.get("ma50"),
        "rsi14": last.get("rsi14"),
        "atr14": last.get("atr14"),
        "atr14_pct": last.get("atr14_pct"),
        "volatility_20_pct": last.get("volatility_20_pct"),
        "change_24h_pct": ticker.get("priceChangePercent"),
        "high_24h": ticker.get("highPrice"),
        "low_24h": ticker.get("lowPrice"),
        "volume_24h": ticker.get("volume"),
        "quote_volume_24h": ticker.get("quoteVolume"),
        "funding_rate": funding.get("lastFundingRate") or funding.get("fundingRate"),
        "next_funding_time": funding.get("nextFundingTime"),
        "open_interest": open_interest.get("openInterest"),
        "order_book_imbalance": order_book_imbalance(order_book),
    }
    
    # 添加客观信号分析
    summary = analyze_signals(summary, klines)
    
    return summary


def format_summary(summary: Dict[str, Any]) -> str:
    """格式化为结构化的技术指标输出"""
    lines = [
        "=" * 60,
        f"Symbol: {summary['symbol']}",
        "=" * 60,
    ]
    
    # 价格信息
    lines.append("\n[PRICE]")
    lines.append(f"Current: {summary.get('current_price', 0)}")
    if summary.get('kline_close') and abs(summary.get('current_price', 0) - summary.get('kline_close', 0)) > 0.0001:
        lines.append(f"K-line Close: {summary.get('kline_close')}")
    lines.append(f"24h Change: {summary.get('change_24h_pct')}%")
    
    # 技术指标
    lines.append("\n[TECHNICAL INDICATORS]")
    lines.append(f"RSI(14): {summary.get('rsi14')}")
    lines.append(f"MA20: {summary.get('ma20')}")
    lines.append(f"MA50: {summary.get('ma50')}")
    
    # 信号分析
    signals = summary.get('signals', {})
    if signals:
        lines.append("\n[SIGNALS]")
        for key, value in signals.items():
            lines.append(f"{key}: {value}")
    
    # 市场数据
    lines.append("\n[MARKET DATA]")
    lines.append(f"Funding Rate: {summary.get('funding_rate')}")
    lines.append(f"Open Interest: {summary.get('open_interest')}")
    lines.append(f"Order Book Imbalance: {summary.get('order_book_imbalance'):.4f}")
    
    # ATR波动率
    if summary.get('atr14'):
        lines.append(f"ATR(14): {summary.get('atr14')}")
    if summary.get('atr14_pct'):
        lines.append(f"ATR(14) %: {summary.get('atr14_pct')}%")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract technical indicators from crypto_fetcher.py JSON output."
    )
    parser.add_argument("--file", required=True, help="Path to the JSON file to summarize")
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of formatted text")
    parser.add_argument("--volatility", action="store_true", help="Include volatility expansion analysis")
    args = parser.parse_args()
    
    path = Path(args.file)
    data = load_json(path)
    summary = summarize(data)
    
    if args.json:
        # JSON输出模式，方便程序化处理
        import json
        output = {"summary": summary}
        if args.volatility:
            vol_result = detect_volatility_expansion_signals(
                klines=data.get("klines", []),
                ticker_24hr=data.get("ticker_24hr"),
                funding_rate=data.get("funding_rate"),
                open_interest=data.get("open_interest"),
                order_book=data.get("order_book")
            )
            output["volatility_analysis"] = vol_result
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        # 格式化文本输出
        print(format_summary(summary))
        
        if args.volatility:
            print("\n" + "=" * 60)
            print("[VOLATILITY ANALYSIS]")
            print("=" * 60)
            vol_result = detect_volatility_expansion_signals(
                klines=data.get("klines", []),
                ticker_24hr=data.get("ticker_24hr"),
                funding_rate=data.get("funding_rate"),
                open_interest=data.get("open_interest"),
                order_book=data.get("order_book")
            )
            print(format_volatility_analysis(vol_result))


if __name__ == "__main__":
    main()

