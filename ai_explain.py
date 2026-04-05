import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def get_client():
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        # Streamlit Cloud secrets
        try:
            import streamlit as st
            api_key = st.secrets.get("GEMINI_API_KEY", "")
        except:
            pass
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")

def explain_code(code: str, question: str, language: str) -> str:
    """AI se code ke baare mein question ka jawab leta hai"""
    try:
        model = get_client()
        prompt = f"""You are an expert {language} code reviewer.

Code:
```{language}
{code[:2000]}
```

Question: {question}

Give a clear, helpful answer. Use code examples where needed."""

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"
