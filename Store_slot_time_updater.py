import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Store Slot Updater", layout="wide")

st.title("🏪 Store Slot Time Updater")

# -----------------------------
# FILE UPLOAD (CSV + EXCEL)
# -----------------------------
uploaded_file = st.file_uploader(
    "📂 Upload Excel or CSV File",
    type=["xlsx", "csv"]
)

# -----------------------------
# STORE INPUT
# -----------------------------
store_input = st.text_area(
    "🏪 Enter Store IDs (comma separated)",
    placeholder="Example: 101,102,103"
)

# -----------------------------
# SLOT TIME INPUT
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    slot_start = st.text_input("⏰ Slot Start (hh:mm)", value="09:00")

with col2:
    slot_end = st.text_input("⏰ Slot End (hh:mm)", value="18:00")

# -----------------------------
# DEFAULT OPTIONS
# -----------------------------
st.subheader("⚙️ Default Values")

fill_enddate = st.checkbox("Fill EndDate as 'N/A'", value=True)
fill_servicecc = st.checkbox("Fill ServiceChargeCC as 0", value=True)

# -----------------------------
# PROCESS BUTTON
# -----------------------------
if st.button("🚀 Update File"):

    if uploaded_file is None:
        st.error("Please upload a file first.")
    
    elif not store_input.strip():
        st.error("Please enter store IDs.")
    
    else:
        try:
            # -----------------------------
            # READ FILE
            # -----------------------------
            file_name = uploaded_file.name

            if file_name.endswith(".xlsx"):
                df = pd.read_excel(uploaded_file, dtype=str)

            elif file_name.endswith(".csv"):
                df = pd.read_csv(uploaded_file, dtype=str)

            else:
                st.error("Unsupported file format")
                st.stop()

            df.columns = df.columns.str.strip()

            # -----------------------------
            # PROCESS STORE LIST
            # -----------------------------
            store_list = [s.strip() for s in store_input.split(",")]

            # Existing stores
            existing_stores = set(df['StoreID'].astype(str))

            # Not found stores
            not_found_stores = [s for s in store_list if s not in existing_stores]

            # -----------------------------
            # UPDATE DATA
            # -----------------------------
            mask = df['StoreID'].astype(str).isin(store_list)
            rows_updated = mask.sum()

            df.loc[mask, 'SlotStart'] = slot_start
            df.loc[mask, 'SlotEnd'] = slot_end

            # -----------------------------
            # APPLY DEFAULTS
            # -----------------------------
            if fill_enddate:
                df['EndDate'] = df['EndDate'].replace('', pd.NA).fillna("N/A")

            if fill_servicecc:
                df['ServiceChargeCC'] = df['ServiceChargeCC'].replace('', pd.NA).fillna("0")

            # -----------------------------
            # OUTPUT FILE (same format)
            # -----------------------------
            output = io.BytesIO()

            if file_name.endswith(".xlsx"):
                df.to_excel(output, index=False)
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                output_name = "updated_store_data.xlsx"

            else:
                df.to_csv(output, index=False)
                mime_type = "text/csv"
                output_name = "updated_store_data.csv"

            output.seek(0)

            # -----------------------------
            # SUCCESS MESSAGE
            # -----------------------------
            st.success(f"✅ {rows_updated} rows updated")

            # -----------------------------
            # NOT FOUND STORES
            # -----------------------------
            if not_found_stores:
                st.warning(f"⚠️ Stores not found: {', '.join(not_found_stores)}")

            # -----------------------------
            # DOWNLOAD BUTTON
            # -----------------------------
            st.download_button(
                label="📥 Download Updated File",
                data=output,
                file_name=output_name,
                mime=mime_type
            )

        except Exception as e:
            st.error(f"Error: {str(e)}")
