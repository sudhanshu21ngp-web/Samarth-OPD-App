import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io
import string
import time

# --- 1. CLINIC BRANDING & CONFIG ---
CLINIC = "SHRI SWAMI SAMARTH HOMEOPATHIC CLINIC AND HOSPITAL"
DR_NAME = "DR. SUDHANSHU GUPTA"
DR_QUAL = "B.H.M.S., P.G.D.C.P., M.D.(HOLISTIC MEDICINE), P.G.D.C.F.L., REG.NO-47553"
TAGLINE = "CONSULTANT HOMEOPATH AND PSYCHOTHERAPIST"

# AI Configuration
API_KEY = "AIzaSyB94LyTAcWiKmOohM1wDOYgrtZeyvO9USY"
genai.configure(api_key=API_KEY)
# 5-Layer Failover Architecture
MODELS = ["gemini-2.5-flash", "gemini-2.0-pro-exp", "gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"]

# --- 2. CORE UTILITIES (ID, PDF, OFFLINE LOGIC) ---

def get_id(count):
    """Calculates ID sequence from A1-A100 to Z1-Z100."""
    letter_idx = (count // 100) % 26
    letter = string.ascii_uppercase[letter_idx]
    number = (count % 100) + 1
    return f"{letter}{number}"

def create_pdf(text):
    """Generates 80mm Thermal Printer PDF."""
    buf = io.BytesIO()
    p = canvas.Canvas(buf, pagesize=(80*mm, 297*mm))
    p.setFont("Helvetica-Bold", 10)
    p.drawString(5*mm, 285*mm, "SHRI SWAMI SAMARTH CLINIC")
    p.setFont("Helvetica", 8)
    y = 275*mm
    for line in text.split('\n'):
        if y < 10*mm: p.showPage(); y = 285*mm
        p.drawString(5*mm, y, line)
        y -= 4.5*mm
    p.showPage(); p.save()
    return buf.getvalue()

def local_fallback(symptoms, mode, vitals):
    """Offline Safety Shield."""
    s = symptoms.lower()
    t_val = "".join(filter(str.isdigit, vitals.get('tmp', '0')))
    is_fever = int(t_val) > 99 if t_val.isdigit() else False
    if mode == "Allopathic":
        if "fever" in s or is_fever:
            return "|DIAGNOSIS| Viral Pyrexia |\n|RX_LIST|\n1. Tab. Paracetamol 650mg --- TDS --- 3 Days\n2. Tab. Pantoprazole 40mg --- OD (E.S.)"
        return "|DIAGNOSIS| Acute Clinical Evaluation |\n|RX_LIST|\n1. Tab. Multivitamin --- OD --- 10 Days"
    return "|DIAGNOSIS| Case Logged |\n|REMEDY| Placebo (Sac Lac) |"

# --- 3. THE "PERFECT TREATMENT" ENGINE ---

def get_clinical_analysis(mode, age, symptoms, vitals, history=""):
    v_str = f"BP: {vitals['bp']}, Pulse: {vitals['pls']}, Temp: {vitals['tmp']}F, Wt: {vitals['wt']}kg"
    
    if mode == "Homeopathic":
        prompt = f"""You are a Master Homeopathic Consultant. Analyze this case:
Age: {age} | Symptoms: {symptoms} | Vitals: {v_str} | History: {history}
Structure: 1.[REPERTORIAL_CHART] 2.[DEEP_ANALYSIS] (Miasm) 3.[DDX_TOP_5] 4.[FINAL_SELECTION_LOGIC] 5.[PLAN_OF_TREATMENT]
AUTO-FILL: |DIAGNOSIS|...|REMEDY|...|POTENCY|...|REPETITION|...|DURATION|..."""
    else:
        prompt = f"""You are a Senior Consultant Physician. Provide a PERFECT ALLOPATHIC PLAN:
Age: {age} | Complaints: {symptoms} | Vitals: {v_str} | Hx: {history}
GUIDELINES: 1. If BP > 140/90, address hypertension. 2. Calculate dose by weight. 3. Follow Indian Rx format.
AUTO-FILL: |DIAGNOSIS|...|RX_LIST| (Drug -- Dose -- Freq -- Dur -- Instr) |ADVICE|..."""

    for attempt, m_name in enumerate(MODELS):
        try:
            model = genai.GenerativeModel(m_name)
            res = model.generate_content(prompt).text
            if "|DIAGNOSIS|" in res: return res, f"{m_name} (Attempt {attempt+1})"
            time.sleep(0.5)
        except: continue
    return local_fallback(symptoms, mode, vitals), "LOCAL_FAILOVER_SHIELD"

# --- 4. STREAMLIT INTERFACE ---

st.set_page_config(page_title="SWAMI SAMARTH PRO V28", layout="wide")
if 'db' not in st.session_state: st.session_state.db = []
if 'f' not in st.session_state: st.session_state.f = {}
if 'inventory' not in st.session_state: st.session_state.inventory = ["Paracetamol", "Pantoprazole", "Cetirizine", "Amlodipine", "Metformin"]

# Sidebar: Inventory & Visit Logs
st.sidebar.title("📁 Clinic Management")
with st.sidebar.expander("📦 Inventory Alert System"):
    new_med = st.text_input("Add Medicine to Stock")
    if st.button("Update Stock"): st.session_state.inventory.append(new_med)
    st.write("Stock:", ", ".join(st.session_state.inventory))

search = st.sidebar.text_input("🔍 Search Patient Name")
if search:
    hits = [r for r in st.session_state.db if search.lower() in r['Name'].lower()]
    for r in reversed(hits):
        if st.sidebar.button(f"📅 {r['Date']} - {r['ID']}", key=f"{r['ID']}{r['Date']}"):
            st.session_state.f = r
    if st.sidebar.button("➕ START FOLLOW-UP"):
        last = hits[-1]
        st.session_state.f = {"ID":last['ID'], "Name":last['Name'], "Age":last['Age'], "Phone":last.get('Phone',""), "Addr":last.get('Addr',""), "Old":f"PREV Dx: {last['Diagnosis']}"}

st.sidebar.divider()
st.sidebar.download_button("📥 Export CSV", pd.DataFrame(st.session_state.db).to_csv(index=False), "Clinic_Data.csv")
up = st.sidebar.file_uploader("📤 Import CSV", type="csv")
if up: st.session_state.db = pd.read_csv(up).to_dict('records')

# Main Form
st.title(f"🏥 {CLINIC}")
st.caption(f"{DR_NAME} | {DR_QUAL} | {TAGLINE}")

with st.container():
    st.subheader("Patient Registration & Vitals")
    c1, c2, c3 = st.columns([1, 2, 1])
    p_id = c1.text_input("ID", value=st.session_state.f.get("ID", get_id(len(st.session_state.db))))
    name = c2.text_input("Full Name", value=st.session_state.f.get("Name", ""))
    age = c3.text_input("Age/Sex", value=st.session_state.f.get("Age", ""))
    
    c4, c5 = st.columns([1, 3])
    phone = c4.text_input("Contact No.", value=st.session_state.f.get("Phone", ""))
    addr = c5.text_input("Address", value=st.session_state.f.get("Addr", ""))
    
    st.markdown("---")
    v1, v2, v3, v4 = st.columns(4)
    bp = v1.text_input("BP (mmHg)", value=st.session_state.f.get("BP", ""))
    pls = v2.text_input("Pulse (bpm)", value=st.session_state.f.get("Pulse", ""))
    wt = v3.text_input("Weight (kg)", value=st.session_state.f.get("Weight", ""))
    tmp = v4.text_input("Temp (F)", value=st.session_state.f.get("Temp", ""))

if "Old" in st.session_state.f: st.warning(st.session_state.f["Old"])

symp = st.text_area("Symptoms")
hist = st.text_area("History")
mode = st.radio("Protocol", ["Homeopathic", "Allopathic"], horizontal=True)

if st.button("🧠 GENERATE PERFECT TREATMENT PLAN"):
    v_dict = {'bp': bp, 'pls': pls, 'wt': wt, 'tmp': tmp}
    ans, engine = get_clinical_analysis(mode, age, symp, v_dict, hist)
    st.session_state['rx'] = ans
    
    # Inventory Alert
    found = [m for m in st.session_state.inventory if m.lower() in ans.lower()]
    if found: st.toast(f"✅ In Stock: {', '.join(found)}", icon="💊")
    st.success(f"System: {engine}")

st.divider()
f_rx = st.text_area("Prescription (Editable)", value=st.session_state.get('rx', ""), height=350)
f_diag = st.text_input("Diagnosis", value=f_rx.split("|DIAGNOSIS|")[-1].split("|")[0] if "|DIAGNOSIS|" in f_rx else "")

if st.button("💾 SAVE & PRINT PDF"):
    timestamp = datetime.now().strftime("%d%m%Y")
    fname = f"RX-{name.replace(' ','').upper()}-{timestamp}.pdf"
    
    st.session_state.db.append({"ID": p_id, "Name": name, "Age": age, "Phone": phone, "Addr": addr, "Symptoms": symp, "Diagnosis": f_diag, "Rx": f_rx, "Date": datetime.now().strftime("%Y-%m-%d"), "BP": bp, "Pulse": pls, "Weight": wt, "Temp": tmp})
    
    pdf_txt = f"{CLINIC}\n{DR_NAME}\n{TAGLINE}\n" + "="*25 + \
              f"\nID: {p_id} | Name: {name}\nAge: {age} | Ph: {phone}\nBP: {bp} | WT: {wt} | T: {tmp}\n" + "-"*25 + \
              f"\nDx: {f_diag}\n\nRx:\n{f_rx}\n" + "="*25
    st.download_button(f"📥 Download {fname}", data=create_pdf(pdf_txt), file_name=fname)
    st.success("Record Finalized.")