from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class PlatformName(str, Enum):
    binance = "binance"


class ScribeConfiguration(BaseModel):
    class Platform(BaseModel):
        name: PlatformName
        pairs: Optional[List[str]]
        options: Optional[Dict[str, Any]]

    broker_url: str
    pairs: List[str]
    platforms: List[Platform]


class BinanceKlineInterval(str, Enum):
    _1m = "1m"
    _3m = "3m"
    _5m = "5m"
    _15m = "15m"
    _30m = "30m"
    _1h = "1h"
    _2h = "2h"
    _4h = "4h"
    _6h = "6h"
    _8h = "8h"
    _12h = "12h"
    _1d = "1d"
    _3d = "3d"
    _1w = "1w"
    _1M = "1M"  # one month


class BinanceFuturesType(str, Enum):
    usd_m = "usd_m"
    coin_m = "coin_m"
