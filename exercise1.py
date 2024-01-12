import copy
import math
import numbers
import random
from typing import NamedTuple, Protocol
import matplotlib.pyplot
import exerciser
import pygame
import numpy as np

# NB: Do not edit this file!

class PID(Protocol):
    def control(self, delta: float, x: float) -> float:
        ...

class Params(NamedTuple):
    x: float
    angle: float

def _to_params(exercise: int | Params) -> Params:
    if isinstance(exercise, Params):
        return exercise
    elif exercise == 1:
        return Params(100, 0)
    elif exercise == 2:
        return Params(100, 30)
    elif exercise == 3:
        return Params(random.uniform(-200, 200), random.uniform(-60, 60))
    else:
        raise exerciser.ValidationError(f"Unknown exercise number: {exercise}")

_GRAVITY = 50 # Effective gravitational acceleration: 50 px/s^2

class BlockExercise(exerciser.Exercise):
    name = "Lab 1 - PID"

    # TODO: Currently distance units are pixels. Should we use more natural distance units such as meters with some kind of scaling constant?
    t = 0.0
    x: float
    vx = 0.0
    F = math.nan

    def __init__(self, pid: PID, exercise: int | Params):
        self.x, self.angle = _to_params(exercise)
        self.pid = pid
        self._gravity = math.sin(math.radians(self.angle)) * _GRAVITY 
        rect = pygame.Surface((30, 23))
        rect.set_colorkey("black")
        rect.fill("red")
        self._rect = pygame.transform.rotate(rect, -self.angle)

    def tick(self, delta: float):
        try:
            control_return = self.pid.control(delta, self.x)
        except Exception as err:
            raise exerciser.CodeRunError("Error running control method") from err

        if not isinstance(control_return, numbers.Real):
            # TODO: Show actual returned value?
            raise exerciser.ValidationError("Error simulating solution: Control method did not return a number")

        self.F = np.clip(control_return, -100, 100)       

        self.t += delta
        # TODO: Is silently ignoring NaN bad?
        self.vx += ((0 if math.isnan(self.F) else self.F) + self._gravity) * delta
        self.x += self.vx * delta

    def draw(self, screen: pygame.Surface):
        # if self.cursor is not None:
        #     self.cursor.set_xdata((self.t, self.t))

        exerciser.show_value("α", f"{round(self.angle, 1)}°")
        exerciser.show_value("t", round(self.t, 2))
        exerciser.show_value("x", round(self.x, 2))
        exerciser.show_value("vx", round(self.vx, 2))
        exerciser.show_value("F", round(self.F, 2))

        up_axis = pygame.Vector2(0, -1)
        up_axis.rotate_ip(self.angle)
        right_axis = pygame.Vector2(-up_axis.y, up_axis.x)
        center = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)

        exerciser.pygame.draw_dashed_line(screen, "gray", center + screen.get_height() * up_axis, center - screen.get_height() * up_axis, pattern=(10, 8))

        mass_center = center + self.x * right_axis
        rect_bounds = self._rect.get_rect()
        rect_bounds.center = (int(mass_center.x), int(mass_center.y))
        screen.blit(self._rect, rect_bounds)
        floor_center = center - 11 * up_axis
        pygame.draw.line(screen, "orange", floor_center + screen.get_width() * right_axis, floor_center - screen.get_width() * right_axis, width=2)

        # exerciser.pygame.draw_arrow(screen, "purple", mass_center, self._gravity * right_axis, 1)
        exerciser.pygame.draw_arrow(screen, "purple", mass_center, (0, _GRAVITY), 1)
        exerciser.pygame.draw_arrow(screen, "green3", mass_center, self.vx * right_axis, 2)
        if not math.isnan(self.F):
            exerciser.pygame.draw_arrow(screen, "blue", mass_center, self.F * right_axis, 2)

# TODO: Some kind of method to simulate and find stabilization time?

def simulate(pid: PID, exercise: int | Params):
    # TODO: Is there a meaningful risk that a student will create a PID class that breaks with deepcopy?
    # TODO: The current presimulation approach is convenient, but assumes that the PID controller is deterministic, which is not guaranteed.
    # TODO: The current presimulation approach means that any console output and other side effects in the first 30 seconds will happen twice.

    # Convert to params immediately to ensure both simulations get the same random values
    params = _to_params(exercise)

    fig = matplotlib.pyplot.figure(num=BlockExercise.name, clear=True)
    ax = fig.gca()

    # TODO: Some way for students to graph custom values?
    hist_t = np.arange(0, 30, exerciser.DELTA)
    hist_x = []
    hist_vx = []
    hist_F = []
    presimulate_exercise = BlockExercise(copy.deepcopy(pid), params)
    for t in hist_t:
        try:
            presimulate_exercise.tick(exerciser.DELTA)
        except (exerciser.CodeRunError, exerciser.ValidationError):
            # TODO: Better wording?
            ax.set_xlabel(f"Error simulating solution at t = {t:.2f}", color="red", loc='right')
            break
        hist_x.append(presimulate_exercise.x)
        hist_vx.append(presimulate_exercise.vx)
        hist_F.append(presimulate_exercise.F)
    # cursor = ax.axvline(x=0.0, lw=0.8)
    ax.axhline(y=0.0, lw=0.8, ls='--', color="darkgrey")
    ax.plot(hist_t[:len(hist_x)], hist_x, label="x", color="red")
    ax.plot(hist_t[:len(hist_vx)], hist_vx, label="vx", color="green")
    ax.plot(hist_t[:len(hist_F)], hist_F, label="F", color="blue")
    ax.legend()
    
    matplotlib.pyplot.show(block=False)

    exerciser.run(BlockExercise(pid, params))

if __name__ == '__main__':
    raise RuntimeError("Do not run this file directly. Instead call the simulate(..) function from this module in your solution.")
