import PyPDF2 as pdf
from docx import Document
import json, requests, os, re
from io import BytesIO
import numpy as np
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

class ResumeAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")

    # ---------- TEXT EXTRACTION ----------
    def extract_pdf_text(self, file_content):
        try:
            if isinstance(file_content, str):
                file_content = file_content.encode("utf-8")
            reader = pdf.PdfReader(BytesIO(file_content))
            return "".join([page.extract_text() or "" for page in reader.pages]).strip()
        except Exception as e:
            raise Exception(f"Error reading PDF: {e}")

    def extract_docx_text(self, file_content):
        try:
            doc = Document(BytesIO(file_content))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as e:
            raise Exception(f"Error reading DOCX: {e}")

    def extract_text_from_file(self, file_content, file_type):
        try:
            if file_type == "application/pdf":
                return self.extract_pdf_text(file_content)
            elif file_type in [
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword",
            ]:
                return self.extract_docx_text(file_content)
            elif file_type == "text/plain":
                return (
                    file_content.decode("utf-8", errors="ignore")
                    if isinstance(file_content, bytes)
                    else str(file_content)
                )
            raise Exception(f"Unsupported file type: {file_type}")
        except Exception as e:
            raise Exception(f"Text extraction failed: {e}")

    # ---------- ANALYSIS HELPERS ----------
    def advanced_text_similarity(self, jd_text, resume_text):
        try:
            if not jd_text.strip() or not resume_text.strip():
                return 0
            vec = TfidfVectorizer(stop_words="english", max_features=1000)
            tfidf = vec.fit_transform([jd_text, resume_text])
            return round(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0] * 100, 2)
        except Exception as e:
            print(f"Similarity calculation error: {e}")
            return 0

    def extract_skills_from_text(self, text):
        try:
            pattern = (
                r"\b(?:python|java|javascript|react|node\.js|sql|mongodb|aws|docker|kubernetes|"
                r"machine learning|deep learning|nlp|computer vision|tensorflow|pytorch|scikit-learn|"
                r"pandas|numpy|tableau|power bi|excel|git|jenkins|linux|rest api|graphql|typescript|"
                r"angular|vue\.js|html|css|sass|less|php|ruby|rails|go|rust|c\+\+|c#|swift|kotlin|"
                r"flutter|react native)\b"
            )
            return list(set(re.findall(pattern, text.lower())))
        except Exception:
            return []

    def calculate_experience(self, text):
        try:
            patterns = [
                r"(\d+)\+?\s*years?",
                r"(\d+)\+?\s*yrs?",
                r"experience.*?(\d+)\+?\s*years?",
            ]
            years = []
            for p in patterns:
                for match in re.findall(p, text.lower()):
                    try:
                        years.append(int(match))
                    except ValueError:
                        pass
            return max(years) if years else 0
        except Exception:
            return 0

    # ---------- AI ANALYSIS ----------
    def get_ai_enhanced_analysis(self, jd_text, resume_text, must_have_skills, skill_strictness):
        if not self.api_key:
            raise Exception("OPENROUTER_API_KEY not found")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        model = "nvidia/nemotron-3-nano-30b-a3b:free"
        jd_trunc = jd_text[:3000] + "..." if len(jd_text) > 3000 else jd_text
        res_trunc = resume_text[:4000] + "..." if len(resume_text) > 4000 else resume_text

        prompt = f"""
        As an expert ATS (Applicant Tracking System) analyst, analyze this resume against the job description.
        JOB DESCRIPTION:\n{jd_trunc}\n
        RESUME CONTENT:\n{res_trunc}\n
        Must-have skills: {must_have_skills} | Strictness: {skill_strictness}/100

        Return JSON:
        {{
            "overall_match_percentage": "85",
            "match_category": "High",
            "skills_analysis": {{
                "missing_critical_skills": ["skill1"],
                "strong_skills": ["skill2"],
                "skills_match_percentage": "85"
            }},
            "experience_evaluation": {{
                "years_experience_match": "Strong",
                "relevant_experience_score": "8/10",
                "career_progression": "Positive"
            }},
            "keyword_analysis": {{
                "missing_keywords": ["keyword1"],
                "keyword_density_score": "75",
                "ats_optimization_score": "80"
            }},
            "detailed_feedback": {{
                "strengths": ["strength1"],
                "weaknesses": ["weakness1"],
                "immediate_improvements": ["improvement1"]
            }},
            "recommendations": {{
                "resume_optimization": ["tip1"],
                "skill_development": ["skill1"],
                "presentation_improvements": ["improvement1"]
            }},
            "risk_factors": ["risk1"],
            "potential_red_flags": ["flag1"]
        }}
        """

        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are an ATS analyst. You must return your response as purely valid JSON, with no markdown formatting or extra text."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 4096,
        }

        try:
            res = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=90,
            )
            if res.status_code == 200:
                j = res.json()
                return j["choices"][0]["message"]["content"]
            raise Exception(f"OpenRouter API Error: {res.status_code} - {res.text}")
        except Exception as e:
            raise Exception(f"Error during API call: {e}")

    # ---------- SCORING ----------
    def calculate_comprehensive_score(self, ai_analysis, jd_text, resume_text, must_have_skills):
        try:
            # Clean markdown formatting if present
            clean_ai = ai_analysis.strip()
            if clean_ai.startswith("```json"):
                clean_ai = clean_ai[7:]
            if clean_ai.startswith("```"):
                clean_ai = clean_ai[3:]
            if clean_ai.endswith("```"):
                clean_ai = clean_ai[:-3]
            clean_ai = clean_ai.strip()

            try:
                a = json.loads(clean_ai)
            except Exception as e:
                print(f"RAW AI RESPONSE:\\n{ai_analysis}")
                raise e

            base = float(a.get("overall_match_percentage", 0))

            must = [s.strip().lower() for s in must_have_skills.split(",") if s.strip()]
            res_lower = resume_text.lower()
            found = sum(1 for s in must if s in res_lower)
            skills = (found / len(must)) * 100 if must else 100

            sim = self.advanced_text_similarity(jd_text, resume_text)
            jd_exp = self.calculate_experience(jd_text)
            res_exp = self.calculate_experience(resume_text)
            exp = min(100, (res_exp / max(jd_exp, 1)) * 100) if jd_exp > 0 else 100

            jd_kw = self.extract_skills_from_text(jd_text)
            res_kw = self.extract_skills_from_text(resume_text)
            kw = (len(set(jd_kw) & set(res_kw)) / len(jd_kw)) * 100 if jd_kw else 100

            final = base * 0.3 + skills * 0.25 + sim * 0.2 + exp * 0.15 + kw * 0.1
            return {
                "final_score": round(final),
                "component_scores": {
                    "base_ai_score": round(base),
                    "skills_score": round(skills),
                    "similarity_score": round(sim),
                    "experience_score": round(exp),
                    "keyword_score": round(kw),
                },
            }
        except Exception as e:
            raise Exception(f"Score calculation error: {e}")

    # ---------- MAIN FUNCTION ----------
    def analyze_resume(
        self, jd_file_content, jd_file_type, resume_file_content, resume_file_type, must_have_skills, skill_strictness=75
    ):
        try:
            jd = self.extract_text_from_file(jd_file_content, jd_file_type)
            res = self.extract_text_from_file(resume_file_content, resume_file_type)
            if not jd or not res:
                raise Exception("Could not extract text from one or both files")

            print("🔄 Getting AI-enhanced analysis...")
            ai = self.get_ai_enhanced_analysis(jd, res, must_have_skills, skill_strictness)
            if not ai:
                raise Exception("Failed to get AI analysis")

            scores = self.calculate_comprehensive_score(ai, jd, res, must_have_skills)
            
            clean_ai = ai.strip()
            if clean_ai.startswith("```json"):
                clean_ai = clean_ai[7:]
            if clean_ai.startswith("```"):
                clean_ai = clean_ai[3:]
            if clean_ai.endswith("```"):
                clean_ai = clean_ai[:-3]
            clean_ai = clean_ai.strip()
            
            data = json.loads(clean_ai)
            return {
                "success": True,
                "overall_score": scores["final_score"],
                "component_scores": scores["component_scores"],
                "analysis_data": data,
                "text_stats": {"jd_length": len(jd), "resume_length": len(res)},
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
