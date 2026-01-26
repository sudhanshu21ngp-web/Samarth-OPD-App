import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io
import string

# --- 1. REPAIRED AI-BRAIN LOGIC ---
API_KEY = "AIzaSyB94LyTAcWiKmOohM1wDOYgrtZeyvO9USY"
genai.configure(api_key=API_KEY)
MODELS = ["gemini-2.0-flash-exp", "gemini-2.0-pro-exp", "gemini-1.5-pro", "gemini-1.5-flash"]

def get_clinical_analysis(mode, age, symptoms, history=""):
    """
    Repaired AI Logic: Stricter prompting and Failover Loop.
    """
    if mode == "Homeopathic":
        prompt = f"""You are a Master Homeopathic Consultant. Analyze this case:
        Age: {age} | Symptoms: {symptoms} | History: {history}
        
        REQUIRED STRUCTURE:
        1. [REPERTORIAL_CHART]: Table of rubrics vs top 5 remedies.
        2. [DEEP_ANALYSIS]: Miasmatic (Psora/Sycotic/Syphilitic) & Susceptibility.
        3. [DDX_TOP_5]: Guiding/Confirmatory/Ruling Out symptoms for top 5.
        4. [FINAL_SELECTION_LOGIC]: Detailed reasoning for Simillimum.
        5. [PLAN_OF_TREATMENT]: Potency & auxiliary advice.
        
        AUTO-FILL SECTION:
        |DIAGNOSIS| (Enter Clinical Diagnosis) |
        |REMEDY| (Final Simillimum) |
        |POTENCY| (Selected Potency) |
        |REPETITION| (Schedule) |
        |DURATION| (Days) |
        """
    else:
        prompt = f"Clinical Consultant Analysis. Age: {age}, Symptoms: {symptoms}. Provide Diagnosis and Rx. |DIAGNOSIS|...|RX_LIST|..."

    # Multi-Model Failover Loop
    for m_name in MODELS:
        try:
            model = genai.GenerativeModel(m_name)
            response = model.generate_content(prompt)
            return response.text, m_name
        except Exception:
            continue
            
    # Final Local Fallback if all APIs fail
    return local_medical_brain(symptoms, mode), "LOCAL_FALLBACK_ENGINE"

def local_medical_brain(symptoms, mode):
    s = symptoms.lower()
    # Expanded pediatric & common clinical protocols
    if "cough" in s or "breath" in s: protocol = "|DIAGNOSIS| Bronchial Irritation |REMEDY| Bryonia |POTENCY| 30 |"
    elif "skin" in s or "itch" in s: protocol = "|DIAGNOSIS| Dermatitis |REMEDY| Sulphur |POTENCY| 200 |"
    elif "injury" in s or "pain" in s: protocol = "|DIAGNOSIS| Trauma |REMEDY| Arnica |POTENCY| 200 |"
    else: protocol = "|DIAGNOSIS| Acute Presentation |REMEDY| Placebo |POTENCY| -- |"
    return protocol

