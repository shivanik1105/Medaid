# backend_processing.py

# A simple list of known symptoms for keyword matching.
KNOWN_SYMPTOMS = [
    "fever", "high fever", "low fever", "cough", "dry cough", "wet cough",
    "headache", "migraine", "dizziness", "nausea", "vomiting",
    "sore throat", "runny nose", "chest pain", "shortness of breath",
    "fatigue", "body ache", "weakness"
]

def extract_symptoms_from_text(text: str) -> list:
    """A simple NLP function to find known symptoms in a text string."""
    if not text:
        return []
    text = text.lower()
    found_symptoms = [symptom for symptom in KNOWN_SYMPTOMS if symptom in text]
    # Return only unique symptoms
    return list(set(found_symptoms))