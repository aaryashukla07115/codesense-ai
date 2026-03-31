import ast
import re

def detect_smells(code: str) -> list:
    smells = []
    lines = code.split('\n')

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Long Method
            if hasattr(node, 'end_lineno'):
                fn_lines = node.end_lineno - node.lineno + 1
                if fn_lines > 20:
                    smells.append({
                        'type': 'Long Method',
                        'name': node.name,
                        'description': f'Function "{node.name}" mein {fn_lines} lines hain. 20 se zyada = too long. Chote functions mein tod do.',
                        'location': f'Line {node.lineno}',
                        'impact': 'High',
                        'refactoring': 'Extract Method',
                    })
            # Too Many Parameters
            params = len(node.args.args)
            if params > 5:
                smells.append({
                    'type': 'Long Parameter List',
                    'name': node.name,
                    'description': f'"{node.name}" mein {params} parameters hain. Dictionary ya dataclass use karo.',
                    'location': f'Line {node.lineno}',
                    'impact': 'Medium',
                    'refactoring': 'Introduce Parameter Object',
                })

        # God Class
        if isinstance(node, ast.ClassDef):
            methods = [n for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]
            if len(methods) > 10:
                smells.append({
                    'type': 'God Class',
                    'name': node.name,
                    'description': f'Class "{node.name}" mein {len(methods)} methods hain. Responsibilities divide karo.',
                    'location': f'Line {node.lineno}',
                    'impact': 'High',
                    'refactoring': 'Extract Class',
                })

    # Magic Numbers
    magic_count = 0
    for i, line in enumerate(lines, 1):
        if re.search(r'(?<!["\'\w])\b(?!0\b|1\b)\d{2,}\b', line) and not line.strip().startswith('#'):
            smells.append({
                'type': 'Magic Number',
                'name': f'Line {i}',
                'description': f'Hardcoded number: "{line.strip()}". Named constant banao.',
                'location': f'Line {i}',
                'impact': 'Low',
                'refactoring': 'Replace Magic Number with Constant',
            })
            magic_count += 1
            if magic_count >= 3:
                break

    # Dead Code
    defined_fns, called_fns = [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            defined_fns.append((node.name, node.lineno))
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_fns.append(node.func.id)

    for fn_name, fn_line in defined_fns:
        if fn_name not in called_fns and not fn_name.startswith('_') and fn_name != 'main':
            smells.append({
                'type': 'Dead Code',
                'name': fn_name,
                'description': f'Function "{fn_name}" define hua hai lekin kahi call nahi hota. Remove karo.',
                'location': f'Line {fn_line}',
                'impact': 'Low',
                'refactoring': 'Remove Dead Code',
            })
    return smells
