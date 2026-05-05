from functools import reduce


def forall(pred, iterable):
    return reduce(lambda acc, x: acc and bool(pred(x)), iterable, True)


def exists(pred, iterable):
    return reduce(lambda acc, x: acc or bool(pred(x)), iterable, False)


def atleast(n, pred, iterable):
    return reduce(lambda acc, x: acc + bool(pred(x)), iterable, 0) >= n


def atmost(n, pred, iterable):
    return reduce(lambda acc, x: acc + bool(pred(x)), iterable, 0) <= n


if __name__ == "__main__":
    nums = [1, 2, 3, 4, 5]

    print("forall(>0):", forall(lambda x: x > 0, nums))       # True
    print("forall(>3):", forall(lambda x: x > 3, nums))       # False
    print("exists(>4):", exists(lambda x: x > 4, nums))       # True
    print("exists(>9):", exists(lambda x: x > 9, nums))       # False
    print("atleast(3, >2):", atleast(3, lambda x: x > 2, nums))  # True  (3,4,5)
    print("atleast(4, >2):", atleast(4, lambda x: x > 2, nums))  # False
    print("atmost(2, >3):", atmost(2, lambda x: x > 3, nums))    # True  (4,5)
    print("atmost(1, >3):", atmost(1, lambda x: x > 3, nums))    # False