# Medaid Clinician Dashboard

## Overview
The clinician dashboard provides real-time access to patient triage assessments. It's a separate Streamlit application that runs on its own port.

## How to Access

### 1. Start the Clinician Dashboard
The clinician dashboard runs as a separate application from the main patient app.

To start it, run:
```bash
cd "f:\shivani\VSCode\projects\Medaid\project - Copy"
python -m streamlit run clinician_app.py
```

### 2. Access in Browser
Once running, the dashboard will be available at:
- **Local URL**: http://localhost:8510

### 3. Login
Use the following credentials:
- **Password**: medaid123 (default)

To change the password, edit the `.streamlit/secrets.toml` file.

## Features

### Real-time Patient Feed
- Displays the 50 most recent triage assessments
- Shows patient names, assessment times, and risk levels
- Color-coded cards for different risk levels:
  - 🔴 Emergency
  - 🟠 High Risk
  - 🟡 Medium Risk
  - 🟢 Low Risk

### Detailed Assessment View
- Expandable sections for detailed patient information
- Shows possible conditions with confidence levels
- Displays key recommendations for immediate action
- Clear indication of assessment source:
  - "Source: Deterministic Safety Rule (Emergency keyword detected)"
  - "Source: Generative AI Assessment"

### Dashboard Metrics
- Total assessments counter
- Emergency cases counter
- High-risk cases counter
- Medium-risk cases counter

### Filtering Options
- Filter by risk level
- See specific types of cases

## How It Works

### Data Source
The dashboard retrieves data from the same database used by the patient application:
- Local JSON file: `local_db.json`
- MongoDB (if configured)

### Security
- Password-protected access
- Separate application from patient interface
- No patient PII displayed without authentication

## Troubleshooting

### Issue: "I don't see any patient records"
**Solution**: Patient records are only displayed after patients complete assessments in the main application.

1. Run the main patient app: `python -m streamlit run app.py`
2. Complete a patient assessment
3. Refresh the clinician dashboard

### Issue: "Connection refused when accessing dashboard"
**Solution**: Make sure the clinician dashboard is running.

1. Check that you started it with: `python -m streamlit run clinician_app.py`
2. Check the terminal for any error messages
3. Verify the port number in the terminal output

### Issue: "Incorrect password"
**Solution**: Use the default password or check the secrets file.

1. Default password is: `medaid123`
2. To change it, edit `.streamlit/secrets.toml`

## Development Information

### File Structure
- Main dashboard file: `clinician_app.py`
- Database functions: `database.py` (function: `get_all_triage_records`)
- Password configuration: `.streamlit/secrets.toml`

### Customization
- To change the password, edit `.streamlit/secrets.toml`
- To modify the display, edit `clinician_app.py`
- To change data retrieval, modify `database.py`