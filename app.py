# # # app.py - FIXED VERSION WITH PROPER ERROR HANDLING
# # import streamlit as st
# # import pandas as pd
# # import ast
# # from database import get_user_by_email, create_user, update_user_history, update_user_report_data
# # from backend_processing import run_prediction_engine, merge_and_extract_symptoms
# # from report_generator import generate_pdf_report
# # from report_processor import analyze_medical_report, generate_report_explanation
# # from recommendations import get_dietary_recommendations, get_recommendations
# # from language_strings import LANGUAGE_STRINGS
# # import traceback

# # # --- State Machine & Session Setup ---
# # if 'stage' not in st.session_state: st.session_state.stage = 'login'
# # if 'user_profile' not in st.session_state: st.session_state.user_profile = None
# # if 'session_data' not in st.session_state: st.session_state.session_data = {}

# # # Initialize sub-stage for consultation flow
# # if 'consultation_sub_stage' not in st.session_state.session_data: 
# #     st.session_state.session_data['consultation_sub_stage'] = 'collect_current_symptoms'

# # # Helper function to get translated string
# # def _(key):
# #     lang = st.session_state.user_profile.get('language', 'English') if st.session_state.user_profile else 'English'
# #     return LANGUAGE_STRINGS.get(lang, LANGUAGE_STRINGS["English"]).get(key, key)

# # # =======================================
# # # STAGE 1: LOGIN
# # # =======================================
# # if st.session_state.stage == 'login':
# #     st.info(_("welcome_message"))
# #     with st.form(key="login_form"):
# #         name = st.text_input(_("full_name"))
# #         age = st.number_input(_("age"), 1, 120)
# #         email = st.text_input(_("email_address"))
# #         language = st.selectbox(_("preferred_language"), ["English", "Marathi", "Hindi"])
        
# #         # Input Mode Selection
# #         input_mode = st.radio("Select Input Mode", ["Text", "Voice", "Report"], key="input_mode_selector")
        
# #         submitted = st.form_submit_button(_("start_session"))
# #         if submitted:
# #             if name and age and email:
# #                 with st.spinner(_("setting_up_session")):
# #                     user = get_user_by_email(email)
# #                     st.session_state.user_profile = user if user else create_user(name, age, email, language)
                    
# #                     if st.session_state.user_profile is None:
# #                         st.error(_("database_connection_error"))
# #                     else:
# #                         st.session_state.stage = 'consultation'
# #                         st.session_state.session_data['input_mode'] = input_mode
# #                 st.rerun()

# # # =======================================
# # # STAGE 2: CONSULTATION (DATA GATHERING)
# # # =======================================
# # elif st.session_state.stage == 'consultation':
# #     st.header(_("consultation_welcome").format(name=st.session_state.user_profile['name']))

# #     # Use sub-stages to manage the consultation flow
# #     if st.session_state.session_data['consultation_sub_stage'] == 'collect_current_symptoms':
# #         with st.form("current_symptoms_form"):
# #             current_input_mode = st.session_state.session_data.get('input_mode', 'Text')

# #             st.subheader(_("symptoms_question"))
# #             symptoms_text = ""
# #             uploaded_audio = None
# #             uploaded_report = None

# #             if current_input_mode == "Text":
# #                 symptoms_text = st.text_area(_("describe_symptoms"), height=150, key="symptoms_text_area")
# #             elif current_input_mode == "Voice":
# #                 uploaded_audio = st.file_uploader(_("upload_voice_recording"), type=['mp3', 'wav'], key="voice_uploader")
# #                 if uploaded_audio:
# #                     st.info(_("voice_input_received"))
# #                     st.session_state.session_data['voice_input'] = uploaded_audio.name
# #                     symptoms_text = "Voice input provided (awaiting transcription)."
# #             elif current_input_mode == "Report":
# #                 uploaded_report = st.file_uploader(_("upload_report"), type=['pdf', 'png', 'jpg'], key="report_uploader")
# #                 if uploaded_report:
# #                     st.info(_("processing_report"))
# #                     report_analysis_result = analyze_medical_report(uploaded_report)
# #                     st.session_state.session_data['report_data'] = report_analysis_result
# #                     st.success(_("report_processed_success"))
# #                     update_user_report_data(st.session_state.user_profile['_id'], report_analysis_result['structured_data'])
# #                 else:
# #                     st.warning(_("please_upload_report"))

# #             submit_current_symptoms = st.form_submit_button(_("submit_for_analysis"))

# #             if submit_current_symptoms:
# #                 st.session_state.session_data['current_symptoms_text'] = symptoms_text
# #                 st.session_state.session_data['consultation_sub_stage'] = 'handle_past_history'
# #                 st.rerun()

# #     elif st.session_state.session_data['consultation_sub_stage'] == 'handle_past_history':
# #         with st.form("past_history_form"):
# #             st.subheader(_("past_history_question"))
# #             past_history_from_db = st.session_state.user_profile.get('past_history', [])
# #             is_new_user_history = not bool(past_history_from_db)

# #             if is_new_user_history:
# #                 st.info(_("ask_previous_issues"))
# #                 has_previous_issues = st.radio(
# #                     "Do you have any previous medical issues?",
# #                     ["Yes", "No"], 
# #                     key="has_prev_issues"
# #                 )

# #                 selected_conditions = []
# #                 if has_previous_issues == "Yes":
# #                     common_conditions = ["Diabetes", "Hypertension (High BP)", "Asthma", "Heart Disease", "Anemia", "Thyroid Issues"]
# #                     st.write(_("ask_common_conditions").format(conditions_list=", ".join(common_conditions)))
# #                     selected_conditions = st.multiselect(
# #                         _("select_conditions"), 
# #                         options=common_conditions,
# #                         key="new_user_conditions"
# #                     )
# #             else:
# #                 st.info(_("confirm_past_history").format(history_list=", ".join(past_history_from_db)))
                
# #                 history_accurate = st.radio(
# #                     "Is your medical history still accurate?",
# #                     ["Yes", "No"],
# #                     key="history_accuracy_check"
# #                 )
                
# #                 if history_accurate == "No":
# #                     st.session_state.session_data['needs_history_update'] = True
# #                     st.info("Please update your medical conditions below:")
                
# #                 common_conditions = ["Diabetes", "Hypertension (High BP)", "Asthma", "Heart Disease", "Anemia", "Thyroid Issues"]
# #                 all_possible_options = sorted(list(set(common_conditions + past_history_from_db)))
# #                 selected_conditions = st.multiselect(
# #                     _("select_conditions"), 
# #                     options=all_possible_options, 
# #                     default=past_history_from_db if history_accurate == "Yes" else [],
# #                     key="existing_user_conditions"
# #                 )
            
# #             submit_past_history = st.form_submit_button(_("confirm_update_history"))

# #             if submit_past_history:
# #                 st.session_state.session_data['past_history'] = selected_conditions
# #                 st.session_state.session_data['consultation_sub_stage'] = 'collect_report_optional'
# #                 st.rerun()

# #     elif st.session_state.session_data['consultation_sub_stage'] == 'collect_report_optional':
# #         with st.form("report_optional_form"):
# #             st.subheader(_("recent_report_question"))
            
# #             if not st.session_state.session_data.get('report_data'):
# #                 uploaded_report_optional = st.file_uploader(_("upload_report"), type=['pdf', 'png', 'jpg'], key="report_uploader_optional")
                
