import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional, Sequence, Union

import aioredis
from binance import AsyncClient, BinanceSocketManager
from pydantic import validate_arguments

from .validation import BinanceFuturesType, BinanceKlineInterval

logger = logging.getLogger(__name__)


@validate_arguments
async def stream_bars(
    pairs: Union[str, Sequence[str]],
    *,
    broker_url: str,
    intervals: Union[
        BinanceKlineInterval, Sequence[BinanceKlineInterval]
    ] = BinanceKlineInterval._1m,
    spot: bool = True,
    usd_m: bool = True,
    coin_m: bool = False,
    lifetime: Optional[int] = None,
):
    """
    Streams spot and futures price bars from binance.

    Args:
        pairs: list of crypto-currency pairs to monitor.
        broker_url: URL of the pub/sub broker.
        intervals: the widths of the klines / candlesticks.
        spot: True to include spot prices.
        usd_m: True to include usd margined futures.
        coin_m: True to include coin margined futures.
        lifetime: maximum lifetime, in seconds, of the socket.
    """
    if spot and not (usd_m or coin_m):
        tasks = [
            stream_spot_bars(
                pairs,
                broker_url=broker_url,
                intervals=intervals,
                lifetime=lifetime,
            )
        ]
    else:
        tasks = []
        if usd_m:
            tasks += [
                stream_futures_bars(
                    pairs,
                    broker_url=broker_url,
                    intervals=intervals,
                    include_spot=spot,
                    futures_type=BinanceFuturesType.usd_m,
                    lifetime=lifetime,
                )
            ]
        if coin_m:
            tasks += [
                stream_futures_bars(
                    pairs,
                    broker_url=broker_url,
                    intervals=intervals,
                    include_spot=(spot and not usd_m),
                    futures_type=BinanceFuturesType.coin_m,
                    lifetime=lifetime,
                )
            ]
    await asyncio.gather(*[asyncio.create_task(task) for task in tasks])


@validate_arguments
async def stream_spot_bars(
    pairs: Union[str, Sequence[str]],
    *,
    broker_url: str,
    intervals: Union[
        BinanceKlineInterval, Sequence[BinanceKlineInterval]
    ] = BinanceKlineInterval._1m,
    lifetime: Optional[int] = None,
):
    """
    Streams spot price bars from binance.

    Args:
        pairs: list of crypto-currency pairs to monitor.
        broker_url: URL of the pub/sub broker.
        intervals: the widths of the klines / candlesticks.
        lifetime: maximum lifetime, in seconds, of the socket.
    """
    if isinstance(pairs, str):
        pairs = [pairs]
    if isinstance(intervals, BinanceKlineInterval):
        intervals = [intervals]
    redis_client = aioredis.from_url(broker_url)
    binance_client = await AsyncClient.create()
    socket_manager = BinanceSocketManager(binance_client)
    streams = [
        f"{pair.lower()}@kline_{interval}" for pair in pairs for interval in intervals
    ]
    socket = socket_manager.multiplex_socket(streams)
    msg = (
        f"Opening a {(str(lifetime) + 's') if lifetime else ''} websocket "
        f"to binance, for candlesticks on {', '.join(pairs)} spot prices."
    )
    logger.info(msg)
    async with socket:
        end_time = (time.time() + lifetime) if lifetime else float("inf")
        while time.time() < end_time:
            message = await socket.recv()
            logger.debug(message)

            # publish to redis
            event = message["data"]
            kline = event["k"]
            pair = kline["s"].lower()
            expiry = "spot"
            event_to_publish = {
                "type": "bar",
                "time": datetime.fromtimestamp(
                    event["E"] / 1000, timezone.utc
                ).isoformat(),
                "pair": pair,
                "expiry": expiry,
                "bar": {
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
                },
            }
            channel = f"binance/{pair}/{expiry}/{kline['i']}"
            msg = f"{channel} <-- {json.dumps(event_to_publish)}"
            logger.debug(msg)
            await redis_client.publish(channel, json.dumps(event_to_publish))

    await binance_client.close_connection()


@validate_arguments
async def stream_futures_bars(
    pairs: Union[str, Sequence[str]],
    *,
    broker_url: str,
    include_spot: bool = True,
    intervals: Union[
        BinanceKlineInterval, Sequence[BinanceKlineInterval]
    ] = BinanceKlineInterval._1m,
    futures_type: BinanceFuturesType = BinanceFuturesType.usd_m,
    lifetime: Optional[int] = None,
):
    """
    Streams futures price bars from binance.

    Args:
        pairs: list of crypto pairs to monitor.
        broker_url: where to publish updates.
        include_spot: True to also publish spot bars.
        intervals: the widths of the klines / candlesticks.
        futures_type: USD-margined or coin-margined futures.
        lifetime: maximum lifetime, in seconds, of the socket.
    """
    if isinstance(pairs, str):
        pairs = [pairs]
    if isinstance(intervals, BinanceKlineInterval):
        intervals = [intervals]
    redis_client = aioredis.from_url(broker_url)
    binance_client = await AsyncClient.create()
    socket_manager = BinanceSocketManager(binance_client)

    streams = (
        [f"{pair.lower()}@kline_{interval}" for pair in pairs for interval in intervals]
        if include_spot
        else []
    )
    streams += [
        f"{pair.lower()}_{contract}@continuousKline_{interval}"
        for pair in pairs
        for contract in ["perpetual", "current_quarter", "next_quarter"]
        for interval in intervals
    ]
    socket = socket_manager.futures_multiplex_socket(streams)
    msg = (
        f"Opening a {(str(lifetime) + 's') if lifetime else ''} websocket "
        f"to binance, for candlesticks on {', '.join(pairs)} "
        f"{'spot and ' if include_spot else ''}"
        f"{'USD' if futures_type == BinanceFuturesType.usd_m else 'coin'}-"
        "margined futures."
    )
    logger.info(msg)
    async with socket:
        end_time = (time.time() + lifetime) if lifetime else float("inf")
        while time.time() < end_time:
            message = await socket.recv()
            logger.debug(message)

            event = message["data"]
            event_type = event["e"]
            if event_type == "continuous_kline":
                pair = event["ps"].lower()
                expiry = event["ct"].lower()
            else:
                assert event_type == "kline"
                pair = event["s"]
                expiry = "spot"

            # publish to redis
            kline = event["k"]
            event_to_publish = {
                "type": "bar",
                "time": datetime.fromtimestamp(
                    event["E"] / 1000, timezone.utc
                ).isoformat(),
                "pair": pair,
                "expiry": expiry,
                "bar": {
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
                },
            }
            channel = f"binance/{pair}/{expiry}/{kline['i']}"
            msg = f"{channel} <-- {json.dumps(event_to_publish)}"
            logger.debug(msg)
            await redis_client.publish(channel, json.dumps(event_to_publish))

    await binance_client.close_connection()
