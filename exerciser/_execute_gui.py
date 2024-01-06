import os
import time
import warnings
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
from typing import Any, Callable, Final, List, Optional
import importlib.util
from pathlib import Path
import sys
import traceback
from types import ModuleType
import matplotlib._pylab_helpers
import pygame
from ._shared import CodeRunError, Exercise, ValidationError

TPS: Final[int] = 60
DELTA: Final[float] = 1 / TPS

class ErrorProxyExercise:
    def __init__(self, exercise: Exercise, error: BaseException) -> None:
        self.name = exercise.name
        self.exercise = exercise
        self.error = error
    
    def tick(self, _):
        raise self.error

    def draw(self, surface):
        self.exercise.draw(surface)
    
    def cleanup(self):
        self.exercise.cleanup()

def _prepare_module_for_reload(module: ModuleType):
    # TODO: This creates a spec if a spec is missing, which is never done in the documentation. Is this somehow unsound?
    if not module.__spec__:
        loader = module.__loader__
        assert loader
        module.__spec__ = importlib.util.spec_from_loader(module.__name__, loader) # type: ignore

def _reload_module(module: ModuleType):
    # NB: Only use this for modules prepared using _prepare_module_for_reload!
    spec = module.__spec__
    assert spec and spec.loader

    # Delete existing globals, to avoid old functions and constants lingering on reload.
    # TODO: importlib.reload preserves globals. Are there issues that might arise from deleting them?
    for key in list(vars(module)):
        if not key.startswith('__'):
            delattr(module, key)

    # TODO: What is the actual difference between importlib.reload and spec.loader.exec_module?
    # importlib.reload(module)    
    spec.loader.exec_module(module)

_exercise: Optional[Exercise] = None
_cleanup: Optional[Callable[[], Any]] = None
_initialized = False
_running = True
_values_to_draw: List[str] = []

# TODO: This only shows something if a Pygame window is open. Move this to pygame module?
def show_value(label: str, value: Any):
    _values_to_draw.append(f"{label} = {value}")

def quit():
    global _running
    if _running:
        _running = False
        try:
            matplotlib._pylab_helpers.Gcf.destroy_all()
        except Exception:
            # Calling Gcf.destroy_all() while matplotlib is already closing tends to cause errors.
            # It should be safe to ignore them to avoid spamming console.
            pass

# TODO: Maybe cleanup should be non-optional? You could explicitly pass in a no-op if required.
def run_idle(cleanup: Optional[Callable[[], Any]]):
    """
    Watches main module source file for changes and reloads it on change.
    If `cleanup` is provided, it will be called before reload.

    Yields time to matplotlib windows for processing events and updating plots, if any exist.
    This allows it to run at the same time as matplotlib without issues.
    """

    global _cleanup, _initialized, _running

    _cleanup = cleanup
    del cleanup
    if _initialized:
        return
    _initialized = True

    # Automatically exit if any matplotlib window is closed.
    for manager in matplotlib._pylab_helpers.Gcf.get_all_fig_managers():
        manager.canvas.mpl_connect('close_event', lambda _: quit())
    
    # TODO: Python importlib docs recommend against reloading __main__. Is reloading __main__ somehow unsound?
    solution_module = sys.modules['__main__']
    _prepare_module_for_reload(solution_module)

    solution_file = solution_module.__file__
    assert solution_file
    last_mtime = os.stat(solution_file).st_mtime

    while _running:
        should_reload = False
        
        # TODO: Optimize this?
        new_mtime = os.stat(solution_file).st_mtime
        if new_mtime != last_mtime:
            last_mtime = new_mtime
            should_reload = True
        
        if should_reload:
            should_reload = False
            if _cleanup is not None:
                _cleanup()
            _cleanup = None
            try:
                _reload_module(solution_module)
            except Exception as e:
                print(f"Error reloading solution: {type(e).__name__}: {e}")
                traceback.print_exc()
            else:
                print("Reloaded solution")

        # Yield time to matplotlib for processing events and updating plots.
        for manager in matplotlib._pylab_helpers.Gcf.get_all_fig_managers():
            canvas = manager.canvas
            if canvas.figure.stale:
                canvas.draw_idle()
        manager = matplotlib._pylab_helpers.Gcf.get_active()
        if manager is not None:
            manager.canvas.start_event_loop(1.0)
        else:
            time.sleep(1.0)

