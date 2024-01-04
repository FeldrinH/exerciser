import math
import exercise1

class PID:
    def __init__(self):
        self.last_x = math.nan

    def control(self, delta: float, x: float) -> float:
        vx = (x - self.last_x) / delta
        self.last_x = x
        return -x * 1.5 - vx * 2

if __name__ == '__main__':
    exercise1.run(PID, exercise=1)