import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io
import string

# --- 1. AI-BRAIN FAILOVER ENGINE ---
API_KEY = "AIzaSyB94LyTAcWiKmOohM1wDOYgrtZeyvO9USY"
genai.configure(api_key=API_KEY)
MODELS = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-pro", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]

def get_clinical_analysis(mode, age, symptoms, history=""):
    if mode == "Homeopathic":
        prompt = f"""You are a Master Homeopathic Consultant. Analyze: Age {age}, Symptoms: {symptoms}, History: {history}.
        Structure: 1.[REPERTORIAL_CHART] 2.[DEEP_ANALYSIS] (Miasmatic background) 3.[DDX_TOP_5] 4.[FINAL_SELECTION_LOGIC] 5.[PLAN_OF_TREATMENT].
        AUTO-FILL: |DIAGNOSIS|...|REMEDY|...|POTENCY|...|REPETITION|..."""
    else:
        prompt = f"""Clinical Consultant. Provide Allopathic Rx for Age: {age} | Symptoms: {symptoms}.
        Include Provisional Diagnosis and numbered list of medicines with Dosage/Duration.
        AUTO-FILL: |DIAGNOSIS|...|RX_LIST|..."""

    for m_name in MODELS:
        try:
            model = genai.GenerativeModel(m_name)
            return model.generate_content(prompt).text, m_name
        except: continue
    return "|DIAGNOSIS| Review Required |REMEDY| Local Fallback Applied |", "LOCAL_BRAIN"

