import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import base64

st.set_page_config(page_title="الصندوق الشخصي", page_icon="💰", layout="wide")

# إعدادات Airtable
ENCODED_KEY = "cGF0bmtsZ05WT0xlWjJ1RGYuNTk2NjgzMDM5NmRmOGUxOGNhNzkwYzVmYWU1NDlhZDdjOTk3Y2YxZDFjYWFjMDI2MTE1OTFkNDIzM2ZjNzYyYg=="
AIRTABLE_API_KEY = base64.b64decode(ENCODED_KEY).decode("utf-8")
BASE_ID = "app8p8z76mWPa3fET"
TABLE_NAME = "Table 1"
headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}", "Content-Type": "application/json"}
url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

# دالة جلب البيانات
def fetch_data():
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            records = response.json().get("records", [])
            data = []
            for r in records:
                fields = r.get("fields", {})
                data.append({
                    "ID": r.get("id"),
                    "التاريخ": fields.get("التاريخ", ""),
                    "النوع": fields.get("النوع", ""),
                    "المبلغ": fields.get("المبلغ", 0),
                    "البيان": fields.get("البيان", "")
                })
            return pd.DataFrame(data)
        return pd.DataFrame()
    except: return pd.DataFrame()

# --- واجهة التطبيق ---
st.title("💰 الصندوق الشخصي")

df = fetch_data()

# 1. لوحة التحكم (الخلاصة)
if not df.empty:
    income = df[df['النوع'] == 'المدخول']['المبلغ'].sum()
    expense = df[df['النوع'] == 'المصروف']['المبلغ'].sum()
    balance = income - expense
else:
    income, expense, balance = 0, 0, 0

# عرض الأرقام في الأعلى (ستايل المسجد)
col1, col2, col3 = st.columns(3)
col1.metric("إجمالي المدخول", f"{income:,.2f}")
col2.metric("إجمالي المصروف", f"{expense:,.2f}")
col3.metric("الرصيد المتبقي (الصندوق)", f"{balance:,.2f}", delta_color="normal")

st.markdown("---")

# 2. أزرار الإدارة
tab1, tab2 = st.tabs(["➕ إضافة معاملة", "⚙️ إدارة الصندوق"])

with tab1:
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        amount = c1.number_input("المبلغ", min_value=0.1, step=1.0)
        trans_type = c2.selectbox("النوع", ["المصروف", "المدخول"])
        date = st.date_input("التاريخ", datetime.today())
        desc = st.text_input("البيان")
        if st.form_submit_button("إضافة"):
            payload = {"records": [{"fields": {"Name": desc, "البيان": desc, "النوع": trans_type, "المبلغ": float(amount), "التاريخ": date.strftime("%Y-%m-%d")}}]}
            requests.post(url, headers=headers, json=payload)
            st.rerun()

with tab2:
    if st.button("🔄 تحديث البيانات"): st.rerun()
    if st.button("🚨 تصفير الصندوق بالكامل", type="primary"):
        # كود التصفير (مبسط)
        if not df.empty:
            for r_id in df["ID"]: requests.delete(f"{url}/{r_id}", headers=headers)
            st.rerun()

st.markdown("---")

# 3. عرض الجدول
st.subheader("📊 تفاصيل المعاملات")
if not df.empty:
    display_df = df.drop(columns=["ID"])
    st.dataframe(display_df, use_container_width=True)
else:
    st.info("لا توجد بيانات.")
