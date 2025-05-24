import streamlit as st
import pandas as pd
from io import BytesIO

# Set page config
st.set_page_config(layout="wide")

# -------------------- Authentication --------------------
def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""

    if not st.session_state.logged_in:
        st.markdown("### 🔐 Login Required")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username == "yogaraj" and password == "afrin":
                st.session_state.logged_in = True
                st.session_state.username = "admin"
                st.rerun()
            elif username == "user" and password == "Stupefy":
                st.session_state.logged_in = True
                st.session_state.username = "QA"
                st.rerun()
            else:
                st.error("Invalid credentials,Better ask Yogaraj")
        st.stop()

login()

username = st.session_state.username

# -------------------- Styling --------------------
st.markdown("""
<style>
/* Main background */
.stApp {
    background-color: #000000;
}

/* Sidebar background */
[data-testid="stSidebar"] {
    background-color: #111111 !important;
}

/* Sidebar text bright white */
[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
    font-weight: normal;
}

/* Left-aligned Heading */
.custom-heading {
    font-size: 2rem;
    color: white;
    text-align: left;
    font-weight: bold;
    margin-bottom: 1.5rem;
    margin-left: 2rem;
}

/* File uploader clean box */
[data-testid="stFileUploader"] > div {
    background-color: #222222 !important;
    padding: 10px !important;
    border: 1px solid #444 !important;
    border-radius: 5px;
}

/* Label and input text */
label, .stFileUploader, .stNumberInput label, .stSelectbox label {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# -------------------- Sidebar Menu --------------------
st.sidebar.markdown("### Menu")
menu_items = ["Alltrans"]
if username == "admin":
    menu_items += ["HDVI MVR", "Truckings IFTA", "Riscom MVR"]
selected_menu = st.sidebar.radio("Select Page", menu_items)

# -------------------- GitHub Link --------------------
if username == "admin":
    st.sidebar.markdown("---")
    st.sidebar.markdown("[🔗 GitHub Profile](https://github.com/your-profile)", unsafe_allow_html=True)

# -------------------- Main Content --------------------
if selected_menu == "Alltrans":
    st.markdown('<div class="custom-heading">Alltrans Excel Creation</div>', unsafe_allow_html=True)

    file1 = st.file_uploader("Upload Client Driver List", type=['xlsx'])
    file2 = st.file_uploader("Upload Output File", type=['xlsx'])

    # ---------- Logic ----------
    def auto_detect_column(columns, keywords):
        for kw in keywords:
            for col in columns:
                if isinstance(col, str) and kw.lower() in col.lower():
                    return col
        return None

    def normalize_name(name):
        if pd.isna(name): return ""
        return str(name).lower().strip()

    def partial_match(n1, n2):
        return bool(set(n1.split()) & set(n2.split()))

    if file1 and file2:
        skip1 = st.number_input("Rows to skip in File 1", 0, 20, 0)
        skip2 = 3  # Default skip 3 rows in file2

        df1 = pd.read_excel(file1, skiprows=skip1)
        xls2 = pd.ExcelFile(file2)
        sheet2 = st.selectbox("Select sheet in File 2", xls2.sheet_names)
        df2_raw = pd.read_excel(xls2, sheet_name=sheet2, skiprows=skip2)
        df2_edit = df2_raw.copy()

        name_col1 = auto_detect_column(df1.columns, ["Driver Name", "Full Name", "Name"])
        date_col1 = auto_detect_column(df1.columns, ["Date of Hire", "Hire Date", "DOH"])
        cdl_col1 = auto_detect_column(df1.columns, ["CDL", "CDL Number", "CDL No", "DL No"])

        name_col2 = auto_detect_column(df2_edit.columns, ["Driver Name", "Full Name", "Name of Driver"])
        date_col2 = auto_detect_column(df2_edit.columns, ["Date of Hire", "Hire Date", "DOH"])

        if not date_col2:
            date_col2 = "Date of Hire"
            df2_edit[date_col2] = pd.NaT

        df1['__name1'] = df1[name_col1].apply(normalize_name)
        df2_edit['__name2'] = df2_edit[name_col2].apply(normalize_name)
        df1[date_col1] = pd.to_datetime(df1[date_col1], errors='coerce')

        for idx, row in df2_edit[df2_edit[date_col2].isna()].iterrows():
            name2 = row['__name2']
            matched = False
            for _, r1 in df1.iterrows():
                if partial_match(name2, r1['__name1']):
                    df2_edit.at[idx, date_col2] = r1[date_col1]
                    matched = True
                    break
            if not matched and cdl_col1:
                val = row.get(cdl_col1)
                if pd.notna(val):
                    match = df1[df1[cdl_col1] == val]
                    if not match.empty:
                        df2_edit.at[idx, date_col2] = match.iloc[0][date_col1]

        df2_edit[date_col2] = pd.to_datetime(df2_edit[date_col2], errors='coerce').dt.strftime('%m/%d/%Y')

        # Remove temp column
        if '__name2' in df2_edit.columns:
            df2_edit.drop(columns=['__name2'], inplace=True)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for sheet in xls2.sheet_names:
                df_orig = pd.read_excel(xls2, sheet_name=sheet, skiprows=skip2 if sheet == sheet2 else 0)
                if sheet == sheet2:
                    combined = pd.concat([df_orig.iloc[:0], df2_edit], ignore_index=True)
                    combined.to_excel(writer, sheet_name=sheet, index=False)
                else:
                    df_orig.to_excel(writer, sheet_name=sheet, index=False)

        st.download_button("Download Excel", output.getvalue(), file_name="output.xlsx")
else:
    st.markdown("### 🚧 Page under construction...")
