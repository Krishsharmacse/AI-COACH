import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from docx import Document
import json
from dotenv import load_dotenv
from datetime import datetime
import re
from typing import Dict, List, Any, Optional

# --- Initialization ---
load_dotenv()

# Initialize session state for persistent data
if 'past_evaluations' not in st.session_state:
    st.session_state.past_evaluations = []
if 'shortlisted_candidates' not in st.session_state:
    st.session_state.shortlisted_candidates = []

try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("❌ Error: GOOGLE_API_KEY environment variable not found.")
        st.info("Please create a .env file with your GOOGLE_API_KEY")
    else:
        genai.configure(api_key=api_key)
        st.success("✅ Gemini API configured successfully!")
except Exception as e:
    st.error(f"❌ Failed to configure Gemini API: {e}")

# --- Enhanced Functions ---
def extract_pdf_text(file) -> str:
    """Extract text from PDF with error handling and better formatting"""
    try:
        reader = pdf.PdfReader(file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                # Clean up text formatting
                page_text = re.sub(r'\s+', ' ', page_text)  # Replace multiple whitespaces
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"❌ Error reading PDF: {e}")
        return ""

def extract_docx_text(file) -> str:
    """Extract text from DOCX with better formatting"""
    try:
        doc = Document(file)
        text = ""
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text += paragraph.text + "\n"
        
        # Extract text from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        text += cell.text + " | "
                text += "\n"
        
        return re.sub(r'\s+', ' ', text).strip()
    except Exception as e:
        st.error(f"❌ Error reading DOCX: {e}")
        return ""

def clean_skills_input(skills_text: str) -> List[str]:
    """Clean and normalize skills input"""
    skills = [skill.strip().lower() for skill in skills_text.split(",")]
    # Remove empty strings and duplicates
    skills = list(set([skill for skill in skills if skill]))
    return skills

def calculate_skill_match(resume_text: str, required_skills: List[str]) -> Dict[str, Any]:
    """Calculate skill matching with synonyms and variations"""
    resume_lower = resume_text.lower()
    
    found_skills = []
    missing_skills = []
    
    # Skill synonyms mapping for better matching
    skill_synonyms = {
        "python": ["python", "python3", "python programming"],
        "machine learning": ["machine learning", "ml", "ai/ml"],
        "sql": ["sql", "mysql", "postgresql", "database"],
        "java": ["java", "java programming"],
        "javascript": ["javascript", "js", "node.js"],
        "react": ["react", "react.js", "reactjs"],
        "aws": ["aws", "amazon web services"],
        "docker": ["docker", "containerization"],
        "kubernetes": ["kubernetes", "k8s"]
    }
    
    for skill in required_skills:
        skill_variations = skill_synonyms.get(skill, [skill])
        found = any(variation in resume_lower for variation in skill_variations)
        
        if found:
            found_skills.append(skill)
        else:
            missing_skills.append(skill)
    
    match_percentage = (len(found_skills) / len(required_skills)) * 100 if required_skills else 0
    
    return {
        "found_skills": found_skills,
        "missing_skills": missing_skills,
        "match_percentage": match_percentage,
        "total_required": len(required_skills),
        "found_count": len(found_skills)
    }

