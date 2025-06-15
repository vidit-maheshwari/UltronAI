import ast

files = ['file1.py', 'file2.py']  # List of Python files to check

for file in files:
    try:
        with open(file, 'r') as f:
            ast.parse(f.read())
        print(f'File {file} has correct syntax.\n')
    except SyntaxError as e:
        print(f'Syntax error in {file}:\n{e}\n')