<<<<<<< HEAD

import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from docx import Document
import json
from dotenv import load_dotenv
from datetime import datetime

# --- Initialization ---
load_dotenv()

try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("Error: GOOGLE_API_KEY environment variable not found.")
    else:
        genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Failed to configure Gemini API: {e}")


# --- Functions ---
def get_gemini_response(input_text, json_schema):
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    try:
        response = model.generate_content(
            input_text,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": json_schema,
            }
        )
        return response.text
    except Exception as e:
        st.error(f"Error during API call: {e}")
        return None


def extract_pdf_text(file):
    reader = pdf.PdfReader(file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()
    return text


def extract_docx_text(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs])


# --- JSON Schema ---
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "JD Match": {"type": "string"},
        "Missing Keywords": {"type": "array", "items": {"type": "string"}},
        "Profile Summary": {"type": "string"}
    },
    "required": ["JD Match", "Missing Keywords", "Profile Summary"]
}


# --- Streamlit Layout ---
st.set_page_config(page_title="Smart ATS Resume Evaluator", layout="centered")
st.markdown("<h1 style='text-align: center; color: #2C3E50;'>🧠 Smart ATS Resume Evaluator</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #7F8C8D;'>Improve Your Resume Match for Application Tracking Systems</p>", unsafe_allow_html=True)

# --- Job Description Upload ---
st.header("📌 Job Description & Settings")
uploaded_jd = st.file_uploader("Upload JD (PDF/DOCX)", type=["pdf", "docx"])
jd_text = ""
if uploaded_jd:
    if uploaded_jd.type == "application/pdf":
        jd_text = extract_pdf_text(uploaded_jd)
    else:
        jd_text = extract_docx_text(uploaded_jd)

# --- Must-Have Skills ---
must_have_skills = st.text_input("Enter Must-Have Skills (comma separated):", "Python, Machine Learning, SQL")
skill_strictness = st.slider("Skill Matching Strictness", 0, 100, 50)
model_option = st.radio("Text Comparison Model", ["Fast Comparison Model (quick, less detailed)", "Detailed Model (slower, more accurate)"])

# --- Resume Upload ---
uploaded_resume = st.file_uploader("Upload Your Resume (PDF only)", type="pdf")

# --- Evaluate ---
if st.button("🚀 Evaluate Resume"):
    if not uploaded_resume or not jd_text:
        st.warning("Please upload both JD and Resume.")
    elif 'api_key' in locals() and not api_key:
        pass
    else:
        with st.spinner("Analyzing resume..."):
            resume_text = extract_pdf_text(uploaded_resume)

            # --- Prepare prompt ---
            input_prompt = f"""
            Act like a skilled ATS evaluating resumes for AI/ML roles.
            JD Text: {jd_text}
            Resume Text: {resume_text}
            Must-Have Skills: {must_have_skills}
            Skill Strictness: {skill_strictness}
            Comparison Model: {model_option}

            Provide output as JSON:
            {{
                "JD Match": "...",
                "Missing Keywords": ["..."],
                "Profile Summary": "..."
            }}
            """

            # --- Gemini response ---
            json_response_string = get_gemini_response(input_prompt, RESPONSE_SCHEMA)

            if json_response_string:
                try:
                    response_data = json.loads(json_response_string)

                    st.markdown("---")
                    st.subheader("✅ ATS Evaluation Results")

                    # --- JD Match handling ---
                    match_text = response_data.get("JD Match", "0")
                    match_map = {"Low": 30, "Medium": 60, "High": 85, "Very High": 95}
                    try:
                        jd_match = int(match_text.replace("%", ""))
                    except ValueError:
                        jd_match = match_map.get(match_text, 0)

                    # --- Must-have skills coverage ---
                    must_have_list = [s.strip().lower() for s in must_have_skills.split(",") if s.strip()]
                    resume_text_lower = resume_text.lower()
                    skills_found = sum(1 for skill in must_have_list if skill in resume_text_lower)
                    skills_total = len(must_have_list)
                    skills_percent = int((skills_found / skills_total) * 100) if skills_total > 0 else 0

                    # --- Missing keywords penalty ---
                    missing_keywords = response_data.get("Missing Keywords", [])
                    keyword_penalty = int((len(missing_keywords)/max(len(missing_keywords)+skills_found, 1)) * 100)

                    # --- Final weighted score ---
                    final_score = int(jd_match*0.6 + skills_percent*0.3 - keyword_penalty*0.1)
                    final_score = max(0, min(final_score, 100))

                    # --- Display results ---
                    st.markdown(f"**JD Match:** {match_text}")
                    st.markdown(f"**Skills Found:** {skills_found}/{skills_total} ({skills_percent}%)")
                    st.markdown(f"**Missing Keywords:** {len(missing_keywords)}")
                    st.progress(final_score)

                    st.markdown("### 🔍 Missing Keywords")
                    if missing_keywords:
                        st.warning(", ".join(missing_keywords))
                    else:
                        st.success("All required skills are present in the resume!")

                    st.markdown("### 📝 Profile Summary & Feedback")
                    st.info(response_data.get("Profile Summary", "No summary provided."))

                    # --- Why Hire / Why Reject ---
                    st.markdown("### ⚖️ Why Hire / Why Reject")
                    if final_score >= 70:
                        hire_reason = f"Candidate has strong skills match ({skills_percent}%), JD match ({jd_match}%), and few missing keywords ({len(missing_keywords)})."
                        st.success(hire_reason)
                    else:
                        reject_reason = f"Candidate has low overall match (score: {final_score}). Missing key skills: {', '.join(missing_keywords)}. JD match: {jd_match}%, Skills coverage: {skills_percent}%."
                        st.error(reject_reason)

                    # --- Past Evaluations ---
                    try:
                        with open("past_evaluations.json", "r") as f:
                            past_evaluations = json.load(f)
                    except:
                        past_evaluations = []

                    evaluation_record = {
                        "Candidate": uploaded_resume.name,
                        "JD": uploaded_jd.name if uploaded_jd else "N/A",
                        "Score": final_score,
                        "Timestamp": str(datetime.now())
                    }
                    past_evaluations.append(evaluation_record)

                    with open("past_evaluations.json", "w") as f:
                        json.dump(past_evaluations, f, indent=2)

                    st.markdown("### 📂 Past Evaluations")
                    st.table(past_evaluations)

                    # --- Shortlisted Candidates ---
                    shortlisted = [c for c in past_evaluations if c["Score"] >= 70]
                    st.markdown("### 🏆 Shortlisted Candidates (Score ≥ 70)")
                    st.table(shortlisted)

                except json.JSONDecodeError:
