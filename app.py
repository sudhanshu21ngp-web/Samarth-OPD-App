import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io
import string

# --- 1. CLINIC IDENTITY (UNCHANGED) ---
CLINIC = "SHRI SWAMI SAMARTH HOMEOPATHIC CLINIC AND HOSPITAL"
DR_NAME = "DR. SUDHANSHU GUPTA"
DR_QUAL = "B.H.M.S., P.G.D.C.P., M.D.(HOLISTIC MEDICINE), P.G.D.C.F.L., REG.NO-47553"
TAGLINE = "CONSULTANT HOMEOPATH AND PSYCHOTHERAPIST"

# --- 2. CONFIGURATION ---
API_KEY = "AIzaSyAwnRH3xrb6Oa5s6fOKgeCS5GxK9MT1fW4"
genai.configure(api_key=API_KEY)
MODELS = ["gemini-2.5-flash", "gemini-2.0-pro", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]

# --- 3. UTILITIES (A1-Z100 & AFEBRILE LOGIC) ---
def get_id(count):
    letter_idx = (count // 100) % 26
    letter = string.ascii_uppercase[letter_idx]
    number = (count % 100) + 1
    return f"{letter}{number}"

def safe_float_convert(val):
    numeric_part = "".join(c for c in str(val) if c.isdigit() or c == '.')
    try: return float(numeric_part) if numeric_part else 0.0
    except ValueError: return 0.0

def create_pdf(text):
    buf = io.BytesIO()
    p = canvas.Canvas(buf, pagesize=(80*mm, 297*mm))
    p.setFont("Helvetica-Bold", 10)
    p.drawString(5*mm, 290*mm, "PRESCRIPTION")
    p.setFont("Helvetica", 8)
    y = 282*mm
    for line in text.split('\n'):
        if y < 15*mm: p.showPage(); y = 285*mm
        p.drawString(5*mm, y, line); y -= 4.5*mm
    p.showPage(); p.save()
    return buf.getvalue()

# --- 4. THE MASTER AI ENGINE (REINFORCED ALLOPATHIC & MASTER HOMEOPATHIC) ---
def get_clinical_analysis(mode, age, symptoms, vitals, history=""):
    v_str = f"BP: {vitals['bp']}, Pulse: {vitals['pls']}, Temp: {vitals['tmp']}, Wt: {vitals['wt']}kg"
    
    if mode == "Homeopathic":
        prompt = f"""You are a Master Homeopathic Consultant. Analyze: Age: {age} | Symptoms: {symptoms} | History: {history} | Vitals: {v_str}
        Structure: 1.[REPERTORIAL_CHART] 2.[DEEP_ANALYSIS] 3.[DDX_TOP_5] 4.[FINAL_SELECTION_LOGIC] 5.[PLAN_OF_TREATMENT]
        |DIAGNOSIS| (Result) |REMEDY| (Simillimum) |POTENCY| (Power) |REPETITION| (Schedule) |DURATION| (Time) |"""
    else:
        prompt = f"""You are a Senior M.D. Physician. Strictly provide Allopathic Rx for:
        Patient: {age} | Symptoms: {symptoms} | Vitals: {v_str} | History: {history}
        FORMAT:
        |DIAGNOSIS| (Clinical Name)
        |RX_LIST| (Drug --- Dose --- Freq --- Dur)
        |ADVICE| (Diet/Rest)"""

    for m_name in MODELS:
        try:
            res = genai.GenerativeModel(m_name).generate_content(prompt).text
            if "|DIAGNOSIS|" in res: return res, m_name
        except: continue
    return "|DIAGNOSIS| General Consultation |\n|RX_LIST| 1. Multivitamin OD 15 days", "OFFLINE_SHIELD"

# --- 5. INTERFACE ---
st.set_page_config(page_title="SWAMI SAMARTH PRO V39", layout="wide")

if 'db' not in st.session_state: st.session_state.db = []
if 'f' not in st.session_state: st.session_state.f = {}
if 'daily_rev' not in st.session_state: st.session_state.daily_rev = 0.0

# Sidebar - Administration
st.sidebar.title("📁 CLINIC ADMIN")
st.sidebar.metric("Today's Revenue", f"₹{st.session_state.daily_rev}")

# Excel Export
if st.sidebar.button("📊 EXPORT DAY REPORT", key="excel_btn"):
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False, engine='openpyxl')
        st.sidebar.download_button("📥 Click to Download", data=towrite.getvalue(), file_name=f"Clinic_Report_{datetime.now().date()}.xlsx")

