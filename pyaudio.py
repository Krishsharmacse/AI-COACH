import requests
import json
import os
import time
# --- Configuration ---
MODEL_NAME = "gemini-2.5-flash-preview-05-20"
API_KEY = os.environ.get("GEMINI_API_KEY") # Reads API key from environment variable
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent"

# List to store the conversation history, used to maintain context
chat_history = []

def initialize_chat():
    """Initializes the chat, checks for the API key, and sets the system prompt."""
    if not API_KEY:
        print("ERROR: GEMINI_API_KEY environment variable not found.")
        print("Please set your Google AI API key as an environment variable to run this script.")
        print("Example (Linux/macOS): export GEMINI_API_KEY='YOUR_API_KEY_HERE'")
        print("Example (Windows CMD): set GEMINI_API_KEY='YOUR_API_KEY_HERE'")
        return False

    # Optional: Add a system instruction to guide the model's behavior
    system_instruction = "You are a friendly and conversational AI assistant. Keep your responses concise and helpful."

    # Add an initial greeting message from the AI (model)
    print("--- Gemini Conversational Chat ---")
    print("AI: Hello! I'm Gemini, a large language model. Ask me anything!")
    print("-" * 35)

    # Note: We add the system instruction outside the history for the API call payload,
    # but the history list tracks only the back-and-forth conversation.
    return system_instruction

def fetch_with_backoff(payload, system_instruction, max_retries=5):
    """
    Sends the request to the Gemini API with exponential backoff for retries.
    """
    headers = {
        'Content-Type': 'application/json'
    }

    for attempt in range(max_retries):
        try:
            # Construct the final request body
            request_body = {
                "contents": payload,
                "systemInstruction": {
                    "parts": [{"text": system_instruction}]
                },
            }

            # Send the request
            response = requests.post(
                f"{API_URL}?key={API_KEY}",
                headers=headers,
                data=json.dumps(request_body),
                timeout=30 # Set a timeout for the API call
            )
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            return response.json()

        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                print(f"\n[ERROR] All API request attempts failed.")
                print(f"Details: {e}")
                raise

            delay = 2 ** attempt
            print(f"\n[INFO] Request failed. Retrying in {delay} seconds (Attempt {attempt + 1}/{max_retries})...")
            time.sleep(delay)

def send_message(user_message, system_instruction):
    """
    Sends the user message, updates history, and gets the AI's response.
    """
    global chat_history

    # 1. Add the user message to history
    chat_history.append({"role": "user", "parts": [{"text": user_message}]})

    try:
        print("\nAI is thinking...", end="", flush=True)

        # 2. Call the API with the full conversation history
        result = fetch_with_backoff(chat_history, system_instruction)

        # 3. Process the response
        candidates = result.get('candidates', [])
        if candidates and candidates[0].get('content'):
            ai_text = candidates[0]['content']['parts'][0]['text']

            # 4. Add the AI response to history
            chat_history.append({"role": "model", "parts": [{"text": ai_text}]})

            print("\rAI:", ai_text)
        else:
            print("\rAI: Sorry, I received an empty or invalid response from the AI.")

    except Exception as e:
        print(f"\r[ERROR] An unexpected error occurred: {e}")


def main():
    """Main function to handle the conversation loop."""
    system_instruction = initialize_chat()
    if not system_instruction:
        return

    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ["quit", "exit", "stop"]:
                print("--- Conversation ended. Goodbye! ---")
                break
            if user_input.strip() == "":
                continue

            send_message(user_input, system_instruction)

        except KeyboardInterrupt:
            print("\n--- Conversation interrupted. Goodbye! ---")
            break
        except Exception as e:
            print(f"\nAn error occurred in the main loop: {e}")
            break

if __name__ == "__main__":
    main()