# #                 if uploaded_report_optional:
# #                     with st.spinner(_("processing_report")):
# #                         try:
# #                             report_analysis_result = analyze_medical_report(uploaded_report_optional)
# #                             st.session_state.session_data['report_data'] = report_analysis_result
# #                             st.success(_("report_processed_success"))
# #                             update_user_report_data(st.session_state.user_profile['_id'], report_analysis_result['structured_data'])
# #                         except Exception as e:
# #                             st.error(f"Error processing report: {e}")
# #                             st.session_state.session_data['report_data'] = None
# #             else:
# #                 st.info("✓ Medical report already uploaded and processed")
            
# #             continue_to_analysis = st.form_submit_button("Continue to Analysis")
            
# #             if continue_to_analysis:
# #                 # Run the prediction engine to check if we need clarification
# #                 with st.spinner(_("running_ai_analysis")):
# #                     prediction_output = run_prediction_engine(st.session_state.session_data, st.session_state.user_profile)
                    
# #                     # THE CRITICAL FIX: Check if we need clarification
# #                     if prediction_output.get("status") == "need_clarification":
# #                         st.session_state.session_data['clarifying_questions'] = prediction_output['questions']
# #                         st.session_state.stage = 'chatbot_questions'
# #                     else:
# #                         st.session_state.session_data['triage_result'] = prediction_output
# #                         st.session_state.stage = 'results'
# #                 st.rerun()

# # # =======================================
# # # STAGE 3: CHATBOT TARGETED QUESTIONS
# # # =======================================
# # elif st.session_state.stage == 'chatbot_questions':
# #     st.header("Additional Health Questions")
# #     st.info("Please provide more details for a more accurate assessment.")

# #     # Retrieve the questions sent from the backend
# #     questions_to_ask = st.session_state.session_data.get('clarifying_questions', [])
    
# #     # Initialize a place to store answers
# #     if 'chatbot_answers' not in st.session_state.session_data:
# #         st.session_state.session_data['chatbot_answers'] = {}

# #     if not questions_to_ask:
# #         st.warning("No clarifying questions were found. Proceeding to results.")
# #         st.session_state.stage = 'results'
# #         st.rerun()
# #     else:
# #         with st.form(key="clarification_form"):
# #             # Dynamically create a text input for each question
# #             for i, question in enumerate(questions_to_ask):
# #                 answer = st.text_input(question, key=f"answer_{i}")
# #                 st.session_state.session_data['chatbot_answers'][question] = answer
            
# #             submitted_answers = st.form_submit_button("Submit Answers")

# #             if submitted_answers:
# #                 # When submitted, go back to the results stage to re-run the engine
# #                 with st.spinner("Processing your answers..."):
# #                     # Run prediction again with the clarification answers
# #                     final_prediction = run_prediction_engine(
# #                         st.session_state.session_data, 
# #                         st.session_state.user_profile,
# #                         st.session_state.session_data['chatbot_answers']
# #                     )
# #                     st.session_state.session_data['triage_result'] = final_prediction
# #                     st.session_state.stage = 'results'
# #                 st.rerun()

# # # =======================================
# # # STAGE 4: RESULTS
# # # =======================================
# # elif st.session_state.stage == 'results':
# #     st.header(_("final_triage_results"))
    
# #     # Get the prediction result
# #     prediction_output = st.session_state.session_data.get('triage_result', {})
    
# #     if not prediction_output:
# #         st.error("No assessment results found. Please start a new consultation.")
# #         if st.button(_("start_new_consultation")):
# #             st.session_state.stage = 'consultation'
# #             st.session_state.session_data = {}
# #             st.rerun()
# #         st.stop()
    
# #     risk_level = prediction_output.get('risk_level', 'Moderate Risk')
# #     reason = prediction_output.get('reason', 'Medical assessment completed.')
# #     confidence = prediction_output.get('confidence', 0.0)
# #     possible_diseases = prediction_output.get('possible_diseases', ['Unknown'])
    
# #     # Update user history in the database
# #     update_user_history(
# #         st.session_state.user_profile['_id'], 
# #         st.session_state.session_data.get('past_history', []),
# #         st.session_state.session_data
# #     )

# #     # --- Display Results ---
# #     assessment_text = _("overall_assessment")
    
# #     # Color code based on risk level
# #     if risk_level == "High Risk":
# #         st.error(f"## ⚠️ {risk_level} {assessment_text}")
# #     elif risk_level == "Moderate Risk":
# #         st.warning(f"## ⚠️ {risk_level} {assessment_text}")
# #     else:
# #         st.success(f"## ✅ {risk_level} {assessment_text}")
    
# #     risk_explanations = {
# #         'Low Risk': "Your symptoms match mostly mild cases that can typically be managed with self-care.",
# #         'Moderate Risk': "Your symptoms suggest a medical condition that requires professional evaluation.",
# #         'High Risk': "Your symptoms suggest urgent medical evaluation is required."
# #     }    
# #     st.info(risk_explanations.get(risk_level, "Risk assessment completed."))

# #     # Action recommendations
# #     st.write(_("recommended_next_steps"))
# #     if "High" in risk_level:
# #         st.error("**Seek immediate medical attention** - These symptoms require urgent evaluation by a healthcare professional.", icon="🚨")
# #     elif "Moderate" in risk_level:
# #         st.warning("**Consult a doctor within 24-48 hours** - These symptoms should be evaluated by a healthcare professional.", icon="⚠️")
# #     else:
# #         st.success("**Self-care recommended** - Continue monitoring your symptoms and maintain regular health checkups.", icon="✅")

# #     # Get recommendations
# #     user_city = st.session_state.user_profile.get('city', 'Pune')
# #     dynamic_recommendations = get_recommendations(risk_level, user_city)
# #     if dynamic_recommendations:
# #         st.write("**Suggested Facilities/Actions:**")
# #         for item in dynamic_recommendations:
# #             st.write(f"- {item}")
    
# #     # Detailed analysis
# #     with st.expander(_("view_analysis_details")):
# #         disease_text = _("possible_disease")
# #         ai_text = _("ai_reasoning")
        
# #         if possible_diseases and possible_diseases[0] != 'Unknown':
# #             st.write(f"**{disease_text}** {', '.join(possible_diseases)}")
# #         else:
# #             st.write(f"**{disease_text}** {_('Unknown')}")

# #         st.write(f"**{ai_text}** {reason}")
        
# #         # Show confidence level
# #         st.write(f"**Confidence Level:** {confidence*100:.0f}%")
        
# #         if st.session_state.session_data.get('report_data') and st.session_state.session_data['report_data'].get('structured_data'):
# #             report_text = _("extracted_report_data")
# #             st.write(f"**{report_text}**")
# #             for key, value in st.session_state.session_data['report_data']['structured_data'].items():
# #                 st.write(f"- {key.replace('_', ' ').title()}: {value}")

# #             user_age = st.session_state.user_profile.get('age')
# #             report_explanation = generate_report_explanation(st.session_state.session_data['report_data']['structured_data'], user_age)
# #             explanation_text = _("report_explanation")
# #             st.write(f"**{explanation_text}**")
# #             st.write(report_explanation)

# #             diet_recommendations = get_dietary_recommendations(st.session_state.session_data['report_data']['structured_data'])
# #             if diet_recommendations:
# #                 diet_text = _("dietary_recommendations")
# #                 st.write(f"**{diet_text}**")
# #                 for rec in diet_recommendations:
# #                     st.write(f"- {rec}")

