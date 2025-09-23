# dashboard.py
import streamlit as st
from database import get_health_passport_data
from datetime import datetime

def show_health_dashboard(user_id, user_profile):
    """Displays the health passport dashboard"""
    passport_data = get_health_passport_data(user_id)
    
    if not passport_data:
        st.warning("No health passport data available yet.")
        return
    
    st.header("🏥 Your Health Passport")
    
    # Current Status Card
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Consultations", passport_data['total_consultations'])
    with col2:
        if passport_data['last_risk_level']:
            risk_color = {
                'High Risk': '🔴',
                'Moderate Risk': '🟡', 
                'Low Risk': '🟢'
            }.get(passport_data['last_risk_level'], '⚪')
            st.metric("Last Risk Level", f"{risk_color} {passport_data['last_risk_level']}")
    with col3:
        if passport_data['last_consultation_date']:
            days_ago = (datetime.now() - passport_data['last_consultation_date']).days
            st.metric("Last Consultation", f"{days_ago} days ago")
    
    # Active Conditions
    if passport_data['active_conditions']:
        st.subheader("Active Medical Conditions")
        for condition in passport_data['active_conditions']:
            st.write(f"• {condition}")
    
    # Consultation History (you can expand this later)
    st.subheader("Recent Activity")
    st.info("Complete consultation history will be available here soon.")