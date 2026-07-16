import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import base64

# إعدادات الصفحة
st.set_page_config(page_title="الصندوق الشخصي", page_icon="💰", layout="centered")

# فك تشفير الرمز السري الجديد تلقائياً
ENCODED_KEY = "cGF0bmtsZ05WT0xlWjJ1RGYuNTk2NjgzMDM5NmRmOGUxOGNhNzkwYzVmYWU1NDlhZDdjOTk3Y2YxZDFjYWFjMDI2MTE1OTFkNDIzM2ZjNzYyYg=="
AIRTABLE_API_KEY = base64.b64decode(ENCODED_KEY).decode("utf-8")

# الإعدادات الصحيحة والمطابقة لجدولك تماماً
BASE_ID = "app8p8z76mWPa3fET"
TABLE_NAME = "Table 1"  

# إعداد رأس الطلب للاتصال بـ Airtable
headers = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}
url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

# دالة لجلب البيانات وعرضها
def fetch_data():
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            records = response.json().get("records", [])
            data = []
            for r in records:
                fields = r.get("fields", {})
                data.append({
                    "البيان": fields.get("البيان", ""),
                    "النوع": fields.get("النوع", ""),
                    "المبلغ": fields.get("المبلغ", 0),
                    "التاريخ": fields.get("التاريخ", "")
                })
            df = pd.DataFrame(data)
            if not df.empty:
                cols = ["التاريخ", "النوع", "المبلغ", "البيان"]
                df = df.reindex(columns=[c for c in cols if c in df.columns])
            return df
        else:
            st.error(f"فشل الاتصال بـ Airtable. رمز الخطأ: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"حدث خطأ غير متوقع: {e}")
        return pd.DataFrame()

# دالة لإضافة معاملة جديدة
def add_record(date, trans_type, amount, description):
    payload = {
        "records": [
            {
                "fields": {
                    "Name": description,  # تعبئة الحقل الأساسي لتجنب Unnamed record
                    "البيان": description,
                    "النوع": trans_type,   # سيرسل القيمة المطابقة تماماً (المصروف / المدخول)
                    "المبلغ": float(amount),
                    "التاريخ": date.strftime("%Y-%m-%d")
                }
            }
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return True, "تمت الإضافة بنجاح!"
        else:
            return False, f"رمز الخطأ {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

# عنوان التطبيق
st.title("💰 الصندوق الشخصي للمدخول والمصروفات")
st.write("سجل معاملاتك المالية وراقب حركة صندوقك بسهولة.")

st.markdown("---")

# نموذج إضافة معاملة جديدة
st.subheader("📝 إضافة معاملة جديدة")
with st.form("transaction_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        amount = st.number_input("المبلغ", min_value=0.1, step=1.0, format="%.2f")
    with col2:
        # تعديل الخيارات هنا لتطابق الحقول في Airtable تماماً بـ ال التعريف
        trans_type = st.selectbox("النوع", ["المصروف", "المدخول"])
        date = st.date_input("التاريخ", datetime.today())
        
    description = st.text_input("البيان / الوصف")
    
    submit_button = st.form_submit_button("إضافة المعاملة")

if submit_button:
    success, message = add_record(date, trans_type, amount, description)
    if success:
        st.success("🎉 تم تسجيل المعاملة بنجاح وإرسالها إلى Airtable!")
        st.rerun()
    else:
        st.error(f"❌ حدث خطأ أثناء الإرسال. التفاصيل:")
        st.code(message)

st.markdown("---")

# عرض المعاملات المسجلة
st.subheader("📊 حركة الصندوق الحالية")
df = fetch_data()
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("لا توجد معاملات مسجلة بعد في الجدول.")