# #     # Final features
# #     st.subheader(_("your_health_passport"))
# #     st.write(_("download_summary"))
# #     pdf_data = generate_pdf_report(st.session_state.user_profile, st.session_state.session_data)
# #     st.download_button(
# #         label=_("download_pdf_summary"),
# #         data=pdf_data,
# #         file_name=f"Health_Summary_{st.session_state.user_profile['name']}.pdf",
# #         mime="application/pdf"
# #     )

# #     # Placeholder for Share via WhatsApp/Email
# #     col1, col2 = st.columns(2)
# #     with col1:
# #         if st.button("Share via WhatsApp", key="share_whatsapp"):
# #             st.info("WhatsApp sharing functionality coming soon!")
# #     with col2:
# #         if st.button("Share via Email", key="share_email"):
# #             st.info("Email sharing functionality coming soon!")

# #     if st.button(_("start_new_consultation")):
# #         st.session_state.stage = 'consultation'
# #         st.session_state.session_data = {}
# #         st.rerun()

# #     if st.button(_("logout")):
# #         st.session_state.stage = 'login'
# #         st.session_state.user_profile = None
# #         st.session_state.session_data = {}
# #         st.rerun()

# # enhanced_app.py - Rural Healthcare Assistant with Natural Conversation Flow
# import streamlit as st
# import pandas as pd
# from datetime import datetime
# import json
# import os
# import sys
# from database import get_user_by_email, create_user, update_user_history, update_user_report_data
# # from medai_2.medai.report_data_extractor.value_extractor import 
# from backend_processing import (
#     handle_report_upload,
#     handle_user_message,
#     get_final_assessment,
#     reset_conversation,
#     get_conversation_status,
#     rural_health_assistant
# )
# from report_processor import ReportProcessor
# from report_generator import generate_pdf_report
# import speech_recognition as sr
# import io

# if 'stage' not in st.session_state:
#     st.session_state.stage = 'welcome'
# if 'conversation_history' not in st.session_state:
#     st.session_state.conversation_history = []
# if 'user_profile' not in st.session_state:
#     st.session_state.user_profile = None

# current_dir = os.path.dirname(os.path.abspath(__file__))
# parent_dir = os.path.dirname(current_dir)
# sys.path.append(parent_dir)

# report_processor = ReportProcessor()

# # Configure page
# st.set_page_config(
#     page_title="Rural Health Assistant",
#     page_icon="🏥",
#     layout="wide",
#     initial_sidebar_state="collapsed"
# )

# # Initialize session state
# def initialize_session_state():
#     """Initialize all session state variables"""
#     defaults = {
#         'stage': 'welcome',
#         'user_profile': None,
#         'conversation_history': [],
#         'all_symptoms': [],
#         'consultation_complete': False,
#         'final_assessment': None,
#         'input_mode': 'Type/Text',
#         'current_question': '',
#         'waiting_for_response': False,
#         'report_uploaded': False,
#         'report_data': None,
#         'conversation_started': False,
#         'emergency_detected': False
#     }
    
#     for key, value in defaults.items():
#         if key not in st.session_state:
#             st.session_state[key] = value

# initialize_session_state()

# # Language settings
# LANGUAGES = {
#     "English": {
#         "welcome": "Welcome to Rural Health Assistant",
#         "description": "AI-powered healthcare support designed for rural communities",
#         "start_consultation": "Start Health Consultation",
#         "name": "Full Name",
#         "age": "Age",
#         "email": "Email Address", 
#         "language": "Preferred Language",
#         "input_mode": "How would you like to communicate?",
#         "loading": "Loading...",
#         "error": "Error occurred"
#     },
#     "Hindi": {
#         "welcome": "ग्रामीण स्वास्थ्य सहायक में आपका स्वागत है",
#         "description": "ग्रामीण समुदायों के लिए डिज़ाइन किया गया AI-संचालित स्वास्थ्य सहायक",
#         "start_consultation": "स्वास्थ्य परामर्श शुरू करें",
#         "name": "पूरा नाम",
#         "age": "उम्र",
#         "email": "ईमेल पता",
#         "language": "भाषा चुनें",
#         "input_mode": "आप कैसे बात करना चाहते हैं?",
#         "loading": "लोड हो रहा है...",
#         "error": "त्रुटि हुई"
#     }
# }

# def get_text(key, lang="English"):
#     """Get translated text"""
#     return LANGUAGES.get(lang, LANGUAGES["English"]).get(key, key)

# def display_header():
#     """Display app header"""
#     st.markdown("""
#     <div style="background: linear-gradient(90deg, #4CAF50, #45a049); padding: 1rem; border-radius: 10px; margin-bottom: 2rem;">
#         <h1 style="color: white; text-align: center; margin: 0;">🏥 Rural Health Assistant</h1>
#         <p style="color: white; text-align: center; margin: 0.5rem 0 0 0;">AI-Powered Healthcare Support for Rural Communities</p>
#     </div>
#     """, unsafe_allow_html=True)

# def record_audio():
#     """Record audio input using speech recognition"""
#     try:
#         r = sr.Recognizer()
#         with sr.Microphone() as source:
#             st.info("🎤 Listening... Please speak now")
#             r.adjust_for_ambient_noise(source, duration=1)
#             audio = r.listen(source, timeout=10, phrase_time_limit=30)
            
#         # Convert speech to text
#         text = r.recognize_google(audio, language='hi-IN')  # Hindi recognition
#         return text
#     except sr.UnknownValueError:
#         st.error("Could not understand the audio. Please try again.")
#         return None
#     except sr.RequestError:
#         st.error("Could not connect to speech recognition service.")
#         return None
#     except Exception as e:
#         st.error(f"Error in voice recording: {str(e)}")
#         return None

# def handle_report_upload_ui(uploaded_file, user_name, initial_symptoms=None):
#     """Handle report upload with optional initial symptoms"""
#     try:
#         with st.spinner("Processing your medical report and symptoms..."):
#             # Save uploaded file temporarily
#             temp_file_path = f"temp_{uploaded_file.name}"
#             with open(temp_file_path, "wb") as f:
#                 f.write(uploaded_file.getbuffer())
            
#             # Process the report using report processor
#             report_analysis = report_processor.process_report(
#                 temp_file_path,
#                 user_data={
#                     "name": user_name,
#                     "initial_symptoms": initial_symptoms
#                 }
#             )
            
#             # Clean up temp file
#             os.remove(temp_file_path)
            
#             if report_analysis["status"] != "success":
#                 st.error(f"Error processing report: {report_analysis.get('message')}")
#                 return False
            
#             # Combine report data with symptoms
#             combined_data = {
#                 "report_data": report_analysis["data"],
#                 "initial_symptoms": initial_symptoms,
#                 "extracted_symptoms": []
#             }
            
#             if initial_symptoms:
#                 # Extract symptoms from initial input
#                 extracted_symptoms = rural_health_assistant.extract_symptoms_from_text(initial_symptoms)
#                 combined_data["extracted_symptoms"] = extracted_symptoms
#                 st.session_state.all_symptoms.extend(extracted_symptoms)
            
#             # Process with conversational backend
#             response = handle_report_upload(
#                 report_data=combined_data,
#                 patient_name=user_name,
#                 initial_symptoms=initial_symptoms
#             )
            
#             # Store data in session state
#             st.session_state.report_uploaded = True
#             st.session_state.report_data = combined_data
            
