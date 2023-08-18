from enum import Enum


class ChartType(Enum):
    REALTIME = "실시간"
    DAY = "일봉"
    WEEK = "주봉"
    MONTHLY = "월봉"
    MONTH_1 = "1개월"
    MONTH_3 = "3개월"
    YEAR = "1년"
    YERR_3 = "3년"
    YEAR_10 = "10년"
