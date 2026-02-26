from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from processing import ResumeAnalyzer
from interview_coach import InterviewCoach
import json
import os
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager
import uuid
import asyncio

# Global variables
analysis_history = []
active_interviews = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global analysis_history
    try:
        if os.path.exists("analysis_history.json"):
            with open("analysis_history.json", "r") as f:
                analysis_history = json.load(f)
            print(f"Loaded {len(analysis_history)} previous analyses")
    except Exception as e:
        print(f"Could not load history file: {e}")
        analysis_history = []
    yield
    # Shutdown
    print("Server shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title="CareerPrep Pro - ATS Analyzer & AI Interview Coach",
    description="Complete career preparation platform with resume analysis and AI-powered interview coaching",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # Using wildcard origins; do not allow credentials to avoid browser CORS errors
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize analyzers
analyzer = ResumeAnalyzer()
interview_coach = InterviewCoach()

# Get current directory
current_dir = Path(__file__).parent
static_dir = current_dir / "static"

print(f"Current directory: {current_dir}")
print(f"Static directory: {static_dir}")
print(f"Static exists: {static_dir.exists()}")

# Serve static files
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    print("Static files mounted at /static")
else:
    print("Static directory not found! Creating it...")
    static_dir.mkdir(exist_ok=True)

@app.get("/")
async def serve_frontend():
    """Serve the main frontend page"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    else:
        basic_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>CareerPrep Pro</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>CareerPrep Pro - ATS Analyzer & AI Interview Coach</h1>
                <p>Backend is running! Please make sure the frontend files are in the static directory.</p>
                <p>Check the console for setup instructions.</p>
            </div>
        </body>
        </html>
        """
        return basic_html

@app.get("/styles.css")
async def serve_css():
    css_path = static_dir / "styles.css"
    if css_path.exists():
        return FileResponse(css_path)
    raise HTTPException(status_code=404)

@app.get("/script.js")
async def serve_js():
    js_path = static_dir / "script.js"
    if js_path.exists():
        return FileResponse(js_path)
    raise HTTPException(status_code=404)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Resume Analysis Endpoints
@app.post("/analyze")
async def analyze_resume(
    jd_file: UploadFile = File(...),
    resume_file: UploadFile = File(...),
    must_have_skills: str = Form("Python, Machine Learning, SQL, AWS, Docker"),
    skill_strictness: int = Form(75),
    min_experience: int = Form(2),
    analysis_depth: str = Form("Standard"),
    industry_focus: str = Form("Technology")
):
    """Analyze resume against job description"""
    try:
        print(f"Received analysis request:")
        print(f"   JD File: {jd_file.filename}")
        print(f"   Resume File: {resume_file.filename}")
        
        # Validate file types
        allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword", "text/plain"]
        
        if jd_file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Job description must be PDF, DOCX, or TXT")
        
        if resume_file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Resume must be PDF, DOCX, or TXT")
        
        # Read file contents
        jd_content = await jd_file.read()
        resume_content = await resume_file.read()
        
        if len(jd_content) == 0:
            raise HTTPException(status_code=400, detail="Job description file is empty")
        if len(resume_content) == 0:
            raise HTTPException(status_code=400, detail="Resume file is empty")
        
        # Perform analysis (run synchronous, blocking work in a thread)
        print("Starting analysis with ResumeAnalyzer (offloaded to thread)...")
        result = await asyncio.to_thread(
            analyzer.analyze_resume,
            jd_content,
            jd_file.content_type,
            resume_content,
            resume_file.content_type,
            must_have_skills,
            skill_strictness,
        )
        
        if not result["success"]:
            print(f"Analysis failed with error: {result['error']}")
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Add to history
        analysis_record = {
            "timestamp": datetime.now().isoformat(),
            "jd_file": jd_file.filename,
            "resume_file": resume_file.filename,
            "overall_score": result["overall_score"],
            "component_scores": result["component_scores"],
            "analysis_data": result["analysis_data"]
        }
        
        analysis_history.append(analysis_record)
        
        # Save history to file
        try:
            with open("analysis_history.json", "w") as f:
                json.dump(analysis_history, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save history: {e}")
        
        print("Analysis completed successfully!")
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected analysis error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# Interview Coach Endpoints
@app.post("/interview/start")
async def start_interview(
    job_role: str = Form("Software Engineer"),
    company: str = Form("TechCorp Solutions"),
    experience_level: str = Form("Mid Level"),
    interview_type: str = Form("Technical"),
    voice_enabled: bool = Form(False)
):
    """Start a new interview session"""
    try:
        session_id = str(uuid.uuid4())

        # Start interview session (offload blocking API call)
        session_data = await asyncio.to_thread(
            interview_coach.start_interview,
            job_role,
            company,
            experience_level,
            interview_type,
        )
        
        active_interviews[session_id] = {
            **session_data,
            "session_id": session_id,
            "voice_enabled": voice_enabled,
            "conversation_history": [],
            "start_time": datetime.now().isoformat()
        }
        
        # Add first message
        first_message = session_data["first_message"]
        active_interviews[session_id]["conversation_history"].append({
            "role": "interviewer",
            "message": first_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # If voice enabled, speak the first message
        if voice_enabled:
            interview_coach.speak_text(first_message)

        
        return {
            "success": True,
            "session_id": session_id,
            "first_message": first_message
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")

@app.post("/interview/respond")
async def interview_respond(
    session_id: str = Form(...),
    user_response: str = Form(...)
):
    """Process user response and get AI reply"""
    try:
        if session_id not in active_interviews:
            raise HTTPException(status_code=404, detail="Interview session not found")
        
        session = active_interviews[session_id]
        
        # Add user message to history
        session["conversation_history"].append({
            "role": "candidate",
            "message": user_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Get AI response (offload blocking API call)
        ai_response = await asyncio.to_thread(
            interview_coach.get_response,
            session["chat_session"],
            user_response,
            session["job_role"],
            session["company"],
        )
        
        # Add AI message to history
        session["conversation_history"].append({
            "role": "interviewer",
            "message": ai_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # If voice enabled, speak the AI response
        if session.get("voice_enabled"):
            interview_coach.speak_text(ai_response)

        
        return {
            "success": True,
            "ai_response": ai_response,
            "conversation_history": session["conversation_history"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process response: {str(e)}")

@app.get("/interview/history/{session_id}")
async def get_interview_history(session_id: str):
    """Get interview conversation history"""
    try:
        if session_id not in active_interviews:
            raise HTTPException(status_code=404, detail="Interview session not found")
        
        return {
            "success": True,
            "conversation_history": active_interviews[session_id]["conversation_history"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

@app.post("/interview/end")
async def end_interview(session_id: str = Form(...)):
    """End an interview session and get evaluation"""
    try:
        if session_id not in active_interviews:
            raise HTTPException(status_code=404, detail="Interview session not found")
            
        session = active_interviews[session_id]
        
        evaluation = None
        if len(session["conversation_history"]) > 1:
            try:
                # Offload blocking eval call
                result_text = await asyncio.to_thread(
                    interview_coach.evaluate_interview,
                    session["conversation_history"],
                    session["job_role"],
                    session["company"]
                )
                
                # Cleanup JSON formatting if present
                clean_text = result_text.strip()
                if clean_text.startswith("```json"): clean_text = clean_text[7:]
                if clean_text.startswith("```"): clean_text = clean_text[3:]
                if clean_text.endswith("```"): clean_text = clean_text[:-3]
                
                evaluation = json.loads(clean_text.strip())
            except Exception as e:
                print(f"Evaluation failed: {e}")
        
        del active_interviews[session_id]
        
        return {
            "success": True, 
            "message": "Interview session ended", 
            "evaluation": evaluation
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end interview: {str(e)}")

@app.post("/interview/listen")
async def interview_listen(session_id: str = Form(...)):
    """Listen to candidate via server microphone"""
    try:
        if session_id not in active_interviews:
            raise HTTPException(status_code=404, detail="Interview session not found")
        
        text = await asyncio.to_thread(interview_coach.listen_candidate)
        if text:
            return {"success": True, "text": text}
        else:
            return {"success": False, "error": "Could not recognize speech. Please try again or type your response."}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to listen: {str(e)}")


# History Endpoints
@app.get("/history")
async def get_analysis_history(limit: int = 10):
    """Get analysis history"""
    try:
        recent_history = analysis_history[-limit:] if analysis_history else []
        
        formatted_history = []
        for record in recent_history:
            formatted_history.append({
                "date": datetime.fromisoformat(record['timestamp']).strftime("%Y-%m-%d %H:%M"),
                "jd_file": record['jd_file'],
                "resume_file": record['resume_file'],
                "score": record['overall_score'],
                "status": "Shortlist" if record['overall_score'] >= 70 else "Review" if record['overall_score'] >= 50 else "Reject"
            })
        
        return {
            "success": True,
            "history": formatted_history,
            "total_analyses": len(analysis_history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")

@app.delete("/history")
async def clear_history():
    """Clear analysis history"""
    try:
        global analysis_history
        analysis_history.clear()
        
        if os.path.exists("analysis_history.json"):
            os.remove("analysis_history.json")
            
        return {"success": True, "message": "History cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear history: {str(e)}")
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
