import pandas as pd
import streamlit as st
from fuzzywuzzy import fuzz, process
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
    background-color: #4CAF50;
    color: white;
    border-radius: 5px;
    padding: 0.5rem 1rem;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Sidebar menu
with st.sidebar:
    st.markdown("### Menu")
    menu = st.radio("", ["App", "HDVI MVR", "All Trans MVR", "Truckings IFTA", "Riscom MVR"], 
                   label_visibility="collapsed")
    
       
        
    st.markdown("---")
    st.markdown("Built with ❤️ Yogaraj")

# Main content
if menu == "All Trans MVR":
    # Left-aligned heading in main page
    st.markdown('<div class="custom-heading">Alltrans Excel Creation</div>', unsafe_allow_html=True)
    
    # --- Name Matching Functions (Core Logic) ---
    def normalize_name(name):
        """Robust name normalization handling various formats"""
        if pd.isna(name) or not name:
            return []
        
        # Clean and standardize name
        name = str(name).lower()
        name = re.sub(r'[^a-z\s]', '', name)  # Remove non-alphabetic characters
        name = re.sub(r'\s+', ' ', name).strip()  # Normalize spaces
        
        # Split into parts
        parts = name.split()
        if not parts:
            return []
        
        # Create multiple normalization formats
        formats = []
        
        # Format 1: First + Last
        if len(parts) > 1:
            formats.append(f"{parts[0]} {parts[-1]}")
        
        # Format 2: Last + First
        if len(parts) > 1:
            formats.append(f"{parts[-1]} {parts[0]}")
        
        # Format 3: First + Last (concatenated)
        if len(parts) > 1:
            formats.append(f"{parts[0]}{parts[-1]}")
        
        # Format 4: Last + First (concatenated)
        if len(parts) > 1:
            formats.append(f"{parts[-1]}{parts[0]}")
        
        # Format 5: Full name
        formats.append(' '.join(parts))
        
        return formats

    def names_match(name1, name2):
        """Comprehensive name matching using multiple strategies"""
        if pd.isna(name1) or pd.isna(name2) or not name1 or not name2:
            return False
        
        # Get normalized formats
        formats1 = normalize_name(name1)
        formats2 = normalize_name(name2)
        
        # Compare all format combinations
        for f1 in formats1:
            for f2 in formats2:
                # Direct match
                if f1 == f2:
                    return True
                
                # Fuzzy match with 85% threshold
                if fuzz.token_set_ratio(f1, f2) >= 85:
                    return True
                
                # Partial match with 90% threshold
                if fuzz.partial_ratio(f1, f2) >= 90:
                    return True
        
        return False

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
        st.header("📂 Step 1: Upload Files")
        col1, col2 = st.columns(2)
        
        with col1:
            driver_file = st.file_uploader("DRIVER LIST", type=["xlsx"])
        
        with col2:
            output_file = st.file_uploader("OUTPUT FILE", type=["xlsx"])
        
        if not driver_file or not output_file:
            st.info("Please upload both files to proceed")
            return
        
        # Configuration section
        st.header("⚙️ Step 2: Configuration")
        
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
            st.header("🗂️ Step 3: Column Mapping")
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
            if st.button("🚀 Start Matching", use_container_width=True):
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
                        
                        if not matched:
                            existing_notes = str(row.get(output_notes_col, ""))
                            if "MVR MISSING" not in existing_notes:
                                new_notes = f"{existing_notes} (MVR MISSING)" if existing_notes else "MVR MISSING"
                                output.at[idx, output_notes_col] = new_notes.strip()
                        
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
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
                    st.success("✅ Matching complete!")
                    
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
                        label="📥 Download Excel",
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