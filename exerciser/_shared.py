from abc import abstractmethod
from typing import List, Tuple, Protocol
import pygame

class ValidationError(RuntimeError):
    pass

class CodeRunError(RuntimeError):
    pass

# Note: Even though Simulation is structurally typed, it is recommended to explicitly subclass it for better type hints
# and to get default implementations for optional methods and default values for optional attributes.
class Simulation(Protocol):
    name: str
    """Name of the simulation. Used as window title."""
    initial_window_size: Tuple[int, int] = (800, 600)
    """Initial size of window in pixels. Defaults to (800, 600) if not specified."""

    def post_init(self, /) -> None:
        """
        Perform initialization that depends on Pygame.

        Called once after Pygame has been initialized but before any other methods have been called.
        """
        pass

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
