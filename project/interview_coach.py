import google.generativeai as genai
import os
import tempfile
from dotenv import load_dotenv
from gtts import gTTS
import pygame
import time
import threading

load_dotenv()

class InterviewCoach:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.5-flash-lite")
        pygame.mixer.init()
    
    def get_system_prompt(self, job_role, company, experience_level, interview_type):
        return f"""
        You are HR, a professional interviewer at {company}. You are conducting a {interview_type} interview 
        for a {experience_level} {job_role} position.

        Rules:
        1. Speak naturally and conversationally
        2. Ask one question at a time
        3. Provide brief, constructive feedback
        4. Keep responses concise (2–3 sentences)
        5. Maintain a professional but friendly tone
        6. Do not mention you are an AI
        7. Conduct a complete interview with 6–8 questions

        Start with a warm, professional greeting and first question.
        """
    
    def start_interview(self, job_role, company, experience_level, interview_type):
        try:
            chat_session = self.model.start_chat(history=[])
            system_prompt = self.get_system_prompt(job_role, company, experience_level, interview_type)
            response = chat_session.send_message(system_prompt)
            return {
                "chat_session": chat_session,
                "job_role": job_role,
                "company": company,
                "experience_level": experience_level,
                "interview_type": interview_type,
                "first_message": response.text
            }
        except Exception as e:
            raise Exception(f"Error starting interview: {e}")
    
    def get_response(self, chat_session, user_response, job_role, company):
        try:
            prompt = f"""
            Candidate said: {user_response}

            Provide feedback and ask the next question naturally.
            Remember: interviewing for {job_role} at {company}.
            Keep your response conversational and professional.
            """
            response = chat_session.send_message(prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Error getting AI response: {e}")
    
    def speak_text(self, text):
        def speak_thread(text):
            try:
                clean_text = text.replace('*', '').replace('`', '').replace('#', '').strip()
                tts = gTTS(text=clean_text, lang='en', slow=False)
                filename = os.path.join(tempfile.gettempdir(), f"hr_voice_{int(time.time())}.mp3")
                tts.save(filename)
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
            except Exception as e:
                print(f"Speech error: {e}")
        
        thread = threading.Thread(target=speak_thread, args=(text,))
        thread.daemon = True
        thread.start()
        return thread
