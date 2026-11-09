"""Execute Members 1-5 in dependency order, preserving outputs in each notebook."""
from copy import deepcopy
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"


def execute(name, preparation_only=False, research_only=False):
    if preparation_only and research_only:
        raise ValueError("Choose either preparation-only or research-only execution, not both.")
    path = NOTEBOOKS / name
    notebook = nbformat.read(path, as_version=4)
    work = deepcopy(notebook)
    indices = list(range(len(notebook.cells)))
    if preparation_only or research_only:
        boundary = next(i for i, c in enumerate(notebook.cells)
                        if c.cell_type == "markdown" and c.source.startswith("## 7."))
        indices = indices[:boundary] if preparation_only else indices[boundary:]
        work.cells = [work.cells[i] for i in indices]
    phase = " (preparation only)" if preparation_only else " (research only)" if research_only else ""
    print(f"Executing {name}{phase}", flush=True)
    client = NotebookClient(
        work, timeout=900, kernel_name="python3",
        resources={"metadata": {"path": str(ROOT)}},
    )
    try:
        client.execute()
    except CellExecutionError:
        if not preparation_only:
            for index, cell in zip(indices, work.cells):
                notebook.cells[index] = cell
            nbformat.write(notebook, path)
        raise
    for index, cell in zip(indices, work.cells):
        notebook.cells[index] = cell
    nbformat.write(notebook, path)
    plots = sum(any(kind in output.get("data", {})
                    for kind in ("image/png", "application/vnd.plotly.v1+json"))
                for cell in work.cells if cell.cell_type == "code"
                for output in cell.get("outputs", []))
    print(f"Saved {name}: {plots} rendered figures", flush=True)


if __name__ == "__main__":
    execute("Member2_Transportation_SIRTA.ipynb", preparation_only=True)
    execute("Member1_Housing.ipynb", preparation_only=True)
    execute("Member3_Integration.ipynb")
    execute("Member1_Housing.ipynb", research_only=True)
    execute("Member2_Transportation_SIRTA.ipynb")
    execute("Member4_Story_and_Final.ipynb")
    execute("Member5_Website_Research.ipynb")
