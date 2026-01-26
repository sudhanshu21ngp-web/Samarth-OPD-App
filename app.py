import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. THE TWIN BRAINS (LOGIC ENGINES) ---

def suggest_allopathic(text):
    """Brain for Modern Medicine"""
    s = text.lower()
    if any(x in s for x in ["back", "joint", "stiffness", "pain", "extremities"]):
        return {
            "diag": "Generalized Arthralgia / Spondylosis",
            "rx": "1. TAB. ETORICOXIB 90mg | 0--0--1 (After Food) | 5 Days\n2. TAB. THIOCOLCHICOSIDE 4mg | 1--0--1 (After Food) | 5 Days\n3. TAB. CALCIUM + VIT D3 | 0--1--0 | 15 Days"
        }
    elif any(x in s for x in ["fever", "chill", "cold", "body ache"]):
        return {
            "diag": "Acute Viral Syndrome",
            "rx": "1. TAB. PARACETAMOL 650mg | 1--1--1 (SOS) | 3 Days\n2. TAB. LEVOCETIRIZINE 5mg | 0--0--1 (HS) | 3 Days"
        }
    elif any(x in s for x in ["acidity", "burning", "nausea", "vomiting"]):
        return {
            "diag": "Acute Gastritis / GERD",
            "rx": "1. CAP. PANTOPRAZOLE 40mg | 1--0--0 (Empty Stomach) | 5 Days\n2. SYP. SUCRALFATE | 2 tsp TDS | 5 Days"
        }
    else:
        return {"diag": "", "rx": ""}

def suggest_homeopathic(text):
    """Brain for Homeopathy"""
    s = text.lower()
    # Logic for Patient A2 (Saurabh Gupta)
    if "stiffness" in s and ("morning" in s or "cold" in s):
        return {
            "diag": "Rheumatic Affection",
            "rx": "|REMEDY| Rhus Toxicodendron |\n|POTENCY| 200C |\n|REPETITION| TDS (Thrice Daily) |\n|DURATION| 7 Days |"
        }
    # Logic for Patient A1 (Shreya Naidu)
    elif "fever" in s and ("chill" in s or "restless" in s):
        return {
            "diag": "Viral Pyrexia",
            "rx": "|REMEDY| Arsenicum Album |\n|POTENCY| 30C |\n|REPETITION| Every 2 Hours |\n|DURATION| 2 Days |"
        }
    elif "injury" in s or "fall" in s or "trauma" in s:
        return {
            "diag": "Trauma / Contusion",
            "rx": "|REMEDY| Arnica Montana |\n|POTENCY| 200C |\n|REPETITION| BD (Twice Daily) |\n|DURATION| 5 Days |"
        }
    else:
        return {"diag": "Constitutional Analysis Req.", "rx": "|REMEDY|  |\n|POTENCY|  |\n|REPETITION|  |"}

# --- 2. SECURITY ---
def check_password():
    if "password_correct" not in st.session_state:
        st.sidebar.text_input("🔑 Enter Password", type="password", key="password_input", on_change=verify_pass)
        return False
    return st.session_state["password_correct"]

def verify_pass():
    if st.session_state["password_input"] == "Clinic@47553":
        st.session_state["password_correct"] = True
    else:
        st.sidebar.error("Incorrect Password")

# --- 3. MAIN APP ---
if check_password():
    # Clinic Constants
    CLINIC_NAME = "SHRI SWAMI SAMARTH HOMEOPATHIC CLINIC AND HOSPITAL"
    ADDRESS = "BHOSLEWADI BUS STOP, MHGAON ROAD, HINGNA-440011."
    DOCTOR = "DR. SUDHANSHU GUPTA (REG.NO. 47553)"
    QUALIFICATIONS = "B.H.M.S., P.G.D.C.P., M.D. (HOLISTIC MEDICINE), P.G.D.C.F.L"
    
    if 'db' not in st.session_state: st.session_state.db = []

    # --- SIDEBAR: RECORDS ---
    st.sidebar.title("📂 Records")
    if st.sidebar.button("📥 Export CSV"):
        df = pd.DataFrame(st.session_state.db)
        st.sidebar.download_button("Click to Save", df.to_csv(index=False).encode('utf-8'), "OPD_Data.csv")
    
    # --- MAIN INTERFACE ---
    st.title("🏥 Smart Hybrid OPD")
    
    # A. MODE SWITCHING (Restored!)
    mode = st.radio("Select Protocol Mode:", ["Allopathic (Acute)", "Homeopathic (Constitutional)"], horizontal=True)
    
    # B. Patient Info
    with st.expander("Patient Details & Vitals", expanded=True):
        c1, c2, c3 = st.columns(3)
        p_id = c1.text_input("ID", value=f"A{len(st.session_state.db)+1}")
        name = c2.text_input("Name")
        age = c3.text_input("Age/Sex", "28/F")
        bp = c1.text_input("BP", "120/80")
        weight = c2.text_input("Weight", "60")
        pulse = c3.text_input("Pulse", "80")

    # C. Active Analysis
    st.subheader("Clinical Brain")
    symptoms = st.text_area("Type Symptoms (e.g. 'Stiffness worse in morning')", height=80)
    
    if st.button("⚡ AUTO-ANALYZE CASE"):
        if mode == "Allopathic (Acute)":
            result = suggest_allopathic(symptoms)
        else:
            result = suggest_homeopathic(symptoms)
            
        st.session_state['auto_diag'] = result['diag']
        st.session_state['auto_rx'] = result['rx']
        st.success(f"Generated {mode} Protocol!")

    # D. Final Review (Editable)
    st.divider()
    final_diag = st.text_input("Diagnosis", value=st.session_state.get('auto_diag', ""))
    final_rx = st.text_area("Rx / Remedy Plan", value=st.session_state.get('auto_rx', ""), height=200)

    # E. Print Slip
    if st.button("🖨️ Generate Thermal Slip"):
        # Save to History
        st.session_state.db.append({"ID": p_id, "Name": name, "Diag": final_diag, "Date": datetime.now().strftime("%Y-%m-%d")})
        
        # Format Slip
        slip = f"""
{CLINIC_NAME}
{ADDRESS}

{DOCTOR}
{QUALIFICATIONS}
------------------------------
ID: {p_id} | Name: {name.upper()}
Age/Sex: {age} | Weight: {weight}kg
BP: {bp} | Pulse: {pulse}
------------------------------
DIAGNOSIS: {final_diag}

RX ({'ALLOPATHIC' if mode == 'Allopathic (Acute)' else 'HOMEOPATHIC'}):
{final_rx}
------------------------------
SIGNATURE: DR. SUDHANSHU GUPTA
"""
        st.text_area("Ready for Print", slip, height=400)