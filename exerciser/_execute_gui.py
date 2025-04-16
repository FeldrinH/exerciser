import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
os.environ['SDL_MOUSE_FOCUS_CLICKTHROUGH'] = '1'
import sys
import time
import asyncio
from contextvars import ContextVar
import threading
import warnings
from typing import Any, Callable, Final, Optional, Sequence, Tuple, Union
import traceback
import matplotlib
import pygame
from ._shared import CodeRunError, Simulation, ValidationError

# Type copied from pygame/_common.pyi
ColorValue = Union[pygame.Color, int, str, Tuple[int, int, int], Tuple[int, int, int, int], Sequence[int]]

TPS: Final[int] = 60
"""Target tick rate in ticks per second (equal to 1 / DELTA ignoring rounding error)"""
DELTA: Final[float] = 1 / TPS
"""Target time delta between ticks in seconds (equal to 1 / TPS)"""

_CONTROLS = [
    "R - Restart the simulation",
    "P - Pause the simulation",
    "S - Step the simulation (execute one tick)",
    "F1 - Toggle help text",
]

_lock = threading.Lock()

_create_simulation: Optional[Callable[[], Simulation]] = None
_simulation: Optional[Simulation] = None
_initialized = False
_parent_header = None
_timer = None
_values_to_draw: ContextVar = ContextVar('values', default=None)
_user_values_to_draw: ContextVar = ContextVar('user_values', default=None)

def show_value(label: str, value: Any):
    """
    Show a user-supplied value on screen for debugging purposes.
    """
    values = _user_values_to_draw.get()
    if values is not None:
        values.append(f"{label} = {value:.3f}" if isinstance(value, float) else f"{label} = {value}")

def show_simulation_value(label: str, value: Any, color: ColorValue = 'black'):
    """
    Show a simulation-specific value on screen for informational/debugging purposes.
    
    Note: This should be called inside `draw`, not inside `tick`.
    """
    values = _values_to_draw.get()
    if values is not None:
        values.append((f"{label} = {value:.3f}" if isinstance(value, float) else f"{label} = {value}", color))

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
        tk_pygame_compat_warning = 'Matplotlib is using the Tk backend. Tk has compatibility issues with Pygame that may cause Python to crash. Using a different Matplotlib backend is recommended.'
        warnings.warn(tk_pygame_compat_warning, RuntimeWarning)

    global _create_simulation, _simulation, _initialized, _parent_header, _timer

    # TODO: It might be necessary to add more locking for thread safety.
    # Simple assignment is atomic on current CPython but that is not guaranteed for other implementations or future versions of CPython.

    _simulation = create_simulation()
    _create_simulation = create_simulation
    with _lock:
        if _initialized:
            try:
                # Store parent header of latest run if running in an IPython notebook
                _parent_header = sys.stdout.parent_header # type: ignore
            except AttributeError:
                # Not running in an IPython notebook
                pass
            return
        _initialized = True

    if sys.platform == 'darwin':
        # MacOS requires that Pygame run on the main thread, so we need to hook whatever event loop is active on the main thread and run our main loop there.
        # TODO: Some way to run this without an event loop (for example in a regular Python script).
        mainloop = _mainloop(sleep=False)

        # Hook IPython asyncio event loop
        async def run_async():
            for _ in mainloop:
                # TODO: Try to figure out some way to compensate for the fact that asyncio.sleep generally sleeps slightly longer than the provided time.
                await asyncio.sleep(DELTA)
        try:
            asyncio.create_task(run_async())
        except RuntimeError:
            raise RuntimeError("Running exerciser on MacOS requires a running event loop (e.g. being in a Jupyter notebook)")

        # Hook Qt GUI event loop
        try:
            from IPython.external.qt_for_kernel import QtCore # type: ignore
            from ipykernel.kernelbase import Kernel
            if _timer is not None:
                _timer.stop()
                _timer.deleteLater()
            def run_timer():
                global _timer
                try:
                    next(mainloop)
                except StopIteration:
                    if _timer is not None:
                        _timer.stop()
                        _timer.deleteLater()
                        _timer = None
            app = Kernel.instance().app # type: ignore
            app.qt_event_loop # `qt_event_loop` attribute is present only if `app` is a Qt application
            _timer = QtCore.QTimer(app)
            _timer.timeout.connect(run_timer)
            _timer.start(int(DELTA * 1000))
        except (ImportError, AttributeError):
            # Either IPython or Qt is not installed or the Qt event loop is not running
            pass
    else:
        threading.Thread(target=_run).start()

def _run():
    mainloop = _mainloop(sleep=True)
    for _ in mainloop:
        pass

