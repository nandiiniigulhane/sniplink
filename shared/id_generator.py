"""Distributed ID generator using Redis atomic counter + Base62 encoding.

At 100M DAU, this produces 6-7 character short codes.
- 6 chars (62^6 ≈ 56.8B): first ~568 days at 100M/day
- 7 chars (62^7 ≈ 3.5T): decades of capacity
"""

import string

BASE62_ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase
BASE = 62
# Start counter at 62^5 so codes are at least 6 characters
COUNTER_START = BASE ** 5  # ~916M — first code will be "100000"


def encode_base62(num: int) -> str:
    if num == 0:
        return BASE62_ALPHABET[0]
    chars = []
    while num > 0:
        num, rem = divmod(num, BASE)
        chars.append(BASE62_ALPHABET[rem])
    return "".join(reversed(chars))


def decode_base62(code: str) -> int:
    num = 0
    for char in code:
        num = num * BASE + BASE62_ALPHABET.index(char)
    return num
