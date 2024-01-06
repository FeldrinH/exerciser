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
    
    # The cleanup method should be optional, but Python does not allow this to be represented with protocols.
    # TODO: Revisit this if/when https://github.com/python/typing/issues/601 gets resolved.
    # TODO: Is there a workaround for this if the aforementioned proposal gets rejected?
    # TODO: Given that matplotlib cleanup is automatic, is there a need to keep this hook?
    @abstractmethod
    def cleanup(self, /) -> None:
        raise NotImplementedError
