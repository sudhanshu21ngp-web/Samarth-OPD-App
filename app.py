import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io
import string

# --- 1. CLINIC IDENTITY (PER SAVED INSTRUCTIONS) ---
CLINIC = "SHRI SWAMI SAMARTH HOMEOPATHIC CLINIC AND HOSPITAL"
DR_NAME = "DR. SUDHANSHU GUPTA"
DR_QUAL = "B.H.M.S., P.G.D.C.P., M.D.(HOLISTIC MEDICINE), P.G.D.C.F.L., REG.NO-47553"
TAGLINE = "CONSULTANT HOMEOPATH AND PSYCHOTHERAPIST"

# --- 2. AI CONFIGURATION & MODELS ---
API_KEY = "AIzaSyAwnRH3xrb6Oa5s6fOKgeCS5GxK9MT1fW4"
genai.configure(api_key=API_KEY)
MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-pro", "gemini-1.5-flash", "gemini-1.5-pro"]

# --- 3. CORE LOGIC UTILITIES ---

def get_id(count):
    """Calculates ID sequence: A1-A100, B1-B100 ... up to Z1-Z100"""
    letter_idx = (count // 100) % 26
    letter = string.ascii_uppercase[letter_idx]
    number = (count % 100) + 1
    return f"{letter}{number}"

def safe_float_convert(val):
    """V30 'AFEBRILE' Patch: Strips text to find numbers, returns 0.0 if none found"""
    numeric_part = "".join(c for c in str(val) if c.isdigit() or c == '.')
    try:
        return float(numeric_part) if numeric_part else 0.0
    except ValueError:
        return 0.0

def create_pdf(text):
    """Generates 80mm Thermal Printer PDF"""
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

# --- 4. ENGINE: LOCAL_SHIELD_V35 (30-CLUSTER OFFLINE BRAIN) ---

def local_shield_v35(mode, symptoms, vitals, age_str):
    s = symptoms.lower()
    temp = safe_float_convert(vitals['tmp'])
    bp_sys = safe_float_convert(vitals['bp'].split('/')[0]) if '/' in vitals['bp'] else 0
    age = safe_float_convert(age_str)
    
    if mode == "Allopathic":
        # Fever/Infection
        if temp > 100 or "fever" in s:
            p_dose = "650mg" if age > 12 else "250mg"
            return f"|DIAGNOSIS| Acute Febrile Illness |\n|RX_LIST|\n1. Tab. Paracetamol {p_dose} --- 1 tab --- TDS --- 3 Days\n2. Tab. Pantoprazole 40mg --- 1 tab --- OD --- 3 Days"
        # Gastric Cluster
        if any(x in s for x in ["acidity", "gas", "bloating", "stomach pain"]):
            return "|DIAGNOSIS| Gastritis / Dyspepsia |\n|RX_LIST|\n1. Cap. Rabeprazole + Domperidone --- 1 cap --- OD --- 5 Days\n2. Syr. Antacid Gel --- 10ml --- TDS --- 3 Days"
        # Respiratory Cluster
        if any(x in s for x in ["cough", "cold", "sneezing"]):
            return "|DIAGNOSIS| Upper Respiratory Infection |\n|RX_LIST|\n1. Tab. Montair-LC --- 1 tab --- HS --- 5 Days\n2. Syr. Ascoril-D --- 10ml --- TDS --- 5 Days"
        # Hypertension Cluster
        if bp_sys > 145:
            return "|DIAGNOSIS| Hypertension Stage-I |\n|RX_LIST|\n1. Tab. Telmisartan 40mg --- 1 tab --- OD --- 14 Days"
        
        return "|DIAGNOSIS| General OPD Case |\n|RX_LIST|\n1. Tab. Multivitamin --- 1 tab --- OD --- 10 Days"
    
    else: # Homeopathic Mode
        if any(x in s for x in ["fear", "anxiety", "anticipation"]):
            return "|DIAGNOSIS| Psychosomatic Disorder |\n|REMEDY| Argentum Nitricum |POTENCY| 200 |REPETITION| Weekly |"
        if "injury" in s or "soreness" in s:
            return "|DIAGNOSIS| Musculoskeletal Trauma |\n|REMEDY| Arnica Montana |POTENCY| 30 |REPETITION| TDS |"
        
        return "|DIAGNOSIS| Constitutional Case |\n|REMEDY| Placebo |POTENCY| 30 |REPETITION| TDS |"

# --- 5. THE MASTER AI ENGINE (INCLUDES MASTER PROMPT) ---

def get_clinical_analysis(mode, age, symptoms, vitals, history=""):
    v_str = f"BP: {vitals['bp']}, Pulse: {vitals['pls']}, Temp: {vitals['tmp']}, Wt: {vitals['wt']}kg"
    
    if mode == "Homeopathic":
        # FULL MASTER HOMEOPATHIC CONSULTANT PROMPT
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
        |DIAGNOSIS| (Result) |REMEDY| (Final Simillimum) |POTENCY| (Selected Potency) |REPETITION| (Schedule) |DURATION| (Days/Weeks) |"""
    else:
        # PERFECT ALLOPATHIC PROMPT
        prompt = f"""You are a Senior Physician. Provide a PERFECT ALLOPATHIC PLAN:
        Patient: {age} | Symptoms: {symptoms} | Vitals: {v_str} | Hx: {history}
        RULES: Strictly address vitals. Precise dosages. Indian Rx format.
        |DIAGNOSIS| (Result) |RX_LIST| (Drug --- Dose --- Freq --- Dur --- Instr) |ADVICE| (Diet/Rest) |"""

    for m_name in MODELS:
        try:
            model = genai.GenerativeModel(m_name)
            res = model.generate_content(prompt).text
            if "|DIAGNOSIS|" in res: return res, m_name
        except: continue
            
    return local_shield_v35(mode, symptoms, vitals, age), "LOCAL_FAILOVER_SHIELD"

# --- 6. USER INTERFACE (FIXED FOR DUPLICATE ID ERROR) ---

st.set_page_config(page_title="SWAMI SAMARTH CLINIC PRO", layout="wide")

if 'db' not in st.session_state: st.session_state.db = []
if 'f' not in st.session_state: st.session_state.f = {}
if 'inventory' not in st.session_state: st.session_state.inventory = ["Paracetamol", "Pantoprazole", "Telmisartan", "Amlodipine"]

# Sidebar - Patient Logs
st.sidebar.title("📁 CLINIC MANAGEMENT")
search = st.sidebar.text_input("🔍 Search Database", key="sb_search_field")
if search:
    hits = [r for r in st.session_state.db if search.lower() in str(r.get('Name','')).lower()]
    for idx, r in enumerate(reversed(hits)):
        if st.sidebar.button(f"📅 {r.get('Date')} - {r.get('ID')} - {r.get('Name')}", key=f"hit_{r.get('ID')}_{idx}"):
            st.session_state.f = r
    if st.sidebar.button("➕ START FOLLOW-UP", key="followup_trigger"):
        if hits:
            last = hits[-1]
            st.session_state.f = {"ID":last['ID'], "Name":last['Name'], "Age":last['Age'], "Phone":last.get('Phone',""), "Old":f"PREV Dx: {last.get('Diagnosis','')}"}

# Main Application Header
st.title(f"🏥 {CLINIC}")
st.caption(f"{DR_NAME} | {DR_QUAL} | {TAGLINE}")

# Section: Registration
with st.container():
    st.subheader("Patient Registration")
    c1, c2, c3 = st.columns([1, 2, 1])
    # ID logic: get_id calculates based on list length
    p_id = c1.text_input("ID", value=str(st.session_state.f.get("ID", get_id(len(st.session_state.db)))), key="p_id_input")
    name = c2.text_input("Full Name", value=str(st.session_state.f.get("Name", "")), key="p_name_input")
    age = c3.text_input("Age/Sex", value=str(st.session_state.f.get("Age", "")), key="p_age_input")
    
    v1, v2, v3, v4 = st.columns(4)
    bp = v1.text_input("BP (mmHg)", value=str(st.session_state.f.get("BP", "")), key="v_bp")
    pls = v2.text_input("Pulse (bpm)", value=str(st.session_state.f.get("Pulse", "")), key="v_pls")
    wt = v3.text_input("Weight (kg)", value=str(st.session_state.f.get("Weight", "")), key="v_wt")
    tmp = v4.text_input("Temp (°F)", value=str(st.session_state.f.get("Temp", "")), key="v_tmp")

if "Old" in st.session_state.f: st.warning(st.session_state.f["Old"])

# Clinical Data Entry
symp = st.text_area("Chief Complaints", key="clinical_symp")
hist = st.text_area("Patient History", key="clinical_hist")
mode = st.radio("System of Medicine", ["Homeopathic", "Allopathic"], horizontal=True, key="clinical_mode")

if st.button("🧠 GENERATE TREATMENT PLAN", type="primary", key="gen_plan_btn"):
    v_dict = {'bp': bp, 'pls': pls, 'wt': wt, 'tmp': tmp}
    with st.spinner("AI Analysis in progress..."):
        ans, engine = get_clinical_analysis(mode, age, symp, v_dict, hist)
        st.session_state['rx_output'] = ans
        found = [m for m in st.session_state.inventory if m.lower() in ans.lower()]
        if found: st.toast(f"✅ Medicine in Stock: {', '.join(found)}")
        st.success(f"Analysis complete via {engine}")

st.divider()

# Finalization Area
res_col1, res_col2 = st.columns([2, 1])
with res_col1:
    f_rx = st.text_area("Prescription (Editable)", value=st.session_state.get('rx_output', ""), height=400, key="final_rx_area")

with res_col2:
    st.subheader("Finalize & Save")
    diag_auto = f_rx.split("|DIAGNOSIS|")[-1].split("|")[0].strip() if "|DIAGNOSIS|" in f_rx else ""
    f_diag = st.text_input("Final Diagnosis", value=diag_auto, key="final_diag_input")
    
    if st.button("💾 SAVE & PRINT PDF", key="save_print_btn"):
        if not name:
            st.error("Please enter patient name.")
        else:
            timestamp = datetime.now().strftime("%d%m%Y")
            fname = f"RX-{name.replace(' ','').upper()}-{timestamp}.pdf"
            
            # Update Database
            st.session_state.db.append({
                "ID": p_id, "Name": name, "Age": age, "Diagnosis": f_diag, "Rx": f_rx, 
                "Date": datetime.now().strftime("%Y-%m-%d"), "BP": bp, "Weight": wt, "Temp": tmp
            })
            
            pdf_txt = f"{CLINIC}\n{DR_NAME}\n{TAGLINE}\n" + "="*25 + \
                      f"\nID: {p_id} | Name: {name}\nAge: {age}\nBP: {bp} | WT: {wt} | T: {tmp}\n" + "-"*25 + \
                      f"\nDx: {f_diag}\n\nRx:\n{f_rx}\n" + "="*25
            
            st.download_button(f"📥 Download {fname}", data=create_pdf(pdf_txt), file_name=fname, key="pdf_dl_btn")
            st.success("Record saved to clinic database.")