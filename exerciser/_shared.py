from abc import abstractmethod
from typing import Protocol
import pygame

class ValidationError(RuntimeError):
    pass

class CodeRunError(RuntimeError):
    pass

# Note: Even though Exercise is structurally typed, it is recommended to explicitly subclass Exercise for better type hints.
class Exercise(Protocol):
    name: str

    @abstractmethod
    def tick(self, delta: float, /) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def draw(self, screen: pygame.Surface, /) -> None:
        raise NotImplementedError