=======

import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from docx import Document
import json
from dotenv import load_dotenv
from datetime import datetime

# --- Initialization ---
load_dotenv()

try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("Error: GOOGLE_API_KEY environment variable not found.")
    else:
        genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Failed to configure Gemini API: {e}")


# --- Functions ---
def get_gemini_response(input_text, json_schema):
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    try:
        response = model.generate_content(
            input_text,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": json_schema,
            }
        )
        return response.text
    except Exception as e:
        st.error(f"Error during API call: {e}")
        return None


def extract_pdf_text(file):
    reader = pdf.PdfReader(file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()
    return text


def extract_docx_text(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs])


# --- JSON Schema ---
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "JD Match": {"type": "string"},
        "Missing Keywords": {"type": "array", "items": {"type": "string"}},
        "Profile Summary": {"type": "string"}
    },
    "required": ["JD Match", "Missing Keywords", "Profile Summary"]
}


# --- Streamlit Layout ---
st.set_page_config(page_title="Smart ATS Resume Evaluator", layout="centered")
st.markdown("<h1 style='text-align: center; color: #2C3E50;'>🧠 Smart ATS Resume Evaluator</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #7F8C8D;'>Improve Your Resume Match for Application Tracking Systems</p>", unsafe_allow_html=True)

# --- Job Description Upload ---
st.header("📌 Job Description & Settings")
uploaded_jd = st.file_uploader("Upload JD (PDF/DOCX)", type=["pdf", "docx"])
jd_text = ""
if uploaded_jd:
    if uploaded_jd.type == "application/pdf":
        jd_text = extract_pdf_text(uploaded_jd)
    else:
        jd_text = extract_docx_text(uploaded_jd)

# --- Must-Have Skills ---
must_have_skills = st.text_input("Enter Must-Have Skills (comma separated):", "Python, Machine Learning, SQL")
skill_strictness = st.slider("Skill Matching Strictness", 0, 100, 50)
model_option = st.radio("Text Comparison Model", ["Fast Comparison Model (quick, less detailed)", "Detailed Model (slower, more accurate)"])

# --- Resume Upload ---
uploaded_resume = st.file_uploader("Upload Your Resume (PDF only)", type="pdf")

