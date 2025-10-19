"""
Clinician Dashboard for Medaid
A separate Streamlit app for clinicians to view real-time triage assessments
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import time
from database import get_all_triage_records

# Set page config
st.set_page_config(
    page_title="Medaid Clinician Dashboard",
    page_icon="🧑‍⚕️",
    layout="wide"
)

# Apply custom CSS
st.markdown("""
<style>
    /* Change default text color to black */
    body, h3:not(.recent-assessments-title), h4:not(.assessment-header):not(.recommendations-header), h5, h6, div:not(.dashboard-info-text):not(.recent-assessments-title):not(.risk-level-header):not(.source-text):not(.reason-text):not(.condition-badge), span:not(.dashboard-info-text):not(.condition-badge), li, td, th {
        color: #fffff !important;
    }
    
    /* Keep the main title (h1) in white */
    h1 {
        color: #ffffff !important;
    }
    
    /* Make the Overview title (h2) white */
    h2,
    div[data-testid="stSubheader"] h2,
    .overview-title {
        color: #ffffff !important;
    }
    
    /* Make specific dashboard info text white */
    .dashboard-info-text {
        color: #ffffff !important;
    }
    
    /* Make the Recent Patient Assessments title white */
    .recent-assessments-title {
        color: #ffffff !important;
    }
    
    /* Make the assessment header text white */
    .assessment-header {
        color: #ffffff !important;
    }
    
    /* Make assessment card content white */
    .source-text,
    .reason-text,
    .recommendations-header,
    .recommendation-item {
        color: #ffffff !important;
    }
    
    /* Add separate rule for condition-badge to make it black */
    .condition-badge {
        color: #000000 !important;
    }
    
    /* Risk level header in white for consistency */
    .risk-level-header,
    h3.risk-level-header {
        color: #ffffff !important;
    }
    
    /* Make rerun and always rerun text white */
    button[kind="secondary"] {
        color: #ffffff !important;
    }
    
    /* Patient card styling */
    .patient-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color: #000000; /* Changed back to black */
    }
    .emergency {
        border-left: 5px solid #ff4b4b;
        background-color: #fff5f5;
    }
    .high-risk {
        border-left: 5px solid #ff9500;
        background-color: #fff9f2;
    }
    .medium-risk {
        border-left: 5px solid #ffc107;
        background-color: #fffdf5;
    }
    .low-risk {
        border-left: 5px solid #28a745;
        background-color: #f6fff9;
    }
    
    /* Ensure assessment cards have black text */
    .patient-card h4 {
        color: #000000 !important;
    }
    .patient-card p {
        color: #000000 !important;
    }
    
    /* Dashboard info text in white */
    .dashboard-info-text {
        color: #ffffff !important;
    }
    
    /* Metric cards with black text */
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        color: #000000;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #000000 !important;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #000000 !important;
    }
    
    /* Sidebar text in black */
    section[data-testid="stSidebar"] * {
        color: #000000 !important;
    }
    
    /* Subheader text in white */
    div[data-testid="stSubheader"] {
        color: #ffffff !important;
    }
    
    /* Info and warning messages in white */
    .stAlert div {
        color: #ffffff !important;
    }
    
    /* Error messages in white */
    .stError div {
        color: #ffffff !important;
    }
    
    /* Sidebar metric text in black */
    section[data-testid="stSidebar"] .metric-value,
    section[data-testid="stSidebar"] .metric-label {
        color: #000000 !important;
    }
    
    /* Expandable section headers in white */
    div[data-testid="stExpander"] > details > summary,
    div[data-testid="stExpander"] > details > summary * {
        color: #ffffff !important;
    }
    
    /* Streamlit buttons text in white */
    div[data-testid="stButton"] button {
        color: #ffffff !important;
    }
    
    /* More specific rule for the Refresh button */
    div[data-testid="stButton"] button[kind="secondary"] {
        color: #ffffff !important;
    }
    
    /* Universal button text color */
    button {
        color: #ffffff !important;
    }
    
    /* Specific rules for Streamlit's built-in rerun buttons */
    button[data-testid="stAppViewToolbarRerunButton"],
    button[data-testid="stAppViewToolbarAlwaysRerunButton"] {
        color: #ffffff !important;
    }
    
    /* Password input text in white */
    input[type="password"] {
        color: #ffffff !important;
    }
    
    /* Password label in white */
    label[for*="password"] {
        color: #ffffff !important;
    }
    
    /* Password input text in white (more specific) */
    div[data-testid="stTextInput"] input[type="password"],
    div[data-testid="stTextInput"] label,
    div[data-testid="stTextInput"] div,
    #password {
        color: #ffffff !important;
    }
    
    /* Make sidebar filter text white */
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4,
    section[data-testid="stSidebar"] h5,
    section[data-testid="stSidebar"] h6,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] select,
    section[data-testid="stSidebar"] option,
    section[data-testid="stSidebar"] img,
    section[data-testid="stSidebar"] svg {
        color: #ffffff !important;
    }
    
    /* Ensure all sidebar content is white - more specific rule */
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Remove conflicting rules that make sidebar text black */
    
    /* Specific selectors for the filter section */
    section[data-testid="stSidebar"] select,
    section[data-testid="stSidebar"] label,
    .stSelectbox label,
    .stSelectbox div {
        color: #ffffff !important;
    }
    
    /* Dashboard info in sidebar */
    .sidebar-dashboard-info {
        color: #ffffff !important;
    }
    
    /* Expandable section text in white */
    .streamlit-expanderHeader *,
    div[data-testid="stExpander"] summary *,
    .streamlit-expanderHeader {
        color: #ffffff !important;
    }
    
    /* Make expander content text black */
    div[data-testid="stExpander"] div:not(.streamlit-expanderHeader):not(.streamlit-expanderHeader *) {
        color: #000000 !important;
    }
    
    /* Additional specificity for risk level header */
    div[class*="assessment-card"] h3.risk-level-header,
    .assessment-card .risk-level-header {
        color: #ffffff !important;
    }
    
    /* Ensure selectbox dropdown options are white */
    .stSelectbox div[data-baseweb="select"] *,
    .stSelectbox span,
    .stSelectbox p {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

def check_password():
    """Returns `True` if the user has entered the correct password."""
    def password_entered():
        if st.session_state["password"] == st.secrets.get("password", "medaid123"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password", help="Enter password to access clinician dashboard")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password", help="Enter password to access clinician dashboard")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

def format_timestamp(timestamp_str):
    """Format timestamp for display"""
    try:
        # Handle different timestamp formats
        if 'T' in timestamp_str:
            if '+' in timestamp_str:
                dt = datetime.fromisoformat(timestamp_str)
            else:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            # Handle other formats if needed
            return timestamp_str
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception as e:
        # If parsing fails, return the original string
        return timestamp_str

def get_risk_color_class(risk_level):
    """Get CSS class based on risk level"""
    risk_mapping = {
        "Emergency": "emergency",
        "High": "high-risk",
        "High Risk": "high-risk",
        "Medium": "medium-risk",
        "Moderate Risk": "medium-risk",
        "Low": "low-risk",
        "Low Risk": "low-risk"
    }
    return risk_mapping.get(risk_level, "low-risk")

def get_risk_badge(risk_level):
    """Get emoji badge based on risk level"""
    risk_badges = {
        "Emergency": "🔴",
        "High": "🟠",
        "High Risk": "🟠",
        "Medium": "🟡",
        "Moderate Risk": "🟡",
        "Low": "🟢",
        "Low Risk": "🟢"
    }
    return risk_badges.get(risk_level, "⚪")

def show_assessment_card(assessment: dict):
    """Display an assessment card with detailed information"""
    rl = assessment.get("risk_level", "Unknown")
    proba = assessment.get("risk_proba", 0.0)
    color = {"Emergency":"#b30000","High":"#ff4d4d","Medium":"#ffb84d","Low":"#4caf50"}.get(rl,"#777")
    
    st.markdown(f"<div style='padding:12px;border-radius:10px;background:#f8f9fa;color:#ffffff' class='assessment-card'>", unsafe_allow_html=True)
    # Add a visual indicator for the risk level color
    color_indicator = f"<span style='display:inline-block;width:12px;height:12px;background-color:{color};border-radius:50%;margin-right:8px;'></span>"
    st.markdown(f"<h3 style='margin:6px 0' class='risk-level-header'>{color_indicator}{rl} risk — {proba:.0%} probability</h3>", unsafe_allow_html=True)
    
    # Determine and display the source of the assessment
    reason = assessment.get("reason","")
    if "Emergency keyword detected" in reason or rl == "Emergency":
        source_text = "Source: Deterministic Safety Rule (Emergency keyword detected)"
        st.markdown(f"<div style='margin-bottom:8px;font-weight:bold;color:#ffffff' class='source-text'>{source_text}</div>", unsafe_allow_html=True)
    else:
        source_text = "Source: Generative AI Assessment"
        st.markdown(f"<div style='margin-bottom:8px;font-weight:bold;color:#ffffff' class='source-text'>{source_text}</div>", unsafe_allow_html=True)
    
    if reason:
        st.markdown(f"<div style='margin-bottom:8px;color:#ffffff' class='reason-text'>{reason}</div>", unsafe_allow_html=True)

    conds = assessment.get("possible_conditions", [])
    if conds:
        badges = ""
        for c in conds:
            name = c.get("disease","Unknown")
            conf = c.get("confidence", 0.0)
            badges += f"<span style='display:inline-block;margin:4px 6px;padding:6px 10px;border-radius:14px;background:#e9ecef;font-size:13px;color:#000000' class='condition-badge'>{name} {conf:.0%}</span>"
        st.markdown(badges, unsafe_allow_html=True)

    st.markdown("<h4 class='recommendations-header'>Recommendations</h4>", unsafe_allow_html=True)
    recs = assessment.get("recommendations", []) or []
    if recs:
        for r in recs:
            st.markdown(f"<p class='recommendation-item'>- {r}</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p class='recommendation-item'>- Follow up with local health provider</p>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

def main():
    st.title("🧑‍⚕️ Medaid Clinician Dashboard")
    
    # Add refresh controls
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<p class="dashboard-info-text">Showing the 50 most recent triage assessments.</p>', unsafe_allow_html=True)
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Check password for security
    if not check_password():
        st.stop()

    # Get records from database
    records = get_all_triage_records()
    
    # Debug information
    st.sidebar.markdown(f"**<span class='sidebar-dashboard-info'>📊 Dashboard Info:</span>**", unsafe_allow_html=True)
    st.sidebar.markdown(f"<span class='sidebar-dashboard-info'>Records found: {len(records)}</span>", unsafe_allow_html=True)
    
    if not records:
        st.warning("No triage records found in the database.")
        st.info("💡 Tip: Patient records will appear here after patients complete assessments in the main application.")
        st.info("🔗 Access the patient application at: http://localhost:8508")
        return
    
    # Display metrics
    st.markdown('<h2 class="overview-title">Overview</h2>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    total_records = len(records)
    emergency_count = len([r for r in records if r.get("triage_result", {}).get("risk_level") == "Emergency"])
    high_risk_count = len([r for r in records if r.get("triage_result", {}).get("risk_level") in ["High", "High Risk"]])
    medium_risk_count = len([r for r in records if r.get("triage_result", {}).get("risk_level") in ["Medium", "Moderate Risk"]])
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_records}</div>
            <div class="metric-label">Total Assessments</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{emergency_count}</div>
            <div class="metric-label">Emergency Cases</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{high_risk_count}</div>
            <div class="metric-label">High Risk Cases</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{medium_risk_count}</div>
            <div class="metric-label">Medium Risk Cases</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Display records
    st.markdown(f'<h3 class="recent-assessments-title">Recent Patient Assessments ({total_records} found)</h3>', unsafe_allow_html=True)
    
    # Add filter options
    st.sidebar.markdown("---")
    st.sidebar.markdown("### <span class='sidebar-dashboard-info'>🔍 Filters</span>", unsafe_allow_html=True)
    
    # Risk level filter
    risk_levels = ["All"] + list(set([r.get("triage_result", {}).get("risk_level", "Unknown") for r in records]))
    selected_risk = st.sidebar.selectbox("Risk Level", risk_levels, index=0)
    
    # Filter records if needed
    if selected_risk != "All":
        filtered_records = [r for r in records if r.get("triage_result", {}).get("risk_level") == selected_risk]
        st.sidebar.markdown(f"<span class='sidebar-dashboard-info'>Filtered to {len(filtered_records)} records</span>", unsafe_allow_html=True)
    else:
        filtered_records = records
    
    if not filtered_records:
        st.info("No records match the current filter.")
        return
    
    # Display records
    for i, record in enumerate(filtered_records):
        assessment = record.get("triage_result", {})
        risk_level = assessment.get("risk_level", "N/A")
        patient_name = record.get("patient_name", "Unknown Patient")
        date = record.get("date", "No Date")
        
        # Get CSS class based on risk level
        card_class = get_risk_color_class(risk_level)
        risk_badge = get_risk_badge(risk_level)
        
        with st.container():
            st.markdown(f"""
            <div class="patient-card {card_class}">
                <h4>{risk_badge} {patient_name}</h4>
                <p><strong>Assessment Time:</strong> {format_timestamp(date)}</p>
                <p><strong>Risk Level:</strong> {risk_level}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Expandable section for details
            with st.expander(f"📋 View Detailed Assessment #{i+1}"):
                show_assessment_card(assessment)

if __name__ == "__main__":
    main()