def run(exercise: Exercise, error: Optional[BaseException] = None):
    """
    Runs provided `exercise` in a Pygame window. If `error` is provided behaves as if the error was raised by the exercise on the first tick.
    Watches main module source file for changes and reloads it on change.

    Yields time to matplotlib windows for processing events and updating plots, if any exist.
    This allows it to run at the same time as matplotlib without issues.
    """

    global _exercise, _initialized, _running

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

    if error is None:
        _exercise = exercise
    else:
        _exercise = ErrorProxyExercise(exercise, error)
    del exercise # Unbind to avoid accidentally using the initial exercise value and allow GC
    if _initialized:
        return
    _initialized = True

    # Automatically exit if any matplotlib window is closed.
    for manager in matplotlib._pylab_helpers.Gcf.get_all_fig_managers():
        manager.canvas.mpl_connect('close_event', lambda _: quit())
    
    # TODO: Python importlib docs recommend against reloading __main__. Is reloading __main__ somehow unsound?
    solution_module = sys.modules['__main__']
    _prepare_module_for_reload(solution_module)

    solution_file = solution_module.__file__
    assert solution_file
    last_mtime = os.stat(solution_file).st_mtime

    solution_module_valid = True

    last_message = ""
    last_message_color = "black"
    last_message_hide = 0

    def show_message(message: str, message_color, message_duration_ms: Optional[int]):
        nonlocal last_message, last_message_color, last_message_hide
        print(message)
        last_message = message
        last_message_color = message_color
        last_message_hide = pygame.time.get_ticks() + message_duration_ms if message_duration_ms is not None else None

    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    pygame.display.set_caption(f"{_exercise.name} / {Path(solution_file).name}")
    clock = pygame.time.Clock()
    tick = 0
    variables_font = pygame.font.SysFont('Arial', 20)

    last_reload_check = pygame.time.get_ticks()

    while _running:
        should_reload = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                _running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    should_reload = True
        
        # TODO: Optimize this?
        if pygame.time.get_ticks() - last_reload_check >= 1000:
            last_reload_check = pygame.time.get_ticks()
            new_mtime = os.stat(solution_file).st_mtime
            if new_mtime != last_mtime:
                last_mtime = new_mtime
                should_reload = True
        
        if should_reload:
            should_reload = False
            if _exercise is not None:
                _exercise.cleanup()
            _exercise = None
            try:
                _reload_module(solution_module)
            except Exception as e:
                show_message(f"Error reloading solution: {type(e).__name__}: {e}", "red", None)
                traceback.print_exc()
            else:
                show_message("Reloaded solution", "blue", 2000)
                solution_module_valid = True
                if _exercise is None:
                    # TODO: Better error message?
                    show_message(f"Reloaded solution did not call the required method to provide a solution", "red", None)

        if solution_module_valid and _exercise is not None:
            try:
                # Tick with fixed delta to ensure that simulation is as deterministic as possible
                _exercise.tick(DELTA)
            except ValidationError as e:
                show_message(f"{e}", "red", None)
                solution_module_valid = False
            except CodeRunError as e:
                cause = e.__cause__ or e.__context__
                if cause is None:
                    show_message(f"{e}: <unknown cause>", "red", None)
                else:
                    show_message(f"{e}: {type(cause).__name__}: {cause}", "red", None)
                    traceback.print_tb(cause.__traceback__)
                solution_module_valid = False

        screen.fill("white")

        # TODO: Add some kind of toggle to enable FPS counter?
        # _values_to_draw.append(f"FPS: {clock.get_fps():.2f}")

        if _exercise is not None:
            _exercise.draw(screen)

        # Output variable values
        for i, value in enumerate(_values_to_draw):
            variables_text_surface = variables_font.render(value, True, "black")
            screen.blit(variables_text_surface, (0, i * 25))
            #if isinstance(v, numbers.Real):
            #    graph.add_point(k, v)
        _values_to_draw.clear()
        
        #graph.draw(screen, 0, screen.get_height() - 200)
        
        if last_message_hide is None or pygame.time.get_ticks() < last_message_hide:
            message_text_surface = variables_font.render(last_message, True, last_message_color)
            screen.blit(message_text_surface, (0, screen.get_height() - 25))

        pygame.display.flip()

        # Yield time to matplotlib for processing events and updating plots.
        # Note: Using this instead of matplotlib.pyplot.pause() avoids the matplotlib window showing up when matplotlib is loaded but not currently in use.
        # Note: Redrawing only happens every 3 frames (giving matplotlib an effective max FPS of 20), because redrawing the plot is very CPU intensive.
        # TODO: Is there a better way to optimize matplotlib redrawing?
        if tick % 3 == 0:
            for manager in matplotlib._pylab_helpers.Gcf.get_all_fig_managers():
                canvas = manager.canvas
                if canvas.figure.stale:
                    canvas.draw_idle()
        manager = matplotlib._pylab_helpers.Gcf.get_active()
        if manager is not None:
            manager.canvas.start_event_loop(DELTA * 0.2)

        clock.tick(TPS)
        tick += 1

    pygame.quit()
