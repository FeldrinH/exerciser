# `exerciser`

A library for control exercises based on pygame.

## Usage

```bash
python exercise.py solution.py
```

`exercise.py` should call `exerciser.run(ExerciseClass)`, where `ExerciseClass` is a class implementing `exerciser.Exercise`.

`solution.py` should contain a top-level function named `control`. It will be called each tick with arguments returned by `ExerciseClass.get_args()` and its return value will be fed to `ExerciseClass.tick(..)`.
