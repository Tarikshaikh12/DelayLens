"""Validate notebook format and compile every Python cell without executing it."""
import ast
from pathlib import Path
import nbformat

root = Path(__file__).resolve().parents[1]
for path in sorted((root/"notebooks").glob("*.ipynb")):
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type == "code":
            ast.parse(cell.source, filename=f"{path.name}:cell-{index}")
    print(f"Valid: {path.name}")
