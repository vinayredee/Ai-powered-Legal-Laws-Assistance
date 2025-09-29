import streamlit as st
st.set_page_config(page_title="Legal Assistant", layout="wide")
import threading
import pandas as pd
import json
import os
from voice import speak, listen, listen_for_stop
from pdf_export import generate_pdf_from_log
from email_service import send_email
import requests

# Initialize session state attributes if not already set
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_context" not in st.session_state:
    st.session_state.conversation_context = []
if "interaction_log" not in st.session_state:
    st.session_state.interaction_log = pd.DataFrame(columns=["user_query", "assistant_response"])

# Ensure language_preference and user_logged_in are initialized
if "language_preference" not in st.session_state:
    st.session_state.language_preference = "English"
if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False
if "greet_started" not in st.session_state:
    st.session_state.greet_started = False
if "use_llm" not in st.session_state:
    st.session_state.use_llm = True
if "use_voice" not in st.session_state:
    st.session_state.use_voice = False

# Voice functions are imported from voice.py

# Patterns loader is imported from patterns.py

# No pattern loading: fully LLM-driven

# Define response function based on patterns
def get_response(query):
    query = query.strip()
    if len(query) < 3:
        return translations.get(st.session_state.language_preference, translations["English"]).get("no_response", "No response.")

    st.session_state.conversation_context.append(f"User: {query}")

    llm_reply = generate_llm_response(query)
    if llm_reply:
        st.session_state.conversation_context.append(f"Assistant: {llm_reply}")
        return llm_reply
    return translations.get(st.session_state.language_preference, translations["English"]).get("no_response", "No response.")

def generate_llm_response(query):
    """Generate a response using a local LLM via Ollama (no API key required)."""
    if not st.session_state.use_llm:
        return None

    # Try local Ollama if running (no API key needed)
    try:
        ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        ollama_model = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")
        sys_msg = "You provide non-advisory legal information for India. Keep answers concise with a brief disclaimer."
        # Prefer native Ollama chat API
        chat_payload = {
            "model": ollama_model,
            "messages": [
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": f"User question: {query}"},
            ],
            "stream": False,
        }
        r = requests.post(f"{ollama_host}/api/chat", json=chat_payload, timeout=120)
        if r.status_code == 200:
            data = r.json()
            msg = (data.get("message") or {}).get("content")
            if msg:
                return msg.strip()
        else:
            st.info(f"Ollama not ready (HTTP {r.status_code}). Ensure the model '{ollama_model}' is pulled: ollama run {ollama_model}")
        # Fallback to OpenAI-compatible endpoint if available
        compat_payload = {
            "model": ollama_model,
            "messages": [
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": f"User question: {query}"},
            ],
            "stream": False,
        }
        r2 = requests.post(f"{ollama_host}/v1/chat/completions", json=compat_payload, timeout=120)
        if r2.status_code == 200:
            data2 = r2.json()
            msg2 = data2.get("choices", [{}])[0].get("message", {}).get("content")
            if msg2:
                return msg2.strip()
        else:
            st.info(f"Ollama compatibility endpoint not ready (HTTP {r2.status_code}). Try again after model download finishes.")
    except Exception:
        st.info("Local LLM (Ollama) not available. Install from ollama.com and run: ollama run llama3.2")

    return None

