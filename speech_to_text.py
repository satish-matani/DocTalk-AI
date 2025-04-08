import whisper
import sounddevice as sd
import numpy as np
import wave
import pyttsx3  # Text-to-speech library
import app  # Importing your app.py functions

def record_audio(filename="recorded_audio.wav", duration=5, samplerate=44100):
    print("Please speak now....")
    audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype=np.int16)
    sd.wait()
    
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(audio_data.tobytes())
    
    print("Recording saved as", filename)
    return filename

def transcribe_audio(filename):
    print("Loading Whisper model...")
    model = whisper.load_model("base")  # Using a lighter Whisper model
    print("Transcribing audio...")
    result = model.transcribe(filename)
    return result["text"]

def speak_text(text):
    """Convert text to speech and read it out loud."""
    print("Speaking response...")  # Debugging step
    engine = pyttsx3.init()
    
    # Ensure speech rate & volume are properly set
    engine.setProperty("rate", 170)  # Adjust speed (default is ~200)
    engine.setProperty("volume", 1.0)  # Max volume

    voices = engine.getProperty("voices")
    engine.setProperty("voice", voices[151].id)  # Use default voice (can be adjusted)

    engine.say(text)
    engine.runAndWait()  # Ensures it speaks before moving on

def chatbot():
    audio_file = record_audio()
    question = transcribe_audio(audio_file)
    print("You asked:", question)
    
    answer = app.generate_response(question)  # Using the chatbot function from app.py
    print("Chatbot Response:", answer)
    
    speak_text(answer)  # Read out the chatbot's response

if __name__ == "__main__":
    chatbot()
