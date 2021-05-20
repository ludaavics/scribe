import logging

import pytest

import scribe


@pytest.mark.parametrize("coins", ["bnbbtc", ["bnbbtc"], ["btcusdt", "bnbusd"]])
@pytest.mark.asyncio
async def test_listen(caplog, coins):
    with caplog.at_level(logging.DEBUG, logger="scribe.platforms.binance"):
        await scribe.platforms.binance.listen(coins, lifetime=5)

        # make sure we logged at least one candlestick
        seen = False
        for record in caplog.records:
            if not isinstance(record.msg, dict):
                continue
            if not ("stream" in record.msg):
                continue
            seen = True
            break
        assert seen