#             # Initialize conversation
#             st.session_state.conversation_history.append({
#                 'role': 'assistant',
#                 'content': response.get('response', 'I have analyzed your report and symptoms. How are you feeling now?'),
#                 'timestamp': datetime.now()
#             })
            
#             if initial_symptoms:
#                 st.session_state.conversation_history.append({
#                     'role': 'user',
#                     'content': initial_symptoms,
#                     'timestamp': datetime.now()
#                 })
            
#             return True
            
#     except Exception as e:
#         st.error(f"Error processing report and symptoms: {str(e)}")
#         return False

# # Update the report upload stage
# elif st.session_state.stage == 'report_upload':
#     display_header()
    
#     user_profile = st.session_state.get("user_profile") or {}
#     user_name = user_profile.get("name", "Patient")

#     st.markdown(f"### 📄 Hello {user_name}, please upload your report and describe your symptoms")
    
#     with st.form("report_upload_form"):
#         uploaded_file = st.file_uploader(
#             "Upload your medical report (blood test, prescription, etc.):",
#             type=['pdf', 'png', 'jpg', 'jpeg']
#         )
        
#         initial_symptoms = st.text_area(
#             "Please describe your current symptoms:",
#             placeholder="जैसे: मुझे दो दिन से बुखार और सिर दर्द है। (e.g., I have fever and headache for two days.)",
#             height=100
#         )
        
#         submitted = st.form_submit_button("Process Report and Start Consultation", type="primary")

#         if submitted and uploaded_file:
#             success = handle_report_upload_ui(uploaded_file, user_name, initial_symptoms)
#             if success:
#                 st.success("✅ Report and symptoms processed successfully!")
#                 st.session_state.stage = 'consultation'
#                 st.rerun()

# # Update process_user_input_ui function
# def process_user_input_ui(user_input, input_type="text"):
#     """Process user input considering both report data and conversation"""
#     try:
#         # Get report context if available
#         report_context = st.session_state.get('report_data', {})
        
#         # Process through backend with combined context
#         response = handle_user_message(
#             user_input, 
#             input_type,
#             report_context=report_context
#         )
        
#         # Update symptoms list
#         if response.get('extracted_symptoms'):
#             st.session_state.all_symptoms.extend(response['extracted_symptoms'])
#             st.session_state.all_symptoms = list(set(st.session_state.all_symptoms))
        
#         return response
        
#     except Exception as e:
#         st.error(f"Error processing input: {str(e)}")
#         return {
#             'response': "I'm having trouble understanding. Can you please repeat that?",
#             'stage': 'CONVERSING',
#             'requires_user_input': True
#         }

# # STAGE 1: WELCOME & USER SETUP
# if st.session_state.stage == 'welcome':
#     display_header()
    
#     st.markdown("### Welcome to Your Personal Health Assistant")
#     st.markdown("""
#     This AI assistant is designed specifically for rural healthcare needs:
#     - **Natural Conversation**: Talk naturally about your health concerns
#     - **Voice Support**: Speak in Hindi or English  
#     - **Simple Language**: No complex medical terms
#     - **Practical Advice**: Recommendations suitable for rural settings
#     - **Emergency Detection**: Identifies urgent situations
#     - **Report Analysis**: Upload medical reports for context
#     """)
    
#     with st.form("user_setup_form"):
#         st.subheader("Let's get started")
        
#         col1, col2 = st.columns(2)
#         with col1:
#             name = st.text_input("Full Name (पूरा नाम)")
#             age = st.number_input("Age (उम्र)", min_value=1, max_value=120, value=30)
            
#         with col2:
#             email = st.text_input("Email Address (ईमेल)")
#             language = st.selectbox("Preferred Language (भाषा)", ["English", "Hindi", "Mixed"])
        
#         st.markdown("### How would you like to communicate?")
#         input_mode = st.radio(
#             "Choose your preferred way to describe your health concerns:",
#             ["💬 Type/Text", "🎤 Voice (Speak)", "📄 Upload Report First"],
#             horizontal=True
#         )
        
#         start_button = st.form_submit_button("🚀 Start Health Consultation", use_container_width=True)
        
#         if start_button and name and email and age:
#             # Create or get user
#             user = get_user_by_email(email)
#             if not user:
#                 user = create_user(name, age, email, language)
            
#             st.session_state.user_profile = user
#             st.session_state.input_mode = input_mode
            
#             # Reset conversation state
#             reset_conversation()
            
#             # Go to appropriate stage based on input mode
#             if "Report" in input_mode:
#                 st.session_state.stage = 'report_upload'
#             else:
#                 st.session_state.stage = 'consultation'
#             st.rerun()

# # STAGE 1.5: REPORT UPLOAD (if selected)
# elif st.session_state.stage == 'report_upload':
#     display_header()
    
#     user_profile = st.session_state.get("user_profile") or {}
#     user_name = user_profile.get("name", "Patient")

#     st.markdown(f"### 📄 Hello {user_name}, please upload your report")
#     st.info("Dr. AI will review your report and start the conversation by asking you questions about it.")

#     with st.form("report_upload_form"):
#         uploaded_file = st.file_uploader(
#             "Upload your medical report (blood test, prescription, etc.):",
#             type=['pdf', 'png', 'jpg', 'jpeg']
#         )
        
#         initial_symptoms = st.text_area(
#             "If you also have current symptoms, describe them here (optional):",
#             placeholder="जैसे: मुझे दो दिन से बुखार और सिर दर्द है। (e.g., I have fever and headache for two days.)"
#         )
        
#         submitted = st.form_submit_button("Process Report and Start Conversation", type="primary")

#         if submitted and uploaded_file:
#             with st.spinner("Analyzing your report and preparing Dr. AI..."):
#                 # Process the report file
#                 temp_file_path = f"temp_{uploaded_file.name}"
#                 with open(temp_file_path, "wb") as f:
#                     f.write(uploaded_file.getbuffer())
                
#                 # Use report processor
#                 report_analysis_data = report_processor.process_report(
#                     temp_file_path,
#                     user_data={
#                         "name": user_name,
#                         "initial_symptoms": initial_symptoms if initial_symptoms else None
#                     }
#                 )
                
#                 # Clean up
#                 os.remove(temp_file_path)
        
#                 if report_analysis_data["status"] == "success":
#                     st.session_state.report_data = report_analysis_data["data"]
                    
#                     # Call backend with processed data
#                     response = handle_report_upload(
#                         report_data=report_analysis_data["data"],
#                         patient_name=user_name,
#                         initial_symptoms=initial_symptoms if initial_symptoms else None
#                     )
                
#                     # Add the AI's first message to the conversation history
#                     st.session_state.conversation_history.append({
#                         'role': 'assistant',
#                         'content': response.get('response', 'Report processed. How are you feeling today?'),
#                         'timestamp': datetime.now()
#                     })
                    
#                     # If user provided initial symptoms, add them to history too
#                     if initial_symptoms:
#                         st.session_state.conversation_history.append({
#                             'role': 'user',
#                             'content': initial_symptoms,
#                             'timestamp': datetime.now()
#                         })

#                     # Move to the main consultation stage
#                     st.session_state.stage = 'consultation'
#                     st.session_state.conversation_started = True
#                     st.rerun()

#     # Option to skip report upload
#     st.markdown("---")
#     if st.button("I don't have a report, start conversation directly"):
#         st.session_state.stage = 'consultation'
#         st.rerun()

