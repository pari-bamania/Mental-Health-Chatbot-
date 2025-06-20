from flask import Flask, request, jsonify, session
from flask_cors import CORS
import google.generativeai as genai
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  
app.secret_key = "your_secret_key"


api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("API key not found!")
genai.configure(api_key=api_key)


RESTRICTED_TOPICS = [
    "quitting studies", "drop out", "leave school", "fail exams",
    "disobey parents", "hate parents", "ignore teachers", "fight with parents",
    "self-harm", "depression", "suicide", "harm myself", "kill myself",
    "end my life", "hopeless", "no future", "life is meaningless",
    "violence", "bullying", "abuse", "self-hate", "worthless", "die alone",
    "hurt myself", "cut myself", "painful thoughts", "I want to disappear",
    "crying all the time", "no one loves me", "no one cares about me",
    "what's the point of living", "running away from home", "I'm giving up"
]


MEDICINE_KEYWORDS = [
    "medicine", "medication", "antidepressant", "painkiller", "antibiotic", 
    "paracetamol", "aspirin", "ibuprofen", "prozac", "xanax", "drug", 
    "prescribe", "pill", "tablet", "capsule", "dosage", "treatment", 
    "opioid", "sedative", "sleeping pills", "morphine", "codeine", 
    "tramadol", "ritalin", "adderall", "ssri", "benzodiazepine", 
    "antipsychotic", "stimulant", "sertraline", "fluoxetine", "clonazepam", 
    "diazepam", "hallucinogen", "mdma", "cocaine", "heroin", "methamphetamine"
]



def is_message_safe(user_message):
    """Uses Gemini to analyze message safety."""
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(f"""
    Analyze this message for safety and inappropriate topics: 
    "{user_message}"

    If it contains harmful or restricted content, respond with "restricted".
    Otherwise, respond with "safe".
    """)

    return "restricted" not in response.text.lower()

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

   
    user_message_lower = user_message.lower()

   
    if any(word in user_message_lower for word in MEDICINE_KEYWORDS):
        return jsonify({"response": "I'm not a doctor, but I recommend consulting a medical professional for proper guidance. 😊"})

  
    if not is_message_safe(user_message):
        return jsonify({"response": "I'm here to support you in a positive way. If you're facing difficulties, consider talking to a mentor or a trusted individual. 😊"})

   
    history = session.get("history", "")

    
    formatted_prompt = f"""
    You are a mental health chatbot. Always provide positive encouragement.
    Never suggest quitting studies, disrespecting parents or faculty, or self-harm.
    Never suggest medicines—only recommend consulting doctors.
    also give coping strategies

    Conversation History:
    {history}

    User: {user_message}
    Assistant:
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(formatted_prompt)

        if hasattr(response, "text"):
            history += f"\nUser: {user_message}\nAssistant: {response.text}\n"
            session["history"] = history

            return jsonify({"response": response.text})
        else:
            return jsonify({"error": "No valid response received"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
