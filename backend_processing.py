# backend_processing.py - RAG-POWERED VERSION
import pandas as pd
import numpy as np
import joblib
import os
import faiss
import re
from collections import Counter
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import json

LLM_MODEL_NAME = "models/gemini-1.5-flash" # Use a specific model name if 'gemini-pro' is not found

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
ARTIFACTS_DIR = 'model_outputs/'
K_NEIGHBORS = 15

# LLM Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("❌ GOOGLE_API_KEY not found. Please set it in your .env file.")
    llm = None # Set LLM to None if API key is missing
else:
    llm = ChatGoogleGenerativeAI(model=LLM_MODEL_NAME, google_api_key=GOOGLE_API_KEY, temperature=0.3)

# NEW: MEDICAL RULES FOR CRITICAL OVERRIDES
CRITICAL_RULES = [
    {"symptoms": ["chest pain", "chest discomfort"], "history": ["heart disease", "myocardial infarction", "angina", "cardiac", "coronary"], "override_risk": "High Risk", "reason": "Chest pain with a history of heart disease requires immediate evaluation."},
    {"symptoms": ["shortness of breath", "difficulty breathing", "wheezing"], "history": ["asthma", "copd", "emphysema", "respiratory"], "override_risk": "High Risk", "reason": "Respiratory distress with a history of lung disease requires immediate evaluation."},
    {"symptoms": ["severe headache", "worst headache"], "history": ["hypertension", "high blood pressure", "aneurysm", "stroke"], "override_risk": "High Risk", "reason": "A severe headache with a cardiovascular history requires immediate evaluation."},
    # Add more critical rules as needed
]

# IMPROVED SYMPTOM MAPPING - Critical for rural users
SYMPTOM_KEYWORD_MAP = {
    # Dizziness and related terms
    'dizziness': ['dizzy', 'lightheaded', 'vertigo', 'spinning', 'balance_problem'],
    'dizzy': ['dizzy', 'lightheaded', 'vertigo', 'spinning', 'balance_problem'],
    'chakkar': ['dizzy', 'lightheaded', 'vertigo', 'spinning', 'balance_problem'],  # Hindi/Marathi
    
    # Fever terms
    'fever': ['fever', 'high_temperature', 'chills'],
    'bukhar': ['fever', 'high_temperature', 'chills'],  # Hindi/Marathi
    'taap': ['fever', 'high_temperature', 'chills'],
    
    # Pain terms
    'headache': ['headache', 'head_pain'],
    'sir_dard': ['headache', 'head_pain'],  # Hindi
    'stomach_pain': ['abdominal_pain', 'stomach_ache'],
    'pet_dard': ['abdominal_pain', 'stomach_ache'],  # Hindi
    
    # Breathing issues
    'breathing_problem': ['dyspnea', 'shortness_of_breath', 'chest_tightness'],
    'saans_ki_problem': ['dyspnea', 'shortness_of_breath', 'chest_tightness'],
    
    # Common rural complaints
    'weakness': ['fatigue', 'weakness', 'tired'],
    'kamjori': ['fatigue', 'weakness', 'tired'],  # Hindi/Marathi
    'loose_motion': ['diarrhea', 'loose_stools'],
    'dast': ['diarrhea', 'loose_stools'],  # Hindi
    'vomiting': ['nausea', 'vomiting', 'throwing_up'],
    'ulti': ['nausea', 'vomiting', 'throwing_up'],  # Hindi
}

# RURAL-SPECIFIC DISEASE PATTERNS
RURAL_DISEASE_CONTEXT = {
    'High Risk': {
        'common_in_rural': ['Malaria', 'Dengue', 'Pneumonia', 'Tuberculosis'],
        'urgent_symptoms': ['high_fever_with_chills', 'severe_breathing_difficulty', 'chest_pain']
    },
    'Moderate Risk': {
        'common_in_rural': ['Gastroenteritis', 'Anemia', 'Dehydration'],
        'watch_symptoms': ['persistent_fever', 'severe_weakness', 'dehydration']
    }
}

