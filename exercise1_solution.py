import math
import exercise1

class PID:
    def __init__(self):
        self.last_x = math.nan

    def control(self, delta: float, x: float) -> float:
        vx = (x - self.last_x) / delta
        self.last_x = x
        # if abs(x) < 0.01 and abs(vx) < 0.01:
        #    raise RuntimeError("Stabiilne")
        return -x * 1.5 - vx * 2.0

if __name__ == '__main__':
    exercise1.simulate(PID, exercise=1)