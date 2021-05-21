import logging

import aioredis
import pytest

import scribe

logger = logging.getLogger(__name__)


@pytest.mark.parametrize("coins", ["bnbbtc", ["bnbbtc"], ["btcusdt", "bnbusd"]])
@pytest.mark.asyncio
async def test_listen(caplog, coins, redis_url):
    with caplog.at_level(logging.DEBUG, logger="scribe.platforms.binance"):
        await scribe.platforms.binance.bars(coins, broker_url=redis_url, lifetime=5)

        # make sure we logged at least one bar
        seen = False
        for record in caplog.records:
            if not isinstance(record.msg, dict):
                continue
            if not ("stream" in record.msg):
                continue
            seen = True
            break
        assert seen


@pytest.mark.asyncio
async def test_subscribe(scribe_binance, redis_url):
    redis_client = aioredis.from_url(redis_url)
    channel = redis_client.pubsub()
    await channel.psubscribe("binance/*")
    async for message in channel.listen():
        # make sure we receive at least one message
        if message["type"] == "pmessage":
            break