# Language Translation Dictionary
translations = {
    "English": {
        "ask_query": "Ask your query for legal assistance",
        "thinking": "Thinking ✨...",
        "no_response": "Sorry, I couldn't find a matching response for your query.",
        "positive_feedback": "👍 Positive feedback",
        "negative_feedback": "👎 Negative feedback",
        "login_button": "Login",
        "welcome": "Welcome",
        "faq_button": "Show FAQs",
        "download_button": "Download",
        "interaction_history": "Show Interaction History",
        "voice_query": "Voice Query 🎙️",
        "view_history": "View History 📜",
        "download_law": "Download Law 📁 ",
        "info_section": "**Legal Laws Assistance:📄**\n- **Objective:** Developed a conversational chatbot to provide legal laws info and assistance.\n- **Features:**📜\n  - Allows users to ask their query of law.\n  - Includes Mutlilingual, Voice query, Legal templates support.\n  - Provides a response to user query. ✔\n  - Offers a user-friendly interface for asking legal queries."
    },
    "Hindi - हिन्दी": {
        "ask_query": "कानूनी सहायता के लिए अपना प्रश्न पूछें",
        "thinking": "सोच रहे हैं ✨...",
        "no_response": "मुझे आपके प्रश्न का मिलान करने वाला उत्तर नहीं मिला।",
        "positive_feedback": "👍 सकारात्मक प्रतिक्रिया",
        "negative_feedback": "👎 नकारात्मक प्रतिक्रिया",
        "login_button": "लॉगिन करें",
        "welcome": "स्वागत है",
        "faq_button": "सामान्य प्रश्न दिखाएँ",
        "download_button": "चैट इतिहास डाउनलोड करें",
        "interaction_history": "इंटरएक्शन इतिहास दिखाएँ",
        "voice_query": "आवाज़ से पूछें 🎙️",
        "view_history": "इतिहास देखें 📜",
        "download_law": "कानून डाउनलोड करें 📁",
         "info_section": """
        **कानूनी क़ानून सलाहकार बॉट📄**
        - **लक्ष्य:** कानूनी क़ानून जानकारी और सहायता प्रदान करने के लिए एक संवादात्मक चैटबॉट विकसित किया गया।
        - **विशेषताएँ:**📜
          -  उपयोगकर्ताओं को कानून से संबंधित प्रश्न पूछने की अनुमति देता है। 𓍝
          -  उपयोगकर्ता के प्रश्न का उत्तर प्रदान करता है। ✔
          -  उपयोगकर्ता के प्रश्न का विस्तृत विवरण, दंड, लाभ, और हानियाँ प्रदर्शित करता है। ✉︎
          -  कानूनी प्रश्न पूछने के लिए एक उपयोगकर्ता-मित्र इंटरफेस प्रदान करता है। 🔗
        """
    },
    "Telugu - తెలుగు": {
        "ask_query": "న్యాయ సహాయం కోసం మీ ప్రశ్నను అడగండి",
        "thinking": "ఆలోచిస్తున్నాను ✨...",
        "no_response": "మీ ప్రశ్నకు సరిపడే సమాధానం కనుగొనలేకపోయాను.",
        "positive_feedback": "👍 సానుకూల అభిప్రాయం",
        "negative_feedback": "👎 ప్రతికూల అభిప్రాయం",
        "login_button": "లాగిన్ చేయండి",
        "welcome": "స్వాగతం",
        "faq_button": "ఎఫ్ ఏ క్యూ లను చూపించండి",
        "download_button": "చాట్ చరిత్రను డౌన్‌లోడ్ చేయండి",
        "interaction_history": "మాట్లాడిన చరిత్ర చూపించు",
        "voice_query": "వాయిస్ క్వెరీ 🎙️",
        "view_history": "చరిత్ర చూడండి 📜",
        "download_law": "డౌన్‌లోడ్ చేయండి 📁",
        "info_section": """
        **చట్టాల సలహా బాట్📄**
        - **ఉద్దేశం:** చట్టాల సమాచారం మరియు సహాయం అందించడానికి ఒక సంభాషణ చాట్‌బాట్‌ను అభివృద్ధి చేయడం।
        - **ప్రతి పౌరుడు చట్టాల గురించి అవగాహన కలిగి ఉండాలి.
        - **సదుపాయాలు:**📜
          -  వినియోగదారులు చట్టం గురించి తమ ప్రశ్నను అడగగలుగుతారు। 𓍝
          -  వినియోగదారుల ప్రశ్నకు సమాధానం అందిస్తుంది। ✔
          -  వినియోగదారు ప్రశ్నకు సంబంధించిన వివరణ, శిక్షలు, లాభాలు మరియు నష్టాలను ప్రదర్శిస్తుంది। ✉︎
          -  చట్టంపై ప్రశ్నలను అడగడానికి వినియోగదారు-అనుకూల ఇంటర్‌ఫేస్ అందిస్తుంది। 🔗
        - **ప్రాముఖ్యత:** సంభాషణ కృత్రిమ నుణ్ణి గుణం ద్వారా చట్ట సమాచారాన్ని అందించే లోనిపడి సరళత, సామర్థ్యం మరియు యాక్సెస్‌పై దృష్టి సారిస్తుంది। 📝
        """
    },
    "Tamil - தமிழ்": {
        "ask_query":"சட்ட உதவிக்கு உங்கள் கேள்வியைக் கேளுங்கள்",
        "thinking": "சிந்தித்து கொண்டிருக்கிறேன் ✨...",
        "no_response": "உங்கள் கேள்விக்கான பதிலை காணவில்லை.",
        "positive_feedback": "👍 நல்ல கருத்து",
        "negative_feedback": "👎 எதிர்மறை கருத்து",
        "login_button": "உள்நுழைய",
        "welcome": "வரவேற்கிறேன்",
        "faq_button": "கேள்விகளை காண்பிக்கவும்",
        "download_button": "அரட்டை வரலாற்றைப் பதிவிறக்கவும்",
        "interaction_history": "உரையாடல் வரலாற்றைக் காண்பிக்கவும்",
        "voice_query": "குரல் கேள்வி 🎙️",
        "view_history": "வரலாற்றைக் காண்க 📜",
        "download_law": "சட்டத்தை பதிவிறக்கவும் 📁",
        "info_section": """
        **சட்ட ஆலோசகர்போட்📄**
        - **நோக்கம்:** சட்ட தகவல்கள் மற்றும் உதவியை வழங்குவதற்காக உருவாக்கப்பட்ட ஒரு உரையாடல் சாட் பாட்டை உருவாக்கியது.
        - **ஒவ்வொரு குடிமகனும் சட்டங்களைப் பற்றி அறிந்திருக்க வேண்டும்.**
        - **சாதனைகள்:**📜
          -  பயனாளர்களுக்கு சட்டம் பற்றிய கேள்விகளை கேட்க அனுமதிக்கின்றது। 𓍝
          -  பயனாளரின் கேள்விக்கு பதில் அளிக்கின்றது। ✔
          -  பயனாளரின் கேள்விக்கு தொடர்புடைய விளக்கம், தண்டனைகள், நன்மைகள் மற்றும் தீமைகளை காட்டுகின்றது। ✉︎
          -  சட்டங்களைப் பற்றி கேட்க பயனாளர் நட்பான இடைமுகத்தை வழங்குகிறது। 🔗
        - **முக்கியத்துவம்:** உரையாடல் செயற்கை நுண்ணறிவு வழியாக சட்ட தகவல்களை வழங்குவதில் எளிமை, திறன் மற்றும் அணுகுமுறை என்பதிலுள்ள கவனம். 📝
        """
    },
    "Kannada - ಕನ್ನಡ": {
    "ask_query": "ನಿಮ್ಮ ಕಾನೂನು ಸಹಾಯಕ್ಕಾಗಿ ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ",
    "thinking": "ಆಲೋಚನೆ ✨...",
    "no_response": "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ಪ್ರಶ್ನೆಗೆ ಹೊಂದುವ ಉತ್ತರವನ್ನು ನಾನು ಕಂಡುಹಿಡಿಯಲಿಲ್ಲ.",
    "positive_feedback": "👍 ಉತ್ತಮ ಪ್ರತಿಕ್ರಿಯೆ",
    "negative_feedback": "👎 ಹೀನಾಯ ಪ್ರತಿಕ್ರಿಯೆ",
    "login_button": "ಲಾಗಿನ್",
    "welcome": "ಸ್ವಾಗತ",
    "faq_button": "FAQಗಳನ್ನು ತೋರಿಸಿ",
    "download_button": "ಚಾಟ್ ಇತಿಹಾಸವನ್ನು PDFಗೆ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ",
    "interaction_history": "ಇಂಟರಾಕ್ಷನ್ ಇತಿಹಾಸವನ್ನು ತೋರಿಸಿ",
    "voice_query": "ಧ್ವನಿ ಪ್ರಶ್ನೆ 🎙️",
    "view_history": "ಇತಿಹಾಸ ವೀಕ್ಷಿಸಿ 📜",
    "download_law": "ಕಾನೂನು ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ 📁",
    "info_section": "**ಕಾನೂನು ಸಲಹೆಗಾರ ಬಾಟ್:📄**\n- **ಉದ್ದೇಶ:** ಕಾನೂನು ಮಾಹಿತಿ ಮತ್ತು ಸಹಾಯ ನೀಡಲು ಸಂವಾದಾತ್ಮಕ ಚಾಟ್‌ಬಾಟ್ ಅನ್ನು ಅಭಿವೃದ್ಧಿಪಡಿಸಲಾಗಿದೆ.\n- **ವೈಶಿಷ್ಟ್ಯಗಳು:**📜\n  - ಬಳಕೆದಾರರಿಗೆ ಕಾನೂನು ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಲು ಅವಕಾಶ ನೀಡುತ್ತದೆ.\n  - ಬಳಕೆದಾರರ ಪ್ರಶ್ನೆಗೆ ಉತ್ತರವನ್ನು ನೀಡುತ್ತದೆ. ✔\n  - ಕಾನೂನು ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳಲು ಬಳಕೆದಾರ-ಹಿತಕರ ಇಂಟರ್‌ಫೇಸ್ ಅನ್ನು ಒದಗಿಸುತ್ತದೆ."
},
    "Malayalam - മലയാളം": {
    "ask_query": "നിങ്ങളുടെ നിയമ സഹായത്തിനായുള്ള ചോദ്യം ചോദിക്കുക",
    "thinking": "ചിന്തിക്കുന്നു ✨...",
    "no_response": "ക്ഷമിക്കണം, നിങ്ങളുടെ ചോദ്യത്തിന് അനുയോജമായ പ്രതികരണം കണ്ടെത്താനായില്ല.",
    "positive_feedback": "👍 സാന്ദര്യപരമായ പ്രതികരണം",
    "negative_feedback": "👎 പ്രതികൂല പ്രതികരണം",
    "login_button": "ലോഗിൻ",
    "welcome": "സ്വാഗതം",
    "faq_button": "FAQ കാണിക്കുക",
    "download_button": "ചാറ്റ് ചരിത്രം PDF ആയി ഡൗൺലോഡ് ചെയ്യുക",
    "interaction_history": "ഇന്ററാക്ഷൻ ചരിത്രം കാണിക്കുക",
    "voice_query": "ശബ്ദ ചോദ്യം 🎙️",
    "view_history": "ചരിത്രം കാണുക 📜",
    "download_law": "നിയമം ഡൗൺലോഡ് ചെയ്യുക 📁",
    "info_section": "**നിയമ ഉപദേഷ്ടാവ് ബോട്ട്:📄**\n- **ലക്ഷ്യം:** നിയമ വിവരങ്ങളും സഹായവും നൽകാൻ സംഭാഷണ ചാറ്റ്‌ബോട്ട് വികസിപ്പിച്ചിരിക്കുന്നു.\n- **സവിശേഷതകൾ:**📜\n  - ഉപയോക്താക്കളെ നിയമ ചോദ്യങ്ങൾ ചോദിക്കാൻ അനുവദിക്കുന്നു.\n  - ഉപയോക്തൃ ചോദ്യത്തിന് പ്രതികരണം നൽകുന്നു. ✔\n  - നിയമ ചോദ്യങ്ങൾ ചോദിക്കാൻ ഉപയോക്തൃ സൗഹൃദ ഇന്റർഫേസ് നൽകുന്നു."
}
}
# Streamlit Title
st.title("LEGAL LAWS ASSISTANCE 🎗️")

