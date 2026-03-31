import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

def explain_code(code: str, question: str, language: str) -> str:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""You are an expert {language} developer and code reviewer.

The user has this {language} code:
```{language}
{code[:3000]}
```

User's question: {question}

Instructions:
- Give a clear, direct answer
- If there are bugs or errors, show the FIXED code with explanation
- Use code examples to explain
- Be specific — don't give vague answers
- If code has issues, always show corrected version"""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text
