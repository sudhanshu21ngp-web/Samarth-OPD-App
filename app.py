import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import io
import string

# --- 1. CONFIG & AI FAILOVER ---
API_KEY = "AIzaSyB94LyTAcWiKmOohM1wDOYgrtZeyvO9USY"
genai.configure(api_key=API_KEY)
MODELS = ["gemini-2.0-pro-exp", "gemini-2.0-flash-exp", "gemini-2.0-pro-exp", "gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"]

def get_ai_analysis(mode, age, symptoms, history=""):
    if mode == "Homeopathic":
        prompt = f"""You are a Master Homeopathic Consultant. Analyze this case with clinical depth:
Age: {age} | Symptoms: {symptoms} | History: {history}

Please provide the response in this structure:
1. [REPERTORIAL_CHART]: A markdown table of rubrics vs top 5 remedies with scores.
2. [DEEP_ANALYSIS]: Miasmatic background (Psora/Sycotic/Syphilitic) and Susceptibility analysis.
3. [DDX_TOP_5]: For the top 5 candidate remedies, provide Guiding, Confirmatory, and Ruling Out Symptoms.
4. [FINAL_SELECTION_LOGIC]: Detailed reasoning for the chosen Simillimum.
5. [PLAN_OF_TREATMENT]: Potency selection logic and auxiliary advice.

FOR SYSTEM AUTO-FILL (CRITICAL):
|DIAGNOSIS| (Clinical Result) |
|REMEDY| (Final Simillimum) |
|POTENCY| (Selected Potency) |
|REPETITION| (Dosage Schedule) |
|DURATION| (Days/Weeks) |"""
    else:
        prompt = f"Allopathic Acute Analysis for Age {age}, Symptoms: {symptoms}. Provide Diagnosis and Rx. |DIAGNOSIS|...|RX_LIST|..."

    for m_name in MODELS:
        try:
            model = genai.GenerativeModel(m_name)
            return model.generate_content(prompt).text, m_name
        except: continue
    return "Failover: Manual Entry Required", "LOCAL_FALLBACK"

# --- 2. PATIENT ID GENERATOR (A1-Z100 Logic) ---
def get_next_id(current_count):
    letter_idx = current_count // 100
    num = (current_count % 100) + 1
    letter = string.ascii_uppercase[letter_idx] if letter_idx < 26 else "Z"
    return f"{letter}{num}"

# --- 3. PDF ENGINE (Thermal Formatting) ---
def create_pdf(content):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=(80*mm, 250*mm))
    p.setFont("Helvetica", 9)
    y = 240 * mm
    for line in content.split('\n'):
        if y < 10*mm: break
        p.drawString(5*mm, y, line)
        y -= 5*mm
    p.showPage()
    p.save()
    return buffer.getvalue()

# --- 4. SESSION & APP SETUP ---
if 'db' not in st.session_state: st.session_state.db = []
if 'form' not in st.session_state: st.session_state.form = {}

CLINIC = "SHRI SWAMI SAMARTH HOMEOPATHIC CLINIC AND HOSPITAL"
DR_NAME = "DR. SUDHANSHU GUPTA"
DR_QUAL = "B.H.M.S., P.G.D.C.P., M.D.(HOLISTIC MEDICINE), P.G.D.C.F.L., REG.NO-47553"
TAGLINE = "CONSULTANT HOMEOPATH AND PSYCHOTHERAPIST"

st.set_page_config(page_title="Clinic Master v12", layout="wide")

# --- 5. SIDEBAR: RECORDS & ANALYTICS ---
st.sidebar.title("🏥 Clinic Management")
search = st.sidebar.text_input("🔍 Search Patient Name")
if search:
    res = [r for r in st.session_state.db if search.lower() in r['Name'].lower()]
    for r in reversed(res):
        if st.sidebar.button(f"📅 {r['Date']} - {r['Name']}", key=f"h_{r['ID']}{r['Date']}"):
            st.session_state.form = r
    if st.sidebar.button("➕ NEW FOLLOW-UP"):
        last = res[-1]
        st.session_state.form = {"ID": last['ID'], "Name": last['Name'], "Age": last['Age'], "History": f"Prev Symptoms: {last['Symptoms']}\nPrev Rx: {last['Rx']}"}

