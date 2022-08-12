import string


def b62encode(data: bytes) -> str:
    num = int.from_bytes(data, "big")
    characters = string.digits + string.ascii_letters

    encoded = ""
    base: int = len(characters)

    if num < 0:
        return ""

    while num >= base:
        mod = num % base
        num //= base
        encoded = characters[mod] + encoded

    if num > 0:
        encoded = characters[num] + encoded

    return encoded
