from flask import Flask, jsonify, render_template_string, request
import random
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Database setup
DATABASE = 'patients.db'

# Function to create the database and the patients table
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS patient_data (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            patient_id TEXT NOT NULL,
                            patient_name TEXT NOT NULL,
                            heart_rate INTEGER NOT NULL,
                            blood_pressure TEXT NOT NULL,
                            temperature REAL NOT NULL,
                            oxygen_level REAL NOT NULL,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                        )''')
        conn.commit()

# Function to store patient data in the database
def store_patient_data(patient_data):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO patient_data (patient_id, patient_name, heart_rate, blood_pressure, temperature, oxygen_level)
                          VALUES (?, ?, ?, ?, ?, ?)''', (
                              patient_data['patient_id'],
                              patient_data['patient_name'],
                              patient_data['heart_rate'],
                              patient_data['blood_pressure'],
                              patient_data['temperature'],
                              patient_data['oxygen_level']
                          ))
        conn.commit()

# Function to check abnormal conditions and return color-coded classes
def check_abnormal_conditions(patient_data):
    warnings = []
    color_class = {'heart_rate': 'normal', 'blood_pressure': 'normal', 'temperature': 'normal', 'oxygen_level': 'normal'}
    
    # Heart rate check
    if patient_data["heart_rate"] < 60:
        warnings.append("Low heart rate detected.")
        color_class['heart_rate'] = 'low'
    elif patient_data["heart_rate"] > 100:
        warnings.append("High heart rate detected.")
        color_class['heart_rate'] = 'high'
    else:
        color_class['heart_rate'] = 'normal'
    
    # Blood pressure check
    systolic = int(patient_data["blood_pressure"].split('/')[0])
    if systolic < 90:
        warnings.append("Low blood pressure detected.")
        color_class['blood_pressure'] = 'low'
    elif systolic > 120:
        warnings.append("High blood pressure detected.")
        color_class['blood_pressure'] = 'high'
    else:
        color_class['blood_pressure'] = 'normal'
    
    # Temperature check
    if patient_data["temperature"] < 36.0:
        warnings.append("Low body temperature detected.")
        color_class['temperature'] = 'low'
    elif patient_data["temperature"] > 38.5:
        warnings.append("High body temperature detected.")
        color_class['temperature'] = 'high'
    else:
        color_class['temperature'] = 'normal'
    
    # Oxygen level check
    if patient_data["oxygen_level"] < 90.0:
        warnings.append("Low oxygen level detected.")
        color_class['oxygen_level'] = 'low'
    elif patient_data["oxygen_level"] > 100.0:
        warnings.append("High oxygen level detected.")
        color_class['oxygen_level'] = 'high'
    else:
        color_class['oxygen_level'] = 'normal'

    return warnings, color_class

# Generate simulated patient data
def generate_patient_data(patient_id, patient_name):
    heart_rate = random.randint(45, 110)
    blood_pressure = f"{random.randint(80, 120)}/{random.randint(60, 80)}"
    temperature = round(random.uniform(36.0, 45.0), 1)
    oxygen_level = round(random.uniform(80.0, 100.0), 1)  # Oxygen level between 90% and 100%
    
    # Store data in database
    patient_data = {
        "patient_id": patient_id,
        "patient_name": patient_name,
        "heart_rate": heart_rate,
        "blood_pressure": blood_pressure,
        "temperature": temperature,
        "oxygen_level": oxygen_level
    }
    store_patient_data(patient_data)

    # Check for abnormalities and color-coding
    warnings, color_class = check_abnormal_conditions(patient_data)

    patient_data["warnings"] = warnings
    patient_data["color_class"] = color_class

    return patient_data

# HTML template with color-coding and form for patient ID and name inputs
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Patient Monitoring System</title>
    <style>
        .normal { color: green; }
        .low { color: yellow; font-weight: bold; }
        .high { color: red; font-weight: bold; }
        .patient-data { margin-bottom: 20px; }
        .warnings { color: red; }
    </style>
    <script>
        async function fetchPatientData() {
            const patientInfo = document.getElementById('patientInfoInput').value.split(',').map(info => info.trim());
            const response = await fetch(`/api/patient_data?patient_info=${patientInfo.join(',')}`);
            const data = await response.json();
            const patientDataContainer = document.getElementById('patientData');
            patientDataContainer.innerHTML = '';  // Clear previous data

            if (data.length === 0) {
                patientDataContainer.innerHTML = '<p>No patient data found for the entered information.</p>';
            } else {
                data.forEach(patient => {
                    const patientDiv = document.createElement('div');
                    patientDiv.classList.add('patient-data');
                    patientDiv.innerHTML = `
                        <div><strong>Patient ID:</strong> ${patient.patient_id}</div>
                        <div><strong>Patient Name:</strong> ${patient.patient_name}</div>
                        <div class="${patient.color_class.heart_rate}"><strong>Heart Rate:</strong> ${patient.heart_rate} bpm</div>
                        <div class="${patient.color_class.blood_pressure}"><strong>Blood Pressure:</strong> ${patient.blood_pressure} mmHg</div>
                        <div class="${patient.color_class.temperature}"><strong>Temperature:</strong> ${patient.temperature} °C</div>
                        <div class="${patient.color_class.oxygen_level}"><strong>Oxygen Level:</strong> ${patient.oxygen_level} %</div>
                        <div class="warnings">
                            ${patient.warnings.length > 0 ? '<strong>Warnings:</strong><ul>' + patient.warnings.map(warning => `<li>${warning}</li>`).join('') + '</ul>' : '' }
                        </div>
                        <hr>
                    `;
                    patientDataContainer.appendChild(patientDiv);
                });
            }
        }

        // Periodically fetch patient data every 5 seconds
        setInterval(fetchPatientData, 5000); // Fetch data every 5 seconds
        window.onload = fetchPatientData; // Fetch data when the page loads
    </script>
</head>
<body>
    <h1>Patient Monitoring System</h1>
    
    <div>
        <strong>Enter Patient Information (comma-separated Patient ID and Patient Name):</strong>
        <input type="text" id="patientInfoInput" placeholder="e.g., 1234 John Doe" />
        <button onclick="fetchPatientData()">Submit</button>
    </div>
    
    <div id="patientData">
        <!-- Patient data will be displayed here -->
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/patient_data', methods=['GET'])
def get_patient_data():
    requested_info = request.args.get('patient_info', '').split(',')
    requested_info = [info.strip() for info in requested_info if info.strip()]  # Clean up empty or invalid entries

    if len(requested_info) % 2 != 0:  # Ensure that there is an even number of entries (ID and name pairs)
        return jsonify([])  # Return empty list if the input is invalid

    # Prepare the patient data for the requested patient IDs and names
    patient_data_list = []
    for i in range(0, len(requested_info), 2):
        patient_id = requested_info[i]
        patient_name = requested_info[i + 1]

        # Simulate updated patient data for each ID and name
        patient_data = generate_patient_data(patient_id, patient_name)
        
        patient_data_list.append(patient_data)

    return jsonify(patient_data_list)

if __name__ == '__main__':
    init_db()  # Create database and table on startup
    app.run(host='0.0.0.0', port=5000)