from typing import Dict
import requests
from bs4 import BeautifulSoup
import json


class RobinHood:
    def __init__(self):
        self.access_token: str = ""
        self.instruments: Dict = {}
        self.url_format = "https://robinhood.com/us/en/stocks/{}/"

    def load_data(self):
        try:
            with open("robinhood_data.json", "r") as f:
                data = json.load(f)
                self.access_token = data["access_token"]
                self.instruments = data["instruments"]
        except FileNotFoundError:
            # create a new file
            self.save_data()

    def save_data(self):
        with open("robinhood_data.json", "w") as f:
            json.dump(
                {
                    "access_token": self.access_token,
                    "instruments": self.instruments,
                },
                f,
                indent=2,
            )

    def renew_access_token(self):
        res = requests.get(self.url_format.format("NVDA"))
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        scripts = soup.find_all("script")
        for s in scripts:
            if s.get("id") == "__NEXT_DATA__":
                next_data = s.string
                break
        else:
            print("No __NEXT_DATA__")

        next_data = json.loads(next_data)
        token = next_data["props"]["pageProps"]["dehydratedState"]["queries"][0][
            "state"
        ]["data"]

        self.access_token = token
        self.save_data()

    def get_instrument_id(self, ticker):
        if id := self.instruments.get(ticker):
            return id

        res = requests.get(self.url_format.format(ticker))
        if res.status_code == 404:
            return None

        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        metas = soup.find_all("meta")
        for m in metas:
            if m.get("name") == "twitter:app:url:iphone":
                instrument_id = m.get("content")
                instrument_id = instrument_id.replace("robinhood://instrument?id=", "")
                self.instruments[ticker] = instrument_id
                self.save_data()
                return instrument_id

    def get_data(self, ticker, is_retry=False):
        if not (instrument_id := self.get_instrument_id(ticker)):
            return None

        headers = {
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "authorization": f"Bearer {self.access_token}",
            "origin": "https://robinhood.com",
            "referer": "https://robinhood.com/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        }

        params = {
            "display_span": "day",
            "hide_extended_hours": "false",
        }

        response = requests.get(
            f"https://bonfire.robinhood.com/instruments/{instrument_id}/detail-page-live-updating-data/",
            params=params,
            headers=headers,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            if is_retry:
                raise e
            self.renew_access_token()
            return self.get_data(ticker, is_retry=True)
        return response.json()
