# # backend_processing.py - FIXED VERSION WITH MEDICAL VALIDATION

# import pandas as pd
# import numpy as np
# import joblib
# import os
# import faiss
# import re
# from collections import Counter
# from sklearn.preprocessing import MultiLabelBinarizer
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.decomposition import TruncatedSVD
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.prompts import PromptTemplate
# from langchain.chains import LLMChain
# from dotenv import load_dotenv
# import json
# import traceback
# from datetime import datetime

# LLM_MODEL_NAME = "models/gemini-1.5-flash"

# # Load environment variables
# load_dotenv()

# # MEDICAL VALIDATION RULES
# MEDICAL_CONSISTENCY_RULES = {
#     "gastrointestinal": ["stomach", "abdominal", "digestive", "vomit", "nausea", "diarrhea", "constipation", "indigestion"],
#     "respiratory": ["breath", "cough", "wheeze", "lungs", "asthma", "pneumonia", "bronchitis", "laryngo"],
#     "cardiac": ["chest", "heart", "cardiac", "angina", "pressure", "palpitation"],
#     "neurological": ["head", "brain", "migraine", "seizure", "dizzy", "vertigo", "confusion"],
#     "musculoskeletal": ["pain", "ache", "joint", "muscle", "bone", "arthritis", "sprain"]
# }

# def validate_medical_consistency(diseases, reasoning):
#     """
#     Validate that the medical reasoning is consistent with the listed diseases
#     Returns (is_valid, validation_message)
#     """
#     reasoning_lower = reasoning.lower()
#     diseases_lower = " ".join(diseases).lower()
    
#     # Check if reasoning mentions diseases that aren't in the list
#     mentioned_conditions = []
#     for disease_category, keywords in MEDICAL_CONSISTENCY_RULES.items():
#         if any(keyword in reasoning_lower for keyword in keywords):
#             mentioned_conditions.append(disease_category)
    
#     # Check if mentioned conditions align with diagnosed diseases
#     consistency_issues = []
#     for condition in mentioned_conditions:
#         if not any(keyword in diseases_lower for keyword in MEDICAL_CONSISTENCY_RULES[condition]):
#             consistency_issues.append(f"Reasoning mentions {condition} issues but no {condition} diseases are listed")
    
#     if consistency_issues:
#         return False, " | ".join(consistency_issues)
    
#     return True, "Medical reasoning is consistent with diagnosed conditions"
# # Add to CRITICAL RULES section
# LOW_RISK_RULES = [
#     {
#         "symptoms": ["stomach pain", "stomach ache", "pet dard", "abdominal pain"],
#         "absence_of": ["fever", "vomit", "vomiting", "blood", "bleeding", "severe", "sharp", "unbearable"],
#         "override_risk": "Low Risk",
#         "reason": "Isolated stomach pain without fever, vomiting, or bleeding is often minor indigestion, gas, or a mild stomach bug that can be managed with rest, hydration, and over-the-counter remedies.",
#         "possible_diseases": ["Indigestion", "Gas", "Mild Gastritis", "Abdominal Muscle Strain"]
#     },
#     {
#         "symptoms": ["headache", "sir dard"],
#         "absence_of": ["severe", "worst", "thunderclap", "vomit", "vomiting", "vision", "confusion", "numbness"],
#         "override_risk": "Low Risk",
#         "reason": "Common headache without severe, neurological, or vomiting symptoms is often tension-related or due to dehydration, fatigue, or stress.",
#         "possible_diseases": ["Tension Headache", "Dehydration", "Eye Strain", "Stress"]
#     },
#     {
#         "symptoms": ["cough", "khansi"],
#         "absence_of": ["fever", "breath", "shortness", "chest pain", "blood", "wheezing"],
#         "override_risk": "Low Risk",
#         "reason": "Isolated cough without fever or breathing difficulties is often a mild respiratory irritation, post-nasal drip, or the tail end of a cold.",
#         "possible_diseases": ["Common Cold", "Post-Nasal Drip", "Allergic Cough", "Throat Irritation"]
#     }
# ]

# def check_low_risk_rules(current_symptoms_text: str) -> dict or None:
#     """
#     Check if symptoms clearly match a common, low-risk condition.
#     Returns a Low Risk assessment if they do, otherwise None.
#     """
#     current_symptoms_lower = current_symptoms_text.lower()
    
#     for rule in LOW_RISK_RULES:
#         # Check if main symptom is present
#         symptom_match = any(symptom in current_symptoms_lower for symptom in rule["symptoms"])
        
#         # Check that NO high-risk symptoms are present
#         absence_match = not any(absent_symptom in current_symptoms_lower for absent_symptom in rule["absence_of"])
        
#         if symptom_match and absence_match:
#             return {
#                 "risk_level": rule["override_risk"],
#                 "reason": rule["reason"],
#                 "confidence": 0.8, 
#                 "possible_diseases": rule["possible_diseases"],
#                 "similar_cases": {"Note": "Decision based on low-risk symptom pattern."}
#             }
#     return None
# def generate_clarifying_questions(final_symptom_set, user_history):
#     """Generate targeted questions based on symptoms and history"""
#     questions = []
    
#     # Only ask questions if we have very limited information
#     symptom_keywords = [symptom.lower() for symptom in final_symptom_set]
    
#     # Only generate questions if we have fewer than 3 symptoms
#     if len(symptom_keywords) < 3:
#         if any(symptom in symptom_keywords for symptom in ['fever', 'temperature', 'bukhar']):
#             if not any(keyword in symptom_keywords for keyword in ['duration', 'day', 'how long']):
#                 questions.append("How long have you had fever?")
#             if not any(keyword in symptom_keywords for keyword in ['temperature', 'degree']):
#                 questions.append("What is your current temperature?")
        
#         if any(symptom in symptom_keywords for symptom in ['pain', 'ache', 'dard']):
#             if not any(keyword in symptom_keywords for keyword in ['scale', 'severity', '1-10']):
#                 questions.append("On a scale of 1-10, how severe is your pain?")
#             if not any(keyword in symptom_keywords for keyword in ['location', 'where']):
#                 questions.append("Where exactly is the pain located?")
    
#     # Return questions only if we really need more info
#     return questions if len(symptom_keywords) < 2 else []

# # --- CONFIGURATION ---
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# ARTIFACTS_DIR = os.path.join(BASE_DIR, 'model_outputs')

# K_NEIGHBORS = 15

# # LLM Configuration
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# if not GOOGLE_API_KEY:
#     print("❌ GOOGLE_API_KEY not found. Please set it in your .env file.")
#     llm = None
# else:
#     llm = ChatGoogleGenerativeAI(model=LLM_MODEL_NAME, google_api_key=GOOGLE_API_KEY, temperature=0.3)

# # CRITICAL RULES FOR HIGH-RISK OVERRIDES
# CRITICAL_RULES = [
#     {"symptoms": ["chest pain", "chest discomfort", "pressure chest"], "history": ["heart disease", "myocardial infarction", "angina", "cardiac", "coronary"], "override_risk": "High Risk", "reason": "Chest pain with a history of heart disease requires immediate evaluation."},
#     {"symptoms": ["shortness of breath", "difficulty breathing", "wheezing", "cannot breathe"], "history": ["asthma", "copd", "emphysema", "respiratory"], "override_risk": "High Risk", "reason": "Respiratory distress with a history of lung disease requires immediate evaluation."},
#     {"symptoms": ["severe headache", "worst headache", "thunderclap headache"], "history": ["hypertension", "high blood pressure", "aneurysm", "stroke"], "override_risk": "High Risk", "reason": "A severe headache with a cardiovascular history requires immediate evaluation."},
#     {"symptoms": ["uncontrolled bleeding", "heavy bleeding", "bleeding won't stop"], "history": [], "override_risk": "High Risk", "reason": "Uncontrolled bleeding requires immediate medical attention."},
#     {"symptoms": ["fainting", "lost consciousness", "passed out"], "history": [], "override_risk": "High Risk", "reason": "Loss of consciousness requires urgent medical evaluation."},
# ]

