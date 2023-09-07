import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import copy
from typing import Callable, Type
import numbers
import importlib.util
from pathlib import Path
import sys
import traceback
from types import ModuleType
import pygame
from .shared import Exercise, ValidationError
from .graph_plotter import GraphPlotter


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

_initialized = False
_control_function = None

def run(exercise_constructor: Type[Exercise], new_control_function: Callable, *, autorestart_default: bool = False):
    global _initialized, _control_function
    _control_function = new_control_function
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

    def show_message(message: str, message_color, message_duration_ms: int | None):
        nonlocal last_message, last_message_color, last_message_hide
        print(message)
        last_message = message
        last_message_color = message_color
        last_message_hide = pygame.time.get_ticks() + message_duration_ms if message_duration_ms is not None else None

    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    pygame.display.set_caption(f"Exerciser - {exercise_constructor.name} / {Path(solution_file).name}")
    clock = pygame.time.Clock()
    variables_font = pygame.font.SysFont('Arial', 20)
    running = True

    autorestart = autorestart_default

    exercise = exercise_constructor()
    args = exercise.get_args()
    graph = GraphPlotter(800)

    last_reload_check = pygame.time.get_ticks()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    if event.mod & pygame.KMOD_CTRL:
                        autorestart = not autorestart
                        show_message("Automatic restart enabled" if autorestart else "Automatic restart disabled", "green2", 2000)
                    else:
                        exercise = exercise_constructor()
                        args = exercise.get_args()
                        graph.clear()
        
        # TODO: Optimize this?
        if pygame.time.get_ticks() - last_reload_check >= 1000:
            last_reload_check = pygame.time.get_ticks()
            new_mtime = os.stat(solution_file).st_mtime
            if new_mtime != last_mtime:
                last_mtime = new_mtime
                try:
                    _control_function = None
                    _reload_module(solution_module)
                    show_message("Reloaded solution", "blue", 2000)
                except Exception as e:
                    show_message(f"Error reloading solution: {type(e).__name__}: {e}", "red", None)
                    traceback.print_exc()
                else:
                    if  autorestart and _control_function:
                        exercise = exercise_constructor()
                        args = exercise.get_args()
                        graph.clear()

        if solution_module_valid and _control_function:
            try:
                # TODO: Deep copy might have performance or compatibility problems, depending on how complex the internal state is.
                control_return = _control_function(*(copy.deepcopy(v) for v in args.values()))
            except Exception as e:
                show_message(f"Error while running control(): {type(e).__name__}: {e}", "red", None)
                traceback.print_exc()
                solution_module_valid = False
            else:
                try:
                    # Tick with fixed delta to ensure that simulation is as deterministic as possible
                    exercise.tick(1 / 60, control_return)
                except ValidationError as e:
                    show_message(f"Invalid solution: {e}", "red", None)
                    solution_module_valid = False
                except Exception as e:
                    show_message(f"Error while running exercise tick (this should not happen): {type(e).__name__}: {e}", "red", None)
                    traceback.print_exc()
                    solution_module_valid = False

        screen.fill("white")

        exercise.draw(screen)

        # Output variable values
        variables = [
            (f"{arg_k}.{k}", v)
            for arg_k, arg_v in args.items()
            for k, v in vars(arg_v).items()
            if not k.startswith('_')
        ]
        for i, (k, v) in enumerate(variables):
            variables_text_surface = variables_font.render(f"{k} = {repr(v)}", True, "black")
            screen.blit(variables_text_surface, (0, i * 25))
            if isinstance(v, numbers.Real):
                graph.add_point(k, v)
        
        graph.draw(screen, 0, screen.get_height() - 200)
        
        if last_message_hide is None or pygame.time.get_ticks() < last_message_hide:
            message_text_surface = variables_font.render(last_message, True, last_message_color)
            screen.blit(message_text_surface, (0, screen.get_height() - 25))

        pygame.display.flip()

        clock.tick(60)

    pygame.quit()
