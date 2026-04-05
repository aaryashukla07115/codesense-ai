import streamlit as st
import os
import json
import anthropic
from datetime import datetime
from dotenv import load_dotenv
from auth import init_db, login, signup

load_dotenv()
init_db()

# Streamlit Cloud secrets support
try:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
except:
    pass

st.set_page_config(
    page_title="CodeSense AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Session State ──
defaults = {
    'logged_in': False, 'username': '', 'show_signup': False,
    'done': False, 'results': None, 'chat': [],
    'code': '', 'code_output': None,
    'theme': 'dark',
    'history': [], 'total_reviews': 0,
    'suggestion': '',
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

D       = st.session_state.theme == 'dark'
BG      = "#0a0b0f"  if D else "#f0f2f6"
SURFACE = "#111318"  if D else "#ffffff"
SRF2    = "#181b22"  if D else "#f8f9fa"
BORDER  = "#1e2230"  if D else "#dee2e6"
TEXT    = "#e2e8f0"  if D else "#212529"
TEXT2   = "#94a3b8"  if D else "#495057"
TEXT3   = "#475569"  if D else "#868e96"
SIDE    = "#111318"  if D else "#f8f9fa"
EDCLR   = "#181b22"  if D else "#ffffff"
EDTXT   = "#cdd6f4"  if D else "#212529"
ACC     = "#00e5ff"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@700;800&display=swap');
.stApp {{ background-color:{BG}; color:{TEXT}; }}
.main .block-container {{ padding-top:1.5rem; }}
section[data-testid="stSidebar"] {{ background-color:{SIDE}; border-right:1px solid {BORDER}; }}
section[data-testid="stSidebar"] label {{ color:{TEXT2} !important; }}
.stButton > button {{
    background:linear-gradient(135deg,#00e5ff,#00b8cc);
    color:#0a0b0f; font-weight:700; border:none;
    border-radius:8px; width:100%; transition:all 0.2s;
}}
.stButton > button:hover {{ box-shadow:0 6px 25px rgba(0,229,255,0.35); transform:translateY(-1px); }}
.stTextInput input {{
    background-color:{SRF2} !important; color:{TEXT} !important;
    border:1px solid {BORDER} !important; border-radius:8px !important;
}}
.stTextInput input:focus {{ border-color:#00e5ff !important; }}
.stTextArea textarea {{
    background-color:{EDCLR} !important; color:{EDTXT} !important;
    font-family:'JetBrains Mono',monospace !important;
    font-size:14px !important; border:1px solid {BORDER} !important;
    border-radius:8px !important;
}}
[data-testid="metric-container"] {{
    background:{SURFACE}; border:1px solid {BORDER}; border-radius:12px; padding:1rem;
}}
[data-testid="metric-container"] label {{ color:{TEXT2} !important; }}
[data-testid="metric-container"] [data-testid="stMetricValue"] {{ color:{TEXT} !important; }}
.stTabs [data-baseweb="tab-list"] {{ background-color:{SURFACE}; border-bottom:1px solid {BORDER}; }}
.stTabs [data-baseweb="tab"] {{ background-color:transparent; color:{TEXT2}; }}
.stTabs [aria-selected="true"] {{
    background-color:rgba(0,229,255,0.08) !important;
    color:#00e5ff !important; border-bottom:2px solid #00e5ff !important;
}}
.stSelectbox > div > div {{
    background-color:{SRF2} !important; color:{TEXT} !important;
    border:1px solid {BORDER} !important; border-radius:8px !important;
}}
.stExpander {{
    background-color:{SURFACE} !important;
    border:1px solid {BORDER} !important;
    border-radius:8px !important;
}}
footer {{ visibility:hidden; }}
</style>
""", unsafe_allow_html=True)

# ── Modules ──
try:
    from analyzer import analyze_code
    from complexity import calculate_complexity
    from smells import detect_smells
    from report import generate_report
    MODULES_OK = True
except ImportError as e:
    MODULES_OK = False
    MODULE_ERROR = str(e)

# ── Samples ──
BUGGY = """import os
import os

password = "admin123"
API_KEY = "sk-abc123"

def get_user(id):
    query = "SELECT * FROM users WHERE id=" + str(id)
    return query

def divide(a, b):
    return a / b

def unused_func():
    pass

try:
    x = divide(10, 0)
except:
    pass
"""

CLEAN = """from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)
MAX_DISCOUNT = 100

@dataclass
class Product:
    id: int
    name: str
    price: float

def calculate_discount(price: float, discount_pct: float) -> float:
    if price < 0:
        raise ValueError("Price must be non-negative")
    if not 0 <= discount_pct <= MAX_DISCOUNT:
        raise ValueError("Discount must be 0-100")
    return price * (1 - discount_pct / 100)
"""

# ════════════════════════════════════════
#  LOGIN PAGE
# ════════════════════════════════════════
if not st.session_state.logged_in:
    st.markdown(f"""
    <div style='text-align:center;padding:40px 0 20px 0'>
        <div style='font-size:52px'>⚡</div>
        <h1 style='font-family:Syne,sans-serif;font-size:42px;font-weight:800;
            background:linear-gradient(135deg,#00e5ff,#7c3aed);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0'>
            CodeSense AI</h1>
        <p style='color:{TEXT3};font-size:15px;margin-top:6px'>Intelligent Code Review System</p>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        if not st.session_state.show_signup:
            st.markdown(f"""<div style='background:{SURFACE};border:1px solid {BORDER};
                border-radius:16px;padding:24px;margin-bottom:12px'>
                <h3 style='color:{TEXT};font-family:Syne,sans-serif;
                    margin:0 0 16px 0;text-align:center'>🔐 Login</h3></div>""",
                unsafe_allow_html=True)
            u = st.text_input("👤 Username", key="login_u", placeholder="Enter username")
            p = st.text_input("🔑 Password", key="login_p", placeholder="Enter password", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 Login", use_container_width=True, key="login_btn"):
                if not u or not p:
                    st.error("⚠️ Fill both fields!")
                else:
                    r = login(u, p)
                    if r["success"]:
                        st.session_state.logged_in = True
                        st.session_state.username  = r["username"]
                        st.rerun()
                    else:
                        st.error(f"❌ {r['message']}")
            st.markdown(f"<div style='text-align:center;color:{TEXT3};font-size:13px;margin-top:12px'>No account?</div>", unsafe_allow_html=True)
            if st.button("✨ Create New Account", use_container_width=True, key="go_signup"):
                st.session_state.show_signup = True
                st.rerun()
        else:
            st.markdown(f"""<div style='background:{SURFACE};border:1px solid {BORDER};
                border-radius:16px;padding:24px;margin-bottom:12px'>
                <h3 style='color:{TEXT};font-family:Syne,sans-serif;
                    margin:0 0 16px 0;text-align:center'>✨ Create Account</h3></div>""",
                unsafe_allow_html=True)
            nu = st.text_input("👤 Username", key="su_u", placeholder="Min 3 characters")
            np = st.text_input("🔑 Password", key="su_p", placeholder="Min 6 characters", type="password")
            cp = st.text_input("🔑 Confirm", key="su_c", placeholder="Re-enter password", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🎉 Create Account", use_container_width=True, key="signup_btn"):
                if not nu or not np or not cp:
                    st.error("⚠️ Fill all fields!")
                elif np != cp:
                    st.error("❌ Passwords don't match!")
                else:
                    r = signup(nu, np)
                    if r["success"]:
                        st.success(f"✅ {r['message']}")
                        st.session_state.show_signup = False
                        st.rerun()
                    else:
                        st.error(f"❌ {r['message']}")
            st.markdown(f"<div style='text-align:center;color:{TEXT3};font-size:13px;margin-top:12px'>Already have account?</div>", unsafe_allow_html=True)
            if st.button("🔐 Back to Login", use_container_width=True, key="go_login"):
                st.session_state.show_signup = False
                st.rerun()
    st.stop()

# ════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════
with st.sidebar:

    st.markdown(f"""
    <div style='background:rgba(0,229,255,0.08);border:1px solid rgba(0,229,255,0.2);
                border-radius:10px;padding:12px 16px;margin-bottom:10px'>
        <div style='font-size:10px;color:{TEXT3};text-transform:uppercase;letter-spacing:1px'>Logged in as</div>
        <div style='font-size:17px;font-weight:700;color:#00e5ff'>👤 {st.session_state.username}</div>
    </div>""", unsafe_allow_html=True)

    if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.rerun()

    st.markdown("---")

    # Theme
    st.markdown(f"<p style='font-size:11px;font-weight:700;color:{TEXT3};text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>🎨 Theme</p>", unsafe_allow_html=True)
    tc1, tc2 = st.columns(2)
    with tc1:
        if st.button(f"🌙 Dark {'✓' if D else ''}", use_container_width=True, key="dark_btn"):
            st.session_state.theme = 'dark'; st.rerun()
    with tc2:
        if st.button(f"☀️ Light {'✓' if not D else ''}", use_container_width=True, key="light_btn"):
            st.session_state.theme = 'light'; st.rerun()

    st.markdown("---")

    # Language
    st.markdown(f"<p style='font-size:11px;font-weight:700;color:{TEXT3};text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>🌐 Language</p>", unsafe_allow_html=True)
    language = st.selectbox("lang", ["python","javascript","typescript","java","cpp","go"],
                             label_visibility="collapsed", key="lang_sel")

    st.markdown("---")

    # Load Sample
    st.markdown(f"<p style='font-size:11px;font-weight:700;color:{TEXT3};text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>📂 Load Sample</p>", unsafe_allow_html=True)
    samp = st.selectbox("samp", ["-- Choose --","🐛 Buggy Code","✨ Clean Code"],
                         label_visibility="collapsed", key="samp_sel")
    if samp != "-- Choose --" and st.button("Load ↓", use_container_width=True, key="load_samp"):
        st.session_state.code = BUGGY if "Buggy" in samp else CLEAN
        st.rerun()

    st.markdown("---")

    # Live Stats
    history = st.session_state.history
    total   = st.session_state.total_reviews
    avg_sc  = round(sum(h['score'] for h in history) / len(history), 1) if history else 0
    best_sc = max((h['score'] for h in history), default=0)

    st.markdown(f"<p style='font-size:11px;font-weight:700;color:{TEXT3};text-transform:uppercase;letter-spacing:1px;margin-bottom:8px'>📈 Live Stats</p>", unsafe_allow_html=True)

    s1, s2 = st.columns(2)
    with s1:
        st.markdown(f"""<div style='background:{SURFACE};border:1px solid {BORDER};
            border-radius:10px;padding:10px;text-align:center;margin-bottom:8px'>
            <div style='font-size:26px;font-weight:800;color:{ACC}'>{total}</div>
            <div style='font-size:10px;color:{TEXT3}'>Reviews</div>
        </div>""", unsafe_allow_html=True)
    with s2:
        avg_color = "#10b981" if avg_sc >= 70 else "#f59e0b" if avg_sc >= 50 else "#ef4444" if avg_sc > 0 else TEXT3
        st.markdown(f"""<div style='background:{SURFACE};border:1px solid {BORDER};
            border-radius:10px;padding:10px;text-align:center;margin-bottom:8px'>
            <div style='font-size:26px;font-weight:800;color:{avg_color}'>{avg_sc if avg_sc > 0 else "—"}</div>
            <div style='font-size:10px;color:{TEXT3}'>Avg Score</div>
        </div>""", unsafe_allow_html=True)

    best_color = "#10b981" if best_sc >= 80 else "#f59e0b" if best_sc >= 60 else "#ef4444" if best_sc > 0 else TEXT3
    st.markdown(f"""<div style='background:{SURFACE};border:1px solid {BORDER};
        border-radius:10px;padding:10px;
        display:flex;justify-content:space-between;align-items:center;margin-bottom:8px'>
        <span style='font-size:12px;color:{TEXT3}'>🏆 Best</span>
        <span style='font-size:18px;font-weight:800;color:{best_color}'>{best_sc}/100</span>
    </div>""", unsafe_allow_html=True)

    if st.session_state.done and st.session_state.results:
        last_sc    = st.session_state.results['report']['score']
        last_color = "#10b981" if last_sc >= 80 else "#f59e0b" if last_sc >= 60 else "#ef4444"
        st.markdown(f"""<div style='background:{SURFACE};border:1px solid {BORDER};
            border-radius:10px;padding:12px;text-align:center'>
            <div style='font-size:10px;color:{TEXT3};text-transform:uppercase;letter-spacing:1px'>Last Score</div>
            <div style='font-family:Syne,sans-serif;font-size:48px;font-weight:800;
                color:{last_color};line-height:1'>{last_sc}</div>
            <div style='font-size:11px;color:{TEXT3}'>/100</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    st.markdown(f"<p style='font-size:11px;font-weight:700;color:{TEXT3};text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>🕐 Recent Reviews</p>", unsafe_allow_html=True)
    if not history:
        st.markdown(f"<div style='font-size:12px;color:{TEXT3};text-align:center;padding:8px'>No reviews yet</div>", unsafe_allow_html=True)
    else:
        for i, h in enumerate(reversed(history[-5:])):
            icon = "🟢" if h['score'] >= 80 else "🟡" if h['score'] >= 60 else "🔴"
            if st.button(
                f"{icon} {h['lang'].upper()} · {h['score']}/100 · {h['time']}",
                use_container_width=True, key=f"sb_hist_{i}"
            ):
                st.session_state.code    = h['code']
                st.session_state.results = h['results']
                st.session_state.done    = True
                st.rerun()

    st.markdown("---")
    api_ok = os.getenv("ANTHROPIC_API_KEY", "")
    if api_ok and "yahan" not in api_ok:
        st.success("✅ API Key OK")
    else:
        st.error("❌ API Key missing!")

# ════════════════════════════════════════
#  HEADER
# ════════════════════════════════════════
st.markdown(f"""
<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:20px'>
    <div>
        <h1 style='font-family:Syne,sans-serif;font-size:30px;font-weight:800;
            background:linear-gradient(135deg,#00e5ff,#7c3aed);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0'>
            ⚡ CodeSense AI</h1>
        <p style='color:{TEXT3};font-size:13px;margin:0'>
            Bugs • Security • Complexity • Smells • AI Suggestions • Stats & History
        </p>
    </div>
    <div style='background:rgba(0,229,255,0.08);border:1px solid rgba(0,229,255,0.2);
                border-radius:20px;padding:6px 16px;font-size:13px;color:#00e5ff;font-weight:600'>
        👤 {st.session_state.username}
    </div>
</div>
""", unsafe_allow_html=True)

if not MODULES_OK:
    st.error(f"❌ Import Error: {MODULE_ERROR}")
    st.stop()

# ════════════════════════════════════════
#  TABS
# ════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📝 Editor",
    "🔍 Issues & AI Fix",
    "📊 Complexity",
    "🧪 Code Smells",
    "📈 Stats & History",
    "📋 Report",
])

# ── TAB 1: EDITOR ──
with tab1:
    st.markdown("### 📝 Code Editor")

    up = st.file_uploader("Upload file:", type=['py','js','ts','java','cpp','go'],
                           label_visibility="visible", key="uploader")
    if up:
        st.session_state.code = up.read().decode('utf-8')

    code_input = st.text_area("", value=st.session_state.code, height=380,
        placeholder="# Paste your code here...", key="code_area")
    if code_input:
        st.session_state.code = code_input
        ln = len(code_input.split('\n'))
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📄 Lines", ln)
        c2.metric("🔤 Chars", len(code_input))
        c3.metric("📝 Words", len(code_input.split()))
        c4.metric("🌐 Lang",  language.upper())

    st.markdown("---")
    b1, b2, b3 = st.columns([2, 2, 1])
    with b1:
        run_btn  = st.button("🔍 Run Full Review", type="primary", use_container_width=True, key="run_btn")
    with b2:
        exec_btn = st.button("▶️ Run Code", use_container_width=True, key="exec_btn")
    with b3:
        if st.button("🗑️ Clear", use_container_width=True, key="clear_btn"):
            st.session_state.code        = ""
            st.session_state.done        = False
            st.session_state.results     = None
            st.session_state.code_output = None
            st.session_state.suggestion  = ""
            st.rerun()

    if exec_btn:
        if not st.session_state.code.strip():
            st.warning("⚠️ Paste code first!")
        elif language != 'python':
            st.warning("⚠️ Only Python execution supported!")
        else:
            import subprocess, sys, tempfile
            with st.spinner("▶️ Running..."):
                try:
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
                        tmp.write(st.session_state.code)
                        tmp_path = tmp.name
                    res = subprocess.run([sys.executable, tmp_path],
                                         capture_output=True, text=True, timeout=10)
                    os.unlink(tmp_path)
                    st.session_state.code_output = {
                        'stdout': res.stdout, 'stderr': res.stderr, 'rc': res.returncode
                    }
                except subprocess.TimeoutExpired:
                    st.session_state.code_output = {'stdout':'','stderr':'⏱️ Timeout — 10s exceeded!','rc':-1}
                except Exception as e:
                    st.session_state.code_output = {'stdout':'','stderr':str(e),'rc':-1}

    if st.session_state.get('code_output'):
        out = st.session_state.code_output
        st.markdown("### ▶️ Output")
        if out['stdout']:
            st.markdown(f"""<div style='background:#0d1117;border-left:3px solid #00e5ff;
                border-radius:8px;padding:14px;font-family:JetBrains Mono,monospace;
                font-size:13px;color:#a6e3a1;white-space:pre-wrap'>
                {out['stdout'].replace('<','&lt;').replace('>','&gt;')}</div>""",
                unsafe_allow_html=True)
        if out['stderr']:
            st.markdown(f"""<div style='background:#0d1117;border-left:3px solid #ef4444;
                border-radius:8px;padding:14px;font-family:JetBrains Mono,monospace;
                font-size:13px;color:#f38ba8;white-space:pre-wrap'>
                {out['stderr'].replace('<','&lt;').replace('>','&gt;')}</div>""",
                unsafe_allow_html=True)
        if not out['stdout'] and not out['stderr']:
            st.info("✅ Code ran — no print output.")
        if out['rc'] == 0:
            st.success("✅ Code Run Successfully!")
        elif out['rc'] != -1:
            st.error(f"❌ Exit code: {out['rc']}")

    if run_btn:
        if not st.session_state.code.strip():
            st.warning("⚠️ Paste code first!")
        else:
            with st.spinner("🔍 Analyzing..."):
                prog = st.progress(0, "Running analysis...")
                analysis = analyze_code(st.session_state.code, language)
                prog.progress(35, "✓ Issues detected...")
                complexity, smells = [], []
                if language == 'python':
                    if not analysis.get('syntax_error'):
                        complexity = calculate_complexity(st.session_state.code)
                        prog.progress(60, "✓ Complexity done...")
                        smells = detect_smells(st.session_state.code)
                        prog.progress(80, "✓ Smells done...")
                report = generate_report(analysis, complexity, smells, language)
                prog.progress(100, "✅ Done!")
                results = {
                    'analysis': analysis, 'complexity': complexity,
                    'smells': smells, 'report': report,
                }
                st.session_state.results       = results
                st.session_state.done          = True
                st.session_state.suggestion    = ""
                st.session_state.total_reviews += 1
                st.session_state.history.append({
                    'score':   report['score'],
                    'lang':    language,
                    'time':    datetime.now().strftime("%d %b %H:%M"),
                    'issues':  analysis['stats']['total'],
                    'smells':  len(smells),
                    'code':    st.session_state.code,
                    'results': results,
                })
                if len(st.session_state.history) > 5:
                    st.session_state.history.pop(0)
                prog.empty()

            sc   = report['score']
            icon = "🟢" if sc >= 80 else "🟡" if sc >= 60 else "🔴"
            if analysis.get('syntax_error'):
                st.error(f"🔴 Syntax Error! Score: **{sc}/100** — Fix syntax error first!")
            else:
                st.success(f"{icon} Done! Score: **{sc}/100** | Issues: **{analysis['stats']['total']}** | Smells: **{len(smells)}**")
            st.info("👆 Check 'Issues & AI Fix' tab for details!")

# ── TAB 2: ISSUES & AI FIX ──
with tab2:
    if not st.session_state.done:
        st.info("⬅️ Editor mein code paste karo aur **Run Full Review** dabao.")
    else:
        issues  = st.session_state.results['analysis']['issues']
        stats   = st.session_state.results['analysis']['stats']
        is_synt = st.session_state.results['analysis'].get('syntax_error', False)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔴 Critical", stats.get('critical', 0))
        c2.metric("🟡 Warnings", stats.get('warnings', 0))
        c3.metric("🔵 Info",     stats.get('info', 0))
        c4.metric("📄 Lines",    stats.get('lines', 0))

        if is_synt:
            st.error("🚨 Syntax Error detected! Fix it first.")

        st.markdown("---")

        if not issues:
            st.success("✅ No issues found — excellent code!")
        else:
            filt  = st.selectbox("Filter:", ["All","critical","warning","info"], key="iss_filt")
            shown = issues if filt == "All" else [i for i in issues if i['severity'] == filt]
            SICONS = {'critical':'🔴','warning':'🟡','info':'🔵'}
            st.markdown(f"**{len(shown)} issue(s):**")
            for issue in shown:
                with st.expander(f"{SICONS.get(issue['severity'],'⚪')} **{issue['title']}** — Line {issue.get('line','?')} | {issue['category']}"):
                    st.markdown(f"**Problem:** {issue['description']}")
                    if issue.get('code'):
                        st.code(issue['code'], language=language)

        st.markdown("---")
        st.markdown("### 🤖 AI Code Suggestion")
        st.markdown("AI tumhara **poora code fix** karke corrected version suggest karega.")

        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key or "yahan" in api_key:
            st.error("❌ API Key missing.")
        else:
            if st.button("✨ Get AI Suggestion for Fixed Code", type="primary",
                         use_container_width=True, key="suggest_btn"):
                with st.spinner("🤖 AI is fixing your code..."):
                    try:
                        client_ai = anthropic.Anthropic(api_key=api_key)
                        issue_list = "\n".join([
                            f"- Line {iss.get('line','?')}: [{iss['severity'].upper()}] {iss['title']} — {iss['description']}"
                            for iss in issues
                        ]) if issues else "No specific issues detected."

                        prompt = f"""You are a senior {language} developer.

Issues found:
{issue_list}

ORIGINAL CODE:
```{language}
{st.session_state.code}
```

Fix ALL issues. Return EXACTLY:

FIXED_CODE:
```{language}
[complete fixed code]
```

CHANGES:
- [change 1]
- [change 2]"""

                        msg = client_ai.messages.create(
                            model="claude-opus-4-5",
                            max_tokens=3000,
                            messages=[{"role": "user", "content": prompt}]
                        )
                        response = msg.content[0].text
                        fixed_code, changes = "", ""
                        if "FIXED_CODE:" in response:
                            after = response.split("FIXED_CODE:")[1]
                            if "```" in after:
                                s = after.find("```")
                                s = after.find("\n", s) + 1
                                e = after.find("```", s)
                                fixed_code = after[s:e].strip()
                        if "CHANGES:" in response:
                            changes = response.split("CHANGES:")[1].strip()
                        st.session_state.suggestion         = fixed_code if fixed_code else response
                        st.session_state.suggestion_changes = changes
                    except Exception as e:
                        st.error(f"❌ AI Error: {str(e)}")

            if st.session_state.get('suggestion'):
                st.markdown("---")
                st.markdown("#### 📊 Before vs After")
                col_orig, col_fix = st.columns(2)
                with col_orig:
                    st.markdown("""<div style='background:rgba(239,68,68,0.1);border:1px solid #ef4444;
                        border-radius:8px;padding:8px 14px;margin-bottom:8px;
                        font-weight:700;color:#ef4444'>❌ Your Code</div>""", unsafe_allow_html=True)
                    st.code(st.session_state.code, language=language)
                with col_fix:
                    st.markdown("""<div style='background:rgba(16,185,129,0.1);border:1px solid #10b981;
                        border-radius:8px;padding:8px 14px;margin-bottom:8px;
                        font-weight:700;color:#10b981'>✅ AI Fixed</div>""", unsafe_allow_html=True)
                    st.code(st.session_state.suggestion, language=language)

                if st.session_state.get('suggestion_changes'):
                    st.markdown("#### 📝 Changes:")
                    for line in st.session_state.suggestion_changes.strip().split('\n'):
                        if line.strip():
                            st.markdown(f"""<div style='background:{SURFACE};border-left:3px solid #00e5ff;
                                border-radius:0 6px 6px 0;padding:8px 14px;margin-bottom:4px;
                                font-size:13px;color:{TEXT2}'>{line.strip()}</div>""",
                                unsafe_allow_html=True)

                st.markdown("---")
                ac1, ac2, ac3 = st.columns(3)
                with ac1:
                    if st.button("✅ Use in Editor", use_container_width=True, key="use_sug_btn"):
                        st.session_state.code       = st.session_state.suggestion
                        st.session_state.suggestion = ""
                        st.session_state.done       = False
                        st.success("✅ Loaded! Run Review again.")
                        st.rerun()
                with ac2:
                    st.download_button("📥 Download Fixed",
                        data=st.session_state.suggestion,
                        file_name=f"fixed.{'py' if language=='python' else language[:2]}",
                        mime="text/plain", use_container_width=True, key="dl_sug_btn")
                with ac3:
                    if st.button("🔄 Clear", use_container_width=True, key="clear_sug_btn"):
                        st.session_state.suggestion = ""
                        st.rerun()

# ── TAB 3: COMPLEXITY ──
with tab3:
    if not st.session_state.done:
        st.info("⬅️ Editor mein code paste karo aur **Run Full Review** dabao.")
    elif st.session_state.results['analysis'].get('syntax_error'):
        st.error("❌ Syntax error — pehle fix karo.")
    elif language != 'python':
        st.warning("⚠️ Complexity only for Python.")
    else:
        cx = st.session_state.results['complexity']
        if not cx:
            st.info("No functions found.")
        else:
            avg = sum(f['cyclomatic'] for f in cx) / len(cx)
            c1, c2, c3 = st.columns(3)
            c1.metric("📊 Functions", len(cx))
            c2.metric("📈 Avg CC",    f"{avg:.1f}")
            c3.metric("🔝 Max CC",    max(f['cyclomatic'] for f in cx))
            st.markdown("---")
            for fn in sorted(cx, key=lambda x: x['cyclomatic'], reverse=True):
                cc, gr = fn['cyclomatic'], fn['grade']
                with st.expander(f"**{fn['name']}()** — Grade: **{gr}** | CC: **{cc}** | Lines: {fn['lines']}"):
                    a, b, c = st.columns(3)
                    a.metric("Cyclomatic", cc)
                    b.metric("Lines", fn['lines'])
                    c.metric("Grade", gr)
                    if cc <= 5:    st.success("✅ Excellent!")
                    elif cc <= 10: st.info("🔵 Good.")
                    elif cc <= 15: st.warning("🟡 High — refactor.")
                    else:          st.error("🔴 Very High — break into smaller functions!")
                    st.progress(min(cc/20.0,1.0), text=f"Complexity: {cc}/20")

# ── TAB 4: CODE SMELLS ──
with tab4:
    if not st.session_state.done:
        st.info("⬅️ Editor mein code paste karo aur **Run Full Review** dabao.")
    elif st.session_state.results['analysis'].get('syntax_error'):
        st.error("❌ Syntax error — pehle fix karo.")
    elif language != 'python':
        st.warning("⚠️ Smell detection only for Python.")
    else:
        smells = st.session_state.results['smells']
        if not smells:
            st.success("✅ No code smells!")
        else:
            st.markdown(f"**{len(smells)} smell(s):**")
            SI = {'Long Method':'📏','God Class':'👑','Dead Code':'💀',
                  'Magic Number':'🔮','Long Parameter List':'📝'}
            for impact, ico in [('High','🔴'),('Medium','🟡'),('Low','🔵')]:
                grp = [s for s in smells if s['impact']==impact]
                if not grp: continue
                st.markdown(f"### {ico} {impact} ({len(grp)})")
                for s in grp:
                    with st.expander(f"{SI.get(s['type'],'🔍')} **{s['type']}** — {s['name']}"):
                        st.markdown(f"**Problem:** {s['description']}")
                        st.markdown(f"**Fix:** `{s['refactoring']}`")

# ── TAB 5: STATS & HISTORY ──
with tab5:
    st.markdown("### 📈 Review Stats & History")
    history = st.session_state.history
    total   = st.session_state.total_reviews

    avg_sc   = round(sum(h['score'] for h in history)/len(history),1) if history else 0
    best_sc  = max((h['score'] for h in history), default=0)
    tot_iss  = sum(h.get('issues',0) for h in history)
    tot_sml  = sum(h.get('smells',0) for h in history)

    m1,m2,m3,m4,m5 = st.columns(5)
    m1.metric("🔍 Reviews",     total)
    m2.metric("⭐ Avg Score",   avg_sc)
    m3.metric("🏆 Best",        f"{best_sc}/100")
    m4.metric("🐛 Issues",      tot_iss)
    m5.metric("🧪 Smells",      tot_sml)

    if avg_sc > 0:
        st.markdown("---")
        pc1, pc2 = st.columns([3,1])
        with pc1:
            st.progress(avg_sc/100, text=f"Avg Quality: {avg_sc}/100")
        with pc2:
            if avg_sc>=80:   st.success("🌟 Excellent!")
            elif avg_sc>=60: st.warning("📈 Improving!")
            else:            st.error("💪 Keep Going!")

    if len(history) >= 2:
        st.markdown("---")
        st.line_chart({"Review":[f"#{i+1}" for i in range(len(history))],
                       "Score":[h['score'] for h in history]},
                      x="Review", y="Score")

    st.markdown("---")
    if not history:
        st.markdown(f"""<div style='background:{SURFACE};border:1px solid {BORDER};
            border-radius:12px;padding:40px;text-align:center'>
            <div style='font-size:40px'>📭</div>
            <div style='font-size:16px;color:{TEXT2};margin-top:10px'>No reviews yet!</div>
        </div>""", unsafe_allow_html=True)
    else:
        for i, h in enumerate(reversed(history)):
            sc_icon = "🟢" if h['score']>=80 else "🟡" if h['score']>=60 else "🔴"
            with st.expander(f"{sc_icon} Review #{total-i} — {h['score']}/100 | {h['lang'].upper()} | {h['time']} | Issues:{h.get('issues',0)} Smells:{h.get('smells',0)}"):
                hc1,hc2,hc3,hc4 = st.columns(4)
                hc1.metric("Score",    f"{h['score']}/100")
                hc2.metric("Language", h['lang'].upper())
                hc3.metric("Issues",   h.get('issues',0))
                hc4.metric("Smells",   h.get('smells',0))
                if h.get('code'):
                    st.code(h['code'][:300]+("..." if len(h['code'])>300 else ""), language=h['lang'])
                lc1,lc2 = st.columns(2)
                with lc1:
                    if st.button("📂 Load Code", use_container_width=True, key=f"ld_code_{i}"):
                        st.session_state.code    = h['code']
                        st.session_state.results = h['results']
                        st.session_state.done    = True
                        st.rerun()
                with lc2:
                    if st.button("📊 Load Results", use_container_width=True, key=f"ld_res_{i}"):
                        st.session_state.results = h['results']
                        st.session_state.done    = True
                        st.rerun()

    if history:
        st.markdown("---")
        if st.button("🗑️ Clear History", use_container_width=True, key="clr_hist"):
            st.session_state.history       = []
            st.session_state.total_reviews = 0
            st.rerun()

# ── TAB 6: REPORT ──
with tab6:
    if not st.session_state.done:
        st.info("⬅️ Editor mein code paste karo aur **Run Full Review** dabao.")
    else:
        rpt  = st.session_state.results['report']
        anal = st.session_state.results['analysis']
        sml  = st.session_state.results['smells']
        cxp  = st.session_state.results['complexity']
        sc   = rpt['score']

        st.markdown(f"""
        <div style='background:linear-gradient(135deg,rgba(0,229,255,0.08),rgba(124,58,237,0.08));
                    border:1px solid {BORDER};border-radius:12px;padding:24px;margin-bottom:24px'>
            <div style='font-family:Syne,sans-serif;font-size:26px;font-weight:800;
                background:linear-gradient(135deg,#00e5ff,#7c3aed);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent'>
                📋 Code Quality Report</div>
            <div style='color:{TEXT3};font-size:13px;margin-top:4px'>
                {rpt['timestamp']} · {rpt['language'].upper()} · By: {st.session_state.username}
            </div>
        </div>""", unsafe_allow_html=True)

        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("⭐ Score",     f"{sc}/100")
        c2.metric("🔴 Critical",  anal['stats'].get('critical',0))
        c3.metric("🟡 Warnings",  anal['stats'].get('warnings',0))
        c4.metric("🧪 Smells",    len(sml))
        c5.metric("🔧 Functions", len(cxp))
        st.markdown("---")

        rd1, rd2 = st.columns(2)
        with rd1:
            st.markdown("### 📊 Dimension Scores")
            dims = rpt.get('dimension_scores',{})
            for dk,dl in [('correctness','🎯 Correctness'),('security','🔐 Security'),
                          ('performance','⚡ Performance'),('maintainability','🔧 Maintainability'),
                          ('readability','📖 Readability')]:
                dv = dims.get(dk,0)
                st.markdown(f"**{dl}** — {dv}/100")
                st.progress(dv/100)
        with rd2:
            st.markdown("### 💡 Recommendations")
            for ri, rec in enumerate(rpt.get('recommendations',[]),1):
                st.markdown(f"""<div style='background:{SURFACE};border:1px solid {BORDER};
                    border-radius:8px;padding:10px 14px;margin-bottom:8px;
                    font-size:13px;color:{TEXT2}'>
                    <strong style='color:#00e5ff'>{ri}.</strong> {rec}</div>""",
                    unsafe_allow_html=True)

        st.markdown("---")
        st.download_button("📥 Download Report (JSON)",
            data=json.dumps({'user':st.session_state.username,'report':rpt,
                'issues':anal['issues'],'complexity':cxp,'smells':sml},
                indent=2, default=str),
            file_name=f"codesense_{language}_report.json",
            mime="application/json", use_container_width=True, key="dl_report_btn")
