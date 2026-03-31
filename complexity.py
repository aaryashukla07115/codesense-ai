import ast

def calculate_complexity(code: str) -> list:
    results = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexity = 1
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With, ast.Assert)):
                    complexity += 1
                elif isinstance(child, ast.BoolOp):
                    complexity += len(child.values) - 1

            lines = 0
            if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                lines = node.end_lineno - node.lineno + 1

            if complexity <= 5:     grade = 'A'
            elif complexity <= 10:  grade = 'B'
            elif complexity <= 15:  grade = 'C'
            elif complexity <= 20:  grade = 'D'
            else:                   grade = 'F'

            results.append({
                'name': node.name,
                'cyclomatic': complexity,
                'lines': lines,
                'grade': grade,
                'line_start': node.lineno,
            })
    return results
