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
        st.markdown(f"**{name}**")
        if addr:
            st.markdown(f"{addr}")
        if dist:
            st.markdown(f"Distance: {dist} km")
        if phone:
            st.markdown(f"Phone: {phone} — [Call](tel:{phone})")
        if maps_url:
            st.markdown(f"[Open in map]({maps_url})")
        st.markdown("---")
    else:
        st.markdown(f"- {f}")

def collect_past_history():
    """Collect past medical history after successful login"""
    st.subheader("📋 Past Medical History")
    st.markdown("Help us provide better assessment by sharing your medical history:")
    
    # Common conditions checklist
    st.markdown("**Select any conditions you have or have had:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        diabetes = st.checkbox("Diabetes")
        hypertension = st.checkbox("High Blood Pressure")
        heart_disease = st.checkbox("Heart Disease")
        asthma = st.checkbox("Asthma")
        kidney_disease = st.checkbox("Kidney Disease")
        
    with col2:
        cancer = st.checkbox("Cancer")
        stroke = st.checkbox("Stroke")
        liver_disease = st.checkbox("Liver Disease")
        thyroid = st.checkbox("Thyroid Disorder")
        mental_health = st.checkbox("Mental Health Condition")
    
    # Additional conditions
    other_conditions = st.text_area(
        "Other conditions or medications (optional):",
        placeholder="E.g., Allergies to penicillin, Previous surgeries, Current medications",
        height=80
    )
    
    # Family history
    family_history = st.text_area(
        "Family medical history (optional):",
        placeholder="E.g., Family history of diabetes, heart disease, cancer",
        height=60
    )
    
    if st.button("Save Medical History", type="primary"):
        # Compile the history
        conditions = []
        if diabetes: conditions.append("Diabetes")
        if hypertension: conditions.append("High Blood Pressure")
        if heart_disease: conditions.append("Heart Disease")
        if asthma: conditions.append("Asthma")
        if kidney_disease: conditions.append("Kidney Disease")
        if cancer: conditions.append("Cancer")
        if stroke: conditions.append("Stroke")
        if liver_disease: conditions.append("Liver Disease")
        if thyroid: conditions.append("Thyroid Disorder")
        if mental_health: conditions.append("Mental Health Condition")
        
        if other_conditions:
            conditions.extend([x.strip() for x in other_conditions.split(',') if x.strip()])
        
        # Update user's history
        st.session_state.user["past_history"] = conditions
        if family_history:
            st.session_state.user["family_history"] = family_history
        
        # Save to database if available
        if update_user_history:
            try:
                record = {
                    "note": "Medical history collection",
                    "conditions": conditions,
                    "family_history": family_history
                }
                update_user_history(st.session_state.user.get("_id"), conditions, record)
                st.success("✅ Medical history saved successfully!")
            except Exception as e:
                st.warning(f"History saved locally. Database error: {e}")
        else:
            st.success("✅ Medical history saved for this session!")
        
        # Set flag to indicate history has been collected
        st.session_state.user["history_collected"] = True
        st.rerun()

# ---------------- Session state ----------------
st.set_page_config(page_title="Rural Health Assistant", layout="wide")

# Improved CSS for better visibility
st.markdown("""
<style>
/* Global app styling */
.stApp {
    background-color: #f8fafc;
}

/* Fix textarea visibility issues */
.stTextArea > div > div > textarea {
    background-color: #ffffff !important;
    color: #1f2937 !important;
    border: 2px solid #e5e7eb !important;
    border-radius: 8px !important;
    padding: 16px !important;
    font-size: 16px !important;
    line-height: 1.5 !important;
    min-height: 120px !important;
}

.stTextArea > div > div > textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    outline: none !important;
}

.stTextArea > div > div > textarea::placeholder {
    color: #9ca3af !important;
    opacity: 1 !important;
}

/* Button styling */
.stButton > button {
    background: linear-gradient(90deg, #3b82f6, #2563eb) !important;
    color: white !important;
    border: none !important;
    padding: 12px 24px !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}

.stButton > button:hover {
    background: linear-gradient(90deg, #2563eb, #1d4ed8) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
}

/* Form styling */
.stForm {
    background: white;
    padding: 24px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Card styling for results */
.result-card {
    background: white;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin-bottom: 16px;
}

/* Sidebar styling */
.css-1d391kg {
    background-color: #f1f5f9;
}

/* Input field styling */
.stTextInput > div > div > input {
    background-color: #ffffff !important;
    color: #1f2937 !important;
    border: 2px solid #e5e7eb !important;
    border-radius: 6px !important;
    padding: 12px !important;
}

.stTextInput > div > div > input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}

/* Checkbox styling */
.stCheckbox > label {
    color: #374151 !important;
    font-weight: 500 !important;
}

/* Success/Error message styling */
.stSuccess {
    background-color: #f0fdf4 !important;
    border: 1px solid #bbf7d0 !important;
    border-radius: 8px !important;
}

.stError {
    background-color: #fef2f2 !important;
    border: 1px solid #fecaca !important;
    border-radius: 8px !important;
}

.stWarning {
    background-color: #fffbeb !important;
    border: 1px solid #fed7aa !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🏥 Rural Health Assistant")
st.markdown("**AI-powered health assessment for rural communities**")

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

# ---------------- Sidebar: Login/Register ----------------
with st.sidebar:
    st.header("👤 Account")
    
    if not st.session_state.user:
        st.subheader("Login / Register")
        su_name = st.text_input("Full Name", placeholder="Enter your full name")
        su_age = st.number_input("Age", min_value=0, max_value=120, value=25)
        su_email = st.text_input("Email", placeholder="your.email@example.com")
        su_lang = st.selectbox("Preferred Language", ["English", "Hindi"])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Register", type="primary"):
                if not su_name or not su_email:
                    st.error("Please provide name and email")
                else:
                    existing = None
                    try:
                        existing = get_user_by_email(su_email) if get_user_by_email else None
                    except Exception:
                        existing = None
                    
                    if existing:
                        st.session_state.user = existing
                        st.success("Logged in existing user!")
                    else:
                        if create_user:
                            try:
                                created = create_user(su_name, int(su_age), su_email, su_lang)
                                st.session_state.user = created
                                st.success("Account created successfully!")
                            except Exception as e:
                                st.session_state.user = {
                                    "_id": su_email, 
                                    "name": su_name, 
                                    "age": int(su_age), 
                                    "email": su_email, 
                                    "language": su_lang, 
                                    "past_history": []
                                }
                                st.success("Account created (local session)")
                        else:
                            st.session_state.user = {
                                "_id": su_email, 
                                "name": su_name, 
                                "age": int(su_age), 
                                "email": su_email, 
                                "language": su_lang, 
                                "past_history": []
                            }
                            st.success("Account created (local session)")
                    st.rerun()
        
        with col2:
            if st.button("Login"):
                if not su_email:
                    st.error("Please provide email")
                else:
                    try:
                        u = get_user_by_email(su_email) if get_user_by_email else None
                    except Exception:
                        u = None
                    
                    if u:
                        st.session_state.user = u
                        st.success("Logged in successfully!")
                        st.rerun()
                    else:
                        st.error("User not found. Please register first.")
    else:
        # User is logged in
        st.success(f"Welcome, {st.session_state.user.get('name')}!")
        st.markdown(f"**Email:** {st.session_state.user.get('email')}")
        st.markdown(f"**Age:** {st.session_state.user.get('age')} years")
        
        if st.button("Logout", type="secondary"):
            st.session_state.user = None
            st.session_state.final_assessment = None
            st.rerun()
        
        # Show medical history summary if collected
        if st.session_state.user.get("history_collected"):
            with st.expander("📋 Medical History", expanded=False):
                history = st.session_state.user.get("past_history", [])
                if history:
                    for condition in history:
                        st.markdown(f"• {condition}")
                else:
                    st.markdown("No conditions recorded")
                
                family_hist = st.session_state.user.get("family_history", "")
                if family_hist:
                    st.markdown(f"**Family History:** {family_hist}")
                
                if st.button("Update History"):
                    st.session_state.user["history_collected"] = False
                    st.rerun()

# ---------------- Main Content ----------------
if not st.session_state.user:
    st.info("👈 Please login or register in the sidebar to continue")
    st.stop()

# Check if we need to collect medical history
if not st.session_state.user.get("history_collected", False):
    collect_past_history()
    st.stop()

# Main consultation interface
col_left, col_right = st.columns([3, 2])

with col_left:
    st.header("💬 Consultation")
    
    with st.form("consultation_form", clear_on_submit=False):
        st.markdown("**Describe your current symptoms:**")
        symptoms_text = st.text_area(
            "Current symptoms",
            placeholder="Please describe your symptoms in detail. For example:\n• When did they start?\n• How severe are they (1-10)?\n• What makes them better or worse?\n• Any associated symptoms?",
            height=150,
            label_visibility="collapsed"
        )
        
        st.markdown("**Upload medical report (optional):**")
        report_file = st.file_uploader(
            "Medical report", 
            type=["pdf", "png", "jpg", "jpeg"],
            help="Upload any recent medical reports, test results, or prescriptions",
            label_visibility="collapsed"
        )
        
        st.markdown("**Location for nearby facilities:**")
        location_input = st.text_input(
            "Location",
            placeholder="Enter city name or pincode",
            help="This helps us find nearby healthcare facilities",
            label_visibility="collapsed"
        )
        
        analyze_button = st.form_submit_button(
            "🔍 Analyze Symptoms", 
            type="primary", 
            use_container_width=True
        )

    if analyze_button:
        if not symptoms_text and not report_file:
            st.error("Please provide either symptoms description or upload a medical report.")
        else:
            with st.spinner("🔍 Analyzing your symptoms and medical history..."):
                try:
                    final_symptoms = symptoms_text or ""
                    report_json = None
                    
                    # Process uploaded report
                    if report_file:
                        tmpf = tempfile.NamedTemporaryFile(
                            delete=False, 
                            suffix=os.path.splitext(report_file.name)[1]
                        )
                        tmpf.write(report_file.getbuffer())
                        tmpf.flush()
                        tmpf.close()
                        
                        try:
                            if ReportProcessor:
                                rp = ReportProcessor()
                                res = rp.process_report(
                                    tmpf.name, 
                                    user_data={"name": st.session_state.user.get("name")}
                                )
                                if res.get("status") == "success":
                                    report_json = res.get("data")
                                    st.success("✅ Medical report processed successfully")
                                    try:
                                        if update_user_report_data:
                                            update_user_report_data(
                                                st.session_state.user.get("_id"), 
                                                report_json
                                            )
                                    except Exception:
                                        pass
                                else:
                                    st.warning("⚠️ " + str(res.get("message", "")))
                            else:
                                st.info("Report processor not available")
                        except Exception as e:
                            st.warning(f"⚠️ Report processing failed: {e}")
                        finally:
                            try: 
                                os.unlink(tmpf.name)
                            except: 
                                pass

                    st.session_state.report_data = report_json

                    # Prepare user data with medical history
                    user_data = st.session_state.user.copy()
                    
                    # Run assessment with all available data
                    result = None
                    if integrate_report_and_run_assessment:
                        assessment_input = {
                            "symptoms_text": final_symptoms,
                            "city": location_input,
                            "past_history": user_data.get("past_history", []),
                            "family_history": user_data.get("family_history", ""),
                            "age": user_data.get("age"),
                            "user_name": user_data.get("name")
                        }
                        result = integrate_report_and_run_assessment(
                            report_json, 
                            assessment_input, 
                            user_data
                        )
                    else:
                        result = {
                            "status": "error",
                            "message": "Assessment backend not available",
                            "debug": "integrate_report_and_run_assessment not available"
                        }

                    if result.get("status") == "error":
                        st.error("❌ Assessment error: " + str(result.get("message")))
                        st.session_state.conversation.append({
                            "role": "assistant",
                            "content": f"Assessment error: {result.get('message')}",
                            "time": datetime.utcnow().isoformat()
                        })
                    else:
                        assessment = result.get("assessment")
                        st.session_state.final_assessment = assessment
                        st.success("✅ Assessment complete! Check results on the right →")
                        
                        st.session_state.conversation.append({
                            "role": "assistant",
                            "content": assessment.get("reason", "Assessment complete"),
                            "time": datetime.utcnow().isoformat()
                        })
                        
                        # Save triage record
                        try:
                            record = {
                                "user_id": st.session_state.user.get("_id"),
                                "date": datetime.utcnow().isoformat(),
                                "current_symptoms": final_symptoms,
                                "report_data": report_json,
                                "triage_result": assessment,
                                "past_history": user_data.get("past_history", [])
                            }
                            if update_user_history:
                                update_user_history(
                                    st.session_state.user.get("_id"),
                                    st.session_state.user.get("past_history", []),
                                    record
                                )
                            st.session_state.last_triage_record = record
                        except Exception:
                            pass

                except Exception as e:
                    st.error(f"❌ Assessment failed: {e}")
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())

with col_right:
    st.header("📊 Assessment Results")
    
    if st.session_state.final_assessment:
        assessment = st.session_state.final_assessment
        
        # Show emergency banner if needed
        if assessment.get("risk_level") == "Emergency":
            show_emergency_banner()
        
        # Show assessment results
        with st.container():
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            show_assessment_card(assessment)
            st.markdown('</div>', unsafe_allow_html=True)

        # Show nearby facilities for medium+ risk
        if assessment.get("risk_level") in ("Medium", "High", "Emergency"):
            st.markdown("### 🏥 Nearby Healthcare Facilities")
            
            if not location_input.strip():
                st.info("💡 Enter your location in the form to see nearby facilities")
            else:
                try:
                    with st.spinner("Finding nearby facilities..."):
                        facilities = get_recommendations(
                            assessment.get("risk_level"),
                            user_city=location_input,
                            user_state="Maharashtra",
                            user_pincode=location_input
                        )

                    if not facilities:
                        st.warning("No facilities found for this location. Please try a different city or pincode.")
                    else:
                        for f in facilities[:5]:  # Show top 5
                            with st.container():
                                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                                render_facility_card(f)
                                st.markdown('</div>', unsafe_allow_html=True)
                        
                        if len(facilities) > 5:
                            with st.expander(f"Show all {len(facilities)} facilities"):
                                for f in facilities[5:]:
                                    render_facility_card(f)
                                    
                except Exception as e:
                    st.error(f"❌ Could not fetch facilities: {e}")
    else:
        st.info("👈 Complete the consultation form to see your health assessment and recommendations")

# Conversation log
st.markdown("---")
with st.expander("💬 Conversation History", expanded=False):
    if st.session_state.conversation:
        for msg in st.session_state.conversation[-10:]:  # Show last 10 messages
            role = msg.get("role", "user")
            content = msg.get("content", "")
            time = msg.get("time", "")
            
            if role == "assistant":
                st.markdown(f"**🤖 AI Assistant:** {content}")
                st.caption(f"Time: {time}")
            else:
                st.markdown(f"**👤 You:** {content}")
                st.caption(f"Time: {time}")
            st.markdown("---")
    else:
        st.info("No conversation history yet")

# Footer
st.markdown("---")
st.markdown(
    "⚠️ **Disclaimer:** This is a prototype AI system for health screening purposes only. "
    "Always consult with qualified healthcare professionals for medical advice and treatment. "
    "In case of emergency, contact local emergency services immediately."
)