# # Update the consultation stage section
# elif st.session_state.stage == 'consultation':
#     display_header()
    
#     # Display conversation history
#     if st.session_state.conversation_history:
#         st.markdown("### 💬 Conversation with Dr. AI")
#         for message in st.session_state.conversation_history:
#             if message['role'] == 'user':
#                 st.markdown(f"""
#                 <div style="background-color: #e3f2fd; color: black; padding: 1rem; 
#                 border-radius: 15px; margin: 1rem 0; margin-left: 20%; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">
#                 <strong>👤 You:</strong> {message['content']}
#                 </div>
#                 """, unsafe_allow_html=True)
#             else:
#                 st.markdown(f"""
#                 <div style="background-color: #f1f8e9; color: black; padding: 1rem;
#                 border-radius: 15px; margin: 1rem 0; margin-right: 20%; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">
#                 <strong>🩺 Dr. AI:</strong> {message['content']}
#                 </div>
#                 """, unsafe_allow_html=True)

#     # User input section
#     st.markdown("### ✍️ Your Response")
    
#     # Create a form for user input
#     with st.form(key="user_input_form", clear_on_submit=True):
#         col1, col2 = st.columns([4, 1])
        
#         with col1:
#             user_message = st.text_area(
#                 "Type your message:",
#                 key="message_input",
#                 height=100,
#                 placeholder="Describe your symptoms or ask a question...",
#                 label_visibility="collapsed"
#             )
        
#         with col2:
#             submit_button = st.form_submit_button(
#                 "Send 📤", 
#                 use_container_width=True,
#                 type="primary"
#             )
        
#         if submit_button and user_message:
#             # Process user input
#             st.session_state.conversation_history.append({
#                 'role': 'user',
#                 'content': user_message,
#                 'timestamp': datetime.now()
#             })
            
#             # Get AI response
#             with st.spinner("Dr. AI is thinking..."):
#                 response = process_user_input_ui(user_message, "text")
                
#                 if response:
#                     st.session_state.conversation_history.append({
#                         'role': 'assistant',
#                         'content': response.get('response', "I understand. Could you provide more details?"),
#                         'timestamp': datetime.now()
#                     })
                    
#                     # Extract and store symptoms if any
#                     if 'extracted_symptoms' in response:
#                         st.session_state.all_symptoms.extend(response['extracted_symptoms'])
#                         st.session_state.all_symptoms = list(set(st.session_state.all_symptoms))
                
#             st.rerun()

#     # Quick action buttons
#     st.markdown("---")
#     quick_actions = st.columns(4)
    
#     with quick_actions[0]:
#         if st.button("🔍 Need More Info", use_container_width=True):
#             followup = "Could you tell me more about when these symptoms started and if anything makes them better or worse?"
#             st.session_state.conversation_history.append({
#                 'role': 'assistant',
#                 'content': followup,
#                 'timestamp': datetime.now()
#             })
#             st.rerun()
    
#     with quick_actions[1]:
#         if st.button("🔄 Start Over", use_container_width=True):
#             reset_conversation()
#             st.session_state.conversation_history = []
#             st.session_state.all_symptoms = []
#             st.rerun()
            
#     with quick_actions[2]:
#         if st.button("📋 Get Assessment", use_container_width=True):
#             if len(st.session_state.conversation_history) > 4:
#                 st.session_state.stage = 'assessment'
#                 st.rerun()
#             else:
#                 st.warning("Please provide more information for a proper assessment.")
    
#     with quick_actions[3]:
#         if st.button("❓ Help", use_container_width=True):
#             st.info("""
#             - Type your symptoms and concerns naturally
#             - You can use Hindi or English
#             - Be specific about your symptoms
#             - Mention when symptoms started
#             - Share any relevant medical history
#             """)
            
# # STAGE 3: EMERGENCY ALERT
# elif st.session_state.stage == 'emergency':
#     display_header()
    
#     st.markdown("""
#     <div style="background-color: #ffebee; border: 3px solid #f44336; padding: 2rem; border-radius: 15px; text-align: center;">
#     <h1 style="color: #f44336;">⚠️ MEDICAL EMERGENCY DETECTED ⚠️</h1>
#     <h2 style="color: #d32f2f;">आपातकालीन चिकित्सा सेवा की आवश्यकता</h2>
#     </div>
#     """, unsafe_allow_html=True)
    
#     # Display the emergency response if available
#     if st.session_state.conversation_history:
#         last_message = st.session_state.conversation_history[-1]
#         if last_message['role'] == 'assistant':
#             st.markdown(f"""
#             <div style="background-color: #ffcdd2; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #f44336; margin: 2rem 0;">
#             <h3>🚨 Dr. AI's Emergency Assessment:</h3>
#             <p style="font-size: 16px;">{last_message['content']}</p>
#             </div>
#             """, unsafe_allow_html=True)
    
#     st.markdown("""
#     ### 🚨 IMMEDIATE ACTIONS REQUIRED:
    
#     **1. Go to the nearest hospital immediately**  
#     **तुरंत नजदीकी अस्पताल जाएं**
    
#     **2. Call Emergency Services:**
#     - 🚑 National Emergency: **108**
#     - 🏥 Ambulance: **102**
#     - 👮 Police: **100**
    
#     **3. While going to hospital:**
#     - Take someone with you if possible (कोई साथ ले जाएं)
#     - Carry any medicines you're taking (दवाइयां साथ ले जाएं)
#     - Bring ID and medical reports (पहचान पत्र और रिपोर्ट्स)
#     - **DO NOT drive yourself** (खुद गाड़ी न चलाएं)
    
#     **4. Stay calm but act quickly** (घबराएं नहीं, लेकिन तुरंत कार्य करें)
#     """)
    
#     # Emergency contact numbers for rural areas
#     st.markdown("""
#     ### 📞 Rural Emergency Contacts:
#     - **Primary Health Center (PHC)**: Contact your nearest PHC
#     - **District Hospital**: For serious emergencies
#     - **ASHA Worker**: Your local ASHA can help coordinate
#     - **Village Sarpanch**: For transportation assistance
#     """)
    
#     # Still provide basic assessment option
#     st.markdown("---")
#     col1, col2 = st.columns(2)
#     with col1:
#         if st.button("📋 Show Basic Assessment", type="secondary"):
#             st.session_state.stage = 'assessment'
#             st.rerun()
    
#     with col2:
#         if st.button("💬 Continue Conversation", type="secondary"):
#             st.session_state.emergency_detected = False
#             st.session_state.stage = 'consultation'
#             st.rerun()

# # STAGE 4: FINAL ASSESSMENT
# elif st.session_state.stage == 'assessment':
#     display_header()
    
#     user_name = st.session_state.user_profile.get('name', 'Patient')
    
#     st.markdown(f"## 📊 Health Assessment for {user_name}")
    
#     # Generate final assessment if not done
#     if not st.session_state.final_assessment:
#         with st.spinner("Preparing your comprehensive health assessment..."):
#             try:
#                 assessment_result = get_final_assessment()
                
#                 if assessment_result.get('error'):
#                     st.warning(assessment_result.get('error'))
#                     st.markdown("### Continue conversation to get a complete assessment")
#                     if st.button("Continue Conversation"):
#                         st.session_state.stage = 'consultation'
#                         st.rerun()
#                     st.stop()
                
#                 st.session_state.final_assessment = assessment_result.get('assessment')
#             except Exception as e:
#                 st.error(f"Error generating assessment: {str(e)}")
#                 st.stop()
    
