from jupyter_notebook_parser import JupyterNotebookParser
import re, os

PROJECT = 'Results'
import os
from IPython.display import display
os.makedirs(PROJECT, exist_ok=True)

def display_table(df, name, centering=True, caption="", label=None):
    display(df)
    print(*[
        f'\\begin{{table}}[h]',
        f'\\centering' if centering else '',
        df.to_latex(index=False),
        f'\\caption{{{caption}}}',
        f'\\label{{{label}}}' if label is not None else '',
        f'\\end{{table}}'
    ],
    file=open(f'{PROJECT}/{name}.tex', 'w'),
    sep='\n'
    )

import matplotlib.pyplot as plt
def display_figure(plt_fig, name, centering=True, width=0.5, caption=""):
    plt.show()
    fname = f'{PROJECT}/{name}.pdf'
    plt_fig.savefig(fname, bbox_inches='tight')
    print(*[
        f'\\begin{{figure}}[h]',
        f'\\centering' if centering else '',
        f'\\includegraphics[width={width}\\textwidth]{{{fname}}}',
        f'\\caption{{{caption}}}',
        f'\\end{{figure}}'
    ],
    file=open(fname.replace('.pdf', '.tex'), 'w'),
    sep='\n'
    )

def setup(title="Title", authors=[], abstract=""):
    title = "\\title{" + title + "}"
    authors = '\\author{' + '\\and '.join(authors) + '}'
    bd = '\\begin{document} \maketitle'
    abstract = "\\begin{abstract}" + abstract + "\\end{abstract}"

    s = title + "\n" + authors + "\n" + bd + "\n" + abstract
    f = open(f'{PROJECT}/setup.txt', 'w')
    f.write(s)
    f.close()
################################################################################
    
import ast
class FunctionCallExtractor(ast.NodeVisitor):
    def __init__(self):
        self.function_calls = []

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = ast.unparse(node.func)
        else:
            func_name = "unknown_function"

        args = [ast.unparse(arg) for arg in node.args]
        kwargs = {kw.arg: ast.unparse(kw.value) for kw in node.keywords}
        self.function_calls.append((func_name, args, kwargs))
        self.generic_visit(node)

def extract_function_calls(code):
    tree = ast.parse(code)
    extractor = FunctionCallExtractor()
    extractor.visit(tree)
    return extractor.function_calls

enum_i = []
item_i = []

def count_spaces(l):
    ret = 0
    first = 0
    for i in range(len(l)):
        if l[i] == ' ':
            ret += 1
        elif l[i] == '\t':
            ret += 4
        else:
            break
        first += 1
    return ret // 4, l[first:]

def enumerate(line):
    global enum_i
    pre = []
    level, l = count_spaces(line)
    if '.' in l:
        l_s = l.split('.')
        l_num = l_s[0]
        if l_num.isnumeric():
            l_rest = '.'.join(l_s[1:])
            if level == len(enum_i) or len(enum_i) == 0:
                if l_num == '1':
                    enum_i.append(1)
                    return ['\\begin{enumerate} \n' + f'\item[{enum_i[-1]}.]' + l_rest]
                else:
                    return [line]
            elif level <= len(enum_i):
                p = []
                for i in range(level, len(enum_i)-1):
                    p.append('\\end{enumerate}\n')
                enum_i = enum_i[:level+1]
                enum_i[-1] += 1
                return [''.join(p), f'\item[{enum_i[-1]}.]' + l_rest]
        else:
            for i in range(len(enum_i)):
                pre.append('\\end{enumerate}\n')
            enum_i = []

    elif len(enum_i) > 0:
        for i in range(len(enum_i)):
            pre.append('\\end{enumerate}\n')
        enum_i = []
    
    # ELSE
    return [''.join(pre), line]

def first_non_whitespace(s):
    for c in s:
        if not c.isspace():
            return c
    return -1 

def only_dashes(l):
    for c in l:
        if not (c.isspace() or c == '-'):
            return False        
    return True

item_depth = -1
def itemize(line):
    global item_depth
    ret = []
    if only_dashes(line) or first_non_whitespace(line) == -1 or first_non_whitespace(line) != '-':
        for i in range(item_depth + 1):
            ret.append("\\end{itemize} \n")
        ret.append(line)
        item_depth = -1
    else:
        level, l = count_spaces(line)
        if level == item_depth + 1:
            ret.append("\\begin{itemize}\n \\item " + l[1:] + "\n")
            item_depth += 1
        elif level == item_depth:
            ret.append("\\item " + l[1:] + "\n")
        else:
            for i in range(item_depth - level):
                ret.append("\\end{itemize} \n")
            ret.append("\\item " + l[1:] + "\n")
            item_depth = level
    return ret

def process_hlines(line):
    lines = line.split("\n")
    for i in range(len(lines)):
        line = lines[i]
        count = 0
        for c in line:
            if c == '-':
                count += 1
            if not (c.isspace() or c == '-'):
                break
        if count >= 3:
            lines[i] = "\n\\noindent\\rule{\\textwidth}{1pt}"
    return ''.join(lines)

