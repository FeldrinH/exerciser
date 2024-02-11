# `exerciser`

A library for control exercises based on Pygame.

## Usage

Each exercise should define a function that calls `exerciser.run(create_simulation)`, where `create_simulation` is a lambda/function that returns objects implementing [`exerciser.Simulation`](/exerciser/_shared.py) (`create_simulation` may be called more than once to restart the simulation and should return a new simulation object every time).

Calling `exerciser.run` opens a new Pygame window (or replaces the simulation in the existing window if called multiple times) and runs the simulation in that window.

The simulation has two required methods:
* `tick` is given the time elapsed since the last call to `tick` (by default 1/60 s) and should update the internal state of the simulation. If you need to call user-supplied code, then it should be done in this method (see below for some special exceptions available for error handling).
* `draw` is given the Pygame window surface and should draw the simulation on screen.

Additionally, the simulation has one optional method:
* `handle_input` can be used to handle user input and make simulations interactive (for example to move a simulated object using the mouse).
It is given the screen size for calculating screen space coordinates.  
You can call methods in `pygame.event`, `pygame.key`, `pygame.mouse` and other related modules to receive user input. Note: To avoid interfering with the main event loop, you should use `pygame.event.get(pump=False)` to get events.

During each frame the methods are called in the order `handle_input` -> `tick` -> `draw`. Under certain conditions, `handle_input` and `tick` may not be called (see below for more details).

## Special exception handling

Exceptions thrown from simulation methods generally cause the window to close and the system to exit. However, there are some exception types that get special treatment when raised in `tick`:

* [`exerciser.ValidationError`](/exerciser/_shared.py) shows the error message on screen with no other details. This can be used to show a general-purpose error message to the user.
* [`exerciser.CodeRunError`](/exerciser/_shared.py) shows the error message followed by the error type and message of the cause (a cause can be attached to the error using `raise exerciser.CodeRunError("Message") from cause`). This can be used to report an error that occurred when running student code and add some extra info to the error.

When any of these special error types are caught the system does not exit. Instead the error is shown on screen and the simulation is stopped (`handle_input` and `tick` are no longer called). Note that `draw` is still called even when the simulation is stopped. Also note that this is distinct from the simulation being paused. When the simulation is paused then both `handle_input` and `draw` are still called, but `tick` is not.

## Controls

There are some useful keybinds available in the simulation window:

* R - restart the simulation
* P - pause the simulation
* S - step the simulation (advance by one frame; if not paused pauses the simulation)

## Minimum Python version

This libarary should support Python 3.8 and above.

Going below 3.8 will degrade user experience, because exercise type checking depends heavily on https://peps.python.org/pep-0544/.

Python 3.8 compatibility has been checked using static analysis tool [vermin](https://github.com/netromdk/vermin).
