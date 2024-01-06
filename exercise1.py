import copy
from dataclasses import dataclass
import math
import numbers
import random
from typing import Optional, Protocol
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.pyplot
import exerciser
import pygame
import numpy as np

# NB: Do not edit this file!

class PID(Protocol):
    def control(self, delta: float, x: float) -> float:
        ...

@dataclass
class BlockExercise:
    name = "Lab 1 - PID"

    t = 0.0
    x = 100.0
    vx = 0.0
    F = math.nan
    pid_controller: PID
    cursor: Optional[Line2D] = None

    def tick(self, delta: float):
        try:
            control_return = self.pid_controller.control(delta, self.x)
        except Exception:
            raise exerciser.CodeRunError("Error running control method")

        if not isinstance(control_return, numbers.Real):
            # TODO: Show actual returned value?
            raise exerciser.ValidationError("Error simulating solution: Control method did not return a number")

        self.F = np.clip(control_return, -1000, 1000)       

        self.t += delta
        # TODO: Is silently ignoring NaN bad?
        if not math.isnan(self.F):
            self.vx += self.F * delta
        self.x += self.vx * delta

    def draw(self, screen: pygame.Surface):
        if self.cursor is not None:
            # TODO: Moving the cursor in real time seems to cause high CPU usage. Is there a way to improve this?
            self.cursor.set_xdata((self.t, self.t))

        # exerciser.show_value("t", round(self.t, 2))
        exerciser.show_value("x", round(self.x, 2))
        exerciser.show_value("vx", round(self.vx, 2))
        exerciser.show_value("F", round(self.F, 2))

        pygame.draw.line(screen, "gray", (screen.get_width() / 2, 0), (screen.get_width() / 2, screen.get_height()))

        center_pos = (self.x + screen.get_width() / 2, screen.get_height() / 2)
        pygame.draw.rect(screen, "red", ((center_pos[0] - 10, center_pos[1] - 10), (20, 20)))
        exerciser.pygame.draw_arrow(screen, "green3", center_pos, (self.vx, 0), 2)
        if not math.isnan(self.F):
            exerciser.pygame.draw_arrow(screen, "blue", center_pos, (self.F, 0), 2)

_initialized = False

def simulate(pid: PID, exercise: int):
    # TODO: Is there a meaningful risk that a student will create a PID class that breaks with deepcopy?
    # TODO: The current presimulation approach is convenient, but assumes that the PID controller is deterministic, which is not guaranteed.
    # TODO: The current presimulation approach means that any console output and other side effects in the first 30 seconds will happen twice.

    global _initialized

    fig = matplotlib.pyplot.figure(num=BlockExercise.name)
    ax = fig.gca()

    hist_t = np.arange(0, 30, exerciser.DELTA)
    hist_x = []
    hist_vx = []
    hist_F = []
    presimulate_exercise = BlockExercise(copy.deepcopy(pid))
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
    cursor = ax.axvline(x=0.0, lw=0.8)
    ax.plot(hist_t[:len(hist_x)], hist_x, label="x", color="red")
    ax.plot(hist_t[:len(hist_vx)], hist_vx, label="vx", color="green")
    ax.plot(hist_t[:len(hist_F)], hist_F, label="F", color="blue")
    ax.legend()
    
    if not _initialized:
        _initialized = True
        # Calling show only once avoids stealing focus and other unnecessary indicators on reload.
        matplotlib.pyplot.show(block=False)

    exerciser.run(BlockExercise(pid, cursor))

if __name__ == '__main__':
    raise RuntimeError("Do not run this file directly. Instead call the simulate(..) function from this module in your solution.")