# # IMPROVED SYMPTOM MAPPING
# SYMPTOM_KEYWORD_MAP = {
#     'dizziness': ['dizzy', 'lightheaded', 'vertigo', 'spinning', 'balance_problem'],
#     'dizzy': ['dizzy', 'lightheaded', 'vertigo', 'spinning', 'balance_problem'],
#     'chakkar': ['dizzy', 'lightheaded', 'vertigo', 'spinning', 'balance_problem'],
#     'fever': ['fever', 'high_temperature', 'chills'],
#     'bukhar': ['fever', 'high_temperature', 'chills'],
#     'taap': ['fever', 'high_temperature', 'chills'],
#     'headache': ['headache', 'head_pain'],
#     'sir_dard': ['headache', 'head_pain'],
#     'stomach_pain': ['abdominal_pain', 'stomach_ache'],
#     'pet_dard': ['abdominal_pain', 'stomach_ache'],
#     'breathing_problem': ['dyspnea', 'shortness_of_breath', 'chest_tightness'],
#     'saans_ki_problem': ['dyspnea', 'shortness_of_breath', 'chest_tightness'],
#     'weakness': ['fatigue', 'weakness', 'tired'],
#     'kamjori': ['fatigue', 'weakness', 'tired'],
#     'loose_motion': ['diarrhea', 'loose_stools'],
#     'dast': ['diarrhea', 'loose_stools'],
#     'vomiting': ['nausea', 'vomiting', 'throwing_up'],
#     'ulti': ['nausea', 'vomiting', 'throwing_up'],
#     'body_pain': ['body_ache', 'muscle_pain', 'joint_pain'],
#     'badan_dard': ['body_ache', 'muscle_pain', 'joint_pain'],
#     'cough': ['cough', 'dry_cough', 'productive_cough'],
#     'khansi': ['cough', 'dry_cough', 'productive_cough'],
# }

# # ENHANCED LLM PROMPT TEMPLATE WITH STRICTER GUIDELINES
# rag_prompt_template = PromptTemplate(
#     input_variables=["user_symptoms", "user_history", "user_age", "user_sex", "similar_cases_context", "rural_context", "current_date"],
#     template="""
# You are an AI Medical Expert for a Health Triage System. Based on the provided information, give a comprehensive medical assessment.

# CRITICAL INSTRUCTIONS:
# 1. Your medical reasoning MUST directly support and explain the conditions listed in possible_diseases.
# 2. DO NOT introduce conditions in the reasoning that are not in the possible_diseases list.
# 3. If the retrieved cases are contradictory, acknowledge this and explain why you are prioritizing certain symptoms or conditions.
# 4. Focus on the most likely explanations based on symptom patterns.
# 5. Your response must be medically coherent and consistent.

# User Information:
# - Current Symptoms: {user_symptoms}
# - Past Medical History: {user_history}
# - Age: {user_age}
# - Sex: {user_sex}
# - Assessment Date: {current_date}

# Similar Medical Cases from Database:
# {similar_cases_context}

# Rural Healthcare Context: {rural_context}

# Provide your assessment as a JSON object with these exact keys:
# - "risk_level": Must be exactly one of ["Low Risk", "Moderate Risk", "High Risk"]
# - "reason": Detailed medical reasoning (2-3 sentences explaining your assessment)
# - "possible_diseases": Array of 3-5 disease names in simple terms
# - "confidence": Number between 0.0 and 1.0

# Example of GOOD response:
# {{"risk_level": "Moderate Risk", "reason": "The combination of fever and body pain suggests a viral infection. Given the patient's age and symptoms, monitoring is recommended.", "possible_diseases": ["Viral Fever", "Flu", "Common Cold"], "confidence": 0.8}}

# Example of BAD response (DO NOT DO THIS):
# {{"risk_level": "Moderate Risk", "reason": "Your stomach pain could be related to laryngospasm in your throat.", "possible_diseases": ["Stomach ache", "Gas", "Gastroenteritis"], "confidence": 0.8}}

# Your response must be ONLY the JSON object, no other text.
# """
# )

# # LLM Chain
# if llm:
#     rag_chain = LLMChain(llm=llm, prompt=rag_prompt_template)
# else:
#     rag_chain = None

# # =======================================
# # LOAD ARTIFACTS
# # =======================================
# def load_artifacts():
#     """Load all required model artifacts with enhanced error handling"""
#     global ARTIFACTS_LOADED, ARTIFACTS
    
#     try:
#         print("Loading all AI model artifacts for Similarity Search...")
        
#         if not os.path.exists(ARTIFACTS_DIR):
#             print(f"❌ Artifacts directory '{ARTIFACTS_DIR}' not found.")
#             ARTIFACTS_LOADED = False
#             return False
        
#         artifacts_to_load = {
#             'index': lambda: faiss.read_index(os.path.join(ARTIFACTS_DIR, 'patient_library.index')),
#             'y_library_encoded': lambda: np.load(os.path.join(ARTIFACTS_DIR, 'patient_library_labels.npy'), allow_pickle=True),
#             'y_pathologies': lambda: np.load(os.path.join(ARTIFACTS_DIR, 'patient_library_pathologies.npy'), allow_pickle=True),
#             'le': lambda: joblib.load(os.path.join(ARTIFACTS_DIR, 'risk_label_encoder.pkl')),
#             'mlb': lambda: joblib.load(os.path.join(ARTIFACTS_DIR, 'symptom_encoder.pkl')),
#             'tfidf': lambda: joblib.load(os.path.join(ARTIFACTS_DIR, 'tfidf_model.pkl')),
#             'svd': lambda: joblib.load(os.path.join(ARTIFACTS_DIR, 'svd_model.pkl')),
#             'feature_columns': lambda: joblib.load(os.path.join(ARTIFACTS_DIR, 'final_feature_columns.pkl')),
#             'symptom_map': lambda: joblib.load(os.path.join(ARTIFACTS_DIR, 'symptom_map.pkl'))
#         }
        
#         ARTIFACTS = {}
#         for name, loader in artifacts_to_load.items():
#             try:
#                 ARTIFACTS[name] = loader()
#                 print(f"✅ Loaded {name}")
#             except FileNotFoundError:
#                 print(f"❌ Missing artifact: {name}")
#                 if name in ['le', 'mlb', 'feature_columns', 'symptom_map']:
#                     ARTIFACTS_LOADED = False
#                     return False
        
#         ARTIFACTS['risk_labels_map'] = {i: label for i, label in enumerate(ARTIFACTS['le'].classes_)}
        
#         try:
#             ARTIFACTS['layman_map'] = joblib.load(os.path.join(ARTIFACTS_DIR, 'layman_map.pkl'))
#         except:
#             ARTIFACTS['layman_map'] = {}
#             print("⚠️  Layman map not found, using empty mapping")
        
#         ARTIFACTS_LOADED = True
#         print("✅ All artifacts loaded successfully.")
#         return True
        
#     except Exception as e:
#         print(f"❌ Error loading artifacts: {e}")
#         traceback.print_exc()
#         ARTIFACTS_LOADED = False
#         return False

# ARTIFACTS_LOADED = load_artifacts() 

# def fallback_prediction(session_data, user_profile):
#     """Provide a basic prediction when the main system isn't fully operational"""
#     symptoms = session_data.get('current_symptoms_text', '').lower()
#     history = session_data.get('past_history', [])
    
#     # Enhanced fallback logic
#     high_risk_terms = ['chest pain', 'difficulty breathing', 'severe bleeding', 'fainting', 'severe headache', 'unconscious']
#     moderate_risk_terms = ['fever', 'pain', 'vomiting', 'dizziness', 'weakness', 'cough']
    
#     for term in high_risk_terms:
#         if term in symptoms:
#             return {
#                 "risk_level": "High Risk",
#                 "reason": "Critical symptoms detected. This requires immediate medical attention from a qualified healthcare provider.",
#                 "confidence": 0.85,
#                 "possible_diseases": ["Emergency Medical Condition", "Acute Illness", "Critical Condition"],
#                 "similar_cases": {"Note": "Emergency assessment - seek immediate care"}
#             }
    
#     for term in moderate_risk_terms:
#         if term in symptoms:
#             return {
#                 "risk_level": "Moderate Risk",
#                 "reason": "Your symptoms suggest a medical condition that requires evaluation. Please consult with a healthcare provider within 24-48 hours.",
#                 "confidence": 0.75,
#                 "possible_diseases": ["Viral Infection", "Bacterial Infection", "Common Illness"],
#                 "similar_cases": {"Note": "Basic assessment - consult doctor for proper evaluation"}
#             }
    
