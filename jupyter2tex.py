from jupyter_notebook_parser import JupyterNotebookParser
import re, os

parsed = JupyterNotebookParser('sample.ipynb')
all_markdown_lines = [y for x in parsed.get_markdown_cell_sources() for y in x.split('\n')]
enum_i = []

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
                    return '\\begin{enumerate} \n' + f'\item[{enum_i[-1]}.]' + l_rest
                else:
                    return line
            elif level <= len(enum_i):
                p = []
                for i in range(level, len(enum_i)-1):
                    p.append('\\end{enumerate}\n')
                enum_i = enum_i[:level+1]
                enum_i[-1] += 1
                return ''.join(p) + f'\item[{enum_i[-1]}.]' + l_rest
        else:
            for i in range(len(enum_i)):
                pre.append('\\end{enumerate}\n')
            enum_i = []

    elif len(enum_i) > 0:
        for i in range(len(enum_i)):
            pre.append('\\end{enumerate}\n')
        enum_i = []
    
    # ELSE
    return ''.join(pre) + line

def preprocess(line):
    # replace any *_* with *\_*
    line = line.replace('_','\_')
    # replace anything within ** with \textbf{...}
    # BOLD AND ITALIC
    line = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', line)
    line = re.sub(r'\*(.*?)\*', r'\\textit{\1}', line)

    # ENUMERATE
    line = enumerate(line)

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

def markdown_to_latex(lines):
    latex_lines = ['\\documentclass{article}\n\\usepackage{graphicx}\n\\begin{document}']
    began_verbatim = False; began_math = False
    lines = [y.strip() for x in lines for y in split_on_dollar_signs(x)]
    lines = [y.strip() for x in lines for y in split_on_verbatim_signs(x)]
    for line in lines:
        if not is_part_of_special_block(line, began_math, began_verbatim):
            line = preprocess(line)

        # Convert headers
        if line.startswith('# '):
            latex_lines.append('\\section{' + line[2:] + '}')
        elif line.startswith('## '):
            latex_lines.append('\\subsection{' + line[3:] + '}')
        elif line.startswith('### '):
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
    latex_lines.append('\\end{document}')
    return latex_lines

# RUN ON SAMPLE
latex_lines = markdown_to_latex(all_markdown_lines)
print(*latex_lines, sep='\n', file=open('latex.tex', 'w'))
os.system('pdflatex latex.tex')