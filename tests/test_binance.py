import logging

import aioredis
import pytest

import scribe

logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "coins, spot, usd_m, coin_m, intervals",
    [
        ("bnbbtc", True, False, False, "1m"),
        (["ethusdt"], True, False, False, ["3m"]),
        ("btcusdt", False, False, True, ["1m"]),
        (["btcusdt", "bnbusd"], True, True, True, ["1m", "3m"]),
    ],
)
@pytest.mark.asyncio
async def test_stream_bars(caplog, coins, spot, usd_m, coin_m, intervals, redis_url):
    with caplog.at_level(logging.DEBUG, logger="scribe.platforms.binance"):
        await scribe.platforms.binance.stream_bars(
            coins,
            broker_url=redis_url,
            spot=spot,
            usd_m=usd_m,
            coin_m=coin_m,
            intervals=intervals,
            lifetime=5,
        )

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
