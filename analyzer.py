import re
import ast

def analyze_code(code: str, language: str) -> dict:
    issues = []
    lines  = code.split('\n')

    # ── Syntax Check (Python only) ──
    syntax_error = None
    if language == 'python':
        try:
            ast.parse(code)
        except SyntaxError as e:
            syntax_error = e
            issues.append({
                'id': 'issue-syntax',
                'line': e.lineno or 1,
                'title': f'Syntax Error: {e.msg}',
                'severity': 'critical',
                'category': 'Bug',
                'description': f'Line {e.lineno}: {e.msg}. Code will not run until this is fixed.',
                'code': (lines[e.lineno - 1].strip() if e.lineno and e.lineno <= len(lines) else ''),
            })

    # ── Security Patterns ──
    security_patterns = [
        (r'password\s*=\s*["\'][^"\']+["\']',  'Hardcoded Password',  'critical', 'Security', 'Never hardcode passwords. Use environment variables (.env file).'),
        (r'api_key\s*=\s*["\'][^"\']+["\']',   'Hardcoded API Key',   'critical', 'Security', 'API keys must not be in code. Store in .env file.'),
        (r'secret\s*=\s*["\'][^"\']+["\']',    'Hardcoded Secret',    'critical', 'Security', 'Never hardcode secrets in source code.'),
        (r'SELECT.*\+.*',                       'SQL Injection Risk',  'critical', 'Security', 'Do not build SQL with string concatenation. Use parameterized queries.'),
    ]

    # ── Bug Patterns ──
    bug_patterns = [
        (r'except\s*:',                'Bare Except Clause',      'warning', 'Bug',   'Use "except Exception as e:" instead of bare "except:"'),
        (r'==\s*None',                 'Wrong None Comparison',   'warning', 'Bug',   'Use "is None" instead of "== None"'),
        (r'==\s*True|==\s*False',      'Wrong Boolean Comparison','warning', 'Bug',   'Use "if x:" instead of "if x == True:"'),
        (r'print\(',                   'Debug Print Statement',   'info',    'Style', 'Use logging module instead of print() in production code.'),
    ]

    all_patterns = security_patterns + bug_patterns

    if not syntax_error:
        # Only run pattern checks if syntax is valid
        for line_num, line in enumerate(lines, 1):
            for pattern, title, severity, category, description in all_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        'id': f'issue-{len(issues)+1}',
                        'line': line_num,
                        'title': title,
                        'severity': severity,
                        'category': category,
                        'description': description,
                        'code': line.strip(),
                    })

        # ── Duplicate Imports ──
        imports_seen = []
        for line_num, line in enumerate(lines, 1):
            match = re.match(r'^import\s+(\w+)', line.strip())
            if match:
                module = match.group(1)
                if module in imports_seen:
                    issues.append({
                        'id': f'issue-{len(issues)+1}',
                        'line': line_num,
                        'title': f'Duplicate Import: {module}',
                        'severity': 'warning',
                        'category': 'Style',
                        'description': f'"{module}" is imported twice. Remove the duplicate.',
                        'code': line.strip(),
                    })
                else:
                    imports_seen.append(module)

    # ── Score Calculation ──
    critical = sum(1 for i in issues if i['severity'] == 'critical')
    warnings = sum(1 for i in issues if i['severity'] == 'warning')

    # Syntax error = very low score
    if syntax_error:
        score = 10
    else:
        score = max(0, 100 - (critical * 20) - (warnings * 5))

    return {
        'issues':       issues,
        'score':        score,
        'syntax_error': syntax_error is not None,
        'stats': {
            'total':    len(issues),
            'critical': critical,
            'warnings': warnings,
            'info':     sum(1 for i in issues if i['severity'] == 'info'),
            'lines':    len(lines),
        }
    }
