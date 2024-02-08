import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
from contextvars import ContextVar
import threading
import warnings
from typing import Any, Callable, Final, Optional, Sequence, Tuple, Union
import traceback
import matplotlib
import pygame
from ._shared import CodeRunError, Simulation, ValidationError

# Types copied from pygame/_common.pyi
RGBAOutput = Tuple[int, int, int, int]
ColorValue = Union[pygame.Color, int, str, Tuple[int, int, int], RGBAOutput, Sequence[int]]

TPS: Final[int] = 60
"""Default tick rate in ticks per second (equal to 1 / DELTA ignoring rounding error)"""
DELTA: Final[float] = 1 / TPS
"""Default time delta between ticks in seconds (equal to 1 / TPS)"""

_lock = threading.Lock()

_create_simulation: Optional[Callable[[], Simulation]] = None
_simulation: Optional[Simulation] = None
_initialized = False
_values_to_draw: ContextVar = ContextVar('values', default=None)
_user_values_to_draw: ContextVar = ContextVar('user_values', default=None)

def show_value(label: str, value: Any):
    """Show a user-supplied value on screen for debugging purposes"""
    values = _user_values_to_draw.get()
    if values is not None:
        values.append(f"{label} = {value:.2f}" if isinstance(value, float) else f"{label} = {value}")

def show_simulation_value(label: str, value: Any, color: ColorValue = 'black'):
    """Show an simulation-specific value on screen for informational/debugging purposes"""
    values = _values_to_draw.get()
    if values is not None:
        values.append((f"{label} = {value:.2f}" if isinstance(value, float) else f"{label} = {value}", color))

def run(create_simulation: Callable[[], Simulation]):
    """
    Calls `create_simulation` to create a simulation object. Runs the obtained simulation in a Pygame window.
    
    Note: `create_simulation` may be called more than once to restart the simulation. It should return a new simulation object every time.
    """

    if matplotlib.get_backend().casefold() == 'tkagg':
        # Running matplotlib with Tk backend and Pygame together occasionally causes Python to crash with the error message `Fatal Python error: PyEval_RestoreThread: NULL tstate`.
        # The Tk backend is also kind of flaky in general, having issues handling KeyboardInterrupt and moving the window in front of other windows on every reload.
        # Even if the Tk and Pygame crashing gets resolved it is probably a good idea to avoid the Tk backend.
        # 
        # TODO: What is the actual cause of this issue?
        # The only reference to it I could find was https://stackoverflow.com/questions/58598836/pygame-event-get-fatal-python-error-pyeval-restorethread-null-tstate,
        # which only speculates about the cause and provides no sources for anything.
        # Note: The workarond in that post works, but causes Pygame to freeze if the Tk main loop is not running.
        # Reliably detecting if the Tk main loop is running seems to be impossible without very dirty hacks, so this workaround is not viable for our use case. 
        #
        # TODO: This issue may be Windows specific.
        # A comment in an old version of the TkAgg backend seems to imply this: https://github.com/matplotlib/matplotlib/blob/68f86b37bb294913513b7ee5106a5aaa1558969e/lib/matplotlib/backends/backend_tkagg.py#L597-L600.
        tk_pygame_compat_warning = 'matplotlib is using the Tk backend. Tk has compatibility issues with Pygame that may cause Python to crash. Using a different matplotlib backend is recommended.'
        warnings.warn(tk_pygame_compat_warning, RuntimeWarning)

    global _create_simulation, _simulation, _initialized

    # TODO: It might be necessary to add more locking for thread safety.
    # Simple assignment is atomic on current CPython but that is not guaranteed for other implementations or future versions of CPython.

    _create_simulation = create_simulation
    _simulation = create_simulation()
    with _lock:
        if _initialized:
            return
        _initialized = True

    threading.Thread(target=_run).start()

def _run():
    global _simulation, _initialized

    try:
        assert _create_simulation is not None
        assert _simulation is not None

        running = True

        # TODO: Moving Pygame into a separate thread has broken matplotlib compatibility outside of interactive notebooks.
        # See comments labeled with 'Matplotlib compatibility' for specific issues.

        # TODO: Matplotlib compatibility: When Pygame closes, it should probably close all the matplotlib figures as well.
        # When matplotlib closes, it should close the Pygame window.
        # Note that matplotlib figures could be created after Pygame has started.

        last_message = ""
        last_message_color = 'black'
        last_message_hide = 0

        def show_message(message: str, message_color, message_duration_ms: Optional[int]):
            nonlocal last_message, last_message_color, last_message_hide
            print(message)
            last_message = message
            last_message_color = message_color
            last_message_hide = pygame.time.get_ticks() + message_duration_ms if message_duration_ms is not None else None
        
        def clear_message():
            nonlocal last_message_hide
            last_message_hide = 0

        pygame.display.init()
        pygame.font.init()
        screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
        pygame.display.set_caption(_simulation.name)
        clock = pygame.time.Clock()
        variables_font = pygame.font.SysFont('Arial', 20)

        values_to_draw, user_values_to_draw = [], []
        _values_to_draw.set(values_to_draw)
        _user_values_to_draw.set(user_values_to_draw)

        tick = 0
        show_fps = False

        last_invalid_simulation = None

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        _simulation = _create_simulation()
                    if event.key == pygame.K_F1:
                        show_fps = not show_fps

            simulation = _simulation

            if simulation is not last_invalid_simulation:
                if last_invalid_simulation is not None:
                    # Clear previous error.
                    clear_message()
                try:
                    # Tick with fixed delta to ensure that simulation is as deterministic as possible
                    simulation.tick(DELTA)
                except ValidationError as e:
                    show_message(f"{e}", "red", None)
                    last_invalid_simulation = simulation
                except CodeRunError as e:
                    cause = e.__cause__ or e.__context__
                    if cause is None:
                        show_message(f"{e}: <unknown cause>", 'red', None)
                    else:
                        show_message(f"{e}: {type(cause).__name__}: {cause}", 'red', None)
                        traceback.print_exception(cause)
                    last_invalid_simulation = simulation

            screen.fill('white')

            if show_fps:
                values_to_draw.append(f"FPS: {clock.get_fps():.2f}")

            simulation.draw(screen)

            # Output variable values
            for i, (value, color) in enumerate(values_to_draw):
                variables_text_surface = variables_font.render(value, True, color)
                screen.blit(variables_text_surface, (5, i * 25))
            user_values_start = len(values_to_draw) * 25 + 5
            for i, value in enumerate(user_values_to_draw):
                variables_text_surface = variables_font.render(value, True, 'black')
                screen.blit(variables_text_surface, (5, user_values_start + i * 25))
            values_to_draw.clear()
            user_values_to_draw.clear()

            if last_message_hide is None or pygame.time.get_ticks() < last_message_hide:
                message_text_surface = variables_font.render(last_message, True, last_message_color)
                screen.blit(message_text_surface, (5, screen.get_height() - 25))

            pygame.display.flip()

            # TODO: Matplotlib compatibility: draw_idle needs to be called regularly to make live updates to data work.
            # On the other hand, calling draw_idle from a different thread for no good reason is probably a bad idea,
            # so for maximum compatibility we currently don't do this automatically.
            # Should we do this automatically in some cases?

            # Example generic redraw logic:
            # if tick % 3 == 0:
            #     for manager in matplotlib._pylab_helpers.Gcf.get_all_fig_managers():
            #         canvas = manager.canvas
            #         if canvas.figure.stale:
            #             canvas.draw_idle()

            clock.tick(TPS)
            tick += 1

        pygame.quit()
    finally:
        with _lock:
            _initialized = False
