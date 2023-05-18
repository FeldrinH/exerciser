from abc import abstractmethod
from typing import Any, Protocol
import pygame

class ValidationError(RuntimeError):
    pass

class Exercise(Protocol):
    def __init__(self):
        ...

    @staticmethod
    @abstractmethod
    def get_template() -> str:
        raise NotImplementedError

    @abstractmethod
    def get_args(self) -> dict[str, Any]:
        raise NotImplementedError
    
    @abstractmethod
    def tick(self, delta: float, control_return):
        raise NotImplementedError
    
    @abstractmethod
    def draw(self, screen: pygame.Surface):
        raise NotImplementedError