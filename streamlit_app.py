import streamlit as st
import pandas as pd
from io import BytesIO

# -------------------- PAGE CONFIG --------------------
st.set_page_config(layout="wide", page_title="Non_LR-Report Generation")

# -------------------- SESSION AUTH --------------------
def login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "Yoga" and password == "afrin":
            st.session_state['authenticated'] = True
            st.session_state['user_role'] = 'admin'
        elif username == "user" and password == "Stupefy":
            st.session_state['authenticated'] = True
            st.session_state['user_role'] = 'QA'
        else:
            st.error("Invalid credentials")

if 'authenticated' not in st.session_state:
    login()
    st.stop()

# -------------------- STYLING --------------------
st.markdown("""
<style>
.stApp { background-color: #000000; }
[data-testid="stSidebar"] { background-color: #111111 !important; }
[data-testid="stSidebar"] * { color: #FFFFFF !important; }
.custom-heading {
    font-size: 2rem;
    color: white;
    text-align: left;
    font-weight: bold;
    margin-bottom: 1.5rem;
    margin-left: 2rem;
}
</style>
""", unsafe_allow_html=True)

# -------------------- SIDEBAR MENU --------------------
if st.session_state['user_role'] == 'admin':
    st.sidebar.title("Menu")
    page = st.sidebar.radio("Go to", ["Alltrans", "HDVI MVR", "Truckings IFTA", "Riscom MVR"])
    st.sidebar.markdown("[GitHub](https://github.com/yourprofile)")
else:
    st.sidebar.title("Menu")
    page = st.sidebar.radio("Go to", ["Alltrans"])

# -------------------- PAGE ROUTING --------------------
if page == "Alltrans":
    st.markdown('<div class="custom-heading">Alltrans Excel Creation</div>', unsafe_allow_html=True)

    file1 = st.file_uploader("Upload Client Driver List", type=['xlsx'])
    file2 = st.file_uploader("Upload Output File", type=['xlsx'])

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
        skip2 = st.number_input("Rows to skip in File 2", 0, 20, 3)

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
    st.markdown(f"<h3 style='color:white'>{page} page coming soon...</h3>", unsafe_allow_html=True)
