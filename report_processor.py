import fitz # PyMuPDF
from PIL import Image
import io
import re # New import for regex

def extract_text_from_pdf(file_content):
    """Extracts text from a PDF file."""
    doc = fitz.open(stream=file_content, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_image(file_content):
    """
    Extracts text from an image file.
    Note: For robust OCR, an external Tesseract installation and pytesseract library would be needed.
    This is a basic placeholder.
    """
    # Using Pillow to open image, but actual OCR would require pytesseract
    # For now, we'll return a placeholder string for image analysis
    try:
        Image.open(io.BytesIO(file_content))
        return "Image report uploaded. OCR processing not fully implemented in this placeholder."
    except Exception as e:
        return f"Error processing image: {e}"

def analyze_medical_report(uploaded_file) -> dict:
    """
    Analyzes an uploaded medical report (PDF or image) and extracts text.
    Returns a dictionary with the extracted text and structured medical terms.
    """
    extracted_text = ""
    file_type = uploaded_file.type

    if "pdf" in file_type:
        extracted_text = extract_text_from_pdf(uploaded_file.getvalue())
    elif "image" in file_type or "png" in file_type or "jpg" in file_type or "jpeg" in file_type:
        extracted_text = extract_text_from_image(uploaded_file.getvalue())
    else:
        extracted_text = "Unsupported file type for analysis."

    # Extract structured medical terms
    structured_data = extract_medical_terms(extracted_text)

    return {"raw_text": extracted_text, "structured_data": structured_data}

def extract_medical_terms(text: str) -> dict:
    """
    Extracts structured medical terms (e.g., hemoglobin, sugar, BP) using regex.
    This is a placeholder for more advanced NLP/ML extraction.
    """
    medical_terms = {}

    # Example: Hemoglobin extraction (e.g., "Hemoglobin: 12.5 g/dL" or "Hb 12.5")
    hemoglobin_match = re.search(r"[Hh][Bb](?:[ .:]|\s*concentration)?\s*(\d+\.?\d*)\s*(g/dL|g/L)?", text, re.IGNORECASE)
    if hemoglobin_match:
        medical_terms["hemoglobin"] = f"{hemoglobin_match.group(1)} {hemoglobin_match.group(2) or 'g/dL'}".strip()

    # Example: Sugar/Glucose extraction (e.g., "Glucose: 100 mg/dL" or "Sugar 5.5 mmol/L")
    sugar_match = re.search(r"(?:glucose|sugar):?\s*(\d+\.?\d*)\s*(mg/dL|mmol/L)?", text, re.IGNORECASE)
    if sugar_match:
        medical_terms["sugar"] = f"{sugar_match.group(1)} {sugar_match.group(2) or 'mg/dL'}".strip()

    # Example: Blood Pressure extraction (e.g., "BP 120/80" or "Blood Pressure: 130/85 mmHg")
    bp_match = re.search(r"(?:blood pressure|BP):?\s*(\d{2,3}/\d{2,3})\s*(mmHg)?", text, re.IGNORECASE)
    if bp_match:
        medical_terms["bp"] = f"{bp_match.group(1)} {bp_match.group(2) or 'mmHg'}".strip()

    # TODO: Add risk flagging logic here in a future step.

    return medical_terms

def generate_report_explanation(structured_data: dict, user_age: int = None) -> str:
    """
    Generates a human-readable explanation of the medical report based on structured data and user age.
    This is a simplified version and can be expanded with more medical knowledge.
    """
    explanation_parts = []

    age_context = ""
    if user_age:
        if user_age < 12:
            age_context = "(for a child)"
        elif user_age >= 65:
            age_context = "(for an elder)"

    if "hemoglobin" in structured_data:
        try:
            value_str = structured_data["hemoglobin"]
            # Extract numerical part, assuming format like '12.5 g/dL'
            value = float(re.search(r'(\d+\.?\d*)', value_str).group(1))
            # Age-specific thresholds for hemoglobin (simplified example)
            if user_age and user_age < 18: # Pediatric reference
                if value < 11.5:
                    explanation_parts.append(f"Your hemoglobin level ({value_str}) {age_context} is lower than normal, which could indicate anemia or other conditions. Consult a pediatrician.")
                elif value > 15.5:
                    explanation_parts.append(f"Your hemoglobin level ({value_str}) {age_context} is higher than normal, which might require further investigation by a pediatrician.")
                else:
                    explanation_parts.append(f"Your hemoglobin level ({value_str}) {age_context} is within the normal range.")
            else: # Adult reference
                if value < 12.0:
                    explanation_parts.append(f"Your hemoglobin level ({value_str}) {age_context} is lower than normal, which could indicate anemia or other conditions.")
                elif value > 16.0:
                    explanation_parts.append(f"Your hemoglobin level ({value_str}) {age_context} is higher than normal, which might require further investigation.")
                else:
                    explanation_parts.append(f"Your hemoglobin level ({value_str}) {age_context} is within the normal range.")
        except (ValueError, AttributeError):
            explanation_parts.append(f"Could not interpret hemoglobin value: {structured_data["hemoglobin"]}.")

    if "sugar" in structured_data:
        try:
            value_str = structured_data["sugar"]
            value = float(re.search(r'(\d+\.?\d*)', value_str).group(1)) # Assuming mg/dL or mmol/L for now
            # Age-specific thresholds for blood sugar (simplified example)
            if user_age and user_age < 18: # Pediatric reference
                if value > 125:
                    explanation_parts.append(f"Your blood sugar level ({value_str}) {age_context} is elevated, which may suggest a risk of diabetes or pre-diabetes. Consult a pediatrician.")
                elif value < 60:
                    explanation_parts.append(f"Your blood sugar level ({value_str}) {age_context} is low, which might be hypoglycemia. Consult a pediatrician.")
                else:
                    explanation_parts.append(f"Your blood sugar level ({value_str}) {age_context} is within the normal range.")
            elif user_age and user_age >= 65: # Geriatric reference
                if value > 160:
                    explanation_parts.append(f"Your blood sugar level ({value_str}) {age_context} is elevated, which may suggest a risk of diabetes or pre-diabetes. Regular monitoring is advised.")
                else:
                    explanation_parts.append(f"Your blood sugar level ({value_str}) {age_context} is within a reasonable range for your age.")
            else: # Adult reference
                if value > 140:
                    explanation_parts.append(f"Your blood sugar level ({value_str}) {age_context} is elevated, which may suggest a risk of diabetes or pre-diabetes.")
                elif value < 70:
                    explanation_parts.append(f"Your blood sugar level ({value_str}) {age_context} is low, which might be hypoglycemia.")
                else:
                    explanation_parts.append(f"Your blood sugar level ({value_str}) {age_context} is within the normal range.")
        except (ValueError, AttributeError):
            explanation_parts.append(f"Could not interpret blood sugar value: {structured_data["sugar"]}.")

    if "bp" in structured_data:
        try:
            value_str = structured_data["bp"]
            systolic, diastolic = map(int, value_str.split('/'))
            # Age-specific thresholds for blood pressure (simplified example)
            if user_age and user_age < 18: # Pediatric reference
                if systolic >= 120 or diastolic >= 80:
                    explanation_parts.append(f"Your blood pressure ({value_str}) {age_context} is elevated for your age, indicating potential hypertension. Consult a pediatrician.")
                elif systolic < 90 or diastolic < 55:
                    explanation_parts.append(f"Your blood pressure ({value_str}) {age_context} is low for your age, which could lead to dizziness or fainting. Consult a pediatrician.")
                else:
                    explanation_parts.append(f"Your blood pressure ({value_str}) {age_context} is within the healthy range for your age.")
            elif user_age and user_age >= 65: # Geriatric reference
                if systolic >= 150 or diastolic >= 90:
                    explanation_parts.append(f"Your blood pressure ({value_str}) {age_context} is elevated. It's important to consult a doctor for management, considering age-related factors.")
                else:
                    explanation_parts.append(f"Your blood pressure ({value_str}) {age_context} is within a reasonable range for your age.")
            else: # Adult reference
                if systolic >= 140 or diastolic >= 90:
                    explanation_parts.append(f"Your blood pressure ({value_str}) {age_context} is elevated, indicating hypertension. It's recommended to consult a doctor.")
                elif systolic < 90 or diastolic < 60:
                    explanation_parts.append(f"Your blood pressure ({value_str}) {age_context} is low, which could lead to dizziness or fainting.")
                else:
                    explanation_parts.append(f"Your blood pressure ({value_str}) {age_context} is within the healthy range.")
        except (ValueError, AttributeError):
            explanation_parts.append(f"Could not interpret blood pressure value: {structured_data["bp"]}.")

    if not explanation_parts:
        return "No specific medical terms were extracted or could be interpreted for an explanation."

    return "\n".join(explanation_parts)
