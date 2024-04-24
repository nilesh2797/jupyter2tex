PROJECT = 'Results'
import os
from IPython.display import display
os.makedirs(PROJECT, exist_ok=True)

def display_table(df, name):
    display(df)
    df.to_latex(f'{PROJECT}/{name}.tex', index=False)

def parse_function_call(call_string):
    # Split the call string by '(' and ')'
    func_and_args = call_string.split('(', 1)
    func_name = func_and_args[0].strip()
    args_string = func_and_args[1].rsplit(')', 1)[0]  # Remove trailing ')'

    # Split the arguments string by ','
    args_list = args_string.split(',')

    # Initialize lists to store positional and keyword arguments
    pos_args = []
    kw_args = {}

    # Iterate over arguments and separate positional and keyword arguments
    for arg in args_list:
        arg = arg.strip()
        if '=' in arg:
            key, value = arg.split('=')
            kw_args[key.strip()] = value.strip()
        else:
            pos_args.append(arg)

    return func_name, pos_args, kw_args

x = 'display_table(df, center=True, caption=\"the land of the free\")'
parsed_func_call = parse_function_call(x)