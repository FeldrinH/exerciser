import exerciser
import pygame
import numpy as np

class PointMass:
    vx = 0.0
    vy = 0.0
    x = 100.0
    y = 100.0
    _last_acceleration = (0, 0)

class BlockExercise:
    def __init__(self):
        self.ball = PointMass()

    def get_args(self):
        return { "ball": self.ball }
    
    def tick(self, delta, control_return):
        acceleration = np.clip(control_return, -1000, 1000)
        self.ball.vx += acceleration[0] * delta
        self.ball.vy += acceleration[1] * delta
        self.ball.x += self.ball.vx * delta
        self.ball.y += self.ball.vy * delta
        self.ball._last_acceleration = acceleration
    
    def draw(self, screen: pygame.Surface):
        center_pos = (self.ball.x + screen.get_width() / 2, self.ball.y + screen.get_height() / 2)
        pygame.draw.circle(screen, "red", center_pos, 30)
        exerciser.pygame.draw_arrow(screen, "green3", center_pos, (self.ball.vx, self.ball.vy), 2)
        exerciser.pygame.draw_arrow(screen, "blue", center_pos, self.ball._last_acceleration, 2)
    
if __name__ == '__main__':
    exerciser.run(BlockExercise)