def get_gemini_response(input_text: str, json_schema: Dict) -> Optional[str]:
    """Enhanced Gemini API call with better error handling"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-lite')  # Updated to more capable model
        
        response = model.generate_content(
            input_text,
            generation_config={
                "temperature": 0.2,  # Lower temperature for more consistent results
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
                "response_mime_type": "application/json",
                "response_schema": json_schema,
            }
        )
        return response.text
    except Exception as e:
        st.error(f"❌ Error during Gemini API call: {e}")
        st.info("💡 Tip: Check your API key and quota limits")
        return None

def create_enhanced_prompt(jd_text: str, resume_text: str, must_have_skills: List[str], 
                          skill_strictness: int, model_option: str) -> str:
    """Create a more detailed and structured prompt for better analysis"""
    
    prompt = f"""
    ACT as an expert ATS (Applicant Tracking System) analyst with 10+ years of experience in HR technology and resume screening for AI/ML roles.

    TASK: Analyze the resume against the job description and provide a comprehensive evaluation.

    JOB DESCRIPTION:
    {jd_text[:3000]}  # Limit length to avoid token limits

    RESUME CONTENT:
    {resume_text[:3000]}  # Limit length to avoid token limits

    MUST-HAVE SKILLS: {', '.join(must_have_skills)}
    SKILL STRICTNESS LEVEL: {skill_strictness}/100
    ANALYSIS MODEL: {model_option}

    ANALYSIS CRITERIA:
    1. JD Match Percentage: Consider experience relevance, education, certifications, and overall fit
    2. Missing Keywords: Identify crucial technical skills, tools, and methodologies mentioned in JD but missing in resume
    3. Profile Summary: Provide constructive feedback on strengths, weaknesses, and improvement suggestions

    IMPORTANT INSTRUCTIONS:
    - Be objective and unbiased in evaluation
    - Focus on quantifiable achievements in the resume
    - Consider skill transferability and related technologies
    - Account for the strictness level in your assessment
    - Provide actionable recommendations for improvement

    EXPECTED JSON OUTPUT FORMAT:
    {{
        "JD Match": "85%",  // Be specific with percentage
        "Missing Keywords": ["specific technology", "required certification", ...],
        "Profile Summary": "Detailed analysis covering experience match, skill gaps, and recommendations"
    }}

    Be thorough but concise in your analysis.
    """
    
    return prompt

# --- Enhanced JSON Schema ---
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "JD Match": {"type": "string"},
        "Missing Keywords": {"type": "array", "items": {"type": "string"}},
        "Profile Summary": {"type": "string"},
        "Strengths": {"type": "array", "items": {"type": "string"}},
        "Improvement_Areas": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["JD Match", "Missing Keywords", "Profile Summary"]
}

# --- Streamlit UI Enhancement ---
st.set_page_config(
    page_title="Smart ATS Resume Evaluator", 
    layout="wide",
    page_icon="🧠"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem !important;
        color: #2C3E50 !important;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        color: #7F8C8D !important;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #3498db;
        margin: 0.5rem 0;
    }
    .success-card {
        border-left-color: #2ecc71;
    }
    .warning-card {
        border-left-color: #f39c12;
    }
    .error-card {
        border-left-color: #e74c3c;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 class='main-header'>🧠 Smart ATS Resume Evaluator</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>AI-Powered Resume Analysis for Better Job Application Success</p>", unsafe_allow_html=True)

# --- Main Layout ---
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📋 Job Description & Requirements")
    
    uploaded_jd = st.file_uploader("Upload Job Description (PDF/DOCX)", 
                                  type=["pdf", "docx"], 
                                  key="jd_uploader")
    
    jd_text = ""
    if uploaded_jd:
        with st.spinner("Extracting text from job description..."):
            if uploaded_jd.type == "application/pdf":
                jd_text = extract_pdf_text(uploaded_jd)
            else:
                jd_text = extract_docx_text(uploaded_jd)
        
        if jd_text:
            st.success(f"✅ JD extracted successfully! ({len(jd_text)} characters)")
            with st.expander("Preview JD Text"):
                st.text(jd_text[:500] + "..." if len(jd_text) > 500 else jd_text)
    
    must_have_skills = st.text_area(
        "Must-Have Skills (comma separated):", 
        "Python, Machine Learning, SQL, Data Analysis, Deep Learning",
        help="List the crucial skills required for this position"
    )
    
    skill_strictness = st.slider(
        "Skill Matching Strictness", 
        0, 100, 70,
        help="How strictly should skills be matched? Higher values require exact matches"
    )
    
    model_option = st.selectbox(
        "Analysis Model",
        ["Fast Analysis (quick assessment)", "Detailed Analysis (comprehensive evaluation)"],
        help="Choose based on your needs - detailed analysis provides more insights but takes longer"
    )

with col2:
    st.header("📄 Resume Analysis")
    
    uploaded_resume = st.file_uploader(
        "Upload Your Resume (PDF)", 
        type="pdf",
        help="Currently supporting PDF format only for resumes"
    )
    
    if uploaded_resume:
        with st.spinner("Extracting text from resume..."):
            resume_text = extract_pdf_text(uploaded_resume)
        
        if resume_text:
            st.success(f"✅ Resume extracted successfully! ({len(resume_text)} characters)")
            with st.expander("Preview Resume Text"):
                st.text(resume_text[:500] + "..." if len(resume_text) > 500 else resume_text)

# --- Evaluation Button ---
st.markdown("---")
evaluate_col1, evaluate_col2, evaluate_col3 = st.columns([1, 2, 1])

with evaluate_col2:
    if st.button("🚀 Start Comprehensive Evaluation", use_container_width=True):
        if not uploaded_resume or not resume_text:
            st.error("❌ Please upload a valid resume file.")
        elif not jd_text:
            st.error("❌ Please upload a job description file.")
        elif 'api_key' not in locals() or not api_key:
            st.error("❌ API configuration error. Please check your Google API key.")
        else:
            with st.spinner("🔍 Performing comprehensive analysis..."):
                # Clean and process skills
                required_skills = clean_skills_input(must_have_skills)
                
                # Calculate skill match
                skill_analysis = calculate_skill_match(resume_text, required_skills)
                
                # Prepare enhanced prompt
                input_prompt = create_enhanced_prompt(
                    jd_text, resume_text, required_skills, 
                    skill_strictness, model_option
                )
                
                # Get Gemini response
                json_response_string = get_gemini_response(input_prompt, RESPONSE_SCHEMA)
                
                if json_response_string:
                    try:
                        response_data = json.loads(json_response_string)
                        
                        st.markdown("---")
                        st.header("📊 Evaluation Results")
                        
                        # Extract JD Match percentage
                        jd_match_text = response_data.get("JD Match", "0%")
                        jd_match_value = int(re.search(r'(\d+)%', jd_match_text).group(1)) if re.search(r'(\d+)%', jd_match_text) else 0
                        
                        # Display metrics in cards
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.markdown(f'<div class="metric-card success-card">'
                                      f'<h3>JD Match</h3>'
                                      f'<h2>{jd_match_value}%</h2>'
                                      f'</div>', unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown(f'<div class="metric-card { "success-card" if skill_analysis["match_percentage"] >= 70 else "warning-card" }">'
                                      f'<h3>Skills Match</h3>'
                                      f'<h2>{skill_analysis["match_percentage"]:.1f}%</h2>'
                                      f'<small>{skill_analysis["found_count"]}/{skill_analysis["total_required"]} skills</small>'
                                      f'</div>', unsafe_allow_html=True)
                        
                        with col3:
                            missing_keywords = response_data.get("Missing Keywords", [])
                            st.markdown(f'<div class="metric-card { "success-card" if len(missing_keywords) <= 3 else "warning-card" }">'
                                      f'<h3>Missing Keywords</h3>'
                                      f'<h2>{len(missing_keywords)}</h2>'
                                      f'</div>', unsafe_allow_html=True)
                        
                        with col4:
                            # Calculate final score with weighted factors
                            final_score = (
                                jd_match_value * 0.5 + 
                                skill_analysis["match_percentage"] * 0.4 + 
                                (100 - min(len(missing_keywords) * 5, 50)) * 0.1
                            )
                            final_score = max(0, min(100, final_score))
                            
                            score_color = "success-card" if final_score >= 70 else "warning-card" if final_score >= 50 else "error-card"
                            st.markdown(f'<div class="metric-card {score_color}">'
                                      f'<h3>Overall Score</h3>'
                                      f'<h2>{final_score:.1f}%</h2>'
                                      f'</div>', unsafe_allow_html=True)
                        
                        # Progress bar
                        st.progress(final_score / 100)
                        
                        # Detailed Results
                        tab1, tab2, tab3, tab4 = st.tabs(["📋 Skills Analysis", "🔍 Missing Keywords", "📝 Profile Summary", "⚖️ Recommendation"])
                        
                        with tab1:
                            st.subheader("Skills Analysis")
                            st.write(f"**Required Skills:** {', '.join(required_skills)}")
                            st.write(f"**Found Skills:** {', '.join(skill_analysis['found_skills'])}")
                            st.write(f"**Missing Skills:** {', '.join(skill_analysis['missing_skills'])}")
                            
                            # Skills visualization
                            if required_skills:
                                for skill in required_skills:
                                    status = "✅" if skill in skill_analysis['found_skills'] else "❌"
                                    st.write(f"{status} {skill}")
                        
                        with tab2:
                            st.subheader("Missing Keywords & Skills")
                            missing_keywords = response_data.get("Missing Keywords", [])
                            if missing_keywords:
                                st.warning("The following keywords from the JD are missing in your resume:")
                                for i, keyword in enumerate(missing_keywords, 1):
                                    st.write(f"{i}. {keyword}")
                            else:
                                st.success("🎉 No major keywords missing! Your resume covers most requirements.")
                        
                        with tab3:
                            st.subheader("Profile Summary & Feedback")
                            profile_summary = response_data.get("Profile Summary", "No summary provided.")
                            st.info(profile_summary)
                        
                        with tab4:
                            st.subheader("Hiring Recommendation")
                            if final_score >= 75:
                                st.success("🏆 **STRONG RECOMMENDATION** - This candidate is well-qualified for the position.")
                                st.write("**Why Hire:**")
                                st.write(f"- Strong JD match ({jd_match_value}%)")
                                st.write(f"- Excellent skills coverage ({skill_analysis['match_percentage']:.1f}%)")
                                st.write(f"- Minimal missing keywords ({len(missing_keywords)})")
                            elif final_score >= 60:
                                st.warning("⚠️ **CONSIDER WITH INTERVIEW** - Candidate has potential but some gaps exist.")
                                st.write("**Areas to explore in interview:**")
                                for skill in skill_analysis['missing_skills']:
                                    st.write(f"- Experience with {skill}")
                            else:
                                st.error("❌ **NOT RECOMMENDED** - Significant gaps between resume and requirements.")
                                st.write("**Primary concerns:**")
                                st.write(f"- Low JD match ({jd_match_value}%)")
                                st.write(f"- Missing {len(missing_keywords)} key keywords")
                                st.write(f"- Only {skill_analysis['found_count']}/{skill_analysis['total_required']} required skills found")
                        
                        # Save evaluation to session state
                        evaluation_record = {
                            "Candidate": uploaded_resume.name,
                            "JD": uploaded_jd.name if uploaded_jd else "Manual Input",
                            "JD_Match": jd_match_value,
                            "Skills_Match": skill_analysis["match_percentage"],
                            "Missing_Keywords": len(missing_keywords),
                            "Overall_Score": final_score,
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        st.session_state.past_evaluations.append(evaluation_record)
                        
                        # Update shortlisted candidates
                        st.session_state.shortlisted_candidates = [
                            candidate for candidate in st.session_state.past_evaluations 
                            if candidate["Overall_Score"] >= 70
                        ]
                        
                    except json.JSONDecodeError as e:
                        st.error(f"❌ Failed to parse API response: {e}")
                        st.text("Raw response for debugging:")
                        st.text(json_response_string)
                    except Exception as e:
                        st.error(f"❌ Unexpected error: {e}")

# --- History Section ---
st.markdown("---")
st.header("📊 Evaluation History")

if st.session_state.past_evaluations:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("All Evaluations")
        # Convert to DataFrame for better display
        import pandas as pd
        df = pd.DataFrame(st.session_state.past_evaluations)
        st.dataframe(df, use_container_width=True)
    
    with col2:
        st.subheader("📈 Statistics")
        if st.session_state.past_evaluations:
            avg_score = sum(eval["Overall_Score"] for eval in st.session_state.past_evaluations) / len(st.session_state.past_evaluations)
            best_score = max(eval["Overall_Score"] for eval in st.session_state.past_evaluations)
            shortlisted_count = len(st.session_state.shortlisted_candidates)
            
            st.metric("Average Score", f"{avg_score:.1f}%")
            st.metric("Best Score", f"{best_score:.1f}%")
            st.metric("Shortlisted", shortlisted_count)
        
        if st.button("Clear History"):
            st.session_state.past_evaluations = []
            st.session_state.shortlisted_candidates = []
            st.rerun()

else:
    st.info("No evaluation history yet. Complete your first analysis to see results here.")

# --- Footer ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: #7F8C8D;'>"
           "🧠 Smart ATS Resume Evaluator v2.0 | Powered by Google Gemini AI"
           "</div>", unsafe_allow_html=True)