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

    def listen_candidate(self):
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                print("\n[Microphone] Adjusting for ambient noise...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                print("[Microphone] Listening for candidate response...")
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=30)
            
            print("[Microphone] Recognizing speech...")
            text = recognizer.recognize_google(audio)
            print(f"[Microphone] Candidate said: {text}")
            return text
        except ImportError:
            print("SpeechRecognition library is not installed. Please install it using `pip install SpeechRecognition pyaudio`")
            return ""
        except Exception as e:
            print(f"[Microphone] Speech recognition error: {e}")
            return ""

    def evaluate_interview(self, conversation_history, job_role, company):
        try:
            # Format history for the prompt
            formatted_history = ""
            for msg in conversation_history:
                role = "Interviewer" if msg['role'] == "interviewer" else "Candidate"
                formatted_history += f"{role}: {msg['message']}\n"
                
            prompt = f"""
            You are an expert HR Interview Evaluator. Review this interview transcript for a {job_role} position at {company}.
            
            Interview Transcript:
            {formatted_history}
            
            Please provide a short evaluation in valid JSON format:
            {{
                "score": <number between 0 and 100>,
                "strengths": ["string", "string"],
                "areas_for_improvement": ["string", "string"],
                "overall_feedback": "string (2-3 sentences max)"    
            }}
            Return purely valid JSON, with no markdown formatting or extra text.
            """
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Error evaluating interview: {e}")
