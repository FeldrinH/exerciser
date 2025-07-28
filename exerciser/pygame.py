from typing import List, Sequence, Tuple, Union
from dataclasses import dataclass
import os
import math
import pygame
from matplotlib.backends.backend_agg import FigureCanvasAgg

# Types copied from pygame/_common.pyi
Coordinate = Union[Tuple[float, float], Sequence[float], pygame.Vector2]
ColorValue = Union[pygame.Color, int, str, Tuple[int, int, int], Tuple[int, int, int, int], Sequence[int]]

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

_setup_done = False

@dataclass(frozen=True)
class _AxisParams:
    label: str
    range: float
    bounds: Tuple[float, float]
    step: float
    formatter: str
    align_right: bool

class LinePlot:
    """Pygame based line plot. More limited than Matplotlib, but also much more performant."""

    def __init__(self):
        self._lines: List[LinePlotLine] = []
        self._yaxes: List[_AxisParams] = []
    
    def add_xaxis(self, *, label: str, range: float, step: float, formatter: str = "{}"):
        self._xaxis = _AxisParams(label, range, (0, 0), step, formatter, False)
    
    def add_yaxis(self, *, label: str, bounds: Tuple[float, float], step: float, formatter: str = "{}", align_right: bool = False):
        self._yaxes.append(_AxisParams(label, 0, bounds, step, formatter, align_right))
    
    def add_line(self, *, label: str, color: ColorValue, yaxis: int = 0) -> 'LinePlotLine':
        line = LinePlotLine(label, color, yaxis)
        self._lines.append(line)
        return line

    def draw(self, surface: pygame.Surface, left: float, top: float, width: float, height: float):
        global _setup_done, _axes_font
        if _setup_done:
            _setup_done = True
            _axes_font = pygame.font.Font(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Roboto-Regular-Modified.ttf'), 20)
        
        # TODO: Draw axes
        
        for line in self._lines:
            x_max = max(line._points[-1][0] for line in self._lines)
            xaxis_bounds = (x_max - self._xaxis.range, x_max)
            # TODO: Calculate correct bounds that account for and padding
            line._draw(surface, left, top, width, height, xaxis_bounds, self._yaxes[line._yaxis].bounds)

class LinePlotLine:
    """Individual line plot line. Created by calling `LinePlot.add_line`."""

    def __init__(self, label: str, color: ColorValue, yaxis: int):
        self._label = label
        self._color = color
        self._yaxis = yaxis
        self._points = []

    def add_point(self, x: float, y: float):
        self._points.append((x, y))
    
    def clear(self):
        self._points.clear()

    def _draw(self, surface: pygame.Surface, left: float, top: float, width: float, height: float, xaxis_bounds: Tuple[float, float], yaxis_bounds: Tuple[float, float]):
        yaxis_discontinuity_limit = (yaxis_bounds[1] - yaxis_bounds[0]) * 0.8 # TODO: Should this be an explicit parameter?
        x_offset, x_scaler = -xaxis_bounds[0], width / (xaxis_bounds[1] - xaxis_bounds[0])
        y_offset, y_scaler = -yaxis_bounds[1], height / (yaxis_bounds[0] - yaxis_bounds[1])
        
        y_prev = math.nan
        segments = [[]]
        for x, y in self._points:
            if x >= xaxis_bounds[0]:
                if abs(y - y_prev) > yaxis_discontinuity_limit:
                    segments.append([])
                y_prev = y
                segments[-1].append((left + (x + x_offset) * x_scaler, top + (y + y_offset) * y_scaler))
                
        for points in segments:
            if len(points) >= 2:
                pygame.draw.lines(surface, self._color, False, points, 2)
