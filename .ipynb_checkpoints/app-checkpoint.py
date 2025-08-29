# app.py
import streamlit as st
import pandas as pd
import ast
# FIX: Removed the unused 'get_clarifying_questions' import
from database import get_user_by_email, create_user, update_user_history
from backend_processing import run_prediction_engine
from report_generator import generate_pdf_report # For the Health Passport

# --- Placeholder for Teammate Modules ---
def analyze_report_placeholder(uploaded_file):
    """Placeholder for Teammate 1's Report Analyzer."""
    st.toast(f"Analyzing report: {uploaded_file.name}...")
    # In a real scenario, this would return a structured JSON from OCR/NLP
    return {"Hemoglobin": "11.5 g/dL (Normal)", "WBC Count": "12,000 /mcL (High)"}

def get_recommendations_placeholder(risk_level, city="Pune"):
    """Placeholder for Teammate 2's Hospital Recommender."""
    if "High" in risk_level:
        return ["Ruby Hall Clinic, Sassoon Road", "Jehangir Hospital, Pune Station", "Sahyadri Super Speciality Hospital, Deccan"]
    elif "Moderate" in risk_level:
        return ["Your local General Practitioner", "A nearby Polyclinic for consultation"]
    return []

# --- State Machine & Session Setup ---
if 'stage' not in st.session_state: st.session_state.stage = 'login'
if 'user_profile' not in st.session_state: st.session_state.user_profile = None
if 'session_data' not in st.session_state: st.session_state.session_data = {}

# --- Main App UI ---
st.set_page_config(layout="wide", page_title="AI Health Triage")
st.title("🩺 AI Health Triage System")

# =======================================
# STAGE 1: LOGIN
# =======================================
if st.session_state.stage == 'login':
    st.info("Welcome! Please provide your details to begin your consultation.")
    with st.form(key="login_form"):
        name = st.text_input("👤 Full Name")
        age = st.number_input("🎂 Age", 1, 120)
        email = st.text_input("📧 Email Address")
        language = st.selectbox("🗣️ Preferred Language", ["English", "Marathi", "Hindi"])
        submitted = st.form_submit_button("Start Session")
        if submitted:
            if name and age and email:
                with st.spinner("Setting up your session..."):
                    user = get_user_by_email(email)
                    st.session_state.user_profile = user if user else create_user(name, age, email, language)
                    st.session_state.stage = 'consultation'
                st.rerun()

# =======================================
# STAGE 2: CONSULTATION (DATA GATHERING)
# =======================================
elif st.session_state.stage == 'consultation':
    st.header(f"Welcome, {st.session_state.user_profile['name']}! Let's begin.")
    with st.form("consultation_form"):
        st.subheader("1. How are you feeling today?")
        symptoms_text = st.text_area("Describe your current symptoms (Text or Voice):", height=150)
        
        st.subheader("2. What is your past medical history?")
        past_history_from_db = st.session_state.user_profile.get('past_history', [])
        common_conditions = ["Diabetes", "Hypertension (High BP)", "Asthma", "Heart Disease", "Anemia"]
        selected_conditions = st.multiselect("Select any pre-existing conditions:", options=common_conditions, default=past_history_from_db)
        
        st.subheader("3. Do you have a recent medical report?")
        uploaded_report = st.file_uploader("Upload report (PDF or Image)", type=['pdf', 'png', 'jpg'])
        
        if st.form_submit_button("Submit for Analysis"):
            with st.spinner("Processing your information..."):
                # Store all collected data in the session
                st.session_state.session_data['current_symptoms_text'] = symptoms_text
                st.session_state.session_data['past_history'] = selected_conditions
                
                # Integrate Teammate 1's module
                if uploaded_report:
                    st.session_state.session_data['report_data'] = analyze_report_placeholder(uploaded_report)
                
                # Update user's history in the database for next time
                update_user_history(st.session_state.user_profile['_id'], selected_conditions)
                
                st.session_state.stage = 'analysis'
                st.rerun()

# =======================================
# STAGE 3: AI ANALYSIS & RESULTS
# =======================================
elif st.session_state.stage == 'analysis':
    st.header("Final Triage Results")
    with st.spinner("Running AI analysis... Please wait."):
        # Integrate the AI Prediction Engine
        prediction_output = run_prediction_engine(st.session_state.session_data, st.session_state.user_profile)
        
        risk_level = prediction_output['risk_level']
        reason = prediction_output['reason']
        confidence = prediction_output.get('score', 0) # Use .get for safety
        similar_cases = prediction_output.get('similar_cases', {})
        
        # Store results for the Health Passport
        st.session_state.session_data['triage_result'] = prediction_output

    # --- Display Results (Risk Level First) ---
    st.subheader(f"Overall Assessment: {risk_level}")
    st.progress(confidence)
    
    with st.expander("View Analysis Details"):
        st.write(f"**AI Reasoning:** {reason}")
        

    st.subheader("Recommended Next Steps")
    if "High" in risk_level:
        st.error("Please seek immediate medical attention.", icon="🚨")
    elif "Moderate" in risk_level:
        st.warning("We recommend consulting a doctor within 24 hours.", icon="⚠️")
    else:
        st.success("Home care may be sufficient. Monitor your symptoms.", icon="✅")
        
    # Integrate Teammate 2's module
    recommendations = get_recommendations_placeholder(risk_level)
    if recommendations:
        st.subheader("Suggested Hospitals/Clinics in Pune:")
        for item in recommendations:
            st.write(f"- {item}")
            
    # --- Health Passport Feature ---
    st.subheader("Your Health Passport")
    st.write("Download a complete summary of this consultation for your records or to share with a doctor.")
    pdf_data = generate_pdf_report(st.session_state.user_profile, st.session_state.session_data)
    st.download_button(
        label="Download PDF Summary",
        data=pdf_data,
        file_name=f"Health_Summary_{st.session_state.user_profile['name']}.pdf",
        mime="application/pdf"
    )

    if st.button("Start New Consultation"):
        # Reset for a new session, but keep the user logged in
        st.session_state.stage = 'consultation'
        st.session_state.session_data = {}
        st.rerun()
