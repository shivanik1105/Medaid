# report_analyzer.py
"""
Small helper to convert report JSON + symptoms into a feature dict for model input.
This is a stub — replace with your real feature engineering later.
"""

from typing import Dict, Any

def report_to_feature_vector(report_json: dict, symptoms_text: str, user_profile: dict) -> Dict[str, Any]:
    """
    Returns a simple dict of features (not a numpy vector).
    Real model code should map this to ordered vector using FEATURE_ORDER.
    """
    fv = {}
    fv["age"] = user_profile.get("age") or 0
    fv["sex"] = user_profile.get("sex") or ""
    fv["symptom_text"] = (symptoms_text or "").lower()
    # numeric flags from report
    for t in (report_json or {}).get("medical_tests", []):
        key = t.get("test_name","").lower().replace(" ","_")
        fv[f"report_{key}_value"] = t.get("value")
        fv[f"report_{key}_status"] = t.get("status")
    # simple counts
    fv["num_abnormal"] = len((report_json or {}).get("abnormal_results", []))
    return fv
