from abc import abstractmethod
from typing import Protocol
import pygame

class ValidationError(RuntimeError):
    pass

class CodeRunError(RuntimeError):
    pass

# Note: Even though Exercise is structurally typed, it is recommended to explicitly subclass Exercise
# for better type hints and default implementations of methods.
class Exercise(Protocol):
    name: str

    @abstractmethod
    def tick(self, delta: float, /) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def draw(self, screen: pygame.Surface, /) -> None:
        raise NotImplementedError
    
    # The cleanup method should be optional, but Python does not allow this to be fully represented with protocols.
    # TODO: Revisit this if/when https://github.com/python/typing/issues/601 gets resolved.
    def cleanup(self, /) -> None:
        pass
