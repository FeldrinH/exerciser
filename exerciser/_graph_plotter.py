import numbers
from typing import Iterable
import matplotlib.pyplot
from matplotlib.lines import Line2D
import pygame

# TODO: Do we actually want to use this?
# Currently the example simulates n seconds ahead of time and uses matplotlib instead
class GraphPlotter:
    points: dict[str, list[numbers.Real]]
    limit: int

    def __init__(self, limit: int):
        self.series_font = pygame.font.SysFont("Arial", 16)
        self.points = {}
        self.limit = limit

    def add_point(self, series: str, value: numbers.Real):
        if series not in self.points:
            self.points[series] = []
        
        series_values = self.points[series]
        series_values.append(value)
        if len(series_values) > self.limit:
            series_values.pop(0)
    
    def clear(self):
        self.points.clear()
    
    def draw(self, screen: pygame.Surface, origin_x: int, origin_y: int):
        for series, values in self.points.items(): 
            line_points = [(origin_x + i, origin_y + v) for i, v in enumerate(values)]
            if len(line_points) > 1:
                pygame.draw.aalines(screen, "gray", False, line_points, 2)
                series_text = self.series_font.render(series, True, "gray")
                screen.blit(series_text, line_points[-1])

# This allows plotting with matplotlib in more or less real time.
# TODO: Do we want to use this?
class InteractivePlot:
    def __init__(self, lines: list[Line2D]):
        self.lines = lines
        self.data_x = []
        self.data_y = [[] for _ in lines]

    def append(self, x: float, y: Iterable[float]):
        self.data_x.append(x)
        for i, val in enumerate(y):
            self.data_y[i].append(val)

    def draw(self):
        # TODO: Only update on some ticks for performance? This makes the matplotlib window feel laggy.
        if len(self.data_x) % 6 == 0:
            for i, line in enumerate(self.lines):
                line.set_xdata(self.data_x)
                line.set_ydata(self.data_y[i])
            matplotlib.pyplot.gca().relim()
            matplotlib.pyplot.gca().autoscale_view()
            # TODO: This moves the matplotlib window on top of other windows. Can this be fixed?
            matplotlib.pyplot.pause(0.01)
