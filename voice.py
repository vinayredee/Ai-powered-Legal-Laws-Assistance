import threading
import streamlit as st
import pyttsx3
import speech_recognition as sr

# Robust TTS engine initialization
try:
    engine = pyttsx3.init()
except Exception as e:
    engine = None
    st.warning("Text-to-speech is unavailable on this system.")

engine_lock = threading.Lock()

def speak(text: str) -> None:
    if engine:
        def _speak():
            with engine_lock:
                engine.say(text)
                engine.runAndWait()
        threading.Thread(target=_speak).start()
    else:
        st.info("TTS engine not available.")

def stop_speech() -> None:
    if engine:
        with engine_lock:
            engine.stop()

def listen_for_stop() -> None:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio).lower()
            if "stop" in command and engine:
                stop_speech()
        except Exception:
            pass

def listen() -> str:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        try:
            query = recognizer.recognize_google(audio)
            st.write(f"Voice Input: {query}")
            return query
        except Exception:
            st.error("Voice input unavailable.")
            return ""


