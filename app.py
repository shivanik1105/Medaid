# app.py
import streamlit as st
from database import get_user_by_email, create_user, update_user_history
from backend_processing import extract_symptoms_from_text
# --- State Machine & Session Setup ---
# We use 'stage' to control which part of the UI is shown.
if 'stage' not in st.session_state:
    st.session_state.stage = 'login'
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = None
if 'session_data' not in st.session_state:
    st.session_state.session_data = {}

# --- Main App Title ---
st.title("🩺 AI Health Triage System")

# --- Step 1: User Login Stage ---
if st.session_state.stage == 'login':
    st.info("Welcome! Please provide your details to begin your consultation.")
    
    with st.form(key="login_form"):
        name = st.text_input("👤 Full Name")
        age = st.number_input("🎂 Age", min_value=1, max_value=120, step=1)
        email = st.text_input("📧 Email Address")
        language = st.selectbox("🗣 Preferred Language", ["English", "Marathi", "Hindi"])
        
        submitted = st.form_submit_button("Start Session")

        if submitted:
            if name and age and email:
                with st.spinner("Setting up your session..."):
                    user = get_user_by_email(email)
                    if user:
                        # If user is found, load their profile
                        st.session_state.user_profile = user
                        st.success(f"Welcome back, {user['name']}!")
                    else:
                        # If user is not found, create a new profile
                        st.session_state.user_profile = create_user(name, age, email, language)
                        st.success(f"Welcome, {name}! Your profile has been created.")
                    
                    # Move to the next step in the workflow
                    st.session_state.stage = 'collect_symptoms'
                    st.session_state.stage = 'consultation'
                    st.rerun()
            else:
                st.warning("Please fill in all the details.")

# --- Placeholder for the next phase ---
elif st.session_state.stage == 'collect_symptoms':
    st.header(f"Welcome, {st.session_state.user_profile['name']}!")
    st.success("Phase 1 is complete. You are successfully logged in.")
    st.info("The next phase will begin here, where we build the UI to collect your current symptoms.")

elif st.session_state.stage == 'consultation':
    st.header("Initial Consultation")
    st.info("Please provide the following information to help us understand your condition.")

    with st.form("consultation_form"):
        # Step 2: Collect Current Symptoms
        st.subheader("1. How are you feeling today?")
        symptoms_text = st.text_area("Describe your current symptoms:", height=150)

        # Step 3: Handle Past Medical History
        st.subheader("2. Do you have any pre-existing conditions?")
        common_conditions = ["Diabetes", "Hypertension (High BP)", "Asthma", "Thyroid Issues", "Anemia"]
        selected_conditions = st.multiselect("Select from the list:", options=common_conditions)
        other_conditions = st.text_input("Any other conditions? (comma-separated)")

        # Step 4: Handle Report Upload
        st.subheader("3. Do you have a recent medical report?")
        uploaded_report = st.file_uploader("Upload report (PDF or Image)", type=['pdf', 'png', 'jpg', 'jpeg'])
        
        submitted = st.form_submit_button("Submit for Analysis")

        if submitted:
            with st.spinner("Collecting and processing your information..."):
                # Process and store all data
                st.session_state.session_data['current_symptoms'] = extract_symptoms_from_text(symptoms_text)
                
                final_history = selected_conditions
                if other_conditions:
                    final_history.extend([item.strip() for item in other_conditions.split(',')])
                
                update_user_history(st.session_state.user_profile['_id'], final_history)
                st.session_state.session_data['past_history'] = final_history

                if uploaded_report is not None:
                    # In a real scenario, you'd call Teammate 1's function here
                    # For now, we'll just store the file name
                    st.session_state.session_data['report_info'] = {"filename": uploaded_report.name}
                
                st.session_state.stage = 'analysis' # Move to the next phase
                st.rerun()

elif st.session_state.stage == 'analysis':
    st.header(f"Thank you, {st.session_state.user_profile['name']}.")
    st.success("Phase 2 is complete. We have collected your initial information.")
    st.info("The next phase will begin here, where the AI asks clarifying questions and provides its prediction.")
    st.subheader("Data Collected in this Session:")
    st.json(st.session_state.session_data)
