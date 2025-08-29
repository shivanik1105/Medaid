# app.py
import streamlit as st
import pandas as pd
import ast
from database import get_user_by_email, create_user, update_user_history, update_user_report_data
from backend_processing import run_prediction_engine, merge_and_extract_symptoms
from report_generator import generate_pdf_report
from report_processor import analyze_medical_report, generate_report_explanation
from recommendations import get_dietary_recommendations, get_recommendations
from language_strings import LANGUAGE_STRINGS # New import

# --- Chatbot Question Definitions (Simplified for now) ---
CHATBOT_QUESTIONS = {
    "chest pain": [
        {"id": "chest_pain_duration", "question": "Have you had chest pain for more than 2 days?", "type": "radio", "options": ["Yes", "No"]},
        {"id": "chest_pain_severity", "question": "On a scale of 1-10, how severe is your chest pain?", "type": "slider", "min": 1, "max": 10},
    ],
    "fever": [
        {"id": "fever_exceeded_101", "question": "Has your fever exceeded 101°F?", "type": "radio", "options": ["Yes", "No"]},
        {"id": "fever_duration", "question": "How many days have you had a fever?", "type": "number", "min": 0, "max": 30},
    ],
    "weakness": [
        {"id": "feeling_dizzy", "question": "Are you feeling weak or dizzy?", "type": "radio", "options": ["Yes", "No"]},
    ]
    # Add more questions for other symptoms/conditions
}

# --- Placeholder for Teammate Modules ---
# The analyze_report_placeholder is replaced by analyze_medical_report from report_processor.py
# def analyze_report_placeholder(uploaded_file):
#     """Placeholder for Teammate 1's Report Analyzer."""
#     st.toast(f"Analyzing report: {uploaded_file.name}...")
#     return {"Hemoglobin": "11.5 g/dL (Normal)", "WBC Count": "12,000 /mcL (High)"}

#change this 
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

# Initialize sub-stage for consultation flow
if 'consultation_sub_stage' not in st.session_state.session_data: 
    st.session_state.session_data['consultation_sub_stage'] = 'collect_current_symptoms'

# --- Main App UI ---
st.set_page_config(layout="wide", page_title="AI Health Triage")
st.title("🩺 AI Health Triage System")

# Helper function to get translated string
def _(key):
    lang = st.session_state.user_profile.get('language', 'English') if st.session_state.user_profile else 'English'
    return LANGUAGE_STRINGS.get(lang, LANGUAGE_STRINGS["English"]).get(key, key)

# =======================================
# STAGE 1: LOGIN
# =======================================
if st.session_state.stage == 'login':
    st.info(_("welcome_message"))
    with st.form(key="login_form"):
        name = st.text_input(_("full_name"))
        age = st.number_input(_("age"), 1, 120)
        email = st.text_input(_("email_address"))
        language = st.selectbox(_("preferred_language"), ["English", "Marathi", "Hindi"])
        
        # New: Input Mode Selection
        input_mode = st.radio("Select Input Mode", ["Text", "Voice", "Report"], key="input_mode_selector")
        
        submitted = st.form_submit_button(_("start_session"))
        if submitted:
            if name and age and email:
                with st.spinner(_("setting_up_session")):
                    user = get_user_by_email(email)
                    st.session_state.user_profile = user if user else create_user(name, age, email, language)
                    
                    if st.session_state.user_profile is None:
                        st.error(_("database_connection_error"))
                    else:
                        st.session_state.stage = 'consultation'
                        st.session_state.session_data['input_mode'] = input_mode # Store selected input mode
                st.rerun()