# Load and display the info section
lang = translations.get(st.session_state.language_preference, translations["English"]) 
st.info(lang.get("info_section", ""))
st.warning("This app provides general legal information, not legal advice. Consult a qualified lawyer for advice.")

# Language selection from the sidebar
st.sidebar.title("FEATURES")
language_preference = st.sidebar.selectbox(
    "Welcome Select your preferred language :",
    ["English", "Hindi - हिन्दी", "Telugu - తెలుగు", "Tamil - தமிழ்", "Malayalam - മലയാളം", "Kannada - ಕನ್ನಡ"],
    index=["English", "Hindi - हिन्दी", "Telugu - తెలుగు", "Tamil - தமிழ்", "Malayalam - മലയാളം", "Kannada - ಕನ್ನಡ"].index(st.session_state.language_preference)
)

# Voice toggle and LLM status
st.session_state.use_llm = True
st.sidebar.checkbox(
    "Enable Voice (TTS)",
    value=st.session_state.use_voice,
    key="use_voice"
)

def _ollama_ready() -> bool:
    try:
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        r = requests.get(f"{host}/api/tags", timeout=2)
        return r.status_code == 200
    except Exception:
        return False

if _ollama_ready():
    st.sidebar.success("LLM: Ready")
else:
    st.sidebar.warning("LLM: Not ready")

