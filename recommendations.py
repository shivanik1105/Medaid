# recommendations.py - RURAL-FOCUSED HEALTHCARE RECOMMENDATIONS
import streamlit as st

# Rural healthcare facility database (expandable)
RURAL_HEALTHCARE_FACILITIES = {
    'Maharashtra': {
        'Pune': {
            'High Risk': [
                "Ruby Hall Clinic - Emergency: 020-2605-6000",
                "KEM Hospital - Emergency: 020-2612-5000", 
                "Sahyadri Hospital - Emergency: 020-6777-6777",
                "Government Civil Hospital - Free: 020-2612-4949"
            ],
            'Moderate Risk': [
                "Local Primary Health Center (PHC)",
                "Nearby Community Health Center (CHC)",
                "Government Dispensary",
                "Private General Practitioner"
            ]
        },
        'Solapur': {
            'High Risk': [
                "Government District Hospital - Free: 0217-2310100",
                "Ashwini Rural Medical College - 0217-2323200"
            ],
            'Moderate Risk': [
                "Primary Health Center",
                "Rural Hospital",
                "Local Medical Officer"
            ]
        }
    },
    'Karnataka': {
        'Bangalore': {
            'High Risk': [
                "Victoria Hospital - Emergency: 080-2670-1150",
                "NIMHANS - Emergency: 080-2699-5023"
            ],
            'Moderate Risk': [
                "Primary Health Center",
                "Community Health Center"
            ]
        }
    }
}

# Rural-specific dietary recommendations
RURAL_DIETARY_RECOMMENDATIONS = {
    'anemia': [
        "Eat green leafy vegetables like spinach (palak), fenugreek (methi)",
        "Include jaggery (gur) instead of sugar",
        "Cook in iron utensils to increase iron content",
        "Consume seasonal fruits like guava, pomegranate when available"
    ],
    'diabetes': [
        "Limit rice and wheat portions, increase millet consumption",
        "Use local bitter gourd (karela), fenugreek seeds",
        "Avoid market sweets, use stevia or minimal jaggery",
        "Include local seasonal vegetables"
    ],
    'hypertension': [
        "Reduce salt intake, avoid pickles and papad",
        "Include garlic, onion in daily cooking",
        "Use local herbs like tulsi, neem",
        "Increase water intake, reduce tea/coffee"
    ],
    'general_weakness': [
        "Ensure proper meal timing - 3 meals daily",
        "Include protein sources: dal, milk, eggs if available",
        "Consume seasonal fruits for vitamins",
        "Stay hydrated, especially during summer"
    ]
}

# Rural-specific home remedies (to be used alongside medical care)
HOME_REMEDIES = {
    'fever': [
        "Cool sponging with clean water",
        "Plenty of fluids - water, buttermilk, coconut water",
        "Light diet - khichdi, porridge",
        "Rest in cool, ventilated area"
    ],
    'cough': [
        "Warm water with turmeric and salt for gargling",
        "Ginger-honey tea (if available)",
        "Steam inhalation with hot water",
        "Avoid cold foods and drinks"
    ],
    'stomach_pain': [
        "Light diet - rice water, curd rice",
        "Avoid spicy, oily foods",
        "Ajwain (carom seeds) water",
        "Small frequent meals instead of large ones"
    ],
    'headache': [
        "Rest in quiet, dark room",
        "Cold compress on forehead",
        "Adequate hydration",
        "Avoid strong smells and bright lights"
    ]
}

