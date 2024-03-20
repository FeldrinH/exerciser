from typing import Sequence, Tuple, Union
import pygame
from matplotlib.backends.backend_agg import FigureCanvasAgg

# Types copied from pygame/_common.pyi
Coordinate = Union[Tuple[float, float], Sequence[float], pygame.Vector2]
RGBAOutput = Tuple[int, int, int, int]
ColorValue = Union[pygame.Color, int, str, Tuple[int, int, int], RGBAOutput, Sequence[int]]

# TODO: Make these functions use anti-aliasing so the lines look nicer.

def draw_dashed_line(surface: pygame.Surface, color: ColorValue, start: Coordinate, end: Coordinate, pattern: Tuple[int, int], width: int = 1):
    axis = pygame.Vector2(end) - pygame.Vector2(start)
    if axis.length_squared() == 0.0:
        return
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

def draw_spring(surface: pygame.Surface, color: ColorValue, start: Coordinate, end: Coordinate, coil_count: int, coil_width: int, end_length = 5, width: int = 1):
    axis = pygame.Vector2(end) - pygame.Vector2(start)
    if axis.length_squared() == 0.0:
        return
    coil_height = (axis.length() - 2 * end_length) / (2 * coil_count)
    axis.normalize_ip()
    coil_line = pygame.Vector2(coil_height, coil_width).rotate(pygame.Vector2(1, 0).angle_to(axis))
    coil_reverse_line = coil_line.reflect(pygame.Vector2(-axis.y, axis.x))

    pos = pygame.Vector2(start)
    pygame.draw.line(surface, color, pos, pos + end_length * axis, width)
    pos += end_length * axis
    pygame.draw.line(surface, color, pos, pos + 0.5 * coil_line, width)
    pos += 0.5 * coil_line
    pygame.draw.line(surface, color, pos, pos + coil_reverse_line, width)
    pos += coil_reverse_line
    for _ in range(coil_count - 1):
        pygame.draw.line(surface, color, pos, pos + coil_line, width)
        pos += coil_line
        pygame.draw.line(surface, color, pos, pos + coil_reverse_line, width)
        pos += coil_reverse_line
    pygame.draw.line(surface, color, pos, pos + 0.5 * coil_line, width)
    pos += 0.5 * coil_line
    pygame.draw.line(surface, color, pos, end, width)

def draw_figure(surface: pygame.Surface, canvas: FigureCanvasAgg, left: float, top: float, width: float, height: float):
    """Draws the Matplotlib figure attached to the given canvas"""
    width, height = int(width), int(height)
    size = canvas.get_width_height(physical=True)
    if width != size[0] or height != size[1]:
        # Note: No layout engine (the default) generally does not work well when resizing figures, so we automatically apply tight layout.
        # Keeping tight layout (or any layout engine) constantly enabled is not desireable, because it hurts drawing performance.
        dpi = canvas.figure.get_dpi()
        canvas.figure.set_size_inches((width + 0.25) / dpi, (height + 0.25) / dpi, forward=False)
        canvas.figure.tight_layout()
        size = canvas.get_width_height(physical=True)
    canvas.draw()
    image = pygame.image.frombuffer(canvas.buffer_rgba(), size, 'RGBA').convert()
    surface.blit(image, (left, top))