# LLM Prompt Template for RAG
rag_prompt_template = PromptTemplate(
    input_variables=["user_symptoms", "user_history", "user_age", "user_sex", "similar_cases_context", "rural_context"],
    template="""
    You are an AI Medical Expert for a Health Triage System. Your goal is to provide a comprehensive and trustworthy health assessment. 
    Consider the user's details and relevant medical cases to generate a precise risk level, a detailed medical reasoning, 
    and a list of possible diseases in layman's terms. Your output MUST be in a JSON format with keys: 
    'risk_level', 'reason', 'possible_diseases' (a list of strings), and 'confidence' (a float between 0.0 and 1.0).

    User's Current Symptoms: {user_symptoms}
    User's Past Medical History: {user_history}
    User's Age: {user_age}
    User's Sex: {user_sex}

    Similar Medical Cases from Database (for context and reasoning):
    {similar_cases_context}

    Additional Rural Context: {rural_context}

    Based on the above information, acting as a medical expert, provide your assessment:
    """
)

# LLM Chain
if llm:
    rag_chain = LLMChain(llm=llm, prompt=rag_prompt_template)
else:
    rag_chain = None # No LLMChain if LLM not initialized

# =======================================
# 1. LOAD ALL ARTIFACTS ON STARTUP
# =======================================
try:
    print("Loading all AI model artifacts for Similarity Search...")
    index = faiss.read_index(os.path.join(ARTIFACTS_DIR, 'patient_library.index'))
    y_library_encoded = np.load(os.path.join(ARTIFACTS_DIR, 'patient_library_labels.npy'), allow_pickle=True)
    y_pathologies = np.load(os.path.join(ARTIFACTS_DIR, 'patient_library_pathologies.npy'), allow_pickle=True)
    le = joblib.load(os.path.join(ARTIFACTS_DIR, 'risk_label_encoder.pkl'))
    mlb = joblib.load(os.path.join(ARTIFACTS_DIR, 'symptom_encoder.pkl'))
    tfidf = joblib.load(os.path.join(ARTIFACTS_DIR, 'tfidf_model.pkl'))
    svd = joblib.load(os.path.join(ARTIFACTS_DIR, 'svd_model.pkl'))
    feature_columns = joblib.load(os.path.join(ARTIFACTS_DIR, 'final_feature_columns.pkl'))
    symptom_map = joblib.load(os.path.join(ARTIFACTS_DIR, 'symptom_map.pkl'))
    risk_labels_map = {i: label for i, label in enumerate(le.classes_)}
    
    try:
        layman_map = joblib.load(os.path.join(ARTIFACTS_DIR, 'layman_map.pkl'))
    except:
        layman_map = {}
    
    ARTIFACTS = {
        'index': index,
        'y_library_encoded': y_library_encoded,
        'y_pathologies': y_pathologies,
        'le': le,
        'mlb': mlb,
        'tfidf': tfidf,
        'svd': svd,
        'feature_columns': feature_columns,
        'symptom_map': symptom_map,
        'risk_labels_map': risk_labels_map,
        'layman_map': layman_map
    }
    print("✅ All artifacts loaded successfully.")
    ARTIFACTS_LOADED = True
except FileNotFoundError as e:
    print(f"❌ Error loading artifacts: {e}. Please ensure train.py has been run successfully.")
    ARTIFACTS_LOADED = False
except Exception as e:
    print(f"Error loading model artifacts: {e}")
    ARTIFACTS_LOADED = False

