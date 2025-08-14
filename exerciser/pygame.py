from typing import List, Sequence, Tuple, Union
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

class LinePlot:
    """Pygame based line plot. More limited than Matplotlib, but also much more performant."""

    def __init__(self, *, x_label: str, x_range: float, x_formatter: str = "{}"):
        self._x_label = x_label
        self._x_range = x_range
        self._x_formatter = x_formatter
        self._lines: List[_LinePlotLine] = []
    
    def add_line(self, *, label: str, color: ColorValue, 
                 bounds: Tuple[float, float] | None = None, range: float | None = None, formatter: str = "{}"):
        line = _LinePlotLine(label, color, bounds, range, formatter)
        self._lines.append(line)
    
    def add_data(self, x: float, y: tuple[float, ...]):
        assert len(y) == len(self._lines)
        for y_l, line in zip(y, self._lines):
            line._points.append((x, y_l))
    
    def clear(self):
        for line in self._lines:
            line._points.clear()

    def draw(self, surface: pygame.Surface, left: float, top: float, width: float, height: float):
        global _setup_done, _axes_font
        if not _setup_done:
            _setup_done = True
            _axes_font = pygame.font.Font(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Roboto-Regular-Modified.ttf'), 16)

        top += 2
        left += 2
        width -= 5
        height -= 5

        x_min = min((line._points[0][0] for line in self._lines if line._points), default=0.0)
        x_max = max((line._points[-1][0] for line in self._lines if line._points), default=0.0)
        x_start = max(x_min, x_max - self._x_range)
        x_bounds = (x_start, x_start + self._x_range)

        axis_height = 40
        axis_width = 60
        pad = 8

        padded_left = left + axis_width
        padded_width = width - axis_width

        line_height = (height - axis_height) / len(self._lines)
        
        # Draw plot lines and top line of each bounding box
        for i, line in enumerate(self._lines):
            # TODO: Calculate correct height that accounts for padding
            line_top = top + i * line_height
            line._draw(surface, padded_left, line_top, padded_width, line_height, axis_width, pad, x_bounds)
            pygame.draw.line(surface, 'black', (padded_left, line_top), (padded_left + padded_width, line_top))
        
        axis_top = top + height - axis_height

        # Draw remaining bounding box lines
        pygame.draw.line(surface, 'black', (padded_left, axis_top), (padded_left + padded_width, axis_top))
        pygame.draw.line(surface, 'black', (padded_left, top), (padded_left, axis_top))
        pygame.draw.line(surface, 'black', (padded_left + padded_width, top), (padded_left + padded_width, axis_top))

        # Draw x-axis ticks
        x_offset, x_scaler = -x_bounds[0], (padded_width - 2 * pad) / (x_bounds[1] - x_bounds[0])
        step, indexes = _plot_calculate_steps(x_bounds, 10) # TODO: Smarter step calculation
        for i in indexes:
            value = i * step
            x = padded_left + pad + (value + x_offset) * x_scaler
            pygame.draw.line(surface, 'black', (x, axis_top), (x, axis_top + 5))
            label = _axes_font.render(self._x_formatter.format(value), True, 'black') # type: ignore
            surface.blit(label, (x - label.get_width() / 2, axis_top + 5))
        
        # Draw x-axis label
        label = _axes_font.render(self._x_label, True, 'black') # type: ignore
        surface.blit(label, (padded_left + padded_width / 2, axis_top + 22))

class _LinePlotLine:
    def __init__(self, label: str, color: ColorValue, bounds: Tuple[float, float] | None, range: float | None, formatter: str):
        self._label = label
        self._color = color
        self._bounds = bounds
        self._range = range
        self._formatter = formatter
        self._points = []

    def _draw(self, surface: pygame.Surface, left: float, top: float, width: float, height: float,
              axis_width: float, pad: float, x_bounds: Tuple[float, float]):
        # TODO: Use fact that points.x is sorted to optimize this?
        visible_points = [(x, y) for x, y in self._points if x >= x_bounds[0]]
        
        if self._bounds is not None:
            y_bounds = self._bounds
        else:
            y_bounds = (min((y for _, y in visible_points), default=0.0), max((y for _, y in visible_points), default=0.0))
            if self._range is not None and y_bounds[1] - y_bounds[0] < self._range:
                y_bounds_center = sum(y_bounds) / 2
                y_bounds = (y_bounds_center - self._range / 2, y_bounds_center + self._range / 2)
        
        x_offset, x_scaler = -x_bounds[0], (width - 2 * pad) / (x_bounds[1] - x_bounds[0])
        y_offset, y_scaler = -y_bounds[1], (height - 2 * pad) / (y_bounds[0] - y_bounds[1])
        
        # Split plot line into segments
        segments = [[]]
        for x, y in visible_points:
            if math.isnan(y):
                segments.append([])
            else:
                segments[-1].append((left + pad + (x + x_offset) * x_scaler, top + pad + (y + y_offset) * y_scaler))
        
        # Draw plot line
        for points in segments:
            if len(points) >= 2:
                pygame.draw.lines(surface, self._color, False, points, 2)
        
        # Draw y-axis ticks
        step, indexes = _plot_calculate_steps(y_bounds, 5) # TODO: Smarter step calculation
        for i in indexes:
            value = i * step
            y = top + pad + (value + y_offset) * y_scaler
            pygame.draw.line(surface, 'black', (left, y), (left - 5, y))
            label = _axes_font.render(self._formatter.format(value), True, 'black')
            surface.blit(label, (left - 5 - label.get_width(), y - label.get_height() / 2))
        
        # Draw y-axis label
        label = _axes_font.render(self._label, True, 'black')
        label = pygame.transform.rotate(label, 90)
        surface.blit(label, (left - axis_width, top + height / 2 - label.get_height() / 2))

def _plot_calculate_steps(bounds: Tuple[float, float], steps: int):
    # TODO: Smarter step calculation
    step = (bounds[1] - bounds[0]) / steps
    if step < 0.75:
        step = 0.5
    else:
        step = round(step)
    indexes = range(math.ceil(bounds[0] / step - 0.001), math.floor(bounds[1] / step + 0.001) + 1)
    return step, indexes
