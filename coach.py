import streamlit as st
import google.generativeai as genai
import os
import tempfile
from dotenv import load_dotenv
from gtts import gTTS
import pygame
import time
import threading
import base64
import requests
import json

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize model
model = genai.GenerativeModel("gemini-2.5-flash-lite")

st.set_page_config(page_title="AI HR Interview Coach", page_icon="🎤", layout="wide")

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        text-align: center;
        font-weight: bold;
    }
    .recording {
        background-color: #ff6b6b;
        color: white;
        animation: pulse 1.5s infinite;
    }
    .speaking {
        background-color: #4ecdc4;
        color: white;
    }
    .ready {
        background-color: #45b7d1;
        color: white;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    .conversation-box {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
        max-height: 300px;
        overflow-y: auto;
    }
    .user-message {
        border-left: 4px solid #28a745;
        background-color: #e8f5e8;
    }
    .ai-message {
        border-left: 4px solid #1f77b4;
        background-color: #e3f2fd;
    }
    .record-button {
        background-color: #ff6b6b !important;
        color: white !important;
        border: none !important;
        padding: 10px 20px !important;
        border-radius: 25px !important;
        font-size: 16px !important;
        margin: 10px 0 !important;
    }
    .stop-button {
        background-color: #45b7d1 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🤵 AI HR Interview Coach</div>', unsafe_allow_html=True)

# Initialize session state
if "chat" not in st.session_state:
    st.session_state.chat = None
if "interview_started" not in st.session_state:
    st.session_state.interview_started = False
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "is_speaking" not in st.session_state:
    st.session_state.is_speaking = False
if "is_recording" not in st.session_state:
    st.session_state.is_recording = False
if "audio_data" not in st.session_state:
    st.session_state.audio_data = None

# Initialize pygame mixer
pygame.mixer.init()

# Interview settings in sidebar
with st.sidebar:
    st.header("🎯 Interview Settings")
    job_role = st.text_input("Job Role", "Software Engineer")
    company = st.text_input("Company", "TechCorp Solutions")
    experience_level = st.selectbox("Experience Level", ["Entry Level", "Mid Level", "Senior Level"])
    interview_type = st.selectbox("Interview Type", ["Technical", "Behavioral", "HR Screening", "Comprehensive"])
    
    st.markdown("---")
    st.header("🎤 Voice Options")
    voice_enabled = st.checkbox("Enable Voice Responses", value=True)
    st.info("Voice works best with Chrome/Edge browsers")
    
    st.markdown("---")
    st.header("💡 Instructions")
    st.markdown("""
    1. Click **Start Interview**
    2. Wait for HR greeting
    3. **Type your answer** in the text box
    4. Click **Send Response**
    5. AI will respond (with voice if enabled)
    6. Continue the conversation
    """)

# System prompt
SYSTEM_PROMPT = f"""
You are HR, a professional HR interviewer at {company}. You are conducting a {interview_type} interview for a {experience_level} {job_role} position.

IMPORTANT RULES:
1. Speak naturally and conversationally
2. Ask ONE question at a time
3. Provide brief, constructive feedback
4. Show genuine interest in candidate's answers
5. Keep responses concise (2-3 sentences)
6. Adapt questions based on candidate's experience level
7. Maintain professional but friendly tone
8. Do NOT mention you are an AI
9. Conduct a complete interview with 6-8 questions

Start with a warm professional greeting and first question.
"""

# Function: Speak text
def speak_text(text):
    if not voice_enabled:
        return
        
    def speak_thread(text):
        try:
            st.session_state.is_speaking = True
            
            # Clean text for speech
            clean_text = text.replace('*', '').replace('`', '').replace('#', '').strip()
            
            tts = gTTS(text=clean_text, lang='en', slow=False)
            filename = os.path.join(tempfile.gettempdir(), f"hr_voice_{int(time.time())}.mp3")
            tts.save(filename)
            
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
        except Exception as e:
            st.error(f"Speech error: {e}")
        finally:
            st.session_state.is_speaking = False
    
    thread = threading.Thread(target=speak_thread, args=(text,))
    thread.daemon = True
    thread.start()

# Function: Transcribe using Google Speech-to-Text API
def transcribe_audio_api(audio_bytes):
    try:
        # For now, we'll use manual input as primary
        # This function is a placeholder for when you want to integrate with a speech-to-text API
        return None
    except Exception as e:
        st.error(f"Transcription error: {e}")
        return None

# Start interview function
def start_interview():
    try:
        st.session_state.chat = model.start_chat(history=[])
        response = st.session_state.chat.send_message(SYSTEM_PROMPT)
        first_message = response.text
        
        st.session_state.conversation_history.append({
            "role": "interviewer", 
            "message": first_message,
            "timestamp": time.time()
        })
        
        st.session_state.interview_started = True
        if voice_enabled:
            speak_text(first_message)
        st.rerun()
        
    except Exception as e:
        st.error(f"Error starting interview: {e}")

# Process text response
def process_text_response(text_response):
    if not text_response.strip():
        st.warning("Please enter your response before sending.")
        return
        
    # Add user response to conversation
    st.session_state.conversation_history.append({
        "role": "candidate", 
        "message": text_response,
        "timestamp": time.time()
    })
    
    # Get AI response
    with st.spinner("🤵 HR is thinking..."):
        try:
            ai_response = st.session_state.chat.send_message(
                f"Candidate said: {text_response}. Please provide appropriate feedback and ask the next question naturally."
            )
            ai_message = ai_response.text
            
            st.session_state.conversation_history.append({
                "role": "interviewer", 
                "message": ai_message,
                "timestamp": time.time()
            })
            
            if voice_enabled:
                speak_text(ai_message)
                
            st.rerun()
            
        except Exception as e:
            st.error(f"Error getting AI response: {e}")

# Main interface layout
col1, col2 = st.columns([2, 1])

with col1:
    # Status panel
    st.subheader("🎮 Control Panel")
    
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        if st.session_state.interview_started:
            st.markdown('<div class="status-box ready">✅ Interview Active</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box">⏸️ Ready to Start</div>', unsafe_allow_html=True)
    
    with status_col2:
        if st.session_state.get('is_speaking', False):
            st.markdown('<div class="status-box speaking">🎤 HR Speaking</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box">💤 Ready</div>', unsafe_allow_html=True)
    
    with status_col3:
        if voice_enabled:
            st.markdown('<div class="status-box ready">🔊 Voice ON</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box">🔇 Voice OFF</div>', unsafe_allow_html=True)

    # Control buttons
    button_col1, button_col2 = st.columns(2)
    
    with button_col1:
        if not st.session_state.interview_started:
            if st.button("🚀 Start Interview", use_container_width=True, type="primary"):
                start_interview()
        else:
            if st.button("⏹️ End Interview", use_container_width=True, type="secondary"):
                st.session_state.interview_started = False
                st.session_state.conversation_history = []
                st.success("Interview completed! Thank you.")
                st.rerun()

    # Text input for responses
    if st.session_state.interview_started and not st.session_state.is_speaking:
        st.subheader("💬 Your Response")
        
        with st.form("response_form", clear_on_submit=True):
            text_response = st.text_area(
                "Type your answer to the interviewer's question:",
                placeholder="Type your response here...",
                height=150,
                key="response_text"
            )
            
            col1, col2 = st.columns([3, 1])
            with col2:
                submitted = st.form_submit_button(
                    "📤 Send Response",
                    type="primary",
                    use_container_width=True
                )
            
            if submitted and text_response:
                process_text_response(text_response)

with col2:
    st.subheader("📊 Interview Info")
    st.info(f"""
    **Role:** {job_role}
    **Company:** {company}
    **Level:** {experience_level}
    **Type:** {interview_type}
    **Questions:** {len([m for m in st.session_state.conversation_history if m['role'] == 'interviewer'])}/8
    """)
    
    if st.session_state.interview_started:
        progress = min(len([m for m in st.session_state.conversation_history if m['role'] == 'interviewer']) / 8, 1.0)
        st.progress(progress)
        st.caption(f"Interview Progress: {int(progress * 100)}%")

# Conversation display
st.markdown("---")
st.subheader("💬 Live Conversation")

# Create a container for conversation with fixed height and scroll
conversation_container = st.container()

with conversation_container:
    if st.session_state.conversation_history:
        for chat in st.session_state.conversation_history:
            if chat["role"] == "interviewer":
                st.markdown(f"""
                <div class="conversation-box ai-message">
                    <strong>🤵 HR Interviewer:</strong><br>
                    {chat["message"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="conversation-box user-message">
                    <strong>👤 You:</strong><br>
                    {chat["message"]}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("💬 Conversation will appear here. Start the interview to begin!")

# Voice recording alternative (optional)
if st.session_state.interview_started:
    with st.expander("🎤 Alternative: Upload Audio Response (Optional)"):
        st.info("If you have a pre-recorded audio file, you can upload it here")
        uploaded_audio = st.file_uploader("Choose an audio file", type=['wav', 'mp3', 'm4a'])
        if uploaded_audio is not None:
            st.audio(uploaded_audio, format='audio/wav')
            if st.button("Transcribe Uploaded Audio"):
                st.info("Audio upload feature - would transcribe here with proper API")

# Quick tips
with st.expander("🚀 Quick Tips for Successful Interview"):
    st.markdown("""
    **How to get the best experience:**
    
    **🎯 Answering Questions:**
    - Be specific and provide examples
    - Use the STAR method (Situation, Task, Action, Result)
    - Keep responses focused but detailed
    - Show enthusiasm for the role
    
    **💬 Conversation Flow:**
    - The AI remembers everything you say
    - It will ask follow-up questions based on your answers
    - Treat it like a real interview
    - Ask clarifying questions if needed
    
    **🔊 Voice Features:**
    - Enable voice for most realistic experience
    - Use headphones for better audio quality
    - Ensure your system volume is adequate
    """)

# Sample questions to help users
if not st.session_state.interview_started:
    with st.expander("📋 Common Interview Questions to Prepare For"):
        st.markdown("""
        **Technical Roles:**
        - Tell me about a challenging technical project
        - How do you approach problem-solving?
        - Describe your experience with [specific technology]
        
        **Behavioral Questions:**
        - Tell me about a time you faced conflict at work
        - Describe a situation where you failed and what you learned
        - How do you handle tight deadlines?
        
        **HR Questions:**
        - Why do you want to work here?
        - Where do you see yourself in 5 years?
        - What are your strengths and weaknesses?
        """)

# Add auto-scroll JavaScript
st.markdown("""
<script>
function scrollToBottom() {
    window.scrollTo(0, document.body.scrollHeight);
}
// Scroll when the page loads or updates
window.addEventListener('load', scrollToBottom);
</script>
""", unsafe_allow_html=True)