#a
from cmath import sqrt


def liczba(l):
    return 0 if not l else (l[0] if l[0] > 0 else 0) + liczba(l[1:])

#b
def median(l):
    l.sort()
    return 0 if not l else (l[len(l) // 2] if len(l) % 2 == 1 else (l[len(l) // 2] + l[len(l) // 2 - 1]) / 2)

#c
def pierwiastek(x, epsilon):
    if x < 0:
        print("ERROR: Cannot square the negative number!")
        return None

    def helper(y):
        return y if abs(y ** 2 - x) < epsilon else helper((y + x/y) / 2)
    return helper(1.0)

#d
def make_alpha_dict(text):
    result = {
        char : [word for word in text.split() if char in word]
        for char in set(text) if char.isalpha() #set unikalnych liter
    }
    return result

#e
def flatten(l):
    return (
    (flatten(l[0]) if isinstance(l[0], (list, tuple)) else [l[0]]) + flatten(l[1:])
    ) if l else []

#f
def group_anagrams(l):
    def get_canonical(word):
        return ''.join(sorted(word))

    unique_keys = set(get_canonical(w) for w in l)

    return {
        key : [w for w in l if get_canonical(w) == key]
        for key in unique_keys
    }



if __name__ == '__main__':
    print("=== a) ===")
    print(liczba([]))
    print(liczba([1, 0, 5]))
    print(liczba([-3, -1.2, 1.5]))

    print("=== b) ===")
    print(median([1,1,19,2,3,4,4,5,1]))
    print(median([]))
    print(median([2,3,1,4]))

    print("=== c) ===")
    print(pierwiastek(3, 0.1))
    print(pierwiastek(10, 0.0001))
    print(pierwiastek(-1, 0.001))

    print("=== d) ===")
    print(make_alpha_dict("on i ona"))
    print(make_alpha_dict(""))
    print(make_alpha_dict("1 abc d"))

    print("=== e) ===")
    print(flatten([1, [2, 3], [[4, 5], 6]]))
    print(flatten([[[]], []]))
    print(flatten(['a']))

    print("=== f) ===")
    print(group_anagrams(["kot", "tok", "pies", "kep", "pek"]))
    print(group_anagrams([]))
    print(group_anagrams(["1!23.", "3.1!2"]))