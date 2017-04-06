from urllib.parse import ParseResult

from spec.coercions import Url


def test_url():
    parsed = Url.conform("http://google.com") # type:ParseResult
    assert parsed.scheme == "http"