def markdown_to_latex_link(markdown_link):
    match = re.match(r'\[([^\]]+)\]\((.*?)\)', markdown_link)
    if match:
        link_text = match.group(1)
        url = match.group(2)
        latex_link = f'\\href{{{url}}}{{{link_text}}}'
        return latex_link
    else:
        return None

def preprocess(line):
    # replace any *_* with *\_*
    line = line.replace('_','\_')
    line = re.sub(r'\[([^\]]+)\]\((.*?)\)', lambda match: markdown_to_latex_link(match.group(0)), line)
    # replace anything within ** with \textbf{...}
    # BOLD AND ITALIC
    line = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', line)
    line = re.sub(r'\*(.*?)\*', r'\\textit{\1}', line)
    # ENUMERATE
    ret = enumerate(line)

    # ITEMIZE
    other_ret = itemize(ret[-1])

    line = ''.join(ret[:-1]) + ''.join(other_ret)
    # HLINES
    line = process_hlines(line)
    # DONE
    return line

def split_on_dollar_signs(text):
    pattern = r'(\${1,2}.*?\${1,2})'
    parts = re.split(pattern, text)
    return [part for part in parts if part.strip()]

def split_on_verbatim_signs(text):
    pattern = r'(\`{1,3}.*?\`{1,3})'
    parts = re.split(pattern, text)
    return [part for part in parts if part.strip()]

def is_part_of_special_block(line, began_math, began_verbatim):
    return line.startswith('```') or line.startswith('$') or line.startswith('$$') or line.startswith('```') or began_math or began_verbatim

def markdown_to_latex(cells):
    latex_lines = ['\\documentclass{article}\n\\usepackage{graphicx}\n\\usepackage{hyperref}\n\\usepackage{booktabs}\n\\usepackage{amsmath}\n\\usepackage{amssymb}\n\\usepackage{mathtools}\n\\usepackage{listings}\n\\usepackage[letterpaper, portrait, margin=1in]{geometry}']
    try:
        f = open(f"{PROJECT}/setup.txt")
        lines = f.readlines()
        f.close()
    except FileNotFoundError:
        lines = ''
    print("LINES", lines)
    for line in lines:
        latex_lines.append(line)
    for cell in cells:
        if cell[0] == 'markdown':
            lines = cell[1]
            began_verbatim = False; began_math = False
            lines = [y for x in lines for y in split_on_dollar_signs(x)]
            lines = [y for x in lines for y in split_on_verbatim_signs(x)]
            for line in lines:
                if not is_part_of_special_block(line, began_math, began_verbatim):
                    line = preprocess(line)
                # Convert headers
                if line.strip().startswith('# '):
                    latex_lines.append('\\section{' + line[2:] + '}')
                elif line.strip().startswith('## '):
                    latex_lines.append('\\subsection{' + line[3:] + '}')
                elif line.strip().startswith('### '):
                    latex_lines.append('\\subsubsection{' + line[4:] + '}')
                # Convert code blocks
                elif line == '```':
                    if latex_lines and began_verbatim:
                        latex_lines.append('\\end{verbatim}')
                        began_verbatim = False
                    else:
                        latex_lines.append('\\begin{verbatim}')
                        began_verbatim = True
                # Inline code
                elif line[0] == '`' and line[-1] == '`':
                    latex_lines.append('\\texttt{' + line.replace('`', '') + '}')
                # Math blocks
                elif line == '$' or line == '$$':
                    began_math = not began_math
                else:
                    latex_lines.append(line.strip())
        else:
            lines = cell[1]
            if lines[0].startswith('''#%capture code'''):
                lines = lines[1:]
                latex_lines.append("\\begin{lstlisting}[language=Python]")
                for l in lines:
                    latex_lines.append(l.strip())
                latex_lines.append("\\end{lstlisting}")
            else:
                fn_calls = extract_function_calls('\n'.join(lines))
                if fn_calls is not None and len(fn_calls) > 0:
                    for fn_name, args, kwargs in fn_calls:
                        if fn_name == 'display_table':
                            name = args[1] if len(args) > 1 else kwargs.get('name')
                            name = name.replace("'", "").replace('"', '')
                            fname = f'{PROJECT}/{name}.tex'
                            if os.path.exists(fname):
                                latex_lines.append(f'\\input{{{fname}}}')
                        elif fn_name == 'display_figure':
                            name = args[1] if len(args) > 1 else kwargs.get('name')
                            name = name.replace("'", "").replace('"', '')
                            fname = f'{PROJECT}/{name}.tex'
                            if os.path.exists(fname):
                                latex_lines.append(f'\\input{{{fname}}}')

    for i in range(item_depth):
        latex_lines.append("\\end{itemize}")
    for i in range(len(enum_i)):
        latex_lines.append("\\end{enumerate}")
    latex_lines.append('\\end{document}')
    return latex_lines