# =======================================
# STAGE 2: CONSULTATION (DATA GATHERING)
# =======================================
elif st.session_state.stage == 'consultation':
    st.header(_("consultation_welcome").format(name=st.session_state.user_profile['name']))

    # Use sub-stages to manage the consultation flow
    if st.session_state.session_data['consultation_sub_stage'] == 'collect_current_symptoms':
        with st.form("current_symptoms_form"):
            current_input_mode = st.session_state.session_data.get('input_mode', 'Text') # Default to Text

            st.subheader(_("symptoms_question"))
            symptoms_text = ""
            uploaded_audio = None
            uploaded_report = None

            if current_input_mode == "Text":
                symptoms_text = st.text_area(_("describe_symptoms"), height=150, key="symptoms_text_area")
            elif current_input_mode == "Voice":
                uploaded_audio = st.file_uploader(_("upload_voice_recording"), type=['mp3', 'wav'], key="voice_uploader")
                if uploaded_audio:
                    st.info(_("voice_input_received"))
                    st.session_state.session_data['voice_input'] = uploaded_audio.name
                    symptoms_text = "Voice input provided (awaiting transcription)." # Placeholder
            elif current_input_mode == "Report":
                uploaded_report = st.file_uploader(_("upload_report"), type=['pdf', 'png', 'jpg'], key="report_uploader")
                if uploaded_report:
                    st.info(_("processing_report"))
                    report_analysis_result = analyze_medical_report(uploaded_report)
                    st.session_state.session_data['report_data'] = report_analysis_result
                    st.success(_("report_processed_success"))
                    # Update user's top-level report_data in DB
                    update_user_report_data(st.session_state.user_profile['_id'], report_analysis_result['structured_data'])
                else:
                    st.warning(_("please_upload_report"))

            submit_current_symptoms = st.form_submit_button(_("submit_for_analysis"))

            if submit_current_symptoms:
                st.session_state.session_data['current_symptoms_text'] = symptoms_text
                st.session_state.session_data['consultation_sub_stage'] = 'handle_past_history'
                st.rerun()

    elif st.session_state.session_data['consultation_sub_stage'] == 'handle_past_history':
        with st.form("past_history_form"):
            st.subheader(_("past_history_question"))
            past_history_from_db = st.session_state.user_profile.get('past_history', [])
            is_new_user_history = not bool(past_history_from_db)

            if is_new_user_history:
                st.info(_("ask_previous_issues"))
                has_previous_issues = st.radio("", ["Yes", "No"], key="has_prev_issues")

                selected_conditions = []
                if has_previous_issues == "Yes":
                    common_conditions = ["Diabetes", "Hypertension (High BP)", "Asthma", "Heart Disease", "Anemia", "Thyroid Issues"]
                    st.write(_("ask_common_conditions").format(conditions_list=", ".join(common_conditions)))
                    selected_conditions = st.multiselect(
                        _("select_conditions"), 
                        options=common_conditions,
                        key="new_user_conditions"
                    )
            else: # Existing user
                st.info(_("confirm_past_history").format(history_list=", ".join(past_history_from_db)))
                common_conditions = ["Diabetes", "Hypertension (High BP)", "Asthma", "Heart Disease", "Anemia", "Thyroid Issues"]
                all_possible_options = sorted(list(set(common_conditions + past_history_from_db)))
                selected_conditions = st.multiselect(
                    _("select_conditions"), 
                    options=all_possible_options, 
                    default=past_history_from_db,
                    key="existing_user_conditions"
                )
            
            submit_past_history = st.form_submit_button(_("confirm_update_history"))

            if submit_past_history:
                st.session_state.session_data['past_history'] = selected_conditions
                st.session_state.session_data['consultation_sub_stage'] = 'collect_report_optional' # New sub-stage for report
                st.rerun()

    elif st.session_state.session_data['consultation_sub_stage'] == 'collect_report_optional':
        with st.form("report_optional_form"):
            st.subheader(_("recent_report_question"))
            # We already handled report upload in 'collect_current_symptoms' if input_mode was 'Report'
            # So this section is for 'Text' or 'Voice' users who might also have a report.

            uploaded_report_optional = st.file_uploader(_("upload_report"), type=['pdf', 'png', 'jpg'], key="report_uploader_optional")
            
            if uploaded_report_optional:
                st.info(_("processing_report"))
                report_analysis_result = analyze_medical_report(uploaded_report_optional)
                st.session_state.session_data['report_data'] = report_analysis_result
                st.success(_("report_processed_success"))
                # Update user's top-level report_data in DB
                update_user_report_data(st.session_state.user_profile['_id'], report_analysis_result['structured_data'])

            col_submit_report, col_skip_report = st.columns(2)
            with col_submit_report:
                submit_report_optional = st.form_submit_button(_("submit_for_analysis"))
            with col_skip_report:
                skip_report = st.form_submit_button(_("no_skip_report"))

            if submit_report_optional or skip_report:
                # This is where the old 'consultation_form' submit logic goes
                symptoms_text = st.session_state.session_data.get('current_symptoms_text', '')
                selected_conditions = st.session_state.session_data.get('past_history', [])
                # uploaded_report is already processed if input mode was 'Report'
                # If this sub-stage was entered, it means input_mode was Text/Voice and report might be optional.
                
                # The update_user_history call is now in the 'results' stage for full session data.
                
                # Check for chatbot questions before moving to results
                final_symptom_set_for_questions = merge_and_extract_symptoms(
                    symptoms_text,
                    selected_conditions,
                    st.session_state.session_data.get('report_data', {}).get('structured_data', {})
                )
                
                relevant_questions_found = False
                for symptom in final_symptom_set_for_questions:
                    if symptom in CHATBOT_QUESTIONS:
                        relevant_questions_found = True
                        break

                if relevant_questions_found:
                    st.session_state.session_data['final_symptom_set_for_questions'] = final_symptom_set_for_questions
                    st.session_state.stage = 'chatbot_questions'
                else:
                    st.session_state.stage = 'results'
                st.rerun()