# --- 2. CORE UTILITIES (ID, PDF, EXPORT) ---
def get_id(count):
    letter = string.ascii_uppercase[count // 100] if count // 100 < 26 else "Z"
    return f"{letter}{(count % 100) + 1}"

def create_pdf(text):
    buf = io.BytesIO()
    p = canvas.Canvas(buf, pagesize=(80*mm, 297*mm)) # A4 width for thermal compatibility
    p.setFont("Helvetica-Bold", 10)
    p.drawString(5*mm, 285*mm, "SHRI SWAMI SAMARTH CLINIC")
    p.setFont("Helvetica", 8)
    y = 275*mm
    for line in text.split('\n'):
        if y < 10*mm: break
        p.drawString(5*mm, y, line)
        y -= 4.5*mm
    p.showPage(); p.save()
    return buf.getvalue()

# --- 3. APP SETUP & DATA ---
st.set_page_config(page_title="SWAMI SAMARTH CLINIC PRO V16", layout="wide")
if 'db' not in st.session_state: st.session_state.db = []
if 'f' not in st.session_state: st.session_state.f = {}

CLINIC = "SHRI SWAMI SAMARTH HOMEOPATHIC CLINIC AND HOSPITAL"
DR_DETAILS = "DR. SUDHANSHU GUPTA | B.H.M.S., M.D., REG: 47553\nCONSULTANT HOMEOPATH AND PSYCHOTHERAPIST"

# --- 4. SIDEBAR: VISIT LOGS & DATA MGMT ---
st.sidebar.title("📁 Clinic Management")

# A. Visit Log List & Search
search = st.sidebar.text_input("🔍 Search Patient (Name)")
if search:
    hits = [r for r in st.session_state.db if search.lower() in r['Name'].lower()]
    if hits:
        st.sidebar.subheader(f"Visit Logs ({len(hits)})")
        for r in reversed(hits):
            if st.sidebar.button(f"📅 {r['Date']} - {r['ID']}", key=f"log_{r['Date']}{r['ID']}"):
                st.session_state.f = r # Reload old visit
        
        if st.sidebar.button("➕ NEW FOLLOW-UP FORM"):
            last = hits[-1]
            st.session_state.f = {
                "ID": last['ID'], "Name": last['Name'], "Age": last['Age'], 
                "Address": last.get('Address', ""), "Phone": last.get('Phone', ""),
                "Old_Complaints": last['Symptoms'], "Old_Rx": last['Rx']
            }
st.sidebar.divider()

# B. Import/Export
st.sidebar.subheader("💾 Backup & Restore")
if st.session_state.db:
    st.sidebar.download_button("📥 Export Database (CSV)", pd.DataFrame(st.session_state.db).to_csv(index=False), "Clinic_Database.csv")
up = st.sidebar.file_uploader("📤 Import Database (CSV)", type="csv")
if up: 
    st.session_state.db = pd.read_csv(up).to_dict('records')
    st.sidebar.success("Records Restored!")

# --- 5. PATIENT REGISTRATION & VITALS ---
st.title(f"🏥 {CLINIC}")
st.caption(DR_DETAILS)

with st.container():
    st.subheader("Patient Registration & Vitals")
    c1, c2, c3 = st.columns(3)
    p_id = c1.text_input("ID", value=st.session_state.f.get("ID", get_id(len(st.session_state.db))))
    name = c2.text_input("Patient Name", value=st.session_state.f.get("Name", ""))
    age_sex = c3.text_input("Age/Sex", value=st.session_state.f.get("Age", ""))
    
    # NEW: ADDRESS AND CONTACT FIELDS
    phone = c1.text_input("Contact Number", value=st.session_state.f.get("Phone", ""))
    address = c2.text_area("Patient Address", value=st.session_state.f.get("Address", ""), height=68)
    
    with st.expander("Clinical Vitals (BP, Pulse, Weight)", expanded=True):
        v1, v2, v3, v4 = st.columns(4)
        bp = v1.text_input("BP", value=st.session_state.f.get("BP", ""))
        pulse = v2.text_input("Pulse", value=st.session_state.f.get("Pulse", ""))
        weight = v3.text_input("Weight (kg)", value=st.session_state.f.get("Weight", ""))
        temp = v4.text_input("Temp", value=st.session_state.f.get("Temp", ""))

if "Old_Complaints" in st.session_state.f:
    st.info(f"📌 LAST VISIT STATUS:\nComplaints: {st.session_state.f['Old_Complaints']}\nLast Rx: {st.session_state.f['Old_Rx']}")

# --- 6. CONSULTATION & AI ---
st.divider()
symp = st.text_area("Presenting Symptoms / Follow-up Status")
hist = st.text_area("Medical/Family History (For Constitutional Analysis)")
mode = st.radio("Treatment Protocol", ["Homeopathic", "Allopathic"], horizontal=True)

if st.button("🧠 GENERATE AI CLINICAL ANALYSIS"):
    with st.spinner("Analyzing case history and vitals..."):
        full_context = f"Symptoms: {symp} | Vitals: BP {bp}, Pulse {pulse}, Wt {weight}"
        ans, engine = get_clinical_analysis(mode, age_sex, full_context, hist)
        st.session_state['current_rx'] = ans
        st.success(f"Analysis complete using {engine}")

# --- 7. EDITABLE PRESCRIPTION & SAVE ---
st.divider()
st.subheader("Final Editable Prescription")
f_rx = st.text_area("Prescription Plan (Edit as needed)", value=st.session_state.get('current_rx', ""), height=300)

diag_val = ""
if "|DIAGNOSIS|" in f_rx:
    diag_val = f_rx.split("|DIAGNOSIS|")[-1].split("|")[0].strip()
f_diag = st.text_input("Final Diagnosis", value=diag_val)

if st.button("💾 SAVE VISIT & GENERATE PDF"):
    timestamp = datetime.now().strftime("%d%m%Y")
    clean_name = name.replace(" ", "").upper()
    filename = f"RX-{clean_name}-{timestamp}.pdf"
    
    # Record the Visit
    visit_data = {
        "ID": p_id, "Name": name, "Age": age_sex, "Phone": phone, "Address": address,
        "Symptoms": symp, "Diagnosis": f_diag, "Rx": f_rx, "Date": datetime.now().strftime("%Y-%m-%d"),
        "BP": bp, "Pulse": pulse, "Weight": weight, "Temp": temp
    }
    st.session_state.db.append(visit_data)
    
    # Build Thermal Slip
    slip_text = f"{CLINIC}\n{DR_DETAILS}\n" + "="*25 + \
                f"\nID: {p_id} | Name: {name}\nContact: {phone}\nAge/Sex: {age_sex}\nDate: {datetime.now().strftime('%d-%m-%Y')}\n" + \
                f"BP: {bp} | Pulse: {pulse} | Wt: {weight}\n" + "-"*25 + \
                f"\nDIAGNOSIS: {f_diag}\n\nRX:\n{f_rx}\n" + "="*25 + "\nDr. Sudhanshu Gupta"
    
    st.download_button(f"📥 Download {filename}", data=create_pdf(slip_text), file_name=filename)
    st.success("Patient Record Updated and Saved.")