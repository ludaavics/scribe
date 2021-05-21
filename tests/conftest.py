import asyncio
import os

import pytest

import scribe


@pytest.fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()


@pytest.fixture(scope="session")
def redis_url():
    return os.getenv("REDIS_URL_TEST", "redis://localhost:6379/test")


@pytest.fixture(scope="session")
async def scribe_binance(redis_url):
    coins = ["btcusdt", "btcbnb"]
    task = asyncio.create_task(
        scribe.platforms.binance.bars(coins, broker_url=redis_url)
    )
    yield
    task.cancel()
