import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional, Sequence, Union

import aioredis
from binance import AsyncClient, BinanceSocketManager
from pydantic import validate_arguments

from .validation import BinanceKlineInterval

logger = logging.getLogger(__name__)


@validate_arguments
async def bars(
    coins: Union[str, Sequence[str]],
    *,
    broker_url: str,
    bar_intervals: Union[
        BinanceKlineInterval, Sequence[BinanceKlineInterval]
    ] = BinanceKlineInterval._1m,
    lifetime: Optional[int] = None,
):
    """
    Opens a websocket to binance and listens for spot price bars.

    Args:
        coins: list of crypto pairs to monitor.
        bar_intervals: the widths of the klines / candlesticks.
        lifetime: maximum lifetime, in seconds, of the socket.
    """
    if isinstance(coins, str):
        coins = [coins]
    if isinstance(bar_intervals, BinanceKlineInterval):
        bar_intervals = [bar_intervals]
    redis_client = aioredis.from_url(broker_url)
    binance_client = await AsyncClient.create()
    socket_manager = BinanceSocketManager(binance_client)
    socket = socket_manager.multiplex_socket(
        [
            f"{coin.lower()}@kline_{interval}"
            for coin in coins
            for interval in bar_intervals
        ]
    )
    msg = (
        f"Opening a {(str(lifetime) + 's') if lifetime else ''} websocket "
        f"to binance, for candleticks on {', '.join(coins)}."
    )
    logger.info(msg)
    async with socket:
        end_time = (time.time() + lifetime) if lifetime else float("inf")
        while time.time() < end_time:

            datastream = await socket.recv()
            logger.debug(datastream)

            # publish to redis
            kline = datastream["data"]["k"]
            bar = {
                "start_time": datetime.fromtimestamp(
                    kline["t"] / 1000, timezone.utc
                ).isoformat(),
                "end_time": datetime.fromtimestamp(
                    kline["T"] / 1000, timezone.utc
                ).isoformat(),
                "open": kline["o"],
                "high": kline["h"],
                "low": kline["l"],
                "close": kline["c"],
                "base_volume": kline["v"],
                "quote_volume": kline["q"],
                "trades": kline["n"],
                "is_closed": kline["x"],
            }
            channel = f"binance/{kline['s'].lower()}/spot/{kline['i']}"
            await redis_client.publish(channel, json.dumps(bar))

    await binance_client.close_connection()
