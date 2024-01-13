from contextvars import ContextVar
import os
import threading
import warnings
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
from typing import Any, Final, List, Optional
import traceback
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

_lock = threading.Lock()

_exercise: Optional[Exercise] = None
_initialized = False
# Note: This list is primarily populated using the public function exerciser.pygame.show_value.
_values_to_draw: ContextVar[Optional[List[str]]] = ContextVar('values', default=None)
_user_values_to_draw: ContextVar[Optional[List[str]]] = ContextVar('user_values', default=None)

def show_value(label: str, value: Any):
    """Show a user-supplied value on screen for debugging purposes"""
    values = _user_values_to_draw.get()
    if values is not None:
        values.append(f"{label} = {value:.2f}" if isinstance(value, float) else f"{label} = {value}")

def show_exercise_value(label: str, value: Any):
    """Show an exercise-specific value on screen for informational/debugging purposes"""
    values = _values_to_draw.get()
    if values is not None:
        values.append(f"{label} = {value:.2f}" if isinstance(value, float) else f"{label} = {value}")

def run(exercise: Exercise, error: Optional[BaseException] = None):
    """
    Runs provided `exercise` in a Pygame window. If `error` is provided behaves as if the error was raised by the exercise on the first tick.

    Yields time to matplotlib windows for processing events and updating plots, if any exist.
    This allows it to run at the same time as matplotlib without issues.
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

    threading.Thread(target=_run, args=(exercise, error)).start()

def _run(exercise: Exercise, error: Optional[BaseException] = None):
    global _exercise, _initialized

    # TODO: It might be necessary to add more locking for thread safety.
    # Simple assignment is atomic on current CPython but that is not guaranteed for other implementations or future versions of CPython.

    if error is None:
        _exercise = exercise
    else:
        _exercise = ErrorProxyExercise(exercise, error)
    del exercise, error # Unbind to avoid accidentally using the initial exercise value and allow GC

    with _lock:
        if _initialized:
            return
        _initialized = True
    
    running = True

    # TODO: Is there a better way to detect non-interactive backends?
    # TODO: The backend can change while Pygame is open. Is there a better way to handle that?
    enable_matplotlib_compat = 'inline' not in matplotlib.get_backend().casefold()

    if enable_matplotlib_compat:
        def quit():
            nonlocal running
            if running:
                running = False
                try:
                    matplotlib._pylab_helpers.Gcf.destroy_all()
                except Exception:
                    # Calling Gcf.destroy_all() while matplotlib is already closing tends to cause errors.
                    # It should be safe to ignore them to avoid spamming console.
                    pass

        for manager in matplotlib._pylab_helpers.Gcf.get_all_fig_managers():
            manager.canvas.mpl_connect('close_event', lambda _: quit())

    last_message = ""
    last_message_color = "black"
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
    pygame.display.set_caption(_exercise.name)
    clock = pygame.time.Clock()
    variables_font = pygame.font.SysFont('Arial', 20)

    values_to_draw, user_values_to_draw = [], []
    _values_to_draw.set(values_to_draw)
    _user_values_to_draw.set(user_values_to_draw)

    tick = 0
    show_fps = False

    last_invalid_exercise = None

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F1:
                        show_fps = not show_fps
                    # TODO: Add some way to restart simulation without re-running code (for exercises with random initial state)?

            exercise = _exercise

            if exercise is not None and exercise is not last_invalid_exercise:
                if last_invalid_exercise is not None:
                    # Clear previous error.
                    clear_message()
                try:
                    # Tick with fixed delta to ensure that simulation is as deterministic as possible
                    exercise.tick(DELTA)
                except ValidationError as e:
                    show_message(f"{e}", "red", None)
                    last_invalid_exercise = exercise
                except CodeRunError as e:
                    cause = e.__cause__ or e.__context__
                    if cause is None:
                        show_message(f"{e}: <unknown cause>", "red", None)
                    else:
                        show_message(f"{e}: {type(cause).__name__}: {cause}", "red", None)
                        traceback.print_tb(cause.__traceback__)
                    last_invalid_exercise = exercise

            screen.fill("white")

            if show_fps:
                values_to_draw.append(f"FPS: {clock.get_fps():.2f}")

            if exercise is not None:
                exercise.draw(screen)

            # Output variable values
            for i, value in enumerate(values_to_draw):
                variables_text_surface = variables_font.render(value, True, "black")
                screen.blit(variables_text_surface, (5, i * 25))
            user_values_start = len(values_to_draw) * 25 + 5
            for i, value in enumerate(user_values_to_draw):
                variables_text_surface = variables_font.render(value, True, "black")
                screen.blit(variables_text_surface, (5, user_values_start + i * 25))
            values_to_draw.clear()
            user_values_to_draw.clear()
            
            #graph.draw(screen, 0, screen.get_height() - 200)
            
            if last_message_hide is None or pygame.time.get_ticks() < last_message_hide:
                message_text_surface = variables_font.render(last_message, True, last_message_color)
                screen.blit(message_text_surface, (5, screen.get_height() - 25))

            pygame.display.flip()

            if enable_matplotlib_compat:
                # Yield time to matplotlib for processing events and updating plots.
                # Note: Using this instead of matplotlib.pyplot.pause() avoids the matplotlib window showing up when matplotlib is loaded but not currently in use.
                # Note: Redrawing only happens every 3 frames (giving matplotlib an effective max FPS of 20), because redrawing the plot is fairly CPU intensive.
                # TODO: Animated plots seem to more or less work with the ipympl backend, but this needs more testing.
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
    finally:
        with _lock:
            _initialized = False