# Save selected language preference in session state
if language_preference != st.session_state.language_preference:
    st.session_state.language_preference = language_preference

# User login logic
if not st.session_state.user_logged_in:
    # Optional admin/passcode gate via env var
    admin_pass = os.environ.get("ADMIN_PASS")
    if admin_pass:
        entered = st.text_input("Enter access passcode to continue", type="password")
        if entered and entered == admin_pass:
            st.session_state.user_logged_in = True
            st.rerun()
        elif entered and entered != admin_pass:
            st.error("Incorrect passcode")
    else:
        # Prompt for the user's name
        st.session_state.username = st.text_input("Enter your name to start interaction with legal laws assistant 🎗️")
        if st.session_state.username:
            st.session_state.user_logged_in = True
            st.rerun()
else:
    # Once logged in, show the legal assistant functionalities
    st.write(f"👋 Hello {st.session_state.username}! {translations[st.session_state.language_preference]['ask_query']}")
    prompt = st.chat_input(translations[st.session_state.language_preference]["ask_query"])

    if prompt:
        st.write(f"👤 Your Query: {prompt}")
        response = get_response(prompt)
        st.write(f"🤖 Response: {response}")

        new_log = {"user_query": prompt, "assistant_response": response}
        st.session_state.interaction_log = pd.concat(
            [st.session_state.interaction_log, pd.DataFrame([new_log])], ignore_index=True
        )
        
