from enum import Enum


class KoreanMarketType(Enum):
    KOSPI = "KOSPI"
    KOSDAQ = "KOSDAQ"


class Country(Enum):
    KOREA = "KRW"
    USA = "USD"
    JAPAN = "JPY"
