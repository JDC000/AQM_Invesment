import os

# Ignorierte Ordner und Dateien
EXCLUDE_DIRS = {".git", "__pycache__", ".idea", ".venv", ".mypy_cache", ".pytest_cache", "env", "venv"}
EXCLUDE_FILES = {".DS_Store", ".gitignore", "AQM_Struktur.docx", "__init__.py", "Strukturdiagramm.py"}

def print_tree(startpath, prefix=""):
    items = sorted([
        item for item in os.listdir(startpath)
        if item not in EXCLUDE_FILES and not item.endswith(".pyc")
    ])
    items = [item for item in items if not any(item.startswith(ex) for ex in EXCLUDE_DIRS)]

    for index, item in enumerate(items):
        path = os.path.join(startpath, item)
        is_last = index == len(items) - 1
        connector = "└── " if is_last else "├── "
        print(prefix + connector + item)

        if os.path.isdir(path) and item not in EXCLUDE_DIRS:
            extension = "    " if is_last else "│   "
            print_tree(path, prefix + extension)

# Dein Projektordner (z. B. "." oder genauer Pfad)
project_path = "Backend"
print("Project/")
print_tree(project_path)
