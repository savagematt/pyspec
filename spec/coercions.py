from urllib.parse import urlparse, ParseResult
from uuid import UUID

from spec.core import coerce


def coerce_uuid(x):
    return x if isinstance(x, UUID) else UUID(x)


Uuid = coerce(coerce_uuid, UUID)


def coerce_int(x):
    return x if isinstance(x, int) else int(x)


Int = coerce(coerce_int, int)


def parse_url(x):
    return urlparse(x)


Url = coerce(parse_url, ParseResult)
