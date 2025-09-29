import threading
import streamlit as st
import pyttsx3
import speech_recognition as sr


engine = pyttsx3.init()
engine_lock = threading.Lock()


def speak(text: str) -> None:
    def _speak():
        with engine_lock:
            engine.say(text)
            engine.runAndWait()
    threading.Thread(target=_speak).start()


def stop_speech() -> None:
    with engine_lock:
        engine.stop()


def listen_for_stop() -> None:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio).lower()
            if "stop" in command:
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


