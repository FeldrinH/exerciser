# `exerciser`

A library for control exercises based on pygame.

## Usage

```bash
python solution.py
```

`solution.py` should be written by the student and should import the relevant exercise and call `exercise.run(control)` where `control` is a function that takes in the current state and retuns some values describing the desired action (e.g. a force to apply).

Each exercise should define a `run` function that calls `exerciser.run(ExerciseClass, control)`, where `ExerciseClass` is a class implementing [`exerciser.Exercise`](/exerciser/shared.py) and `control` is the function provided by the student.

The supplied `control` function is called each tick with arguments returned by `ExerciseClass.get_args()` and its return value is fed to `ExerciseClass.tick(...)`.

The solution file is automatically reloaded every time it changes. There will eventually be a public API to enable automatic reloading for other modules/files.

Note: The API in general and the top-level public API specifically are very much experimental and subject to change. See [`/exercise1.py`](/exercise1.py) and [`/exercise1_solution.py`](/exercise1_solution.py) for an up to date example.

## Minimum Python version

This library currently requires at least Python 3.10 (because it uses https://peps.python.org/pep-0604/).

By removing some convenience features it should be possible to get down to 3.8.
Going below 3.8 will degrade user experience, because exercise type checking depends heavily on https://peps.python.org/pep-0544/.
