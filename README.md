# `exerciser`

A library for control exercises based on pygame.

## Usage

```bash
python solution.py
```

`solution.py` should be written by the student and should import the relevant exercise and call its run/simulate function with whatever arguments the specific exercise requires.

Each exercise should define a function that calls `exerciser.run(exercise)`, where `exercise` is an object implementing [`exerciser.Exercise`](/exerciser/shared.py).

The solution file is automatically reloaded every time it changes. There may eventually be a public API to enable automatic reloading for other modules/files.

Note: The API in general and the top-level public API specifically are very much experimental and subject to change. See [`/exercise1.py`](/exercise1.py) and [`/exercise1_solution.py`](/exercise1_solution.py) for an up to date example.

## Minimum Python version

This libarary should support Python 3.8 and above.

Going below 3.8 will degrade user experience, because exercise type checking depends heavily on https://peps.python.org/pep-0544/.

TODO: Currently tested on 3.10. Validate that it actually works on 3.8.
