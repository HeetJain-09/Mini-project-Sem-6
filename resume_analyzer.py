

import streamlit as st
import PyPDF2
import google.generativeai as genai
import time
from io import BytesIO

st.set_page_config(page_title="Resume Checker", page_icon="📄", layout="wide")

# Session state setup
if 'resume_text' not in st.session_state: st.session_state.resume_text = ""
if 'result' not in st.session_state: st.session_state.result = ""
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

# Simple CSS
st.markdown("""
<style>
.primary-btn {background-color: #4CAF50; color: white; border-radius: 8px;}
.result-box {padding: 20px; background: #e8f5e8; border-left: 5px solid #4CAF50; border-radius: 8px;}
</style>
""", unsafe_allow_html=True)

# Extract PDF text directly
def extract_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

# Get AI model
@st.cache_resource
def load_ai(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash')

# Safe AI call with retry
def get_ai_response(model, prompt):
    for i in range(3):
        try:
            return model.generate_content(prompt).text
        except:
            if i < 2: 
                time.sleep(2)
            else:
                return "❌ API error - check quota or key"
    return "❌ Try again later"

# Main title
st.title("🔍 AI Resume Matcher")
st.markdown("---")

# Sidebar API key
with st.sidebar:
    st.header("⚙️ Setup")
    api_key = st.text_input("Gemini API Key", type="password")
    if api_key:
        try:
            model = load_ai(api_key)
            st.success("✅ Ready!")
            st.session_state.model = model
        except:
            st.error("❌ Invalid key")

# Main sections
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📄 Upload Resume")
    pdf_file = st.file_uploader("Choose PDF", type="pdf")
    if pdf_file:
        st.session_state.resume_text = extract_pdf(pdf_file)
        st.success("✅ Extracted!")
        with st.expander("Preview (first 500 chars)"):
            st.text_area("", st.session_state.resume_text[:500])

with col2:
    st.subheader("💼 Job Details")
    job_title = st.text_input("Job Title", value="Data Analyst Intern")
    job_desc = st.text_area("Job Description", height=180)

# Analyze button
if st.button("🚀 ANALYZE RESUME", key="analyze", help="Click to check match"):
    model = st.session_state.get('model')
    if model and st.session_state.resume_text and job_desc:
        with st.spinner("AI analyzing..."):
            prompt = f"""
Job: {job_title}
Description: {job_desc[:700]}
Resume: {st.session_state.resume_text[:1400]}

Please give:
1. MATCH SCORE (0-100%):
2. ✅ STRENGTHS:
3. ❌ MISSING:
4. ➤ FIXES:
"""
            result = get_ai_response(model, prompt)
            st.session_state.result = result
            st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)
    else:
        st.error("⚠️ Need: API Key + PDF + Job Description")

# Simple chat tab
tab2, tab3 = st.tabs(["📊 Results", "💬 Chat"])

with tab2:
    if st.session_state.result:
        st.markdown("### 📊 Analysis Results")
        st.markdown(st.session_state.result)

with tab3:
    st.markdown("### 💬 Ask about your analysis")
    if st.session_state.result and st.session_state.get('model'):
        # Show chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["text"])
        
        # Chat input
        user_q = st.chat_input("Ask anything about the analysis...")
        if user_q:
            st.session_state.chat_history.append({"role": "user", "text": user_q})
            with st.chat_message("user"):
                st.write(user_q)
            
            model = st.session_state.model
            prompt = f"""Analysis: {st.session_state.result}
Resume: {st.session_state.resume_text[:600]}
Question: {user_q}"""
            
            with st.chat_message("assistant"):
                with st.spinner():
                    answer = get_ai_response(model, prompt)
                    st.write(answer)
                    st.session_state.chat_history.append({"role": "assistant", "text": answer})

