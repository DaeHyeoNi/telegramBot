import json
import logging
from dataclasses import dataclass
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup


@dataclass
class RobinhoodConfig:
    """Robinhood 설정 데이터"""

    url_format: str = "https://robinhood.com/us/en/stocks/{}/"
    api_url: str = (
        "https://bonfire.robinhood.com/instruments/{}/detail-page-live-updating-data/"
    )
    data_file: str = "robinhood_data.json"
    headers: Dict = None

    def __post_init__(self):
        self.headers = {
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "origin": "https://robinhood.com",
            "referer": "https://robinhood.com/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        }


class RobinHood:
    """Robinhood API 클라이언트"""

    def __init__(self, config: RobinhoodConfig = None):
        self.config = config or RobinhoodConfig()
        self.access_token: str = ""
        self.instruments: Dict = {}

    def load_data(self) -> None:
        """저장된 데이터를 로드합니다."""
        try:
            with open(self.config.data_file, "r") as f:
                data = json.load(f)
                self.access_token = data["access_token"]
                self.instruments = data["instruments"]
        except FileNotFoundError:
            logging.info(f"Creating new {self.config.data_file}")
            self.save_data()

    def save_data(self) -> None:
        """현재 데이터를 파일에 저장합니다."""
        with open(self.config.data_file, "w") as f:
            json.dump(
                {
                    "access_token": self.access_token,
                    "instruments": self.instruments,
                },
                f,
                indent=2,
            )

    def renew_access_token(self) -> None:
        """액세스 토큰을 갱신합니다."""
        try:
            res = requests.get(self.config.url_format.format("NVDA"))
            res.raise_for_status()

            soup = BeautifulSoup(res.text, "html.parser")
            next_data = self._extract_next_data(soup)

            if not next_data:
                raise ValueError("No __NEXT_DATA__ found")

            token = next_data["props"]["pageProps"]["dehydratedState"]["queries"][0][
                "state"
            ]["data"]
            self.access_token = token
            self.save_data()

        except Exception as e:
            logging.error(f"Failed to renew access token: {str(e)}")
            raise

    def get_instrument_id(self, ticker: str) -> Optional[str]:
        """종목 ID를 조회합니다."""
        if instrument_id := self.instruments.get(ticker):
            return instrument_id

        try:
            res = requests.get(self.config.url_format.format(ticker))
            if res.status_code == 404:
                return None
            res.raise_for_status()

            soup = BeautifulSoup(res.text, "html.parser")
            instrument_id = self._extract_instrument_id(soup)

            if instrument_id:
                self.instruments[ticker] = instrument_id
                self.save_data()
                return instrument_id

        except Exception as e:
            logging.error(f"Failed to get instrument ID for {ticker}: {str(e)}")
            return None

    def get_data(self, ticker: str, is_retry: bool = False) -> Optional[Dict]:
        """종목 데이터를 조회합니다."""
        try:
            instrument_id = self.get_instrument_id(ticker)
            if not instrument_id:
                return None

            headers = {
                **self.config.headers,
                "authorization": f"Bearer {self.access_token}",
            }
            params = {
                "display_span": "day",
                "hide_extended_hours": "false",
            }

            response = requests.get(
                self.config.api_url.format(instrument_id),
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

        except requests.HTTPError as e:
            if is_retry:
                raise e
            logging.info(f"Token expired, renewing for {ticker}")
            self.renew_access_token()
            return self.get_data(ticker, is_retry=True)

        except Exception as e:
            logging.error(f"Failed to get data for {ticker}: {str(e)}")
            return None

    @staticmethod
    def _extract_next_data(soup: BeautifulSoup) -> Optional[Dict]:
        """__NEXT_DATA__ 스크립트를 추출합니다."""
        if script := soup.find("script", {"id": "__NEXT_DATA__"}):
            return json.loads(script.string)
        return None

    @staticmethod
    def _extract_instrument_id(soup: BeautifulSoup) -> Optional[str]:
        """instrument ID를 추출합니다."""
        if meta := soup.find("meta", {"name": "twitter:app:url:iphone"}):
            return meta["content"].replace("robinhood://instrument?id=", "")
        return None
