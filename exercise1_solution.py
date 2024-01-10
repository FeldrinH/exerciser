import math
import exercise1
import exerciser

class PID:
    def __init__(self, a: float, b: float):
        self.a = a
        self.b = b
        self.last_x = math.nan

    def control(self, delta: float, x: float) -> float:
        vx = (x - self.last_x) / delta
        self.last_x = x
        return -x * self.a - vx * self.b

def simulate(pid: PID):
    ex = exercise1.BlockExercise(pid)
    for _ in range(10 * exerciser.TPS):
        ex.tick(exerciser.DELTA)
        if abs(ex.vx) <= 0.01 and abs(ex.x) <= 0.01:
            return ex.t
    return math.inf

def optimize():
    min_a, min_b = 0, 0
    min_t = math.inf
    for a in range(0, 50):
        a /= 10
        for b in range(0, 50):
            b /= 10
            t = simulate(PID(a, b))
            if t < min_t:
                min_t = t
                min_a, min_b = a, b
                print(f"a={a} b={b} t={t}")
    return min_a, min_b

if __name__ == '__main__':
    exercise1.simulate(PID(4.0, 4.0), exercise=1)