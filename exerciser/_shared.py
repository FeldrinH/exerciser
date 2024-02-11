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
    """Name of the simulation. Used as window title."""

    def handle_input(self, events: List[pygame.event.Event], /) -> None:
        """
        Handle input and update state of interactive elements.
        
        Args:
            events: list of events from `pygame.event.get()`
        """
        pass

    @abstractmethod
    def tick(self, delta: float, /) -> None:
        """
        Run controller and simulation logic. Update state of the simulation.

        Not called when simulation is paused.

        Args:
            delta: time elapsed in simulation since last call to `tick` (note: might not match real time)
        """
        raise NotImplementedError

    @abstractmethod
    def draw(self, screen: pygame.Surface, /) -> None:
        """
        Draw simulation on screen. Should not change simulation state.

        Args:
            screen: Pygame surface to draw on
        """
        raise NotImplementedError
