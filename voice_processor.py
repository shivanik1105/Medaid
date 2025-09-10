# voice_processor.py
"""
Lightweight audio transcription wrapper.
Uses SpeechRecognition if available; otherwise provides a simple stub.
"""

import os

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except Exception:
    SR_AVAILABLE = False

class RuralVoiceProcessor:
    def __init__(self):
        pass

    def transcribe_audio(self, file_or_path):
        """
        Accepts either bytes, file-like, or path to file.
        Returns best-effort transcription string or None.
        """
        if not SR_AVAILABLE:
            return None
        r = sr.Recognizer()
        # If bytes passed in, write to temp file
        if isinstance(file_or_path, (bytes, bytearray)):
            import tempfile
            tf = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            tf.write(file_or_path); tf.flush(); tf.close()
            path = tf.name
        else:
            path = file_or_path
        try:
            with sr.AudioFile(path) as source:
                audio = r.record(source)
            text = r.recognize_google(audio, language="en-IN")
            return text
        except Exception:
            return None
        finally:
            if isinstance(file_or_path, (bytes, bytearray)):
                try: os.unlink(path)
                except: pass