#     return {
#         "risk_level": "Low Risk",
#         "reason": "No significant concerning symptoms reported. Continue monitoring your health and maintain regular checkups.",
#         "confidence": 0.8,
#         "possible_diseases": ["No Specific Condition", "General Health Maintenance"],
#         "similar_cases": {"Note": "Preventive care recommended"}
#     }

# def improved_symptom_extraction(symptoms_text, past_history, report_data):
#     """IMPROVED symptom extraction with better mapping"""
#     all_symptoms = []
    
#     if symptoms_text:
#         text_lower = symptoms_text.lower()
#         # Map user terms to medical codes
#         for user_term, medical_codes in SYMPTOM_KEYWORD_MAP.items():
#             if user_term in text_lower:
#                 all_symptoms.extend(medical_codes)
#         # Extract basic symptoms
#         basic_symptoms = re.findall(r'\b(?:pain|fever|headache|nausea|cough|weakness|fatigue|dizzy|vomit|ache|cold|flu|bleeding|breath|shortness)\b', text_lower)
#         all_symptoms.extend(basic_symptoms)
    
#     # Add symptoms based on history
#     if past_history:
#         condition_symptoms = {
#             'Diabetes': ['glucose_high', 'frequent_urination', 'excessive_thirst'],
#             'Hypertension (High BP)': ['high_blood_pressure', 'headache'],
#             'Asthma': ['breathing_difficulty', 'wheezing', 'cough'],
#             'Heart Disease': ['chest_pain', 'shortness_of_breath'],
#             'Anemia': ['fatigue', 'weakness', 'pale_skin'],
#             'Thyroid Issues': ['fatigue', 'weight_changes']
#         }
#         for condition in past_history:
#             if condition in condition_symptoms:
#                 all_symptoms.extend(condition_symptoms[condition])
    
#     # Add symptoms from report data
#     if report_data:
#         for key, value in report_data.items():
#             if 'hemoglobin' in key.lower() and 'low' in str(value).lower():
#                 all_symptoms.extend(['anemia', 'fatigue', 'weakness'])
#             elif 'glucose' in key.lower() and 'high' in str(value).lower():
#                 all_symptoms.extend(['diabetes', 'high_glucose'])
    
#     return list(set(all_symptoms))

# def create_realistic_features(session_data, user_profile, artifacts):
#     """Create feature vectors for similarity search"""
#     try:
#         symptom_keywords = improved_symptom_extraction(
#             session_data.get('current_symptoms_text', ''),
#             session_data.get('past_history', []),
#             session_data.get('report_data', {}).get('structured_data', {})
#         )
        
#         evidence_codes = []
#         for symptom in symptom_keywords[:5]:
#             if symptom in artifacts['symptom_map'].values():
#                 for code, name in artifacts['symptom_map'].items():
#                     if name.lower().replace('_', ' ') == symptom.replace('_', ' '):
#                         evidence_codes.append(code)
#                         break
        
#         patient_data = {
#             'AGE': [user_profile['age']],
#             'SEX': [user_profile.get('sex', 'F')],
#             'EVIDENCES_LIST': [evidence_codes]
#         }
        
#         df_patient = pd.DataFrame(patient_data)
#         df_patient['AGE'] = df_patient['AGE'].fillna(35)
#         df_patient['symptom_text'] = [' '.join(symptom_keywords)]
        
#         symptom_features = artifacts['mlb'].transform(df_patient['EVIDENCES_LIST'])
#         df_symptoms = pd.DataFrame(symptom_features, columns=artifacts['mlb'].classes_)
        
#         text_features_tfidf = artifacts['tfidf'].transform(df_patient['symptom_text'])
#         contextual_features = artifacts['svd'].transform(text_features_tfidf)
#         df_context = pd.DataFrame(contextual_features, columns=[f'context_{i}' for i in range(100)])
        
#         sex_encoded = pd.get_dummies(df_patient['SEX'], drop_first=True, prefix='SEX')
#         if 'SEX_M' not in sex_encoded.columns:
#             sex_encoded['SEX_M'] = 0
            
#         X_patient_unaligned = pd.concat([df_patient['AGE'], sex_encoded[['SEX_M']], df_symptoms, df_context], axis=1)
#         X_patient_aligned = X_patient_unaligned.reindex(columns=artifacts['feature_columns'], fill_value=0)
        
#         return X_patient_aligned.values.astype('float32')
        
#     except Exception as e:
#         print(f"Error creating patient features: {e}")
#         return None

# def check_critical_rules(current_symptoms_text: str, past_history_list: list) -> dict or None:
#     """Check if the current case triggers any critical medical rules"""
#     current_symptoms_lower = current_symptoms_text.lower()
#     past_history_lower = " ".join(past_history_list).lower()

#     for rule in CRITICAL_RULES:
#         symptom_match = any(symptom in current_symptoms_lower for symptom in rule["symptoms"])
#         history_match = any(history in past_history_lower for history in rule["history"])
        
#         if symptom_match and history_match:
#             return {
#                 "risk_level": rule["override_risk"],
#                 "reason": rule["reason"],
#                 "confidence": 1.0, 
#                 "possible_diseases": ["Critical Condition", "Emergency", "Requires Immediate Care"],
#                 "similar_cases": {"Note": "Decision based on critical medical safety rule."}
#             }
#     return None

# def run_prediction_engine(session_data: dict, user_profile: dict, clarification_answers: dict = None) -> dict:
#     """
#     FIXED: RAG-powered prediction engine with medical consistency validation
#     """
#     # Merge clarification answers with symptoms
#     if clarification_answers:
#         symptoms_text = session_data.get('current_symptoms_text', '')
#         for question, answer in clarification_answers.items():
#             symptoms_text += f". {answer}"
#         session_data['current_symptoms_text'] = symptoms_text

#     # Extract symptoms first
#     final_symptom_set = improved_symptom_extraction(
#         session_data.get('current_symptoms_text', ''),
#         session_data.get('past_history', []),
#         session_data.get('report_data', {}).get('structured_data', {})
#     )

#     # ONLY ask for clarification if we have almost no information
#     clarifying_questions = generate_clarifying_questions(final_symptom_set, session_data.get('past_history', []))
#     current_symptoms_text = session_data.get('current_symptoms_text', '')
    
#     # Skip clarification if we have enough information OR if user already provided symptoms
#     if clarifying_questions and len(current_symptoms_text.strip()) < 10:
#         return {
#             "status": "need_clarification",
#             "questions": clarifying_questions,
#             "risk_level": "Pending",
#             "reason": "Need additional information for accurate assessment"
#         }
    
#     # Use fallback if system not fully loaded
#     if not ARTIFACTS_LOADED or not llm:
#         print("⚠️ AI system not fully initialized. Using enhanced fallback prediction.")
#         return fallback_prediction(session_data, user_profile)

#     current_symptoms_text = session_data.get('current_symptoms_text', '')
#     past_history_list = session_data.get('past_history', [])

#     # Step 1: Check Critical Rules
#     rule_override = check_critical_rules(current_symptoms_text, past_history_list)
#     if rule_override:
#         return rule_override

#     # Step 2: Retrieve Similar Cases
#     try:
#         patient_features = create_realistic_features(session_data, user_profile, ARTIFACTS)
#         if patient_features is None:
#             return fallback_prediction(session_data, user_profile)

#         faiss.normalize_L2(patient_features)
#         distances, top_k_indices = ARTIFACTS['index'].search(patient_features, K_NEIGHBORS)
        
#         similar_cases_context = []
#         for i, idx in enumerate(top_k_indices[0][:5]):  # Use top 5 for context
#             pathology = ARTIFACTS['y_pathologies'][idx]
#             risk = ARTIFACTS['risk_labels_map'][ARTIFACTS['y_library_encoded'][idx]]
#             layman_term = ARTIFACTS['layman_map'].get(pathology, pathology)
#             similar_cases_context.append(
#                 f"Case {i+1}: Patient with similar symptoms had '{layman_term}' (Risk: {risk})"
#             )
#         similar_cases_context_str = "\n".join(similar_cases_context)

