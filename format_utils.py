PROJECT = 'Results'
import os
from IPython.display import display
os.makedirs(PROJECT, exist_ok=True)

def display_table(df, name):
    display(df)
    df.to_latex(f'{PROJECT}/{name}.tex', index=False)