import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io
import string

# --- 1. AI-BRAIN: VITAL-AWARE LOGIC ---
API_KEY = "AIzaSyB94LyTAcWiKmOohM1wDOYgrtZeyvO9USY"
genai.configure(api_key=API_KEY)
MODELS = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-pro", "gemini-2.0-flash"]

def get_clinical_analysis(mode, age, symptoms, vitals, history=""):
    """Repaired to ensure Vitals are integrated into the Rx logic."""
    v_str = f"BP: {vitals['bp']}, Pulse: {vitals['pls']}, Temp: {vitals['tmp']}, Wt: {vitals['wt']}kg"
    
    if mode == "Homeopathic":
        prompt = f"""Master Homeopathic Consultant. 
        Case: Age {age} | Symptoms: {symptoms} | Vitals: {v_str} | History: {history}
        Structure: 1.[REPERTORIAL_CHART] 2.[DEEP_ANALYSIS] (Miasmatic) 3.[DDX_TOP_5] 4.[FINAL_SELECTION_LOGIC] 5.[PLAN_OF_TREATMENT]
        AUTO-FILL: |DIAGNOSIS|...|REMEDY|...|POTENCY|...|REPETITION|..."""
    else:
        # Repaired Allopathic logic to specifically consider vitals (e.g., Fever, Hypertension)
        prompt = f"""Clinical Consultant. 
        Case: Age {age} | Symptoms: {symptoms} | Vitals: {v_str}.
        Instructions: Analyze the vitals. If BP or Temp is abnormal, include it in the plan.
        Provide Provisional Diagnosis and Medicines with Dosage.
        FOR SYSTEM AUTO-FILL:
        |DIAGNOSIS| (Enter Result) |
        |RX_LIST| (Include vital-specific medications if needed) |"""

    for m_name in MODELS:
        try:
            model = genai.GenerativeModel(m_name)
            res = model.generate_content(prompt).text
            if "|DIAGNOSIS|" in res: return res, m_name
        except: continue
    return local_fallback(symptoms, mode), "LOCAL_BRAIN_TEMPLATE"

def local_fallback(symptoms, mode):
    s = symptoms.lower()
    if mode == "Allopathic":
        return "|DIAGNOSIS| Clinical Review |RX_LIST| 1. Symptomatic Treatment based on Vitals |"
    return "|DIAGNOSIS| Chronic Case |REMEDY| Pending AI Analysis |"

