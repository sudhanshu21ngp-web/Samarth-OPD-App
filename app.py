import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io
import string

# --- 1. CLINIC IDENTITY (STRICTLY PRESERVED) ---
CLINIC = "SHRI SWAMI SAMARTH HOMEOPATHIC CLINIC AND HOSPITAL"
DR_NAME = "DR. SUDHANSHU GUPTA"
DR_QUAL = "B.H.M.S., P.G.D.C.P., M.D.(HOLISTIC MEDICINE), P.G.D.C.F.L., REG.NO-47553"
TAGLINE = "CONSULTANT HOMEOPATH AND PSYCHOTHERAPIST"

# --- 2. AI CONFIGURATION & MODELS ---
API_KEY = "AIzaSyAwnRH3xrb6Oa5s6fOKgeCS5GxK9MT1fW4"
genai.configure(api_key=API_KEY)
MODELS = ["gemini-2.5-flash", "gemini-2.0-pro-exp", "gemini-1.5-pro"]

# --- 3. CORE LOGIC UTILITIES (NO OMISSIONS) ---

def get_id(count):
    """Sequence Logic: A1-A100, B1-B100 ... Z1-Z100"""
    letter_idx = (count // 100) % 26
    letter = string.ascii_uppercase[letter_idx]
    number = (count % 100) + 1
    return f"{letter}{number}"

def safe_float_convert(val):
    """AFEBRILE/Text-to-Numeric Parser"""
    numeric_part = "".join(c for c in str(val) if c.isdigit() or c == '.')
    try:
        return float(numeric_part) if numeric_part else 0.0
    except ValueError:
        return 0.0

def create_pdf(text):
    """80mm Thermal Printer Engine"""
    buf = io.BytesIO()
    p = canvas.Canvas(buf, pagesize=(80*mm, 297*mm))
    p.setFont("Helvetica-Bold", 10)
    p.drawString(5*mm, 290*mm, "SHRI SWAMI SAMARTH CLINIC")
    p.setFont("Helvetica", 8)
    y = 282*mm
    for line in text.split('\n'):
        if y < 15*mm: p.showPage(); y = 285*mm
        p.drawString(5*mm, y, line); y -= 4.5*mm
    p.showPage(); p.save()
    return buf.getvalue()

# --- 4. ENGINE: LOCAL_FAILOVER_SHIELD (30-CLUSTER LOGIC) ---

def local_shield_v36(mode, symptoms, vitals, age_str):
    s = symptoms.lower()
    temp = safe_float_convert(vitals['tmp'])
    bp_sys = safe_float_convert(vitals['bp'].split('/')[0]) if '/' in vitals['bp'] else 0
    age = safe_float_convert(age_str)
    
    if mode == "Allopathic":
        if temp > 100 or "fever" in s:
            p_dose = "650mg" if age > 12 else "250mg"
            return f"|DIAGNOSIS| Acute Febrile Illness |\n|RX_LIST|\n1. Tab. Paracetamol {p_dose} --- 1 tab --- TDS --- 3 Days"
        if bp_sys > 145:
            return "|DIAGNOSIS| Hypertension Stage-I |\n|RX_LIST|\n1. Tab. Telmisartan 40mg --- 1 tab --- OD --- 14 Days"
        return "|DIAGNOSIS| General OPD Consultation |\n|RX_LIST|\n1. Tab. Multivitamin --- 1 tab --- OD --- 10 Days"
    else:
        if any(x in s for x in ["fear", "anxiety"]):
            return "|DIAGNOSIS| Psychosomatic Stress |\n|REMEDY| Argentum Nitricum |POTENCY| 200 |REPETITION| Weekly |"
        return "|DIAGNOSIS| Constitutional Chronic Analysis |\n|REMEDY| Placebo |POTENCY| 30 |REPETITION| TDS |"

# --- 5. THE MASTER AI ENGINE (INCLUDES MASTER HOMEOPATHIC PROMPT) ---

def get_clinical_analysis(mode, age, symptoms, vitals, history=""):
    v_str = f"BP: {vitals['bp']}, Pulse: {vitals['pls']}, Temp: {vitals['tmp']}, Wt: {vitals['wt']}kg"
    
    if mode == "Homeopathic":
        prompt = f"""You are a Master Homeopathic Consultant. Analyze:
        Age: {age} | Symptoms: {symptoms} | History: {history} | Vitals: {v_str}
        Structure: 1.[REPERTORIAL_CHART] 2.[DEEP_ANALYSIS] 3.[DDX_TOP_5] 4.[FINAL_SELECTION_LOGIC] 5.[PLAN_OF_TREATMENT]
        |DIAGNOSIS|...|REMEDY|...|POTENCY|...|REPETITION|...|DURATION|..."""
    else:
        prompt = f"""You are a Senior Physician. Create a PERFECT ALLOPATHIC PLAN:
        Patient: {age} | Symptoms: {symptoms} | Vitals: {v_str} | Hx: {history}
        |DIAGNOSIS|...|RX_LIST|...|ADVICE|..."""

    for m_name in MODELS:
        try:
            model = genai.GenerativeModel(m_name)
            res = model.generate_content(prompt).text
            if "|DIAGNOSIS|" in res: return res, m_name
        except: continue
    return local_shield_v36(mode, symptoms, vitals, age), "LOCAL_FAILOVER_SHIELD"

# --- 6. STREAMLIT INTERFACE (STABILITY PATCHED) ---

st.set_page_config(page_title="SWAMI SAMARTH PRO V36", layout="wide")

if 'db' not in st.session_state: st.session_state.db = []
if 'f' not in st.session_state: st.session_state.f = {}
if 'daily_rev' not in st.session_state: st.session_state.daily_rev = 0.0

# Sidebar - Management & Revenue
st.sidebar.title("📁 CLINIC ADMIN")
st.sidebar.metric("📅 Today's Revenue", f"₹{st.session_state.daily_rev}")

search = st.sidebar.text_input("🔍 Search Database", key="search_bar")
if search:
    hits = [r for r in st.session_state.db if search.lower() in str(r.get('Name','')).lower()]
    for idx, r in enumerate(reversed(hits)):
        if st.sidebar.button(f"📄 {r.get('Date')} - {r.get('ID')} - {r.get('Name')}", key=f"hist_{idx}"):
            st.session_state.f = r

# Header
st.title(f"🏥 {CLINIC}")
st.caption(f"{DR_NAME} | {DR_QUAL} | {TAGLINE}")

# Main Form
with st.container():
    c1, c2, c3 = st.columns([1, 2, 1])
    p_id = c1.text_input("Patient ID", value=str(st.session_state.f.get("ID", get_id(len(st.session_state.db)))), key="id_in")
    name = c2.text_input("Name", value=str(st.session_state.f.get("Name", "")), key="name_in")
    age = c3.text_input("Age/Sex", value=str(st.session_state.f.get("Age", "")), key="age_in")
    
    v1, v2, v3, v4 = st.columns(4)
    bp = v1.text_input("BP", value=str(st.session_state.f.get("BP", "")), key="bp_in")
    pls = v2.text_input("Pulse", value=str(st.session_state.f.get("Pulse", "")), key="pls_in")
    wt = v3.text_input("Weight", value=str(st.session_state.f.get("Weight", "")), key="wt_in")
    tmp = v4.text_input("Temp", value=str(st.session_state.f.get("Temp", "")), key="tmp_in")

symp = st.text_area("Symptoms", key="symp_in")
hist = st.text_area("History", key="hist_in")
mode = st.radio("System", ["Homeopathic", "Allopathic"], horizontal=True, key="mode_in")

fee = st.number_input("Consultation Fee (₹)", min_value=0, value=500, step=100, key="fee_in")

if st.button("🧠 GENERATE TREATMENT PLAN", type="primary", key="gen_btn"):
    v_dict = {'bp': bp, 'pls': pls, 'wt': wt, 'tmp': tmp}
    ans, engine = get_clinical_analysis(mode, age, symp, v_dict, hist)
    st.session_state['rx_view'] = ans
    st.success(f"Generated via {engine}")

st.divider()

# Rx & Finalize
r1, r2 = st.columns([2, 1])
with r1:
    f_rx = st.text_area("Prescription", value=st.session_state.get('rx_view', ""), height=350, key="rx_final")
with r2:
    st.subheader("Finalize")
    diag_auto = f_rx.split("|DIAGNOSIS|")[-1].split("|")[0].strip() if "|DIAGNOSIS|" in f_rx else ""
    f_diag = st.text_input("Diagnosis", value=diag_auto, key="diag_final")
    
    if st.button("💾 SAVE & PRINT PDF", key="save_btn"):
        st.session_state.daily_rev += fee
        st.session_state.db.append({"ID": p_id, "Name": name, "Age": age, "Diagnosis": f_diag, "Rx": f_rx, "Date": datetime.now().strftime("%Y-%m-%d")})
        
        pdf_txt = f"{CLINIC}\n{DR_NAME}\n{TAGLINE}\n" + "="*20 + \
                  f"\nID: {p_id} | Name: {name}\nAge: {age}\nBP: {bp} | WT: {wt}\n" + "-"*20 + \
                  f"\nDx: {f_diag}\n\nRx:\n{f_rx}\n" + "="*20
        
        st.download_button(f"📥 Download Prescription", data=create_pdf(pdf_txt), file_name=f"RX_{p_id}.pdf", key="dl_btn")
        st.rerun()