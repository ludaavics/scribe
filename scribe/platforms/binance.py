import logging
import time
from typing import Iterable, Optional

from binance import AsyncClient, BinanceSocketManager
from pydantic import validate_arguments

from .validation import BinanceKlineInterval

logger = logging.getLogger(__name__)


@validate_arguments
async def listen(
    coins: Iterable[str],
    *,
    interval: BinanceKlineInterval = BinanceKlineInterval._1m,
    lifetime: Optional[int] = None,
):
    """
    Opens a websocket to binance and listens for spot, futures and basis prices.

    Args:
        coins: list of crypto pairs to monitor.
        interval: the width of the klines / candlesticks.
        liftime: maximum lifetime, in seconds, of the socket.
    """
    client = await AsyncClient.create()
    socket_manager = BinanceSocketManager(client)
    multiplex_socket = socket_manager.multiplex_socket(
        [f"{coin.lower()}@kline_{interval}" for coin in coins]
    )
    msg = (
        f"Opening a {(str(lifetime) + 's') if lifetime else ''}"
        f"websocket to binance, for candleticks on "
        ", ".join(coins)
    )
    logger.info(msg)
    async with multiplex_socket as socket:
        end_time = (time.time() + lifetime) if lifetime else float("inf")
        while time.time() < end_time:
            res = await socket.recv()
            print(res)

    await client.close_connection()