#     except Exception as e:
#         print(f"Error in similarity search: {e}")
#         return fallback_prediction(session_data, user_profile)

#     # Step 3: Generate LLM Assessment
#     try:
#         llm_input = {
#             "user_symptoms": current_symptoms_text or "Patient reporting general discomfort",
#             "user_history": ", ".join(past_history_list) or "No significant past medical history",
#             "user_age": user_profile.get('age', 'Adult'),
#             "user_sex": user_profile.get('sex', 'Not specified'),
#             "current_date": datetime.now().strftime("%Y-%m-%d"),
#             "similar_cases_context": similar_cases_context_str,
#             "rural_context": "Consider conditions common in rural areas including infectious diseases, nutritional deficiencies, and limited access to healthcare."
#         }

#         # Get LLM response
#         llm_response = rag_chain.run(llm_input)
#         print(f"LLM Raw Response: {llm_response}")
        
#         # Parse the response
#         parsed_output = _parse_llm_json_response(llm_response)
        
#         # MEDICAL CONSISTENCY VALIDATION - CRITICAL FIX
#         is_consistent, validation_msg = validate_medical_consistency(
#             parsed_output.get("possible_diseases", []),
#             parsed_output.get("reason", "")
#         )
        
#         if not is_consistent:
#             print(f"❌ Medical consistency validation failed: {validation_msg}")
#             # Fall back to a safer, more generic assessment
#             return {
#                 "risk_level": "Moderate Risk",
#                 "reason": f"Your symptoms are complex and require professional evaluation. {validation_msg} Please consult a healthcare professional for an accurate diagnosis.",
#                 "confidence": 0.6,
#                 "possible_diseases": ["Medical Evaluation Needed", "Complex Symptoms"],
#                 "similar_cases": {"Note": "Medical consistency validation failed - recommending professional evaluation"}
#             }
        
#         # Ensure we have valid risk level
#         if parsed_output.get("risk_level") not in ["Low Risk", "Moderate Risk", "High Risk"]:
#             parsed_output["risk_level"] = "Moderate Risk"
        
#         # Ensure we have diseases
#         if not parsed_output.get("possible_diseases") or len(parsed_output["possible_diseases"]) == 0:
#             parsed_output["possible_diseases"] = ["Medical Condition Requiring Evaluation", "General Health Concern"]
        
#         # Add similar cases for UI display
#         parsed_output["similar_cases"] = {
#             "Similarity": [f"{(1-distances[0][i])*100:.0f}%" for i in range(min(5, len(distances[0])))],
#             "Risk Level": [ARTIFACTS['risk_labels_map'][ARTIFACTS['y_library_encoded'][idx]] for idx in top_k_indices[0][:5]],
#             "Condition in Similar Case": [ARTIFACTS['layman_map'].get(ARTIFACTS['y_pathologies'][idx], ARTIFACTS['y_pathologies'][idx]) for idx in top_k_indices[0][:5]]
#         }
        
#         return parsed_output

#     except Exception as e:
#         print(f"❌ Error during LLM processing: {e}")
#         traceback.print_exc()
        
#         # Enhanced fallback with more context
#         result = fallback_prediction(session_data, user_profile)
#         result['reason'] = f"AI assessment based on symptoms: {result['reason']}"
        
#         try:
#             # Try to add similarity info even in fallback
#             result["similar_cases"] = {
#                 "Similarity": [f"{(1-distances[0][i])*100:.0f}%" for i in range(min(3, len(distances[0])))],
#                 "Risk Level": [ARTIFACTS['risk_labels_map'][ARTIFACTS['y_library_encoded'][idx]] for idx in top_k_indices[0][:3]],
#                 "Condition in Similar Case": [ARTIFACTS['layman_map'].get(ARTIFACTS['y_pathologies'][idx], ARTIFACTS['y_pathologies'][idx]) for idx in top_k_indices[0][:3]]
#             }
#         except:
#             result["similar_cases"] = {"Note": "Similar cases analysis unavailable"}
        
#         return result

# def _parse_llm_json_response(response_text):
#     """Parse LLM JSON response with robust fallbacks"""
#     try:
#         # Clean the response
#         response_text = response_text.strip()
        
#         # Try to find JSON in the response
#         json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
#         if json_match:
#             json_str = json_match.group()
#             parsed = json.loads(json_str)
            
#             # Validate required fields
#             if not parsed.get("risk_level") or parsed["risk_level"] not in ["Low Risk", "Moderate Risk", "High Risk"]:
#                 parsed["risk_level"] = "Moderate Risk"
            
#             if not parsed.get("reason"):
#                 parsed["reason"] = "Medical assessment suggests monitoring and potential medical consultation."
            
#             if not parsed.get("possible_diseases") or not isinstance(parsed["possible_diseases"], list):
#                 parsed["possible_diseases"] = ["Medical Condition", "Health Concern"]
            
#             if not parsed.get("confidence") or not isinstance(parsed["confidence"], (int, float)):
#                 parsed["confidence"] = 0.75
            
#             return parsed
        
#         else:
#             # No JSON found, create from text
#             risk_level = "Moderate Risk"
#             if "high risk" in response_text.lower() or "urgent" in response_text.lower():
#                 risk_level = "High Risk"
#             elif "low risk" in response_text.lower() or "mild" in response_text.lower():
#                 risk_level = "Low Risk"
            
#             return {
#                 "risk_level": risk_level,
#                 "reason": response_text[:300] + "..." if len(response_text) > 300 else response_text,
#                 "possible_diseases": ["Medical Condition", "Health Concern"],
#                 "confidence": 0.7
#             }
    
#     except json.JSONDecodeError:
#         return {
#             "risk_level": "Moderate Risk", 
#             "reason": "Medical assessment suggests consultation with healthcare provider for proper evaluation.",
#             "possible_diseases": ["Medical Condition", "Health Issue"],
#             "confidence": 0.7
#         }
#     except Exception as e:
#         print(f"Error parsing LLM response: {e}")
#         return {
#             "risk_level": "Moderate Risk",
#             "reason": "Unable to complete full assessment. Please consult with a healthcare provider.",
#             "possible_diseases": ["Medical Evaluation Needed"],
#             "confidence": 0.6
#         }

# def merge_and_extract_symptoms(symptoms_text, past_history, report_data):
#     """Wrapper for backward compatibility"""
#     return improved_symptom_extraction(symptoms_text, past_history, report_data)
    












# enhanced_conversational_backend.py - Rural-Focused Medical AI System with Proper Conversation Flow
# import pandas as pd
# import numpy as np
# import joblib
# import os
# import faiss
# import re
# from collections import Counter
# from sklearn.preprocessing import MultiLabelBinarizer
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.decomposition import TruncatedSVD
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.prompts import PromptTemplate
# from langchain.chains import LLMChain
# from dotenv import load_dotenv
# import json
# import traceback
# from datetime import datetime

# # Load environment variables
# load_dotenv()

