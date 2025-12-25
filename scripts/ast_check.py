import ast
p = 'observability/metrics.py'
with open(p, 'r', encoding='utf-8') as f:
    s = f.read()
try:
    tree = ast.parse(s, p)
    # print try blocks and handlers
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            print(f"Try at line {node.lineno} has {len(node.handlers)} handlers and finalbody {len(node.finalbody)}")
    print('AST parse OK')
except SyntaxError as e:
    print('SyntaxError:', e)