def improved_symptom_extraction(symptoms_text, past_history, report_data):
    """IMPROVED symptom extraction with better mapping"""
    all_symptoms = []
    
    if symptoms_text:
        text_lower = symptoms_text.lower()
        for user_term, medical_codes in SYMPTOM_KEYWORD_MAP.items():
            if user_term in text_lower:
                all_symptoms.extend(medical_codes)
        basic_symptoms = re.findall(r'\b(?:pain|fever|headache|nausea|cough|weakness|fatigue|dizzy|vomit)\b', text_lower)
        all_symptoms.extend(basic_symptoms)
    
    if past_history:
        condition_symptoms = {
            'Diabetes': ['glucose_high', 'frequent_urination', 'excessive_thirst'],
            'Hypertension (High BP)': ['high_blood_pressure', 'headache'],
            'Asthma': ['breathing_difficulty', 'wheezing', 'cough'],
            'Heart Disease': ['chest_pain', 'shortness_of_breath'],
            'Anemia': ['fatigue', 'weakness', 'pale_skin'],
            'Thyroid Issues': ['fatigue', 'weight_changes']
        }
        for condition in past_history:
            if condition in condition_symptoms:
                all_symptoms.extend(condition_symptoms[condition])
    
    if report_data:
        for key, value in report_data.items():
            if 'hemoglobin' in key.lower() and 'low' in str(value).lower():
                all_symptoms.extend(['anemia', 'fatigue', 'weakness'])
            elif 'glucose' in key.lower() and 'high' in str(value).lower():
                all_symptoms.extend(['diabetes', 'high_glucose'])
    
    return list(set(all_symptoms))  # Remove duplicates

def create_realistic_features(session_data, user_profile, artifacts):
    """Create more realistic feature vectors"""
    try:
        symptom_keywords = improved_symptom_extraction(
            session_data.get('current_symptoms_text', ''),
            session_data.get('past_history', []),
            session_data.get('report_data', {}).get('structured_data', {})
        )
        
        evidence_codes = []
        for symptom in symptom_keywords[:5]:
            if symptom in artifacts['symptom_map'].values():
                for code, name in artifacts['symptom_map'].items():
                    if name.lower().replace('_', ' ') == symptom.replace('_', ' '):
                        evidence_codes.append(code)
                        break
        
        patient_data = {
            'AGE': [user_profile['age']],
            'SEX': [user_profile.get('sex', 'F')],
            'EVIDENCES_LIST': [evidence_codes]
        }
        
        df_patient = pd.DataFrame(patient_data)
        df_patient['AGE'] = df_patient['AGE'].fillna(35)
        df_patient['symptom_text'] = [' '.join(symptom_keywords)]
        
        symptom_features = artifacts['mlb'].transform(df_patient['EVIDENCES_LIST'])
        df_symptoms = pd.DataFrame(symptom_features, columns=artifacts['mlb'].classes_)
        
        text_features_tfidf = artifacts['tfidf'].transform(df_patient['symptom_text'])
        contextual_features = artifacts['svd'].transform(text_features_tfidf)
        df_context = pd.DataFrame(contextual_features, columns=[f'context_{i}' for i in range(100)])
        
        sex_encoded = pd.get_dummies(df_patient['SEX'], drop_first=True, prefix='SEX')
        if 'SEX_M' not in sex_encoded.columns:
            sex_encoded['SEX_M'] = 0
            
        X_patient_unaligned = pd.concat([df_patient['AGE'], sex_encoded[['SEX_M']], df_symptoms, df_context], axis=1)
        X_patient_aligned = X_patient_unaligned.reindex(columns=artifacts['feature_columns'], fill_value=0)
        
        return X_patient_aligned.values.astype('float32')
        
    except Exception as e:
        print(f"Error creating patient features: {e}")
        return None

def check_critical_rules(current_symptoms_text: str, past_history_list: list) -> dict or None:
    """ Checks if the current case triggers any critical medical rules. """
    current_symptoms_lower = current_symptoms_text.lower()
    past_history_lower = " ".join(past_history_list).lower()

    for rule in CRITICAL_RULES:
        symptom_match = any(symptom in current_symptoms_lower for symptom in rule["symptoms"])
        history_match = any(history in past_history_lower for history in rule["history"])
        
        if symptom_match and history_match:
            return {
                "risk_level": rule["override_risk"],
                "reason": rule["reason"],
                "confidence": 1.0, 
                "possible_diseases": [rule.get("possible_disease", "Critical Condition")], # Changed to possible_diseases
                "similar_cases": {"Note": "Decision based on a critical medical safety rule."} # Retained for now
            }
    return None


