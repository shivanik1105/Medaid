# backend_processing.py
import pandas as pd
import numpy as np
import ast
import joblib
import os
import faiss
from collections import Counter
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
import re # Added for merge_and_extract_symptoms

# --- CONFIGURATION ---
ARTIFACTS_DIR = 'model_outputs/'
K_NEIGHBORS = 15
RISK_WEIGHTS = {
    'High Risk': 3.0,  # Increased weights for high risk
    'Moderate Risk': 2.0,  # Increased weights for moderate risk
    'Low Risk': 1.0
}

# --- MEDICAL RULES FOR CRITICAL OVERRIDES ---
CRITICAL_RULES = [
    {"symptoms": ["chest pain", "chest discomfort"], 
     "history": ["heart disease", "myocardial infarction", "angina", "cardiac", "coronary"],
     "override_risk": "High Risk",
     "reason": "Chest pain with history of heart disease requires immediate evaluation"},
     
    {"symptoms": ["shortness of breath", "difficulty breathing", "wheezing"],
     "history": ["asthma", "copd", "emphysema", "respiratory"],
     "override_risk": "High Risk",
     "reason": "Respiratory distress with history of lung disease"},
     
    {"symptoms": ["severe headache", "worst headache"],
     "history": ["hypertension", "high blood pressure", "aneurysm", "stroke"],
     "override_risk": "High Risk",
     "reason": "Severe headache with cardiovascular history"},
     
    {"symptoms": ["fever", "high temperature"],
     "history": ["hiv", "aids", "cancer", "chemotherapy", "immunocompromised"],
     "override_risk": "High Risk",
     "reason": "Fever in immunocompromised patient"},
     
    {"symptoms": ["chest pain"],
     "history": ["diabetes"],
     "override_risk": "High Risk",
     "reason": "Chest pain in diabetic patient (possible silent MI)"},
     
    {"symptoms": ["abdominal pain", "stomach pain"],
     "history": ["appendicitis", "diverticulitis", "ibd", "crohn's"],
     "override_risk": "High Risk",
     "reason": "Abdominal pain with history of serious GI conditions"},
]

# Symptom priority mapping
SYMPTOM_CRITICALITY = {
    "chest pain": "High Risk",
    "loss of consciousness": "High Risk",
    "severe bleeding": "High Risk",
    "shortness of breath": "High Risk",
    "difficulty breathing": "High Risk",
    "sudden weakness": "High Risk",
    "severe headache": "High Risk",
    "fainting": "High Risk",
    "severe dizziness": "Moderate Risk",
    "high fever": "Moderate Risk",
    "persistent vomiting": "Moderate Risk"
}

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

    print("✅ All artifacts loaded successfully.")
    ARTIFACTS_LOADED = True
except FileNotFoundError as e:
    print(f"❌ Error loading artifacts: {e}. Please ensure train.py has been run successfully.")
    ARTIFACTS_LOADED = False

# =======================================
# 2. MEDICAL RULE CHECKING FUNCTION
# =======================================
def check_critical_rules(current_symptoms_text: str, past_history_list: list) -> dict or None:
    """
    Check if the current case triggers any critical medical rules that should override
    the similarity-based prediction.
    """
    current_symptoms_lower = current_symptoms_text.lower()
    past_history_lower = [h.lower() for h in past_history_list]
    
    for rule in CRITICAL_RULES:
        # Check if any symptom from the rule is present
        symptom_match = any(symptom in current_symptoms_lower for symptom in rule["symptoms"])
        
        # Check if any history item from the rule is present
        history_match = any(history in past_history_lower for history in rule["history"])
        
        if symptom_match and history_match:
            return {
                "risk_level": rule["override_risk"],
                "reason": rule["reason"],
                "confidence": 1.0,
                "rule_triggered": True
            }
    
    # Check for high-criticality symptoms regardless of history
    for symptom, risk_level in SYMPTOM_CRITICALITY.items():
        if symptom in current_symptoms_lower:
            # If it's a high-risk symptom, never allow low risk
            if risk_level == "High Risk" and any(s in current_symptoms_lower for s in ["chest", "breath", "bleed", "conscious"]):
                return {
                    "risk_level": risk_level,
                    "reason": f"Critical symptom detected: {symptom}",
                    "confidence": 0.9,
                    "rule_triggered": True
                }
    
    return None

# =======================================
# 3. SYMPTOM MERGING AND EXTRACTION
# =======================================
def merge_and_extract_symptoms(
    current_symptoms_text: str,
    past_history_list: list,
    report_structured_data: dict
) -> list[str]:
    """
    Merges symptoms from various sources into a unified list of keywords/phrases.
    This combined list forms the 'Final Symptom Set'.
    """
    final_symptom_set = set()

    # 1. Process current symptoms text (simple tokenization for now)
    if current_symptoms_text:
        words = re.findall(r'\b\w+\b', current_symptoms_text.lower())
        final_symptom_set.update(words)

    # 2. Add past history items
    final_symptom_set.update([item.lower() for item in past_history_list])

    # 3. Process structured report data (keys as potential symptoms/conditions)
    if report_structured_data:
        for key, value in report_structured_data.items():
            # Example: 'hemoglobin' or 'sugar' as keywords
            final_symptom_set.add(key.lower())
            # If values contain descriptive text, extract keywords from them too
            if isinstance(value, str):
                value_words = re.findall(r'\b\w+\b', value.lower())
                final_symptom_set.update(value_words)

    return list(final_symptom_set)


