import re

def get_recommendations(risk_level: str, city: str, specialization: str = None) -> list[str]:
    """
    Provides dynamic doctor/hospital recommendations based on risk level and city.
    """
    recommendations_list = []
    city_lower = city.lower()

    if "high" in risk_level.lower():
        if "pune" in city_lower:
            recommendations_list.extend([
                "Ruby Hall Clinic, Sassoon Road, Pune (Emergency)",
                "Jehangir Hospital, Pune Station, Pune (Emergency)",
                "Sahyadri Super Speciality Hospital, Deccan, Pune"
            ])
        else:
            recommendations_list.append(f"Seek immediate medical attention at the nearest emergency hospital in {city}.")
    elif "moderate" in risk_level.lower():
        if "pune" in city_lower:
            recommendations_list.extend([
                "Your local General Practitioner in Pune",
                "A nearby Polyclinic for consultation in Pune",
                "Deenanath Mangeshkar Hospital, Erandwane, Pune"
            ])
        else:
            recommendations_list.append(f"Consult a doctor within 24 hours at a reputable clinic or hospital in {city}.")
    
    # Specific recommendations for 'Low Risk' cases
    elif "low" in risk_level.lower():
        recommendations_list.extend([
            "Consider home remedies such as rest, hydration, and over-the-counter medication if symptoms are mild.",
            "Monitor your symptoms closely and seek medical advice if they worsen or persist.",
            "Maintain a healthy diet and lifestyle to boost your immune system."
        ])

    # General advice if no specific recommendations based on risk/city are found
    if not recommendations_list and ("high" in risk_level.lower() or "moderate" in risk_level.lower()):
        recommendations_list.append(f"It is crucial to consult a medical professional promptly in {city}.")
    elif not recommendations_list:
        recommendations_list.append("Monitor your symptoms and consult a doctor if they worsen.")

    return recommendations_list

def get_dietary_recommendations(structured_data: dict) -> list[str]:
    """
    Provides dietary recommendations based on structured medical report data.
    """
    diet_recommendations = []

    if "sugar" in structured_data:
        try:
            value_str = structured_data["sugar"]
            value = float(re.search(r'(\d+\.?\d*)', value_str).group(1))
            if value > 140: # Example threshold for high sugar
                diet_recommendations.append("Reduce intake of sugary drinks and processed foods.")
                diet_recommendations.append("Focus on whole grains, lean proteins, and plenty of vegetables.")
        except (ValueError, AttributeError):
            pass # Handle cases where sugar value cannot be parsed

    if "hemoglobin" in structured_data:
        try:
            value_str = structured_data["hemoglobin"]
            value = float(re.search(r'(\d+\.?\d*)', value_str).group(1))
            if value < 12.0: # Example threshold for low hemoglobin
                diet_recommendations.append("Include iron-rich foods like spinach, lentils, and red meat (if applicable).")
                diet_recommendations.append("Pair iron-rich foods with Vitamin C sources (e.g., oranges, bell peppers) to enhance absorption.")
        except (ValueError, AttributeError):
            pass # Handle cases where hemoglobin value cannot be parsed
    
    # Add more rules for other conditions or general healthy eating
    if not diet_recommendations:
        diet_recommendations.append("Maintain a balanced diet with a variety of fruits, vegetables, and whole foods for general health.")

    return diet_recommendations