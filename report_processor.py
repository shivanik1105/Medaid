# report_processor.py - Medical Report Analysis Module
import streamlit as st
import re
import json
from typing import Dict, Any
import fitz  # PyMuPDF for PDF processing
from PIL import Image
import pytesseract

# Medical parameter reference ranges (simplified)
NORMAL_RANGES = {
    'hemoglobin': {
        'male': (13.5, 17.5),
        'female': (12.0, 15.5),
        'unit': 'g/dL'
    },
    'wbc_count': {
        'normal': (4000, 11000),
        'unit': '/μL'
    },
    'platelet_count': {
        'normal': (150000, 450000),
        'unit': '/μL'
    },
    'glucose_fasting': {
        'normal': (70, 100),
        'prediabetic': (100, 125),
        'unit': 'mg/dL'
    },
    'glucose_random': {
        'normal': (70, 140),
        'unit': 'mg/dL'
    },
    'creatinine': {
        'male': (0.9, 1.3),
        'female': (0.6, 1.1),
        'unit': 'mg/dL'
    },
    'blood_pressure': {
        'normal': (90, 120),  # Systolic for normal
        'high': (140, 90), # Example for hypertension
        'unit': 'mmHg'
    },
    'temperature': {
        'normal': (97.0, 99.0),
        'unit': '°F'
    },
    'heart_rate': {
        'normal': (60, 100),
        'unit': 'bpm'
    }
}

# Keywords to extract from reports
MEDICAL_KEYWORDS = {
    'hemoglobin': ['hemoglobin', 'hb', 'haemoglobin'],
    'wbc_count': ['wbc', 'white blood cell', 'leucocyte', 'leukocyte'],
    'platelet_count': ['platelet', 'thrombocyte'],
    'glucose_fasting': ['glucose fasting', 'fbs', 'fasting blood sugar'],
    'glucose_random': ['glucose random', 'rbs', 'random blood sugar', 'blood glucose'],
    'creatinine': ['creatinine', 'serum creatinine'],
    'blood_pressure': ['bp', 'blood pressure', 'systolic', 'diastolic'],
    'temperature': ['temperature', 'fever', 'temp'],
    'heart_rate': ['heart rate', 'pulse', 'hr']
}

def extract_text_from_pdf(uploaded_file):
    """Extract text from PDF files"""
    try:
        pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = ""
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            text += page.get_text()
        pdf_document.close()
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def extract_text_from_image(uploaded_file):
    """Extract text from image files using OCR"""
    try:
        image = Image.open(uploaded_file)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return ""

def extract_medical_values(text):
    """Extract medical parameter values from text"""
    structured_data = {}
    
    # Clean and normalize text
    text = text.lower().replace('\n', ' ')
    
    for param, keywords in MEDICAL_KEYWORDS.items():
        for keyword in keywords:
            # Pattern to match parameter name followed by value
            patterns = [
                rf'{keyword}\s*:?\s*(\d+\.?\d*)',  # Basic pattern
                rf'{keyword}\s*[-:]?\s*(\d+\.?\d*)',  # With dash or colon
                rf'(\d+\.?\d*)\s*{keyword}',  # Value before parameter
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text)
                if matches:
                    try:
                        value = float(matches[0])
                        structured_data[param] = value
                        break
                    except ValueError:
                        continue
            
            if param in structured_data:
                break
    
    return structured_data

def interpret_values(structured_data, patient_age=None, patient_sex='unknown'):
    """Interpret medical values against normal ranges"""
    interpretations = {}
    
    for param, value in structured_data.items():
        if param in NORMAL_RANGES:
            range_info = NORMAL_RANGES[param]
            
            # Get appropriate range based on sex if available
            if patient_sex.lower() in ['male', 'female'] and patient_sex.lower() in range_info:
                normal_range = range_info[patient_sex.lower()]
            elif 'normal' in range_info:
                normal_range = range_info['normal']
            else:
                # Default to male range if sex-specific and no sex provided
                normal_range = range_info.get('male', range_info.get('female', (0, 999999)))
            
            unit = range_info.get('unit', '')
            
            # Determine if value is normal, high, or low
            if value < normal_range[0]:
                status = 'Low'
                concern_level = 'Moderate' if param == 'hemoglobin' else 'Low'
            elif value > normal_range[1]:
                status = 'High'
                concern_level = 'Moderate' if param in ['glucose_fasting', 'glucose_random'] else 'Low'
            else:
                status = 'Normal'
                concern_level = 'None'
            
            interpretations[param] = {
                'value': value,
                'status': status,
                'normal_range': normal_range,
                'unit': unit,
                'concern_level': concern_level
            }
    
    return interpretations