# LLM_MODEL_NAME = "models/gemini-1.5-flash"
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# # Enhanced Rural Context Mapping (same as before)
# RURAL_SYMPTOM_MAPPING = {
#     # Hindi/Local terms to medical symptoms
#     'bukhar': ['fever', 'high_temperature', 'chills'],
#     'taap': ['fever', 'high_temperature', 'chills'],
#     'sir_dard': ['headache', 'head_pain', 'migraine'],
#     'sir_me_dard': ['headache', 'head_pain'],
#     'pet_dard': ['abdominal_pain', 'stomach_ache', 'gastritis'],
#     'pet_me_dard': ['abdominal_pain', 'stomach_ache'],
#     'chakkar': ['dizziness', 'vertigo', 'lightheaded'],
#     'chakkar_aana': ['dizziness', 'vertigo'],
#     'kamjori': ['weakness', 'fatigue', 'lethargy'],
#     'thakaan': ['fatigue', 'weakness', 'tiredness'],
#     'saans_ki_problem': ['breathing_difficulty', 'shortness_of_breath', 'dyspnea'],
#     'saans_phoolna': ['shortness_of_breath', 'breathing_difficulty'],
#     'khansi': ['cough', 'dry_cough', 'productive_cough'],
#     'sukhi_khansi': ['dry_cough', 'persistent_cough'],
#     'ulti': ['vomiting', 'nausea', 'throwing_up'],
#     'ji_machalna': ['nausea', 'vomiting', 'motion_sickness'],
#     'dast': ['diarrhea', 'loose_stools', 'loose_motion'],
#     'loose_motion': ['diarrhea', 'loose_stools'],
#     'paet_kharab': ['stomach_upset', 'indigestion', 'gastritis'],
#     'gas': ['flatulence', 'bloating', 'gas_trouble'],
#     'acidity': ['acid_reflux', 'heartburn', 'gastritis'],
#     'badan_dard': ['body_ache', 'muscle_pain', 'joint_pain'],
#     'jodo_ka_dard': ['joint_pain', 'arthritis', 'body_ache'],
#     'pairo_me_sujan': ['leg_swelling', 'edema', 'fluid_retention'],
#     'aankhon_me_jalan': ['eye_irritation', 'conjunctivitis', 'eye_burning'],
#     'khujli': ['itching', 'skin_irritation', 'rash'],
#     'jalan': ['burning_sensation', 'irritation'],
#     'neend_nahi_aana': ['insomnia', 'sleep_difficulty', 'sleeplessness'],
#     'bhookh_nahi_lagna': ['loss_of_appetite', 'anorexia'],
#     'weight_loss': ['unexpected_weight_loss', 'weight_reduction'],
#     'weight_gain': ['weight_increase', 'obesity'],
    
#     # English colloquial terms
#     'stomach_upset': ['gastritis', 'indigestion', 'stomach_ache'],
#     'feeling_weak': ['fatigue', 'weakness', 'lethargy'],
#     'cant_breathe': ['shortness_of_breath', 'breathing_difficulty'],
#     'chest_tight': ['chest_tightness', 'breathing_difficulty'],
#     'running_nose': ['nasal_congestion', 'rhinitis', 'cold'],
#     'throat_pain': ['sore_throat', 'throat_irritation'],
#     'back_pain': ['lower_back_pain', 'spine_pain'],
#     'leg_pain': ['leg_ache', 'muscle_pain'],
#     'hand_pain': ['arm_pain', 'joint_pain'],
#     'stomach_burning': ['acid_reflux', 'gastritis', 'heartburn'],
# }

# # Emergency keywords for immediate detection
# EMERGENCY_KEYWORDS = [
#     # English emergency terms
#     'emergency', 'urgent', 'severe pain', 'can\'t breathe', 'chest pain', 
#     'heart attack', 'stroke', 'unconscious', 'bleeding heavily', 'accident',
#     'very serious', 'critical', 'immediate help', 'ambulance', 'hospital now',
    
#     # Hindi emergency terms
#     'emergency', 'bahut dard', 'saans nahi aa raha', 'seene me dard', 
#     'behosh', 'khoon bah raha', 'turant madad', 'hospital jana hai',
#     'bahut gambhir', 'jaldi doctor chahiye', 'ambulance bulao'
# ]

# # Critical emergency patterns for rural areas
# RURAL_EMERGENCY_PATTERNS = [
#     {'symptoms': ['severe_chest_pain', 'chest_pain'], 'keywords': ['crushing', 'tight', 'pressure', 'left_arm', 'seene me dard'], 'condition': 'Possible Heart Attack', 'urgency': 'EMERGENCY'},
#     {'symptoms': ['severe_headache', 'headache'], 'keywords': ['worst_ever', 'sudden', 'thunderclap', 'bahut tej sir dard'], 'condition': 'Possible Stroke/Brain Issue', 'urgency': 'EMERGENCY'},
#     {'symptoms': ['difficulty_breathing', 'cant_breathe'], 'keywords': ['severe', 'gasping', 'blue_lips', 'saans nahi aa raha'], 'condition': 'Severe Breathing Problem', 'urgency': 'EMERGENCY'},
#     {'symptoms': ['severe_bleeding'], 'keywords': ['heavy', 'wont_stop', 'large_amount', 'bahut khoon'], 'condition': 'Severe Blood Loss', 'urgency': 'EMERGENCY'},
#     {'symptoms': ['unconscious', 'fainting'], 'keywords': ['not_responding', 'collapsed', 'behosh', 'gir gaya'], 'condition': 'Loss of Consciousness', 'urgency': 'EMERGENCY'},
#     {'symptoms': ['severe_abdominal_pain'], 'keywords': ['sudden', 'unbearable', 'rigid_abdomen', 'pet me bahut dard'], 'condition': 'Acute Abdomen', 'urgency': 'EMERGENCY'},
# ]

# class ConversationState:
#     """Manage conversation state and flow"""
    
#     def __init__(self):
#         self.reset()
    
#     def reset(self):
#         self.stage = "INITIAL"  # INITIAL, REPORT_UPLOADED, CONVERSING, EMERGENCY, ASSESSMENT_READY
#         self.conversation_history = []
#         self.extracted_symptoms = []
#         self.user_concerns = []
#         self.emergency_detected = False
#         self.report_data = None
#         self.follow_up_questions = []
#         self.current_question_index = 0
#         self.conversation_complete = False

# class RuralHealthAssistant:
#     def __init__(self):
#         self.llm = None
#         self.artifacts = {}
#         self.artifacts_loaded = False
#         self.conversation_state = ConversationState()
        
#         if GOOGLE_API_KEY:
#             try:
#                 self.llm = ChatGoogleGenerativeAI(
#                     model=LLM_MODEL_NAME, 
#                     google_api_key=GOOGLE_API_KEY, 
#                     temperature=0.3
#                 )
#                 self.setup_conversation_chains()
#             except Exception as e:
#                 print(f"LLM initialization failed: {e}")
        
#         self.load_artifacts()
    
#     def setup_conversation_chains(self):
#         """Setup different conversation chains for different stages"""
        
#         # Initial greeting after report upload
#         self.greeting_prompt = PromptTemplate(
#             input_variables=["report_summary", "patient_name"],
#             template="""
# You are Dr. AI, a caring rural doctor who has just reviewed a patient's medical report.

# REPORT SUMMARY: {report_summary}
# PATIENT NAME: {patient_name}

# Greet the patient warmly and acknowledge that you've reviewed their report. Then ask what is bothering them today or what specific problem they want to discuss. Keep it simple and caring, like a village doctor would speak.

# Use a mix of simple English and Hindi terms. Be warm and reassuring.

# Example response style:
# "Namaste! मैंने आपकी रिपोर्ट देख ली है। सब कुछ ठीक लग रहा है। अब बताइए, आज आप कैसा महसूस कर रहे हैं? कोई तकलीफ है क्या?"

# Your response:
# """
#         )
        
#         # Main conversation chain
#         self.conversation_prompt = PromptTemplate(
#             input_variables=["user_input", "conversation_history", "report_context", "extracted_symptoms"],
#             template="""
# You are Dr. AI, a caring rural doctor having a conversation with a patient.

# CONVERSATION SO FAR:
# {conversation_history}

# PATIENT'S CURRENT MESSAGE: {user_input}

# REPORT CONTEXT: {report_context}

# SYMPTOMS MENTIONED SO FAR: {extracted_symptoms}

# GUIDELINES:
# 1. Respond naturally like a caring village doctor
# 2. Ask ONE follow-up question at a time
# 3. Use simple words with Hindi terms in parentheses when helpful
# 4. If the patient describes concerning symptoms, show appropriate concern
# 5. Don't jump to conclusions - gather more information first
# 6. Be warm and reassuring

# If the patient mentions emergency symptoms (severe chest pain, can't breathe, unconscious, severe bleeding), immediately advise them to go to the hospital.

# Your response:
# """
#         )
        
#         # Emergency assessment chain
#         self.emergency_prompt = PromptTemplate(
#             input_variables=["emergency_symptoms", "patient_input"],
#             template="""
# A patient in a rural area has described emergency symptoms: {emergency_symptoms}

# Patient's exact words: "{patient_input}"

# Provide IMMEDIATE emergency guidance in simple language (Hindi + English mix):

# 1. Acknowledge the seriousness
# 2. Give immediate instructions (go to hospital/call ambulance)
# 3. Provide basic first aid if applicable
# 4. Be calm but urgent

