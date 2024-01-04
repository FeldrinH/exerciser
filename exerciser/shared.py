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
    def tick(self, delta: float, /):
        raise NotImplementedError
    
    @abstractmethod
    def draw(self, screen: pygame.Surface, /):
        raise NotImplementedError