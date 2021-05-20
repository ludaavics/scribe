import logging
import time
from typing import Optional, Sequence, Union

from binance import AsyncClient, BinanceSocketManager
from pydantic import validate_arguments

from .validation import BinanceKlineInterval

logger = logging.getLogger(__name__)


@validate_arguments
async def listen(
    coins: Union[str, Sequence[str]],
    *,
    interval: BinanceKlineInterval = BinanceKlineInterval._1m,
    lifetime: Optional[int] = None,
):
    """
    Opens a websocket to binance and listens for spot, futures and basis prices.

    Args:
        coins: list of crypto pairs to monitor.
        interval: the width of the klines / candlesticks.
        lifetime: maximum lifetime, in seconds, of the socket.
    """
    if isinstance(coins, str):
        coins = [coins]
    client = await AsyncClient.create()
    socket_manager = BinanceSocketManager(client)
    socket = socket_manager.multiplex_socket(
        [f"{coin.lower()}@kline_{interval}" for coin in coins]
    )
    msg = (
        f"Opening a {(str(lifetime) + 's') if lifetime else ''} websocket "
        f"to binance, for candleticks on {', '.join(coins)}."
    )
    logger.info(msg)
    async with socket:
        end_time = (time.time() + lifetime) if lifetime else float("inf")
        while time.time() < end_time:

            res = await socket.recv()
            logger.debug(res)

    await client.close_connection()