# VOICE QUERY HISTORY DOWNLOAD LAW BUTTONS

# Create 4 columns for the buttons
col1, col2, col3, col4 = st.columns(4)

# Speech to Text Button
with col1:
    if st.button(translations[st.session_state.language_preference]["voice_query"]):
        if not st.session_state.use_voice:
            st.info("Voice is disabled. Enable it in the sidebar.")
        else:
            query = listen()
            if query:
                st.session_state.messages.append(query)
                st.write(f"Your Query: {query}")
                response = get_response(query)
                st.write(f"Assistant Response: {response}")
                # Speak only if voice enabled
                if st.session_state.use_voice:
                    speak(response)

                new_log = {"user_query": query, "assistant_response": response}
                st.session_state.interaction_log = pd.concat(
                    [st.session_state.interaction_log, pd.DataFrame([new_log])], ignore_index=True
                )

# Interaction History Button
with col2:
    if st.button(translations[st.session_state.language_preference]["view_history"]):
        st.dataframe(st.session_state.interaction_log)

# PDF generator is imported from pdf_export.py

# Download Button for PDF
with col3:
    if st.button(translations[st.session_state.language_preference]["download_law"]):
        pdf_path = generate_pdf_from_log(st.session_state.interaction_log)
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="📄 Download Chat as PDF",
                data=f.read(),
                file_name="Chat_History.pdf",
                mime="application/pdf",
            )

# Clear history / Export CSV
with col4:
    if st.button("Clear History"):
        st.session_state.interaction_log = pd.DataFrame(columns=["user_query", "assistant_response"])
        st.success("History cleared")
    st.download_button(
        label="⬇️ Export CSV",
        data=st.session_state.interaction_log.to_csv(index=False).encode('utf-8'),
        file_name="interaction_history.csv",
        mime="text/csv"
    )


if __name__ == '__main__':
    # Disable auto TTS greeting to avoid pyttsx3 run-loop conflicts
    pass
    

 #  GMAIL SERVICES ##
 # Path to the templates folder
TEMPLATES_FOLDER = "templates"

# Sidebar Navigation
st.sidebar.title(" ")
menu_selection = st.sidebar.selectbox("Select a Service:", ["Select", "Gmail Services"])

