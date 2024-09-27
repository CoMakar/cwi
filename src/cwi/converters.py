from dataclasses import dataclass

from loguru import logger

from cwi.data_structures import TokenString, MorseToken
from cwi.const import morse_codes


@dataclass(frozen=True)
class ConversionRule:
    old: str
    new: str
    
    def apply(self, string: str):
        return string.replace(self.old, self.new)


class MorseTokenizer:
    __RULES_TO_APPLY = (
        ConversionRule(
            MorseToken.DIT, f"{MorseToken.DIT}{MorseToken.INTRA_CHARACTER}"
        ),
        ConversionRule(
            MorseToken.DAH, f"{MorseToken.DAH}{MorseToken.INTRA_CHARACTER}"
        ),
        ConversionRule(
            f"{MorseToken.INTRA_CHARACTER}{MorseToken.INTER_CHARACTER}",
            MorseToken.INTER_CHARACTER,
        ),
    )

    __VALID_PREDEFINED_TOKENS = set(
        (MorseToken.DIT.value,
         MorseToken.DAH.value,
         MorseToken.INTER_WORD.value)
    )

    def __init__(self):
        self.__morse_codes = morse_codes.DEFAULT_MORSE_CODES.copy()

        if invalid_codes := self.__validate_morse_codes(self.__morse_codes):
            raise ValueError(f"Invalid morse codes provided: {invalid_codes}")

        self.__known_conversions = set(self.__morse_codes.keys())

        logger.debug(f"{self.__class__.__name__} initialized with {self.__morse_codes=}")
        logger.debug(f"{self.__class__.__name__} known rules: {self.__RULES_TO_APPLY=}")
        logger.debug(f"{self.__class__.__name__} valid predefined tokens: {self.__VALID_PREDEFINED_TOKENS=}")

    def __validate_morse_codes(self, morse_codes: dict):
        invalid_morse_codes = set()

        for code in morse_codes.values():
            if len(code) == 0:
                invalid_morse_codes.add(code)
            elif not set(code).issubset(self.__VALID_PREDEFINED_TOKENS):
                invalid_morse_codes.add(code)

        return invalid_morse_codes

    def tokenize(self, string: str):
        tokens = ""
        original_string = string.strip()
        string_to_process = string.strip().upper()
        unknown_chars = set()

        for char in string_to_process:
            if char not in self.__known_conversions:
                unknown_chars.add(char)

            tokens += f"{self.__morse_codes.get(char, MorseToken.UNKNOWN)}{MorseToken.INTER_CHARACTER}"

        for rule in self.__RULES_TO_APPLY:
            tokens = rule.apply(tokens)

        token_string = TokenString(tokens, original_string, unknown_chars, set(MorseToken.__members__.values()))

        logger.debug(f"{self.__class__.__name__}.tokenize('{string}') -> {token_string}")

        if unknown_chars:
            logger.warning(f"Unknown characters found: {unknown_chars}")

        return token_string


class TokenPurifier:    
        __RULES_TO_APPLY = (
            ConversionRule(
                MorseToken.INTRA_CHARACTER, ""
            ),
            ConversionRule(
                MorseToken.INTER_CHARACTER, " "
            ),
            ConversionRule(
                MorseToken.UNKNOWN, ""
            )
        )
        
        def __init__(self):
            logger.debug(f"{self.__class__.__name__} initialized")
            logger.debug(f"{self.__class__.__name__} known rules: {self.__RULES_TO_APPLY=}")
        
        @classmethod
        def purify(cls, token_string: TokenString):
            tokens = token_string.tokens
            
            for rule in cls.__RULES_TO_APPLY:
                tokens = rule.apply(tokens)
                
            return tokens
