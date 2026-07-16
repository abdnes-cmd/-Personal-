import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import base64

# إعدادات الصفحة
st.set_page_config(page_title="الصندوق الشخصي", page_icon="💰", layout="centered")

# فك تشفير الرمز السري الجديد تلقائياً بأمان
ENCODED_KEY = "cGF0bmtsZ05WT0xlWjJ1RGYuNTk2NjgzMDM5NmRmOGUxOGNhNzkwYzVmYWU1NDlhZDdjOTk3Y2YxZDFjYWFjMDI2MTE1OTFkNDIzM2ZjNzYyYg=="
AIRTABLE_API_KEY = base64.b64decode(ENCODED_KEY).decode("utf-8")

# إعدادات جدولك الفعلي الجديد
BASE_ID = "app8p8z76mWPa3fET"
TABLE_NAME = "tbl4VJzkXSFfZpvOd"

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
                    "الفئة": fields.get("الفئة", ""),
                    "المبلغ": fields.get("المبلغ", 0),
                    "التاريخ": fields.get("التاريخ", "")
                })
            # ترتيب الأعمدة لتظهر بشكل منسق في جدول عرض البيانات
            df = pd.DataFrame(data)
            if not df.empty:
                cols = ["التاريخ", "النوع", "الفئة", "المبلغ", "البيان"]
                df = df.reindex(columns=[c for c in cols if c in df.columns])
            return df
        else:
            st.error(f"فشل الاتصال بـ Airtable. رمز الخطأ: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"حدث خطأ أثناء الاتصال: {e}")
        return pd.DataFrame()

# دالة لإضافة معاملة جديدة
def add_record(date, trans_type, category, amount, description):
    payload = {
        "records": [
            {
                "fields": {
                    "البيان": description,
                    "النوع": trans_type,
                    "الفئة": category,
                    "المبلغ": float(amount),
                    "التاريخ": date.strftime("%Y-%m-%d")
                }
            }
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.status_code == 200
    except Exception as e:
        st.error(f"حدث خطأ أثناء الإضافة: {e}")
        return False

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
        category = st.text_input("الفئة (مثال: طعام، وقود، راتب...)")
    with col2:
        trans_type = st.selectbox("النوع", ["مصروف", "مدخول"])
        date = st.date_input("التاريخ", datetime.today())
        
    description = st.text_input("البيان / الوصف")
    
    submit_button = st.form_submit_button("إضافة المعاملة")

if submit_button:
    if not category:
         st.warning("الرجاء كتابة الفئة أولاً!")
    else:
        success = add_record(date, trans_type, category, amount, description)
        if success:
            st.success("🎉 تم تسجيل المعاملة بنجاح وإرسالها إلى Airtable!")
            st.rerun() # تحديث الصفحة فوراً
        else:
            st.error("❌ حدث خطأ أثناء محاولة إرسال البيانات. تأكد من مطابقة أسماء الحقول في جدول Airtable.")

st.markdown("---")

# عرض المعاملات المسجلة
st.subheader("📊 حركة الصندوق الحالية")
df = fetch_data()
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("لا توجد معاملات مسجلة بعد في الجدول.")