def _mainloop(sleep: bool):
    global _simulation, _initialized, _parent_header

    try:
        assert _create_simulation is not None
        assert _simulation is not None

        running = True

        # TODO: Moving Pygame into a separate thread has broken matplotlib compatibility outside of interactive notebooks.
        # See comments labeled with 'Matplotlib compatibility' for specific issues.

        # TODO: Matplotlib compatibility:
        # When Pygame closes, it should close all the matplotlib figures as well.
        # When matplotlib closes, it should close the Pygame window.
        # Note that matplotlib figures could be created after Pygame has started.

        last_message = ""
        last_message_color = 'black'
        last_message_hide = 0

        def show_message(message: str, message_color, message_duration_ms: Optional[int] = None):
            nonlocal last_message, last_message_color, last_message_hide
            print(message, file=sys.stderr)
            last_message = message
            last_message_color = message_color
            last_message_hide = pygame.time.get_ticks() + message_duration_ms if message_duration_ms is not None else None
        
        def clear_message():
            nonlocal last_message_hide
            last_message_hide = 0

        pygame.display.init()
        pygame.font.init()
        screen = pygame.display.set_mode(_simulation.initial_window_size, pygame.RESIZABLE)
        pygame.display.set_caption(_simulation.name)
        clock = pygame.time.Clock()
        variables_font = pygame.font.Font(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Roboto-Regular-Modified.ttf'), 20)

        values_to_draw, user_values_to_draw = [], []

        tick = 0
        last_frame_time = 0.0
        show_fps = False
        show_help = False

        paused = False

        last_parent_header = None

        last_simulation = None
        simulation_valid = True

        while running:
            start_time = time.perf_counter()

            parent_header = _parent_header
            if parent_header is not last_parent_header:
                last_parent_header = parent_header
                # Redirect output from this thread to the notebook cell of the latest run if running in an IPython notebook
                # Based on https://github.com/ipython/ipykernel/blob/v6.29.5/ipykernel/iostream.py#L505-L527
                for stream in [sys.stdout, sys.stderr]:
                    try:
                        stream._parent_header.set(parent_header) # type: ignore
                    except AttributeError:
                        # Either not running in an IPython notebook or this stream is not hooked for output redirection
                        pass

            step = False

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        _simulation = _create_simulation()
                    elif event.key == pygame.K_p:
                        paused = not paused
                    elif event.key == pygame.K_s:
                        if paused:
                            step = True
                        else:
                            paused = True
                    elif event.key == pygame.K_F1:
                        show_help = not show_help
                    elif event.key == pygame.K_F2:
                        show_fps = not show_fps

            simulation = _simulation

            values_to_draw.clear()
            if show_fps:
                values_to_draw.append((f"FPS: {clock.get_fps():.2f}, Frame time: {last_frame_time * 1000:.2f} ms", 'black'))
            _values_to_draw.set(values_to_draw)

            if simulation is not last_simulation:
                simulation.post_init()
                last_simulation = simulation
                simulation_valid = True
                # Clear previous error and values
                clear_message()
                user_values_to_draw.clear()

            if simulation_valid:
                simulation.handle_input(events)
                if not paused or step:
                    # Only enable storing values in show_value during tick.
                    # TODO: Enable show_value support for other simulation methods.
                    # (Needs more complex clearing logic in cases where only some methods run.)
                    user_values_to_draw.clear()
                    _user_values_to_draw.set(user_values_to_draw)
                    try:
                        # Tick with fixed delta to ensure that simulation is as deterministic as possible
                        simulation.tick(DELTA)
                    except ValidationError as e:
                        show_message(f"{e}", 'red')
                        simulation_valid = False
                    except CodeRunError as e:
                        cause = e.__cause__ or e.__context__
                        if cause is None:
                            show_message(f"{e}: <unknown cause>", 'red')
                        else:
                            show_message(f"{e}: {type(cause).__name__}: {cause}", 'red')
                            traceback.print_exception(cause)
                        simulation_valid = False
                    _user_values_to_draw.set(None)

            screen.fill('white')

            simulation.draw(screen)

            if paused:
                paused_indicator_surface = variables_font.render('Paused', True, 'blue')
                screen.blit(paused_indicator_surface, (screen.get_width() - paused_indicator_surface.get_width() - 5, 0))

            # Output variable values
            for i, (value, color) in enumerate(values_to_draw):
                variables_text_surface = variables_font.render(value, True, color)
                screen.blit(variables_text_surface, (5, i * 25))
            user_values_start = len(values_to_draw) * 25 + 5
            for i, value in enumerate(user_values_to_draw):
                variables_text_surface = variables_font.render(value, True, 'black')
                screen.blit(variables_text_surface, (5, user_values_start + i * 25))

            if show_help:
                surfaces = [variables_font.render(text, True, 'black') for text in _CONTROLS]
                offset = screen.get_width() - 5 - max(surface.get_width() for surface in surfaces)
                for i, surface in enumerate(surfaces):
                    screen.blit(surface, (offset, i * 25))

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

            _values_to_draw.set(None)

            last_frame_time = time.perf_counter() - start_time

            clock.tick(TPS if sleep else 0)
            tick += 1

            yield
    except Exception as e:
        print("Unexpected error while running visualization:", file=sys.stderr)
        traceback.print_exception(e)
    finally:
        try:
            # TODO: Apparently pygame.quit() here causes Python to deadlock/freeze on MacOS.
            #       Does using pygame.display.quit() fix the issue? If not, try to figure out why this happens and fix it.
            pygame.display.quit()
        finally:
            with _lock:
                _initialized = False
                _parent_header = None
