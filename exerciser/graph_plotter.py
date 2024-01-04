import numbers
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
            