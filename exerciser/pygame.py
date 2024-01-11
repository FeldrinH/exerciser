from typing import Sequence, Tuple, Union
import pygame

# Types copied from pygame/_common.pyi
Coordinate = Union[Tuple[float, float], Sequence[float], pygame.Vector2]
RGBAOutput = Tuple[int, int, int, int]
ColorValue = Union[pygame.Color, int, str, Tuple[int, int, int], RGBAOutput, Sequence[int]]

def draw_arrow(surface: pygame.Surface, color: ColorValue, start_pos: Coordinate, offset: Coordinate, width: int):
    end_pos_vec = pygame.Vector2(start_pos[0] + offset[0], start_pos[1] + offset[1])
    dir_vec = pygame.Vector2(offset[0], offset[1])
    length = min(8, dir_vec.length())
    if dir_vec.length_squared() > 0:
        dir_vec.normalize_ip()
    pygame.draw.line(surface, color, start_pos, end_pos_vec, width)
    pygame.draw.lines(surface, color, False, [end_pos_vec + dir_vec.rotate(140) * length, end_pos_vec, end_pos_vec + dir_vec.rotate(220) * length], width)