def get_recommendations(risk_level, user_city='Pune', user_state='Maharashtra'):
    """Get healthcare facility recommendations based on risk and location"""
    recommendations = []
    
    try:
        # Get facility recommendations
        if user_state in RURAL_HEALTHCARE_FACILITIES:
            state_data = RURAL_HEALTHCARE_FACILITIES[user_state]
            
            # Check for exact city match
            if user_city in state_data:
                city_data = state_data[user_city]
                if risk_level in city_data:
                    recommendations.extend(city_data[risk_level])
            
            # Fallback to any city in the state
            if not recommendations:
                for city, city_data in state_data.items():
                    if risk_level in city_data:
                        recommendations.extend([f"{rec} (in {city})" for rec in city_data[risk_level]])
                        break
    
    except Exception as e:
        st.error(f"Error getting recommendations: {e}")
    
    # Add general recommendations if no specific ones found
    if not recommendations:
        if "High" in risk_level:
            recommendations = [
                "Nearest Government District Hospital",
                "Call 108 for emergency ambulance service",
                "Contact local Medical Officer immediately"
            ]
        elif "Moderate" in risk_level:
            recommendations = [
                "Visit nearest Primary Health Center (PHC)",
                "Consult local qualified doctor within 24 hours",
                "Contact ASHA worker for guidance"
            ]
        else:
            recommendations = [
                "Monitor symptoms at home",
                "Consult local healthcare provider if symptoms worsen",
                "Maintain hydration and rest"
            ]
    
    return recommendations

def get_dietary_recommendations(report_data):
    """Get dietary recommendations based on medical report findings"""
    recommendations = []
    
    if not report_data:
        return ["Maintain a balanced diet with local, seasonal foods"]
    
    try:
        for key, value in report_data.items():
            key_lower = key.lower()
            value_str = str(value).lower()
            
            if 'hemoglobin' in key_lower and ('low' in value_str or any(word in value_str for word in ['anemia', 'anaemia'])):
                recommendations.extend(RURAL_DIETARY_RECOMMENDATIONS['anemia'])
            elif 'glucose' in key_lower and ('high' in value_str or 'diabetes' in value_str):
                recommendations.extend(RURAL_DIETARY_RECOMMENDATIONS['diabetes'])
            elif 'blood pressure' in key_lower and 'high' in value_str:
                recommendations.extend(RURAL_DIETARY_RECOMMENDATIONS['hypertension'])
    
    except Exception as e:
        st.error(f"Error generating dietary recommendations: {e}")
    
    # Default recommendations if none found
    if not recommendations:
        recommendations = RURAL_DIETARY_RECOMMENDATIONS['general_weakness']
    
    return list(set(recommendations))  # Remove duplicates

def get_home_remedies(symptoms):
    """Get safe home remedies for common symptoms"""
    remedies = []
    
    symptom_keywords = [symptom.lower() for symptom in symptoms if isinstance(symptom, str)]
    
    try:
        for symptom in symptom_keywords:
            if any(word in symptom for word in ['fever', 'bukhar', 'taap']):
                remedies.extend(HOME_REMEDIES['fever'])
            elif any(word in symptom for word in ['cough', 'khansi']):
                remedies.extend(HOME_REMEDIES['cough'])
            elif any(word in symptom for word in ['stomach', 'pet', 'abdominal']):
                remedies.extend(HOME_REMEDIES['stomach_pain'])
            elif any(word in symptom for word in ['headache', 'head', 'sir']):
                remedies.extend(HOME_REMEDIES['headache'])
    
    except Exception as e:
        st.error(f"Error getting home remedies: {e}")
    
    return list(set(remedies))  # Remove duplicates

def get_emergency_contacts():
    """Get emergency contact numbers"""
    return {
        'ambulance': "108 (Free Emergency Ambulance)",
        'police': "100",
        'disaster_management': "108",
        'women_helpline': "1091",
        'child_helpline': "1098"
    }

def get_rural_health_tips(risk_level):
    """Get general health tips for rural population"""
    common_tips = [
        "Maintain good hygiene - wash hands frequently",
        "Boil drinking water if source is uncertain",
        "Keep living area clean and well-ventilated",
        "Get adequate rest and sleep",
        "Stay connected with local ASHA/ANM worker"
    ]
    
    if "High" in risk_level:
        return [
            "Seek immediate medical attention",
            "Keep someone with you at all times",
            "Have emergency contacts ready",
            "Arrange transportation to hospital",
        ] + common_tips
    
    elif "Moderate" in risk_level:
        return [
            "Monitor symptoms closely",
            "Avoid self-medication without guidance",
            "Plan a doctor visit within 24-48 hours",
            "Keep track of symptom changes",
        ] + common_tips
    
    else:
        return common_tips