st.sidebar.divider()
if st.session_state.db:
    csv = pd.DataFrame(st.session_state.db).to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("📥 Export Database", csv, "Clinic_Backup.csv")
uploaded = st.sidebar.file_uploader("📤 Import Database", type="csv")
if uploaded: st.session_state.db = pd.read_csv(uploaded).to_dict('records')

# --- 6. MAIN CONSULTATION ---
tab1, tab2 = st.tabs(["📋 Consultation", "📊 Stats"])
with tab1:
    st.title(f"🏥 {CLINIC}")
    st.caption(f"{DR_NAME} | {DR_QUAL}\n{TAGLINE}")
    
    with st.expander("Patient Identity & Vitals", expanded=True):
        c1, c2, c3 = st.columns(3)
        p_id = c1.text_input("Patient ID", value=st.session_state.form.get("ID", get_next_id(len(st.session_state.db))))
        name = c2.text_input("Full Name", value=st.session_state.form.get("Name", ""))
        age = c3.text_input("Age/Sex", value=st.session_state.form.get("Age", ""))
        bp = c1.text_input("BP", value=st.session_state.form.get("BP", "120/80"))
        wt = c2.text_input("Weight (kg)", value=st.session_state.form.get("WT", ""))
        pls = c3.text_input("Pulse", value=st.session_state.form.get("PLS", ""))

    if "History" in st.session_state.form:
        st.warning(st.session_state.form["History"])

    symp = st.text_area("Present Complaints")
    hist = st.text_area("Medical History (for Homeopathy)")
    mode = st.radio("Mode", ["Homeopathic", "Allopathic"], horizontal=True)

    if st.button("🧠 AI CLINICAL ANALYSIS"):
        with st.spinner("Executing Master Consultant Logic..."):
            ans, model_used = get_ai_analysis(mode, age, symp, hist)
            st.session_state['ai_out'] = ans
            st.toast(f"Model: {model_used}")

    st.divider()
    st.markdown("### AI Detailed Reasoning")
    st.write(st.session_state.get('ai_out', ""))
    
    f_rx = st.text_area("Final Prescription (Editable)", value=st.session_state.get('ai_out', ""), height=200)
    f_diag = st.text_input("Diagnosis", value=f_rx.split("|DIAGNOSIS|")[-1].split("|")[0] if "|DIAGNOSIS|" in f_rx else "")

    if st.button("💾 SAVE & GENERATE PDF"):
        timestamp = datetime.now().strftime("%d%m%Y")
        fname = f"RX-{name.replace(' ','').upper()}-{timestamp}.pdf"
        st.session_state.db.append({"ID": p_id, "Name": name, "Age": age, "Symptoms": symp, "Diagnosis": f_diag, "Rx": f_rx, "Date": datetime.now().strftime("%Y-%m-%d"), "BP": bp, "WT": wt, "PLS": pls})
        
        pdf_content = f"{CLINIC}\n{DR_NAME}\n{TAGLINE}\n" + "="*20 + f"\nID: {p_id} | {name}\nAge: {age} | WT: {wt}kg\nBP: {bp} | PLS: {pls}\n" + "-"*20 + f"\nDx: {f_diag}\n\nRx:\n{f_rx}\n" + "="*20
        st.download_button(f"📥 Download {fname}", data=create_pdf(pdf_content), file_name=fname)

with tab2:
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        st.bar_chart(df['Diagnosis'].value_counts())
        st.table(df[['Date', 'ID', 'Name', 'Diagnosis']].tail(10))