# =======================================
# 4. THE MAIN PREDICTION ENGINE (Renumbered from 3)
# =======================================
def run_prediction_engine(session_data: dict, user_profile: dict) -> dict:
    """
    Takes live user data, processes it, and returns a risk prediction using Faiss similarity search
    with medical rule overrides. It now directly uses the 'final_symptom_set' from session_data.
    """
    if not ARTIFACTS_LOADED:
        return {"risk_level": "Error: Model not loaded", "reason": "Model files not found."}

    # Retrieve the merged symptom set
    final_symptom_set = session_data.get('final_symptom_set', [])
    combined_symptoms_text = ". ".join(final_symptom_set).lower()

    # --- Step A: Check for critical medical rules first ---
    # check_critical_rules expects text and a list of history, let's adapt
    rule_check = check_critical_rules(combined_symptoms_text, final_symptom_set)
    if rule_check:
        # Add similar cases info even for rule-based decisions
        rule_check["similar_cases"] = {
            "Note": "Decision based on critical medical rule override",
            "Rule Applied": rule_check["reason"]
        }
        return rule_check

    # --- Step B: Preprocess the new user's data ---
    # Create a reverse map for efficient lookup: {'fever': 'E_91', 'chest pain': 'E_1'}
    text_to_code_map = {v.lower(): k for k, v in symptom_map.items()}
    
    symptom_codes = set()

    # Find symptom codes from the final symptom set
    for symptom_keyword in final_symptom_set:
        for symptom_text, symptom_code in text_to_code_map.items():
            if symptom_keyword in symptom_text.lower(): # Match keywords from final_symptom_set
                symptom_codes.add(symptom_code)

    new_data = {
        'AGE': user_profile.get('age', 30),
        'SEX': user_profile.get('sex', 'M'),
        'EVIDENCES_LIST': [list(symptom_codes)] # Use the combined, extracted codes
    }
    df_new = pd.DataFrame(new_data)

    df_new['symptom_text'] = df_new['EVIDENCES_LIST'].apply(lambda codes: ". ".join([symptom_map.get(code, "") for code in codes]))
    
    symptom_features = mlb.transform(df_new['EVIDENCES_LIST'])
    df_symptoms = pd.DataFrame(symptom_features, columns=mlb.classes_)
    
    text_features_tfidf = tfidf.transform(df_new['symptom_text'])
    contextual_features = svd.transform(text_features_tfidf)
    df_context = pd.DataFrame(contextual_features, columns=[f'context_{i}' for i in range(contextual_features.shape[1])])
    
    sex_encoded = pd.get_dummies(df_new['SEX'], drop_first=True, prefix='SEX')
    if 'SEX_M' not in sex_encoded.columns: 
        sex_encoded['SEX_M'] = 0
        
    X_new_unaligned = pd.concat([df_new[['AGE']], sex_encoded[['SEX_M']], df_symptoms, df_context], axis=1)

    # --- Step C: Align features to match the library schema ---
    X_new_aligned = X_new_unaligned.reindex(columns=feature_columns, fill_value=0)
    
    # --- Step D: Find Similar Cases with Faiss ---
    X_new_np = np.ascontiguousarray(X_new_aligned.values.astype('float32'))
    faiss.normalize_L2(X_new_np)
    distances, top_k_indices = index.search(X_new_np, K_NEIGHBORS)
    
    # --- Step E: Predict using Weighted Voting ---
    patient_indices = top_k_indices[0]
    patient_similarities = distances[0]
    top_k_labels_encoded = y_library_encoded[patient_indices]
    top_k_pathologies = y_pathologies[patient_indices]
    
    vote_counts = Counter()
    for i, label_encoded in enumerate(top_k_labels_encoded):
        label_text = risk_labels_map[label_encoded]
        risk_weight = RISK_WEIGHTS.get(label_text, 1.0)
        vote_counts[label_text] += patient_similarities[i] * risk_weight
        
    final_prediction = vote_counts.most_common(1)[0][0]
    confidence = round(vote_counts[final_prediction] / sum(vote_counts.values()), 2) if sum(vote_counts.values()) > 0 else 0

    # --- Step F: Apply symptom criticality check (never allow low risk for critical symptoms) ---
    # Use the combined_symptoms_text for criticality check
    current_symptoms_lower = combined_symptoms_text
    for symptom, min_risk in SYMPTOM_CRITICALITY.items():
        if symptom in current_symptoms_lower:
            # If our prediction is lower than the minimum required risk for this symptom, upgrade it
            risk_hierarchy = {"Low Risk": 0, "Moderate Risk": 1, "High Risk": 2}
            if risk_hierarchy.get(final_prediction, 0) < risk_hierarchy.get(min_risk, 0):
                final_prediction = min_risk
                confidence = max(confidence, 0.8)  # Boost confidence when upgrading due to critical symptom

    # --- Step G: Format the Final Output ---
    most_likely_condition = top_k_pathologies[0]
    reasoning_string = f"This assessment is based on your symptoms showing a strong similarity to past cases of '{most_likely_condition}', which is considered a '{final_prediction}' condition."

    output = {
        "risk_level": final_prediction,
        "possible_disease": most_likely_condition, # Added this line
        "reason": reasoning_string,
        "confidence": confidence,
        "similar_cases": {
            "Similarity": [f"{s*100:.0f}%" for s in patient_similarities[:5]],
            "Risk Level": [risk_labels_map[l] for l in top_k_labels_encoded[:5]],
            "Condition in Similar Case": top_k_pathologies[:5]
        }
    }
    return output