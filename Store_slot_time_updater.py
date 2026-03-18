import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Store Slot Updater", layout="wide")

st.title("🏪 Store Slot Time Updater")

# -----------------------------
# FILE UPLOAD
# -----------------------------
uploaded_file = st.file_uploader(
    "📂 Upload Excel or CSV File",
    type=["xlsx", "csv"]
)

# -----------------------------
# NUMBER OF RULES
# -----------------------------
st.subheader("⚙️ Configure Slot Rules")

num_rules = st.number_input("➕ Number of Rules", min_value=1, max_value=10, value=1)

rules = []

# -----------------------------
# DYNAMIC RULE INPUTS
# -----------------------------
for i in range(num_rules):
    st.markdown(f"### 🔹 Rule {i+1}")

    store_ids = st.text_input(
        f"🏪 Store IDs (comma separated) - Rule {i+1}",
        key=f"store_{i}",
        placeholder="101,102,103"
    )

    col1, col2 = st.columns(2)

    with col1:
        start_time = st.text_input(
            f"⏰ Slot Start (hh:mm) - Rule {i+1}",
            key=f"start_{i}",
            value="09:00"
        )

    with col2:
        end_time = st.text_input(
            f"⏰ Slot End (hh:mm) - Rule {i+1}",
            key=f"end_{i}",
            value="18:00"
        )

    # DayOfWeek dropdown (1–7)
    days = st.multiselect(
        f"📅 Select Day Of Week (1=Mon ... 7=Sun) - Rule {i+1}",
        options=[1, 2, 3, 4, 5, 6, 7],
        default=[1,2,3,4,5],
        key=f"days_{i}"
    )

    rules.append({
        "stores": store_ids,
        "start": start_time,
        "end": end_time,
        "days": days
    })

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
            # TRACKING
            # -----------------------------
            all_input_stores = []
            total_rows_updated = 0

            # -----------------------------
            # APPLY RULES
            # -----------------------------
            for rule in rules:
                if not rule["stores"]:
                    continue

                store_list = [s.strip() for s in rule["stores"].split(",")]
                all_input_stores.extend(store_list)

                mask = (
                    df['StoreID'].astype(str).isin(store_list) &
                    df['DayOfWeek'].astype(str).isin([str(d) for d in rule["days"]])
                )

                rows_updated = mask.sum()
                total_rows_updated += rows_updated

                df.loc[mask, 'SlotStart'] = rule["start"]
                df.loc[mask, 'SlotEnd'] = rule["end"]

            # -----------------------------
            # FIND NOT FOUND STORES
            # -----------------------------
            existing_stores = set(df['StoreID'].astype(str))
            not_found_stores = [s for s in set(all_input_stores) if s not in existing_stores]

            # -----------------------------
            # APPLY DEFAULTS
            # -----------------------------
            if fill_enddate:
                df['EndDate'] = df['EndDate'].replace('', pd.NA).fillna("N/A")

            if fill_servicecc:
                df['ServiceChargeCC'] = df['ServiceChargeCC'].replace('', pd.NA).fillna("0")

            # -----------------------------
            # OUTPUT FILE
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
            st.success(f"✅ Total {total_rows_updated} rows updated")

            # -----------------------------
            # SHOW NOT FOUND STORES
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
