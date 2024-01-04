import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
from typing import Any, Final, Optional
import importlib.util
from pathlib import Path
import sys
import traceback
from types import ModuleType
import pygame
from .shared import CodeRunError, Exercise, ValidationError
#from .graph_plotter import GraphPlotter

TPS: Final[int] = 60
DELTA: Final[float] = 1 / TPS

class ErrorExercise:
    def __init__(self, exercise: Exercise, error: BaseException) -> None:
        self.name = exercise.name
        self.exercise = exercise
        self.error = error
    
    def tick(self, _):
        raise self.error

    def draw(self, surface):
        raise self.exercise.draw(surface)

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
_initialized = False
_running = True
_values_to_draw: list[str] = []

def show_value(label: str, value: Any):
    _values_to_draw.append(f"{label} = {value}")

def quit():
    global _running
    _running = False

def show_error(provided_exercise: Exercise, error: BaseException):
    run(ErrorExercise(provided_exercise, error))

def run(exercise: Exercise):
    if exercise is None:
        # TODO: Allow using autoreload without pygame?
        raise NotImplementedError()
    
    global _exercise, _initialized, _running

    _exercise = exercise
    del exercise # Unbind to avoid accidentally using the original exercise value and allow GC
    if _initialized:
        return
    _initialized = True

    # TODO: Figure out a way to reimplement solution file creation from template.
    # if not Path(solution_file).exists():
    #     print(f"Solution file {solution_file} did not exist! It was created based on a template.")
    #     with open(solution_file, mode='w', encoding='utf8') as f:
    #         f.write(exercise_constructor.get_template())
    
    # TODO: Maybe pass in the module instead?
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

    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    pygame.display.set_caption(f"{_exercise.name} / {Path(solution_file).name}")
    clock = pygame.time.Clock()
    variables_font = pygame.font.SysFont('Arial', 20)

    last_reload_check = pygame.time.get_ticks()

    while _running:
        should_reload = False

        # This separation of event.get and event.pump seems to make Pygame play nicely with Tk.
        # Taken from https://stackoverflow.com/questions/58598836/pygame-event-get-fatal-python-error-pyeval-restorethread-null-tstate
        # Presumably this helps because it avoids interacting with whatever shared resource pumping events requires
        # when there are no events (most frames Pygame receives no events).
        events = pygame.event.get(pump=False)
        if events:
            pygame.event.pump()
            for event in events:
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
            try:
                _exercise = None
                _reload_module(solution_module)
                show_message("Reloaded solution", "blue", 2000)
            except Exception as e:
                show_message(f"Error reloading solution: {type(e).__name__}: {e}", "red", None)
                traceback.print_exc()
            else:
                solution_module_valid = True
                if not _exercise:
                    # TODO: Better error message?
                    show_message(f"Reloaded solution did not call the required method to provide a solution", "red", None)

        if solution_module_valid and _exercise:
            try:
                # Tick with fixed delta to ensure that simulation is as deterministic as possible
                _exercise.tick(DELTA)
            except ValidationError as e:
                show_message(f"Invalid solution: {e}", "red", None)
                solution_module_valid = False
            except CodeRunError as e:
                cause = e.__cause__ or e.__context__
                if cause is None:
                    show_message(f"{e}: <unknown cause>", "red", None)
                else:
                    show_message(f"{e}: {type(cause).__name__}: {cause}", "red", None)
                    traceback.print_tb(cause.__traceback__)
                solution_module_valid = False
            except Exception as e:
                show_message(f"Error while running exercise tick (this should not happen): {type(e).__name__}: {e}", "red", None)
                traceback.print_exc()
                solution_module_valid = False

        screen.fill("white")

        _values_to_draw.append(f"FPS: {clock.get_fps():.2f}")

        if _exercise:
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

        clock.tick(TPS)

    pygame.quit()