# =======================================
# STAGE 3: AI ANALYSIS & RESULTS (Renamed from 'analysis')
# =======================================
elif st.session_state.stage == 'results':
    st.header(_("final_triage_results"))
    with st.spinner(_("running_ai_analysis")):
        # Step 5: Merge Data Sources
        current_symptoms_text = st.session_state.session_data.get('current_symptoms_text', '')
        past_history_list = st.session_state.session_data.get('past_history', [])
        report_structured_data = st.session_state.session_data.get('report_data', {}).get('structured_data', {})
        
        final_symptom_set = merge_and_extract_symptoms(
            current_symptoms_text,
            past_history_list,
            report_structured_data
        )
        st.session_state.session_data['final_symptom_set'] = final_symptom_set

        # Step 7: AI Engine Runs
        prediction_output = run_prediction_engine(st.session_state.session_data, st.session_state.user_profile)
        
        risk_level = prediction_output['risk_level']
        reason = prediction_output['reason']
        confidence = prediction_output.get('confidence', 0.0)
        possible_diseases = prediction_output.get('possible_diseases', ['Unknown'])
        # The 'similar_cases' output is now just a note from the RAG model.
        # We don't display the table anymore.
        # similar_cases = prediction_output.get('similar_cases', {}) 
        
        # Step 9: Update Health Passport (Store results for PDF)
        st.session_state.session_data['triage_result'] = prediction_output

        # Now that all session data is complete, update the user history in the database
        update_user_history(
            st.session_state.user_profile['_id'], 
            st.session_state.session_data.get('past_history', []),
            st.session_state.session_data
        )

    # --- Step 8: Displaying the Results ---
    
    # 8a. The Verdict: Display the risk level prominently

    assessment_text = _("overall_assessment")
    st.markdown(f"## ⚠️ {risk_level} {assessment_text}")
    
    # 8b. The Action: Display the most important recommendation
    st.write(_("recommended_next_steps"))
    if "High" in risk_level:
        st.error(_("seek_immediate_attention"), icon="🚨")
    elif "Moderate" in risk_level:
        st.warning(_("consult_doctor_24_hours"), icon="⚠️")
    else:
        st.success(_("home_care_sufficient"), icon="✅")

    # Get user's city for recommendations (assuming it's part of user_profile or session_data)
    user_city = st.session_state.user_profile.get('city', 'Pune')
    
    dynamic_recommendations = get_recommendations(risk_level, user_city)
    if dynamic_recommendations:
        st.write("**Suggested Facilities/Actions:**")
        for item in dynamic_recommendations:
            st.write(f"- {item}")
    
    # 8c. The Explanation: Expandable section for details
    with st.expander(_("view_analysis_details")):
        disease_text=_("possible_disease")
        ai_text=_("ai_reasoning")
        
        # Displaying multiple possible diseases
        if possible_diseases and possible_diseases[0] != 'Unknown':
            st.write(f"**{disease_text}** {', '.join(possible_diseases)}")
        else:
            st.write(f"**{disease_text}** {_('Unknown')}")

        st.write(f"**{ai_text}** {reason}")
        
        if st.session_state.session_data.get('report_data') and st.session_state.session_data['report_data'].get('structured_data'):
            report_text=_("extracted_report_data")
            st.write(f"**{report_text}**")
            for key, value in st.session_state.session_data['report_data']['structured_data'].items():
                st.write(f"- {key.replace('_', ' ').title()}: {value}")

            user_age = st.session_state.user_profile.get('age')
            report_explanation = generate_report_explanation(st.session_state.session_data['report_data']['structured_data'], user_age)
            explanation_text=_("report_explanation")
            st.write(f"**{explanation_text}**")
            st.write(report_explanation)

            diet_recommendations = get_dietary_recommendations(st.session_state.session_data['report_data']['structured_data'])
            if diet_recommendations:
                diet_text=_("dietary_recommendations")
                st.write(f"**{diet_text}**")
                for rec in diet_recommendations:
                    st.write(f"- {rec}")

    # --- Final Features ---
    st.subheader(_("your_health_passport"))
    st.write(_("download_summary"))
    pdf_data = generate_pdf_report(st.session_state.user_profile, st.session_state.session_data)
    st.download_button(
        label=_("download_pdf_summary"),
        data=pdf_data,
        file_name=f"Health_Summary_{st.session_state.user_profile['name']}.pdf",
        mime="application/pdf"
    )

    # Placeholder for Share via WhatsApp/Email
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Share via WhatsApp", key="share_whatsapp"):
            st.info("WhatsApp sharing functionality coming soon!")
    with col2:
        if st.button("Share via Email", key="share_email"):
            st.info("Email sharing functionality coming soon!")

    if st.button(_("start_new_consultation")):
        st.session_state.stage = 'consultation'
        st.session_state.session_data = {}
        st.rerun()

    if st.button(_("logout")):
        st.session_state.stage = 'login'
        st.session_state.user_profile = None
        st.session_state.session_data = {}
        st.rerun()