if menu_selection == "Gmail Services":
    st.subheader("📧 Send Legal Documents via Email")
    user_email = st.text_input("Enter your email:")
    documents = [f for f in os.listdir(TEMPLATES_FOLDER) if f.endswith('.pdf')]
    selected_document = st.selectbox("Choose a document:", documents)

    if st.button("Send Document"):
        if not os.environ.get("SMTP_USERNAME") or not os.environ.get("SMTP_PASSWORD"):
            st.error("Email not configured. Set SMTP_USERNAME and SMTP_PASSWORD.")
        elif user_email and selected_document:
            document_path = os.path.join(TEMPLATES_FOLDER, selected_document)
            success = send_email(user_email, "Your Legal Document", "Please find the attached legal document.", document_path)
            if success:
                st.success(f"✅ Document sent to {user_email} successfully!")
            else:
                st.error("❌ Failed to send the document. Please try again.")
        else:
            st.warning("⚠️ Please enter an email and select a document.")           
# Sidebar for template selection            
# Folder where templates are stored
TEMPLATES_FOLDER = "templates"
# Legal templates with file names
legal_templates = {
    "Rental Agreement": "rental_agreement_template.pdf",
    "Loan Agreement":"loan-agreement-template.pdf",
    "Employment Agreement": "employment_agreement_template.pdf",
    "Business Agreement": "partnership_agreement_template.pdf",
    "Freelancer Agreement": "freelancer_contract_template.pdf",
    "Invoice Agreement": "invoice_template.pdf",
    "Lease Agreement": "lease_agreement_template.pdf",
    "Service Agreement": "service_agreement_template.pdf",
    "Non-Disclosure Agreement": "nda_template.pdf"  
}
# Sidebar 
st.sidebar.title("")
with st.sidebar:   
    # Language selection dropdown for templates with placeholder
    template_selection = st.selectbox(
        "Select a legal template to download :",  # Title for the dropdown
        ["Select a template"] + list(legal_templates.keys())  # Add a placeholder option
    )
# Get the selected template's file name
if template_selection != "Select a template":  # Ensure a valid selection is made
    selected_template_file = legal_templates.get(template_selection)
    # Check if the selected template file exists and provide the download button
    if selected_template_file:
        file_path = os.path.join(TEMPLATES_FOLDER, selected_template_file)     
        if os.path.exists(file_path):  # Check if the file exists
            with open(file_path, "rb") as file:
                st.sidebar.download_button(
                    label=f"📄 Download {template_selection}",
                    data=file.read(),
                    file_name=selected_template_file,
                    mime="application/pdf"
                )
        else:
            st.sidebar.warning(f"Template '{template_selection}' is not available.")
            
 
            
# Sidebar section with a button to show external legal resource links
# Custom CSS to style the button
st.markdown(
    """
    <style>
    /* Style the button to be black and full-width */
    .stButton>button {
        background-color: #0d0d0d !important; /* Black background */
        border: 5px solid light-grey !important;   /* White border */
        color: white !important;              /* White text */
        width: 100% !important;               /* Full width */
        height: 40px !important;              /* Fixed height */
        border-radius: 10px !important;        /* Rounded corners */
        cursor: pointer;                     /* Pointer cursor on hover */
        font-size: 16px !important;           /* Font size */
    }
    .stButton>button:hover {
        background-color: white !important;  /* White background on hover */
        color: #4CAF50 !important;            /* Green text on hover */
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar section with a button to show external legal resource links

with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    # Small text above the button with inline style for font size and minimal margin
    st.markdown('<p style="font-size: 14px; color: white; margin-bottom: 3.8px;">Click to view external legal resources :</p>', unsafe_allow_html=True) 
    # Button to display external legal resources
    if st.button("External Legal Resources 🌐"):
        # External Legal Resource Links shown upon button click
        st.markdown("[**🔗 Indian Judiciary**](https://www.india.gov.in/topics/law-justice/)")
        st.markdown("[**🔗 Ministry of Law & Justice**](https://legislative.gov.in/)")
        st.markdown("[**🔗 Supreme Court of India**](https://main.sci.gov.in/)")     
    # Adding space after the content to separate from other sidebar features
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    