import pandas as pd
import streamlit as st
from thefuzz import fuzz, process
import re
import io
from datetime import datetime

# Set page configuration
st.set_page_config(layout="wide")

# Apply custom styling
st.markdown("""
<style>
/* Main page background pure black */
.stApp {
    background-color: #000000;
}
/* Sidebar background medium black */
[data-testid="stSidebar"] {
    background-color: #111111 !important;
}
/* Sidebar text bright white but now in normal font */
[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
    font-weight: normal;
}
/* Left-aligned Heading with smaller font and no border */
.custom-heading {
    font-size: 2rem;
    color: white;
    text-align: left;
    font-weight: bold;
    margin-bottom: 1.5rem;
    margin-left: 2rem;
    background: none;
    border: none;
    padding: 0;
}
/* Remove extra empty box inside file uploader */
[data-testid="stFileUploader"] > div {
    background-color: transparent !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    min-height: 0 !important;
    min-width: 0 !important;
}
/* Label and input text white */
label, .stFileUploader, .stNumberInput label, .stSelectbox label {
    color: white !important;
}
/* White text for all content */
body, .stMarkdown, .stText, .stDataFrame, .stMetric {
    color: white !important;
}
/* Custom button styling */
.stButton>button {
    background-color: #000000;
    color: white;
    border-radius: 5px;
    padding: 0.5rem 1rem;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Sidebar menu - FIXED INDENTATION
with st.sidebar:
    st.markdown("### Menu")
    menu = st.radio("", ["App", "HDVI MVR", "All Trans MVR", "Truckings IFTA", "Riscom MVR", "MVR GPT"],

 
                   label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("Built with ❤️ Yogaraj")

# Main content
if menu == "All Trans MVR":
    # Left-aligned heading in main page
    st.markdown('<div class="custom-heading">Alltrans Excel Creation</div>', unsafe_allow_html=True)
    
    # --- UPDATED Name Matching Functions (Core Logic) ---
    def normalize_name(name):
        """Enhanced name normalization with title removal and initials handling"""
        if pd.isna(name) or not name:
            return []
        name = str(name).lower()
        # Remove common prefixes/suffixes
        name = re.sub(r'\b(mr|mrs|ms|dr|jr|sr|iii|ii|iv)\b', '', name)
        # Remove non-alpha chars except spaces
        name = re.sub(r'[^a-z\s]', '', name)
        # Normalize spaces
        name = re.sub(r'\s+', ' ', name).strip()
        parts = name.split()
        if not parts:
            return []

        formats = []
        # Full name normal
        formats.append(' '.join(parts))
        # First last and last first formats
        if len(parts) > 1:
            formats.append(f"{parts[0]} {parts[-1]}")
            formats.append(f"{parts[-1]} {parts[0]}")
            formats.append(f"{parts[0]}{parts[-1]}")
            formats.append(f"{parts[-1]}{parts[0]}")

        # Initial-based formats if middle names exist
        if len(parts) > 2:
            first = parts[0]
            last = parts[-1]
            initials = ''.join([p[0] for p in parts[1:-1]])
            formats.append(f"{first} {initials} {last}")
            formats.append(f"{first} {initials}{last}")
            formats.append(f"{first}{initials} {last}")
            formats.append(f"{first}{initials}{last}")

        # Remove duplicates
        return list(set(formats))

    def names_match(name1, name2):
        """Stricter matching with multiple fuzzy strategies"""
        if pd.isna(name1) or pd.isna(name2) or not name1 or not name2:
            return False
        formats1 = normalize_name(name1)
        formats2 = normalize_name(name2)
        for f1 in formats1:
            for f2 in formats2:
                if f1 == f2:
                    return True
                if fuzz.token_set_ratio(f1, f2) >= 95:
                    return True
                if fuzz.partial_ratio(f1, f2) >= 96:
                    return True
                if fuzz.token_sort_ratio(f1, f2) >= 98:
                    return True
        return False

    # --- REST OF THE CODE ---
    def get_valid_column(df, purpose, default_names, required=True):
        """Find column with fuzzy matching, using defaults if possible"""
        # First try exact matches to default names
        for col in default_names:
            if col in df.columns:
                return col
        
        # Then try fuzzy matching
        for col_name in default_names:
            match, score = process.extractOne(col_name, df.columns, scorer=fuzz.ratio)
            if score > 80:
                return match
        
        # If not found and required, return first column
        if required and len(df.columns) > 0:
            return df.columns[0]
        
        return None

    # --- Driver Matching Tool ---
    def driver_matching_app():
        # File upload section
        st.header("Upload Files")
        col1, col2 = st.columns(2)
        
        with col1:
            driver_file = st.file_uploader("DRIVER LIST", type=["xlsx"])
        
        with col2:
            output_file = st.file_uploader("OUTPUT FILE", type=["xlsx"])
        
        if not driver_file or not output_file:
            st.info("Please upload both files to proceed")
            return
        
        # Configuration section
        st.header("Configuration...")
        
        # Default row skipping
        driver_skip = st.number_input("Rows to skip in DRIVER file", min_value=0, value=0)
        output_skip = 3  # Fixed as requested
        
        # Load data
        try:
            # Load output file to get sheet names
            xls = pd.ExcelFile(output_file)
            sheet_names = xls.sheet_names
            
            # Sheet selection with "All Trans" as default
            sheet = st.selectbox("Select sheet to process", sheet_names, 
                                index=sheet_names.index("All Trans") if "All Trans" in sheet_names else 0)
            
            # Read data
            drivers = pd.read_excel(driver_file, skiprows=driver_skip)
            output = pd.read_excel(output_file, sheet_name=sheet, skiprows=output_skip)
            
            # Column mapping section
            st.header("Column Mapping Running...")
            st.info("Map columns between files. The tool will try to auto-detect columns.")
            
            # Driver file columns
            st.subheader("Driver File Columns")
            driver_name_col = get_valid_column(drivers, "driver names", 
                                            ['name', 'driver name', 'full name'])
            hire_date_col = get_valid_column(drivers, "hire dates", 
                                        ['hire date', 'date of hire', 'doh'])
            dob_col = get_valid_column(drivers, "date of birth", 
                                    ['dob', 'date of birth', 'birth date'], False)
            license_col = get_valid_column(drivers, "license state", 
                                        ['license state', 'lic state', 'state'], False)
            
            # Display detected driver columns
            st.write(f"Detected Driver Name Column: `{driver_name_col}`")
            if hire_date_col:
                st.write(f"Detected Hire Date Column: `{hire_date_col}`")
            if dob_col:
                st.write(f"Detected Date of Birth Column: `{dob_col}`")
            if license_col:
                st.write(f"Detected License State Column: `{license_col}`")
            
            # Output file columns (with defaults)
            st.subheader("Output File Columns")
            output_name_col = get_valid_column(output, "driver names", 
                                            ['Name of Driver', 'Driver Name', 'Name'])
            output_dob_col = get_valid_column(output, "date of birth", 
                                            ['DOB', 'Date of Birth'], False) or "DOB"
            output_license_col = get_valid_column(output, "license state", 
                                                ['Lic State', 'License State', 'State'], False) or "Lic State"
            output_notes_col = get_valid_column(output, "notes", 
                                            ['Notes', 'Remarks', 'Comments']) or "Notes"
            output_hire_col = get_valid_column(output, "hire date", 
                                            ['DOH', 'Hire Date', 'Date of Hire'], False) or "DOH"
            
            # Display detected output columns
            st.write(f"Detected Driver Name Column: `{output_name_col}`")
            st.write(f"Detected DOB Column: `{output_dob_col}`")
            st.write(f"Detected License State Column: `{output_license_col}`")
            st.write(f"Detected Notes Column: `{output_notes_col}`")
            st.write(f"Detected Hire Date Column: `{output_hire_col}`")
            
            # Initialize output columns if needed
            for col in [output_dob_col, output_license_col, output_notes_col, output_hire_col]:
                if col not in output.columns:
                    output[col] = ""
            
            # Process button
            if st.button("Process File", use_container_width=True):
                with st.spinner("Matching names..."):
                    # Perform matching
                    match_count = 0
                    total_original = len(output)
                    
                    # Track matched driver indices
                    matched_driver_indices = set()
                    
                    # Progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for idx, row in output.iterrows():
                        output_name = row[output_name_col]
                        matched = False
                        
                        for driver_idx, driver_row in drivers.iterrows():
                            if driver_idx in matched_driver_indices:
                                continue
                                
                            if names_match(output_name, driver_row[driver_name_col]):
                                # Mark as matched
                                matched_driver_indices.add(driver_idx)
                                output.at[idx, output_notes_col] = "MATCH FOUND"
                                
                                # Transfer all available data
                                if hire_date_col:
                                    output.at[idx, output_hire_col] = driver_row[hire_date_col]
                                if dob_col:
                                    output.at[idx, output_dob_col] = driver_row[dob_col]
                                if license_col:
                                    output.at[idx, output_license_col] = driver_row[license_col]
                                
                                match_count += 1
                                matched = True
                                break
                        
                        # REMOVED: MVR MISSING marking for existing rows
                        # We'll only add missing drivers at the end
                        
                        # Update progress
                        progress = (idx + 1) / total_original
                        progress_bar.progress(progress)
                        status_text.text(f"Processed {idx + 1}/{total_original} records")
                    
                    # Add non-matched driver records at the end
                    new_rows = []
                    for driver_idx, driver_row in drivers.iterrows():
                        if driver_idx not in matched_driver_indices:
                            # Create new row with driver data
                            new_row = {col: "" for col in output.columns}
                            new_row[output_name_col] = driver_row[driver_name_col]
                            
                            # Add all available driver information
                            if hire_date_col:
                                new_row[output_hire_col] = driver_row[hire_date_col]
                            if dob_col:
                                new_row[output_dob_col] = driver_row[dob_col]
                            if license_col:
                                new_row[output_license_col] = driver_row[license_col]
                            
                            new_row[output_notes_col] = "MISSING MVR"
                            new_rows.append(new_row)
                    
                    # Append new rows to output
                    if new_rows:
                        new_rows_df = pd.DataFrame(new_rows)
                        output = pd.concat([output, new_rows_df], ignore_index=True)
                        added_count = len(new_rows)
                    else:
                        added_count = 0
                    
                    # Generate timestamped filename
                    timestamp = datetime.now().strftime("%m%d%Y")
                    result_filename = f"Driver_Matching_Result_{timestamp}.xlsx"
                    
                    # Save to BytesIO for download
                    output_bytes = io.BytesIO()
                    with pd.ExcelWriter(output_bytes, engine='openpyxl') as writer:
                        output.to_excel(writer, sheet_name=sheet, index=False)
                        # Preserve other sheets
                        for other_sheet in sheet_names:
                            if other_sheet != sheet:
                                pd.read_excel(output_file, sheet_name=other_sheet).to_excel(writer, sheet_name=other_sheet, index=False)
                    
                    output_bytes.seek(0)
                    
                    # Results Summary
                    total_final = len(output)
                    st.success("Matching complete!")
                    
                    # Show summary
                    st.subheader("📊 Results Summary")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Original Records", total_original)
                    col2.metric("Matched Records", match_count)
                    col3.metric("Added Records", added_count)
                    
                    # Show data transfer summary
                    st.write("**Data Transferred:**")
                    if hire_date_col:
                        st.write(f"- Hire Dates: {match_count + added_count}")
                    if dob_col:
                        st.write(f"- Birth Dates: {match_count + added_count}")
                    if license_col:
                        st.write(f"- License States: {match_count + added_count}")
                    
                    # Download button
                    st.download_button(
                        label="Download Excel",
                        data=output_bytes,
                        file_name=result_filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    # Show preview
                    st.subheader("Preview of Processed Data")
                    st.dataframe(output.head(10))
        
        except Exception as e:
            st.error(f"⚠️ Error occurred: {str(e)}")
            st.exception(e)

    # Run the driver matching app
    driver_matching_app()

# Placeholder for other menu options
elif menu == "App":
    st.markdown('<div class="custom-heading">Main Application</div>', unsafe_allow_html=True)
    st.write("Welcome to the main application. Select a menu option on the left.")
    
elif menu == "HDVI MVR":
    st.markdown('<div class="custom-heading">HDVI MVR Tool</div>', unsafe_allow_html=True)
    st.write("HDVI MVR tool will be available soon.")
    
elif menu == "Truckings IFTA":
    st.markdown('<div class="custom-heading">Truckings IFTA Tool</div>', unsafe_allow_html=True)
    st.write("Truckings IFTA tool will be available soon.")
    
elif menu == "Riscom MVR":
    st.markdown('<div class="custom-heading">Riscom MVR Tool</div>', unsafe_allow_html=True)
    st.write("Riscom MVR tool will be available soon.")
elif menu == "MVR GPT":
    import pandas as pd
    from fuzzywuzzy import process
    import streamlit as st

    @st.cache_data
    def load_data():
        try:
            df = pd.read_excel("violations.xlsx", sheet_name="Sheet1")
            return df
        except Exception as e:
            st.error(f"❌ Failed to load Excel file: {e}")
            return pd.DataFrame()  # return empty dataframe on error

    df = load_data()

    if df.empty:
        st.stop()

    user_input = st.text_input("Enter Violation Description:")

    if user_input:
        if 'Violation Description' not in df.columns or 'Category' not in df.columns:
            st.error("❗Missing required columns ('Violation Description' or 'Category') in Excel file.")
        else:
            choices = df['Violation Description'].dropna().tolist()
            match, score = process.extractOne(user_input, choices)

            threshold = 70
            if score >= threshold:
                category = df.loc[df['Violation Description'] == match, 'Category'].values[0]
                st.success(f"Partial match: '{match}' (Confidence: {score}), If you have doubt ask QC team")
                if score < threshold:
                    print("If you have doubt on this ask QC team once")
                st.info(f"Violation category: **{category}**")
            else:

                st.warning("🤖 Hmm... that one's tricky! Might wanna reach out to the QC wizards 🧙‍♂️✨")

                st.warning("Better reach out to the QC Team!✨")
