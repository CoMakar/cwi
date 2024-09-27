from typing import Iterable


def chunked(iterable: Iterable, size: int):
    if type(size) != int:
        raise TypeError(f"Size must be an integer: {size=}")
    
    for pos in range(0, len(iterable), size):
        yield iterable[pos:pos + size]
