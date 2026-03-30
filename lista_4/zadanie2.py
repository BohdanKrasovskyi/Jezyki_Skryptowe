import os
import sys

def get_path_directories():
    path_var = os.environ.get('PATH', '')
    return [directory for directory in path_var.split(os.pathsep) if directory]

def is_executable(file_path):
    if not os.path.isfile(file_path):
        return False

    if os.name == 'nt':
        return file_path.lower().endswith(('.exe', '.bat', '.cmd'))
    elif os.name == 'posix':
        return os.access(file_path, os.X_OK)
    else:
        print(f"Unknown operating system: {os.name}")
        return False

def print_directories():
    dirs = get_path_directories()
    for d in dirs:
        print(d)

def print_executables():
    dirs = get_path_directories()
    for d in dirs:
        print(f"\nDirectory: {d}")
        try:
            items = os.listdir(d)
            executables = []
            for item in items:
                full_path = os.path.join(d, item)
                if is_executable(full_path):
                    executables.append(item)
            if executables:
                for exe in executables:
                    print(f" - {exe}")
            else:
                print("No executables files found")

        except FileNotFoundError:
            print("Error: Directory not found!")
        except PermissionError:
            print("Error: Permission denied!")
        except Exception as e:
            print(f" Error reading directory: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python zadanie2.py [dirs|exec]")
        print("  dirs : Print all directories in PATH")
        print("  exec : Print directories and their executable files")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'dirs':
        print_directories()
    elif command == 'exec':
        print_executables()
    else:
        print(f"Unknown command: '{command}'. Use 'dirs' or 'exec'.")


if __name__ == "__main__":
    main()