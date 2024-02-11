from abc import abstractmethod
from typing import List, Protocol
import pygame

class ValidationError(RuntimeError):
    pass

class CodeRunError(RuntimeError):
    pass

# Note: Even though Simulation is structurally typed,
# it is recommended to explicitly subclass it for better type hints
# and to get default implementations for optional methods.
class Simulation(Protocol):
    name: str

    # TODO: Merge `handle_input` and `draw` to try and simplify the API?
    def handle_input(self, /) -> None:
        pass

    @abstractmethod
    def tick(self, delta: float, /) -> None:
        raise NotImplementedError

    @abstractmethod
    def draw(self, screen: pygame.Surface, /) -> None:
        raise NotImplementedError
