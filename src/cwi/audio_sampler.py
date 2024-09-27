from functools import lru_cache

import numpy as np
from loguru import logger

from cwi.const.service import MORSE_SAMPLER_CACHE_SIZE
from cwi.data_structures import TokenString, MorseToken, AudioData
from cwi.tone_generators import ToneGenerator, SilenceGenerator
from cwi.utils import chunked


class MorseAudioSampler:
    def __init__(self, tone_generator: ToneGenerator, time_unit):
        silence_generator = SilenceGenerator.copy_of(tone_generator)

        dit_tone = tone_generator.sound(time_unit)
        dah_tone = tone_generator.sound(time_unit * 3)
        intra_character_pause = silence_generator.sound(time_unit)
        inter_character_pause = silence_generator.sound(time_unit * 3)
        inter_word_pause = silence_generator.sound(time_unit * 7)

        self.__audio_lookup = {
            MorseToken.DIT: dit_tone,
            MorseToken.DAH: dah_tone,
            MorseToken.INTRA_CHARACTER: intra_character_pause,
            MorseToken.INTER_CHARACTER: inter_character_pause,
            MorseToken.INTER_WORD: inter_word_pause,
            MorseToken.UNKNOWN: inter_character_pause
        }
        
        logger.debug(f"{self.__class__.__name__} initialized with {time_unit=}s")
        logger.debug(f"{self.__class__.__name__} {MORSE_SAMPLER_CACHE_SIZE=}")
        
    @lru_cache(MORSE_SAMPLER_CACHE_SIZE)
    def __process_and_cache(self, token_chunk: str):
        audio_chunk = np.array([])

        try:
            for symbol in token_chunk:
                audio_chunk = np.concatenate([audio_chunk, self.__audio_lookup[symbol]])
        except KeyError:
            logger.exception(f"Unknown token found: {symbol}!")
            
        logger.debug(f"{self.__class__.__name__} [cache] <- {token_chunk=}")
        
        return audio_chunk

    def produce_audio_data(self, token_string: TokenString, chunk_size: int):
        audio = np.array([])

        for token_chunk in chunked(token_string.tokens, chunk_size):
            audio_chunk = self.__process_and_cache(token_chunk)
            audio = np.concatenate([audio, audio_chunk])

        return AudioData(audio)
