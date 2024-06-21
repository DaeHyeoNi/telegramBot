from typing import Dict, Hashable

import pandas as pd
import requests

CSV_FILE_NAME = "stock_data.csv"


def get_stock_data() -> None:
    code = _get_otp()
    download_url = "http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd"
    res = requests.post(download_url, data={"code": code})
    res.raise_for_status()
    decoded_content = res.content.decode("euc-kr")
    with open(CSV_FILE_NAME, "w", encoding="utf-8") as f:
        f.write(decoded_content)


def _get_otp() -> str:
    req_url = "http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd"
    payload = {
        "locale": "ko_KR",
        "mktId": "ALL",
        "share": 1,
        "csvxls_isNo": "false",
        "name": "fileDown",
        "url": "dbms/MDC/STAT/standard/MDCSTAT01901",
    }
    res = requests.post(req_url, data=payload)
    res.raise_for_status()
    return res.text


def apply_custom_fixtures(df_code: Dict[Hashable, int]) -> Dict[Hashable, int]:
    df_code["곱버스"] = ["252670"]
    return df_code


def create() -> Dict[Hashable, int]:
    try:
        get_stock_data()
    except Exception as e:
        print(e)
    stock_data = pd.read_csv(
        CSV_FILE_NAME, usecols=["한글 종목약명", "단축코드"], encoding="utf8"
    )
    df_code: Dict[Hashable, int] = stock_data.set_index("한글 종목약명").T.to_dict("list")
    df_code = apply_custom_fixtures(df_code)
    return df_code