def analyze_medical_report(uploaded_file):
    """Main function to analyze uploaded medical reports"""
    try:
        # Extract text based on file type
        if uploaded_file.type == "application/pdf":
            extracted_text = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.type in ["image/png", "image/jpg", "image/jpeg"]:
            extracted_text = extract_text_from_image(uploaded_file)
        else:
            return {
                'structured_data': {},
                'interpretations': {},
                'raw_text': '',
                'error': 'Unsupported file type'
            }
        
        if not extracted_text.strip():
            return {
                'structured_data': {},
                'interpretations': {},
                'raw_text': '',
                'error': 'No text could be extracted from the file'
            }
        
        # Extract structured medical data
        structured_data = extract_medical_values(extracted_text)
        
        if not structured_data:
            return {
                'structured_data': {},
                'interpretations': {},
                'raw_text': extracted_text[:500],  # First 500 chars for debugging
                'error': 'No medical parameters found in the report'
            }
        
        # Interpret the values (we don't have patient sex/age here, so using defaults)
        interpretations = interpret_values(structured_data)
        
        return {
            'structured_data': structured_data,
            'interpretations': interpretations,
            'raw_text': extracted_text[:1000],  # First 1000 chars
            'error': None
        }
        
    except Exception as e:
        st.error(f"Error analyzing report: {e}")
        return {
            'structured_data': {},
            'interpretations': {},
            'raw_text': '',
            'error': str(e)
        }

def generate_report_explanation(structured_data, patient_age=None):
    """Generate user-friendly explanations of report findings"""
    if not structured_data:
        return "No medical data could be extracted from your report."
    
    explanations = []
    
    try:
        for param, value in structured_data.items():
            if param == 'hemoglobin':
                if value < 12:
                    explanations.append(f"Your hemoglobin level ({value} g/dL) is low, which may indicate anemia. This can cause weakness and fatigue.")
                elif value > 17:
                    explanations.append(f"Your hemoglobin level ({value} g/dL) is high, which may need further evaluation.")
                else:
                    explanations.append(f"Your hemoglobin level ({value} g/dL) is normal.")
            
            elif param in ['glucose_fasting', 'glucose_random']:
                if param == 'glucose_fasting':
                    if value > 126:
                        explanations.append(f"Your fasting glucose ({value} mg/dL) is high, suggesting possible diabetes.")
                    elif value > 100:
                        explanations.append(f"Your fasting glucose ({value} mg/dL) is slightly elevated (pre-diabetic range).")
                    else:
                        explanations.append(f"Your fasting glucose ({value} mg/dL) is normal.")
                else:  # random glucose
                    if value > 200:
                        explanations.append(f"Your random glucose ({value} mg/dL) is very high, suggesting possible diabetes.")
                    elif value > 140:
                        explanations.append(f"Your random glucose ({value} mg/dL) is elevated.")
                    else:
                        explanations.append(f"Your random glucose ({value} mg/dL) is normal.")
            
            elif param == 'wbc_count':
                if value > 11000:
                    explanations.append(f"Your white blood cell count ({int(value)}/μL) is high, which may indicate infection or inflammation.")
                elif value < 4000:
                    explanations.append(f"Your white blood cell count ({int(value)}/μL) is low, which may indicate immune system issues.")
                else:
                    explanations.append(f"Your white blood cell count ({int(value)}/μL) is normal.")
            
            elif param == 'creatinine':
                if value > 1.3:
                    explanations.append(f"Your creatinine level ({value} mg/dL) is high, which may indicate kidney function issues.")
                else:
                    explanations.append(f"Your creatinine level ({value} mg/dL) is normal.")
    
    except Exception as e:
        return f"Error generating explanation: {e}"
    
    if not explanations:
        return "No specific medical terms were extracted or could be interpreted for an explanation."
    
    return "\n".join(explanations)
