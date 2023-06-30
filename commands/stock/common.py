from enum import Enum
from dataclasses import dataclass
from typing import Optional


class KoreanMarketEnum(Enum):
    KOSPI = "KOSPI"
    KOSDAQ = "KOSDAQ"


class Country(Enum):
    KOREA = "KRW"
    USA = "USD"
    JAPAN = "JPY"


@dataclass
class KoreanMarketPoint:
    closePrice: Optional[str] = None
    fluctuationsRatio: Optional[str] = None
    compareToPreviousClosePrice: Optional[str] = None