# Your response:
# """
#         )
        
#         self.greeting_chain = LLMChain(llm=self.llm, prompt=self.greeting_prompt)
#         self.conversation_chain = LLMChain(llm=self.llm, prompt=self.conversation_prompt)
#         self.emergency_chain = LLMChain(llm=self.llm, prompt=self.emergency_prompt)
    
#     def process_uploaded_report(self, report_data, patient_name=""):
#         """Process uploaded medical report and prepare for conversation"""
#         self.conversation_state.reset()
#         self.conversation_state.stage = "REPORT_UPLOADED"
#         self.conversation_state.report_data = report_data
        
#         # Extract basic info from report (implement based on your report parsing logic)
#         report_summary = self.extract_report_summary(report_data)
        
#         # Generate initial greeting
#         if self.llm:
#             try:
#                 greeting_response = self.greeting_chain.run({
#                     'report_summary': report_summary,
#                     'patient_name': patient_name
#                 })
#                 return {
#                     'response': greeting_response,
#                     'stage': 'REPORT_UPLOADED',
#                     'requires_user_input': True,
#                     'show_final_assessment': False
#                 }
#             except Exception as e:
#                 print(f"Error generating greeting: {e}")
        
#         # Fallback greeting
#         return {
#             'response': f"नमस्ते! मैंने आपकी रिपोर्ट देख ली है। अब बताइए, आज आप कैसा महसूस कर रहे हैं? कोई तकलीफ है क्या? (Hello! I've reviewed your report. Now tell me, how are you feeling today? Any discomfort?)",
#             'stage': 'REPORT_UPLOADED',
#             'requires_user_input': True,
#             'show_final_assessment': False
#         }
    
#     def process_user_input(self, user_input, input_type="text"):
#         """Process user input during conversation"""
        
#         # Handle voice input
#         if input_type == "voice":
#             user_input = self.process_voice_input(user_input)
        
#         # Check for emergency first
#         emergency_result = self.check_emergency_in_input(user_input)
#         if emergency_result['is_emergency']:
#             self.conversation_state.stage = "EMERGENCY"
#             return self.handle_emergency(user_input, emergency_result)
        
#         # Extract symptoms from current input
#         new_symptoms = self.extract_symptoms_from_text(user_input)
#         self.conversation_state.extracted_symptoms.extend(new_symptoms)
#         self.conversation_state.extracted_symptoms = list(set(self.conversation_state.extracted_symptoms))
        
#         # Add to conversation history
#         self.conversation_state.conversation_history.append({
#             'speaker': 'patient',
#             'message': user_input,
#             'timestamp': datetime.now().isoformat()
#         })
        
#         # Generate conversational response
#         if self.llm:
#             try:
#                 response = self.conversation_chain.run({
#                     'user_input': user_input,
#                     'conversation_history': self.format_conversation_history(),
#                     'report_context': self.get_report_context(),
#                     'extracted_symptoms': ', '.join(self.conversation_state.extracted_symptoms)
#                 })
#             except Exception as e:
#                 print(f"Error in conversation: {e}")
#                 response = self.basic_conversational_response(user_input)
#         else:
#             response = self.basic_conversational_response(user_input)
        
#         # Add AI response to history
#         self.conversation_state.conversation_history.append({
#             'speaker': 'doctor',
#             'message': response,
#             'timestamp': datetime.now().isoformat()
#         })
        
#         self.conversation_state.stage = "CONVERSING"
        
#         # Check if we have enough information for assessment
#         should_offer_assessment = self.should_offer_final_assessment()
        
#         return {
#             'response': response,
#             'stage': 'CONVERSING',
#             'extracted_symptoms': self.conversation_state.extracted_symptoms,
#             'requires_user_input': True,
#             'show_final_assessment': False,
#             'can_provide_assessment': should_offer_assessment,
#             'conversation_length': len(self.conversation_state.conversation_history)
#         }
    
#     def check_emergency_in_input(self, user_input):
#         """Check if user input contains emergency indicators"""
#         user_input_lower = user_input.lower()
        
#         # Check for emergency keywords
#         for keyword in EMERGENCY_KEYWORDS:
#             if keyword.lower() in user_input_lower:
#                 return {
#                     'is_emergency': True,
#                     'emergency_type': 'keyword_detected',
#                     'keyword': keyword
#                 }
        
#         # Check for emergency symptom patterns
#         for pattern in RURAL_EMERGENCY_PATTERNS:
#             symptom_match = any(symptom in user_input_lower for symptom in pattern['symptoms'])
#             keyword_match = any(keyword in user_input_lower for keyword in pattern['keywords'])
            
#             if symptom_match or keyword_match:
#                 return {
#                     'is_emergency': True,
#                     'emergency_type': 'symptom_pattern',
#                     'condition': pattern['condition'],
#                     'urgency': pattern['urgency']
#                 }
        
#         return {'is_emergency': False}
    
#     def handle_emergency(self, user_input, emergency_result):
#         """Handle emergency situations immediately"""
#         if self.llm:
#             try:
#                 emergency_response = self.emergency_chain.run({
#                     'emergency_symptoms': emergency_result.get('condition', 'Emergency situation'),
#                     'patient_input': user_input
#                 })
#             except Exception as e:
#                 print(f"Error in emergency response: {e}")
#                 emergency_response = self.basic_emergency_response(emergency_result)
#         else:
#             emergency_response = self.basic_emergency_response(emergency_result)
        
#         return {
#             'response': f"🚨 EMERGENCY DETECTED 🚨\n\n{emergency_response}",
#             'stage': 'EMERGENCY',
#             'is_emergency': True,
#             'requires_user_input': False,
#             'show_final_assessment': False,
#             'emergency_advice': "SEEK_IMMEDIATE_MEDICAL_CARE"
#         }
    
#     def basic_emergency_response(self, emergency_result):
#         """Basic emergency response when LLM is not available"""
#         return """यह एक आपातकालीन स्थिति हो सकती है! 
        
# तुरंत करें:
# 1. नजदीकी अस्पताल जाएं
# 2. 108 पर कॉल करें (ambulance)
# 3. किसी को साथ ले जाएं
# 4. घबराएं नहीं, जल्दी करें

# This may be an emergency situation!

# Do immediately:
# 1. Go to nearest hospital
# 2. Call 108 (ambulance)
# 3. Take someone with you
# 4. Don't panic, act quickly"""
    
#     def basic_conversational_response(self, user_input):
#         """Basic conversational response when LLM is not available"""
#         symptoms = self.extract_symptoms_from_text(user_input)
        
#         if symptoms:
#             return f"मैं समझ गया, आपको {', '.join(symptoms)} की समस्या है। कृपया और बताएं - यह कब से है? कितना तेज है? (I understand you have {', '.join(symptoms)}. Please tell me more - since when? How severe?)"
#         else:
#             return "कृपया अपनी तकलीफ के बारे में और बताएं। मैं आपकी मदद करना चाहता हूं। (Please tell me more about your problem. I want to help you.)"
    
#     def should_offer_final_assessment(self):
#         """Determine if we have enough information to offer final assessment"""
#         conversation_length = len(self.conversation_state.conversation_history)
#         symptom_count = len(self.conversation_state.extracted_symptoms)
        
#         # Offer assessment after reasonable conversation
#         return conversation_length >= 4 and symptom_count >= 2
    
#     def provide_final_assessment_if_ready(self):
#         """Provide final assessment when conversation is complete"""
#         if not self.should_offer_final_assessment():
#             return {
#                 'error': 'Not enough information for assessment',
#                 'requires_more_conversation': True
#             }
        
#         self.conversation_state.stage = "ASSESSMENT_READY"
        
#         # Generate comprehensive assessment
#         assessment = self.generate_final_assessment()
        
#         return {
#             'assessment': assessment,
#             'stage': 'ASSESSMENT_COMPLETE',
#             'conversation_summary': self.get_conversation_summary(),
#             'show_final_assessment': True
#         }
    
#     def extract_report_summary(self, report_data):
#         """Extract key information from uploaded medical report"""
#         # Implement based on your report parsing logic
#         # This is a placeholder
#         if isinstance(report_data, dict):
#             return f"Report contains: {', '.join(report_data.keys())}"
#         else:
#             return "Medical report uploaded successfully"
    
