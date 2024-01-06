from abc import abstractmethod
from typing import Protocol
import pygame

class ValidationError(RuntimeError):
    pass

class CodeRunError(RuntimeError):
    pass

class Exercise(Protocol):
    name: str

    @abstractmethod
    def tick(self, delta: float, /) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def draw(self, screen: pygame.Surface, /) -> None:
        raise NotImplementedError
    
    # The cleanup method is optional, but Python does not allow this to be represented with protocols.
    # TODO: Revisit this if/when https://github.com/python/typing/issues/601 gets resolved.
    # If the cleanup method exists, it should conform to this signature:
    # def cleanup(self, /) -> None:
    #    ...
