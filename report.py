from datetime import datetime

def generate_report(analysis: dict, complexity: list, smells: list, language: str) -> dict:
    score  = analysis.get('score', 0)
    stats  = analysis.get('stats', {})
    issues = analysis.get('issues', [])

    security_issues = [i for i in issues if i.get('category') == 'Security']
    bug_issues      = [i for i in issues if i.get('category') == 'Bug']

    dimension_scores = {
        'correctness':     max(0, 100 - len(bug_issues) * 15),
        'security':        max(0, 100 - len(security_issues) * 25),
        'performance':     max(0, 100 - len([s for s in smells if s['impact'] == 'High']) * 10),
        'maintainability': max(0, 100 - len(smells) * 8),
        'readability':     max(0, 100 - stats.get('warnings', 0) * 5),
    }

    recommendations = []
    if security_issues:
        recommendations.append("🔐 Hardcoded credentials hata do — .env file use karo")
    if bug_issues:
        recommendations.append("🐛 Bare except clauses fix karo — specific exceptions pakdo")
    if any(s['type'] == 'Long Method' for s in smells):
        recommendations.append("✂️ Bade functions tod do — ek function ek kaam kare")
    if any(s['type'] == 'God Class' for s in smells):
        recommendations.append("🏗️ God class ko chhoti classes mein divide karo")
    if len(recommendations) < 3:
        recommendations.append("📝 Docstrings add karo har function mein")
        recommendations.append("🧪 Unit tests likho apne functions ke liye")

    avg_complexity = round(sum(c['cyclomatic'] for c in complexity) / len(complexity), 1) if complexity else 0

    return {
        'score': score,
        'language': language,
        'timestamp': datetime.now().strftime('%d %b %Y, %I:%M %p'),
        'stats': stats,
        'dimension_scores': dimension_scores,
        'recommendations': recommendations,
        'avg_complexity': avg_complexity,
        'total_functions': len(complexity),
        'total_smells': len(smells),
    }