#     def extract_symptoms_from_text(self, user_input):
#         """Enhanced symptom extraction for rural context"""
#         user_input_lower = user_input.lower()
#         extracted_symptoms = []
        
#         # Check for mapped symptoms
#         for local_term, medical_symptoms in RURAL_SYMPTOM_MAPPING.items():
#             if local_term in user_input_lower:
#                 extracted_symptoms.extend(medical_symptoms)
        
#         # Extract common English symptoms
#         common_symptoms = [
#             'fever', 'pain', 'headache', 'cough', 'cold', 'weakness', 
#             'fatigue', 'nausea', 'vomiting', 'diarrhea', 'constipation',
#             'dizziness', 'chest pain', 'back pain', 'stomach pain',
#             'breathing problem', 'shortness of breath'
#         ]
        
#         for symptom in common_symptoms:
#             if symptom in user_input_lower:
#                 extracted_symptoms.append(symptom)
        
#         return list(set(extracted_symptoms))
    
#     def format_conversation_history(self):
#         """Format conversation history for context"""
#         formatted = []
#         for entry in self.conversation_state.conversation_history[-10:]:  # Last 10 exchanges
#             speaker = "Patient" if entry['speaker'] == 'patient' else "Dr. AI"
#             formatted.append(f"{speaker}: {entry['message']}")
#         return "\n".join(formatted)
    
#     def get_report_context(self):
#         """Get context from uploaded report"""
#         if self.conversation_state.report_data:
#             return f"Patient has uploaded medical report: {self.extract_report_summary(self.conversation_state.report_data)}"
#         return "No report uploaded"
    
#     def get_conversation_summary(self):
#         """Generate summary of the conversation"""
#         return f"Conversation with {len(self.conversation_state.conversation_history)} exchanges. Symptoms discussed: {', '.join(self.conversation_state.extracted_symptoms)}"
    
#     def generate_final_assessment(self):
#         """Generate final medical assessment"""
#         # Use existing logic from original code
#         return {
#             "risk_level": "Moderate Risk",
#             "primary_concern": "Based on conversation and report analysis",
#             "explanation": "आपके लक्षणों के आधार पर यह आकलन है। सटीक निदान के लिए डॉक्टर से मिलें।",
#             "possible_conditions": ["सामान्य संक्रमण (General Infection)", "वायरल बुखार (Viral Fever)"],
#             "immediate_actions": ["आराम करें", "पर्याप्त पानी पिएं", "खुराक नियमित लें"],
#             "when_to_see_doctor": "अगले 24-48 घंटे में डॉक्टर से सलाह लें",
#             "confidence": 0.8,
#             "rural_specific_advice": "नजदीकी प्राथमिक स्वास्थ्य केंद्र से संपर्क करें"
#         }
    
#     def process_voice_input(self, audio_file):
#         """Process voice input and convert to text"""
#         # Placeholder for voice processing
#         # In real implementation, use speech-to-text API
#         return "Voice processed: Patient mentioned symptoms in voice message"
    
#     def load_artifacts(self):
#         """Load ML model artifacts"""
#         # Keep existing implementation
#         pass

# # Global instance
# rural_health_assistant = RuralHealthAssistant()

# # Main API functions that your frontend will call

# def handle_report_upload(report_data, patient_name=""):
#     """Handle when a medical report is uploaded"""
#     global rural_health_assistant
#     rural_health_assistant.conversation_state.reset()
#     return rural_health_assistant.process_uploaded_report(report_data, patient_name)

# def handle_user_message(user_input, input_type="text"):
#     """Handle user text or voice input during conversation"""
#     global rural_health_assistant
#     return rural_health_assistant.process_user_input(user_input, input_type)

# def get_final_assessment():
#     """Get final medical assessment when requested"""
#     global rural_health_assistant
#     return rural_health_assistant.provide_final_assessment_if_ready()

# def reset_conversation():
#     """Reset conversation state"""
#     global rural_health_assistant
#     rural_health_assistant.conversation_state.reset()
#     return {"message": "Conversation reset successfully"}

# def get_conversation_status():
#     """Get current conversation status"""
#     global rural_health_assistant
#     state = rural_health_assistant.conversation_state
#     return {
#         'stage': state.stage,
#         'conversation_length': len(state.conversation_history),
#         'symptoms_extracted': state.extracted_symptoms,
#         'emergency_detected': state.emergency_detected,
#         'can_provide_assessment': rural_health_assistant.should_offer_final_assessment()
#     }
"""
backend_processing.py — Gemini-only backend helper for Rural Health Assistant.

- Uses only Google GenAI via langchain_google_genai.ChatGoogleGenerativeAI
- Robust normalization of response shapes
- Clear error messages and safe fallback triage
"""

import os
import json
import traceback
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

# Attempt to import langchain Google wrapper (Gemini)
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except Exception:
    ChatGoogleGenerativeAI = None

# Optional voice processor (local)
try:
    from voice_processor import RuralVoiceProcessor
except Exception:
    RuralVoiceProcessor = None

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
print(f"GOOGLE_API_KEY found: {bool(GOOGLE_API_KEY)}")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash-latest")

# Emergency keywords for immediate override
EMERGENCY_KEYWORDS = [
    "not breathing", "unconscious", "severe chest pain", "heavy bleeding",
    "sudden weakness", "slurred speech", "seizure", "severe burn",
    "blue lips", "very drowsy", "faint", "loss of consciousness", "can't breathe", "cannot breathe"
]

def contains_emergency_keyword(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    for kw in EMERGENCY_KEYWORDS:
        if kw in t:
            return True
    return False

# ----------------------------
# LLM client (Gemini-only)
# ----------------------------
class LLMClient:
    def __init__(self):
        self.client = None
        self.available = False
        self._init_client()

    def _init_client(self):
        if not ChatGoogleGenerativeAI or not GOOGLE_API_KEY:
            self.available = False
            return
        try:
            self.client = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=GOOGLE_API_KEY, temperature=0.0)
            self.available = True
        except Exception:
            traceback.print_exc()
            self.available = False

    def is_available(self) -> bool:
        return self.available and self.client is not None

    def call_chat(self, prompt: str, system: Optional[str] = None, max_tokens: int = 600, temperature: float = 0.0) -> str:
        if not self.is_available():
            raise RuntimeError("Gemini client not available (check GOOGLE_API_KEY and installed langchain_google_genai).")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            if hasattr(self.client, "invoke"):
                resp = self.client.invoke(messages)
                if hasattr(resp, "content"):
                    return resp.content
                if hasattr(resp, "text"):
                    return resp.text
                if isinstance(resp, str):
                    return resp
                return str(resp)
            elif hasattr(self.client, "generate"):
                resp = self.client.generate(messages)
                if hasattr(resp, "generations"):
                    try:
                        gens = resp.generations
                        if isinstance(gens, list) and len(gens) > 0:
                            first = gens[0]
                            if isinstance(first, list) and len(first) > 0 and hasattr(first[0], "text"):
                                return first[0].text
                            elif hasattr(first, "text"):
                                return first.text
                    except Exception:
                        pass
                if hasattr(resp, "text"):
                    return resp.text
                return str(resp)
            else:
                return str(self.client(messages))
        except Exception as e:
            raise RuntimeError(f"Google Gemini call failed: {str(e)}")

# global LLM instance
LLM = LLMClient()

# ----------------------------
# Helpers: JSON extraction
# ----------------------------
def extract_json_from_text(txt: str) -> Optional[Dict[str, Any]]:
    if not txt:
        return None
    start = txt.find("{")
    end = txt.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = txt[start:end+1]
        try:
            return json.loads(candidate)
        except Exception:
            try:
                fixed = candidate.replace("'", '"')
                import re
                fixed = re.sub(r",\s*}", "}", fixed)
                fixed = re.sub(r",\s*]", "]", fixed)
                return json.loads(fixed)
            except Exception:
                return None
    return None

