from jupyter_notebook_parser import JupyterNotebookParser
import re, os

parsed = JupyterNotebookParser('sample2.ipynb')
all_cells = parsed.get_all_cells()
all_cells_simplified = []
for x in all_cells:
    type = x['cell_type']
    source = [c for c in x['source']]
    all_cells_simplified.append((type, source))
all_markdown_lines = [y for x in parsed.get_markdown_cell_sources() for y in x.split('\n')]
print(all_markdown_lines)
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
    print("BEFORE ENUMERATE", line)
    ret = enumerate(line)
    print("OUT OF ENUMERATE", ret)

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
    latex_lines = ['\\documentclass{article}\n\\usepackage{graphicx}\n\\usepackage{hyperref}\n\\begin{document}']
    for cell in cells:
        print(cell)
        if cell[0] == 'markdown':
            lines = cell[1]
            began_verbatim = False; began_math = False
            lines = [y for x in lines for y in split_on_dollar_signs(x)]
            lines = [y for x in lines for y in split_on_verbatim_signs(x)]
            for line in lines:
                print("OH NO", line)
                if not is_part_of_special_block(line, began_math, began_verbatim):
                    line = preprocess(line)
                print(line)
                print()
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
                    latex_lines.append(line)
        else:
            lines = cell[1]
            latex_lines.append("\\begin{verbatim}")
            for l in lines:
                latex_lines.append(l)
            latex_lines.append("\\end{verbatim}")
    for i in range(item_depth):
        latex_lines.append("\\end{itemize}")
    for i in range(len(enum_i)):
        latex_lines.append("\\end{enumerate}")
    latex_lines.append('\\end{document}')   
    return latex_lines

# RUN ON SAMPLE
latex_lines = markdown_to_latex(all_cells_simplified)
print(*latex_lines, sep='\n', file=open('latex.tex', 'w'))
os.system('pdflatex latex.tex')