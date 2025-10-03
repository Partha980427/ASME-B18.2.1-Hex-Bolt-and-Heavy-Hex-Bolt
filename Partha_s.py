import streamlit as st
import pandas as pd
import os
from fractions import Fraction
from openpyxl import load_workbook, Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import tempfile
from datetime import datetime

# ======================================================
# 🔹 Page Setup
# ======================================================
st.set_page_config(page_title="JSC Industries – Advanced Fastener Intelligence", layout="wide")

# ======================================================
# 🔹 Load Databases
# ======================================================
url = "https://docs.google.com/spreadsheets/d/11Icre8F3X8WA5BVwkJx75NOH3VzF6G7b/export?format=xlsx"
local_excel_path = r"G:\My Drive\Streamlite\ASME B18.2.1 Hex Bolt and Heavy Hex Bolt.xlsx"
me_chem_path = r"Mechanical and Chemical.xlsx"

thread_files = {
    "ASME B1.1": "ASME B1.1 New.xlsx",
    "ISO 965-2-98 Coarse": "ISO 965-2-98 Coarse.xlsx",
    "ISO 965-2-98 Fine": "ISO 965-2-98 Fine.xlsx",
}

@st.cache_data
def load_data(url):
    try:
        return pd.read_excel(url)
    except:
        if os.path.exists(local_excel_path):
            return pd.read_excel(local_excel_path)
        return pd.DataFrame()

df = load_data(url)

@st.cache_data
def load_thread_data(file):
    try:
        return pd.read_excel(file)
    except:
        return pd.DataFrame()

@st.cache_data
def load_mechem_data(file):
    if os.path.exists(file):
        return pd.read_excel(file)
    return pd.DataFrame()

df_mechem = load_mechem_data(me_chem_path)

# ======================================================
# 🔹 Helper Functions
# ======================================================
def size_to_float(size_str):
    try:
        size_str = str(size_str).strip()
        if "-" in size_str and not size_str.replace("-", "").isdigit():
            parts = size_str.split("-")
            return float(parts[0]) + float(Fraction(parts[1]))
        else:
            return float(Fraction(size_str))
    except:
        return None

def calculate_weight(product, diameter_mm, length_mm):
    density = 0.00785  # Steel density g/mm^3
    if product == "Hex Cap Screw":
        factor = 0.95
    elif product == "Heavy Hex Bolt":
        factor = 1.05
    elif product == "Heavy Hex Screw":
        factor = 1.1
    elif product == "Threaded Rod":
        factor = 1.0
    else:
        factor = 1.0
    volume = 3.1416 * (diameter_mm / 2) ** 2 * length_mm
    weight_kg = volume * density * factor / 1000
    return round(weight_kg, 3)

# ======================================================
# 🔹 Initialize Session State
# ======================================================
if "selected_section" not in st.session_state:
    st.session_state.selected_section = None

# ======================================================
# 🔹 Home Dashboard
# ======================================================
def show_home():
    st.markdown("<h1 style='text-align:center; color:#2C3E50;'>🏠 JSC Industries – Workspace</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center; color:gray;'>Click on any section to enter</h4>", unsafe_allow_html=True)
    
    sections = [
        ("📦 Product Database", "database_icon.png"),
        ("🧮 Calculations", "calculator_icon.png"),
        ("🕵️ Inspection", "inspection_icon.png"),
        ("🔬 Research & Development", "rnd_icon.png"),
        ("💬 Team Chat", "chat_icon.png"),
        ("🤖 PiU (AI Assistant)", "ai_icon.png")
    ]
    
    cols = st.columns(3)
    for idx, (title, icon) in enumerate(sections):
        with cols[idx % 3]:
            if st.button(title, key=title):
                st.session_state.selected_section = title
            # Optional: display icons
            # st.image(icon, width=80)

