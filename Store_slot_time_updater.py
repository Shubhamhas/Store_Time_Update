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
# NEW USER INPUTS
# -----------------------------
st.subheader("📅 Global Settings for All Stores")

user_startdate = st.text_input(
    "📅 Enter StartDate (DD/MM/YYYY)",
    placeholder="01/01/2025"
)

picking_limit = st.number_input(
    "📦 Enter Picking Limit",
    min_value=0,
    value=0
)

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
            new_rows = []

            # -----------------------------
            # APPLY RULES
            # -----------------------------
            for rule in rules:

                if not rule["stores"]:
                    continue

                store_list = [s.strip() for s in rule["stores"].split(",")]
                all_input_stores.extend(store_list)

                mask = (
                    df["StoreID"].astype(str).isin(store_list) &
                    df["DayOfWeek"].astype(str).isin([str(d) for d in rule["days"]])
                )

                rows_updated = mask.sum()
                total_rows_updated += rows_updated

                df.loc[mask, "SlotStart"] = rule["start"]
                df.loc[mask, "SlotEnd"] = rule["end"]

                existing_store_ids = set(df["StoreID"].astype(str))

                # Add missing stores
                for store_id in store_list:
                    if store_id not in existing_store_ids:

                        reference_row = df.iloc[0].copy()

                        reference_row["StoreID"] = store_id
                        reference_row["SlotStart"] = rule["start"]
                        reference_row["SlotEnd"] = rule["end"]

                        for d in rule["days"]:
                            new_entry = reference_row.copy()
                            new_entry["DayOfWeek"] = str(d)
                            new_rows.append(new_entry)

            if new_rows:
                df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

            # -----------------------------
            # FORCE EndDate = "n/a" FOR ALL RECORDS
            # -----------------------------
            df["EndDate"] = "n/a"

            # -----------------------------
            # APPLY GLOBAL StartDate & PickingLimit
            # -----------------------------
            df["StartDate"] = user_startdate
            df["PickingLimit"] = picking_limit

            # -----------------------------
            # FORCE ServiceChargeCC = "0" FOR ALL RECORDS
            # -----------------------------
            df["ServiceChargeCC"] = "0"

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

            st.success(f"✅ {total_rows_updated} rows updated")
            if new_rows:
                st.success(f"🆕 {len(new_rows)} new rows added")

            st.download_button(
                label="📥 Download Updated File",
                data=output,
                file_name=output_name,
                mime=mime_type
            )

        except Exception as e:
            st.error(f"Error: {str(e)}")