# --- 2. CORE UTILITIES (ID/PDF/DATA) ---
def get_id(count):
    letter = string.ascii_uppercase[count // 100] if count // 100 < 26 else "Z"
    return f"{letter}{(count % 100) + 1}"

def create_pdf(text):
    buf = io.BytesIO()
    p = canvas.Canvas(buf, pagesize=(80*mm, 297*mm))
    p.setFont("Helvetica-Bold", 10)
    p.drawString(5*mm, 285*mm, "SHRI SWAMI SAMARTH CLINIC")
    p.setFont("Helvetica", 8)
    y = 275*mm
    for line in text.split('\n'):
        if y < 10*mm: break
        p.drawString(5*mm, y, line); y -= 4.5*mm
    p.showPage(); p.save()
    return buf.getvalue()

# --- 3. APP SETUP ---
st.set_page_config(page_title="SWAMI SAMARTH PRO V19", layout="wide")
if 'db' not in st.session_state: st.session_state.db = []
if 'f' not in st.session_state: st.session_state.f = {}

CLINIC = "SHRI SWAMI SAMARTH HOMEOPATHIC CLINIC AND HOSPITAL"
DR_NAME = "DR. SUDHANSHU GUPTA"
DR_QUAL = "B.H.M.S., P.G.D.C.P., M.D., P.G.D.C.F.L., REG.NO-47553"
TAGLINE = "CONSULTANT HOMEOPATH AND PSYCHOTHERAPIST"

# --- 4. SIDEBAR (VISIT LOGS & EXPORT) ---
st.sidebar.title("📁 Clinic Management")
search = st.sidebar.text_input("🔍 Search Name")
if search:
    hits = [r for r in st.session_state.db if search.lower() in r['Name'].lower()]
    for r in reversed(hits):
        if st.sidebar.button(f"📅 {r['Date']} - {r['ID']}", key=f"l_{r['Date']}{r['ID']}"):
            st.session_state.f = r
    if st.sidebar.button("➕ NEW FOLLOW-UP"):
        last = hits[-1]
        st.session_state.f = {"ID":last['ID'], "Name":last['Name'], "Age":last['Age'], "Phone":last.get('Phone',""), "Addr":last.get('Addr',""), "Old":f"PREV RX: {last['Rx']}"}

st.sidebar.divider()
if st.session_state.db:
    st.sidebar.download_button("📥 Export DB", pd.DataFrame(st.session_state.db).to_csv(index=False), "Clinic_Data.csv")
up = st.sidebar.file_uploader("📤 Import DB", type="csv")
if up: st.session_state.db = pd.read_csv(up).to_dict('records')

# --- 5. CONSULTATION FORM ---
st.title(f"🏥 {CLINIC}")
st.caption(f"{DR_NAME} | {DR_QUAL} | {TAGLINE}")

with st.container():
    st.subheader("Patient Registration & Vitals")
    c1, c2, c3 = st.columns(3)
    p_id = c1.text_input("ID", value=st.session_state.f.get("ID", get_id(len(st.session_state.db))))
    name = c2.text_input("Full Name", value=st.session_state.f.get("Name", ""))
    age = c3.text_input("Age/Sex", value=st.session_state.f.get("Age", ""))
    phone = c1.text_input("Contact No.", value=st.session_state.f.get("Phone", ""))
    addr = c2.text_area("Address", value=st.session_state.f.get("Addr", ""), height=65)
    
    v1, v2, v3, v4 = st.columns(4)
    bp = v1.text_input("BP", value=st.session_state.f.get("BP", ""))
    pls = v2.text_input("Pulse", value=st.session_state.f.get("Pulse", ""))
    wt = v3.text_input("Weight (kg)", value=st.session_state.f.get("Weight", ""))
    tmp = v4.text_input("Temp", value=st.session_state.f.get("Temp", ""))

if "Old" in st.session_state.f: st.warning(st.session_state.f["Old"])

symp = st.text_area("Symptoms")
hist = st.text_area("History")
mode = st.radio("Protocol", ["Homeopathic", "Allopathic"], horizontal=True)

if st.button("🧠 GENERATE ANALYSIS"):
    vitals_dict = {'bp': bp, 'pls': pls, 'wt': wt, 'tmp': tmp}
    ans, engine = get_clinical_analysis(mode, age, symp, vitals_dict, hist)
    st.session_state['rx'] = ans
    st.toast(f"Engine: {engine}")

# --- 6. FINAL EDIT & PRINT ---
st.divider()
f_rx = st.text_area("Prescription", value=st.session_state.get('rx', ""), height=250)
f_diag = st.text_input("Diagnosis", value=f_rx.split("|DIAGNOSIS|")[-1].split("|")[0] if "|DIAGNOSIS|" in f_rx else "")

if st.button("💾 SAVE & PRINT"):
    timestamp = datetime.now().strftime("%d%m%Y")
    fname = f"RX-{name.replace(' ','').upper()}-{timestamp}.pdf"
    
    st.session_state.db.append({"ID": p_id, "Name": name, "Age": age, "Phone": phone, "Addr": addr, "Symptoms": symp, "Diagnosis": f_diag, "Rx": f_rx, "Date": datetime.now().strftime("%Y-%m-%d"), "BP": bp, "Pulse": pls, "Weight": wt, "Temp": tmp})
    
    pdf_txt = f"{CLINIC}\n{DR_NAME}\n{TAGLINE}\n" + "="*20 + \
              f"\nID: {p_id} | Name: {name}\nAge: {age} | Contact: {phone}\nBP: {bp} | WT: {wt}kg | Pulse: {pls}\n" + "-"*20 + \
              f"\nDx: {f_diag}\n\nRx:\n{f_rx}\n" + "="*20
    st.download_button(f"📥 Download {fname}", data=create_pdf(pdf_txt), file_name=fname)
    st.success("Saved Successfully.")