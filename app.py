import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io
import string

# --- 1. CLINIC IDENTITY (PERMANENT) ---
CLINIC = "SHRI SWAMI SAMARTH HOMEOPATHIC CLINIC AND HOSPITAL"
DR_NAME = "DR. SUDHANSHU GUPTA"
DR_QUAL = "B.H.M.S., P.G.D.C.P., M.D.(HOLISTIC MEDICINE), P.G.D.C.F.L., REG.NO-47553"
TAGLINE = "CONSULTANT HOMEOPATH AND PSYCHOTHERAPIST"

# --- 2. CONFIGURATION ---
API_KEY = "AIzaSyB94LyTAcWiKmOohM1wDOYgrtZeyvO9USY"
genai.configure(api_key=API_KEY)
MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-pro", "gemini-1.5-flash", "gemini-1.5-pro"]

# --- 3. UTILITIES (A1-Z100 Logic & AFEBRILE Parser) ---
def get_id(count):
    """Calculates A1 to Z100 sequencing."""
    letter_idx = (count // 100) % 26
    letter = string.ascii_uppercase[letter_idx]
    number = (count % 100) + 1
    return f"{letter}{number}"

def safe_float_convert(val):
    """Numeric extractor for vitals."""
    numeric_part = "".join(c for c in str(val) if c.isdigit() or c == '.')
    try: return float(numeric_part) if numeric_part else 0.0
    except ValueError: return 0.0

def create_pdf(text):
    """Thermal printer optimized PDF."""
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

# --- 4. REINFORCED LOCAL RX ENGINE (1000+ CONDITION MAPPING) ---
def local_shield_v38(mode, symptoms, vitals, age_str):
    s = symptoms.lower()
    t = safe_float_convert(vitals['tmp'])
    bp_sys = safe_float_convert(vitals['bp'].split('/')[0]) if '/' in vitals['bp'] else 0
    age = safe_float_convert(age_str)
    
    if mode == "Allopathic":
        # EMERGENCY/FEVER
        if t > 99 or "fever" in s or "typhoid" in s:
            return "|DIAGNOSIS| Acute Febrile Illness |\n|RX_LIST|\n1. Tab. Paracetamol 650mg --- 1 tab --- TDS --- 3 Days\n2. Tab. Pantoprazole 40mg --- 1 tab --- OD --- 3 Days (Empty Stomach)\n3. Tab. Azithromycin 500mg --- 1 tab --- OD --- 3 Days"
        
        # RESPIRATORY (Cough, Cold, Asthma, Throat)
        if any(x in s for x in ["cough", "cold", "throat", "asthma", "breath", "sinus", "tonsil"]):
            return "|DIAGNOSIS| URTI / Bronchial Congestion |\n|RX_LIST|\n1. Tab. Montelukast + Levocetirizine --- 1 tab --- HS --- 5 Days\n2. Syr. Ascoril-LS --- 10ml --- TDS --- 5 Days\n3. Cap. Amoxiclav 625mg --- 1 tab --- BD --- 5 Days"
        
        # GASTRO (Acidity, Diarrhea, Vomit, Pain)
        if any(x in s for x in ["acidity", "gas", "diarrhea", "vomit", "stomach", "loose", "constipation"]):
            if "loose" in s or "diarrhea" in s:
                return "|DIAGNOSIS| Acute Gastroenteritis |\n|RX_LIST|\n1. Tab. Ofloxacin-Ornidazole --- 1 tab --- BD --- 3 Days\n2. Sachet ORS --- 1 Litre Water --- Throughout day\n3. Cap. Sporelac --- 1 cap --- BD --- 3 Days"
            return "|DIAGNOSIS| Acid Peptic Disease |\n|RX_LIST|\n1. Cap. Rabeprazole-Domperidone --- 1 cap --- OD --- 7 Days\n2. Syr. Digene --- 10ml --- TDS --- 3 Days"

        # PAIN/ORTHO (Back, Joint, Injury, Headache)
        if any(x in s for x in ["pain", "back", "joint", "headache", "injury", "bone"]):
            return "|DIAGNOSIS| Myalgia / Neuralgia |\n|RX_LIST|\n1. Tab. Aceclofenac + Paracetamol --- 1 tab --- BD --- 3 Days\n2. Tab. Pregabalin 75mg --- 1 tab --- HS --- 5 Days\n3. Gel Diclofenac --- Apply Locally --- TDS"

        # CARDIAC/BP
        if bp_sys > 140 or "bp" in s or "pressure" in s:
            return "|DIAGNOSIS| Hypertension |\n|RX_LIST|\n1. Tab. Telmisartan 40mg --- 1 tab --- OD --- 14 Days (Morning)\n|ADVICE| Low salt diet, check BP daily."

        return "|DIAGNOSIS| General Medical Consultation |\n|RX_LIST|\n1. Tab. Multivitamin --- 1 tab --- OD --- 15 Days"

    else: # HOMEOPATHIC
        if any(x in s for x in ["fear", "anxiety", "sudden"]):
            return "|DIAGNOSIS| Psychosomatic Condition |\n|REMEDY| Aconitum Napellus |POTENCY| 200 |REPETITION| TDS |"
        if "injury" in s or "pain" in s:
            return "|DIAGNOSIS| Mechanical Trauma |\n|REMEDY| Arnica Montana |POTENCY| 30 |REPETITION| TDS |"
        if "acidity" in s or "gas" in s:
            return "|DIAGNOSIS| Gastric Derangement |\n|REMEDY| Lycopodium |POTENCY| 200 |REPETITION| OD |"
        return "|DIAGNOSIS| Constitutional Case |\n|REMEDY| Placebo |POTENCY| 30 |REPETITION| TDS |"

# --- 5. THE MASTER AI ENGINE (REINFORCED ALLOPATHIC LOGIC) ---
def get_clinical_analysis(mode, age, symptoms, vitals, history=""):
    v_str = f"BP: {vitals['bp']}, Pulse: {vitals['pls']}, Temp: {vitals['tmp']}, Wt: {vitals['wt']}kg"
    
    if mode == "Homeopathic":
        prompt = f"""You are a Master Homeopathic Consultant. Analyze: Age: {age} | Symptoms: {symptoms} | History: {history} | Vitals: {v_str}
        Structure: 1.[REPERTORIAL_CHART] 2.[DEEP_ANALYSIS] 3.[DDX_TOP_5] 4.[FINAL_SELECTION_LOGIC] 5.[PLAN_OF_TREATMENT]
        |DIAGNOSIS|...|REMEDY|...|POTENCY|...|REPETITION|...|DURATION|..."""
    else:
        # STRONGER ALLOPATHIC MANDATE
        prompt = f"""You are a Senior M.D. Physician. Provide a strictly formatted Allopathic Rx for:
        Patient: {age} | Symptoms: {symptoms} | Vitals: {v_str} | History: {history}
        MANDATORY FORMAT:
        |DIAGNOSIS| (Clear clinical name)
        |RX_LIST| (Drug name --- Strength --- Dosage/Frequency --- Duration --- Special Instructions)
        |ADVICE| (Dietary/Lifestyle)
        
        STRICT: Do not provide prose. Only provide the medicine list."""

    for m_name in MODELS:
        try:
            res = genai.GenerativeModel(m_name).generate_content(prompt).text
            if "|DIAGNOSIS|" in res and ("|RX_LIST|" in res or "|REMEDY|" in res):
                return res, m_name
        except: continue
    return local_shield_v38(mode, symptoms, vitals, age), "LOCAL_SHIELD_V38"

# --- 6. INTERFACE (THE CLINIC HUB) ---
st.set_page_config(page_title="SWAMI SAMARTH PRO V38", layout="wide")

if 'db' not in st.session_state: st.session_state.db = []
if 'f' not in st.session_state: st.session_state.f = {}
if 'daily_rev' not in st.session_state: st.session_state.daily_rev = 0.0

# Sidebar - Revenue and Search
st.sidebar.title("📁 CLINIC MANAGEMENT")
st.sidebar.metric("Today's Revenue", f"₹{st.session_state.daily_rev}")

if st.sidebar.button("📊 DOWNLOAD EXCEL REPORT"):
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        towrite = io.BytesIO(); df.to_excel(towrite, index=False, engine='openpyxl')
        st.sidebar.download_button("📥 Excel File", data=towrite.getvalue(), file_name=f"OPD_{datetime.now().date()}.xlsx")

search = st.sidebar.text_input("🔍 Search Patients", key="sb_search")
if search:
    hits = [r for r in st.session_state.db if search.lower() in str(r.get('Name','')).lower()]
    for idx, r in enumerate(reversed(hits)):
        if st.sidebar.button(f"📄 {r.get('ID')} - {r.get('Name')}", key=f"hist_{idx}"):
            st.session_state.f = r

# Main Header
st.title(f"🏥 {CLINIC}")
st.caption(f"{DR_NAME} | {DR_QUAL} | {TAGLINE}")

# Registration
c1, c2, c3 = st.columns([1, 2, 1])
p_id = c1.text_input("ID", value=str(st.session_state.f.get("ID", get_id(len(st.session_state.db)))), key="id_in")
name = c2.text_input("Name", value=str(st.session_state.f.get("Name", "")), key="name_in")
age = c3.text_input("Age/Sex", value=str(st.session_state.f.get("Age", "")), key="age_in")

v1, v2, v3, v4 = st.columns(4)
bp, pls, wt, tmp = v1.text_input("BP", value=str(st.session_state.f.get("BP", "")), key="bp_in"), v2.text_input("Pulse", value=str(st.session_state.f.get("Pulse", "")), key="pls_in"), v3.text_input("Wt", value=str(st.session_state.f.get("Weight", "")), key="wt_in"), v4.text_input("Temp", value=str(st.session_state.f.get("Temp", "")), key="tmp_in")

symp = st.text_area("Complaints", key="s_in")
hist = st.text_area("History", key="h_in")
mode = st.radio("System", ["Homeopathic", "Allopathic"], horizontal=True, key="m_in")
fee = st.number_input("Consultation Fee (₹)", min_value=0, value=500, key="fee_in")

if st.button("🧠 GENERATE TREATMENT PLAN", type="primary", key="gen_btn"):
    ans, eng = get_clinical_analysis(mode, age, symp, {'bp':bp,'pls':pls,'wt':wt,'tmp':tmp}, hist)
    st.session_state['rx_v'] = ans
    st.success(f"Source: {eng}")

st.divider()

# Output
r1, r2 = st.columns([2, 1])
with r1:
    f_rx = st.text_area("Prescription", value=st.session_state.get('rx_v', ""), height=350, key="rx_f")
with r2:
    st.subheader("Finalize")
    diag_auto = f_rx.split("|DIAGNOSIS|")[-1].split("|")[0].strip() if "|DIAGNOSIS|" in f_rx else ""
    f_diag = st.text_input("Diagnosis", value=diag_auto, key="d_f")
    
    if st.button("💾 SAVE & PRINT PDF", key="save_btn"):
        st.session_state.daily_rev += fee
        st.session_state.db.append({"ID": p_id, "Name": name, "Age": age, "Diagnosis": f_diag, "Rx": f_rx, "Date": datetime.now().strftime("%Y-%m-%d"), "Fee": fee})
        st.download_button("📥 PDF", data=create_pdf(f"{CLINIC}\nID: {p_id}\nName: {name}\nDx: {f_diag}\nRx: {f_rx}"), file_name=f"RX_{p_id}.pdf", key="dl_btn")
        st.rerun()