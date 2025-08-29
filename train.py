# train.py
import pandas as pd
import numpy as np
import ast
import joblib
import os
import json
import faiss
from sklearn.preprocessing import MultiLabelBinarizer, LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

# --- CONFIGURATION ---
TRAIN_PATH = r"F:\shivani\VSCode\projects\Medaid\disease_dataset\release_train_patients\release_train_patients.csv"
SYMPTOM_MAP_PATH = r"F:\shivani\VSCode\projects\Medaid\disease_dataset\release_evidences.json"
OUTPUT_DIR = 'model_outputs/'
os.makedirs(OUTPUT_DIR, exist_ok=True)
N_SAMPLES_TO_USE = 100000

# --- MAIN SCRIPT ---
if __name__ == "__main__":
    print("=== MEDICAL RISK PREDICTION - TRAINING PHASE ===")
    
    # --- 1. Load and Downsample Data ---
    print(f"\n[1/6] Loading and downsampling data to {N_SAMPLES_TO_USE} samples...")
    df_full = pd.read_csv(TRAIN_PATH)
    df = df_full.sample(n=N_SAMPLES_TO_USE, random_state=42) if len(df_full) > N_SAMPLES_TO_USE else df_full
    
    with open(SYMPTOM_MAP_PATH, 'r', encoding='utf-8') as f:
        symptom_map_json = json.load(f)
    symptom_map = {k: v['name'].replace('_', ' ') for k, v in symptom_map_json.items() if isinstance(v, dict) and 'name' in v}
    print("✅ Data loaded.")

    # --- 2. Preprocess Data ---
    print("\n[2/6] Preprocessing data...")
    df['AGE'] = df['AGE'].fillna(df['AGE'].median())
    df['EVIDENCES_LIST'] = df['EVIDENCES'].apply(ast.literal_eval)
    df['symptom_text'] = df['EVIDENCES_LIST'].apply(lambda codes: " ".join([symptom_map.get(code, "") for code in codes]))

    # --- 3. Generate All Features ---
    print("\n[3/6] Generating features...")
    mlb = MultiLabelBinarizer()
    symptom_features = mlb.fit_transform(df['EVIDENCES_LIST'])
    df_symptoms = pd.DataFrame(symptom_features, columns=mlb.classes_, index=df.index)
    
    tfidf = TfidfVectorizer(max_features=5000, stop_words='english')
    text_features_tfidf = tfidf.fit_transform(df['symptom_text'])
    
    svd = TruncatedSVD(n_components=100, random_state=42)
    contextual_features = svd.fit_transform(text_features_tfidf)
    df_context = pd.DataFrame(contextual_features, index=df.index, columns=[f'context_{i}' for i in range(100)])
    
    # --- 4. Create Final Feature Library & Labels ---
    print("\n[4/6] Combining features and creating BALANCED risk categories...")
    sex_encoded = pd.get_dummies(df['SEX'], drop_first=True, prefix='SEX')
    X_library = pd.concat([df['AGE'], sex_encoded, df_symptoms, df_context], axis=1).fillna(0)
    
    high_risk = [
        'Myocardial infarction', 'Pulmonary embolism', 'Pneumonia', 'Appendicitis',
        'Anaphylaxis', 'Unstable angina', 'Panic attack', 'Acute rhinosinusitis',
        'Bronchitis', 'Possible NSTEMI', 'Scombroid food poisoning', 
        'Acute dystonic reaction', 'Boerhaave syndrome', 'Chagas disease',
    ]
    
    moderate_risk = [
        'Malaria', 'Dengue', 'Tuberculosis', 'Gastroenteritis', 'Anemia',
        'HIV (initial infection)', 'GERD', 'Localized edema', 'Cluster headache',
        'Atrial fibrillation', 'Acute laryngitis', 'Spontaneous pneumothorax',
        'Guillain-Barré syndrome', 'Myasthenia gravis', 'Influenza', 
        'Bronchospasm / acute asthma exacerbation', 'Acute pulmonary edema',
        'Pericarditis', 'Spontaneous rib fracture',
    ]
    
    # Assign risk levels based on pathology. This will be the label for risk prediction.
    y_risk_levels_raw = df['PATHOLOGY'].apply(
        lambda pathology: 'High Risk' if pathology in high_risk 
        else 'Moderate Risk' if pathology in moderate_risk 
        else 'Low Risk'
    )

    # Encode risk levels
    le = LabelEncoder().fit(y_risk_levels_raw)
    y_library_encoded = le.transform(y_risk_levels_raw)

    # --- 5. Build and Save Faiss Index ---
    print("\n[5/6] Building the Faiss similarity search index...")
    X_library_np = np.ascontiguousarray(X_library.values.astype('float32'))
    faiss.normalize_L2(X_library_np)
    index = faiss.IndexFlatIP(X_library_np.shape[1])
    index.add(X_library_np)
    faiss.write_index(index, os.path.join(OUTPUT_DIR, 'patient_library.index'))
    print("✅ FAISS index built and saved.")

    # --- 6. Save All Other Artifacts ---
    print("\n[6/6] Saving all other artifacts...")
    np.save(os.path.join(OUTPUT_DIR, 'patient_library_labels.npy'), y_library_encoded)
    np.save(os.path.join(OUTPUT_DIR, 'patient_library_pathologies.npy'), df['PATHOLOGY'].values)
    joblib.dump(le, os.path.join(OUTPUT_DIR, 'risk_label_encoder.pkl'))
    joblib.dump(mlb, os.path.join(OUTPUT_DIR, 'symptom_encoder.pkl'))
    joblib.dump(tfidf, os.path.join(OUTPUT_DIR, 'tfidf_model.pkl'))
    joblib.dump(svd, os.path.join(OUTPUT_DIR, 'svd_model.pkl'))
    joblib.dump(symptom_map, os.path.join(OUTPUT_DIR, 'symptom_map.pkl'))
    joblib.dump(list(X_library.columns), os.path.join(OUTPUT_DIR, 'final_feature_columns.pkl'))

    # Generate and save a simple layman's map for pathologies
    unique_pathologies = df['PATHOLOGY'].unique()
    layman_map = {p: p.replace('_', ' ').title() for p in unique_pathologies}
    joblib.dump(layman_map, os.path.join(OUTPUT_DIR, 'layman_map.pkl'))
    
    print(f"\n✅ All artifacts saved to '{OUTPUT_DIR}' directory.")
