# `exerciser`

A library for control exercises based on pygame.

## Usage

```bash
python exercise.py solution.py
```

`exercise.py` should call `exerciser.run(ExerciseClass)`, where `ExerciseClass` is a class implementing [`exerciser.Exercise`](/exerciser/shared.py).

`solution.py` should contain a top-level function named `control`. It will be called each tick with arguments returned by `ExerciseClass.get_args()` and its return value will be fed to `ExerciseClass.tick(..)`.

## Minimum Python version

This library currently requires at least Python 3.10 (because it uses https://peps.python.org/pep-0604/).

By removing some convenience features it should be possible to get down to 3.8.
Going below 3.8 will degrade user experience, because exercise type checking depends heavily on https://peps.python.org/pep-0544/.
