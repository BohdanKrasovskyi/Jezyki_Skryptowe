import random
import string


class PasswordGenerator:
    def __init__(self, length, charset=string.ascii_letters + string.digits, count=10):
        self.length = length
        self.charset = charset
        self.count = count
        self._generated = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._generated >= self.count:
            raise StopIteration
        self._generated += 1
        return "".join(random.choices(self.charset, k=self.length))


if __name__ == "__main__":
    gen = PasswordGenerator(length=12, count=3)

    print("--- next() calls ---")
    print(next(gen))
    print(next(gen))
    print(next(gen))
    try:
        print(next(gen))
    except StopIteration:
        print("StopIteration raised as expected")

    print("\n--- for loop ---")
    for pwd in PasswordGenerator(length=8, count=5):
        print(pwd)

    print("\n--- custom charset (digits only) ---")
    for pin in PasswordGenerator(length=4, charset=string.digits, count=3):
        print(pin)