st.sidebar.markdown("---")
st.sidebar.subheader("Patient History & Alerts")
search = st.sidebar.text_input("🔍 Search Name/ID", key="sb_search")

# Patient Search and Follow-up Logic
if st.session_state.db:
    for idx, r in enumerate(reversed(st.session_state.db)):
        last_date = datetime.strptime(r['Date'], "%Y-%m-%d")
        needs_followup = (datetime.now() - last_date).days > 15
        label = f"{'🔴' if needs_followup else '📄'} {r['ID']} - {r['Name']}"
        
        if search.lower() in r['Name'].lower() or search.lower() in r['ID'].lower():
            if st.sidebar.button(label, key=f"hist_{idx}"):
                st.session_state.f = r

# Main Body
st.title(f"🏥 {CLINIC}")
st.caption(f"{DR_NAME} | {DR_QUAL} | {TAGLINE}")

# Registration
c1, c2, c3 = st.columns([1, 2, 1])
p_id = c1.text_input("ID", value=str(st.session_state.f.get("ID", get_id(len(st.session_state.db)))), key="id_in")
name = c2.text_input("Name", value=str(st.session_state.f.get("Name", "")), key="name_in")
age = c3.text_input("Age/Sex", value=str(st.session_state.f.get("Age", "")), key="age_in")

v1, v2, v3, v4 = st.columns(4)
bp, pls, wt, tmp = v1.text_input("BP", value=str(st.session_state.f.get("BP", "")), key="bp_in"), v2.text_input("Pulse", value=str(st.session_state.f.get("Pulse", "")), key="pls_in"), v3.text_input("Wt", value=str(st.session_state.f.get("Weight", "")), key="wt_in"), v4.text_input("Temp", value=str(st.session_state.f.get("Temp", "")), key="tmp_in")

symp = st.text_area("Chief Complaints", key="s_in")
hist = st.text_area("History", key="h_in")
mode = st.radio("System", ["Homeopathic", "Allopathic"], horizontal=True, key="m_in")
fee = st.number_input("Consultation Fee (₹)", min_value=0, value=500, key="fee_in")

if st.button("🧠 GENERATE TREATMENT PLAN", type="primary", key="gen_btn"):
    ans, eng = get_clinical_analysis(mode, age, symp, {'bp':bp,'pls':pls,'wt':wt,'tmp':tmp}, hist)
    st.session_state['rx_v'] = ans
    st.success(f"Source: {eng}")

st.divider()

# Rx and Fix for SAVE/PRINT
f_rx = st.text_area("Final Prescription", value=st.session_state.get('rx_v', ""), height=350, key="rx_f")
diag_auto = f_rx.split("|DIAGNOSIS|")[-1].split("|")[0].strip() if "|DIAGNOSIS|" in f_rx else ""
f_diag = st.text_input("Clinical Diagnosis", value=diag_auto, key="d_f")

# THE REPAIRED SAVE LOGIC
if st.button("💾 SAVE RECORD TO DATABASE", key="save_db_btn"):
    if name:
        st.session_state.daily_rev += fee
        st.session_state.db.append({
            "ID": p_id, "Name": name, "Age": age, "Diagnosis": f_diag, 
            "Rx": f_rx, "Date": datetime.now().strftime("%Y-%m-%d"), 
            "Fee": fee, "BP": bp, "Weight": wt, "Temp": tmp
        })
        st.success(f"✅ Patient {name} saved. Total Revenue updated.")
    else:
        st.error("Please enter a name before saving.")

# PRINT BUTTON (Requires separate click for download due to Streamlit architecture)
if st.session_state.get('db'):
    pdf_content = f"{CLINIC}\n{DR_NAME}\n{TAGLINE}\n" + "="*20 + f"\nID: {p_id} | Name: {name}\nAge: {age} | Date: {datetime.now().date()}\n" + "-"*20 + f"\nDx: {f_diag}\n\nRx:\n{f_rx}\n" + "="*20
    st.download_button("📥 DOWNLOAD & PRINT PDF", data=create_pdf(pdf_content), file_name=f"RX_{p_id}.pdf", key="print_pdf_btn")