# --- 2. PATIENT ID & PDF LOGIC (NO OMISSION) ---
def get_id(count):
    letter = string.ascii_uppercase[count // 100] if count // 100 < 26 else "Z"
    return f"{letter}{(count % 100) + 1}"

def create_pdf(text):
    buf = io.BytesIO()
    p = canvas.Canvas(buf, pagesize=(80*mm, 250*mm))
    p.setFont("Helvetica-Bold", 10)
    p.drawString(10*mm, 240*mm, "SHRI SWAMI SAMARTH CLINIC")
    p.setFont("Helvetica", 8)
    y = 230*mm
    for line in text.split('\n'):
        if y < 10*mm: break
        p.drawString(5*mm, y, line)
        y -= 4*mm
    p.showPage(); p.save()
    return buf.getvalue()

# --- 3. APP INTERFACE ---
st.set_page_config(page_title="SWAMI SAMARTH CLINIC PRO", layout="wide")
if 'db' not in st.session_state: st.session_state.db = []
if 'f' not in st.session_state: st.session_state.f = {}

# Branding
CLINIC = "SHRI SWAMI SAMARTH HOMEOPATHIC CLINIC AND HOSPITAL"
DR_DETAILS = "DR. SUDHANSHU GUPTA | B.H.M.S., M.D., REG: 47553\nCONSULTANT HOMEOPATH AND PSYCHOTHERAPIST"

# Sidebar: Search & Follow-up (REPAIRED)
st.sidebar.title("🔍 Patient Records")
search = st.sidebar.text_input("Search Name")
if search:
    hits = [r for r in st.session_state.db if search.lower() in r['Name'].lower()]
    for r in reversed(hits):
        if st.sidebar.button(f"📅 {r['Date']} - {r['Name']}", key=f"rec_{r['Date']}{r['ID']}"):
            st.session_state.f = r
    if st.sidebar.button("➕ START NEW FOLLOW-UP"):
        if hits:
            last = hits[-1]
            st.session_state.f = {"ID": last['ID'], "Name": last['Name'], "Age": last['Age'], "Old": f"LAST SYMPTOMS: {last['Symptoms']}\nLAST RX: {last['Rx']}"}

st.sidebar.divider()
# Import/Export (NO OMISSION)
if st.session_state.db:
    st.sidebar.download_button("📥 Export CSV", pd.DataFrame(st.session_state.db).to_csv(index=False), "Clinic_Data.csv")
up = st.sidebar.file_uploader("📤 Import CSV", type="csv")
if up: st.session_state.db = pd.read_csv(up).to_dict('records')

# --- 4. CONSULTATION FORM ---
st.title(f"🏥 {CLINIC}")
st.caption(DR_DETAILS)

with st.expander("Patient Vitals & ID", expanded=True):
    c1, c2, c3 = st.columns(3)
    p_id = c1.text_input("ID", value=st.session_state.f.get("ID", get_id(len(st.session_state.db))))
    name = c2.text_input("Name", value=st.session_state.f.get("Name", ""))
    age = c3.text_input("Age/Sex", value=st.session_state.f.get("Age", ""))
    
if "Old" in st.session_state.f: st.warning(st.session_state.f["Old"])

symp = st.text_area("Present Symptoms")
hist = st.text_area("Past/Family History (For Miasmatic Analysis)")
mode = st.radio("Mode", ["Homeopathic", "Allopathic"], horizontal=True)

if st.button("🧠 GENERATE CLINICAL ANALYSIS"):
    with st.spinner("Cycling Multi-Model AI Failover..."):
        ans, engine = get_clinical_analysis(mode, age, symp, hist)
        st.session_state['ai_raw'] = ans
        st.info(f"Analysis Engine: {engine}")

st.divider()
st.subheader("AI Detailed Logic")
st.write(st.session_state.get('ai_raw', "Waiting for input..."))

# FINAL EDITABLE BOXES
rx_final = st.text_area("Final Prescription (Editable)", value=st.session_state.get('ai_raw', ""), height=200)
diag_final = st.text_input("Final Diagnosis", value=rx_final.split("|DIAGNOSIS|")[-1].split("|")[0] if "|DIAGNOSIS|" in rx_final else "")

if st.button("💾 SAVE & PRINT PDF"):
    timestamp = datetime.now().strftime("%d%m%Y")
    filename = f"RX-{name.replace(' ','').upper()}-{timestamp}.pdf"
    
    # Save Visit
    st.session_state.db.append({"ID": p_id, "Name": name, "Age": age, "Symptoms": symp, "Diagnosis": diag_final, "Rx": rx_final, "Date": datetime.now().strftime("%Y-%m-%d")})
    
    # PDF Construction
    pdf_txt = f"{CLINIC}\n{DR_DETAILS}\n" + "="*20 + f"\nID: {p_id} | Name: {name}\nDate: {datetime.now().strftime('%d-%m-%Y')}\n" + "-"*20 + f"\nDx: {diag_final}\n\nRx:\n{rx_final}\n" + "="*20
    st.download_button(f"📥 Download {filename}", data=create_pdf(pdf_txt), file_name=filename)
    st.success("Record Saved Successfully!")