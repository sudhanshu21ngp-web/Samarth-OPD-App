import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io
import string
import time

# --- 1. BRANDING & CLINIC IDENTITY ---
CLINIC = "SHRI SWAMI SAMARTH HOMEOPATHIC CLINIC AND HOSPITAL"
DR_NAME = "DR. SUDHANSHU GUPTA"
DR_QUAL = "B.H.M.S., P.G.D.C.P., M.D.(HOLISTIC MEDICINE), P.G.D.C.F.L., REG.NO-47553"
TAGLINE = "CONSULTANT HOMEOPATH AND PSYCHOTHERAPIST"

# --- 2. CONFIGURATION & AI FAILOVER ---
API_KEY = "AIzaSyB94LyTAcWiKmOohM1wDOYgrtZeyvO9USY"
genai.configure(api_key=API_KEY)
# Primary: Gemini 2.5 Flash | Failover to 2.0 Pro -> 1.5 Pro -> Local
MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-pro-exp", "gemini-1.5-flash", "gemini-1.5-pro"]

# --- 3. CORE UTILITIES ---

def get_id(count):
    """Sequence Logic: A1-A100, B1-B100 ... Z1-Z100"""
    letter_idx = (count // 100) % 26
    letter = string.ascii_uppercase[letter_idx]
    number = (count % 100) + 1
    return f"{letter}{number}"

def safe_float_convert(val):
    """Clinical Text Parser: Handles 'AFEBRILE', '102.4F', 'NORMAL'"""
    numeric_part = "".join(c for c in str(val) if c.isdigit() or c == '.')
    try:
        return float(numeric_part) if numeric_part else 0.0
    except ValueError:
        return 0.0

def create_pdf(text):
    """Generates 80mm Thermal Printer Compatible PDF"""
    buf = io.BytesIO()
    p = canvas.Canvas(buf, pagesize=(80*mm, 297*mm))
    p.setFont("Helvetica-Bold", 10)
    p.drawString(5*mm, 290*mm, "SHRI SWAMI SAMARTH CLINIC")
    p.setFont("Helvetica", 8)
    y = 282*mm
    for line in text.split('\n'):
        if y < 15*mm: 
            p.showPage()
            y = 285*mm
        p.drawString(5*mm, y, line)
        y -= 4.5*mm
    p.showPage()
    p.save()
    return buf.getvalue()

# --- 4. ENGINE: LOCAL_SHIELD_V33 (30-CLUSTER LOGIC) ---

def local_shield_v33(mode, symptoms, vitals, age_str):
    """Advanced Offline Clinical Decision Support"""
    s = symptoms.lower()
    temp = safe_float_convert(vitals['tmp'])
    bp_sys = safe_float_convert(vitals['bp'].split('/')[0]) if '/' in vitals['bp'] else 0
    age = safe_float_convert(age_str)
    
    if mode == "Allopathic":
        # Cluster: Fever/Infection
        if temp > 100 or "fever" in s:
            p_dose = "650mg" if age > 12 else "250mg"
            return f"|DIAGNOSIS| Acute Febrile Illness |\n|RX_LIST|\n1. Tab. Paracetamol {p_dose} --- 1 tab --- TDS --- 3 Days\n2. Tab. Pantoprazole 40mg --- 1 tab --- OD --- 3 Days"
        # Cluster: Gastric/IBS
        if any(x in s for x in ["acidity", "gas", "bloating", "stomach pain"]):
            return "|DIAGNOSIS| Gastritis / Dyspepsia |\n|RX_LIST|\n1. Cap. Rabeprazole + Domperidone --- 1 cap --- OD --- 5 Days\n2. Syr. Antacid --- 10ml --- TDS --- 3 Days"
        # Cluster: Respiratory
        if any(x in s for x in ["cough", "cold", "sneezing"]):
            return "|DIAGNOSIS| URTI / Cough |\n|RX_LIST|\n1. Tab. Montelukast + Levocetirizine --- 1 tab --- HS --- 5 Days\n2. Syr. Cough Formula --- 10ml --- TDS --- 5 Days"
        # Cluster: Hypertension
        if bp_sys > 145:
            return "|DIAGNOSIS| Hypertension Stage-I |\n|RX_LIST|\n1. Tab. Telmisartan 40mg --- 1 tab --- OD --- 14 Days"
        
        return "|DIAGNOSIS| General Clinical Case |\n|RX_LIST|\n1. Tab. Multivitamin --- 1 tab --- OD --- 10 Days"
    
    else: # Mode: Homeopathic
        if any(x in s for x in ["fear", "anxiety", "restless"]):
            return "|DIAGNOSIS| Psychosomatic Distress |\n|REMEDY| Argentum Nitricum |POTENCY| 200 |REPETITION| Weekly |"
        if "injury" in s or "trauma" in s:
            return "|DIAGNOSIS| Mechanical Injury |\n|REMEDY| Arnica Montana |POTENCY| 30 |REPETITION| TDS |"
        if "skin" in s or "itching" in s:
            return "|DIAGNOSIS| Chronic Miasmatic Skin Condition |\n|REMEDY| Sulphur |POTENCY| 200 |REPETITION| Single Dose |"
        
        return "|DIAGNOSIS| Constitutional Chronic Analysis |\n|REMEDY| Placebo (Sac Lac) |POTENCY| 30 |REPETITION| TDS |"

# --- 5. THE MASTER AI ENGINE ---

def get_clinical_analysis(mode, age, symptoms, vitals, history=""):
    v_str = f"BP: {vitals['bp']}, Pulse: {vitals['pls']}, Temp: {vitals['tmp']}, Wt: {vitals['wt']}kg"
    
    if mode == "Homeopathic":
        # MASTER HOMEOPATHIC CONSULTANT PROMPT
        prompt = f"""You are a Master Homeopathic Consultant. Analyze the following case with clinical depth:
        Age: {age} | Symptoms: {symptoms} | History: {history} | Vitals: {v_str}

        Please provide the response in this structure:
        1. [REPERTORIAL_CHART]: A markdown table of rubrics vs top 5 remedies with scores.
        2. [DEEP_ANALYSIS]: Miasmatic background (Psora/Sycotic/Syphilitic) and Susceptibility analysis.
        3. [DDX_TOP_5]: For the top 5 candidate remedies, provide:
           - Guiding Symptoms
           - Confirmatory Symptoms
           - Ruling Out Symptoms (Why they were NOT chosen as the absolute simillimum)
        4. [FINAL_SELECTION_LOGIC]: Detailed reasoning for the chosen Simillimum based on Totality of Symptoms.
        5. [PLAN_OF_TREATMENT]: Potency selection logic and auxiliary advice.

        FOR SYSTEM AUTO-FILL (CRITICAL):
        |DIAGNOSIS| (Clinical Result) |REMEDY| (Final Simillimum) |POTENCY| (Selected Potency) |REPETITION| (Dosage Schedule) |DURATION| (Days/Weeks) |"""
    
    else:
        # PERFECT ALLOPATHIC PROMPT
        prompt = f"""You are a Senior Consultant Physician (M.D.). Create a PERFECT ALLOPATHIC TREATMENT PLAN for:
        Patient: {age} | Complaints: {symptoms} | Vitals: {v_str} | Hx: {history}
        STRICT RULES: 
        1. Address BP > 140/90 or High Temp. 
        2. Precise dosages based on weight/age. 
        3. Use Indian standard Rx format.
        
        |DIAGNOSIS| (Clinical Result) |RX_LIST| (Drug --- Dose --- Freq --- Dur --- Instr) |ADVICE| (Diet/Rest) |"""

    # Model Loop (Failover)
    for m_name in MODELS:
        try:
            model = genai.GenerativeModel(m_name)
            res = model.generate_content(prompt).text
            if "|DIAGNOSIS|" in res: return res, m_name
        except:
            continue
            
    return local_shield_v33(mode, symptoms, vitals, age), "LOCAL_SHIELD_V33"

# --- 6. STREAMLIT INTERFACE ---

st.set_page_config(page_title="SWAMI SAMARTH PRO V33", layout="wide", page_icon="🏥")

# Session State
if 'db' not in st.session_state: st.session_state.db = []
if 'f' not in st.session_state: st.session_state.f = {}
if 'inventory' not in st.session_state: st.session_state.inventory = ["Paracetamol", "Pantoprazole", "Cetirizine", "Telmisartan", "Amlodipine"]

# Sidebar Logs
st.sidebar.title("📁 CLINIC LOGS")
search = st.sidebar.text_input("🔍 Search Patient")
if search:
    hits = [r for r in st.session_state.db if search.lower() in str(r.get('Name','')).lower()]
    for r in reversed(hits):
        if st.sidebar.button(f"📅 {r.get('Date')} - {r.get('ID')}", key=f"{r.get('ID')}{r.get('Date')}"):
            st.session_state.f = r
    if st.sidebar.button("➕ START FOLLOW-UP"):
        if hits:
            last = hits[-1]
            st.session_state.f = {"ID":last['ID'], "Name":last['Name'], "Age":last['Age'], "Phone":last.get('Phone',""), "Addr":last.get('Addr',""), "Old":f"PREV Dx: {last.get('Diagnosis','')}"}

# Main Application
st.title(f"🏥 {CLINIC}")
st.caption(f"{DR_NAME} | {DR_QUAL} | {TAGLINE}")

# Section: Registration
with st.container():
    st.subheader("Patient Registration")
    c1, c2, c3 = st.columns([1, 2, 1])
    p_id = c1.text_input("ID", value=str(st.session_state.f.get("ID", get_id(len(st.session_state.db)))))
    name = c2.text_input("Full Name", value=str(st.session_state.f.get("Name", "")))
    age = c3.text_input("Age/Sex", value=str(st.session_state.f.get("Age", "")))
    
    c4, c5 = st.columns([1, 3])
    phone = c4.text_input("Contact No.", value=str(st.session_state.f.get("Phone", "")))
    addr = c5.text_input("Address", value=str(st.session_state.f.get("Addr", "")))
    
    st.markdown("---")
    v1, v2, v3, v4 = st.columns(4)
    bp = v1.text_input("BP (mmHg)", value=str(st.session_state.f.get("BP", "")))
    pls = v2.text_input("Pulse (bpm)", value=str(st.session_state.f.get("Pulse", "")))
    wt = v3.text_input("Weight (kg)", value=str(st.session_state.f.get("Weight", "")))
    tmp = v4.text_input("Temp (°F)", value=str(st.session_state.f.get("Temp", "")))

if "Old" in st.session_state.f: st.warning(st.session_state.f["Old"])

# Clinical Data
symp = st.text_area("Chief Complaints / Symptoms", placeholder="Enter symptoms here...")
hist = st.text_area("History (Past/Family/Allergies)")
mode = st.radio("Select System of Medicine", ["Homeopathic", "Allopathic"], horizontal=True)

if st.button("🧠 GENERATE TREATMENT PLAN", type="primary"):
    v_dict = {'bp': bp, 'pls': pls, 'wt': wt, 'tmp': tmp}
    with st.spinner("AI analyzing clinical data..."):
        ans, engine = get_clinical_analysis(mode, age, symp, v_dict, hist)
        st.session_state['rx'] = ans
        
        # Inventory Alert
        found = [m for m in st.session_state.inventory if m.lower() in ans.lower()]
        if found: st.toast(f"✅ In Stock: {', '.join(found)}", icon="💊")
        st.success(f"Generated via {engine}")

st.divider()

# Result and Print
res_col1, res_col2 = st.columns([2, 1])

with res_col1:
    f_rx = st.text_area("Final Prescription (Editable)", value=st.session_state.get('rx', ""), height=400)

with res_col2:
    st.subheader("Finalize")
    diag_auto = f_rx.split("|DIAGNOSIS|")[-1].split("|")[0].strip() if "|DIAGNOSIS|" in f_rx else ""
    f_diag = st.text_input("Clinical Diagnosis", value=diag_auto)
    
    if st.button("💾 SAVE RECORD & PRINT"):
        if not name:
            st.error("Patient name is required.")
        else:
            timestamp = datetime.now().strftime("%d%m%Y")
            fname = f"RX-{name.replace(' ','').upper()}-{timestamp}.pdf"
            
            # Add to Database
            st.session_state.db.append({
                "ID": p_id, "Name": name, "Age": age, "Phone": phone, "Addr": addr, 
                "Diagnosis": f_diag, "Rx": f_rx, "Date": datetime.now().strftime("%Y-%m-%d"),
                "BP": bp, "Weight": wt, "Temp": tmp
            })
            
            # PDF Generation
            pdf_txt = f"{CLINIC}\n{DR_NAME}\n{TAGLINE}\n" + "="*25 + \
                      f"\nID: {p_id} | Name: {name}\nAge: {age} | Ph: {phone}\nBP: {bp} | WT: {wt} | T: {tmp}\n" + "-"*25 + \
                      f"\nDIAGNOSIS: {f_diag}\n\nRX PLAN:\n{f_rx}\n" + "="*25
            
            st.download_button(f"📥 Download {fname}", data=create_pdf(pdf_txt), file_name=fname, mime="application/pdf")
            st.success("Record Saved Successfully!")












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
MODELS = ["gemini-2.5-flash", "gemini-2.0-pro", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]

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