# `exerciser`

A library for control exercises based on Pygame.

## Usage

Each exercise should define a function that calls `exerciser.run(exercise)`, where `exercise` is an object implementing [`exerciser.Exercise`](/exerciser/_shared.py).

TODO: Describe error handling and specialized error types.

Note: The API in general and the top-level public API specifically are very much experimental and subject to change. See [`exercise1.py`](/exercise1.py) and [`exercise1_solution.py`](/exercise1_solution.py) for an up to date example.

## Minimum Python version

This libarary should support Python 3.8 and above.

Going below 3.8 will degrade user experience, because exercise type checking depends heavily on https://peps.python.org/pep-0544/.

Python 3.8 compatibility has been checked using static analysis tool [vermin](https://github.com/netromdk/vermin).
TODO: Currently tested on 3.10. Validate that it actually runs on 3.8.