# ----------------------------
# Build triage prompt
# ----------------------------
def _build_triage_prompt(symptoms_text: str, report_summary: str = "", past_history: Optional[Dict[str, Any]] = None, location: str = "") -> str:
    # Format past history for the prompt
    past_history_text = ""
    if past_history:
        if past_history.get("chronic_conditions"):
            past_history_text += f"Chronic conditions: {past_history['chronic_conditions']}\n"
        if past_history.get("allergies"):
            past_history_text += f"Allergies: {past_history['allergies']}\n"
        if past_history.get("surgeries"):
            past_history_text += f"Past surgeries: {past_history['surgeries']}\n"
        if past_history.get("current_medications"):
            past_history_text += f"Current medications: {past_history['current_medications']}\n"
        if past_history.get("family_history"):
            past_history_text += f"Family history: {past_history['family_history']}\n"
        if past_history.get("lifestyle"):
            past_history_text += f"Lifestyle: {past_history['lifestyle']}\n"
        if past_history.get("additional_notes"):
            past_history_text += f"Additional notes: {past_history['additional_notes']}\n"

    prompt = f"""
You are a clinical triage assistant. Provide a single JSON object only with the exact keys:
- possible_conditions: list of objects with "disease" (string) and "confidence" (float 0-1)
- risk_level: one of ["Low","Medium","High","Emergency"]
- risk_proba: float 0-1
- reason: short explanation (2-3 sentences)
- recommendations: list of short actionable recommendations (max 6)

Patient info:
Symptoms: {symptoms_text}
Report summary: {report_summary}
Past medical history:
{past_history_text if past_history_text else "No past medical history provided."}
Location: {location}

Only output the JSON object and nothing else.
"""
    return prompt

# ----------------------------
# LLM prediction wrapper
# ----------------------------
def llm_predict_assessment(symptoms_text: str, report_summary: str = "", past_history: Optional[Dict[str, Any]] = None, location: str = "") -> Dict[str, Any]:
    if not LLM.is_available():
        return {"error": "no_gemini", "message": "Gemini backend not initialized (check GOOGLE_API_KEY and langchain_google_genai)."}
    prompt = _build_triage_prompt(symptoms_text, report_summary, past_history, location)
    system = "Return ONLY a single JSON object."

    try:
        raw_text = LLM.call_chat(prompt, system=system, max_tokens=600, temperature=0.0)
    except Exception as e:
        tb = traceback.format_exc()
        return {"error": "llm_call_failed", "message": str(e), "trace": tb}

    parsed = extract_json_from_text(raw_text)
    if parsed is None:
        return {"error": "parse_failed", "message": "LLM returned unparsable JSON", "raw_text": raw_text}

    try:
        parsed.setdefault("possible_conditions", [])
        parsed.setdefault("risk_level", "Medium")
        parsed.setdefault("risk_proba", 0.0)
        parsed.setdefault("reason", "")
        parsed.setdefault("recommendations", [])

        nconds = []
        for item in parsed.get("possible_conditions", []):
            if isinstance(item, dict):
                name = item.get("disease", "")
                conf = item.get("confidence", 0.0)
            else:
                name = str(item)
                conf = 0.0
            try:
                conf = float(conf)
            except Exception:
                conf = 0.0
            nconds.append({"disease": str(name), "confidence": max(0.0, min(1.0, conf))})
        parsed["possible_conditions"] = nconds

        try:
            parsed["risk_proba"] = float(parsed.get("risk_proba", 0.0))
        except Exception:
            parsed["risk_proba"] = 0.0
        parsed["risk_proba"] = max(0.0, min(1.0, parsed["risk_proba"]))

        return parsed
    except Exception as e:
        return {"error": "validation_failed", "message": str(e), "raw_text": raw_text}

# ----------------------------
# Audio transcription helper
# ----------------------------
def transcribe_audio_bytes(audio_bytes: bytes, filename_hint: str = "audio.wav") -> Optional[str]:
    if RuralVoiceProcessor:
        try:
            v = RuralVoiceProcessor()
            import tempfile, os
            tf = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename_hint)[1] or ".wav")
            tf.write(audio_bytes); tf.flush(); tf.close()
            try:
                txt = v.transcribe_audio(tf.name)
                return txt
            finally:
                try: os.unlink(tf.name)
                except: pass
        except Exception:
            traceback.print_exc()
            return None
    return None

# ----------------------------
# Public API used by app.py
# ----------------------------
def handle_user_message(user_input, input_type: str = "text") -> Dict[str, Any]:
    try:
        if input_type == "audio":
            if isinstance(user_input, (bytes, bytearray)):
                txt = transcribe_audio_bytes(user_input)
                if txt:
                    return {"transcript": txt}
                else:
                    return {"error": "transcription_unavailable", "message": "No transcription engine available in this environment."}
            else:
                return {"error": "invalid_audio_payload", "message": "Expected raw audio bytes."}
        else:
            return {"transcript": str(user_input)}
    except Exception as e:
        return {"error": "handle_user_message_failed", "message": str(e), "trace": traceback.format_exc()}

def integrate_report_and_run_assessment(
    report_data: Optional[Dict[str, Any]],
    user_inputs: Dict[str, Any],
    user_profile: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    try:
        symptoms_text = (user_inputs or {}).get("symptoms_text", "") or ""
        city = (user_inputs or {}).get("city", "") or ""
        pincode = (user_inputs or {}).get("pincode", "") or ""
        
        # Build location string for LLM context
        location_info = ""
        if city and pincode:
            location_info = f"{city}, {pincode}"
        elif city:
            location_info = city
        elif pincode:
            location_info = f"Pincode: {pincode}"

        if contains_emergency_keyword(symptoms_text):
            return {"status": "ok", "assessment": {
                "possible_conditions": [],
                "risk_level": "Emergency",
                "risk_proba": 1.0,
                "reason": "Emergency keyword detected in symptoms. Seek immediate care.",
                "recommendations": ["Call emergency services immediately", "Go to nearest hospital"]
            }}

        if isinstance(report_data, dict):
            try:
                for t in report_data.get("medical_tests", [])[:50]:
                    name = str(t.get("test_name", "")).lower()
                    val = t.get("value")
                    if "spo2" in name or "oxygen" in name:
                        try:
                            if float(val) < 90:
                                return {"status": "ok", "assessment": {
                                    "possible_conditions": [],
                                    "risk_level": "Emergency",
                                    "risk_proba": 1.0,
                                    "reason": "Low oxygen saturation detected in report",
                                    "recommendations": ["Seek emergency medical care"]
                                }}
                        except Exception:
                            pass
                    if "hemoglobin" in name or name == "hb":
                        try:
                            if float(val) < 6.0:
                                return {"status": "ok", "assessment": {
                                    "possible_conditions": [],
                                    "risk_level": "Emergency",
                                    "risk_proba": 1.0,
                                    "reason": "Severely low hemoglobin in report",
                                    "recommendations": ["Seek emergency medical care"]
                                }}
                        except Exception:
                            pass
            except Exception:
                pass

        report_summary = ""
        if isinstance(report_data, dict):
            tests = report_data.get("medical_tests", []) or []
            parts = []
            for t in tests[:10]:
                val = t.get("value", "")
                status = f" ({t.get('status')})" if t.get("status") else ""
                parts.append(f"{t.get('test_name','')}: {val}{status}")
            report_summary = "; ".join(parts)

        # Extract past history from user profile
        past_history = user_profile.get("past_history", {}) if user_profile else {}

        llm_out = llm_predict_assessment(
            symptoms_text, 
            report_summary, 
            past_history=past_history,
            location=location_info
        )
        
        if isinstance(llm_out, dict) and llm_out.get("error"):
            return {"status": "ok", "assessment": {
                "possible_conditions": [{"disease": "Unknown", "confidence": 0.3}],
                "risk_level": "Medium",
                "risk_proba": 0.3,
                "reason": llm_out.get("message", "LLM unavailable"),
                "recommendations": ["Consult physician", "Monitor symptoms", "Visit PHC if worsens"]
            }, "debug": llm_out}

        return {"status": "ok", "assessment": llm_out}

    except Exception as e:
        tb = traceback.format_exc()
        return {"status": "ok", "assessment": {
            "possible_conditions": [{"disease": "Unknown", "confidence": 0.2}],
            "risk_level": "Medium",
            "risk_proba": 0.2,
            "reason": f"Backend error: {str(e)}",
            "recommendations": ["Consult physician", "Monitor symptoms"]
        }, "debug": tb}