from typing import Sequence, Tuple, Union
import pygame

from ._execute_gui import _values_to_draw

# Types copied from pygame/_common.pyi
Coordinate = Union[Tuple[float, float], Sequence[float], pygame.Vector2]
RGBAOutput = Tuple[int, int, int, int]
ColorValue = Union[pygame.Color, int, str, Tuple[int, int, int], RGBAOutput, Sequence[int]]

# TODO: This conflicts with a common name for a similar function in exercise files (for example see exercise1.py). Rename this to avoid the conflict?
def show_value(value: str):
    # For technical reasons drawing of values is currently implemented in _execute_gui.
    # This just adds the value to the list of values to draw.
    _values_to_draw.append(value)

def draw_dashed_line(surface: pygame.Surface, color: ColorValue, start: Coordinate, end: Coordinate, pattern: Tuple[int, int], width: int = 1):
    axis = pygame.Vector2(end) - pygame.Vector2(start)
    length = axis.length()
    axis.normalize_ip()

    # TODO: The individual dashes appear misaligned due to rounding of dash start and end coordinates. Is there some way to improve this? 
    dash_length, gap_length = pattern
    pos = 0
    pos_vec = pygame.Vector2(start)
    while pos < length:
        pygame.draw.line(surface, color, pos_vec, pos_vec + dash_length * axis, width)
        pos += dash_length + gap_length
        pos_vec += (dash_length + gap_length) * axis

def draw_arrow(surface: pygame.Surface, color: ColorValue, start_pos: Coordinate, offset: Coordinate, width: int):
    end_pos_vec = pygame.Vector2(start_pos[0] + offset[0], start_pos[1] + offset[1])
    dir_vec = pygame.Vector2(offset[0], offset[1])
    length = min(8, dir_vec.length())
    if dir_vec.length_squared() > 0:
        dir_vec.normalize_ip()
    pygame.draw.line(surface, color, start_pos, end_pos_vec, width)
    pygame.draw.lines(surface, color, False, [end_pos_vec + dir_vec.rotate(140) * length, end_pos_vec, end_pos_vec + dir_vec.rotate(220) * length], width)