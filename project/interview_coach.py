import google.generativeai as genai
import os
import tempfile
from dotenv import load_dotenv
from gtts import gTTS
import pygame
import time
import threading
import speech_recognition as sr

load_dotenv()

class InterviewCoach:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.5-flash-lite")
        pygame.mixer.init()
        self.listening = False
    
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
                filename = os.path.join(tempfile.gettempdir(), f"hr_voice_{int(time.time() * 1000)}.mp3")
                tts.save(filename)
                
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                    
                if os.path.exists(filename):
                    try:
                        os.remove(filename)
                    except:
                        pass
            except Exception as e:
                print(f"[Speech error]: {e}")
        
        thread = threading.Thread(target=speak_thread, args=(text,))
        thread.daemon = True
        thread.start()
        return thread

    def stop_listening(self):
        """Toggle off the microphone gracefully."""
        print("[Microphone] Stopping...")
        self.listening = False

    def listen_candidate(self, timeout=10, phrase_time_limit=30):
        """
        Listens to candidate until they toggle off the microphone manually.
        """
        try:
            recognizer = sr.Recognizer()
            self.listening = True
            
            with sr.Microphone() as source:
                print("\n[Microphone] Adjusting for ambient noise (0.5 sec)...")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("[Microphone] Listening for candidate response (Click Stop to finish)...")
                
                # We read manually from pyaudio to allow immediate break when user stops
                audio_frames = []
                # Check buffer up to 45 seconds total if user never clicks Stop
                max_iterations = int((45.0 * source.SAMPLE_RATE) / source.CHUNK)
                
                for _ in range(max_iterations):
                    if not self.listening:
                        break
                    try:
                        buffer = source.stream.read(source.CHUNK)
                        audio_frames.append(buffer)
                    except IOError as e:
                        # Depending on platform, sometimes reads can overflow or underflow
                        pass
            
            self.listening = False
            
            if not audio_frames:
                return ""
            
            print("[Microphone] Recognizing speech via Google...")
            # Convert to AudioData which recognizer requires
            audio_data = sr.AudioData(b"".join(audio_frames), source.SAMPLE_RATE, source.SAMPLE_WIDTH)
            text = recognizer.recognize_google(audio_data)
            print(f"[Microphone] Candidate said: {text}")
            return text
            
        except sr.UnknownValueError:
            print("[Microphone] Could not understand audio.")
            return ""
        except sr.RequestError as e:
            print(f"[Microphone] API request failed: {e}")
            return ""
        except ImportError:
            print("SpeechRecognition not fully installed")
            return ""
        except Exception as e:
            print(f"[Microphone] Unexpected error: {e}")
            return ""

    def evaluate_interview(self, conversation_history, job_role, company):
        try:
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
