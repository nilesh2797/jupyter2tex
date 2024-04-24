from jupyter_notebook_parser import JupyterNotebookParser
import re, os
from jupyter2tex import markdown_to_latex

parsed = JupyterNotebookParser('report.ipynb')
all_cells = parsed.get_all_cells()
all_cells_simplified = []
for x in all_cells:
    type = x['cell_type']
    source = [c for c in x['source']]
    all_cells_simplified.append((type, source))

all_markdown_lines = [y for x in parsed.get_markdown_cell_sources() for y in x.split('\n')]
latex_lines = markdown_to_latex(all_cells_simplified)
print(*latex_lines, sep='\n', file=open('latex.tex', 'w'))
os.system('pdflatex latex.tex')