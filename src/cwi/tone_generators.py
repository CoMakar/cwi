from abc import ABC, abstractmethod

import numpy as np
from loguru import logger


class ToneGenerator(ABC):
    def __init__(self, frequency: float | int, sample_rate: int):
        self._frequency = frequency
        self._sample_rate = sample_rate
        
        logger.debug(f"{self.__class__.__name__} initialized with {frequency=}HZ; {sample_rate=}HZ")

    @classmethod
    def copy_of(cls, source: "ToneGenerator"):
        instance = cls.__new__(cls)
        instance.__init__(source._frequency, source._sample_rate)
        return instance

    @abstractmethod
    def sound(duration: float):
        pass
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self._frequency}, {self._sample_rate})"


class SilenceGenerator(ToneGenerator):
    def sound(self, duration: float):
        return np.zeros(int(self._sample_rate * duration))
    
    @classmethod
    def copy_of(cls, source: "ToneGenerator"):
        instance = super().copy_of(source)
        instance._frequency = 0
        return instance


class SineWaveToneGenerator(ToneGenerator):
    def sound(self, duration: float):
        t = np.arange(self._sample_rate * duration) / self._sample_rate
        return np.sin(2 * np.pi * t * self._frequency)


class SquareToneGenerator(ToneGenerator):
    def sound(self, duration: float):
        t = np.arange(self._sample_rate * duration) / self._sample_rate
        return np.sign(np.sin(2 * np.pi * t * self._frequency))


class SawtoothToneGenerator(ToneGenerator):
    def sound(self, duration: float):
        t = np.arange(self._sample_rate * duration) / self._sample_rate
        return 2 * (t % (1 / self._frequency)) * self._frequency - 1


class TriangleToneGenerator(ToneGenerator):
    def sound(self, duration: float):
        t = np.arange(self._sample_rate * duration) / self._sample_rate
        return np.abs(t * self._frequency - np.floor(0.5 + t * self._frequency))
