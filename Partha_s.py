import streamlit as st
import pandas as pd
import os
from fractions import Fraction
from openpyxl import load_workbook, Workbook
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
    return round(weight_kg, 4)

def convert_to_mm(length_val, unit):
    """Convert any supported unit to mm"""
    unit = unit.lower()
    if unit == "mm":
        return length_val
    elif unit == "inch":
        return length_val * 25.4
    elif unit == "meter":
        return length_val * 1000
    elif unit == "ft":
        return length_val * 304.8
    else:
        return length_val

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

# ======================================================
# 🔹 Section Workspaces
# ======================================================
def show_section(title):
    if title == "📦 Product Database":
        st.header("📦 Product Database")
        pass  # Keep existing code

    elif title == "🧮 Calculations":
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
        length_unit = st.selectbox("6️⃣ Select Length Unit", ["mm","inch","meter","ft"])  # Added ft
        length_val = st.number_input("7️⃣ Enter Length", min_value=0.1, step=0.1)
        dia_type = st.selectbox("8️⃣ Select Diameter Type", ["Body Diameter", "Pitch Diameter"])

        diameter_mm = None
        if dia_type == "Body Diameter":
            body_dia = st.number_input("🔹 Enter Body Diameter", min_value=0.1, step=0.1)
            diameter_mm = convert_to_mm(body_dia, length_unit)
        else:
            if not df_thread.empty:
                row = df_thread[df_thread["Thread"]==selected_size]
                if not row.empty:
                    pitch_val = row["Pitch Diameter (Min)"].values[0]
                    diameter_mm = pitch_val if series=="Metric" else pitch_val*25.4
                else:
                    st.warning("⚠️ Pitch Diameter not found.")

        if st.button("⚖️ Calculate Weight"):
            length_mm = convert_to_mm(length_val, length_unit)  # Always convert to mm internally
            if diameter_mm is None:
                st.error("❌ Please provide diameter information.")
            else:
                weight_kg = calculate_weight(selected_product, diameter_mm, length_mm)
                st.success(f"✅ Estimated Weight/pc: **{weight_kg} Kg**")

        # ======================================================
        # 🔹 Batch Weight Calculator
        # ======================================================
        st.subheader("📊 Batch Weight Calculator")
        batch_selected_product = st.selectbox("1️⃣ Select Product for Batch", product_options, key="batch_product")
        batch_series = st.selectbox("2️⃣ Select Series", ["Inch", "Metric"], key="batch_series")
        batch_metric_type = st.selectbox("3️⃣ Select Thread Type", ["Coarse", "Fine"], key="batch_metric_type") if batch_series=="Metric" else None
        batch_standard = "ASME B1.1" if batch_series=="Inch" else ("ISO 965-2-98 Coarse" if batch_metric_type=="Coarse" else "ISO 965-2-98 Fine")
        st.info(f"📏 Standard: **{batch_standard}** (used only for pitch diameter)")
        batch_length_unit = st.selectbox("4️⃣ Select Length Unit", ["mm","inch","meter","ft"], key="batch_length_unit")  # Added ft
        uploaded_file_batch = st.file_uploader("5️⃣ Upload Excel/CSV for Batch", type=["xlsx","csv"], key="batch_file")

        if uploaded_file_batch:
            batch_df = pd.read_excel(uploaded_file_batch) if uploaded_file_batch.name.endswith(".xlsx") else pd.read_csv(uploaded_file_batch)
            st.write("📄 Uploaded File Preview:")
            st.dataframe(batch_df.head())

            required_cols = ["Product","Size","Length"]
            if all(col in batch_df.columns for col in required_cols):
                if st.button("⚖️ Calculate Batch Weights", key="calc_batch_weights"):
                    df_thread_batch = load_thread_data(thread_files[batch_standard])
                    df_dim_batch = df[df['Product']==batch_selected_product]

                    weight_col_name = "Weight/pc (Kg)"
                    if weight_col_name not in batch_df.columns:
                        batch_df[weight_col_name] = 0

                    for idx, row in batch_df.iterrows():
                        prod = row["Product"]
                        size_val = row["Size"]
                        length_val = float(row["Length"])
                        unit = row.get("Unit", batch_length_unit).lower()  # Default to selected unit
                        length_mm = convert_to_mm(length_val, unit)  # Always convert to mm

                        diameter_mm = None
                        dim_row = df_dim_batch[df_dim_batch["Size"]==size_val] if not df_dim_batch.empty else pd.DataFrame()
                        if not dim_row.empty and "Body Diameter" in dim_row.columns:
                            diameter_mm = dim_row["Body Diameter"].values[0]

                        thread_row = df_thread_batch[df_thread_batch["Thread"]==size_val] if not df_thread_batch.empty else pd.DataFrame()
                        if not thread_row.empty and "Pitch Diameter (Min)" in thread_row.columns:
                            diameter_mm = thread_row["Pitch Diameter (Min)"].values[0]

                        if diameter_mm is None:
                            try:
                                diameter_mm = float(size_val)
                            except:
                                diameter_mm = 0

                        weight = calculate_weight(prod, diameter_mm, length_mm)
                        batch_df.at[idx, weight_col_name] = weight

                    st.dataframe(batch_df)
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                    batch_df.to_excel(temp_file.name, index=False)
                    with open(temp_file.name,"rb") as f:
                        st.download_button("⬇️ Download Batch Weight Excel", f, 
                                           file_name="Batch_Weight.xlsx",
                                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.error(f"❌ Uploaded file must contain columns: {', '.join(required_cols)}")

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
