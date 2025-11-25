import asyncio

from crypto_analyzer.config import (
    BINANCE_MAX_CONCURRENT_REQUESTS,
    OKX_MAX_CONCURRENT_REQUESTS,
)


class AsyncConcurrencyLimiter:
    def __init__(self, max_concurrent: int) -> None:
        if max_concurrent < 1:
            raise ValueError("max_concurrent must be >= 1")
        self._sem = asyncio.Semaphore(max_concurrent)

    async def __aenter__(self):
        await self._sem.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self._sem.release()
        return False


binance_public_limiter = AsyncConcurrencyLimiter(BINANCE_MAX_CONCURRENT_REQUESTS)
okx_public_limiter = AsyncConcurrencyLimiter(OKX_MAX_CONCURRENT_REQUESTS)
