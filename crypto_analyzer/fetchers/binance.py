from typing import Any, Dict, List, Optional

import requests
import httpx

from crypto_analyzer.config import BINANCE_BASE_URL
from crypto_analyzer.rate_limiter import binance_public_limiter


def list_binance_symbols(
    contract_type: str = "PERPETUAL",
    status: str = "TRADING",
    quote_assets: Optional[List[str]] = None,
) -> List[str]:
    """列出 Binance USDⓈ-M 合约的所有交易对。"""
    response = requests.get(f"{BINANCE_BASE_URL}/fapi/v1/exchangeInfo", timeout=30)
    response.raise_for_status()
    data = response.json()

    symbols: List[str] = []
    quote_set = {q.upper() for q in quote_assets} if quote_assets else None

    for item in data.get("symbols", []):
        if contract_type and item.get("contractType") != contract_type:
            continue
        if status and item.get("status") != status:
            continue
        if quote_set and item.get("quoteAsset") not in quote_set:
            continue
        sym = item.get("symbol")
        if sym:
            symbols.append(sym)

    return symbols


async def fetch_binance_klines_async(
    client: httpx.AsyncClient,
    symbol: str,
    interval: str,
    limit: int,
) -> List[Dict[str, Any]]:
    async with binance_public_limiter:
        response = await client.get(
            f"{BINANCE_BASE_URL}/fapi/v1/klines",
            params={"symbol": symbol.upper(), "interval": interval, "limit": limit},
            timeout=30,
        )
    response.raise_for_status()
    raw_klines = response.json()

    if not isinstance(raw_klines, list):
        raise ValueError(f"API 返回格式错误：期望列表，得到 {type(raw_klines)}")

    normalized: List[Dict[str, Any]] = []
    for entry in raw_klines:
        if not isinstance(entry, list) or len(entry) < 9:
            raise ValueError(f"K 线数据格式错误：{entry}")

        normalized.append(
            {
                "symbol": symbol.upper(),
                "open_time": int(entry[0]),
                "open": float(entry[1]),
                "high": float(entry[2]),
                "low": float(entry[3]),
                "close": float(entry[4]),
                "volume": float(entry[5]),
                "close_time": int(entry[6]),
                "quote_volume": float(entry[7]),
                "trades": int(entry[8]),
            }
        )
    
    # Binance API 返回的数据是按时间正序（最旧的在前），
    # 我们统一转换为时间倒序（最新的在前），以便与 OKX 保持一致。
    normalized.reverse()
    
    return normalized


async def fetch_binance_24hr_ticker_async(
    client: httpx.AsyncClient,
    symbol: str,
) -> Dict[str, Any]:
    async with binance_public_limiter:
        response = await client.get(
            f"{BINANCE_BASE_URL}/fapi/v1/ticker/24hr",
            params={"symbol": symbol.upper()},
            timeout=30,
        )
    response.raise_for_status()
    ticker_data = response.json()

    if not isinstance(ticker_data, dict):
        raise ValueError(f"API 返回格式错误：期望字典，得到 {type(ticker_data)}")

    return {
        "symbol": ticker_data.get("symbol", symbol.upper()),
        "priceChange": float(ticker_data.get("priceChange", 0)),
        "priceChangePercent": float(ticker_data.get("priceChangePercent", 0)),
        "lastPrice": float(ticker_data.get("lastPrice", 0)),
        "highPrice": float(ticker_data.get("highPrice", 0)),
        "lowPrice": float(ticker_data.get("lowPrice", 0)),
        "volume": float(ticker_data.get("volume", 0)),
        "quoteVolume": float(ticker_data.get("quoteVolume", 0)),
        "count": int(ticker_data.get("count", 0)),
        "openPrice": float(ticker_data.get("openPrice", 0)),
        "prevClosePrice": float(ticker_data.get("prevClosePrice", 0)),
    }


async def fetch_binance_funding_rate_async(
    client: httpx.AsyncClient,
    symbol: str,
) -> Dict[str, Any]:
    async with binance_public_limiter:
        response = await client.get(
            f"{BINANCE_BASE_URL}/fapi/v1/premiumIndex",
            params={"symbol": symbol.upper()},
            timeout=30,
        )
    response.raise_for_status()
    premium_data = response.json()

    if not isinstance(premium_data, dict):
        raise ValueError(f"API 返回格式错误：期望字典，得到 {type(premium_data)}")

    return {
        "symbol": premium_data.get("symbol", symbol.upper()),
        "lastFundingRate": float(premium_data.get("lastFundingRate", 0)),
        "nextFundingTime": int(premium_data.get("nextFundingTime", 0)),
        "markPrice": float(premium_data.get("markPrice", 0)),
        "indexPrice": float(premium_data.get("indexPrice", 0)),
    }


async def fetch_binance_open_interest_async(
    client: httpx.AsyncClient,
    symbol: str,
) -> Dict[str, Any]:
    async with binance_public_limiter:
        response = await client.get(
            f"{BINANCE_BASE_URL}/fapi/v1/openInterest",
            params={"symbol": symbol.upper()},
            timeout=30,
        )
    response.raise_for_status()
    oi_data = response.json()

    if not isinstance(oi_data, dict):
        raise ValueError(f"API 返回格式错误：期望字典，得到 {type(oi_data)}")

    return {
        "symbol": oi_data.get("symbol", symbol.upper()),
        "openInterest": float(oi_data.get("openInterest", 0)),
        "timestamp": int(oi_data.get("time", 0)),
    }


async def fetch_binance_current_price_async(
    client: httpx.AsyncClient,
    symbol: str,
) -> Dict[str, Any]:
    async with binance_public_limiter:
        response = await client.get(
            f"{BINANCE_BASE_URL}/fapi/v1/ticker/price",
            params={"symbol": symbol.upper()},
            timeout=30,
        )
    response.raise_for_status()
    price_data = response.json()

    if not isinstance(price_data, dict):
        raise ValueError(f"API 返回格式错误：期望字典，得到 {type(price_data)}")

    return {
        "symbol": price_data.get("symbol", symbol.upper()),
        "price": float(price_data.get("price", 0)),
    }


async def fetch_binance_order_book_async(
    client: httpx.AsyncClient,
    symbol: str,
    limit: int = 20,
) -> Dict[str, Any]:
    async with binance_public_limiter:
        response = await client.get(
            f"{BINANCE_BASE_URL}/fapi/v1/depth",
            params={"symbol": symbol.upper(), "limit": limit},
            timeout=30,
        )
    response.raise_for_status()
    depth_data = response.json()

    if not isinstance(depth_data, dict):
        raise ValueError(f"API 返回格式错误：期望字典，得到 {type(depth_data)}")

    bids = depth_data.get("bids", [])
    asks = depth_data.get("asks", [])

    if not isinstance(bids, list) or not isinstance(asks, list):
        raise ValueError("订单簿格式错误：bids 或 asks 不是列表")

    bid_total_qty = sum(float(bid[1]) for bid in bids if len(bid) >= 2)
    ask_total_qty = sum(float(ask[1]) for ask in asks if len(ask) >= 2)

    bids_parsed = [[float(bid[0]), float(bid[1])] for bid in bids if len(bid) >= 2]
    asks_parsed = [[float(ask[0]), float(ask[1])] for ask in asks if len(ask) >= 2]

    return {
        "symbol": depth_data.get("symbol", symbol.upper()),
        "lastUpdateId": int(depth_data.get("lastUpdateId", 0)),
        "bids": bids_parsed,
        "asks": asks_parsed,
        "bid_total_qty": round(bid_total_qty, 8),
        "ask_total_qty": round(ask_total_qty, 8),
    }