# =======================================
# STAGE 4: CHATBOT TARGETED QUESTIONS
# =======================================
elif st.session_state.stage == 'chatbot_questions':
    st.header(_("chatbot_more_questions"))
    st.info(_("chatbot_info_message"))

    final_symptom_set_for_questions = st.session_state.session_data.get('final_symptom_set_for_questions', [])
    st.session_state.session_data['chatbot_answers'] = st.session_state.session_data.get('chatbot_answers', {})

    with st.form(key="chatbot_form"):
        for symptom_keyword in final_symptom_set_for_questions:
            if symptom_keyword in CHATBOT_QUESTIONS:
                regarding_text=_("regarding")
                st.subheader(f"{regarding_text} {symptom_keyword.title()}:")
                for question_obj in CHATBOT_QUESTIONS[symptom_keyword]:
                    question_id = question_obj['id']
                    question_text = question_obj['question']
                    question_type = question_obj['type']

                    if question_type == "radio":
                        answer = st.radio(question_text, question_obj['options'], key=question_id)
                    elif question_type == "slider":
                        answer = st.slider(question_text, min_value=question_obj['min'], max_value=question_obj['max'], key=question_id)
                    elif question_type == "number":
                        answer = st.number_input(question_text, min_value=question_obj['min'], max_value=question_obj['max'], key=question_id)
                    else:
                        answer = st.text_input(question_text, key=question_id)
                    
                    st.session_state.session_data['chatbot_answers'][question_id] = answer
        
        submitted_chatbot = st.form_submit_button(_("submit_answers"))
        if submitted_chatbot:
            st.session_state.stage = 'results'
            st.rerun()