#     assessment = st.session_state.final_assessment
    
#     # Display risk level with color coding
#     risk_level = assessment.get('risk_level', 'Moderate Risk')
#     if 'High' in risk_level:
#         st.error(f"🚨 **{risk_level}**")
#     elif 'Moderate' in risk_level:
#         st.warning(f"⚠️ **{risk_level}**")
#     else:
#         st.success(f"✅ **{risk_level}**")
    
#     # Main assessment display
#     col1, col2 = st.columns([2, 1])
    
#     with col1:
#         st.markdown("### 🩺 Medical Assessment")
#         st.markdown(f"**Primary Concern:** {assessment.get('primary_concern', 'General health evaluation')}")
#         st.markdown(f"**Explanation:** {assessment.get('explanation', 'Assessment completed based on reported symptoms.')}")
        
#         st.markdown("### 🏥 Possible Conditions")
#         conditions = assessment.get('possible_conditions', ['General medical consultation recommended'])
#         for condition in conditions:
#             st.markdown(f"• {condition}")
        
#         st.markdown("### ✅ Immediate Actions You Can Take")
#         actions = assessment.get('immediate_actions', ['Rest and monitor symptoms'])
#         for action in actions:
#             st.markdown(f"• {action}")
    
#     with col2:
#         st.markdown("### ⏰ When to See Doctor")
#         st.info(assessment.get('when_to_see_doctor', 'Consult healthcare provider for proper evaluation'))
        
#         st.markdown("### 🏘️ Rural Health Advice")
#         st.info(assessment.get('rural_specific_advice', 'Contact nearest Primary Health Center'))
        
#         confidence = assessment.get('confidence', 0.7)
#         st.markdown(f"### 📊 Assessment Confidence")
#         st.progress(confidence)
#         st.caption(f"{confidence*100:.0f}% confidence based on our conversation")
    
#     # Additional sections
#     st.markdown("---")
    
#     # Conversation summary
#     with st.expander("📝 Conversation Summary", expanded=False):
#         if st.session_state.conversation_history:
#             for i, msg in enumerate(st.session_state.conversation_history):
#                 role_emoji = "👤" if msg['role'] == 'user' else "🩺"
#                 timestamp = msg.get('timestamp', datetime.now()).strftime("%H:%M")
#                 st.markdown(f"**{role_emoji} {msg['role'].title()} ({timestamp}):** {msg['content']}")
#         else:
#             st.markdown("No conversation history available.")
    
#     # Show extracted symptoms
#     if st.session_state.all_symptoms:
#         with st.expander("🔍 Symptoms Identified", expanded=False):
#             st.markdown("Based on our conversation, these symptoms were identified:")
#             for symptom in st.session_state.all_symptoms:
#                 st.markdown(f"• {symptom}")
    
#     # Recommendations
#     st.markdown("### 🎯 Personalized Recommendations")
    
#     col1, col2 = st.columns(2)
#     with col1:
#         st.markdown("""
#         **Self-Care Tips (घरेलू देखभाल):**
#         - Rest adequately (पर्याप्त आराम करें)
#         - Stay hydrated (पानी पिते रहें)  
#         - Eat light, nutritious food (हल्का पौष्टिक खाना खाएं)
#         - Monitor symptoms closely (लक्षणों पर नजर रखें)
#         - Take prescribed medicines on time (दवा समय पर लें)
#         """)
    
#     with col2:
#         st.markdown("""
#         **🚨 Red Flags - See Doctor Immediately:**
#         - Severe chest pain (तेज सीने का दर्द)
#         - Difficulty breathing (सांस लेने में तकलीफ)
#         - High fever >102°F (तेज बुखार)
#         - Severe headache (तेज सिरदर्द)
#         - Persistent vomiting (लगातार उल्टी)
#         - Severe weakness (बहुत कमजोरी)
#         """)
    
#     # Action buttons
#     st.markdown("---")
#     col1, col2, col3, col4 = st.columns(4)
    
#     with col1:
#         try:
#             report_data = {
#                 'assessment': assessment,
#                 'conversation': st.session_state.conversation_history,
#                 'symptoms': st.session_state.all_symptoms,
#                 'report_data': st.session_state.report_data
#             }
#             pdf_data = generate_pdf_report(st.session_state.user_profile, report_data)
#             st.download_button(
#                 "📄 Download Report",
#                 data=pdf_data,
#                 file_name=f"Health_Assessment_{user_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
#                 mime="application/pdf"
#             )
#         except Exception as e:
#             st.error(f"Error generating PDF: {str(e)}")
    
#     with col2:
#         if st.button("💬 Continue Consultation"):
#             st.session_state.stage = 'consultation'
#             st.rerun()
    
#     with col3:
#         if st.button("🔄 New Consultation"):
#             # Reset session data
#             reset_conversation()
#             st.session_state.conversation_history = []
#             st.session_state.all_symptoms = []
#             st.session

# app.py
# Streamlit front-end — shows triage + rich nearby facility list + embedded map
import os
import sys
import tempfile
import traceback
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT)

# Local modules (optional)
try:
    from report_processor import ReportProcessor
except Exception:
    ReportProcessor = None

try:
    import backend_processing
    integrate_report_and_run_assessment = backend_processing.integrate_report_and_run_assessment
    handle_user_message = backend_processing.handle_user_message
except Exception:
    integrate_report_and_run_assessment = None
    handle_user_message = None

try:
    from database import get_user_by_email, create_user, update_user_history, update_user_report_data
except Exception:
    get_user_by_email = create_user = update_user_history = update_user_report_data = None

try:
    from report_generator import generate_pdf_report
except Exception:
    generate_pdf_report = None

# recommendations.py should expose get_recommendations (Google or OSM fallback)
try:
    from recommendations import get_recommendations
except Exception:
    def get_recommendations(risk, user_city="", user_state="", user_pincode=""):
        return []

# Map embed key (prefer MAPS_EMBED_KEY, fallback to GOOGLE_API_KEY)
MAPS_EMBED_KEY = os.getenv("MAPS_EMBED_KEY") or os.getenv("GOOGLE_API_KEY")

# ---------------- UI helpers ----------------
def show_emergency_banner():
    st.markdown("""
    <div style='background:#b30000;padding:12px;border-radius:8px;color:white;margin-bottom:10px'>
      <h3 style='margin:0'>🚨 EMERGENCY — SEEK IMMEDIATE CARE</h3>
      <div style='font-size:14px'>Call emergency services immediately or go to the nearest hospital.</div>
    </div>
    """, unsafe_allow_html=True)

def show_assessment_card(assessment: dict):
    rl = assessment.get("risk_level", "Unknown")
    proba = assessment.get("risk_proba", 0.0)
    color = {"Emergency":"#b30000","High":"#ff4d4d","Medium":"#ffb84d","Low":"#4caf50"}.get(rl,"#777")
    st.markdown(f"<div style='padding:12px;border-radius:10px;background:#0f1720;color:#e6eef8'>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color:{color};margin:6px 0'>{rl} risk — {proba:.0%} probability</h3>", unsafe_allow_html=True)
    reason = assessment.get("reason","")
    if reason:
        st.markdown(f"<div style='color:#cbd5e1;margin-bottom:8px'>{reason}</div>", unsafe_allow_html=True)

    conds = assessment.get("possible_conditions", [])
    if conds:
        badges = ""
        for c in conds:
            name = c.get("disease","Unknown")
            conf = c.get("confidence", 0.0)
            badges += f"<span style='display:inline-block;margin:4px 6px;padding:6px 10px;border-radius:14px;background:#111827;color:#fff;font-size:13px'>{name} {conf:.0%}</span>"
        st.markdown(badges, unsafe_allow_html=True)

    st.markdown("### Recommendations")
    recs = assessment.get("recommendations", []) or []
    if recs:
        for r in recs:
            st.markdown(f"- {r}")
    else:
        st.markdown("- Follow up with local health provider")

    with st.expander("Show detailed JSON"):
        st.json(assessment)
    st.markdown("</div>", unsafe_allow_html=True)

