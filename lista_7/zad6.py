import logging
import functools
import time
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def log(level=logging.DEBUG):
    def decorator(obj):
        if isinstance(obj, type):
            original_init = obj.__init__

            @functools.wraps(original_init)
            def patched_init(self, *args, **kwargs):
                logging.log(
                    level,
                    "Instantiating %s  args=%s  kwargs=%s",
                    obj.__name__, args, kwargs,
                )
                original_init(self, *args, **kwargs)

            obj.__init__ = patched_init
            return obj

        @functools.wraps(obj)
        def wrapper(*args, **kwargs):
            call_time = datetime.now().isoformat(timespec="milliseconds")
            t0 = time.perf_counter()
            result = obj(*args, **kwargs)
            duration = time.perf_counter() - t0
            logging.log(
                level,
                "Function '%s'  called_at=%s  duration=%.6fs  args=%s  kwargs=%s  returned=%r",
                obj.__name__, call_time, duration, args, kwargs, result,
            )
            return result

        return wrapper

    return decorator


# ── demo ─────────────────────────────────────────────────────────────────────

@log(level=logging.INFO)
def add(a, b):
    return a + b


@log(level=logging.DEBUG)
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"


@log(level=logging.WARNING)
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Point({self.x}, {self.y})"


if __name__ == "__main__":
    print(add(3, 4))
    print(greet("Alice"))
    print(greet("Bob", greeting="Hi"))
    p = Point(1, 2)
    print(p)