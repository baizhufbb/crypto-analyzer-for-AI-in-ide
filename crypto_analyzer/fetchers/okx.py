from typing import Any, Dict, List, Optional

import requests
import httpx

from crypto_analyzer.config import OKX_BASE_URL


def _normalize_okx_interval(interval: str) -> str:
    """OKX 分钟级别使用小写 m，其余周期使用大写。"""
    interval = interval.strip()
    if interval.lower().endswith("m"):
        return interval.lower()
    return interval.upper()


def list_okx_symbols(
    inst_type: str = "SWAP",
    state: str = "live",
    quote_assets: Optional[List[str]] = None,
) -> List[str]:
    """列出 OKX 指定类型合约的全部交易对。"""
    response = requests.get(
        f"{OKX_BASE_URL}/api/v5/public/instruments",
        params={"instType": inst_type},
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()

    if result.get("code") != "0":
        raise ValueError(f"OKX API 错误：{result.get('msg', '未知错误')}")

    symbols = []
    quote_set = {q.upper() for q in quote_assets} if quote_assets else None

    for item in result.get("data", []):
        if state and item.get("state") != state:
            continue
        inst_id = item.get("instId")
        if not inst_id:
            continue
        if quote_set:
            parts = inst_id.split("-")
            quote = parts[1] if len(parts) >= 2 else ""
            if quote.upper() not in quote_set:
                continue
        symbols.append(inst_id)

    return symbols


async def fetch_okx_klines_async(
    client: httpx.AsyncClient,
    symbol: str,
    interval: str,
    limit: int,
) -> List[Dict[str, Any]]:
    interval_okx = _normalize_okx_interval(interval)
    response = await client.get(
        f"{OKX_BASE_URL}/api/v5/market/candles",
        params={"instId": symbol, "bar": interval_okx, "limit": str(limit)},
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()

    if result.get("code") != "0":
        raise ValueError(f"OKX API 错误：{result.get('msg', '未知错误')}")

    raw_klines = result.get("data", [])
    if not isinstance(raw_klines, list):
        raise ValueError(f"API 返回格式错误：期望列表，得到 {type(raw_klines)}")

    normalized: List[Dict[str, Any]] = []
    for entry in raw_klines:
        if not isinstance(entry, list) or len(entry) < 8:
            raise ValueError(f"K 线数据格式错误：{entry}")

        open_time_ms = int(entry[0])
        close_time_ms = open_time_ms + 1

        normalized.append(
            {
                "symbol": symbol.upper(),
                "open_time": open_time_ms,
                "open": float(entry[1]),
                "high": float(entry[2]),
                "low": float(entry[3]),
                "close": float(entry[4]),
                "volume": float(entry[5]),
                "close_time": close_time_ms,
                "quote_volume": float(entry[6]),
                "trades": int(float(entry[7])),
            }
        )

    # OKX API 返回的数据是按时间倒序（最新的在前），
    return normalized


async def fetch_okx_24hr_ticker_async(
    client: httpx.AsyncClient,
    symbol: str,
) -> Dict[str, Any]:
    response = await client.get(
        f"{OKX_BASE_URL}/api/v5/market/ticker",
        params={"instId": symbol},
        timeout=10,
    )
    response.raise_for_status()
    result = response.json()

    if result.get("code") != "0":
        raise ValueError(f"OKX API 错误：{result.get('msg', '未知错误')}")

    ticker_data = result.get("data", [{}])[0]

    return {
        "symbol": ticker_data.get("instId", symbol.upper()),
        "priceChange": float(ticker_data.get("last", 0)) - float(ticker_data.get("open24h", 0)),
        "priceChangePercent": float(ticker_data.get("changePercent24h", 0)) * 100,
        "lastPrice": float(ticker_data.get("last", 0)),
        "highPrice": float(ticker_data.get("high24h", 0)),
        "lowPrice": float(ticker_data.get("low24h", 0)),
        "volume": float(ticker_data.get("vol24h", 0)),
        "quoteVolume": float(ticker_data.get("volCcy24h", 0)),
        "openPrice": float(ticker_data.get("open24h", 0)),
        "prevClosePrice": float(ticker_data.get("open24h", 0)),
    }


async def fetch_okx_funding_rate_async(
    client: httpx.AsyncClient,
    symbol: str,
) -> Dict[str, Any]:
    response = await client.get(
        f"{OKX_BASE_URL}/api/v5/public/funding-rate",
        params={"instId": symbol},
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()

    if result.get("code") != "0":
        raise ValueError(
            f"OKX API 错误：{result.get('msg', '未知错误')}。请确认交易对格式正确（合约格式：BTC-USDT-SWAP）"
        )

    funding_data = result.get("data", [{}])
    if not funding_data:
        raise ValueError(f"OKX 资金费率接口返回空数据，请确认交易对 {symbol} 是否为合约交易对")

    funding_data = funding_data[0]

    return {
        "symbol": funding_data.get("instId", symbol.upper()),
        "lastFundingRate": float(funding_data.get("fundingRate", 0)),
        "nextFundingTime": int(funding_data.get("nextFundingTime", 0)),
        "markPrice": float(funding_data.get("markPx", 0)),
        "indexPrice": float(funding_data.get("idxPx", 0)),
    }


async def fetch_okx_open_interest_async(
    client: httpx.AsyncClient,
    symbol: str,
) -> Dict[str, Any]:
    response = await client.get(
        f"{OKX_BASE_URL}/api/v5/public/open-interest",
        params={"instId": symbol},
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()

    if result.get("code") != "0":
        raise ValueError(
            f"OKX API 错误：{result.get('msg', '未知错误')}。请确认交易对格式正确（合约格式：BTC-USDT-SWAP）"
        )

    oi_data = result.get("data", [{}])
    if not oi_data:
        raise ValueError(f"OKX 持仓量接口返回空数据，请确认交易对 {symbol} 是否为合约交易对")

    oi_data = oi_data[0]

    return {
        "symbol": oi_data.get("instId", symbol.upper()),
        "openInterest": float(oi_data.get("oi", 0)),
        "timestamp": int(oi_data.get("ts", 0)),
    }


async def fetch_okx_current_price_async(
    client: httpx.AsyncClient,
    symbol: str,
) -> Dict[str, Any]:
    response = await client.get(
        f"{OKX_BASE_URL}/api/v5/market/ticker",
        params={"instId": symbol},
        timeout=10,
    )
    response.raise_for_status()
    result = response.json()

    if result.get("code") != "0":
        raise ValueError(f"OKX API 错误：{result.get('msg', '未知错误')}")

    ticker_data = result.get("data", [{}])[0]

    return {
        "symbol": ticker_data.get("instId", symbol.upper()),
        "price": float(ticker_data.get("last", 0)),
    }


async def fetch_okx_order_book_async(
    client: httpx.AsyncClient,
    symbol: str,
    limit: int = 20,
) -> Dict[str, Any]:
    response = await client.get(
        f"{OKX_BASE_URL}/api/v5/market/books",
        params={"instId": symbol, "sz": str(limit)},
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()

    if result.get("code") != "0":
        raise ValueError(f"OKX API 错误：{result.get('msg', '未知错误')}")

    depth_data = result.get("data", [{}])[0]
    bids = depth_data.get("bids", [])
    asks = depth_data.get("asks", [])

    bids_parsed = [[float(bid[0]), float(bid[1])] for bid in bids if len(bid) >= 2]
    asks_parsed = [[float(ask[0]), float(ask[1])] for ask in asks if len(ask) >= 2]

    bid_total_qty = sum(bid[1] for bid in bids_parsed)
    ask_total_qty = sum(ask[1] for ask in asks_parsed)

    return {
        "symbol": depth_data.get("instId", symbol.upper()),
        "lastUpdateId": int(depth_data.get("ts", 0)),
        "bids": bids_parsed,
        "asks": asks_parsed,
        "bid_total_qty": round(bid_total_qty, 8),
        "ask_total_qty": round(ask_total_qty, 8),
    }


