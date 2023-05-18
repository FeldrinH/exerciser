import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import copy
from typing import Type
import numbers
import importlib.util
from pathlib import Path
import sys
import traceback
from types import ModuleType
import pygame
from .shared import Exercise, ValidationError
from .graph_plotter import GraphPlotter


def _load_module_from_file(file: str) -> ModuleType:
    # TODO: Better way to guarantee that module is unique?
    name = f'_solution_{Path(file).stem}'

    # From https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
    spec = importlib.util.spec_from_file_location(name, file)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

    return module

def _reload_module(module: ModuleType):
    # NB: Only use this for modules loaded using _load_module_from_file!

    spec = module.__spec__
    assert spec and spec.loader

    # Delete existing globals, to avoid old functions and constants lingering on reload.
    # TODO: importlib.reload preserves globals. Are there issues that might arise from deleting them?
    for key in list(vars(module)):
        if not key.startswith('__'):
            delattr(module, key)

    spec.loader.exec_module(module)

def _validate_solution_module(solution_module):
    # Check that
    # a) control function exists
    # b) control function is callable
    try:
        if not callable(solution_module.control):
            raise ValidationError
    except:
        raise ValidationError(f"Solution file ({Path(solution_module.__file__).name}) must contain top-level control() function!")

def run(exercise_constructor: Type[Exercise]):
    if len(sys.argv) != 2:
        print("ERROR: Wrong number of arguments!")
        print(f"Usage: python {sys.argv[0]} solution.py")
        sys.exit(1)

    solution_file = sys.argv[1]

    if not Path(solution_file).exists():
        print(f"ERROR: Solution file {solution_file} does not exist!")
        sys.exit(1)
    
    last_mtime = os.stat(solution_file).st_mtime
    solution_module = _load_module_from_file(solution_file)

    try:
        _validate_solution_module(solution_module)
    except ValidationError as e:
        print(f"ERROR: Invalid solution: {e}")
        sys.exit(1)

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
    pygame.display.set_caption(f"Exerciser - {Path(sys.argv[0]).name} / {Path(solution_file).name}")
    clock = pygame.time.Clock()
    variables_font = pygame.font.SysFont('Arial', 20)
    running = True

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
                    exercise = exercise_constructor()
                    args = exercise.get_args()
                    graph.clear()
        
        # TODO: Optimize this?
        if pygame.time.get_ticks() - last_reload_check >= 1000:
            last_reload_check = pygame.time.get_ticks()
            new_mtime = os.stat(solution_file).st_mtime
            if new_mtime != last_mtime:
                last_mtime = new_mtime
                solution_module_valid = False
                try:
                    _reload_module(solution_module)
                    show_message("Reloaded solution", "blue", 2000)
                except Exception as e:
                    show_message(f"Error reloading solution: {type(e).__name__}: {e}", "red", None)
                    traceback.print_exc()
                else:
                    try:
                        _validate_solution_module(solution_module)
                        solution_module_valid = True
                    except ValidationError as e:
                        show_message(f"Invalid solution: {e}", "red", None)

        if solution_module_valid:
            try:
                # TODO: Deep copy might have performance or compatibility problems, depending on how complex the internal state is.
                control_return = solution_module.control(*(copy.deepcopy(v) for v in args.values()))
            except Exception as e:
                show_message(f"Error while running control(): {type(e).__name__}: {e}", "red", None)
                traceback.print_exc()
                solution_module_valid = False
            else:
                # Tick with fixed delta to ensure that simulation is as deterministic as possible
                exercise.tick(1 / 60, control_return)

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
