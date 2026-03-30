import os
import sys

def main():
    filters = [arg.lower() for arg in sys.argv[1:]]
    env_variables = os.environ
    results = {}

    for name, value in env_variables.items():
        if not filters:
            results[name] = value
        else:
            name_lower = name.lower()
            for f in filters:
                if f in name_lower:
                    results[name] = value
                    break

    sorted_names = sorted(results.keys())

    for name in sorted_names:
        print(f"{name}={results[name]}")

if __name__ == '__main__':
    main()