def render_facility_card(f):
    """
    f may be a dict (enriched) or a string.
    If dict, expect keys: name,address,phone,distance_km,maps_url,lat,lng
    """
    if isinstance(f, dict):
        name = f.get("name","Unknown")
        addr = f.get("address","")
        phone = f.get("phone")
        dist = f.get("distance_km")
        maps_url = f.get("maps_url") or f.get("maps") or f.get("maps_link")
# Add Clinician Dashboard Link
st.sidebar.markdown("---")
st.sidebar.markdown("### For Clinicians")
st.sidebar.markdown("**Clinician Dashboard:**")
st.sidebar.markdown("Access the clinician dashboard at:")
st.sidebar.code("http://localhost:8512")
st.sidebar.markdown("*Default password: medaid123*")

st.markdown("---")


def show_past_history_form():
    """Show form to collect and save past medical history"""
    st.subheader("📋 Update Your Medical History")
    st.markdown("Please provide your past medical history to help us give you better assessments.")
    
    # Defensive normalization of past_history

    raw_ph = st.session_state.user.get("past_history", {}) if st.session_state.user else {}
    past_history = raw_ph if isinstance(raw_ph, dict) else {}
    
    with st.form("past_history_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            chronic_conditions = st.text_area(
                "Chronic Conditions/Diseases",
                value=past_history.get("chronic_conditions", ""),
                help="e.g., Diabetes, Hypertension, Asthma, Heart Disease",
                height=100
            )
            
            allergies = st.text_area(
                "Known Allergies",
                value=st.session_state.user.get("past_history", {}).get("allergies", ""),
                help="e.g., Penicillin, Peanuts, Latex",
                height=80
            )
            
            surgeries = st.text_area(
                "Past Surgeries/Procedures",
                value=st.session_state.user.get("past_history", {}).get("surgeries", ""),
                help="Include year if possible",
                height=80
            )
        
        with col2:
            current_medications = st.text_area(
                "Current Medications",
                value=st.session_state.user.get("past_history", {}).get("current_medications", ""),
                help="Include dosage if known",
                height=100
            )
            
            family_history = st.text_area(
                "Family Medical History",
                value=st.session_state.user.get("past_history", {}).get("family_history", ""),
                help="Significant conditions in immediate family",
                height=80
            )
            
            lifestyle = st.text_area(
                "Lifestyle Information",
                value=st.session_state.user.get("past_history", {}).get("lifestyle", ""),
                help="Smoking, alcohol, exercise habits",
                height=80
            )
        
        additional_notes = st.text_area(
            "Additional Medical Notes",
            value=st.session_state.user.get("past_history", {}).get("additional_notes", ""),
            help="Any other relevant medical information",
            height=60
        )
        
        col_save, col_skip = st.columns([1, 1])
        
        with col_save:
            save_history = st.form_submit_button("💾 Save Medical History", type="primary")
        
        with col_skip:
            skip_history = st.form_submit_button("⏭️ Skip for Now")
    
    if save_history:
        # Create past history dictionary
        past_history = {
            "chronic_conditions": chronic_conditions.strip(),
            "allergies": allergies.strip(), 
            "surgeries": surgeries.strip(),
            "current_medications": current_medications.strip(),
            "family_history": family_history.strip(),
            "lifestyle": lifestyle.strip(),
            "additional_notes": additional_notes.strip(),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Update user session
        st.session_state.user["past_history"] = past_history
        st.session_state.history_collected = True
        
        # Try to save to database
        try:
            if update_user_history:
                ph_to_save = st.session_state.user.get("past_history", {})
                if not isinstance(ph_to_save, dict):
                    ph_to_save = {}
                update_user_history(st.session_state.user.get("_id"), ph_to_save, record)

        except Exception as e:
            st.warning(f"Could not save to database: {e}")
        
        st.success("✅ Medical history saved successfully!")
        st.balloons()
        st.rerun()
    
    elif skip_history:
        st.session_state.history_collected = True
        st.info("Skipped medical history collection. You can update it later.")
        st.rerun()

# ---------------- Session state ----------------
st.set_page_config(page_title="Rural Health Assistant", layout="wide")
st.title("🏥 Rural Health Assistant")

if "user" not in st.session_state:
    st.session_state.user = None
if "report_data" not in st.session_state:
    st.session_state.report_data = None
if "final_assessment" not in st.session_state:
    st.session_state.final_assessment = None
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "last_triage_record" not in st.session_state:
    st.session_state.last_triage_record = None
if "history_collected" not in st.session_state:
    st.session_state.history_collected = False

# ---------------- Sidebar: Login/Register ----------------
with st.sidebar.expander("Account", expanded=True):
    st.subheader("Login / Register")
    su_name = st.text_input("Full name", value=st.session_state.user.get("name","") if st.session_state.user else "")
    su_age = st.number_input("Age", min_value=0, max_value=120, value=st.session_state.user.get("age",0) if st.session_state.user else 0)
    su_email = st.text_input("Email", value=st.session_state.user.get("email","") if st.session_state.user else "")
    su_lang = st.selectbox("Language", ["English","Hindi"], index=0)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Register / Create"):
            if not su_name or not su_email:
                st.sidebar.error("Provide name & email")
            else:
                existing = None
                try:
                    existing = get_user_by_email(su_email) if get_user_by_email else None
                except Exception:
                    existing = None
                if existing:
                    st.session_state.user = existing
                    # Check if user has past history
                    if existing.get("past_history"):
                        st.session_state.history_collected = True
                    else:
                        st.session_state.history_collected = False
                    st.sidebar.success("Logged in existing user")
                else:
                    if create_user:
                        created = create_user(su_name, int(su_age), su_email, su_lang)
                        st.session_state.user = created
                        st.session_state.history_collected = False
                        st.sidebar.success("User created & logged in")
                    else:
                        st.session_state.user = {"_id": su_email, "name": su_name, "age": int(su_age), "email": su_email, "language": su_lang, "past_history": {}}
                        st.session_state.history_collected = False
                        st.sidebar.success("Local session user created")
    with c2:
        if st.button("Login"):
            try:
                u = get_user_by_email(su_email) if get_user_by_email else None
            except Exception:
                u = None
            if u:
                st.session_state.user = u
                # Check if user has past history
                if u.get("past_history"):
                    st.session_state.history_collected = True
                else:
                    st.session_state.history_collected = False
                st.sidebar.success("Logged in")
            else:
                st.session_state.user = {"_id": su_email, "name": su_name, "age": int(su_age), "email": su_email, "language": su_lang, "past_history": {}}
                st.session_state.history_collected = False
                st.sidebar.info("Local session user created (no DB)")
    
    if st.session_state.user:
        st.markdown("---")
        st.markdown(f"**Signed in:** {st.session_state.user.get('name')}  \n{st.session_state.user.get('email')}")
        
        # Show past history summary if available
        past_history = st.session_state.user.get("past_history", {})
        if past_history and any(past_history.values()):
            st.markdown("**Medical History:** ✅ Collected")
            if st.button("📝 Update History"):
                st.session_state.history_collected = False
        else:
            st.markdown("**Medical History:** ❌ Not collected")
        
        if st.button("Logout"):
            st.session_state.user = None
            st.session_state.history_collected = False
            st.sidebar.success("Logged out")

st.markdown("---")

# ---------------- Check if we need to collect past history ----------------
if st.session_state.user and not st.session_state.history_collected:
    show_past_history_form()
else:
    # ---------------- Main consultation form ----------------
    rp = ReportProcessor() if ReportProcessor else None

    col_left, col_right = st.columns([2,1])
    with col_left:
        st.header("Consultation Room")
        st.markdown("Provide current symptoms (text). Optionally upload a medical report.")

        with st.form("consult_form"):
            symptoms_text = st.text_area("Describe current symptoms (required if no report)", height=140)
            report_file = st.file_uploader("Upload medical report (PDF / image) — optional", type=["pdf","png","jpg","jpeg"])
            location_input = st.text_input("City / Pincode (for recommendations)", value="")
            analyze_now = st.form_submit_button("Analyze Now")

        if analyze_now:
            if not st.session_state.user:
                st.error("Please login/register in the sidebar first.")
            elif not symptoms_text and not report_file:
                st.error("Provide symptoms text or upload a report.")
            else:
                final_symptoms = symptoms_text or ""

                # Report extraction
                report_json = None
                if report_file:
                    tmpf = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(report_file.name)[1])
                    tmpf.write(report_file.getbuffer()); tmpf.flush(); tmpf.close()
                    st.info("Processing report (OCR/extraction)...")
                    try:
                        if rp:
                            res = rp.process_report(tmpf.name, user_data={"name": st.session_state.user.get("name")})
                            if res.get("status") == "success":
                                report_json = res.get("data")
                                st.success("Report processed")
                                try:
                                    if update_user_report_data:
                                        update_user_report_data(st.session_state.user.get("_id"), report_json)
                                except Exception:
                                    pass
                            else:
                                st.warning("Report processor returned: " + str(res.get("message","")))
                        else:
                            st.info("No report processor available.")
                    except Exception as e:
                        st.error("Report processing error: " + str(e))
                        traceback.print_exc()
                    try:
                        os.unlink(tmpf.name)
                    except:
                        pass

                st.session_state.report_data = report_json

                # Prepare user data including past history for assessment
                user_data_for_assessment = st.session_state.user.copy()
                # Include past history in the assessment data
                if st.session_state.user.get("past_history"):
                    user_data_for_assessment["past_medical_history"] = st.session_state.user["past_history"]

                # Run assessment
                st.info("Running assessment...")
                try:
                    result = None
                    if integrate_report_and_run_assessment:
                        # Pass the enhanced user data that includes past history
                        result = integrate_report_and_run_assessment(
                            report_json, 
                            {"symptoms_text": final_symptoms, "city": location_input}, 
                            user_data_for_assessment
                        )
                    else:
                        result = {"status":"error","message":"backend_integration_missing","debug":"integrate_report_and_run_assessment not available"}
                    
                    if result.get("status") == "error":
                        st.error("Assessment error: " + str(result.get("message")))
                        st.session_state.conversation.append({"role":"assistant","content": f"Assessment error: {result.get('message')}", "time": datetime.utcnow().isoformat()})
                    else:
                        assessment = result.get("assessment")
                        st.session_state.final_assessment = assessment
                        st.success("Assessment complete")
                        st.session_state.conversation.append({"role":"assistant","content":assessment.get("reason","Assessment complete"), "time": datetime.utcnow().isoformat()})
                        # save record
                        try:
                            record = {
                                "user_id": st.session_state.user.get("_id") if st.session_state.user else "guest",
                                "date": datetime.utcnow().isoformat(),
                                "current_symptoms": final_symptoms,
                                "report_data": report_json,
                                "past_history_considered": st.session_state.user.get("past_history", {}),
                                "triage_result": assessment
                            }
                            if update_user_history:
                                update_user_history(st.session_state.user.get("_id"), st.session_state.user.get("past_history", []), record)
                            st.session_state.last_triage_record = record
                        except Exception:
                            pass
                except Exception as e:
                    st.error("Assessment call failed unexpectedly: " + str(e))
                    st.code(traceback.format_exc())

    with col_right:
        st.header("Results & Health Passport")
        
        # Show past history summary
        if st.session_state.user and st.session_state.user.get("past_history"):
            with st.expander("📋 Your Medical History", expanded=False):
                ph = st.session_state.user["past_history"]
                if ph.get("chronic_conditions"):
                    st.markdown(f"**Conditions:** {ph['chronic_conditions']}")
                if ph.get("allergies"):
                    st.markdown(f"**Allergies:** {ph['allergies']}")
                if ph.get("current_medications"):
                    st.markdown(f"**Medications:** {ph['current_medications']}")
                if ph.get("last_updated"):
                    st.caption(f"Last updated: {ph['last_updated'][:10]}")
        
        if st.session_state.final_assessment:
            a = st.session_state.final_assessment
            if a.get("risk_level") == "Emergency":
                show_emergency_banner()
            show_assessment_card(a)

            # Nearby facilities + map
            if a.get("risk_level") in ("Medium", "High", "Emergency"):
                st.markdown("### Nearby facilities")
                # Use the location input directly (from the form)
                user_location = location_input.strip()
                if not user_location:
                    st.info("Enter City or Pincode above to fetch nearby facilities.")
                else:
                    try:
                        # Pass same string for both city and pincode so recommendations.py always gets something
                        facilities = get_recommendations(
                            a.get("risk_level"),
                            user_city=user_location,
                            user_state="Maharashtra",
                            user_pincode=user_location
                        )

                        st.write("📍 Debug: Location used =", user_location)
                        st.write("📍 Debug: Facilities returned =", len(facilities))

                        if not facilities:
                            st.warning("No facilities found for this location.")
                        else:
                            for f in facilities[:10]:
                                if isinstance(f, dict):
                                    st.markdown(f"**{f.get('name','Unknown')}**")
                                    if f.get("address"):
                                        st.markdown(f"📍 {f['address']}")
                                    if f.get("distance_km"):
                                        st.markdown(f"📏 Distance: {f['distance_km']} km")
                                    if f.get("maps_url"):
                                        st.markdown(f"[🗺️ Open Map]({f['maps_url']})")
                                    st.markdown("---")
                                else:
                                    st.markdown(f"- {f}")
                    except Exception as e:
                        st.error("Facility lookup failed: " + str(e))
                        st.code(traceback.format_exc())

        else:
            st.info("No assessment yet. Provide input and click Analyze Now.")

    st.markdown("---")
    st.subheader("Conversation & Log")
    for msg in st.session_state.conversation[-12:]:
        role = msg.get("role","user")
        t = msg.get("time","")
        if role == "assistant":
            st.markdown(f"**Dr. AI:** {msg.get('content')}  \n_{t}_")
        else:
            st.markdown(f"**You:** {msg.get('content')}  \n_{t}_")

    st.caption("Prototype only — not a medical device. For emergencies call local emergency services immediately.") 