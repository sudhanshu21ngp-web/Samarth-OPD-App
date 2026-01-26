import streamlit as st
import pandas as pd
from datetime import datetime

# --- CLINIC CONSTANTS ---
CLINIC_NAME = "SHRI SWAMI SAMARTH HOMEOPATHIC CLINIC AND HOSPITAL"
ADDRESS = "BHOSLEWADI BUS STOP, MHGAON ROAD, HINGNA-440011."
DOCTOR_NAME = "DR. SUDHANSHU GUPTA (REG.NO. 47553)"
QUALIFICATIONS = "B.H.M.S., P.G.D.C.P., M.D. (HOLISTIC MEDICINE), P.G.D.C.F.L"
TAGLINE = "(CONSULTANT HOMEOPATH AND PSYCHOTHERAPIST)"

st.set_page_config(page_title="OPD Manager Pro", layout="wide")

# --- DATA & TEMPLATE INITIALIZATION ---
if 'db' not in st.session_state: st.session_state.db = []

# Quick Template Library (Generic Allopathic Protocols)
TEMPLATES = {
    "Custom (Blank)": {"diag": "", "symp": "", "rx": ""},
    "Viral Fever/Flu": {
        "diag": "Acute Viral Syndrome",
        "symp": "Fever with chills, generalized body ache, headache.",
        "rx": "1. TAB. PARACETAMOL 650mg | 1--1--1 (PC) | 3 Days\n2. TAB. LEVOCETIRIZINE 5mg | 0--0--1 (HS) | 5 Days"
    },
    "Acute Gastritis": {
        "diag": "Hyperacidity / Gastritis",
        "symp": "Nausea, epigastric pain, bloating.",
        "rx": "1. CAP. PANTOPRAZOLE 40mg | 1--0--0 (Empty Stomach) | 5 Days\n2. TAB. DOMPERIDONE 10mg | 1--0--1 (Before food) | 3 Days"
    },
    "Acute Myalgia/Pain": {
        "diag": "Musculoskeletal Pain",
        "symp": "Body ache, localized pain, stiffness.",
        "rx": "1. TAB. ETORICOXIB 90mg | 0--0--1 (PC) | 3 Days\n2. GEL. DICLOFENAC | Local Application TDS"
    }
}

# --- SIDEBAR: SEARCH & HISTORY ---
st.sidebar.title("🔍 Patient Records")
search_id = st.sidebar.text_input("Search ID (e.g., A1)")
found_record = None

if search_id:
    results = [r for r in st.session_state.db if r['ID'].upper() == search_id.upper()]
    if results:
        found_record = results[-1]
        st.sidebar.success(f"Record Found: {found_record['Name']}")

st.sidebar.divider()
if st.session_state.db:
    df_export = pd.DataFrame(st.session_state.db)
    st.sidebar.download_button("📥 Export DB", df_export.to_csv(index=False).encode('utf-8'), "Clinic_Records.csv")

# --- MAIN INTERFACE ---
tab1, tab2 = st.tabs(["📋 Consultation", "📊 Analytics"])

with tab1:
    col_mode, col_temp = st.columns([1, 1])
    with col_mode:
        mode = st.radio("Protocol:", ["Allopathic (Acute)", "Homeopathic (Constitutional)"], horizontal=True)
    with col_temp:
        selected_temp = st.selectbox("⚡ Quick Load Template:", list(TEMPLATES.keys()))

    # Registration Section
    with st.expander("Patient Registration & Vitals", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            p_id = st.text_input("Patient ID", value=found_record['ID'] if found_record else f"A{len(st.session_state.db)+1}")
            name = st.text_input("Patient Name", value=found_record['Name'] if found_record else "")
        with c2:
            age = st.number_input("Age", value=int(found_record['Age'] if found_record else 28))
            sex = st.selectbox("Sex", ["F", "M", "Other"], index=0 if (found_record['Sex'] if found_record else "F")=="F" else 1)
            weight = st.number_input("Weight (kg)", value=float(found_record['Weight'] if found_record else 85.0))
        with c3:
            bp = st.text_input("BP (mmHg)", value=found_record['BP'] if found_record else "120/80")
            pulse = st.text_input("Pulse", value=found_record['Pulse'] if found_record else "80")
            o2 = st.text_input("O2 Sat (%)", value=found_record['O2'] if found_record else "98")

    # Editable Clinical Analysis Section
    st.subheader("📝 Clinical Protocol (Editable)")
    
    # Logic to prioritize: 1. Found Record (History), 2. Template, 3. Blank
    def get_initial_val(field, template_key):
        if found_record: return found_record[field]
        return TEMPLATES[selected_temp][template_key]

    s_val = get_initial_val("Symptoms", "symp")
    d_val = get_initial_val("Diagnosis", "diag")
    r_val = get_initial_val("Rx", "rx")

    col_a, col_b = st.columns(2)
    with col_a:
        symptoms_final = st.text_area("Symptoms/History", value=s_val)
        diagnosis_final = st.text_input("Diagnosis", value=d_val)
    with col_b:
        rx_final = st.text_area("Prescription / Remedy Plan", value=r_val, height=150)

    if st.button("✅ Save Visit & Print Slip"):
        entry = {
            "ID": p_id, "Name": name, "Age": age, "Sex": sex, "Weight": weight,
            "BP": bp, "Pulse": pulse, "O2": o2, "Symptoms": symptoms_final,
            "Diagnosis": diagnosis_final, "Rx": rx_final, "Timestamp": datetime.now().strftime("%Y-%m-%d")
        }
        st.session_state.db.append(entry)
        
        # Format matching your DISPENSING SLIP FORMAT.pdf [cite: 1-23]
        slip = f"""
{CLINIC_NAME}
{ADDRESS}

{DOCTOR_NAME}
{QUALIFICATIONS}
{TAGLINE}

--------------------------------------------------
PATIENT VISIT SUMMARY ID: {p_id} | Date: {datetime.now().strftime('%b %d, %Y')}
Name: {name.upper()} | Age/Sex: {age}Y/{sex} | Weight: {weight} kg
--------------------------------------------------
VITALS: BP: {bp} | Pulse: {pulse} | O2 Sat: {o2}%
--------------------------------------------------
CLINICAL ANALYSIS
Symptoms: {symptoms_final}
PROVISIONAL DIAGNOSIS: {diagnosis_final}

RX (TREATMENT PLAN)
{rx_final}

GENERAL ADVICE :-
* Monitor vitals. Maintain light diet.
--------------------------------------------------
CHECK AND SIGNATURE:          DR. SUDHANSHU GUPTA
"""
        st.success("Case Recorded!")
        st.text_area("THERMAL PRINT PREVIEW", slip, height=400)

with tab2:
    st.title("📈 Dashboard")
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        st.metric("Patients Today", len(df[df['Timestamp'] == datetime.now().strftime("%Y-%m-%d")]))
        st.bar_chart(df['Diagnosis'].value_counts())
        st.table(df[['ID', 'Name', 'Diagnosis', 'Timestamp']].tail(5))