# --- Evaluate ---
if st.button("🚀 Evaluate Resume"):
    if not uploaded_resume or not jd_text:
        st.warning("Please upload both JD and Resume.")
    elif 'api_key' in locals() and not api_key:
        pass
    else:
        with st.spinner("Analyzing resume..."):
            resume_text = extract_pdf_text(uploaded_resume)

            # --- Prepare prompt ---
            input_prompt = f"""
            Act like a skilled ATS evaluating resumes for AI/ML roles.
            JD Text: {jd_text}
            Resume Text: {resume_text}
            Must-Have Skills: {must_have_skills}
            Skill Strictness: {skill_strictness}
            Comparison Model: {model_option}

            Provide output as JSON:
            {{
                "JD Match": "...",
                "Missing Keywords": ["..."],
                "Profile Summary": "..."
            }}
            """

            # --- Gemini response ---
            json_response_string = get_gemini_response(input_prompt, RESPONSE_SCHEMA)

            if json_response_string:
                try:
                    response_data = json.loads(json_response_string)

                    st.markdown("---")
                    st.subheader("✅ ATS Evaluation Results")

                    # --- JD Match handling ---
                    match_text = response_data.get("JD Match", "0")
                    match_map = {"Low": 30, "Medium": 60, "High": 85, "Very High": 95}
                    try:
                        jd_match = int(match_text.replace("%", ""))
                    except ValueError:
                        jd_match = match_map.get(match_text, 0)

                    # --- Must-have skills coverage ---
                    must_have_list = [s.strip().lower() for s in must_have_skills.split(",") if s.strip()]
                    resume_text_lower = resume_text.lower()
                    skills_found = sum(1 for skill in must_have_list if skill in resume_text_lower)
                    skills_total = len(must_have_list)
                    skills_percent = int((skills_found / skills_total) * 100) if skills_total > 0 else 0

                    # --- Missing keywords penalty ---
                    missing_keywords = response_data.get("Missing Keywords", [])
                    keyword_penalty = int((len(missing_keywords)/max(len(missing_keywords)+skills_found, 1)) * 100)

                    # --- Final weighted score ---
                    final_score = int(jd_match*0.6 + skills_percent*0.3 - keyword_penalty*0.1)
                    final_score = max(0, min(final_score, 100))

                    # --- Display results ---
                    st.markdown(f"**JD Match:** {match_text}")
                    st.markdown(f"**Skills Found:** {skills_found}/{skills_total} ({skills_percent}%)")
                    st.markdown(f"**Missing Keywords:** {len(missing_keywords)}")
                    st.progress(final_score)

                    st.markdown("### 🔍 Missing Keywords")
                    if missing_keywords:
                        st.warning(", ".join(missing_keywords))
                    else:
                        st.success("All required skills are present in the resume!")

                    st.markdown("### 📝 Profile Summary & Feedback")
                    st.info(response_data.get("Profile Summary", "No summary provided."))

                    # --- Why Hire / Why Reject ---
                    st.markdown("### ⚖️ Why Hire / Why Reject")
                    if final_score >= 70:
                        hire_reason = f"Candidate has strong skills match ({skills_percent}%), JD match ({jd_match}%), and few missing keywords ({len(missing_keywords)})."
                        st.success(hire_reason)
                    else:
                        reject_reason = f"Candidate has low overall match (score: {final_score}). Missing key skills: {', '.join(missing_keywords)}. JD match: {jd_match}%, Skills coverage: {skills_percent}%."
                        st.error(reject_reason)

                    # --- Past Evaluations ---
                    try:
                        with open("past_evaluations.json", "r") as f:
                            past_evaluations = json.load(f)
                    except:
                        past_evaluations = []

                    evaluation_record = {
                        "Candidate": uploaded_resume.name,
                        "JD": uploaded_jd.name if uploaded_jd else "N/A",
                        "Score": final_score,
                        "Timestamp": str(datetime.now())
                    }
                    past_evaluations.append(evaluation_record)

                    with open("past_evaluations.json", "w") as f:
                        json.dump(past_evaluations, f, indent=2)

                    st.markdown("### 📂 Past Evaluations")
                    st.table(past_evaluations)

                    # --- Shortlisted Candidates ---
                    shortlisted = [c for c in past_evaluations if c["Score"] >= 70]
                    st.markdown("### 🏆 Shortlisted Candidates (Score ≥ 70)")
                    st.table(shortlisted)

                except json.JSONDecodeError:
>>>>>>> b508e7129b62b3983ac1db90992d13ae8e295105
                    st.error("Failed to parse Gemini response JSON.") 