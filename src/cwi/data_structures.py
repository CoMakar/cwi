from dataclasses import dataclass, field
from enum import StrEnum

import numpy as np
import numpy.typing as npt


class MorseToken(StrEnum):
    DIT = "."
    DAH = "-"
    INTRA_CHARACTER = "^"
    INTER_CHARACTER = "#"
    INTER_WORD = "/"
    UNKNOWN = "X"
    

class ToneGeneratorType(StrEnum):
    SINE = "sine"
    SAW = "saw"
    TRIANGLE = "triangle"
    SQUARE = "square"


@dataclass
class TokenString:
    tokens: str
    source: str
    unknown_entries: set[str]
    token_space: set[str]
    length: int = field(init=False)
    is_valid: bool = field(init=False)
    
    def __post_init__(self):
        self.length = len(self.tokens)
        self.is_valid = set(self.tokens).issubset(self.token_space)
            
            
            
@dataclass
class Message:
    actual: str = field(init=False)
    morse_tokens: TokenString = field(init=False)
    morse_readable: str = field(init=False)


@dataclass(frozen=True)
class AudioData:
    data: npt.NDArray

    @property
    def as_float32(self):
        return np.float32(self.data / np.max(np.abs(self.data)))

    @property
    def as_int16(self):
        return np.int16(self.data * 32767)