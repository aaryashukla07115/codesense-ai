# CodeSense AI

An AI-powered code review web app that finds bugs, security risks and code smells, scores code quality, and suggests fixes with AI explanations.

**Live demo:** https://codesense-ai-gywrjw6ewkzp65agpkab7v.streamlit.app

## Features

- **Bug and security detection:** finds common errors, hardcoded passwords and API keys, and SQL injection patterns
- **Complexity analysis:** cyclomatic complexity for each function with A–F grades (Python, using the AST module)
- **Code smell detection:** long methods, long parameter lists, god classes, magic numbers and dead code
- **Quality score:** rated across correctness, security, performance, maintainability and readability
- **AI assistance:** AI-generated fixes and answers to questions about your code, using the Anthropic Claude and Google Gemini APIs
- **User accounts:** signup and login with hashed passwords (SQLite)
- **History and stats:** review history, plus downloadable fixed code
- **Languages:** Python, JavaScript, TypeScript, Java, C++ and Go (deepest analysis for Python)

## Tech Stack

Python, Streamlit, Anthropic Claude API, Google Gemini API, SQLite, AST

## Project Structure

| File | Purpose |
|---|---|
| `app.py` | Streamlit app and user interface |
| `analyzer.py` | Bug and security checks |
| `complexity.py` | Cyclomatic complexity calculation |
| `smells.py` | Code smell detection |
| `report.py` | Quality score and report generation |
| `ai_explain.py` | AI explanations (Gemini) |
| `auth.py` | Signup and login (SQLite) |

## Run Locally

```bash
git clone https://github.com/aaryashukla07115/codesense-ai.git
cd codesense-ai
pip install -r requirements.txt
```

Create a `.env` file in the project folder:

```
ANTHROPIC_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

Start the app:

```bash
streamlit run app.py
```

When deployed on Streamlit Cloud, add the same two keys under **Secrets**.

## Author

**Aarya Shukla**, final-year B.E. Computer Science Engineering student
GitHub: [aaryashukla07115](https://github.com/aaryashukla07115)
LinkedIn: [aarya-shuklacse](https://www.linkedin.com/in/aarya-shuklacse)
