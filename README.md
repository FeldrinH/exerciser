# `exerciser`

A library for control exercises based on Pygame.

## Usage

Each exercise should define a function that calls `exerciser.run(create_simulation)`, where `create_simulation` is a lambda/function that returns objects implementing [`exerciser.Simulation`](/exerciser/_shared.py) (`create_simulation` may be called more than once to restart the simulation and should return a new simulation object every time).

Calling `exerciser.run` opens a new Pygame window (or replaces the simulation in the existing window if called multiple times) and runs the simulation in that window.

The simulation has two required methods:
* `tick` is given the time elapsed since the last call to `tick` (by default 1/60 s) and should update the internal state of the simulation.
If you need to call student code while simulating then it should be done in this method.
This allows for good error handling (see special exception handling section below) and ensures that values shown in student code using `excerciser.show_value` show up correctly.
* `draw` is given the Pygame window surface and should draw the simulation on screen. It should generally avoid changing the internal state of the simulation.
Some helper methods for drawing common elements can be found under [`exerciser.pygame`](/exerciser/pygame.py)

Additionally, the simulation has one optional method:
* `handle_input` is passed the list of events from `pygame.event.get()` and can be used to handle user input and make simulations interactive.  
You can call methods in `pygame.key`, `pygame.mouse`, and other related modules to retrieve additional info about user input.  
If you need the screen surface for calculating screen space coordinates then you can obtain it using `pygame.display.get_surface()`.

During each frame the methods are called in the order `handle_input` -> `tick` -> `draw`. Under certain conditions, `handle_input` and `tick` may not be called (see below for more details).

## Special exception handling

Exceptions thrown from simulation methods generally cause the window to close and the system to exit. However, there are some exception types that get special treatment when raised in `tick`. These are primarily designed for handling situations where student code called in `tick` behaves unexpectedly or raises an exception:

* [`exerciser.ValidationError`](/exerciser/_shared.py) shows the error message on screen with no other details. This can be used to show a general-purpose error message to the user.
* [`exerciser.CodeRunError`](/exerciser/_shared.py) shows the error message followed by the error type and message of the cause (a cause can be attached to the error using `raise exerciser.CodeRunError("Message") from cause`). This can be used to report an error that occurred when running student code and add some extra info to the error.

When any of these special error types are caught the system does not exit. Instead the error is shown on screen and the simulation is stopped (`handle_input` and `tick` are no longer called). Note that `draw` is still called even when the simulation is stopped. Also note that this is distinct from the simulation being paused. When the simulation is paused then both `handle_input` and `draw` are still called, but `tick` is not.

## Controls

There are some useful keybinds available in the simulation window:

* R - restart the simulation
* P - pause the simulation
* S - step the simulation (advance by one frame; if not paused pauses the simulation)
* F1 - show help

## Minimum Python version

This library should support Python 3.8 and above.

Going below 3.8 will degrade user experience, because public API type checking depends heavily on https://peps.python.org/pep-0544/.

Python 3.8 compatibility has been checked using static analysis tool [Vermin](https://github.com/netromdk/vermin).
