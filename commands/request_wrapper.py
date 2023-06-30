import requests


class RequestWrapper:
    def __init__(self, headers=None):
        if headers is None:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
            }
        self.headers = headers

    def get(self, url, params=None, **kwargs):
        return self._request_wrapper(requests.get, url, params=params, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        return self._request_wrapper(requests.post, url, data=data, json=json, **kwargs)

    def _request_wrapper(self, method, url, **kwargs):
        if self.headers is not None:
            kwargs.setdefault("headers", self.headers)
        return method(url, **kwargs)
