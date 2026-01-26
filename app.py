import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. SECURITY & ACCESS CONTROL ---
def check_password():
    """Returns True if the user had the correct password."""
    def password_entered():
        # You can change 'Clinic@47553' to your preferred password
        if st.session_state["password"] == "Clinic@47553": 
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 Clinic Management Login")
        st.text_input("Enter Clinic Access Password", type="password", on_change=password_entered, key="password")
        st.info("Authorized access for Dr. Sudhanshu Gupta only.")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔐 Clinic Management Login")
        st.text_input("Enter Clinic Access Password", type="password", on_change=password_entered, key="password")
        st.error("❌ Password incorrect")
        return False
    else:
        return True

if check_password():
    # --- 2. CLINIC CONSTANTS ---
    CLINIC_NAME = "SHRI SWAMI SAMARTH HOMEOPATHIC CLINIC AND HOSPITAL"
    ADDRESS = "BHOSLEWADI BUS STOP, MHGAON ROAD, HINGNA-440011."
    DOCTOR_NAME = "DR. SUDHANSHU GUPTA (REG.NO. 47553)"
    QUALIFICATIONS = "B.H.M.S., P.G.D.C.P., M.D. (HOLISTIC MEDICINE), P.G.D.C.F.L"
    TAGLINE = "CONSULTANT HOMEOPATH AND PSYCHOTHERAPIST"

    # --- 3. DATABASE & TEMPLATES ---
    if 'db' not in st.session_state: st.session_state.db = []

    TEMPLATES = {
        "Custom (Blank)": {"diag": "", "symp": "", "rx": ""},
        "Viral Fever": {"diag": "Acute Viral Syndrome", "symp": "Fever, chills, headache.", "rx": "1. TAB. PARACETAMOL 650mg | 1--1--1 (PC)\n2. TAB. LEVOCETIRIZINE 5mg | 0--0--1 (HS)"},
        "Gastritis": {"diag": "Hyperacidity", "symp": "Nausea, epigastric burning.", "rx": "1. CAP. PANTOPRAZOLE 40mg | 1--0--0 (Empty)\n2. TAB. DOMPERIDONE 10mg | 1--0--1 (Before Food)"}
    }

    # --- 4. SIDEBAR: SEARCH & DATA ---
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
        st.sidebar.download_button("📥 Daily Export (CSV)", df_export.to_csv(index=False).encode('utf-8'), f"OPD_Backup_{datetime.now().strftime('%d-%m-%Y')}.csv")

    uploaded_file = st.sidebar.file_uploader("📤 Morning Import", type=["csv"])
    if uploaded_file:
        st.session_state.db = pd.read_csv(uploaded_file).to_dict('records')

    # --- 5. MAIN INTERFACE ---
    tab1, tab2 = st.tabs(["📋 Consultation", "📊 Clinic Dashboard"])

    with tab1:
        st.subheader("Current OPD Entry")
        mode = st.radio("Protocol Selection:", ["Allopathic (Acute)", "Homeopathic (Constitutional)"], horizontal=True)
        selected_temp = st.selectbox("⚡ Load Template (Editable):", list(TEMPLATES.keys()))

        with st.container():
            c1, c2, c3 = st.columns(3)
            with c1:
                p_id = st.text_input("Patient ID", value=found_record['ID'] if found_record else f"A{len(st.session_state.db)+1}")
                name = st.text_input("Patient Name", value=found_record['Name'] if found_record else "")
            with c2:
                age = st.number_input("Age", value=int(found_record['Age'] if found_record else 28))
                sex = st.selectbox("Sex", ["F", "M", "Other"], index=0 if (found_record['Sex'] if found_record else "F")=="F" else 1)
                weight = st.number_input("Weight (kg)", value=float(found_record['Weight'] if found_record else 85.0))
            with c3:
                bp = st.text_input("BP", value=found_record['BP'] if found_record else "120/80")
                pulse = st.text_input("Pulse", value=found_record['Pulse'] if found_record else "80")
                o2 = st.text_input("O2 Sat", value=found_record['O2'] if found_record else "98")

        st.divider()

        # Logic for pre-filling symptoms and Rx
        init_s = found_record['Symptoms'] if found_record else TEMPLATES[selected_temp]['symp']
        init_d = found_record['Diagnosis'] if found_record else TEMPLATES[selected_temp]['diag']
        init_r = found_record['Rx'] if found_record else TEMPLATES[selected_temp]['rx']

        col_a, col_b = st.columns(2)
        with col_a:
            symptoms_final = st.text_area("Symptoms & History", value=init_s)
            diagnosis_final = st.text_input("Final Diagnosis", value=init_d)
        with col_b:
            rx_final = st.text_area("Prescription (Edit as needed)", value=init_r, height=150)

        if st.button("✅ Save Visit & Generate Slip"):
            entry = {
                "ID": p_id, "Name": name, "Age": age, "Sex": sex, "Weight": weight,
                "BP": bp, "Pulse": pulse, "O2": o2, "Symptoms": symptoms_final,
                "Diagnosis": diagnosis_final, "Rx": rx_final, "Timestamp": datetime.now().strftime("%Y-%m-%d")
            }
            st.session_state.db.append(entry)
            
            # Print Format
            slip = f"{CLINIC_NAME}\n{ADDRESS}\n\n{DOCTOR_NAME}\n{QUALIFICATIONS}\n({TAGLINE})\n" + "="*30 + \
                   f"\nID: {p_id} | Date: {datetime.now().strftime('%b %d, %Y')}\nName: {name.upper()} | {age}Y/{sex}\nWeight: {weight} kg | BP: {bp} | O2: {o2}%\n" + "-"*30 + \
                   f"\nDIAGNOSIS: {diagnosis_final}\n\nRX (TREATMENT PLAN):\n{rx_final}\n" + "-"*30 + \
                   "\nCHECK & SIGNATURE: \n\nDR. SUDHANSHU GUPTA"
            st.success("Case Successfully Recorded!")
            st.text_area("THERMAL PRINTER READY PREVIEW", slip, height=350)

    with tab2:
        st.title("📊 Practice Insights")
        if st.session_state.db:
            df = pd.DataFrame(st.session_state.db)
            st.metric("Total Consultations", len(df))
            st.subheader("Diagnosis Distribution")
            st.bar_chart(df['Diagnosis'].value_counts())
        else:
            st.info("Data will appear here once cases are saved or imported.")