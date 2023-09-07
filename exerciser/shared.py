from abc import abstractmethod
from typing import Any, ClassVar, Protocol
import pygame

class ValidationError(RuntimeError):
    pass

class Exercise(Protocol):
    name: ClassVar[str]
    template: ClassVar[str]

    def __init__(self):
        ...

    @abstractmethod
    def get_args(self) -> dict[str, Any]:
        raise NotImplementedError
    
    @abstractmethod
    def tick(self, delta: float, control_return):
        raise NotImplementedError
    
    @abstractmethod
    def draw(self, screen: pygame.Surface):
        raise NotImplementedError