def run_prediction_engine(session_data: dict, user_profile: dict) -> dict:
    """
    RAG-powered prediction engine for detailed health assessment.
    """
    if not ARTIFACTS_LOADED or not llm:
        return {'risk_level': 'Error', 'reason': 'AI system not fully initialized.', 'possible_diseases': []}

    current_symptoms_text = session_data.get('current_symptoms_text', '')
    past_history_list = session_data.get('past_history', [])

    # --- Step 1: Safety First - Check Critical Rules ---
    rule_override = check_critical_rules(current_symptoms_text, past_history_list)
    if rule_override:
        return rule_override # Immediately return if a critical rule is met

    # --- Step 2: Retrieve Similar Cases (The "R" in RAG) ---
    patient_features = create_realistic_features(session_data, user_profile, ARTIFACTS)
    if patient_features is None:
        return {'risk_level': 'Moderate Risk', 'reason': 'Could not process symptoms.', 'possible_diseases': ['Symptom Processing Issue']}

    faiss.normalize_L2(patient_features)
    distances, top_k_indices = ARTIFACTS['index'].search(patient_features, K_NEIGHBORS)
    
    similar_cases_context = []
    for i, idx in enumerate(top_k_indices[0]):
        pathology = ARTIFACTS['y_pathologies'][idx]
        risk = ARTIFACTS['risk_labels_map'][ARTIFACTS['y_library_encoded'][idx]]
        layman_term = ARTIFACTS['layman_map'].get(pathology, pathology)
        similar_cases_context.append(
            f"- A past case with similar symptoms was diagnosed with '{layman_term}', a '{risk}' condition."
        )
    similar_cases_context_str = "\n".join(similar_cases_context)

    # --- Step 3: Generate the Final Analysis (The "G" in RAG) ---
    llm_input = {
        "user_symptoms": current_symptoms_text or "Not provided.",
        "user_history": ", ".join(past_history_list) or "None",
        "user_age": user_profile.get('age', 'N/A'),
        "user_sex": user_profile.get('sex', 'N/A'),
        "similar_cases_context": similar_cases_context_str,
        "rural_context": "Consider conditions common in rural India like Malaria, Dengue, and Pneumonia."
    }

    try:
        llm_response = rag_chain.run(llm_input)
        print(f"LLM Raw Response: {llm_response}") # For debugging
        
        # Use the robust parser
        parsed_output = _parse_llm_json_response(llm_response)
        
        # Add the retrieved cases for display in the UI
        parsed_output["similar_cases"] = {
            "Similarity": [f"{distances[0][i]*100:.0f}%" for i in range(5)],
            "Risk Level": [ARTIFACTS['risk_labels_map'][ARTIFACTS['y_library_encoded'][idx]] for idx in top_k_indices[0][:5]],
            "Condition in Similar Case": [ARTIFACTS['layman_map'].get(ARTIFACTS['y_pathologies'][idx], ARTIFACTS['y_pathologies'][idx]) for idx in top_k_indices[0][:5]]
        }
        return parsed_output

    except Exception as e:
        print(f"❌ Error during RAG pipeline: {e}")
        return {
            'risk_level': 'Moderate Risk', 
            'reason': f"AI system encountered an error: {e}. Please consult a healthcare provider.",
            'possible_diseases': ['System Error']
        }


def merge_and_extract_symptoms(symptoms_text, past_history, report_data):
    """Wrapper for backward compatibility"""
    return improved_symptom_extraction(symptoms_text, past_history, report_data)