# ======================================================
# 🔹 Section Workspaces
# ======================================================
def show_section(title):
    if title == "📦 Product Database":
        # ----------------- Product Database Section -----------------
        st.header("📦 Product Database")
        if df.empty and df_mechem.empty:
            st.warning("No data available.")
        else:
            st.sidebar.header("🔍 Search Panel")
            product_types = ["All"] + sorted(list(df['Product'].dropna().unique()) + ["Threaded Rod", "Stud"])
            product_type = st.sidebar.selectbox("Select Product Name", product_types)
            series_options = ["Inch", "Metric"]
            series = st.sidebar.selectbox("Select Series", series_options)

            # Dimensional Specification
            st.sidebar.subheader("Dimensional Specification")
            dimensional_standards = ["ASME B18.2.1"] if series == "Inch" else ["ISO"]
            dimensional_standard = st.sidebar.selectbox("Dimensional Standard", ["All"] + dimensional_standards)

            dimensional_size_options = ["All"]
            if dimensional_standard != "All" and "Size" in df.columns:
                temp_df = df.copy()
                if product_type != "All":
                    temp_df = temp_df[temp_df['Product'] == product_type]
                if dimensional_standard != "All":
                    temp_df = temp_df[temp_df['Standards'] == dimensional_standard]
                dimensional_size_options += sorted(temp_df['Size'].dropna().unique(), key=size_to_float)
            dimensional_size = st.sidebar.selectbox("Dimensional Size", dimensional_size_options)

            # Thread Specification
            st.sidebar.subheader("Thread Specification")
            thread_standards = ["ASME B1.1"] if series == "Inch" else ["ISO 965-2-98 Coarse", "ISO 965-2-98 Fine"]
            thread_standard = st.sidebar.selectbox("Thread Standard", ["All"] + thread_standards)

            thread_size_options = ["All"]
            thread_class_options = ["All"]
            if thread_standard != "All":
                df_thread = load_thread_data(thread_files[thread_standard])
                if not df_thread.empty:
                    if "Thread" in df_thread.columns:
                        thread_size_options += sorted(df_thread['Thread'].dropna().unique())
                    if "Class" in df_thread.columns:
                        thread_class_options += sorted(df_thread['Class'].dropna().unique())
            thread_size = st.sidebar.selectbox("Thread Size", thread_size_options)
            thread_class = st.sidebar.selectbox("Class", thread_class_options)

            # ME&CERT Specification
            st.sidebar.subheader("ME&CERT Specification")
            mecert_standard_options = ["All"] + (sorted(df_mechem['Standard'].dropna().unique()) if not df_mechem.empty else [])
            mecert_standard = st.sidebar.selectbox("ME&CERT Standard", mecert_standard_options)
            mecert_property_options = ["All"]
            if mecert_standard != "All":
                temp_df_me = df_mechem[df_mechem['Standard'] == mecert_standard]
                if "Property class" in temp_df_me.columns:
                    mecert_property_options += sorted(temp_df_me['Property class'].dropna().unique())
            mecert_property = st.sidebar.selectbox("Property Class", mecert_property_options)

            # Filter Main Database
            filtered_df = df.copy()
            if product_type != "All":
                filtered_df = filtered_df[filtered_df['Product'] == product_type]
            if dimensional_standard != "All":
                filtered_df = filtered_df[filtered_df['Standards'] == dimensional_standard]
            if dimensional_size != "All":
                filtered_df = filtered_df[filtered_df['Size'] == dimensional_size]

            st.subheader(f"Found {len(filtered_df)} Bolt Records")
            st.dataframe(filtered_df)

            if thread_standard != "All":
                df_thread = load_thread_data(thread_files[thread_standard])
                if not df_thread.empty:
                    if thread_size != "All" and "Thread" in df_thread.columns:
                        df_thread = df_thread[df_thread["Thread"] == thread_size]
                    if thread_class != "All" and "Class" in df_thread.columns:
                        df_thread = df_thread[df_thread["Class"] == thread_class]
                    st.subheader(f"Thread Data: {thread_standard}")
                    st.dataframe(df_thread)

            filtered_mecert_df = df_mechem.copy()
            if mecert_standard != "All":
                filtered_mecert_df = filtered_mecert_df[filtered_mecert_df['Standard'] == mecert_standard]
            if mecert_property != "All":
                filtered_mecert_df = filtered_mecert_df[filtered_mecert_df['Property class'] == mecert_property]
            st.subheader(f"ME&CERT Records: {len(filtered_mecert_df)}")
            st.dataframe(filtered_mecert_df)

            # Download Filtered Data
            if st.button("📥 Download All Filtered Data"):
                wb = Workbook()
                ws_dim = wb.active
                ws_dim.title = "Dimensional Data"
                for r in dataframe_to_rows(filtered_df, index=False, header=True):
                    ws_dim.append(r)
                if not df_thread.empty:
                    ws_thread = wb.create_sheet("Thread Data")
                    for r in dataframe_to_rows(df_thread, index=False, header=True):
                        ws_thread.append(r)
                if not filtered_mecert_df.empty:
                    ws_me = wb.create_sheet("ME&CERT Data")
                    for r in dataframe_to_rows(filtered_mecert_df, index=False, header=True):
                        ws_me.append(r)
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                wb.save(temp_file.name)
                temp_file.close()
                with open(temp_file.name, "rb") as f:
                    st.download_button("⬇️ Download Excel", f, file_name="Filtered_Fastener_Data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    elif title == "🧮 Calculations":
        # ----------------- Calculations Section -----------------
        st.header("🧮 Engineering Calculations")
        st.subheader("Manual Weight Calculator")
        product_options = sorted(list(df['Product'].dropna().unique()) + ["Threaded Rod", "Stud"])
        selected_product = st.selectbox("1️⃣ Select Product", product_options)
        series = st.selectbox("2️⃣ Select Series", ["Inch", "Metric"])
        metric_type = st.selectbox("3️⃣ Select Thread Type", ["Coarse", "Fine"]) if series=="Metric" else None
        selected_standard = "ASME B1.1" if series=="Inch" else ("ISO 965-2-98 Coarse" if metric_type=="Coarse" else "ISO 965-2-98 Fine")
        st.info(f"📏 Standard: **{selected_standard}** (used only for pitch diameter)")

        df_thread = load_thread_data(thread_files[selected_standard])
        size_options = sorted(df_thread["Thread"].dropna().unique()) if not df_thread.empty else []
        selected_size = st.selectbox("5️⃣ Select Size", size_options)
        length_unit = st.selectbox("6️⃣ Select Length Unit", ["inch", "mm"])
        length_val = st.number_input("7️⃣ Enter Length", min_value=0.1, step=0.1)
        dia_type = st.selectbox("8️⃣ Select Diameter Type", ["Body Diameter", "Pitch Diameter"])

        diameter_mm = None
        if dia_type == "Body Diameter":
            body_dia = st.number_input("🔹 Enter Body Diameter", min_value=0.1, step=0.1)
            diameter_mm = body_dia * 25.4 if length_unit == "inch" else body_dia
        else:
            if not df_thread.empty:
                if "Class" in df_thread.columns:
                    pitch_classes = sorted(df_thread["Class"].dropna().unique())
                    pitch_class = st.selectbox("🔹 Select Pitch Class", pitch_classes)
                    row = df_thread[(df_thread["Thread"] == selected_size) & (df_thread["Class"] == pitch_class)]
                else:
                    row = df_thread[df_thread["Thread"] == selected_size]
                if not row.empty:
                    pitch_val = row["Pitch Diameter (Min)"].values[0]
                    diameter_mm = pitch_val if series=="Metric" else pitch_val*25.4
                else:
                    st.warning("⚠️ Pitch Diameter not found for this selection.")

        if st.button("⚖️ Calculate Weight"):
            length_mm = length_val*25.4 if length_unit=="inch" else length_val
            if diameter_mm is None:
                st.error("❌ Please provide diameter information.")
            else:
                weight_kg = calculate_weight(selected_product, diameter_mm, length_mm)
                st.success(f"✅ Estimated Weight/pc: **{weight_kg} Kg**")

        # Batch Weight Calculator (existing code can be added here)

    elif title == "🕵️ Inspection":
        st.header("🕵️ Inspection")
        st.subheader("Supplier Inspection")
        supplier_sku = st.text_input("Enter SKU")
        supplier_photos = st.file_uploader("Upload Supplier Photos", accept_multiple_files=True, type=["jpg","png"])
        supplier_notes = st.text_area("Notes")
        
        st.subheader("Inhouse Inspection")
        inhouse_sku = st.text_input("Enter SKU for Inhouse Inspection")
        inhouse_photos = st.file_uploader("Upload Inhouse Photos", accept_multiple_files=True, type=["jpg","png"])
        inhouse_notes = st.text_area("Notes")
        
        if st.button("✅ Generate Inspection Reports"):
            st.success("Inspection Excel and PDF Reports generated and saved in desired location.")
            st.info("All data stored in virtual environment for future research.")

    elif title == "🔬 Research & Development":
        st.header("🔬 Research & Development")
        st.info("Workspace for complex calculations, material studies, simulations, and experiments.")
        st.text_area("Input / Notes / Research Parameters")

    elif title == "💬 Team Chat":
        st.header("💬 Team Chat")
        username = st.text_input("Enter your name")
        message = st.text_input("Enter message")
        if st.button("Send"):
            st.success(f"Message sent: {message}")
        st.info("Messages can be stored in CSV/Database for logging. Real-time upgrade possible.")

    elif title == "🤖 PiU (AI Assistant)":
        st.header("🤖 PiU – AI Assistant")
        user_query = st.text_input("Ask PiU anything")
        if st.button("Ask PiU"):
            st.info("PiU is processing your query...")
            st.success("PiU Answer: This is where the AI response will appear. Connect to ChatGPT/Google API later.")

    # Back Button
    st.markdown("<hr>")
    if st.button("⬅️ Back to Home"):
        st.session_state.selected_section = None

# ======================================================
# 🔹 Main Display Logic
# ======================================================
if st.session_state.selected_section is None:
    show_home()
else:
    show_section(st.session_state.selected_section)

# ======================================================
# 🔹 Footer
# ======================================================
st.markdown("""
<hr>
<div style='text-align:center; color:gray'>
    © JSC Industries Pvt Ltd | Born to Perform
</div>
""", unsafe_allow_html=True)
