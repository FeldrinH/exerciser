
def control(ball) -> tuple[float, float]:
    return -ball.x * 0.8, -ball.y * 0.3

if __name__ == '__main__':
    import exercise1
    exercise1.run(control)