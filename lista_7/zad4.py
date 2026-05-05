def make_generator(func):
    def generator():
        counter = 1
        while True:
            result = func(counter)
            counter += 1
            yield result

    return generator()


def fib(n):
    a = 0
    b = 1
    if n < 0:
        print("ERROR: Incorrect input")
        return None
    elif n == 0:
        return 0
    elif n == 1:
        return 1

    else:
        for i in range(1, n):
            c = a + b
            a = b
            b = c
        return b


def main():
    #a
    print("=== Fibonacci sequence ===")
    generator_fib = make_generator(fib)
    for i in range(8):
        print(next(generator_fib), end=" ")

    #b
    print("\n=== Lambda expression ===")
    print("--- Multiples of 2 ---")
    generator_lambda = make_generator(lambda x : x * 2)
    for i in range(8):
        print(next(generator_lambda), end=" ")

    print("\n--- Powers of 3 --- ")
    generator_powers = make_generator(lambda x: 3 ** x)
    for i in range(8):
        print(next(generator_powers), end=" ")

if __name__ == "__main__":
    main()
