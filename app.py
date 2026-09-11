import streamlit as st
import pandas as pd

# Callback to clear previous results if new files are uploaded
def clear_results():
    st.session_state.unique_df = None
    st.session_state.df1 = None
    st.session_state.df2 = None

st.set_page_config(page_title="CSV Comparator", page_icon="📊")

st.title("📊 CSV Comparator: Find New Records")
st.write("Upload your Master Data (CSV 1) and Comparing Data (CSV 2). Pick the column that uniquely identifies records, and the app will extract rows from CSV 2 that don't exist in CSV 1.")

st.info('💡 **In short:** It answers *"Which rows in CSV 2 don\'t already exist in CSV 1, based on the columns I care about?"*')

# Initialize session state
for key in ['unique_df', 'df1', 'df2']:
    if key not in st.session_state:
        st.session_state[key] = None

col1, col2 = st.columns(2)

with col1:
    file1 = st.file_uploader("Upload Master Data (CSV 1)", type=["csv"], on_change=clear_results)
with col2:
    file2 = st.file_uploader("Upload Comparing Data (CSV 2)", type=["csv"], on_change=clear_results)

# Read files into session state once both are uploaded
if file1 and file2 and st.session_state.df1 is None:
    try:
        file1.seek(0)
        file2.seek(0)
        st.session_state.df1 = pd.read_csv(file1).drop_duplicates().copy()
        st.session_state.df2 = pd.read_csv(file2).drop_duplicates().copy()
    except Exception as e:
        st.error(f"Error reading files: {e}")

# Show unique identifier selector once both files are loaded
if st.session_state.df1 is not None and st.session_state.df2 is not None:
    df1 = st.session_state.df1
    df2 = st.session_state.df2

    # Find common columns between both files
    common_cols = [c for c in df1.columns if c in df2.columns]

    if not common_cols:
        st.error("❌ The two CSV files have no common columns to compare on.")
    else:
        # Default to 'name' if it exists
        default_cols = [c for c in common_cols if c.strip().lower() == 'name']
        identifier_cols = st.multiselect(
            "🔑 Select Unique Identifier Column(s)",
            options=common_cols,
            default=default_cols if default_cols else [],
            help="Choose one or more columns that together uniquely identify each record (e.g. Email, ID, Name)"
        )

        if st.button("Compare Files", type="primary", disabled=len(identifier_cols) == 0):
            try:
                # Build a composite key from all selected columns (fillna handles NaN/float values)
                master_keys = df1[identifier_cols].fillna("").astype(str).apply(lambda r: "||".join(r.str.strip()), axis=1)
                compare_keys = df2[identifier_cols].fillna("").astype(str).apply(lambda r: "||".join(r.str.strip()), axis=1)

                df_unique = df2[~compare_keys.isin(master_keys)].copy()
                st.session_state.unique_df = df_unique

                st.success("✅ Comparison complete!")
            except Exception as e:
                st.error(f"An error occurred: {e}")

# Display results
if st.session_state.unique_df is not None:
    st.divider()

    unique_count = len(st.session_state.unique_df)

    res_col1, res_col2 = st.columns([3, 1])
    with res_col1:
        st.subheader("New Unique Records (From CSV 2)")
    with res_col2:
        st.metric(label="Unique Records Count", value=unique_count)

    if unique_count == 0:
        st.info("No new records found. All values in the selected column of CSV 2 already exist in the Master Data.")
    else:
        st.dataframe(st.session_state.unique_df, use_container_width=True)

        csv_data = st.session_state.unique_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download New Data as CSV",
            data=csv_data,
            file_name="unique_records_result.csv",
            mime="text/csv",
        )
