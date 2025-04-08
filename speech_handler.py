import whisper
import sounddevice as sd
import numpy as np
import wave
import pyttsx3
from app import generate_response

def record_audio(filename="recorded_audio.wav", duration=5, samplerate=44100):
    print("Please speak now...")
    audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype=np.int16)
    sd.wait()
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(audio_data.tobytes())
    return filename

model = whisper.load_model("base")

def transcribe_audio(filename):
    result = model.transcribe(filename)
    return result["text"]

def speak_text(text):
    engine = pyttsx3.init()
    engine.setProperty("rate", 170)
    engine.setProperty("volume", 1.0)
    voices = engine.getProperty("voices")
    engine.setProperty("voice", voices[0].id)  # Default voice
    engine.say(text)
    engine.runAndWait()

def record_and_respond():
    audio_file = record_audio()
    question = transcribe_audio(audio_file)
    print("You asked:", question)
    answer = generate_response(question)
    print("Chatbot Response:", answer)
    speak_text(answer)
    return answer