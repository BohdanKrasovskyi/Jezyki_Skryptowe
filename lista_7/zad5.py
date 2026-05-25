import functools
from zad4 import make_generator
from zad4 import fib

def make_generator_mem(func):
    cached_func = functools.cache(func)
    return make_generator(cached_func)

@functools.cache
def fib_rec(n):
    if n < 0:
        print("ERROR: Incorrect input")
        return None

    print(f"Calculating for n = {n}: ")

    if n == 0:
        return 0
    elif n == 1:
        return 1
    else: return fib_rec(n-1) + fib_rec(n-2)

def main():
    print("=== Fibonacci sequence ===")
    fib_generator = make_generator_mem(fib)
    for i in range(8):
        print(next(fib_generator), end= " ")

    print("\n=== Cached Fibonacci sequence ===")
    print("---Pierwsze obliczenia---")
    res1 = fib_rec(6)
    print(res1)
    print("---Brakuje jednego obliczenia---")
    res2 = fib_rec(7)
    print(res2)
    print("---Wynik już w pamięci---")
    res3 = fib_rec(6)
    print(res3)
    print("--- Błędne dane na wejściu ---")
    print(fib_rec(-1))

if __name__ == "__main__":
    main()
