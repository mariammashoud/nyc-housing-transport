"""Execute Members 1-3 in dependency order, preserving outputs in each notebook."""
from copy import deepcopy
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"


def execute(name, preparation_only=False):
    path = NOTEBOOKS / name
    notebook = nbformat.read(path, as_version=4)
    work = deepcopy(notebook)
    if preparation_only:
        end = next(i for i, c in enumerate(work.cells)
                   if c.cell_type == "markdown" and c.source.startswith("## 7."))
        work.cells = work.cells[:end]
    print(f"Executing {name}" + (" (preparation only)" if preparation_only else ""), flush=True)
    client = NotebookClient(
        work, timeout=900, kernel_name="python3",
        resources={"metadata": {"path": str(ROOT)}},
    )
    try:
        client.execute()
    except CellExecutionError:
        if not preparation_only:
            nbformat.write(work, path)
        raise
    if preparation_only:
        notebook.cells[:len(work.cells)] = work.cells
        nbformat.write(notebook, path)
    else:
        nbformat.write(work, path)
    plots = sum("image/png" in output.get("data", {})
                for cell in work.cells if cell.cell_type == "code"
                for output in cell.get("outputs", []))
    print(f"Saved {name}: {plots} rendered figures", flush=True)


if __name__ == "__main__":
    execute("Member2_Transportation_SIRTA.ipynb", preparation_only=True)
    execute("Member1_Housing.ipynb")
    execute("Member3_Integration.ipynb")
    execute("Member2_Transportation_SIRTA.ipynb")
